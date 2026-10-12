#!/usr/bin/env python3
"""Extract review frames from the cut: one at each shot's midpoint (plus near its start and end with --edges),
named <id>-mid.jpg, so you can LOOK at every shot before shipping. Optionally also writes the whisper-ready
audio of each singing clip so the singing check is one command per shot.

Run (stdlib; ffmpeg on PATH):
    uv run python review_frames.py shot-plan.json cuts/video.mp4 [--outdir review] [--edges] [--sing-audio]
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys

import plan_lib as pl


def grab(video: str, t: float, out: str) -> None:
    subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-ss", f"{t:.3f}", "-i", video, "-frames:v", "1", "-q:v", "3", out], check=True)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Extract a review frame per shot from the finished cut (and optional singing-check audio).")
    ap.add_argument("plan")
    ap.add_argument("video", help="the cut to review")
    ap.add_argument("--outdir", default="review")
    ap.add_argument("--edges", action="store_true", help="also grab a frame 0.3 s after each shot's start and 0.3 s before its end")
    ap.add_argument("--sing-audio", action="store_true", help="write <id>.wav (16 kHz mono) from each singing shot's clip, for whisper")
    ap.add_argument("--clips-dir", help="clips directory (default <plan dir>/clips); only used with --sing-audio")
    a = ap.parse_args(argv)
    plan = pl.load_plan(a.plan)
    os.makedirs(a.outdir, exist_ok=True)
    clips = a.clips_dir or os.path.join(plan["_dir"], "clips")
    for s in plan["shots"]:
        mid = (s["start"] + s["end"]) / 2
        grab(a.video, mid, os.path.join(a.outdir, f"{s['id']}-mid.jpg"))
        if a.edges:
            grab(a.video, min(s["end"] - 0.05, s["start"] + 0.3), os.path.join(a.outdir, f"{s['id']}-start.jpg"))
            grab(a.video, max(s["start"], s["end"] - 0.3), os.path.join(a.outdir, f"{s['id']}-end.jpg"))
        if a.sing_audio and s.get("sing"):
            clip = os.path.join(clips, f"{s['id']}-{s['slug']}.mp4")
            if os.path.exists(clip):
                subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-i", clip, "-vn", "-ar", "16000", "-ac", "1",
                                os.path.join(a.outdir, f"{s['id']}.wav")], check=True)
    print(f"wrote review frames for {len(plan['shots'])} shots to {a.outdir}/ : open every one before shipping")
    return 0


if __name__ == "__main__":
    sys.exit(main())
