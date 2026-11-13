#!/usr/bin/env python3
"""art-measure.py: deterministic art QA for 2D game sprites and screenshots. Numbers, no AI models.

Run (Pillow 13 broke it when written, keep < 13; numpy and scipy needed):
  uv run --with "pillow<13" --with numpy --with scipy art-measure.py <png|jpg|webp>... \\
      [--thresholds art-measure.thresholds.json] [--ref sprite.png] [--json] [--mode auto|sprite|screen] \\
      [--info tone.,outline.] [--out-dir DIR] [--no-heatmap]
  art-measure.py --selftest

SPRITE (RGBA with real transparency): tone, outline weight, edge feathering, contact shadow, hatch. The sprite is
rescaled to a calibration scale (sqrt of opaque area = CAL_SQRT_AREA) before measuring, so export size does not change
the verdict. SCREEN (opaque capture): HUD rectangles masked out, per-64px-tile hatch / thin black ink / moss, a heatmap
PNG in --out-dir (default: temp dir, never beside the input) and a summary.

IMPORTANT: the fixed analysis constants below (near-black, ink level, moss hue, hatch detector, HUD rectangles) were
tuned on ONE art style (dark ink-and-paper, thin pencil contour). The verdict limits live in the thresholds JSON, which
calibrate-thresholds.py derives from YOUR labelled good/bad sprites. The shipped art-measure.thresholds.example.json is
that style's calibration, an example of the file format and NOT a limit for your art. Edit the constants for your style.
--info lists metric prefixes that are printed but never judged (for example a player hero that may be darker).
--selftest runs synthetic images that must each trip their own metric.
"""
import argparse, json, os, sys, tempfile
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
THRESH_PATH = os.path.join(HERE, 'art-measure.thresholds.json')  # override with --thresholds
TILE = 64

# fixed analysis constants (these define what each metric means; they are not calibrated verdict limits). Tuned for a dark ink-and-paper style
NEAR_BLACK = 40          # L < 40 is "near black"
DARK_INK = 55            # outline pixels are L < 55 (near-black ink, not pencil grey)
MOSS_HUE = (50.0, 110.0) # degrees
MOSS_SAT = 0.28          # HSV saturation floor for moss (dark sepia mud sits at 0.20-0.25, olive moss at 0.28+)
MOSS_VAL = 0.15          # value floor; screens also cap at MOSS_VAL_SCREEN_MAX so bright green glows (eyes, effects) do not read as moss
MOSS_VAL_SCREEN_MAX = 0.45
HATCH_COH, HATCH_BAL, HATCH_DENS, HATCH_ENERGY = 0.72, 0.5, 0.40, 4.0
HATCH_SIGMA = 6.0
CAL_SQRT_AREA = 70.0     # median sqrt(opaque px) of the calibration sprites (256 px cells); sprites are rescaled to this
SCALE_WARN = (0.35, 3.0) # rescale factors outside this range are flagged (heavy up/down-sampling distorts edge metrics)
HUD_RECTS = [            # fractions (x0, y0, x1, y1) of the LIVE area (letterbox excluded): the HUD corners of one game. Replace with yours
    (0.0, 0.0, 0.35, 0.075), (0.70, 0.0, 1.0, 0.065), (0.0, 0.82, 0.34, 1.0), (0.84, 0.89, 1.0, 1.0),
]
INFO_PREFIXES = ()  # metric prefixes shown but never judged, set by --info


# ------------------------------------------------------------------ helpers
def lum(rgb):
    return 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]


def hsv(rgb):
    x = rgb.astype(np.float32) / 255.0
    mx, mn = x.max(-1), x.min(-1)
    d = mx - mn
    s = np.where(mx > 0, d / np.maximum(mx, 1e-6), 0)
    r, g, b = x[..., 0], x[..., 1], x[..., 2]
    h = np.zeros_like(mx)
    m = d > 1e-6
    rc = m & (mx == r); gc = m & (mx == g) & ~rc; bc = m & ~rc & ~gc
    h[rc] = ((g - b)[rc] / d[rc]) % 6
    h[gc] = (b - r)[gc] / d[gc] + 2
    h[bc] = (r - g)[bc] / d[bc] + 4
    return h * 60.0, s, mx


