#!/usr/bin/env python3
"""Photogrammetry on the reference photos. Read-only; produces numbers, not geometry.

  section   — scanline extraction of the profile from ref-06 / ref-03-upright: for every
              row down the device, the front and rear surface positions, in units of the
              device's total height. This is the real section, not a description of one.
  roll      — in-plane rotation of the device in a photo, by PCA on the silhouette. The
              two 3/4 product shots have the device ROLLED in the image plane, which
              inflates its axis-aligned bounding box; that has to be measured, never
              fitted to make a ratio agree.
  corners   — least-squares circle fit on the four corners of ref-01.
  bezel     — dark-bezel bounding box on ref-01, as fractions of the plate.

⚠️ The reference FILENAMES throughout this file, and the two feature-specific readers at
the bottom (`corners` fits a rounded rectangular faceplate, `bezel` finds one dark inset
panel on it), are the worked example. `gray_mask`, `rowspans`, `colspans`, `section`,
`roll` and `fit_circle` are general and work on any object. Re-point the filenames in
__main__ at your own refs/, and expect to rewrite `corners`/`bezel` for features your
object actually has.
"""
import math, os, pathlib, subprocess, sys

# Project root: the cwd, or P23D_ROOT. Full note in driver.py — this was
# __file__.parent.parent back when the scripts lived inside the project they served.
ROOT = pathlib.Path(os.environ.get("P23D_ROOT") or pathlib.Path.cwd()).resolve()
REFS = ROOT / "refs"


def gray_mask(path, white_thresh="99%"):
    """Object mask of a photo shot on a white sweep. Returns (bytes, w, h).

    🔴 The cutoff is 99%, not the 93% this harness used for its first ten rounds.
    At 93% the WHITE PLATE of `ref-01` sits above the cutoff and reads as background,
    so the mask is a crescent of shaded edge instead of a device — which is what made
    a PCA on it report a 23-degree roll on a dead-straight-on elevation photo. At 99%
    the mask bbox agrees with an independent low-fuzz trim on all six photos to within
    4 px, and 99% vs 99.5% give identical results, so it is a real plateau and not a
    lucky cutoff.
    """
    w, h = [int(v) for v in subprocess.run(
        ["magick", "identify", "-format", "%w %h", str(path)],
        capture_output=True, text=True).stdout.split()]
    raw = subprocess.run(["magick", str(path), "-alpha", "off", "-colorspace", "gray",
                          "-white-threshold", white_thresh, "-negate", "-threshold", "1%",
                          "-depth", "8", "gray:-"], capture_output=True).stdout
    return raw, w, h


def rowspans(raw, w, h):
    out = []
    for y in range(h):
        line = raw[y * w:(y + 1) * w]
        xs = [x for x, v in enumerate(line) if v > 127]
        out.append((min(xs), max(xs)) if xs else None)
    return out


def section(path, front_is_left=True, n=60):
    """Front/rear surface vs height, in units of total height, front plane at d=0."""
    raw, w, h = gray_mask(path)
    rows = rowspans(raw, w, h)
    live = [i for i, r in enumerate(rows) if r]
    top, bot = live[0], live[-1]
    H = bot - top + 1
    # the front plane is the extreme front pixel anywhere on the device
    if front_is_left:
        front_plane = min(r[0] for r in rows[top:bot + 1] if r)
    else:
        front_plane = max(r[1] for r in rows[top:bot + 1] if r)
    print(f"\n  SECTION {path.name}   height {H}px  front_plane x={front_plane}")
    print(f"  {'t':>6} {'d_front':>9} {'d_rear':>8} {'depth':>8}")
    prev_rear = None
    for i in range(n + 1):
        y = top + int(i * (H - 1) / n)
        r = rows[y]
        if not r:
            continue
        if front_is_left:
            df, dr = (r[0] - front_plane) / H, (r[1] - front_plane) / H
        else:
            df, dr = (front_plane - r[1]) / H, (front_plane - r[0]) / H
        jump = ""
        if prev_rear is not None and abs(dr - prev_rear) > 0.03:
            jump = f"   <== rear jumps {dr - prev_rear:+.3f}"
        prev_rear = dr
        print(f"  {i / n:>6.3f} {df:>9.3f} {dr:>8.3f} {dr - df:>8.3f}{jump}")


