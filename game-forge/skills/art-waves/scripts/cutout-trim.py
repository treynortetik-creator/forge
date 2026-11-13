#!/usr/bin/env python3
"""cutout-trim.py: turn a returned image-model picture into a game-ready cut-out. Alpha, trim, pad, fit to a cell.

  python3 -I cutout-trim.py IN [IN ...] --out DIR [--bg auto|none|#RRGGBB] [--tol 16] [--pad 4]
        [--cell 256x256] [--anchor-y 0.85] [--height 200] [--max-side 192] [--webp]

Steps, per image (each can be skipped):
  1. BACKGROUND -> ALPHA (--bg auto, default): the flat background colour is the median of the image border; every pixel
     within --tol (max channel difference) of it AND connected to the border becomes transparent. Only border-connected
     pixels go, so paper trapped inside the figure (between an arm and the body) stays until you ask for it
     (--holes N removes enclosed patches of true background colour of at least N px). The edge is soft (ramps over ~46
     levels of colour distance) and the background colour is unmixed from the fringe, so no cream/grey halo shows over a
     dark scene. --bg none keeps the existing alpha (real transparent PNGs from the model); --bg '#BFBFBF' forces the colour.
  2. TRIM to the alpha bounding box, plus --pad transparent pixels.
  3. SCALE (premultiplied Lanczos, so no dark fringe): --height N scales the trimmed figure to N px tall (use ONE value
     for every pose of a character so they share a scale); --max-side N caps the longest side.
  4. CELL: --cell WxH centres the figure horizontally (on the alpha centroid of its bottom 12%, which is where the feet
     are, not the cape) and puts the bottom of the figure on --anchor-y (fraction of the cell height). Frames of one
     character then register identically. Prints the anchor to put in your manifest.
Writes <out>/<stem>.png (or .webp with --webp, alpha lossless) and prints one line per file: size in, size out, % transparent,
anchor. Needs Pillow, numpy, scipy. Never modifies the input.
Limits (untested on photos or painterly backgrounds): a background with a gradient or texture needs a larger --tol and may eat
the figure's pale parts. Check every result on a checkerboard at display size (contact-sheet.py --bg checker).
"""
import argparse, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi


def border_connected(cand):
    lab, n = ndi.label(cand)
    if n == 0:
        return np.zeros_like(cand)
    edge = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
    edge = edge[edge > 0]
    return np.isin(lab, edge)


def parse_hex(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32)


def remove_bg(rgb, bg=None, tol=16, holes=0):
    """-> float32 HxWx4 (0..255). bg None = median of the border."""
    a = rgb.astype(np.float32)
    if bg is None:
        border = np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]])
        bg = np.median(border, axis=0)
    d = np.abs(a - bg).max(axis=2)
    reg = border_connected(d <= tol)
    reg = ndi.binary_opening(reg, iterations=1) | ndi.binary_erosion(reg, iterations=2)
    reg = border_connected(reg)
    if holes:
        lab, n = ndi.label(d <= 12)
        if n:
            sizes = ndi.sum(np.ones_like(lab), lab, range(1, n + 1))
            reg |= np.isin(lab, [i + 1 for i, s in enumerate(sizes) if s >= holes])
    alpha = np.ones(d.shape, np.float32)
    alpha[reg] = 0
    near = ndi.binary_dilation(reg, iterations=3) & ~reg
    dd = np.linalg.norm(a - bg, axis=2)
    alpha[near] = np.clip((dd - 10) / 46.0, 0, 1)[near]
    al = np.maximum(alpha, 1e-3)[..., None]
    out = np.clip((a - (1 - alpha[..., None]) * bg) / al, 0, 255)   # unmix the background from the fringe
    out[alpha < 0.02] = 0
    return np.dstack([out, alpha * 255]).astype(np.float32)


def resize_rgba(rgba, size):
    """premultiplied Lanczos resize: no dark or light fringes at the edge."""
    a = rgba[..., 3:4] / 255.0
    pm = np.dstack([rgba[..., :3] * a, rgba[..., 3:4]])
    chans = [np.asarray(Image.fromarray(pm[..., i].astype(np.float32), 'F').resize(size, Image.LANCZOS)) for i in range(4)]
    r = np.dstack(chans)
    al = np.clip(r[..., 3:4], 0, 255)
    rgb = np.where(al > 0.5, np.clip(r[..., :3] / np.maximum(al / 255.0, 1e-3), 0, 255), 0)
    return np.dstack([rgb, al]).astype(np.uint8)


