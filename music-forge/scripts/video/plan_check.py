#!/usr/bin/env python3
"""Validate a music-video shot plan before any money is spent.

Checks: required fields, duplicate ids, parseable times, gaps and overlaps between shots, the first shot
starting at 0, the last shot ending at the audio length, keyframe files on disk, and shots longer than
the chosen model can generate in one clip. Exit 0 = no errors (warnings allowed), 1 = errors, 2 = bad input.

Run (stdlib only, ffprobe optional for measuring the audio):
    uv run python plan_check.py shot-plan.json [--frames-dir frames] [--audio song.m4a] [--json]
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import plan_lib as pl

REQUIRED_TOP = ("title", "audio", "style", "shots")
REQUIRED_SHOT = ("id", "time", "slug", "description", "frame")


def check(plan: dict, frames_dir: str, audio_override: str | None = None, tol: float = 0.011,
          end_tol: float = 0.25, routing: dict | None = None) -> dict:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in plan:
            errors.append(f"plan is missing '{k}'")
    shots = plan.get("shots", [])
    if not shots:
        errors.append("plan has no shots")
        return {"errors": errors, "warnings": warnings, "shots": 0, "planned_seconds": 0.0, "audio_seconds": None}

    seen = set()
    for s in shots:
        for k in REQUIRED_SHOT:
            if not s.get(k):
                errors.append(f"shot {s.get('id', '?')}: missing '{k}'")
        if s.get("id") in seen:
            errors.append(f"duplicate shot id {s['id']!r}")
        seen.add(s.get("id"))
        if s["end"] <= s["start"]:
            errors.append(f"shot {s['id']}: end {pl.fmt_time(s['end'])} is not after start {pl.fmt_time(s['start'])}")
        if s.get("face") not in (None, "human", "creature", "none"):
            warnings.append(f"shot {s['id']}: face={s['face']!r} is not human/creature/none; routing treats it as unknown")

    ordered = sorted(shots, key=lambda s: s["start"])
    if [s["id"] for s in ordered] != [s["id"] for s in shots]:
        warnings.append("shots are not listed in time order (checked in time order)")
    if abs(ordered[0]["start"]) > tol:
        errors.append(f"first shot {ordered[0]['id']} starts at {pl.fmt_time(ordered[0]['start'])}, not 00:00.00 (gap of {ordered[0]['start']:.2f}s at the start)")
    for a, b in zip(ordered, ordered[1:]):
        delta = b["start"] - a["end"]
        if delta > tol:
            errors.append(f"GAP {delta:.2f}s between {a['id']} (ends {pl.fmt_time(a['end'])}) and {b['id']} (starts {pl.fmt_time(b['start'])})")
        elif delta < -tol:
            errors.append(f"OVERLAP {-delta:.2f}s between {a['id']} (ends {pl.fmt_time(a['end'])}) and {b['id']} (starts {pl.fmt_time(b['start'])})")

    planned = ordered[-1]["end"]
    dur, src = pl.audio_duration(plan, audio_override)
    if dur is None:
        warnings.append("audio length unknown (audio file not found and no audio_duration_seconds); total not checked")
    else:
        if src != "ffprobe":
            warnings.append(f"audio file not measured ({src}); total checked against that value")
        diff = planned - dur
        if abs(diff) > end_tol:
            kind = "short of" if diff < 0 else "past"
            errors.append(f"TOTAL: shots end at {pl.fmt_time(planned)} but the audio is {pl.fmt_time(dur)} ({abs(diff):.2f}s {kind} the audio)")
        elif abs(diff) > tol:
            warnings.append(f"last shot ends {abs(diff):.2f}s {'before' if diff < 0 else 'after'} the audio; cut.py snaps the final shot to the audio end")

    for s in shots:
        if pl.resolve_frame(s, frames_dir) is None and s.get("frame"):
            errors.append(f"shot {s['id']}: keyframe {s['frame']!r} not found in {frames_dir}")

    if routing is not None:
        for s in shots:
            model, why = pl.pick_model(s, routing)
            info = pl.model_info(routing, model)
            hi = (info.get("duration") or [0, 0])[1]
            slot = s["end"] - s["start"]
            if hi and slot > hi + 0.5:
                warnings.append(f"shot {s['id']}: {slot:.1f}s slot is longer than {model} can make in one clip ({hi}s); "
                                f"cut.py will hold or loop the last frames. Split the shot or pick another model.")
    return {"errors": errors, "warnings": warnings, "shots": len(shots),
            "planned_seconds": round(planned, 3), "audio_seconds": None if dur is None else round(dur, 3)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Validate a music-video shot plan: gaps, overlaps, total vs audio, missing frames.")
    ap.add_argument("plan", help="shot-plan.json")
    ap.add_argument("--frames-dir", help="keyframe directory (default: <plan dir>/frames)")
    ap.add_argument("--audio", help="audio file to measure (default: the plan's 'audio', relative to the plan)")
    ap.add_argument("--routing", help="model-routing.json (default: bundled) used for the clip-length warning")
    ap.add_argument("--tolerance", type=float, default=0.011, help="seconds of slack between adjacent shots (default 0.011 = one centisecond)")
    ap.add_argument("--end-tolerance", type=float, default=0.25, help="seconds the last shot may differ from the audio length (default 0.25)")
    ap.add_argument("--json", action="store_true", help="print the result as JSON")
    a = ap.parse_args(argv)
    try:
        plan = pl.load_plan(a.plan)
    except (OSError, ValueError, json.JSONDecodeError) as e:
        print(f"cannot read plan: {e}", file=sys.stderr)
        return 2
    frames = a.frames_dir or os.path.join(plan["_dir"], "frames")
    res = check(plan, frames, a.audio, a.tolerance, a.end_tolerance, pl.load_routing(a.routing))
    if a.json:
        print(json.dumps(res, indent=2))
    else:
        print(f"{plan.get('title', '?')}: {res['shots']} shots, planned {res['planned_seconds']}s, audio {res['audio_seconds']}s")
        for w in res["warnings"]:
            print(f"  WARN  {w}")
        for e in res["errors"]:
            print(f"  ERROR {e}")
        print("PLAN OK" if not res["errors"] else f"PLAN HAS {len(res['errors'])} ERROR(S)")
    return 1 if res["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
