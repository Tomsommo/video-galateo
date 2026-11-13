#!/usr/bin/env python3
"""Genera VARIANTI di immagini per ogni scena, da scegliere prima del montaggio.

Job in previews/<nome>.json:
{ "name": "...", "style": "...", "variants": 3, "base_seed": 200,
  "scenes": [ {"image_prompt": "...", "text": "..."} ] }

Per ogni scena salva previews/<nome>/sNN_<lettera>.jpg (NN da 01, lettere a, b, c)
e crea le tavole previews/<nome>-tavola-<n>.jpg con numero scena + lettera.
Poi nel job video basta mettere "image": "previews/<nome>/s03_b.jpg".
"""
import glob, json, os, sys
from PIL import Image, ImageDraw, ImageFont
from render import download, pollinations_url

TW, TH = 360, 640
PER_SHEET = 4
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def make(job_path):
    job = json.load(open(job_path, encoding="utf-8"))
    name, n = job["name"], job.get("variants", 3)
    folder = os.path.join("previews", name)
    os.makedirs(folder, exist_ok=True)
    letters = "abcdefgh"[:n]
    rows = []
    for i, sc in enumerate(job["scenes"], 1):
        prompt = (job.get("style", "") + " " + sc["image_prompt"]).strip()
        files = []
        for k, L in enumerate(letters):
            dest = os.path.join(folder, f"s{i:02d}_{L}.jpg")
            if not os.path.exists(dest):
                seed = sc.get("base_seed", job.get("base_seed", 200)) + i * 10 + k
                try:
                    download(pollinations_url(prompt, seed), dest)
                    im = Image.open(dest).convert("RGB")
                    im = im.crop((0, 0, im.width, int(im.height * 0.92)))  # toglie la scritta
                    im.save(dest, quality=90)
                except Exception as exc:
                    print(f"scena {i}{L}: {exc}")
                    continue
            files.append((L, dest))
        rows.append((i, sc["text"], files))
    font = ImageFont.truetype(FONT, 34)
    small = ImageFont.truetype(FONT, 22)
    for p in range(0, len(rows), PER_SHEET):
        chunk = rows[p:p + PER_SHEET]
        sheet = Image.new("RGB", (TW * n, (TH + 70) * len(chunk)), "white")
        d = ImageDraw.Draw(sheet)
        for r, (i, text, files) in enumerate(chunk):
            y = r * (TH + 70)
            d.text((10, y + 5), f"{i}. {text[:70]}", fill="black", font=small)
            for L, f in files:
                x = letters.index(L) * TW
                im = Image.open(f).convert("RGB")
                sheet.paste(im.resize((TW, TH)), (x, y + 40))
                d.rectangle((x + 5, y + 45, x + 85, y + 95), fill="black")
                d.text((x + 15, y + 50), f"{i}{L.upper()}", fill="white", font=font)
        out = f"previews/{name}-tavola-{p // PER_SHEET + 1}.jpg"
        sheet.save(out, quality=80)
        print("OK", out)


def main():
    jobs = sys.argv[1:] or [p for p in sorted(glob.glob("previews/*.json"))
                            if not glob.glob(p[:-5] + "-tavola-*.jpg")]
    for p in jobs:
        make(p)


if __name__ == "__main__":
    main()