def roll(path):
    """In-plane rotation of the device, from the principal axis of its silhouette.

    Also reports the bbox W:H of the silhouette as-shot and what that W:H would be
    with the roll undone, which is the number a straight-on render can be compared to.
    """
    raw, w, h = gray_mask(path)
    pts = []
    for y in range(h):
        line = raw[y * w:(y + 1) * w]
        for x, v in enumerate(line):
            if v > 127:
                pts.append((x, y))
    n = len(pts)
    mx = sum(p[0] for p in pts) / n
    my = sum(p[1] for p in pts) / n
    sxx = sum((p[0] - mx) ** 2 for p in pts) / n
    syy = sum((p[1] - my) ** 2 for p in pts) / n
    sxy = sum((p[0] - mx) * (p[1] - my) for p in pts) / n
    # principal axis angle; atan2 form is stable when sxx == syy
    theta = 0.5 * math.atan2(2 * sxy, sxx - syy)
    # angle of the MAJOR axis measured from vertical (the device is portrait)
    major = theta + math.pi / 2
    deg = math.degrees(major)
    while deg > 90:
        deg -= 180
    while deg < -90:
        deg += 180

    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    bw, bh = max(xs) - min(xs) + 1, max(ys) - min(ys) + 1

    # bbox of the silhouette rotated back to upright
    c, s = math.cos(-math.radians(deg)), math.sin(-math.radians(deg))
    rx = [(p[0] - mx) * c - (p[1] - my) * s for p in pts]
    ry = [(p[0] - mx) * s + (p[1] - my) * c for p in pts]
    uw, uh = max(rx) - min(rx) + 1, max(ry) - min(ry) + 1
    print(f"  {path.name:<22} roll {deg:>+6.2f} deg   bbox {bw}x{bh} W:H={bw/bh:.3f}"
          f"   de-rolled {uw:.0f}x{uh:.0f} W:H={uw/uh:.3f}")
    return deg, bw / bh, uw / uh


def fit_circle(pts):
    """Algebraic (Kasa) circle fit. Returns (cx, cy, r)."""
    n = len(pts)
    sx = sum(p[0] for p in pts); sy = sum(p[1] for p in pts)
    sxx = sum(p[0] * p[0] for p in pts); syy = sum(p[1] * p[1] for p in pts)
    sxy = sum(p[0] * p[1] for p in pts)
    sxxx = sum(p[0] ** 3 for p in pts); syyy = sum(p[1] ** 3 for p in pts)
    sxyy = sum(p[0] * p[1] * p[1] for p in pts); sxxy = sum(p[0] * p[0] * p[1] for p in pts)
    a1, b1 = 2 * (sx * sx / n - sxx), 2 * (sx * sy / n - sxy)
    a2, b2 = 2 * (sx * sy / n - sxy), 2 * (sy * sy / n - syy)
    c1 = sx * (sxx + syy) / n - sxxx - sxyy
    c2 = sy * (sxx + syy) / n - sxxy - syyy
    det = a1 * b2 - a2 * b1
    cx = (c1 * b2 - c2 * b1) / det
    cy = (a1 * c2 - a2 * c1) / det
    r = math.sqrt(sum((p[0] - cx) ** 2 + (p[1] - cy) ** 2 for p in pts) / n)
    return cx, cy, r


def colspans(raw, w, h):
    out = []
    for x in range(w):
        ys = [y for y in range(h) if raw[y * w + x] > 127]
        out.append((min(ys), max(ys)) if ys else None)
    return out


