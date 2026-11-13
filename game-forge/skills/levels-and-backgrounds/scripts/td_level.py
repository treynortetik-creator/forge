#!/usr/bin/env python3
"""td_level.py: check and draw a tower-defense level kept as data (paths + build pads + waves), before any art or balance work.

  python3 td_level.py check level.json [--range 150] [--max-range 300]    # lint: pad/road distances, pad spacing, path ends, waves
  python3 td_level.py guide level.json guide.png [--scale 1] [--road 70]   # the painter's trace guide: road, pads, castle, hero start, HUD keep-clear zones
level.json: {"map": {"width": 1920, "height": 1080},
             "paths": [{"id": "main", "points": [[x, y], ...], "smooth": true}],
             "buildSpots": [{"id": "s1", "x": 57, "y": 860}],
             "castle": [x, y], "heroSpawn": [x, y],
             "waves": [{"groups": [{"enemy": "x", "count": 5, "path": "main"}]}]}      (waves optional)
Road = the Catmull-Rom curve through the control points, 10 samples per segment (uniform), like the engine this was lifted from; "smooth": false keeps
the polyline. The distance rules mirror the engine's validator: error when a pad is farther from every road than --max-range (nothing can reach
it), warn above 160 px (tier-1 towers reach ~150), warn under 40 px (pad sits on the road), warn when two pads are closer than 70 px, warn when a
path ends more than 120 px from the castle, warn when a campaign level has fewer than 12 or more than 20 waves. Those thresholds are that game's
numbers: change them with the flags / constants for yours. The guide's keep-clear zones (top-left 640x60, top-right 260x90, bottom-left 420x160
on a 1920x1080 map) are that game's HUD; edit KEEP_CLEAR. Exit 1 on any error.  `check` is stdlib only; `guide` needs Pillow.
"""
import json, math, sys

KEEP_CLEAR = [(0, 0, 640, 60), (1660, 0, 1920, 90), (0, 920, 420, 1080)]   # x0, y0, x1, y1 on a 1920x1080 map


def catmull(pts, samples=10):
    if len(pts) < 3:
        return [tuple(p) for p in pts]
    out = []
    for i in range(len(pts) - 1):
        p0, p1, p2, p3 = pts[max(0, i - 1)], pts[i], pts[i + 1], pts[min(len(pts) - 1, i + 2)]
        for k in range(samples):
            t = k / samples; t2 = t * t; t3 = t2 * t
            out.append(tuple(0.5 * (2 * p1[a] + (-p0[a] + p2[a]) * t + (2 * p0[a] - 5 * p1[a] + 4 * p2[a] - p3[a]) * t2 + (-p0[a] + 3 * p1[a] - 3 * p2[a] + p3[a]) * t3) for a in (0, 1)))
    out.append(tuple(pts[-1]))
    return out


def road(path):
    return catmull(path['points']) if path.get('smooth', True) else [tuple(p) for p in path['points']]


