#!/usr/bin/env python3
"""Silhouette measurement, one place, so every round measures the same way.

Two different sources need two different extractions and mixing them up has already
cost this project six rounds:

  * RENDERS are measured on the ALPHA channel of a transparent-film render. Exact,
    and immune to how dark a material happens to be. Never threshold a render on
    brightness: the ground renders at 21% grey and the bezel is DARKER than that.
  * PHOTOS are white-on-white, so they are measured with a LOW-FUZZ trim swept across
    a range, and we take the stable PLATEAU. At -fuzz 8% the trim eats ref-01's own
    body and understates it ~40%. No plateau = the number is not measuring the object.

Usage:
    python3 measure.py <tag>            # all six views, model vs photo W:H
    python3 measure.py <tag> --bands    # + band-by-band profile for both profiles
"""
import os, pathlib, statistics, subprocess, sys

# Project root: the cwd, or P23D_ROOT. Full note in driver.py — this was
# __file__.parent.parent back when the scripts lived inside the project they served.
ROOT    = pathlib.Path(os.environ.get("P23D_ROOT") or pathlib.Path.cwd()).resolve()
REFS    = ROOT / "refs"
RENDERS = ROOT / "renders"

# ⚠️ WORKED EXAMPLE, and a DUPLICATE. This is the view→photograph mapping from driver.VIEWS
# with the pose columns dropped. It is declared a second time here so measure.py stays
# runnable on its own, which means the two can silently disagree. 🔴 When you fit a rig for
# a new object, change it in all THREE places — driver.VIEWS, this list, and overlay.PAIRS.
# A mapping that disagrees between files scores a render against the wrong photograph, and
# nothing in the harness will tell you: the numbers stay entirely plausible. That exact
# class of defect (an identifier resolving to the wrong thing) accounted for five separate
# failures on the project this came from.
VIEWS = [
    ("front",  "ref-01.jpg"),
    ("threeq", "ref-04.jpg"),
    ("side",   "ref-06.jpg"),
    ("side2",  "ref-03-upright.jpg"),
    ("rear",   "ref-02.jpg"),
    ("upperq", "ref-05.jpg"),
    ("upperq2", "ref-07.jpg"),
]

FUZZ_SWEEP = [1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 18]


def _identify(path):
    out = subprocess.run(["magick", "identify", "-format", "%w %h", str(path)],
                         capture_output=True, text=True).stdout.split()
    return int(out[0]), int(out[1])


CLIFF = 0.03      # a >3% single-step loss of width or height = the trim ate the object


def photo_wh(path, verbose=False):
    """W:H of the device in a photo, from a fuzz sweep cut at the first cliff.

    🔴 The rule here is NOT "take the longest flat run", which is the obvious idea and
    is wrong. On `ref-01` (white device, white sweep) the longest flat run is fuzz
    5-12%, where the trim has already eaten ~24 px off the device's own white flanks;
    it reports 0.659 against a true 0.705. The *correct* plateau is the low-fuzz one.

    So: walk fuzz upward from the conservative end and stop at the first step that
    loses more than 3% of the trimmed width or height in one increment. That step is
    the trim biting into the subject. Take the median ratio of the window before it.
    Three independent methods agree this gives 0.705 on ref-01: this sweep (0.7054),
    a white-threshold mask (0.685), and a least-squares corner fit (0.7077).
    """
    table = []
    for f in FUZZ_SWEEP:
        r = subprocess.run(["magick", str(path), "-fuzz", f"{f}%", "-trim",
                            "-format", "%wx%h", "info:"],
                           capture_output=True, text=True).stdout
        try:
            w, h = [int(v) for v in r.split("x")]
        except ValueError:
            continue
        table.append((f, w, h, w / h))
    if not table:
        raise SystemExit(f"photo_wh: trim produced nothing for {path}")

    window = [table[0]]
    for prev, cur in zip(table, table[1:]):
        if (prev[1] - cur[1]) / prev[1] > CLIFF or (prev[2] - cur[2]) / prev[2] > CLIFF:
            break                      # the trim just bit the subject — stop here
        window.append(cur)
    ratios = [r[3] for r in window]
    # A window whose own ratios still swing more than 3% never settled at all.
    plateau = len(window) >= 3 and (max(ratios) - min(ratios)) / min(ratios) < 0.03
    ratio = statistics.median(ratios)
    if verbose:
        for f, w, h, ra in table:
            mark = " <" if (f, w, h, ra) in window else ""
            print(f"      fuzz {f:>2}%  {w:>4}x{h:<4}  {ra:.4f}{mark}")
    return ratio, plateau, table


