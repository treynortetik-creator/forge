"""Line weight of the DEFINING lines at game size, before / after a line-darkening bake (the brief was: darker defining lines, NOT thicker).
  python3 -I linewidth.py <sprite.png> <frame.ln.png (raw, super-sampled, from bake_sprites.py --line-pass)> <super> <game scale> [--ref label]
Support = cells whose area-averaged line coverage > 0.15. Darkness D = (paper - L) / (paper - ink) of the sprite composited on the paper floor (BG constant below = our floor colour; edit it to yours), resampled to game size (premultiplied bilinear).
Width = mean full width at half maximum (px at game size) of the line's D profile above its local floor (min within 8 px each side) over every ridge pixel in the support (transect along the steeper axis); also prints the mean line contrast (peak minus floor, the value)."""
import sys, numpy as np
from PIL import Image
BG = np.array([205, 191, 164.])
def load(sprite, ln, sup, k):
    a = np.array(Image.open(sprite).convert('RGBA')).astype(np.float64)
    al = a[..., 3:] / 255
    comp = a[..., :3] * al + BG * (1 - al)
    L = comp @ np.array([0.299, 0.587, 0.114])
    l = np.array(Image.open(ln).convert('RGBA'))[..., 3].astype(np.float64) / 255
    h, w = L.shape; lc = l[:h * sup, :w * sup].reshape(h, sup, w, sup).mean((1, 3))
    if k != 1:
        sz = (round(w * k), round(h * k))
        L = np.array(Image.fromarray(L.astype(np.float32), 'F').resize(sz, Image.BILINEAR)); lc = np.array(Image.fromarray(lc.astype(np.float32), 'F').resize(sz, Image.BILINEAR))
    return L, lc
def measure(L, lc):
    paper, ink = 205.0, 20.0
    D = np.clip((paper - L) / (paper - ink), 0, 1)
    sup_ = lc > 0.15
    gy, gx = np.gradient(D)
    ws = []; vals = []
    H, W = D.shape
    for y in range(2, H - 2):
        for x in range(2, W - 2):
            if not sup_[y, x] or D[y, x] < 0.2: continue
            if abs(gx[y, x]) >= abs(gy[y, x]): line = D[y, :]; i = x; n = W
            else: line = D[:, x]; i = y; n = H
            if not (line[i] >= line[i - 1] and line[i] >= line[i + 1]): continue
            win = 8
            seg = line[max(0, i - win):i + win + 1]
            pk = line[i]; base = max(seg[:min(len(seg), win)].min() if len(seg) else 0, 0); lo_b = line[max(0, i - win):i + 1].min(); hi_b = line[i:i + win + 1].min(); base = max(lo_b, hi_b)
            if pk - base < 0.12: continue
            hm = base + (pk - base) / 2
            lo = i
            while lo > 0 and line[lo - 1] >= hm and i - lo < win: lo -= 1
            hi = i
            while hi < n - 1 and line[hi + 1] >= hm and hi - i < win: hi += 1
            fl = lo - (line[lo] - hm) / max(line[lo] - line[lo - 1], 1e-6) if lo > 0 else lo
            fh = hi + (line[hi] - hm) / max(line[hi] - line[hi + 1], 1e-6) if hi < n - 1 else hi
            ws.append(fh - fl + 1 - 1); vals.append(pk - base)
    return dict(ridge_px=len(ws), fwhm_px=round(float(np.mean(ws)), 3), mean_line_contrast=round(float(np.mean(vals)), 3), line_pixels=int(sup_.sum()))
if __name__ == '__main__':
    if len(sys.argv) < 5 or sys.argv[1] in ('-h', '--help'):
        print(__doc__); sys.exit(0 if len(sys.argv) > 1 and sys.argv[1] in ('-h', '--help') else 2)
    sprite, ln, sup, k = sys.argv[1], sys.argv[2], int(sys.argv[3]), float(sys.argv[4])
    L, lc = load(sprite, ln, sup, k)
    print(measure(L, lc))