def moss_mask(rgb, vmax=1.01):
    h, s, v = hsv(rgb)
    return (h >= MOSS_HUE[0]) & (h <= MOSS_HUE[1]) & (s > MOSS_SAT) & (v > MOSS_VAL) & (v < vmax)


def hatch_map(L, valid=None, sigma=HATCH_SIGMA):
    """Boolean map of pixels inside long, parallel, thin strokes.
    Needs (a) coherent orientation (structure tensor), (b) strokes of alternating gradient sign
    (a lone edge has one sign, stripes alternate), (c) edge density (a lone straight line is thin
    against the window; repeated strokes fill it)."""
    L = L.astype(np.float32)
    g = ndi.gaussian_filter(L, 0.7)
    gx = ndi.sobel(g, axis=1) / 8.0
    gy = ndi.sobel(g, axis=0) / 8.0
    jxx = ndi.gaussian_filter(gx * gx, sigma)
    jyy = ndi.gaussian_filter(gy * gy, sigma)
    jxy = ndi.gaussian_filter(gx * gy, sigma)
    tot = jxx + jyy + 1e-6
    coh = np.sqrt((jxx - jyy) ** 2 + 4 * jxy ** 2) / tot
    th = 0.5 * np.arctan2(2 * jxy, jxx - jyy)
    p = gx * np.cos(th) + gy * np.sin(th)
    bal = np.abs(ndi.gaussian_filter(p, sigma)) / (ndi.gaussian_filter(np.abs(p), sigma) + 1e-6)
    mag = np.hypot(gx, gy)
    dens = ndi.gaussian_filter((mag > 2.0).astype(np.float32), sigma)
    energy = np.sqrt(tot)
    m = (coh > HATCH_COH) & (bal < HATCH_BAL) & (dens > HATCH_DENS) & (energy > HATCH_ENERGY)
    if valid is not None:
        m &= valid
    return m