def seg_dist(px, py, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = dx * dx + dy * dy
    t = 0 if L == 0 else max(0, min(1, ((px - a[0]) * dx + (py - a[1]) * dy) / L))
    return math.hypot(px - (a[0] + t * dx), py - (a[1] + t * dy))


def nearest(roads, x, y):
    best = None
    for pid, pts in roads.items():
        for a, b in zip(pts, pts[1:]):
            d = seg_dist(x, y, a, b)
            if best is None or d < best[0]:
                best = (d, pid)
    return best


def length_within(pts, x, y, r, step=4.0):
    """arc length of a road that lies within r of (x, y), sampled every `step` px"""
    tot = 0.0
    for a, b in zip(pts, pts[1:]):
        seg = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(1, int(seg / step))
        for k in range(n):
            m = ((a[0] + (b[0] - a[0]) * (k + .5) / n), (a[1] + (b[1] - a[1]) * (k + .5) / n))
            if math.hypot(m[0] - x, m[1] - y) <= r:
                tot += seg / n
    return tot


def check(lv, rng, max_rng):
    errs, warns = [], []
    W, H = lv['map']['width'], lv['map']['height']
    roads = {p['id']: road(p) for p in lv['paths']}
    ids = set(roads)
    for p in lv['paths']:
        if len(p['points']) < 2:
            errs.append(f"path {p['id']}: needs >= 2 points")
    spots = lv.get('buildSpots', [])
    for s in spots:
        w = f"spot {s['id']}"
        if not (0 <= s['x'] <= W and 0 <= s['y'] <= H):
            errs.append(f'{w}: outside the map')
        d, pid = nearest(roads, s['x'], s['y'])
        cover = {q: length_within(pts, s['x'], s['y'], rng) for q, pts in roads.items()}
        cov = ', '.join(f'{q} {v:.0f}px' for q, v in cover.items() if v > 0) or 'none'
        if d > max_rng:
            errs.append(f'{w}: unreachable, nearest road {d:.0f}px away (max range {max_rng})')
        elif d > 160:
            warns.append(f'{w}: {d:.0f}px from the road (tier-1 reach ~{rng})')
        if d < 40:
            warns.append(f'{w}: overlaps the road ({d:.0f}px)')
        for o in spots:
            if o is not s and s['id'] < o['id'] and math.hypot(o['x'] - s['x'], o['y'] - s['y']) < 70:
                warns.append(f"{w}: too close to {o['id']}")
        print(f"  {s['id']:>4}  road {pid} at {d:5.0f}px   road length in range {rng}: {cov}")
    if 'castle' in lv:
        for pid, pts in roads.items():
            e = pts[-1]
            if math.hypot(e[0] - lv['castle'][0], e[1] - lv['castle'][1]) > 120:
                warns.append(f'path {pid}: does not end near the castle')
    if 'heroSpawn' in lv and not (0 <= lv['heroSpawn'][0] <= W and 0 <= lv['heroSpawn'][1] <= H):
        errs.append('heroSpawn outside the map')
    waves = lv.get('waves')
    if waves is not None:
        if not waves:
            errs.append('needs waves')
        elif not 12 <= len(waves) <= 20:
            warns.append(f'{len(waves)} waves (the design target was 12-20)')
        for i, wv in enumerate(waves, 1):
            if not wv.get('groups'):
                errs.append(f'wave {i}: no groups')
            for g in wv.get('groups', []):
                if g['path'] not in ids:
                    errs.append(f"wave {i}: missing path '{g['path']}'")
                if g['count'] < 1:
                    errs.append(f'wave {i}: group count must be >= 1')
    for e in errs:
        print('ERROR', e)
    for w in warns:
        print('warn ', w)
    print(f'{len(errs)} errors, {len(warns)} warnings')
    return 1 if errs else 0


def guide(lv, out, scale=1.0, road_w=70):
    from PIL import Image, ImageDraw
    W, H = lv['map']['width'], lv['map']['height']
    im = Image.new('RGB', (int(W * scale), int(H * scale)), (24, 28, 40))
    d = ImageDraw.Draw(im, 'RGBA')
    S = lambda p: (p[0] * scale, p[1] * scale)
    for (x0, y0, x1, y1) in KEEP_CLEAR:
        d.rectangle([x0 * scale, y0 * scale, x1 * scale, y1 * scale], fill=(255, 0, 0, 50), outline=(255, 80, 80, 160))
    cols = [(210, 180, 120), (120, 190, 210), (200, 140, 200), (140, 210, 140)]
    for k, p in enumerate(lv['paths']):
        pts = [S(q) for q in road(p)]
        d.line(pts, fill=cols[k % 4] + (150,), width=int(road_w * scale), joint='curve')
        d.line(pts, fill=(255, 255, 255, 200), width=2)
        for q in p['points']:
            r = 5 * scale
            d.ellipse([q[0] * scale - r, q[1] * scale - r, q[0] * scale + r, q[1] * scale + r], outline=(255, 255, 255, 255))
        d.text(S(p['points'][0]), p['id'], fill=(255, 255, 255, 255))
    for s in lv.get('buildSpots', []):
        r = 26 * scale
        d.ellipse([s['x'] * scale - r, s['y'] * scale - r, s['x'] * scale + r, s['y'] * scale + r], fill=(255, 215, 0, 110), outline=(255, 215, 0, 255), width=2)
        d.text((s['x'] * scale - 8, s['y'] * scale - 6), s['id'], fill=(255, 255, 255, 255))
    if 'castle' in lv:
        c = S(lv['castle']); d.rectangle([c[0] - 30, c[1] - 30, c[0] + 30, c[1] + 30], outline=(255, 60, 60, 255), width=3); d.text((c[0] - 14, c[1] - 6), 'castle', fill=(255, 255, 255, 255))
    if 'heroSpawn' in lv:
        h = S(lv['heroSpawn']); d.ellipse([h[0] - 8, h[1] - 8, h[0] + 8, h[1] + 8], fill=(80, 255, 120, 255)); d.text((h[0] + 10, h[1] - 6), 'hero', fill=(255, 255, 255, 255))
    im.save(out)
    print('guide ->', out, im.size)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] in ('-h', '--help'):
        print(__doc__); sys.exit(0)
    a = sys.argv[1:]
    fl = lambda n, dflt: float(a[a.index(n) + 1]) if n in a else dflt
    if len(a) >= 2 and a[0] == 'check':
        sys.exit(check(json.load(open(a[1])), fl('--range', 150), fl('--max-range', 300)))
    elif len(a) >= 3 and a[0] == 'guide':
        guide(json.load(open(a[1])), a[2], fl('--scale', 1), fl('--road', 70))
    else:
        print(__doc__)
        sys.exit(2)
