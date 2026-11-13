#!/usr/bin/env python3
"""
Pen-writer hand builder (offline). From a font file, write one JSON per "hand" with everything a runtime pen-writer effect
needs, so the game never loads the font itself:

  glyphs   per glyph: advance, the outline as an SVG path (font units, y up), and the PEN STROKES: ordered polylines
           [x, y, r, w, ...] along the glyph's centreline, in writing order. r = the radius a reveal dab needs at that point to
           cover all of the glyph's ink nearest to it (so the dabs cover ~100% of the ink by construction); w = the true half
           width of the stroke there (the nib: shades are wide, hairlines thin). `l` = strokes written at the END of the word
           (i dots, j dots, a separate t cross, accents), as a pen does.
  pairs    "ab" -> [kern, alt glyph for a, alt glyph for b], from HarfBuzz shaping every pair of the charset (kerning and the
           font's contextual alternates), so the runtime lays text out glyph by glyph and keeps every cursive join.
  metrics  upem, ascender, descender, x height, cap height; licence and copyright (the notice travels with the data).

How the strokes are found (raster pipeline):
  1. FreeType renders the glyph unhinted at a size that gives every hand the same x height in pixels (XH_PX).
  2. scikit-image Zhang thinning -> 1 px skeleton; scipy EDT -> half width at every pixel.
  3. The skeleton becomes a graph (end points, junction clusters, edges); short spurs from thick shades are pruned, junctions closer
     than their stroke widths are merged, degree-2 nodes are joined.
  4. Writing order: components left to right (small marks above the letter go last and are deferred to the word end); each component
     starts at its leftmost end point (the cursive entry stroke) and the pen always leaves a junction by the STRAIGHTEST arm (it goes
     through a crossing, as a pen does); a closed loop with no end point starts at its top and runs counter-clockwise; when the pen is
     stuck it lifts and starts again at the leftmost node with arms left.
  5. Each stroke is smoothed, simplified (RDP) and given r (Voronoi coverage over the ink) and w (EDT), then rescaled to font units.

Gates (the exit code is non-zero if either fails, so this can sit in CI):
  - ink coverage: the worst glyph's reveal dabs must cover >= --min-coverage of its ink (default 0.995)
  - layout drift: the runtime's pair-by-pair layout vs full HarfBuzz shaping must stay within --max-drift em (default 0.01)

Setup and usage:
  python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
  .venv/bin/python build_hand.py --font MyScript-Regular.ttf --id myscript --name "My Script" --licence OFL.txt \
      --out-dir public/assets/fonts/pen --preview out/preview
  # a font that is not OFL (one you drew yourself): pass its real licence text and a label
  .venv/bin/python build_hand.py --font MyOwnHand.ttf --id myhand --name "My Hand" --licence LICENCE.txt \
      --licence-name "Proprietary (c) <year> <your studio>; see licenceText"
  # --sample "your own test line" (repeatable) adds lines to the drift check
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import freetype
import numpy as np
import uharfbuzz as hb
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont
from scipy import ndimage as ndi
from skimage.morphology import remove_small_holes, remove_small_objects, skeletonize

CHARSET = ''.join(chr(c) for c in range(32, 127)) + '‘’“”–—…éèêëàâäçïîôöüûñÉÀÇ£'
XH_PX = 140  # every hand is analysed with a 140 px x height
PAD = 6
SMOOTH_SIGMA = 1.4
RDP_TOL = 0.7
SLANT = 0.7  # script hands lean ~35 degrees: x + SLANT * y_down is 'left along the letter axis'
OFFS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


# ------------------------------------------------------------------ raster
def render_glyph(face: freetype.Face, gid: int, R: int):
    """the glyph's ink at R px per em, unhinted, as a bool array + its origin (x px of the pen origin, y px of the baseline)"""
    face.set_char_size(R * 64, 0, 72, 72)
    face.load_glyph(gid, freetype.FT_LOAD_NO_HINTING | freetype.FT_LOAD_NO_BITMAP)
    face.glyph.render(freetype.FT_RENDER_MODE_NORMAL)
    bm = face.glyph.bitmap
    if bm.rows == 0 or bm.width == 0:
        return None, 0, 0
    a = np.array(bm.buffer, dtype=np.uint8).reshape(bm.rows, bm.pitch)[:, : bm.width]
    ink = np.zeros((bm.rows + 2 * PAD, bm.width + 2 * PAD), bool)
    ink[PAD:-PAD, PAD:-PAD] = a >= 128
    ink = remove_small_holes(ink, max_size=6)
    ink = remove_small_objects(ink, max_size=6)
    ox = PAD - face.glyph.bitmap_left   # pixel column of the origin
    oy = PAD + face.glyph.bitmap_top    # pixel row of the baseline
    return ink, ox, oy


