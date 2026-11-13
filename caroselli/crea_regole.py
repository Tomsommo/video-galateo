#!/usr/bin/env python3
"""Crea le immagini della «regola del giorno» (1080x1350): regole/AAAA-MM-GG.jpg"""
import datetime as dt, json, os, sys
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(__file__))
from crea import W, H, BASE, SERIF, ITALIC, GOLD, INK, CREAM, font, block, footer, fleur
from regole import REGOLE


def slide(titolo, testo):
    im = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(im)
    d.rectangle((40, 40, W - 40, H - 130), outline=GOLD, width=2)
    fleur(d, W / 2, 190, 90)
    lab = "LA REGOLA DEL GIORNO"
    f = font(SERIF, 30)
    d.text(((W - d.textlength(lab, font=f)) / 2, 270), lab, font=f, fill=GOLD)
    y = block(d, titolo, font(SERIF, 104), 110, 420, W - 220, INK, 1.12)
    d.line((110, y + 40, 260, y + 40), fill=GOLD, width=3)
    block(d, testo, font(ITALIC, 58), 110, y + 100, W - 220, "#3a3a3a", 1.3)
    footer(d, "")
    return im


def main():
    start = dt.date.fromisoformat(sys.argv[1] if len(sys.argv) > 1 else "2026-11-15")
    out = os.path.join(BASE, "regole"); os.makedirs(out, exist_ok=True)
    caps = {}
    for k, (t, s, c) in enumerate(REGOLE):
        day = (start + dt.timedelta(days=k)).isoformat()
        slide(t, s).save(os.path.join(out, f"{day}.jpg"), quality=92)
        caps[day] = c
    json.dump(caps, open(os.path.join(out, "didascalie.json"), "w"), ensure_ascii=False, indent=1)
    print(len(caps))


if __name__ == "__main__":
    main()