def largest_cc_area(mask, close=9):
    if not mask.any():
        return 0
    m = ndi.binary_closing(mask, structure=np.ones((3, 3)), iterations=close // 2)
    m = ndi.binary_opening(m, iterations=2)
    lab, n = ndi.label(m)
    if n == 0:
        return 0
    return int(np.bincount(lab.ravel())[1:].max())


def load(path):
    im = Image.open(path)
    has_alpha = im.mode in ('RGBA', 'LA', 'PA') or 'transparency' in im.info
    im = im.convert('RGBA')
    return np.array(im), has_alpha


def is_sprite(arr, has_alpha):
    if not has_alpha:
        return False
    return (arr[..., 3] < 250).mean() > 0.02


# ------------------------------------------------------------------ sprite
def crop_to_alpha(arr, pad=6):
    ys, xs = np.where(arr[..., 3] > 0)
    if len(ys) == 0:
        return arr
    y0, y1, x0, x1 = max(ys.min() - pad, 0), ys.max() + 1 + pad, max(xs.min() - pad, 0), xs.max() + 1 + pad
    out = np.zeros((y1 - y0, x1 - x0, 4), np.uint8)
    sub = arr[y0:y1, x0:x1]
    out[:sub.shape[0], :sub.shape[1]] = sub
    return out


def normalize_scale(arr):
    """crop to the alpha bbox and resample so sqrt(opaque px) == CAL_SQRT_AREA. Returns (arr, scale)."""
    arr = crop_to_alpha(arr)
    n = int((arr[..., 3] >= 128).sum())
    if n < 50:
        return arr, 1.0
    sc = CAL_SQRT_AREA / (n ** 0.5)
    if abs(sc - 1.0) > 0.02:
        im = Image.fromarray(arr, 'RGBA')  # Pillow resizes RGBA premultiplied, so no colour fringe
        im = im.resize((max(int(round(im.width * sc)), 1), max(int(round(im.height * sc)), 1)), Image.LANCZOS)
        arr = crop_to_alpha(np.array(im), pad=6)
    return arr, sc


def measure_sprite(arr):
    arr, scale = normalize_scale(arr)
    rgb = arr[..., :3].astype(np.float32)
    a = arr[..., 3]
    opq = a >= 128
    vis = a > 0
    n_opq = int(opq.sum())
    out = {'kind': 'sprite', 'size': [int(arr.shape[1]), int(arr.shape[0])], 'opaque_px': n_opq, 'scale': round(scale, 3)}
    if not SCALE_WARN[0] <= scale <= SCALE_WARN[1]:
        out['note'] = f'rescaled x{scale:.2f} to calibration scale; outside {SCALE_WARN}, edge metrics are unreliable. Export nearer the shipped size.'
    if n_opq < 50:
        out['error'] = 'empty sprite'
        return out
    L = lum(rgb)
    h, s, v = hsv(rgb)
    Lo = L[opq]
    # (1) tone
    out['tone'] = {
        'L_median': round(float(np.median(Lo)), 1),
        'L_p10': round(float(np.percentile(Lo, 10)), 1),
        'L_p90': round(float(np.percentile(Lo, 90)), 1),
        'near_black_pct': round(float((Lo < NEAR_BLACK).mean() * 100), 2),
        'sat_mean': round(float(s[opq].mean()), 3),
        'moss_pct': round(float(moss_mask(rgb)[opq].mean() * 100), 2),
    }
    # (2) outline: dark contour width along the alpha boundary
    inner = ndi.binary_erosion(opq, iterations=1, border_value=0)
    boundary = opq & ~inner
    nb = int(boundary.sum())
    edt = ndi.distance_transform_edt(np.pad(opq, 1))[1:-1, 1:-1]  # px from the transparent side
    band = opq & (edt <= 8)
    dark = (L < DARK_INK) & band
    lab, n = ndi.label(dark)
    touch = np.unique(lab[boundary & dark])
    touch = touch[touch > 0]
    contour = np.isin(lab, touch) if len(touch) else np.zeros_like(dark)
    n_bd = int((boundary & dark).sum())
    cov = n_bd / max(nb, 1)
    width = float(contour.sum() / max(n_bd, 1)) if n_bd else 0.0
    ring = opq & (edt <= 2)
    out['outline'] = {
        'width_px': round(width, 2),
        'coverage_pct': round(cov * 100, 1),
        'ink_weight_px': round(width * cov, 2),
        'contour_L_mean': round(float(L[ring].mean()), 1),
        'boundary_px': nb,
    }
    # (3) edge feathering
    perim = max(nb, 1)
    d_out = ndi.distance_transform_edt(np.pad(vis, 1))[1:-1, 1:-1]  # distance to an a==0 pixel
    partial = (a > 0) & (a < 255)
    near_edge = partial & (d_out <= 14)
    zone = vis & (d_out <= 3)
    out['feather'] = {
        'partial_ring_pct': round(float(partial[zone].mean() * 100), 1) if zone.any() else 0.0,
        'ramp_px': round(float(near_edge.sum() / perim), 2),
        'partial_pct_of_sprite': round(float(partial.sum() / vis.sum() * 100), 1),
    }
    # (4) contact shadow: soft darker blob in the bottom 25% of the bbox
    ys, xs = np.where(opq)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    bh, bw = y1 - y0, x1 - x0
    zone4 = np.zeros_like(opq)
    zone4[y1 - max(int(bh * 0.25), 3):y1 + 6, x0:x1] = True
    med = float(np.median(Lo))
    soft = vis & (a >= 8) & (a <= 235) & (L < med * 0.85) & zone4
    soft = ndi.binary_opening(soft, iterations=1)
    lab4, n4 = ndi.label(soft)
    best = None
    for i in range(1, n4 + 1):
        m = lab4 == i
        yy, xx = np.where(m)
        w = xx.max() - xx.min() + 1
        area = int(m.sum())
        if area >= 0.02 * bw * bh and w >= 0.35 * bw:
            if best is None or area > best[0]:
                best = (area, w, float(a[m].mean()), float(L[m].mean()))
    if best:
        out['shadow'] = {'present': True, 'area_pct_of_bbox': round(best[0] / (bw * bh) * 100, 1),
                         'width_pct_of_bbox': round(best[1] / bw * 100, 0), 'alpha_mean': round(best[2], 0), 'L_mean': round(best[3], 0)}
    else:
        out['shadow'] = {'present': False, 'note': 'none in sprite (must be added at runtime)'}
    # (5) hatch (silhouette ring excluded so the outline itself cannot read as a stroke)
    Lh = L.copy()
    Lh[~opq] = float(np.median(Lo))
    valid = ndi.binary_erosion(opq, iterations=3, border_value=0)
    hm = hatch_map(Lh, valid)
    out['hatch'] = {
        'hatch_pct': round(float(hm.sum() / n_opq * 100), 2),
        'largest_area_pct': round(float(largest_cc_area(hm) / n_opq * 100), 2),
    }
    return out


# ------------------------------------------------------------------ screenshot
def letterbox_rows(L):
    rm = L.mean(1)
    top = 0
    while top < len(rm) and rm[top] < 14:
        top += 1
    bot = len(rm)
    while bot > top and rm[bot - 1] < 14:
        bot -= 1
    return top, bot


def thin_ink_mask(L, hatch=None):
    """near-black strokes <= ~5 px thick sitting on pale ground (lettering / sketch outlines drawn in black).
    Pixels in or next to a hatched region (code-drawn ring band, brickwork) are excluded: hatch is its own metric."""
    dark = L < 45
    if hatch is not None and hatch.any():
        dark = dark & ~ndi.binary_dilation(hatch, iterations=4)
    edt = ndi.distance_transform_edt(dark)
    thick = ndi.maximum_filter(edt, size=7)
    pale = ndi.uniform_filter(np.where(dark, 0.0, L), 15) / np.maximum(ndi.uniform_filter((~dark).astype(np.float32), 15), 1e-3)
    return dark & (thick <= 3.0) & (pale > 120)


def measure_screen(arr, heat_path=None, mask_hud=True, show_moss=False):
    rgb = arr[..., :3].astype(np.float32)
    H, W = rgb.shape[:2]
    L = lum(rgb)
    top, bot = letterbox_rows(L)
    live = np.zeros((H, W), bool)
    live[top:bot] = True
    hud = np.zeros((H, W), bool)
    if mask_hud and 1.3 <= W / H <= 1.9:  # only for game-shaped frames; crops and contact sheets keep every pixel
        lh = bot - top
        for x0, y0, x1, y1 in HUD_RECTS:
            hud[top + int(y0 * lh):top + int(y1 * lh), int(x0 * W):int(x1 * W)] = True
        live &= ~hud
    mm = moss_mask(rgb, MOSS_VAL_SCREEN_MAX) & live
    hm = hatch_map(L, live)
    nb = (L < NEAR_BLACK) & live
    ink = thin_ink_mask(L, hm) & live
    area = int(live.sum())
    lab, n = ndi.label(nb)
    sizes = np.bincount(lab.ravel(), minlength=n + 1)
    blob_ids = [i for i in range(1, n + 1) if sizes[i] >= 400]
    blobmask = np.isin(lab, blob_ids) if blob_ids else np.zeros((H, W), bool)
    ty, tx = -(-H // TILE), -(-W // TILE)
    tiles = []
    hatch_t = np.zeros((ty, tx), bool); moss_t = np.zeros((ty, tx), bool)
    for j in range(ty):
        for i in range(tx):
            sl = (slice(j * TILE, min((j + 1) * TILE, H)), slice(i * TILE, min((i + 1) * TILE, W)))
            lv = live[sl]
            if lv.mean() < 0.5:
                continue
            t = {
                'x': i * TILE, 'y': j * TILE,
                'L_median': float(np.median(L[sl][lv])),
                'near_black_pct': float(nb[sl][lv].mean() * 100),
                'moss_pct': float(mm[sl][lv].mean() * 100),
                'hatch_pct': float(hm[sl][lv].mean() * 100),
                'ink_pct': float(ink[sl][lv].mean() * 100),
            }
            tiles.append(t)
            hatch_t[j, i] = t['hatch_pct'] >= TH['screen']['hatch_tile_pct']
            moss_t[j, i] = t['moss_pct'] >= TH['screen']['moss_tile_pct']
    Lv = L[live]
    out = {
        'kind': 'screen', 'size': [W, H], 'letterbox_rows': [top, H - bot],
        'tone': {
            'L_median': round(float(np.median(Lv)), 1), 'L_p10': round(float(np.percentile(Lv, 10)), 1),
            'L_p90': round(float(np.percentile(Lv, 90)), 1),
            'near_black_pct': round(float(nb.sum() / area * 100), 2),
            'moss_pct': round(float(mm.sum() / area * 100), 3),
            'near_black_blobs': len(blob_ids),
            'near_black_blob_pct': round(float(blobmask.sum() / area * 100), 2),
        },
        'hatch': {
            'hatch_pct': round(float(hm.sum() / area * 100), 2),
            'largest_area_pct': round(float(largest_cc_area(hm) / area * 100), 2),
            'hatch_tiles': int(hatch_t.sum()), 'tiles': len(tiles),
            'hatch_tile_pct': round(float(hatch_t.sum() / max(len(tiles), 1) * 100), 1),
        },
        'moss': {'moss_tiles': int(moss_t.sum()),  # INFO only: no real screen moss sample was available to calibrate it
                  'max_tile_moss_pct': round(max([t['moss_pct'] for t in tiles] or [0]), 2)},
        'ink': {'thin_black_ink_pct': round(float(ink.sum() / area * 100), 3), 'max_tile_ink_pct': round(max([t['ink_pct'] for t in tiles] or [0]), 2)},
    }
    out['hud_masked_px'] = int(hud.sum())
    if heat_path:
        base = Image.fromarray(arr[..., :3]).convert('RGBA')
        ov = np.zeros((H, W, 4), np.uint8)
        for j in range(ty):
            for i in range(tx):
                y0, x0 = j * TILE, i * TILE
                if hatch_t[j, i]:
                    ov[y0:y0 + TILE, x0:x0 + TILE] = (255, 40, 40, 90)
                if show_moss and moss_t[j, i]:
                    ov[y0:y0 + TILE, x0:x0 + TILE] = (40, 255, 60, 110)
        edge = blobmask & ~ndi.binary_erosion(blobmask, iterations=2)
        ov[edge] = (40, 120, 255, 255)
        ink_e = ndi.binary_dilation(ink, iterations=1)
        ov[ink_e & ~edge] = (255, 0, 255, 200)
        base.alpha_composite(Image.fromarray(ov, 'RGBA'))
        base.convert('RGB').save(heat_path)
        out['heatmap'] = heat_path
    return out


# ------------------------------------------------------------------ verdicts
def load_thresholds():
    with open(THRESH_PATH) as f:
        return json.load(f)


def flat(m):
    f = {}
    for sec in ('tone', 'outline', 'feather', 'hatch', 'moss', 'ink'):
        for k, v in m.get(sec, {}).items():
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                f[f'{sec}.{k}'] = v
    if 'shadow' in m:
        f['shadow.present'] = 1 if m['shadow'].get('present') else 0
    return f


def judge(m):
    """-> {metric: (verdict, value, limits)} using thresholds[kind]['metrics'][metric] = {warn, fail, dir}"""
    res = {}
    for k, v in flat(m).items():
        t = TH.get(m['kind'], {}).get('metrics', {}).get(k)
        if not t:
            continue
        if INFO_PREFIXES and k.startswith(tuple(INFO_PREFIXES)):
            continue  # INFO: shown, not judged
        if t['dir'] == 'max':
            verdict = 'FAIL' if v > t['fail'] else 'WARN' if v > t['warn'] else 'PASS'
        else:
            verdict = 'FAIL' if v < t['fail'] else 'WARN' if v < t['warn'] else 'PASS'
        res[k] = (verdict, v, t)
    return res


def ref_judge(m, ref):
    out = {}
    tol = TH.get('sprite', {}).get('ref_tolerance', {})
    a, b = flat(m), flat(ref)
    for k in a:
        if k in b and k in tol:
            d = a[k] - b[k]
            av = abs(d)
            out[k] = (round(d, 3), 'FAIL' if av > 2 * tol[k] else 'WARN' if av > tol[k] else 'PASS')
    return out


def table(name, m, ref=None):
    lines = [f'== {name}  [{m["kind"]} {m["size"][0]}x{m["size"][1]}' + (f' x{m["scale"]} rescaled' if m.get('scale', 1) != 1 else '') + ']']
    if m.get('note'):
        lines.append('  NOTE: ' + m['note'])
    if INFO_PREFIXES:
        lines.append('  INFO only (not judged): ' + ', '.join(INFO_PREFIXES))
    if 'error' in m:
        return '\n'.join(lines + ['  ' + m['error']])
    J = judge(m)
    R = ref_judge(m, ref) if ref else {}
    hdr = f'  {"metric":30s} {"value":>9s}  verdict'
    if ref:
        hdr += f'   {"d vs ref":>9s}  ref-verdict'
    lines.append(hdr)
    for k, v in flat(m).items():
        vd = J.get(k, ('', v, None))[0]
        row = f'  {k:30s} {v:9.2f}  {vd:7s}'
        if ref and k in R:
            row += f'   {R[k][0]:9.2f}  {R[k][1]}'
        lines.append(row)
    if m['kind'] == 'sprite':
        sh = m['shadow']
        lines.append('  shadow: ' + (f'present ({sh["area_pct_of_bbox"]}% bbox, {sh["width_pct_of_bbox"]:.0f}% wide)' if sh['present'] else sh['note']))
    if m.get('heatmap'):
        lines.append('  heatmap: ' + m['heatmap'])
    allv = [x[0] for x in J.values()]
    fails = [k for k, x in J.items() if x[0] == 'FAIL']
    lines.append('  OVERALL: ' + ('FAIL' if fails else 'WARN' if 'WARN' in allv else 'PASS') + ('  failing: ' + ', '.join(fails) if fails else ''))
    return '\n'.join(lines)


def measure_path(path, mode='auto', heat=True, out_dir=None, show_moss=False):
    arr, has_alpha = load(path)
    sprite = (mode == 'sprite') or (mode == 'auto' and is_sprite(arr, has_alpha))
    if sprite:
        return measure_sprite(arr)
    out_dir = out_dir or os.path.join(tempfile.gettempdir(), 'art-measure')
    os.makedirs(out_dir, exist_ok=True)  # heatmaps never land beside the input
    base = os.path.splitext(os.path.basename(path))[0]
    return measure_screen(arr, os.path.join(out_dir, base + '.measure.png') if heat else None, show_moss=show_moss)


# ------------------------------------------------------------------ self test
def synth_tests():
    """Synthetic images; each must trip its own metric and not the plain control. Returns [(name, ok, detail)]."""
    rng = np.random.RandomState(7)
    res = []
    yy, xx = np.mgrid[:120, :120]  # synthetic sprites are built AT calibration scale (sqrt area ~70) so the rescale step is a no-op

    def disc(r=40):
        return ((yy - 60) ** 2 + (xx - 60) ** 2) <= r * r

    def mk(mask, fill=(200, 185, 150), alpha=None):
        a = np.zeros(mask.shape + (4,), np.uint8)
        n = rng.randint(-6, 7, mask.shape)
        a[..., :3] = np.clip(np.array(fill, int)[None, None, :] + n[..., None], 0, 255)
        a[..., 3] = np.where(mask, 255, 0) if alpha is None else alpha
        return a

    m = disc()
    clean = measure_sprite(mk(m))
    inner = ndi.binary_erosion(m, iterations=5)
    thick = mk(m); thick[m & ~inner, :3] = 15
    mt = measure_sprite(thick)
    res.append(('thick outline', mt['outline']['width_px'] > 4 and clean['outline']['width_px'] < 1,
                f"clean={clean['outline']['width_px']} thick={mt['outline']['width_px']}"))
    big = disc(44)
    d2 = ndi.distance_transform_edt(big)
    mf = measure_sprite(mk(big, alpha=(np.clip(d2 / 9.0, 0, 1) * 255).astype(np.uint8)))
    res.append(('feathered edge', mf['feather']['ramp_px'] > 5 and clean['feather']['ramp_px'] < 1.5,
                f"clean={clean['feather']['ramp_px']} feather={mf['feather']['ramp_px']}"))
    sq = np.zeros((120, 120), bool); sq[28:92, 28:92] = True
    hs = mk(sq); hs[(((xx + yy) % 6) < 2) & sq, :3] = 40
    mh = measure_sprite(hs)
    cs = measure_sprite(mk(sq))
    ln = mk(sq); ln[59:62, 28:92, :3] = 30
    ml = measure_sprite(ln)
    res.append(('hatched square', mh['hatch']['hatch_pct'] > 30 and cs['hatch']['hatch_pct'] < 1 and ml['hatch']['hatch_pct'] < 15,
                f"hatch={mh['hatch']['hatch_pct']} plain={cs['hatch']['hatch_pct']} lone_line={ml['hatch']['hatch_pct']}"))
    mo = mk(m); mo[48:80, 35:85, :3] = (90, 120, 40)
    mm = measure_sprite(mo)
    res.append(('moss blob', mm['tone']['moss_pct'] > 10 and clean['tone']['moss_pct'] < 0.5,
                f"clean={clean['tone']['moss_pct']} moss={mm['tone']['moss_pct']}"))
    body = np.zeros((120, 120), bool); body[15:85, 48:72] = True
    sh = mk(body)
    ell = (((yy - 88) / 7.0) ** 2 + ((xx - 60) / 24.0) ** 2) <= 1
    sh[ell & ~body] = (60, 55, 50, 120)
    msh = measure_sprite(sh)
    mno = measure_sprite(mk(body))
    res.append(('contact shadow', msh['shadow']['present'] and not mno['shadow']['present'],
                f"with={msh['shadow']['present']} without={mno['shadow']['present']}"))
    scr = np.full((256, 320, 3), (205, 195, 170), np.uint8)
    x2, y2 = np.meshgrid(np.arange(128), np.arange(128))
    scr[0:128, 0:128] = np.where(((x2 + y2) % 6) < 2, 40, 205)[..., None]
    scr[128:256, 128:256] = (70, 95, 35)
    scr[200:256, 0:40] = 30
    out = measure_screen(np.dstack([scr, np.full(scr.shape[:2], 255, np.uint8)]), None)
    res.append(('screen tiles', out['hatch']['hatch_tiles'] >= 3 and out['moss']['moss_tiles'] >= 3 and out['tone']['near_black_blobs'] >= 1,
                f"hatch_tiles={out['hatch']['hatch_tiles']} moss_tiles={out['moss']['moss_tiles']} blobs={out['tone']['near_black_blobs']}"))
    return res


TH = {'screen': {'hatch_tile_pct': 35, 'moss_tile_pct': 8}}


def main():
    global TH, THRESH_PATH, INFO_PREFIXES
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('paths', nargs='*')
    ap.add_argument('--ref', help='target sprite to compare against')
    ap.add_argument('--json', action='store_true', help='print JSON instead of the table')
    ap.add_argument('--mode', default='auto', choices=['auto', 'sprite', 'screen'])
    ap.add_argument('--no-heatmap', action='store_true')
    ap.add_argument('--thresholds', help='thresholds JSON (default: art-measure.thresholds.json beside this script)')
    ap.add_argument('--info', default='', help='comma list of metric prefixes to show but not judge, e.g. tone.,outline.')
    ap.add_argument('--out-dir', help='where heatmaps go (default: <tmp>/art-measure, never beside the input)')
    ap.add_argument('--show-moss', action='store_true', help='paint INFO-only moss tiles on the heatmap (glowing eyes may show)')
    ap.add_argument('--selftest', action='store_true')
    a = ap.parse_args()
    if a.thresholds:
        THRESH_PATH = a.thresholds
    INFO_PREFIXES = tuple(x for x in a.info.split(',') if x)
    if os.path.exists(THRESH_PATH):
        TH = load_thresholds()
    elif not a.selftest:
        print(f'note: no thresholds file at {THRESH_PATH}; metrics are printed without verdicts. '
              'Run calibrate-thresholds.py on your own good/bad sprites to make one.', file=sys.stderr)
    if a.selftest:
        bad = 0
        for name, ok, detail in synth_tests():
            print(('ok   ' if ok else 'FAIL ') + name + '  ' + detail)
            bad += (not ok)
        sys.exit(1 if bad else 0)
    if not a.paths:
        ap.error('give at least one image path')
    ref = measure_path(a.ref, 'sprite') if a.ref else None
    results = {p: measure_path(p, a.mode, not a.no_heatmap, a.out_dir, a.show_moss) for p in a.paths}
    if a.json:
        print(json.dumps({'results': results, **({'ref': ref} if ref else {})}, indent=1))
    else:
        for p, m in results.items():
            print(table(os.path.basename(p), m, ref if m['kind'] == 'sprite' else None))
    sys.exit(1 if any('FAIL' in [v[0] for v in judge(m).values()] for m in results.values()) else 0)


if __name__ == '__main__':
    main()