# ------------------------------------------------------------------ skeleton graph
class Graph:
    def __init__(self):
        self.nodes: dict[int, np.ndarray] = {}   # id -> (y, x)
        self.edges: dict[int, dict] = {}         # id -> {a, b, pts (N,2) y,x}
        self._n = 0
        self._e = 0

    def add_node(self, p) -> int:
        self._n += 1
        self.nodes[self._n] = np.asarray(p, float)
        return self._n

    def add_edge(self, a, b, pts) -> int:
        self._e += 1
        self.edges[self._e] = dict(a=a, b=b, pts=np.asarray(pts, float))
        return self._e

    def ends(self, n):
        out = []
        for eid, e in self.edges.items():
            if e['a'] == n:
                out.append((eid, True))
            if e['b'] == n:
                out.append((eid, False))
        return out

    def degree(self, n):
        return len(self.ends(n))


def arclen(pts):
    return float(np.sum(np.hypot(*np.diff(pts, axis=0).T))) if len(pts) > 1 else 0.0


def build_graph(sk: np.ndarray) -> Graph:
    H, W = sk.shape
    k = np.ones((3, 3), int)
    k[1, 1] = 0
    nb = ndi.convolve(sk.astype(int), k, mode='constant') * sk
    node_of = -np.ones(sk.shape, int)
    g = Graph()
    jl, nj = ndi.label((nb >= 3) & sk, structure=np.ones((3, 3)))
    for j in range(1, nj + 1):
        ys, xs = np.nonzero(jl == j)
        nid = g.add_node((ys.mean(), xs.mean()))
        node_of[ys, xs] = nid
    for y, x in zip(*np.nonzero((nb <= 1) & sk)):
        node_of[y, x] = g.add_node((y, x))

    def nbrs(p):
        y, x = p
        for dy, dx in OFFS:
            yy, xx = y + dy, x + dx
            if 0 <= yy < H and 0 <= xx < W and sk[yy, xx]:
                yield (yy, xx)

    used = np.zeros(sk.shape, bool)  # interior pixels already in an edge
    seen_keys = set()

    def trace(p, q):
        prev, cur, path = p, q, [q]
        while node_of[cur] < 0:
            used[cur] = True
            cands = [n for n in nbrs(cur) if n != prev and n not in path[-3:] and (node_of[n] >= 0 or not used[n])]
            if not cands:
                break
            # prefer a 4-neighbour step that is not also adjacent to prev (avoids cutting staircase corners)
            cands.sort(key=lambda n: (abs(n[0] - prev[0]) <= 1 and abs(n[1] - prev[1]) <= 1, abs(n[0] - cur[0]) + abs(n[1] - cur[1])))
            prev, cur = cur, cands[0]
            path.append(cur)
        return path

    def edge_from(p, q):
        a = node_of[p]
        if node_of[q] == a:
            return
        if node_of[q] < 0 and used[q]:
            return
        path = trace(p, q)
        end = path[-1]
        b = node_of[end]
        if b < 0:  # dead end that was not a node (rare): make it one
            b = g.add_node(end)
            node_of[end] = b
        interior = tuple(sorted(pp for pp in path if node_of[pp] < 0))
        key = interior if interior else (min(a, b), max(a, b))
        if key in seen_keys:
            return
        seen_keys.add(key)
        pts = [g.nodes[a]] + [np.array(pp, float) for pp in path if node_of[pp] < 0] + [g.nodes[b]]
        g.add_edge(a, b, pts)

    for p in zip(*np.nonzero(node_of >= 0)):
        p = (int(p[0]), int(p[1]))
        for q in nbrs(p):
            edge_from(p, q)
    # pure loops (no end point, no junction): give each a node at its top pixel and walk round once
    left = sk & ~used & (node_of < 0)
    while left.any():
        ys, xs = np.nonzero(left)
        i = int(np.argmin(ys * 10000 + xs))
        p = (int(ys[i]), int(xs[i]))
        nid = g.add_node(p)
        node_of[p] = nid
        for q in nbrs(p):
            if node_of[q] < 0 and not used[q]:
                path = trace(p, q)
                pts = [g.nodes[nid]] + [np.array(pp, float) for pp in path if node_of[pp] < 0] + [g.nodes[node_of[path[-1]]] if node_of[path[-1]] >= 0 else np.array(path[-1], float)]
                g.add_edge(nid, int(node_of[path[-1]]) if node_of[path[-1]] >= 0 else nid, pts)
                break
        left = sk & ~used & (node_of < 0)
    return g


