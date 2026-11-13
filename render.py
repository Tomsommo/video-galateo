#!/usr/bin/env python3
"""Monta un video verticale (1080x1920) da immagini fisse + voce narrante + sottotitoli.

Uso: python render.py [jobs/nome.json ...]
Senza argomenti elabora tutti i jobs/*.json che non hanno ancora out/<name>.mp4.

Formato del job:
{
  "name": "ettore-2026-11-08",
  "voice": "it-IT-DiegoNeural",      (facoltativo)
  "rate": "-5%",                      (facoltativo, velocita' voce)
  "pad": 0.25,                        (facoltativo, pausa dopo ogni scena)
  "style": "...",                     (facoltativo, aggiunto davanti a ogni image_prompt)
  "scenes": [ {"image": "https://...jpg", "text": "testo letto mentre si vede l'immagine"},
              {"image": "...", "crop": [0.1, 0.2, 0.5], "text": "..."}  (inquadratura: x, y, lato in frazioni),
              {"image_prompt": "descrizione in inglese: l'immagine viene creata gratis con Pollinations", "text": "..."} ]
}
Variabile d'ambiente FAKE_TTS=1: voce finta (solo per provare il montaggio).
"""
import asyncio
import glob
import json
import math
import os
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request

W, H, FPS = 1080, 1920, 30
PAD = 0.5          # pausa dopo ogni scena (secondi)
ZOOM = 0.12        # quanto zoomare (12%)
MAX_CUE_CHARS = 26
FALLBACK_VOICE = "it-IT-DiegoNeural"


def run(cmd, **kw):
    subprocess.run(cmd, check=True, **kw)


def duration(path):
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path]
    )
    return float(out.decode().strip())


def srt_time(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def download(url, dest, tries=6):
    last = None
    for n in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 video-galateo"})
            with urllib.request.urlopen(req, timeout=180) as r:
                data = r.read()
            if len(data) < 5000:
                raise RuntimeError(f"risposta troppo piccola ({len(data)} byte)")
            with open(dest, "wb") as f:
                f.write(data)
            return
        except Exception as exc:  # riprova dopo una pausa
            last = exc
            print(f"Scarico fallito ({exc}), tentativo {n + 1}/{tries}")
            time.sleep(15)
    raise RuntimeError(f"Impossibile scaricare {url[:80]}: {last}")


def pollinations_url(prompt, seed):
    q = urllib.parse.quote(prompt)
    return (f"https://image.pollinations.ai/prompt/{q}"
            f"?width=1080&height=1920&model=flux&nologo=true&seed={seed}")


def even_words(text, total):
    """Tempi stimati in proporzione alle lettere (se la voce non da' i tempi parola per parola)."""
    words = text.split()
    weights = [max(len(w), 1) for w in words]
    tot = sum(weights)
    t, out = 0.0, []
    for w, wt in zip(words, weights):
        d = total * wt / tot
        out.append((t, t + d, w))
        t += d
    return out


async def tts_edge(text, voice, rate, mp3):
    import edge_tts

    comm = edge_tts.Communicate(text, voice, rate=rate, boundary="WordBoundary")
    words = []
    with open(mp3, "wb") as f:
        async for ch in comm.stream():
            if ch["type"] == "audio":
                f.write(ch["data"])
            elif ch["type"] == "WordBoundary":
                start = ch["offset"] / 1e7
                words.append((start, start + ch["duration"] / 1e7, ch["text"]))
    return words


def tts_fake(text, mp3):
    secs = max(len(text) / 14.0, 1.0)
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
         f"sine=frequency=220:duration={secs:.2f}", "-c:a", "libmp3lame", mp3])
    return []


def make_cues(words, offset):
    cues, cur, start = [], [], None
    last_end = 0.0
    for (s, e, w) in words:
        if cur and len(" ".join(cur + [w])) > MAX_CUE_CHARS:
            cues.append([start + offset, last_end + offset, " ".join(cur)])
            cur, start = [], None
        if start is None:
            start = s
        cur.append(w)
        last_end = e
        if w[-1:] in ".,;:?!…":
            cues.append([start + offset, e + offset, " ".join(cur)])
            cur, start = [], None
    if cur:
        cues.append([start + offset, words[-1][1] + offset, " ".join(cur)])
    # i sottotitoli restano a schermo fino al successivo
    for i in range(len(cues) - 1):
        cues[i][1] = max(cues[i][1], min(cues[i + 1][0], cues[i][1] + 0.4))
    return cues