def corners(path=REFS / "ref-01.jpg"):
    """Least-squares circle on each of the four corners of the front plate.

    🔴 Row-scanning alone cannot fit a corner arc. Near the top of the arc the outline
    is almost horizontal, so a row scan returns a handful of points smeared across a
    wide x range; near the side it is almost vertical and returns a dense stack of
    near-identical x. An algebraic fit on that lopsided sample is dominated by the
    vertical end and reported radii from 0.20 W to 0.39 W on a part whose four corners
    are obviously the same. So sample the arc from BOTH directions (rows give the
    near-vertical half, columns give the near-horizontal half), merge, and drop any
    point lying on a straight run.
    """
    raw, w, h = gray_mask(path)
    rows = rowspans(raw, w, h)
    cols = colspans(raw, w, h)
    live = [i for i, r in enumerate(rows) if r]
    top, bot = live[0], live[-1]
    H = bot - top + 1
    x0 = min(r[0] for r in rows[top:bot + 1] if r)
    x1 = max(r[1] for r in rows[top:bot + 1] if r)
    W = x1 - x0 + 1
    livec = [i for i, c in enumerate(cols) if c]
    print(f"\n  CORNERS {path.name}  plate {W}x{H}  W:H={W/H:.4f}")

    res = []
    for vert, horiz in (("top", "left"), ("top", "right"), ("bot", "left"), ("bot", "right")):
        pts = set()
        # rows: walk in from the horizontal extreme until the edge stops moving
        rng = range(top, top + H // 2) if vert == "top" else range(bot, bot - H // 2, -1)
        for y in rng:
            r = rows[y]
            if not r:
                continue
            xv = r[0] if horiz == "left" else r[1]
            off = (xv - x0) if horiz == "left" else (x1 - xv)
            if off <= 1:
                break                      # reached the straight vertical run
            pts.add((xv, y))
        # columns: walk in from the vertical extreme until the edge stops moving
        crng = range(livec[0], livec[0] + W // 2) if horiz == "left" else \
               range(livec[-1], livec[-1] - W // 2, -1)
        for x in crng:
            c = cols[x]
            if not c:
                continue
            yv = c[0] if vert == "top" else c[1]
            off = (yv - top) if vert == "top" else (bot - yv)
            if off <= 1:
                break                      # reached the straight horizontal run
            pts.add((x, yv))
        pts = sorted(pts)
        if len(pts) < 12:
            print(f"    {vert}-{horiz}: only {len(pts)} samples, skipped")
            continue
        cx, cy, r = fit_circle(pts)
        # one trim pass: drop outliers >2 px off the fitted circle, refit
        keep = [p for p in pts
                if abs(math.hypot(p[0] - cx, p[1] - cy) - r) < 2.0]
        if len(keep) >= 12:
            cx, cy, r = fit_circle(keep)
        rms = math.sqrt(sum((math.hypot(p[0] - cx, p[1] - cy) - r) ** 2
                            for p in keep) / len(keep))
        res.append(r / W)
        print(f"    {vert}-{horiz}: {len(keep):>3} pts  r = {r:>6.1f}px = {r/W:.4f} W"
              f"   fit rms {rms:.2f}px")
    if res:
        print(f"    mean corner radius = {sum(res)/len(res):.4f} W"
              f"   spread {max(res)-min(res):.4f}")
    return res


def bezel(path=REFS / "ref-01.jpg", dark="45%"):
    """Dark bezel bbox on the front photo, as fractions of the plate."""
    raw, w, h = gray_mask(path)
    rows = rowspans(raw, w, h)
    live = [i for i, r in enumerate(rows) if r]
    top, bot = live[0], live[-1]
    H = bot - top + 1
    x0 = min(r[0] for r in rows[top:bot + 1] if r)
    x1 = max(r[1] for r in rows[top:bot + 1] if r)
    W = x1 - x0 + 1
    braw = subprocess.run(["magick", str(path), "-alpha", "off", "-colorspace", "gray",
                           "-threshold", dark, "-negate", "-depth", "8", "gray:-"],
                          capture_output=True).stdout
    brows = rowspans(braw, w, h)
    # 🔴 the faceplate pinhole is also dark and it stretched this bbox vertically the
    # first time it was measured. Keep only rows whose dark run is a real bezel width.
    keep = [(y, r) for y, r in enumerate(brows) if r and (r[1] - r[0] + 1) > W * 0.35]
    if not keep:
        print("  bezel: nothing wide enough found — threshold is wrong")
        return
    by0, by1 = keep[0][0], keep[-1][0]
    bx0 = min(r[0] for _, r in keep)
    bx1 = max(r[1] for _, r in keep)
    bw, bh = bx1 - bx0 + 1, by1 - by0 + 1
    print(f"\n  BEZEL {path.name}  {bw}x{bh}  aspect {bw/bh:.3f}")
    print(f"    width      {bw/W:.4f} of plate width")
    print(f"    top edge   {(by0-top)/H:.4f} H     bottom edge {(by1-top)/H:.4f} H")
    print(f"    margin below bezel {(bot-by1)/H:.4f} H")
    print(f"    centre x   {((bx0+bx1)/2 - x0)/W:.4f} W   centre y {((by0+by1)/2-top)/H:.4f} H")


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    if what in ("all", "roll"):
        print("\n  IN-PLANE ROLL")
        for f in ("ref-01.jpg", "ref-02.jpg", "ref-04.jpg", "ref-05.jpg",
                  "ref-06.jpg", "ref-03-upright.jpg"):
            roll(REFS / f)
    if what in ("all", "section"):
        section(REFS / "ref-06.jpg", front_is_left=True)
        section(REFS / "ref-03-upright.jpg", front_is_left=False)
    if what in ("all", "corners"):
        corners()
    if what in ("all", "bezel"):
        bezel()
