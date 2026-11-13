#!/usr/bin/env python3
"""Cut a flat-grey-background source image to RGBA (border flood-fill), for image-to-3D input.

Usage:  python3 -I cut_grey_bg.py <in.png> <out.png> [R G B] [tol]
  R G B  the exact flat background colour (default 191 191 191, i.e. #BFBFBF)
  tol    max per-channel distance counted as background (default 6)

Why not a threshold matte or an alpha channel from the image generator: a generator's alpha is
often opaque noise (not a matte), and a background left in becomes GEOMETRY in the 3D model.
This floods inward from the image border only, so a grey that appears INSIDE the object is
kept unless it is an enclosed pocket of the exact background colour (> 200 px), which is
treated as background too (the gap between an arm and a torso, a handle loop).
Needs numpy, pillow, scipy.
"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

src, dst = sys.argv[1:3]
bg = np.array([int(v) for v in sys.argv[3:6]] if len(sys.argv) >= 6 else [191, 191, 191])
tol = int(sys.argv[6]) if len(sys.argv) >= 7 else 6

a = np.array(Image.open(src).convert("RGB")).astype(int)
near = np.abs(a - bg).max(axis=2) <= tol
lab, n = ndi.label(near)
border = set(lab[0, :]) | set(lab[-1, :]) | set(lab[:, 0]) | set(lab[:, -1])
border.discard(0)
m = np.isin(lab, list(border))
# enclosed pockets that are the exact background colour and sizeable are background too
rest = near & ~m
lab2, n2 = ndi.label(rest)
for i in range(1, n2 + 1):
    reg = lab2 == i
    if reg.sum() > 200 and np.abs(a[reg] - bg).max() <= 2:
        m |= reg
alpha = (~m).astype(np.uint8) * 255
alpha = ndi.binary_opening(alpha > 0, iterations=1) * 255
Image.fromarray(np.dstack([a.astype(np.uint8), alpha.astype(np.uint8)]), "RGBA").save(dst)
print(dst, "foreground fraction", round(float((alpha > 0).mean()), 3))
