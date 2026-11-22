#!/usr/bin/env python3
"""Draw five neutral, clay-ish placeholder sprites into <out>/ (transparent PNG) so the example builds with no image
model and no assets. Real projects replace these with generated sprites (see ../sprites/README.md).
  python3 make_placeholder_sprites.py --out raw        needs Pillow"""
import argparse
import os
import random

from PIL import Image, ImageDraw, ImageFilter

S = 4  # supersample


def clay(w, h, base, radius, shade=0.18):
    """A rounded block with a soft top light, a darker bottom edge and fine noise, on a transparent canvas."""
    W, H = w * S, h * S
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, W - 1, H - 1], radius=radius * S, fill=255)
    body = Image.new("RGBA", (W, H), base + (255,))
    d = ImageDraw.Draw(body)
    for y in range(H):
        k = y / H
        c = tuple(int(max(0, min(255, v * (1 + shade * (0.5 - k) * 2)))) for v in base)
        d.line([(0, y), (W, y)], fill=c + (255,))
    hl = Image.new("L", (W, H), 0)
    ImageDraw.Draw(hl).ellipse([W * .08, H * .04, W * .6, H * .34], fill=70)
    body.paste(Image.new("RGBA", (W, H), (255, 255, 255, 255)), (0, 0), hl.filter(ImageFilter.GaussianBlur(W * .05)))
    rnd = random.Random(7)
    px = body.load()
    for _ in range(W * H // 40):
        x, y = rnd.randrange(W), rnd.randrange(H)
        r, g, b, a = px[x, y]
        v = rnd.randint(-10, 10)
        px[x, y] = (max(0, min(255, r + v)), max(0, min(255, g + v)), max(0, min(255, b + v)), a)
    im.paste(body, (0, 0), mask)
    return im


def done(im, path, size):
    im.resize(size, Image.LANCZOS).save(path)
    print("wrote", path, size)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    P = lambda n: os.path.join(a.out, n + ".png")
    parcel = clay(400, 300, (205, 160, 104), 56)
    d = ImageDraw.Draw(parcel)
    d.rectangle([160 * S, 0, 240 * S, 300 * S], fill=(176, 130, 80, 255))        # tape
    d.rounded_rectangle([250 * S, 190 * S, 370 * S, 260 * S], radius=10 * S, fill=(246, 240, 228, 255))   # label
    for i in range(4):
        d.rectangle([(262 + i * 24) * S, 202 * S, (272 + i * 24) * S, 248 * S], fill=(60, 56, 52, 255))
    m = Image.new("L", parcel.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, parcel.width - 1, parcel.height - 1], radius=56 * S, fill=255)
    parcel.putalpha(Image.composite(parcel.getchannel("A"), Image.new("L", parcel.size, 0), m))
    done(parcel, P("parcel"), (400, 300))
    sc = Image.new("RGBA", (360 * S, 420 * S), (0, 0, 0, 0))
    arch = clay(360, 420, (118, 134, 148), 80)
    cut = Image.new("L", arch.size, 255)
    ImageDraw.Draw(cut).rounded_rectangle([70 * S, 140 * S, 290 * S, 420 * S + 200], radius=50 * S, fill=0)
    arch.putalpha(Image.composite(arch.getchannel("A"), Image.new("L", arch.size, 0), cut))
    ImageDraw.Draw(arch).ellipse([150 * S, 60 * S, 210 * S, 120 * S], fill=(232, 90, 64, 255))
    sc.alpha_composite(arch)
    done(sc, P("scanner"), (360, 420))
    done(clay(300, 220, (94, 127, 78), 40), P("bin-a"), (300, 220))
    done(clay(300, 200, (196, 83, 59), 40), P("bin-b"), (300, 200))
    done(clay(200, 40, (112, 119, 138), 14), P("slat"), (200, 40))


if __name__ == "__main__":
    main()
