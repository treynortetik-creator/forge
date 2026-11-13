#!/usr/bin/env python3
"""palette-audit.py: measure how much of a screenshot is OFF palette. A number, not an impression.

  python3 -I palette-audit.py <folder-of-pngs | a.png b.png ...> --palette palette.json [--limit 0.5] [--strict] [--out DIR]

palette.json (see palette.example.json):
  ramp           ordered list of neutral tokens (dark to light). On palette = within token_de (Lab) of the POLYLINE
                 through them, not just of the points: anti-aliased pixels between two tokens are not violations.
  exempt         {name: "#hex"} colours that are allowed (hero / faction / power colours). A pixel is exempt when its
                 Lab hue is within hue_tol degrees of the reference AND its chroma is at least chroma_frac of the
                 reference's chroma. (So a glow that fades through mid chroma IS flagged: fade it by alpha, not by tint.)
  named_ramps    optional {name: [hex, ...]} extra polylines that are also on palette (a skin ramp, a metal ramp).
  chroma_min     below this Lab chroma a pixel is a neutral and never off palette (default 12)
  hue_tol 14, token_de 9, chroma_frac 0.6, warm_hue [30, 68] (degrees), warm_limit_pct 0.5, limit_pct 0.5

Per image: off_palette_pct and warm_pct (share of orange/amber pixels off the ramp: a budget for fire effects).
Optional <name>.mask.json next to a shot: {"rects": [[x, y, w, h], ...]} excluded from the count (portraits, UI
that has its own rules). Writes <out>/heat-<name>.png (dimmed shot, off-palette pixels in red) and <out>/audit.json.
Exit 1 with --strict when any shot is over --limit or warm_limit_pct. Needs Pillow and numpy.
Why Lab: a hex distance in RGB flags blue-ish darks that look neutral; Lab distance matches what the eye calls "a different colour".
"""
import argparse, json, math, sys
from pathlib import Path

import numpy as np
from PIL import Image


def hex_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def srgb_to_lab(rgb):
    c = rgb.astype(np.float64) / 255.0
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    m = np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750], [0.0193339, 0.1191920, 0.9503041]])
    xyz = (c @ m.T) / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 216 / 24389, np.cbrt(xyz), (24389 / 27 * xyz + 16) / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], axis=-1)


def lab_of(h):
    return srgb_to_lab(np.array([[hex_rgb(h)]], dtype=np.uint8))[0, 0]


def polyline_dist(lab, pts):
    """Lab distance of every pixel to the polyline through pts (nearest point on any segment)."""
    best = np.full(lab.shape[:-1], 1e9)
    for a, b in zip(pts[:-1], pts[1:]):
        ab = b - a
        t = np.clip(((lab - a) @ ab) / max(ab @ ab, 1e-9), 0, 1)
        best = np.minimum(best, np.sqrt(((lab - (a + t[..., None] * ab)) ** 2).sum(-1)))
    return best


class Palette:
    def __init__(self, cfg):
        self.chroma_min = cfg.get('chroma_min', 12.0)
        self.hue_tol = cfg.get('hue_tol', 14.0)
        self.token_de = cfg.get('token_de', 9.0)
        self.chroma_frac = cfg.get('chroma_frac', 0.6)
        self.warm = cfg.get('warm_hue', [30.0, 68.0])
        self.warm_limit = cfg.get('warm_limit_pct', 0.5)
        self.ramps = [[lab_of(h) for h in cfg['ramp']]] + [[lab_of(h) for h in r] for r in cfg.get('named_ramps', {}).values()]
        self.exempt = []
        for name, h in cfg.get('exempt', {}).items():
            L, a, b = lab_of(h)
            self.exempt.append((name, math.degrees(math.atan2(b, a)) % 360, math.hypot(a, b)))

    def analyse(self, img):
        rgb = np.asarray(img.convert('RGB'))
        lab = srgb_to_lab(rgb)
        chroma = np.hypot(lab[..., 1], lab[..., 2])
        hue = np.degrees(np.arctan2(lab[..., 2], lab[..., 1])) % 360
        colourful = chroma > self.chroma_min
        exempt = np.zeros(chroma.shape, bool)
        for _, h, c in self.exempt:
            d = np.abs((hue - h + 180) % 360 - 180)
            exempt |= (d <= self.hue_tol) & (chroma >= self.chroma_frac * c)
        on_pal = np.zeros(chroma.shape, bool)
        for r in self.ramps:
            on_pal |= polyline_dist(lab, r) <= self.token_de
        off = colourful & ~exempt & ~on_pal
        warm = colourful & (hue >= self.warm[0]) & (hue <= self.warm[1]) & ~on_pal
        return rgb, off, warm


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('paths', nargs='+')
    ap.add_argument('--palette', required=True)
    ap.add_argument('--limit', type=float, default=None, help='max off-palette %% per shot (default: palette limit_pct or 0.5)')
    ap.add_argument('--strict', action='store_true')
    ap.add_argument('--out', help='output folder (default: <first path folder>/audit)')
    a = ap.parse_args()
    cfg = json.load(open(a.palette))
    pal = Palette(cfg)
    limit = a.limit if a.limit is not None else cfg.get('limit_pct', 0.5)
    files = []
    for p in a.paths:
        pp = Path(p)
        files += sorted(x for x in pp.glob('*.png') if x.parent.name != 'audit') if pp.is_dir() else [pp]
    if not files:
        sys.exit('no images')
    out = Path(a.out) if a.out else files[0].parent / 'audit'
    out.mkdir(parents=True, exist_ok=True)
    rows, bad = [], 0
    for p in files:
        img = Image.open(p)
        rgb, off, warm = pal.analyse(img)
        masked = np.zeros(off.shape, bool)
        mk = p.with_name(p.stem + '.mask.json')
        if mk.exists():
            for x, y, w, h in json.loads(mk.read_text()).get('rects', []):
                masked[max(0, y):max(0, y + h), max(0, x):max(0, x + w)] = True
        valid = ~masked
        n = int(valid.sum()) or 1
        row = {'file': p.name, 'size': list(img.size), 'off_palette_pct': round(100.0 * int((off & valid).sum()) / n, 4),
               'warm_pct': round(100.0 * int((warm & valid).sum()) / n, 4), 'masked_px': int(masked.sum())}
        row['pass'] = row['off_palette_pct'] < limit and row['warm_pct'] < pal.warm_limit
        bad += not row['pass']
        heat = (rgb.astype(np.float64) * 0.35).astype(np.uint8)
        heat[off & valid] = (255, 0, 0)
        heat[masked] = (heat[masked] * 0.5).astype(np.uint8)
        Image.fromarray(heat).save(out / f'heat-{p.name}')
        rows.append(row)
        print(f"{p.name:<44} off {row['off_palette_pct']:7.3f}%  warm {row['warm_pct']:7.3f}%  {'PASS' if row['pass'] else 'FAIL'}")
    (out / 'audit.json').write_text(json.dumps({'limit_pct': limit, 'warm_limit_pct': pal.warm_limit, 'shots': rows}, indent=1))
    print(f'{len(rows)} shot(s), {bad} over limit ({limit}% off palette, {pal.warm_limit}% warm). Heatmaps in {out}')
    return 1 if (a.strict and bad) else 0


if __name__ == '__main__':
    sys.exit(main())
