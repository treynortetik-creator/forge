#!/usr/bin/env python3
"""Scoring, verified acceptance, and an oscillation monitor for the modelling loop.

The loop's failure mode up to v11 was that it COMMITTED EVERY ROUND. There was no reject
path, so a change that improved one view and quietly broke two others still shipped, and
the next round's critic then argued about the damage. Two rounds of this and the loop is
chasing its own tail rather than converging.

So a candidate is only committed if BOTH hold:

  1. mean silhouette IoU improves over the incumbent, and
  2. no view that the incumbent already had at or above GOOD degrades by more than TOL.

Rule 2 is the important half. It is what stops the loop trading a solved view for an
unsolved one, which is how "unconstrained exploration causes regression on previously
solved cases" shows up in practice. If nothing qualifies, the incumbent stays and the
search widens — keeping the least-bad candidate is exactly the behaviour being prevented.

The monitor is deliberately deterministic and needs no model call: if a view's error has
changed sign twice across the recorded history, that view is OSCILLATING, and more rounds
of the same edit will not fix it.

    python3 loop.py score  <tag>            # measure and record one version
    python3 loop.py judge  <cand> <base>    # accept or reject, with reasons
    python3 loop.py trend                   # per-view history + oscillation flags
"""
import json, os, pathlib, subprocess, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import measure, overlay

# Project root: the cwd, or P23D_ROOT. Full note in driver.py — this was
# __file__.parent.parent back when the scripts lived inside the project they served.
ROOT    = pathlib.Path(os.environ.get("P23D_ROOT") or pathlib.Path.cwd()).resolve()
RENDERS = ROOT / "renders"
STORE   = RENDERS / "_scores.json"

GOOD = 0.90     # a view at or above this IoU counts as already solved
TOL  = 0.010    # a solved view may not lose more than one IoU point


def load():
    return json.loads(STORE.read_text()) if STORE.exists() else {}


def save(d):
    STORE.write_text(json.dumps(d, indent=2, sort_keys=True))


def score(tag, record=True):
    """Per-view IoU and W:H error for one version."""
    md = RENDERS / tag / "mask"
    if not md.exists():
        sys.exit(f"no masks for {tag} — run driver.render_masks first")
    out = {"iou": {}, "wh_err": {}}
    for view, ref in overlay.PAIRS:
        if not (md / f"{view}.png").exists():
            continue
        out["iou"][view] = overlay.iou(tag, view, ref)
        m = measure.mask_wh(md / f"{view}.png")
        p, _, _ = measure.photo_wh(measure.REFS / ref)
        out["wh_err"][view] = (m - p) / p * 100.0
    out["mean_iou"] = sum(out["iou"].values()) / len(out["iou"])
    out["mean_abs_wh"] = sum(abs(v) for v in out["wh_err"].values()) / len(out["wh_err"])
    if record:
        d = load(); d[tag] = out; save(d)
    return out


def report(tag, s=None):
    s = s or load().get(tag) or score(tag)
    print(f"\n  {tag}")
    print(f"  {'view':<8} {'IoU':>8} {'W:H err':>9}")
    for v in s["iou"]:
        print(f"  {v:<8} {s['iou'][v]*100:>7.1f}% {s['wh_err'][v]:>+8.1f}%")
    print(f"  mean IoU {s['mean_iou']*100:.2f}%   mean |W:H err| {s['mean_abs_wh']:.2f}%")
    return s


def judge(cand, base):
    """Accept or reject `cand` against incumbent `base`. Prints the reasoning."""
    d = load()
    c = d.get(cand) or score(cand)
    b = d.get(base) or score(base)
    print(f"\n  JUDGING {cand} against incumbent {base}")
    print(f"  {'view':<8} {'base IoU':>9} {'cand IoU':>9} {'delta':>8}  verdict")
    regressions = []
    for v in b["iou"]:
        if v not in c["iou"]:
            continue
        db, dc = b["iou"][v], c["iou"][v]
        delta = dc - db
        note = ""
        if db >= GOOD and delta < -TOL:
            note = f"REGRESSION (was solved at {db*100:.1f}%)"
            regressions.append((v, db, dc))
        print(f"  {v:<8} {db*100:>8.1f}% {dc*100:>8.1f}% {delta*100:>+7.1f}pp  {note}")
    gain = c["mean_iou"] - b["mean_iou"]
    print(f"  mean IoU {b['mean_iou']*100:.2f}% -> {c['mean_iou']*100:.2f}%  ({gain*100:+.2f}pp)")

    ok = True
    if gain <= 0:
        print(f"  ✗ REJECT: mean IoU did not improve.")
        ok = False
    if regressions:
        print(f"  ✗ REJECT: {len(regressions)} already-solved view(s) regressed past "
              f"{TOL*100:.1f}pp: {[r[0] for r in regressions]}")
        ok = False
    if ok:
        print(f"  ✓ ACCEPT: mean improved and no solved view regressed.")
    return ok


def trend():
    """Per-view history and a deterministic oscillation flag. No model call needed."""
    d = load()
    tags = sorted(d, key=lambda t: (len(t), t))
    if not tags:
        sys.exit("no scores recorded yet")
    views = list(d[tags[-1]]["iou"])
    print(f"  {'view':<8} " + " ".join(f"{t:>8}" for t in tags) + "   flag")
    for v in views:
        vals = [d[t]["iou"].get(v) for t in tags]
        cells = " ".join(f"{x*100:>7.1f}%" if x is not None else f"{'-':>8}" for x in vals)
        seq = [x for x in vals if x is not None]
        deltas = [b - a for a, b in zip(seq, seq[1:])]
        signs = [1 if x > 0.002 else (-1 if x < -0.002 else 0) for x in deltas]
        flips = sum(1 for a, b in zip(signs, signs[1:]) if a and b and a != b)
        flag = "OSCILLATING" if flips >= 2 else ""
        print(f"  {v:<8} {cells}   {flag}")
    print(f"  {'MEAN':<8} " + " ".join(f"{d[t]['mean_iou']*100:>7.1f}%" for t in tags))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "trend"
    if cmd == "score":
        report(sys.argv[2], score(sys.argv[2]))
    elif cmd == "judge":
        sys.exit(0 if judge(sys.argv[2], sys.argv[3]) else 1)
    elif cmd == "trend":
        trend()
