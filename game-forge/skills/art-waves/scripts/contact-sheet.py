#!/usr/bin/env python3
"""Labelled contact sheet: every cell carries its name burned in (never show an unlabelled lineup).
usage: contact-sheet.py --out review/x.png --title "Heroes" --cols 3 --cell 640x480 [--bg checker|night] [--nearest] files...
Label = file stem (or 'label=path', e.g. 'BEFORE=a.png' 'AFTER=b.png'). --bg checker shows real transparency.
Needs Pillow only."""
import argparse, pathlib
from PIL import Image, ImageDraw, ImageFont

FONTS = ["/System/Library/Fonts/Supplemental/Georgia Bold.ttf", "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
         "/Library/Fonts/Arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/System/Library/Fonts/Helvetica.ttc"]


def font(sz):
    for f in FONTS:
        if pathlib.Path(f).exists():
            return ImageFont.truetype(f, sz)
    return ImageFont.load_default()


def checker(w, h, s=16):
    im = Image.new("RGB", (w, h), (38, 44, 66))
    d = ImageDraw.Draw(im)
    for y in range(0, h, s):
        for x in range(0, w, s):
            if (x // s + y // s) % 2:
                d.rectangle([x, y, x + s - 1, y + s - 1], fill=(48, 56, 82))
    return im


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--out", required=True)
    a.add_argument("--title", default="")
    a.add_argument("--cols", type=int, default=3)
    a.add_argument("--cell", default="640x480")
    a.add_argument("--bg", default="night")
    a.add_argument("--nearest", action="store_true", help="nearest-neighbour upscale (pixel review)")
    a.add_argument("files", nargs="+")
    o = a.parse_args()
    cw, ch = map(int, o.cell.split("x"))
    items = []
    for f in o.files:
        if "=" in f and not pathlib.Path(f).exists():
            lab, p = f.split("=", 1)
        else:
            lab, p = pathlib.Path(f).stem, f
        items.append((lab, p))
    rows = (len(items) + o.cols - 1) // o.cols
    pad, lab_h, top = 12, 30, (60 if o.title else 12)
    W = o.cols * (cw + pad) + pad
    H = top + rows * (ch + lab_h + pad) + pad
    sheet = Image.new("RGB", (W, H), (11, 16, 32))
    d = ImageDraw.Draw(sheet)
    if o.title:
        d.text((pad, 14), o.title, font=font(30), fill=(242, 163, 58))
    for i, (lab, p) in enumerate(items):
        r, c = divmod(i, o.cols)
        x = pad + c * (cw + pad)
        y = top + r * (ch + lab_h + pad)
        bg = checker(cw, ch) if o.bg == "checker" else Image.new("RGB", (cw, ch), (20, 26, 51))
        im = Image.open(p).convert("RGBA")
        sc = min(cw / im.width, ch / im.height)
        if o.nearest:
            sc = max(1, int(sc)) if sc >= 1 else sc
        nw, nh = max(1, int(im.width * sc)), max(1, int(im.height * sc))
        im = im.resize((nw, nh), Image.NEAREST if o.nearest else Image.LANCZOS)
        bg.paste(im, ((cw - nw) // 2, (ch - nh) // 2), im)
        sheet.paste(bg, (x, y))
        d.text((x + 4, y + ch + 4), lab, font=font(18), fill=(201, 212, 232))
    pathlib.Path(o.out).parent.mkdir(parents=True, exist_ok=True)
    sheet.save(o.out)
    print(o.out, sheet.size)


if __name__ == "__main__":
    main()