def simplify_graph(g: Graph, half: np.ndarray):
    def wat(p):
        y, x = int(round(p[0])), int(round(p[1]))
        return float(half[min(max(y, 0), half.shape[0] - 1), min(max(x, 0), half.shape[1] - 1)])

    changed = True
    guard = 0
    while changed and guard < 200:
        guard += 1
        changed = False
        # 1. prune spurs: end point -> junction edges shorter than ~the junction's stroke width
        for eid, e in list(g.edges.items()):
            a, b = e['a'], e['b']
            if a == b:
                continue
            da, db = g.degree(a), g.degree(b)
            L = arclen(e['pts'])
            for tip, jn, dj in ((a, b, db), (b, a, da)):
                if g.degree(tip) == 1 and dj >= 3 and L < max(1.7 * wat(g.nodes[jn]), 4.0):
                    del g.edges[eid]
                    del g.nodes[tip]
                    changed = True
                    break
            if changed:
                break
        if changed:
            continue
        # 2. merge junctions joined by a very short edge (a crossing the thinning split in two)
        for eid, e in list(g.edges.items()):
            a, b = e['a'], e['b']
            if a == b or g.degree(a) < 3 or g.degree(b) < 3:
                continue
            L = arclen(e['pts'])
            if L < 0.9 * (wat(g.nodes[a]) + wat(g.nodes[b])):
                mid = (g.nodes[a] + g.nodes[b]) / 2
                del g.edges[eid]
                g.nodes[a] = mid
                for e2 in g.edges.values():
                    if e2['a'] == b:
                        e2['a'] = a
                    if e2['b'] == b:
                        e2['b'] = a
                    if e2['a'] == a:
                        e2['pts'][0] = mid
                    if e2['b'] == a:
                        e2['pts'][-1] = mid
                del g.nodes[b]
                changed = True
                break
        if changed:
            continue
        # 3. join edges through degree-2 nodes
        for n in list(g.nodes):
            ends = g.ends(n)
            if len(ends) != 2 or ends[0][0] == ends[1][0]:
                continue
            (e1, f1), (e2, f2) = ends
            A, B = g.edges[e1], g.edges[e2]
            p1 = A['pts'] if not f1 else A['pts'][::-1]   # ... -> n
            p2 = B['pts'] if f2 else B['pts'][::-1]       # n -> ...
            o1 = A['a'] if not f1 else A['b']
            o2 = B['b'] if f2 else B['a']
            del g.edges[e1], g.edges[e2]
            del g.nodes[n]
            g.add_edge(o1, o2, np.vstack([p1, p2[1:]]))
            changed = True
            break
    # drop isolated nodes
    used = {e['a'] for e in g.edges.values()} | {e['b'] for e in g.edges.values()}
    for n in list(g.nodes):
        if n not in used:
            del g.nodes[n]


# ------------------------------------------------------------------ writing order
def point_at(pts, L):
    """the point L px along a polyline (or its end)"""
    acc = 0.0
    for i in range(1, len(pts)):
        d = float(np.hypot(*(pts[i] - pts[i - 1])))
        if acc + d >= L:
            k = (L - acc) / d if d > 0 else 0
            return pts[i - 1] + (pts[i] - pts[i - 1]) * k
        acc += d
    return pts[-1]


def unit(v):
    n = float(np.hypot(*v))
    return v / n if n > 1e-9 else np.array([0.0, 0.0])


