#!/usr/bin/env python3
"""Track a piece of on-screen text through a vertically scrolling clip, so a cover patch can follow it exactly.

  python3 track_patch.py <clip.mp4> <ref_t> <x0> <y0> <x1> <y1> <t_from> <t_to> <out.json>

Takes the template box (x0..x1, y0..y1, clip pixels) from the frame at ref_t, then for every frame in [t_from, t_to]
finds the best vertical position in the same x band (assumes the page only scrolls vertically).
Output: [[t, y_top, mse, bg_hex], ...]. mse is the match error: high means the text is not on screen, so hide the
patch there (the stage template hides it above 40). bg_hex is sampled beside the box so the patch matches the page.
Patches show more at full screen: render the patched span and look at it. Needs numpy and ffmpeg/ffprobe.
"""
import json, os, subprocess, sys

if len(sys.argv) != 10 or sys.argv[1] in ("-h", "--help"):
    print(__doc__); sys.exit(0 if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help") else 2)
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view as swv

FF = os.environ.get("FFMPEG", "ffmpeg"); FP = os.environ.get("FFPROBE", "ffprobe")
clip, ref_t = sys.argv[1], float(sys.argv[2])
x0, y0, x1, y1 = map(int, sys.argv[3:7]); ta, tb, out = float(sys.argv[7]), float(sys.argv[8]), sys.argv[9]
W, H = map(int, subprocess.check_output([FP, "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                                         "-of", "csv=p=0", clip]).decode().strip().split(",")[:2])
fps_s = subprocess.check_output([FP, "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate",
                                 "-of", "csv=p=0", clip]).decode().strip()
n, d = (fps_s.split("/") + ["1"])[:2]; FPS = float(n) / float(d)


def frames(t0, dur):
    p = subprocess.run([FF, "-loglevel", "error", "-ss", f"{t0:.3f}", "-i", clip, "-t", f"{dur:.3f}", "-f", "rawvideo",
                        "-pix_fmt", "rgb24", "-"], capture_output=True, check=True)
    return np.frombuffer(p.stdout, np.uint8).reshape(-1, H, W, 3)


ref = frames(ref_t, 1 / FPS)[0]
tpl = ref[y0:y1, x0:x1].mean(2)[:, ::2]
res = []
for i, f in enumerate(frames(ta, tb - ta)):
    strip = f[:, x0:x1].mean(2)[:, ::2]
    err = ((swv(strip, tpl.shape)[:, 0] - tpl) ** 2).mean(axis=(1, 2))
    y = int(err.argmin())
    bg = f[max(0, y - 4), x0 - 6] if x0 >= 6 else f[max(0, y - 4), min(W - 1, x1 + 6)]
    res.append([round(ta + i / FPS, 4), y, round(float(err[y]), 1), "#%02x%02x%02x" % tuple(int(c) for c in bg)])
os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
json.dump(res, open(out, "w"))
ys = [r[1] for r in res]; es = [r[2] for r in res]
print(len(res), "frames; y range", min(ys), max(ys), "; mse median", float(np.median(es)), "max", max(es))