def render_job(job_path):
    with open(job_path, encoding="utf-8") as f:
        job = json.load(f)
    name = job["name"]
    voice = job.get("voice", "it-IT-DiegoNeural")
    rate = job.get("rate", "-5%")
    pad = float(job.get("pad", PAD))
    out_path = os.path.join("out", f"{name}.mp4")
    os.makedirs("out", exist_ok=True)
    fake = os.environ.get("FAKE_TTS") == "1"

    with tempfile.TemporaryDirectory() as tmp:
        clips, cues, t0 = [], [], 0.0
        for i, sc in enumerate(job["scenes"]):
            img = os.path.join(tmp, f"img{i}.jpg")
            mp3 = os.path.join(tmp, f"a{i}.mp3")
            clip = os.path.join(tmp, f"clip{i}.mp4")
            src = sc.get("image") or pollinations_url(
                (job.get("style", "") + " " + sc["image_prompt"]).strip(), sc.get("seed", 7 + i))
            if src.startswith("http"):
                download(src, img)
                if "pollinations.ai" in src:  # toglie la scritta in basso
                    cr = img + ".c.jpg"
                    run(["ffmpeg", "-y", "-loglevel", "error", "-i", img,
                         "-vf", "crop=iw:ih*0.92:0:0", cr])
                    os.replace(cr, img)
            else:
                img = src
            if sc.get("crop"):  # inquadratura: [x, y, f] in frazioni dell'immagine
                cx, cy, cf = sc["crop"]
                cr = os.path.join(tmp, f"crop{i}.jpg")
                run(["ffmpeg", "-y", "-loglevel", "error", "-i", img, "-vf",
                     f"crop=iw*{cf}:ih*{cf}:iw*{cx}:ih*{cy},scale={W}:{H}:flags=lanczos", "-q:v", "2", cr])
                img = cr
            if fake:
                words = tts_fake(sc["text"], mp3)
            else:
                try:
                    words = asyncio.run(tts_edge(sc["text"], voice, rate, mp3))
                except Exception as exc:  # voce non disponibile: ripiega su quella di riserva
                    print(f"Voce {voice} non riuscita ({exc}); uso {FALLBACK_VOICE}")
                    words = asyncio.run(tts_edge(sc["text"], FALLBACK_VOICE, rate, mp3))
            a_dur = duration(mp3)
            if not words:
                words = even_words(sc["text"], a_dur)
            cues += make_cues(words, t0)
            total = a_dur + pad
            frames = max(int(math.ceil(total * FPS)), 1)
            if i % 2 == 0:
                z = f"1+{ZOOM}*on/{frames}"
            else:
                z = f"{1 + ZOOM}-{ZOOM}*on/{frames}"
            vf = (
                f"scale={int(W*1.5)}:{int(H*1.5)}:force_original_aspect_ratio=increase,"
                f"crop={int(W*1.5)}:{int(H*1.5)},"
                f"zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps={FPS},"
                f"format=yuv420p"
            )
            run(["ffmpeg", "-y", "-loglevel", "error", "-i", img, "-i", mp3,
                 "-filter_complex", f"[0:v]{vf}[v];[1:a]apad=pad_dur={pad},aresample=44100[a]",
                 "-map", "[v]", "-map", "[a]", "-t", f"{total:.3f}",
                 "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
                 "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-ac", "2", clip])
            clips.append(clip)
            t0 += total

        listfile = os.path.join(tmp, "list.txt")
        with open(listfile, "w") as f:
            for c in clips:
                f.write(f"file '{c}'\n")
        joined = os.path.join(tmp, "joined.mp4")
        run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
             "-i", listfile, "-c", "copy", joined])

        srt = os.path.join(tmp, "subs.srt")
        with open(srt, "w", encoding="utf-8") as f:
            for n, (s, e, text) in enumerate(cues, 1):
                f.write(f"{n}\n{srt_time(s)} --> {srt_time(e)}\n{text}\n\n")

        style = ("FontName=DejaVu Sans,Bold=1,FontSize=9,PrimaryColour=&H00FFFFFF,"
                 "OutlineColour=&H00000000,BorderStyle=1,Outline=3,Shadow=0,Alignment=2,MarginV=45")
        run(["ffmpeg", "-y", "-loglevel", "error", "-i", "joined.mp4",
             "-vf", f"subtitles=subs.srt:force_style='{style}'",
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p",
             "-c:a", "copy", "-movflags", "+faststart", os.path.abspath(out_path)],
            cwd=tmp)
    print(f"OK {out_path} ({duration(out_path):.1f}s)")


def main():
    jobs = sys.argv[1:]
    if not jobs:
        for p in sorted(glob.glob("jobs/*.json")):
            with open(p, encoding="utf-8") as f:
                name = json.load(f)["name"]
            if not os.path.exists(os.path.join("out", f"{name}.mp4")):
                jobs.append(p)
    if not jobs:
        print("Niente da montare.")
        return
    for p in jobs:
        render_job(p)


if __name__ == "__main__":
    main()