def components(g: Graph):
    parent = {n: n for n in g.nodes}

    def f(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for e in g.edges.values():
        parent[f(e['a'])] = f(e['b'])
    comps: dict[int, list[int]] = {}
    for eid, e in g.edges.items():
        comps.setdefault(f(e['a']), []).append(eid)
    return list(comps.values())


def order_component(g: Graph, eids: list[int], half: np.ndarray):
    """pen strokes (list of (N,2) y,x arrays) for one connected component"""
    remaining = set(eids)
    L_DIR = 7.0

    def opts_at(n):
        out = []
        for eid in remaining:
            e = g.edges[eid]
            if e['a'] == n:
                out.append((eid, True))
            if e['b'] == n:
                out.append((eid, False))
        return out

    def pts_of(eid, fwd):
        p = g.edges[eid]['pts']
        return p if fwd else p[::-1]

    def rdeg(n):
        return len(opts_at(n))

    strokes = []
    first = True
    pen = None
    while remaining:
        nodes = sorted({g.edges[e]['a'] for e in remaining} | {g.edges[e]['b'] for e in remaining})
        ends = [n for n in nodes if rdeg(n) == 1]
        odd = [n for n in nodes if rdeg(n) % 2 == 1]
        # x projected along the hand's slant: a pen starts at the left of the letter's AXIS (the top of a slanted
        # downstroke counts as left of its foot)
        proj = lambda n: g.nodes[n][1] + SLANT * g.nodes[n][0]
        loop_start = None
        if first:
            allp = np.vstack([g.edges[e]['pts'] for e in remaining])
            cproj = float(np.mean(allp[:, 1] + SLANT * allp[:, 0]))
            def crossbar(n):
                # an arm of a cross (t, f, the bar of an A): a flat edge from a tip into a junction. A pen writes the stem first
                eid, fwd = opts_at(n)[0]
                e = g.edges[eid]
                other = e['b'] if fwd else e['a']
                v = g.nodes[other] - g.nodes[n]
                return rdeg(other) >= 3 and abs(v[0]) < 0.5 * abs(v[1])
            left_ends = [n for n in ends if proj(n) <= cproj]
            if any(crossbar(n) for n in left_ends):
                plain = [n for n in ends if not crossbar(n)]
                left_ends = [n for n in left_ends if not crossbar(n)] or ([min(plain, key=proj)] if plain else left_ends)
            if left_ends:
                pool = left_ends
            else:
                # no entry stroke (o, e, a with only an exit tail): start where the loop is, at its highest junction
                looped = [n for n in nodes if rdeg(n) >= 3 or any(g.edges[e]['a'] == g.edges[e]['b'] == n for e in remaining)]
                pool = looped or ends or nodes
                loop_start = bool(looped)
        else:
            pool = odd or nodes
        start = min(pool, key=(lambda n: g.nodes[n][0]) if loop_start else proj)
        cur = start
        incoming = None
        stroke = []
        while True:
            opts = opts_at(cur)
            if not opts:
                break
            if incoming is None:
                loops = [o for o in opts if g.edges[o[0]]['a'] == g.edges[o[0]]['b']]
                if loops:
                    # a closed loop: go round it counter-clockwise (on screen, y down: negative shoelace area)
                    def area(o):
                        p = pts_of(*o)
                        return float(np.sum(p[:-1, 1] * p[1:, 0] - p[1:, 1] * p[:-1, 0]))
                    eid, fwd = min(loops, key=area)
                else:
                    # prefer leaving rightward / upward like a pen would; any arm is fine for an end point (one option)
                    eid, fwd = min(opts, key=lambda o: -unit(point_at(pts_of(*o), L_DIR) - g.nodes[cur])[1])
            else:
                def turn(o):
                    v = unit(point_at(pts_of(*o), L_DIR) - g.nodes[cur])
                    return -float(np.dot(v, incoming))
                eid, fwd = min(opts, key=turn)
            p = pts_of(eid, fwd)
            stroke.extend(p if not stroke else p[1:])
            remaining.discard(eid)
            cur = g.edges[eid]['b'] if fwd else g.edges[eid]['a']
            back = point_at(p[::-1], L_DIR)
            incoming = unit(g.nodes[cur] - back)
        if len(stroke) >= 1:
            strokes.append(np.array(stroke, float))
        first = False
        pen = cur
    return strokes


# ------------------------------------------------------------------ stroke geometry
def smooth(pts, sigma=SMOOTH_SIGMA):
    if len(pts) < 5:
        return pts
    closed = np.allclose(pts[0], pts[-1])
    out = np.empty_like(pts)
    for d in range(2):
        out[:, d] = ndi.gaussian_filter1d(pts[:, d], sigma, mode='wrap' if closed else 'nearest')
    if not closed:
        out[0], out[-1] = pts[0], pts[-1]
    return out


def rdp_idx(pts, tol):
    keep = np.zeros(len(pts), bool)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        i, j = stack.pop()
        if j <= i + 1:
            continue
        a, b = pts[i], pts[j]
        ab = b - a
        n = float(np.hypot(*ab))
        seg = pts[i + 1 : j]
        if n < 1e-9:
            d = np.hypot(*(seg - a).T)
        else:
            d = np.abs(ab[0] * (seg[:, 1] - a[1]) - ab[1] * (seg[:, 0] - a[0])) / n
        k = int(np.argmax(d))
        if d[k] > tol:
            m = i + 1 + k
            keep[m] = True
            stack += [(i, m), (m, j)]
    return np.nonzero(keep)[0]


def densify(pts, step=0.5):
    out = [pts[0]]
    for i in range(1, len(pts)):
        a, b = pts[i - 1], pts[i]
        d = float(np.hypot(*(b - a)))
        n = max(1, int(math.ceil(d / step)))
        for k in range(1, n + 1):
            out.append(a + (b - a) * (k / n))
    return np.array(out)


def analyse(ink: np.ndarray, char: str):
    """strokes for one glyph raster: [(pts (N,2) y,x, r (N), w (N), late: bool)], and the coverage achieved"""
    half = ndi.distance_transform_edt(ink)
    sk = skeletonize(ink)
    g = build_graph(sk)
    simplify_graph(g, half)
    # a round dot (the i dot of a big hand) can thin to a lone pixel with no edge: give every inked blob without one a short tap
    lab, nl = ndi.label(ink, structure=np.ones((3, 3)))
    hit = set()
    for e in g.edges.values():
        for y, x in e['pts']:
            hit.add(int(lab[min(max(int(round(y)), 0), lab.shape[0] - 1), min(max(int(round(x)), 0), lab.shape[1] - 1)]))
    for k in range(1, nl + 1):
        if k in hit:
            continue
        ys, xs = np.nonzero(lab == k)
        c = np.array([ys.mean(), xs.mean()])
        d = np.array([-1.0, -0.6]) * max(1.0, 0.25 * float(half[lab == k].max()))
        g.add_edge(g.add_node(c + d), g.add_node(c - d), [c + d, c, c - d])
    comps = components(g)
    # one record per component: area of its ink (pixels nearest to it), box, centroid
    info = []
    for eids in comps:
        allp = np.vstack([g.edges[e]['pts'] for e in eids])
        info.append(dict(eids=eids, pts=allp, n=len(allp)))
    main_n = max((c['n'] for c in info), default=1)
    main = max(info, key=lambda c: c['n']) if info else None
    for c in info:
        cy, cx = c['pts'][:, 0].mean(), c['pts'][:, 1].mean()
        c['cy'], c['cx'] = cy, cx
        small = c['n'] < 0.35 * main_n
        above = main is not None and c is not main and cy < main['pts'][:, 0].min() + 0.35 * (main['pts'][:, 0].max() - main['pts'][:, 0].min())
        c['small'] = small and c is not main
        c['late'] = c['small'] and above and (char.islower() or char in 'ïîéèêëàâäçôöüûñ')
    # main / big components in reading order (left first, upper first), small ones after the component before them
    big = sorted([c for c in info if not c['small']], key=lambda c: c['pts'][:, 1].min() + 0.6 * c['pts'][:, 0].min())
    small = [c for c in info if c['small'] and not c['late']]
    late = [c for c in info if c['late']]
    order = big + sorted(small, key=lambda c: c['cx'] + 0.6 * c['cy']) + sorted(late, key=lambda c: c['cx'])
    raw = []
    for c in order:
        for s in order_component(g, c['eids'], half):
            raw.append((smooth(s), c['late']))
    if not raw:
        return [], 1.0
    # coverage radius: every ink pixel belongs to its nearest stroke sample; a sample's r reaches its farthest pixel
    dense = [densify(s, 0.5) for s, _ in raw]
    H, W = ink.shape
    mask = np.zeros(ink.shape, bool)
    owner = {}
    for si, d in enumerate(dense):
        for pi, (y, x) in enumerate(d):
            yy, xx = min(max(int(round(y)), 0), H - 1), min(max(int(round(x)), 0), W - 1)
            mask[yy, xx] = True
            owner.setdefault((yy, xx), []).append((si, pi))
    dist, (iy, ix) = ndi.distance_transform_edt(~mask, return_indices=True)
    rpix = {}
    ys, xs = np.nonzero(ink)
    for y, x in zip(ys, xs):
        key = (int(iy[y, x]), int(ix[y, x]))
        d = float(np.hypot(y - key[0], x - key[1]))
        if d > rpix.get(key, 0.0):
            rpix[key] = d
    out = []
    for si, ((s, late), d) in enumerate(zip(raw, dense)):
        rd = np.zeros(len(d))
        wd = np.zeros(len(d))
        for pi, (y, x) in enumerate(d):
            yy, xx = min(max(int(round(y)), 0), H - 1), min(max(int(round(x)), 0), W - 1)
            rd[pi] = rpix.get((yy, xx), 0.0)
            wd[pi] = half[yy, xx]
        rd = np.maximum(rd, wd) + 0.9  # the pixel's own half width (+ a hair of AA)
        rd = ndi.maximum_filter1d(rd, 5)
        wd = ndi.gaussian_filter1d(wd, 2.0)
        keep = rdp_idx(d, RDP_TOL)
        # each kept point covers the dense points up to halfway to its neighbours
        r = np.zeros(len(keep))
        for k, idx in enumerate(keep):
            lo = keep[k - 1] if k > 0 else idx
            hi = keep[k + 1] if k + 1 < len(keep) else idx
            r[k] = rd[(lo + idx) // 2 : (idx + hi) // 2 + 1].max() + RDP_TOL
        out.append((d[keep], r, wd[keep], late))
    # measured coverage with the runtime's interpolation
    cov = np.zeros(ink.shape, bool)
    yy, xx = np.mgrid[0:H, 0:W]
    for pts, r, _, _ in out:
        for i in range(len(pts)):
            a = pts[i]
            b = pts[i + 1] if i + 1 < len(pts) else pts[i]
            ra, rb = r[i], r[i + 1] if i + 1 < len(pts) else r[i]
            n = max(1, int(np.hypot(*(b - a)) / 1.0))
            for k in range(n + 1):
                t = k / n
                c = a + (b - a) * t
                rr = ra + (rb - ra) * t
                y0, y1 = int(max(c[0] - rr - 1, 0)), int(min(c[0] + rr + 2, H))
                x0, x1 = int(max(c[1] - rr - 1, 0)), int(min(c[1] + rr + 2, W))
                sub = (yy[y0:y1, x0:x1] - c[0]) ** 2 + (xx[y0:y1, x0:x1] - c[1]) ** 2 <= rr * rr
                cov[y0:y1, x0:x1] |= sub
    covered = float((cov & ink).sum()) / max(1, int(ink.sum()))
    return out, covered


# ------------------------------------------------------------------ the hand
DEFAULT_LICENCE_NAME = 'SIL Open Font License 1.1'


def build(hand_id: str, font_path: Path, name: str, licence_path: Path | None, role: str = '', preview: Path | None = None, licence_name: str = DEFAULT_LICENCE_NAME,
          out_dir: Path = Path('out/hands'), samples: list[str] | None = None):
    tt = TTFont(str(font_path))
    upem = tt['head'].unitsPerEm
    cmap = tt.getBestCmap()
    gs = tt.getGlyphSet()
    order = tt.getGlyphOrder()
    gid_of = {n: i for i, n in enumerate(order)}

    def bounds(gn):
        bp = BoundsPen(gs)
        gs[gn].draw(bp)
        return bp.bounds

    xh = (bounds(cmap[ord('x')]) or (0, 0, 0, upem * 0.4))[3]
    cap = (bounds(cmap[ord('H')]) or (0, 0, 0, upem * 0.7))[3]
    R = int(round(XH_PX * upem / xh))
    chars = [c for c in CHARSET if ord(c) in cmap]
    missing = [c for c in CHARSET if ord(c) not in cmap]

    # pairs: kerning + contextual alternates, from HarfBuzz on every pair of the charset
    blob = hb.Blob.from_file_path(str(font_path))
    hface = hb.Face(blob)
    hfont = hb.Font(hface)

    def shape(s):
        b = hb.Buffer()
        b.add_str(s)
        b.guess_segment_properties()
        hb.shape(hfont, b, {})
        return [(hfont.glyph_to_string(i.codepoint), p.x_advance) for i, p in zip(b.glyph_infos, b.glyph_positions)]

    adv = {gn: gs[gn].width for gn in order}
    pairs = {}
    glyph_names = {cmap[ord(c)] for c in chars}
    for a in chars:
        for b in chars:
            sh = shape(a + b)
            if len(sh) != 2:
                continue
            (g0, x0), (g1, _) = sh
            ga, gb = cmap[ord(a)], cmap[ord(b)]
            kern = x0 - adv[g0]
            alt_a = g0 if g0 != ga else 0
            alt_b = g1 if g1 != gb else 0
            if kern or alt_a or alt_b:
                pairs[a + b] = [int(kern), alt_a, alt_b] if (alt_a or alt_b) else int(kern)
                glyph_names |= {g0, g1}

    # glyphs
    face = freetype.Face(str(font_path))
    glyphs = {}
    cover = {}
    sheets = []
    for gn in sorted(glyph_names, key=lambda n: gid_of[n]):
        pen = SVGPathPen(gs, ntos=lambda v: str(int(round(v))))
        gs[gn].draw(pen)
        d = pen.getCommands()
        rec = {'a': int(adv[gn])}
        if d:
            rec['d'] = d
        bb = bounds(gn)
        if bb:
            rec['b'] = [int(math.floor(bb[0])), int(math.floor(bb[1])), int(math.ceil(bb[2])), int(math.ceil(bb[3]))]
        ink, ox, oy = render_glyph(face, gid_of[gn], R)
        if ink is not None and ink.any():
            ch = next((c for c in chars if cmap[ord(c)] == gn), gn[:1])
            strokes, cov = analyse(ink, ch)
            cover[gn] = cov
            k = upem / R
            main, late = [], []
            for pts, r, w, is_late in strokes:
                flat = []
                for (y, x), rr, ww in zip(pts, r, w):
                    flat += [int(round((x - ox) * k)), int(round((oy - y) * k)), int(math.ceil(rr * k)), max(1, int(round(ww * k)))]
                (late if is_late else main).append(flat)
            rec['s'] = main
            if late:
                rec['l'] = late
            if preview is not None:
                sheets.append((gn, ink, strokes, cov))
        glyphs[gn] = rec

    lic = licence_path.read_text(encoding='utf8') if licence_path and licence_path.exists() else ''
    copyright_line = next((ln.strip() for ln in lic.splitlines() if ln.strip().lower().startswith('copyright')), '')
    rfn = 'Reserved Font Name' in lic.split('This Font Software')[0] if lic else False
    data = {
        'v': 1,
        'id': hand_id,
        # a Reserved Font Name may not name a Modified Version (OFL 1.1 s3): the data goes by its hand id, the source line credits the font
        'name': f'{hand_id} hand' if rfn else name,
        'role': role,
        'upem': upem,
        'asc': int(tt['hhea'].ascent),
        'desc': int(tt['hhea'].descent),
        'xh': int(xh),
        'cap': int(cap),
        'licence': licence_name + (' (with a Reserved Font Name: this data is a Modified Version and is not presented under that name)' if rfn else ''),
        'copyright': copyright_line,
        'source': f'Glyph outlines and stroke analysis derived from {font_path.name} by build_hand.py; full licence text in licenceText',
        # OFL 1.1 s2: every copy carries the notice AND the licence (a machine-readable field is allowed), so the full text ships in the data
        'licenceText': lic,
        'cmap': {c: cmap[ord(c)] for c in chars},
        'pairs': pairs,
        'glyphs': glyphs,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f'{hand_id}.json'
    out.write_text(json.dumps(data, separators=(',', ':'), ensure_ascii=False), encoding='utf8')
    covs = sorted(cover.items(), key=lambda kv: kv[1])
    nstroke = sum(len(g.get('s', [])) + len(g.get('l', [])) for g in glyphs.values())
    print(f'{hand_id}: {len(glyphs)} glyphs, {nstroke} strokes, {len(pairs)} pairs, R={R} px/em, missing {missing!r}')
    print(f'  coverage min {covs[0][1]*100:.2f}% ({covs[0][0]}), mean {np.mean(list(cover.values()))*100:.2f}%')
    raw = out.stat().st_size
    import gzip
    print(f'  {out}: {raw/1024:.1f} KB raw, {len(gzip.compress(out.read_bytes(), 9))/1024:.1f} KB gzip')
    drift, bad = check_layout(data, shape, samples)
    if preview is not None:
        write_sheet(preview / f'{hand_id}-strokes.png', sheets, cmap)
    data['_gate'] = {'min_cov': covs[0][1], 'drift': drift, 'mismatch': bad}  # popped by main(); never written to the JSON
    return data


def check_layout(data, shape, extra=None):
    """the runtime lays out by pairs; compare with full HarfBuzz shaping on sample lines"""
    samples = ['The quick brown fox jumps over the lazy dog.', 'Hamburgefonstiv, 1234567890!', 'An Old Letter, Written in Haste; Signed & Sealed.'] + list(extra or [])
    worst = 0.0
    bad = 0
    for s in samples:
        cm = data['cmap']
        g = [cm.get(c) for c in s]
        x = 0
        pos = []
        for i, c in enumerate(s):
            gn = g[i]
            if i + 1 < len(s):
                p = data['pairs'].get(c + s[i + 1])
                if isinstance(p, list):
                    if p[2]:
                        g[i + 1] = p[2]
            pos.append(x)
            k = data['pairs'].get(c + s[i + 1]) if i + 1 < len(s) else 0
            kern = (k[0] if isinstance(k, list) else k) or 0
            x += data['glyphs'][g[i]]['a'] + kern
        # alt for the first char of each pair
        g2 = [cm.get(c) for c in s]
        for i in range(len(s) - 1):
            p = data['pairs'].get(s[i] + s[i + 1])
            if isinstance(p, list):
                if p[1]:
                    g2[i] = p[1]
                if p[2]:
                    g2[i + 1] = p[2]
        ref = shape(s)
        hx = 0
        for i, (gn, a) in enumerate(ref):
            worst = max(worst, abs(hx - pos[i]) / data['upem'])
            if gn != g2[i]:
                bad += 1
            hx += a
    print(f'  layout vs HarfBuzz on {len(samples)} lines: worst drift {worst:.4f} em, glyph mismatches {bad}')
    return worst, bad


def write_sheet(path: Path, sheets, cmap):
    from PIL import Image, ImageDraw
    path.parent.mkdir(parents=True, exist_ok=True)
    cell = 260
    cols = 12
    rows = (len(sheets) + cols - 1) // cols
    img = Image.new('RGB', (cols * cell, rows * cell), (240, 232, 214))
    dr = ImageDraw.Draw(img)
    for i, (gn, ink, strokes, cov) in enumerate(sheets):
        cx, cy = (i % cols) * cell, (i // cols) * cell
        h, w = ink.shape
        s = min((cell - 30) / h, (cell - 10) / w, 1.0)
        im = Image.fromarray((~ink * 255).astype(np.uint8)).convert('RGB').resize((max(1, int(w * s)), max(1, int(h * s))))
        im = Image.blend(im, Image.new('RGB', im.size, (240, 232, 214)), 0.55)
        img.paste(im, (cx + 5, cy + 22))
        tot = sum(len(p) for p, *_ in strokes)
        acc = 0
        for si, (pts, r, wd, late) in enumerate(strokes):
            for j in range(1, len(pts)):
                t = (acc + j) / max(1, tot)
                col = (int(40 + 200 * t), int(40 + 60 * (1 - t)), int(220 * (1 - t))) if not late else (0, 160, 60)
                y0, x0 = pts[j - 1] * s
                y1, x1 = pts[j] * s
                dr.line([(cx + 5 + x0, cy + 22 + y0), (cx + 5 + x1, cy + 22 + y1)], fill=col, width=2)
            acc += len(pts)
            y, x = pts[0] * s
            dr.ellipse([cx + 5 + x - 4, cy + 22 + y - 4, cx + 5 + x + 4, cy + 22 + y + 4], fill=(0, 170, 0))
            dr.text((cx + 5 + x + 5, cy + 22 + y - 6), str(si + 1), fill=(0, 110, 0))
        dr.text((cx + 4, cy + 4), f'{gn} {cov*100:.1f}%', fill=(120, 0, 0) if cov < 0.995 else (60, 60, 60))
    img.save(path)
    print(f'  sheet {path}')


def main():
    ap = argparse.ArgumentParser(description='Font -> pen-writer hand JSON (strokes in writing order, nib widths, coverage radii, pair table).')
    ap.add_argument('--font', required=True, help='TTF/OTF file')
    ap.add_argument('--id', help='hand id = output file name (default: the font file stem, lower-cased)')
    ap.add_argument('--name', help='display name stored in the data (default: the font file stem)')
    ap.add_argument('--role', default='', help='free-text note stored in the data')
    ap.add_argument('--licence', help='path to the licence text (shipped in the data as licenceText; its first "Copyright" line becomes the copyright field)')
    ap.add_argument('--licence-name', default=DEFAULT_LICENCE_NAME, help='label stored in the data (default: %(default)s); for a font that is not OFL pass its real licence name')
    ap.add_argument('--out-dir', default='out/hands', help='where <id>.json goes (default: %(default)s)')
    ap.add_argument('--preview', help='write a stroke-order sheet (green dot + number = stroke start, blue->red = time, green line = deferred to word end) into this folder')
    ap.add_argument('--sample', action='append', default=[], help='extra line for the HarfBuzz drift check (repeatable)')
    ap.add_argument('--min-coverage', type=float, default=0.995, help='exit 1 if the worst glyph covers less ink than this (default: %(default)s)')
    ap.add_argument('--max-drift', type=float, default=0.01, help='exit 1 if layout drift vs HarfBuzz exceeds this many em (default: %(default)s)')
    a = ap.parse_args()
    fp = Path(a.font)
    data = build(a.id or fp.stem.lower(), fp, a.name or fp.stem, Path(a.licence) if a.licence else None, a.role,
                 Path(a.preview) if a.preview else None, a.licence_name, Path(a.out_dir), a.sample)
    g = data.pop('_gate')
    fails = []
    if g['min_cov'] < a.min_coverage:
        fails.append(f"coverage {g['min_cov']*100:.2f}% < {a.min_coverage*100:.2f}%")
    if g['drift'] > a.max_drift or g['mismatch']:
        fails.append(f"layout drift {g['drift']:.4f} em (max {a.max_drift}), glyph mismatches {g['mismatch']}")
    if fails:
        print('GATE FAILED: ' + '; '.join(fails))
        return 1
    print('gates ok')
    return 0


if __name__ == '__main__':
    sys.exit(main())