def mask_rows(path):
    """Per-row (min_x, max_x) of the alpha matte of a render."""
    w, h = _identify(path)
    raw = subprocess.run(["magick", str(path), "-alpha", "extract", "-threshold", "50%",
                          "-depth", "8", "gray:-"], capture_output=True).stdout
    rows = []
    for y in range(h):
        line = raw[y * w:(y + 1) * w]
        xs = [x for x, v in enumerate(line) if v > 127]
        rows.append((min(xs), max(xs)) if xs else None)
    return rows, w, h


def mask_wh(path):
    rows, _, _ = mask_rows(path)
    live = [i for i, r in enumerate(rows) if r]
    if not live:
        raise SystemExit(f"mask_wh: empty alpha in {path}")
    top, bot = live[0], live[-1]
    x0 = min(r[0] for r in rows if r)
    x1 = max(r[1] for r in rows if r)
    return (x1 - x0 + 1) / (bot - top + 1)


def photo_rows(path):
    """Per-row extent of a photo's subject, thresholded off the white sweep."""
    w, h = _identify(path)
    # 99%, not 93%: at 93% ref-01's white plate is ABOVE the cutoff and reads as
    # background, leaving a crescent of shaded edge instead of a silhouette. At 99% the
    # mask bbox matches an independent low-fuzz trim on all six photos within 4 px.
    raw = subprocess.run(["magick", str(path), "-alpha", "off", "-colorspace", "gray",
                          "-white-threshold", "99%", "-negate", "-threshold", "1%",
                          "-depth", "8", "gray:-"], capture_output=True).stdout
    rows = []
    for y in range(h):
        line = raw[y * w:(y + 1) * w]
        xs = [x for x, v in enumerate(line) if v > 127]
        rows.append((min(xs), max(xs)) if xs else None)
    return rows, w, h


def bands(rows, n=10):
    live = [i for i, r in enumerate(rows) if r]
    top, bot = live[0], live[-1]
    height = bot - top + 1
    out = []
    for i in range(n):
        a = top + int(i * height / n)
        b = top + int((i + 1) * height / n)
        ws = [r[1] - r[0] + 1 for r in rows[a:b] if r]
        out.append((sum(ws) / len(ws) / height) if ws else 0.0)
    return out


def report(tag, do_bands=False, verbose=False):
    md = RENDERS / tag / "mask"
    print(f"\n  SILHOUETTE W:H — {tag}")
    print(f"  {'view':<8} {'MODEL':>7} {'PHOTO':>7} {'err':>8}  plateau")
    errs = {}
    for view, ref in VIEWS:
        mp = md / f"{view}.png"
        if not mp.exists():
            print(f"  {view:<8} (no mask)")
            continue
        m = mask_wh(mp)
        p, plat, _ = photo_wh(REFS / ref, verbose=verbose)
        e = (m - p) / p * 100
        errs[view] = e
        print(f"  {view:<8} {m:>7.3f} {p:>7.3f} {e:>+7.1f}%  {'yes' if plat else 'NO -- suspect'}")
    if errs:
        mean = sum(abs(v) for v in errs.values()) / len(errs)
        worst = max(errs.items(), key=lambda kv: abs(kv[1]))
        print(f"  mean |err| {mean:.2f}%   worst {worst[0]} {worst[1]:+.1f}%")

    if do_bands:
        for view, ref in (("side", "ref-06.jpg"), ("side2", "ref-03-upright.jpg")):
            mp = md / f"{view}.png"
            if not mp.exists():
                continue
            mrows, _, _ = mask_rows(mp)
            prows, _, _ = photo_rows(REFS / ref)
            mb, pb = bands(mrows), bands(prows)
            print(f"\n  depth/height by band — {view} vs {ref}")
            print(f"  {'band':<10} {'MODEL':>7} {'PHOTO':>7} {'err':>8}")
            for i, (a, b) in enumerate(zip(mb, pb)):
                err = f"{(a - b) / b * 100:+.0f}%" if b > 0.01 else "   n/a"
                print(f"  {i*10:>3}-{(i+1)*10:<3}% {a:>7.3f} {b:>7.3f} {err:>8}")
    return errs


if __name__ == "__main__":
    tag = sys.argv[1]
    report(tag, "--bands" in sys.argv, "--verbose" in sys.argv)