def bbox(arr, thr=3):
    ys, xs = np.where(arr[..., 3] > thr)
    if len(xs) == 0:
        return None
    return xs.min(), ys.min(), xs.max() + 1, ys.max() + 1


def feet_x(arr):
    """alpha centroid x of the bottom 12% of the content (the feet, not the cape)."""
    h = arr.shape[0]
    band = arr[int(h * 0.88):, :, 3].astype(np.float64)
    if band.sum() <= 0:
        return arr.shape[1] / 2
    return float((band.sum(0) * np.arange(arr.shape[1])).sum() / band.sum())


def process(path, a):
    im = Image.open(path)
    has_alpha = im.mode in ('RGBA', 'LA', 'PA') or 'transparency' in im.info
    rgba0 = np.array(im.convert('RGBA'))
    if a.bg == 'none' or (a.bg == 'auto' and has_alpha and (rgba0[..., 3] < 250).mean() > 0.02):
        rgba = rgba0.astype(np.uint8)
    else:
        bgc = None if a.bg == 'auto' else parse_hex(a.bg)
        rgba = remove_bg(rgba0[..., :3], bgc, a.tol, a.holes).astype(np.uint8)
    box = bbox(rgba)
    if box is None:
        print(f'FAIL  {os.path.basename(path)}: nothing left after background removal (raise --tol or check --bg)')
        return False
    x0, y0, x1, y1 = box
    fig = rgba[y0:y1, x0:x1]
    sc = 1.0
    if a.height:
        sc = a.height / fig.shape[0]
    elif a.max_side and max(fig.shape[:2]) > a.max_side:
        sc = a.max_side / max(fig.shape[:2])
    if abs(sc - 1) > 1e-3:
        fig = resize_rgba(fig.astype(np.float32), (max(1, round(fig.shape[1] * sc)), max(1, round(fig.shape[0] * sc))))
    anchor = None
    if a.cell:
        cw, ch = a.cell
        canvas = np.zeros((ch, cw, 4), np.uint8)
        fx = feet_x(fig)
        ox = int(round(cw / 2 - fx))
        oy = int(round(ch * a.anchor_y - fig.shape[0]))
        # paste with clipping; report if the figure is cut
        sx0, sy0 = max(0, -ox), max(0, -oy)
        dx0, dy0 = max(0, ox), max(0, oy)
        w = min(fig.shape[1] - sx0, cw - dx0); h = min(fig.shape[0] - sy0, ch - dy0)
        canvas[dy0:dy0 + h, dx0:dx0 + w] = fig[sy0:sy0 + h, sx0:sx0 + w]
        clipped = (w < fig.shape[1]) or (h < fig.shape[0])
        fig = canvas
        anchor = (0.5, a.anchor_y)
        if clipped:
            print(f'WARN  {os.path.basename(path)}: figure is clipped by the {cw}x{ch} cell (raise the cell or lower --height)')
    elif a.pad:
        fig = np.pad(fig, ((a.pad, a.pad), (a.pad, a.pad), (0, 0)))
    os.makedirs(a.out, exist_ok=True)
    stem = os.path.splitext(os.path.basename(path))[0]
    dest = os.path.join(a.out, stem + ('.webp' if a.webp else '.png'))
    o = Image.fromarray(fig, 'RGBA')
    o.save(dest, **({'lossless': True, 'exact': True} if a.webp else {}))
    transp = (fig[..., 3] < 8).mean()
    print(f'ok    {os.path.basename(path)}  {im.size[0]}x{im.size[1]} -> {o.size[0]}x{o.size[1]}  scale {sc:.3f}  '
          f'transparent {transp:.0%}' + (f'  anchor {anchor}' if anchor else ''))
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('inputs', nargs='+')
    ap.add_argument('--out', required=True)
    ap.add_argument('--bg', default='auto', help="auto | none | #RRGGBB")
    ap.add_argument('--tol', type=int, default=16)
    ap.add_argument('--holes', type=int, default=0, help='also remove enclosed background patches of at least N px')
    ap.add_argument('--pad', type=int, default=4)
    ap.add_argument('--height', type=int)
    ap.add_argument('--max-side', type=int)
    ap.add_argument('--cell', type=lambda s: tuple(int(x) for x in s.lower().split('x')))
    ap.add_argument('--anchor-y', type=float, default=0.85)
    ap.add_argument('--webp', action='store_true')
    a = ap.parse_args()
    ok = all([process(p, a) for p in a.inputs])
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
