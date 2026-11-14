#!/usr/bin/env python3
"""Find when a UI panel is on screen in each clip, by a thin vertical strip that matches a reference colour.

  python3 detect_band.py --clips media/A.mp4 media/B.mp4 --x 354 --y 200 --h 700 --rgb 230,247,248 [--tol 18]
                         [--out build/track/bands.json]

Use it to time a cover (a frosted panel, a blur) over a part of the app you must not show, such as a debug column,
when that part comes and goes inside a clip. Pick a 4 px strip that is a solid colour only while the panel is open
(a splitter bar works). Output: {clip_name: [[t0, t1], ...]} in clip seconds. Needs numpy and ffmpeg/ffprobe.
"""
import argparse, json, os, subprocess

import numpy as np

FF = os.environ.get("FFMPEG", "ffmpeg"); FP = os.environ.get("FFPROBE", "ffprobe")
ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--clips", nargs="+", required=True)
ap.add_argument("--x", type=int, required=True); ap.add_argument("--y", type=int, required=True)
ap.add_argument("--h", type=int, required=True); ap.add_argument("--w", type=int, default=4)
ap.add_argument("--rgb", required=True); ap.add_argument("--tol", type=float, default=18)
ap.add_argument("--share", type=float, default=0.9, help="share of strip rows that must match")
ap.add_argument("--out", default="track/bands.json")
a = ap.parse_args()
ref = np.array([int(v) for v in a.rgb.split(",")])
out = json.load(open(a.out)) if os.path.exists(a.out) else {}
for c in a.clips:
    fps_s = subprocess.check_output([FP, "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate",
                                     "-of", "csv=p=0", c]).decode().strip()
    n, d = (fps_s.split("/") + ["1"])[:2]; fps = float(n) / float(d)
    p = subprocess.run([FF, "-loglevel", "error", "-i", c, "-vf", f"crop={a.w}:{a.h}:{a.x}:{a.y}", "-f", "rawvideo",
                        "-pix_fmt", "rgb24", "-"], capture_output=True, check=True)
    fr = np.frombuffer(p.stdout, np.uint8).reshape(-1, a.h, a.w, 3).astype(int)
    on = [bool((np.abs(f.mean(1) - ref).max(1) < a.tol).mean() > a.share) for f in fr]
    iv, s = [], None
    for i, v in enumerate(on + [False]):
        if v and s is None: s = i
        if not v and s is not None: iv.append([round(s / fps, 3), round(i / fps, 3)]); s = None
    name = os.path.splitext(os.path.basename(c))[0]; out[name] = iv; print(name, iv)
os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
json.dump(out, open(a.out, "w"))
