#!/usr/bin/env python3
"""Crea le slide dei caroselli (1080x1350 JPG) nello stile della pagina.

Uso: python3 caroselli/crea.py 2026-11-13
Scrive caroselli/<data>/01.jpg ... 05.jpg e didascalie.json (data -> testo, numero slide).
"""
import datetime as dt, json, os, sys
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(__file__))
from contenuti import CAROSELLI

W, H = 1080, 1350
BASE = os.path.dirname(os.path.abspath(__file__))
SERIF = os.path.join(BASE, "font", "PlayfairDisplay.ttf")
ITALIC = os.path.join(BASE, "font", "PlayfairDisplay-Italic.ttf")
SYM = os.path.join(BASE, "font", "DejaVuSans.ttf")
GREEN, CREAM, GOLD, INK = "#1d2c22", "#f4efe4", "#c9a45c", "#1b1b1b"
HANDLE = "@leregoledelgentleman"


def font(path, size, wght=None):
    f = ImageFont.truetype(path, size)
    if wght:
        try:
            f.set_variation_by_axes([wght])
        except Exception:
            pass
    return f


def wrap(d, text, f, maxw):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= maxw:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def block(d, text, f, x, y, maxw, fill, gap=1.18):
    for line in wrap(d, text, f, maxw):
        d.text((x, y), line, font=f, fill=fill)
        y += int(f.size * gap)
    return y


def footer(d, page, dark=False):
    small = font(SERIF, 26)
    col = "#cfc6b0" if dark else "#9c8a63"
    if dark:
        d.text((70, H - 80), HANDLE, font=small, fill=col)
    else:
        tw = d.textlength(HANDLE, font=small)
        d.line((70, H - 66, (W - tw) / 2 - 30, H - 66), fill=GOLD, width=2)
        d.line(((W + tw) / 2 + 30, H - 66, W - 120, H - 66), fill=GOLD, width=2)
        d.text(((W - tw) / 2, H - 82), HANDLE, font=small, fill=col)
    d.text((W - 90, H - 86), str(page), font=font(SERIF, 32), fill=col)


def fleur(d, x, y, size=70):
    d.text((x, y), "⚜", font=font(SYM, size), fill=GOLD, anchor="mm")


def cover(c):
    im = Image.new("RGB", (W, H), GREEN)
    d = ImageDraw.Draw(im)
    num = font(SERIF, 420)
    d.text((90, 380), c["n"], font=num, fill=GOLD)
    nx = 90 + d.textlength(c["n"], font=num) + 30
    y = block(d, c["t"], font(SERIF, 112), nx, 460, W - nx - 70, "#ffffff", 1.05)
    y = max(y, 460 + 420) + 90
    block(d, c["sub"], font(SERIF, 46), 140, y, W - 280, GOLD)
    footer(d, 1, dark=True)
    return im


def intro(c):
    im = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(im)
    d.line((60, 0, 60, H), fill=GOLD, width=3)
    fleur(d, 60, 640, 60)
    fleur(d, W / 2, 150, 90)
    y = block(d, c["big"], font(SERIF, 104), 150, 330, W - 260, INK, 1.12)
    block(d, c["it"], font(ITALIC, 96), 150, y + 30, W - 260, INK, 1.12)
    footer(d, 2)
    return im


def item(c, i, page):
    head, text = c["items"][i]
    im = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(im)
    d.text((W - 110, 120), str(i + 1), font=font(SERIF, 330), fill="#e6dcc5", anchor="ra")
    d.text((110, 160), str(i + 1), font=font(SERIF, 150), fill=GOLD)
    d.line((110, 380, 260, 380), fill=GOLD, width=3)
    y = block(d, head, font(SERIF, 110), 110, 460, W - 220, INK, 1.08)
    block(d, text, font(SERIF, 56), 110, y + 50, W - 220, "#3a3a3a", 1.35)
    footer(d, page)
    return im


def final(c, page):
    im = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(im)
    d.text((W - 60, H / 2), "⚜", font=font(SYM, 700), fill="#ece4d2", anchor="rm")
    fleur(d, 210, 250, 110)
    d.line((140, 330, 280, 330), fill=GOLD, width=2)
    y = block(d, c["save"], font(SERIF, 64), 140, 400, W - 300, INK, 1.25)
    d.line((140, y + 40, 260, y + 40), fill=GOLD, width=2)
    y = block(d, c["q"], font(SERIF, 64), 140, y + 100, W - 300, INK, 1.25)
    y = block(d, "Scrivilo nei commenti.", font(SERIF, 64), 140, y, W - 300, INK, 1.25)
    d.text((140, y + 110), "Bonne soirée, signori", font=font(SERIF, 84), fill=GOLD)
    footer(d, page)
    return im


def main():
    start = dt.date.fromisoformat(sys.argv[1] if len(sys.argv) > 1 else "2026-11-13")
    caps = {}
    for k, c in enumerate(CAROSELLI):
        day = (start + dt.timedelta(days=k)).isoformat()
        out = os.path.join(BASE, day)
        os.makedirs(out, exist_ok=True)
        slides = [cover(c), intro(c)] + [item(c, i, 3 + i) for i in range(3)] + [final(c, 6)]
        for j, s in enumerate(slides, 1):
            s.save(os.path.join(out, f"{j:02d}.jpg"), quality=92)
        caps[day] = {"titolo": f'{c["n"]} {c["t"]}', "slide": len(slides), "didascalia": c["cap"]}
    json.dump(caps, open(os.path.join(BASE, "didascalie.json"), "w"), ensure_ascii=False, indent=1)
    print(len(caps), "caroselli")


if __name__ == "__main__":
    main()
