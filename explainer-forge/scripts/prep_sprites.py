#!/usr/bin/env python3
"""Prepare generated sprites for the page: trim to the alpha bounding box, size to the largest on-screen height, save WebP.

  python3 prep_sprites.py --src raw --out img --heights sprites.json [--zoom 1.6] [--quality 88] [--alpha-threshold 24]
  python3 prep_sprites.py --src raw --out img --height parcel=380 --height scanner=420

--src: transparent PNGs, one per object (file stem = sprite name). --heights: JSON {"heights": {"name": px}} (or a bare
{name: px} map) giving the LARGEST height the sprite ever shows on the 1920x1080 stage, camera zoom not included.
The page is sized at height x --zoom (default 1.6) so a close-up camera stays sharp; a sprite already smaller is kept.
Alpha under the threshold is ignored when finding the bounding box (stray faint pixels would otherwise leave a margin
and make the sprite's "bottom edge" float above the ground). The page computes each aspect ratio from the WebP itself.
Only files named in the height table are processed; --all also takes every PNG in --src at --default-height.
Needs Pillow. Prints name, size, aspect ratio and file size, and exits 1 if a named sprite is missing.
"""
import argparse
import json
import os
import sys

from PIL import Image


def trim_resize(im, max_h, thr=24):
    """-> RGBA image cropped to the alpha bbox, downscaled to max_h tall if larger (never upscaled)."""
    im = im.convert("RGBA")
    mask = im.getchannel("A").point(lambda v: 255 if v > thr else 0)
    box = mask.getbbox()
    if not box:
        raise ValueError("fully transparent image")
    im = im.crop(box)
    if im.height > max_h:
        im = im.resize((max(1, round(im.width * max_h / im.height)), max_h), Image.LANCZOS)
    return im


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--heights", help="JSON height table")
    ap.add_argument("--height", action="append", default=[], help="name=px (repeatable)")
    ap.add_argument("--zoom", type=float, default=1.6, help="largest camera zoom the sprite is seen at")
    ap.add_argument("--quality", type=int, default=88)
    ap.add_argument("--alpha-threshold", type=int, default=24)
    ap.add_argument("--all", action="store_true", help="also process every PNG in --src not in the table")
    ap.add_argument("--default-height", type=int, default=400)
    a = ap.parse_args(argv)
    table = {}
    if a.heights:
        d = json.load(open(a.heights))
        table.update(d.get("heights", d))
    for kv in a.height:
        k, _, v = kv.partition("=")
        table[k] = int(v)
    if a.all:
        for f in sorted(os.listdir(a.src)):
            if f.lower().endswith(".png") and os.path.splitext(f)[0] not in table:
                table[os.path.splitext(f)[0]] = a.default_height
    if not table:
        ap.error("no sprites named: give --heights, --height or --all")
    os.makedirs(a.out, exist_ok=True)
    missing = 0
    for name, h in table.items():
        if name.startswith("_"):
            continue
        src = os.path.join(a.src, name + ".png")
        if not os.path.exists(src):
            print("MISSING", src)
            missing += 1
            continue
        im = trim_resize(Image.open(src), round(h * a.zoom), a.alpha_threshold)
        dst = os.path.join(a.out, name + ".webp")
        im.save(dst, "WEBP", quality=a.quality, method=6)
        print(f"{name:<18} {im.width}x{im.height}  aspect {im.width / im.height:.3f}  {os.path.getsize(dst) // 1024} KB")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
