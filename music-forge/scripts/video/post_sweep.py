#!/usr/bin/env python3
"""Add a camera sweep to a locked-off clip in post: a slow per-frame push-in plus a cosine-eased horizontal pan.

Prompted camera moves on wide shots were mostly ignored by the video models (a paid "slow sweep" barely moved), and a
moving camera in the prompt invites duplicate characters. Generate the wide locked-off, then move the camera here:
free, deterministic, and it never invents anyone. Works best on high-resolution sources (a 2K clip swept down to
480p keeps full detail at the deepest zoom).

The filter (ffmpeg only, no drawtext or libass needed):
    scale=w='trunc(CW*(Z0+(Z1-Z0)*t/D)/2)*2':h=-2:eval=frame,
    crop=CW:CH:x='(iw-CW)*(A+(B-A)*(1-cos(PI*t/D))/2)':y='(ih-CH)*Y',
    scale=W:H
where CW x CH is the crop window (--work times the output size), Z0 -> Z1 the zoom over the clip, A -> B the pan as a
fraction of the spare width, eased in and out by the cosine. --print-filter prints it for your own ffmpeg line.

Run (stdlib + ffmpeg):
    uv run python post_sweep.py clips/22-band-wide.mp4 clips/22-band-wide-sweep.mp4
    uv run python post_sweep.py in.mp4 out.mp4 --size 854x480 --zoom 1.25 1.51 --pan 0.95 0.05      # right to left
    uv run python post_sweep.py in.mp4 out.mp4 --zoom 1.0 1.3 --pan 0.5 0.5                         # straight push-in
    uv run python post_sweep.py in.mp4 --print-filter
"""
from __future__ import annotations

import argparse
import subprocess
import sys


def probe(path: str) -> tuple[float, int, int]:
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height:format=duration",
                        "-of", "default=nw=1", path], capture_output=True, text=True)
    vals = dict(line.split("=", 1) for line in r.stdout.split() if "=" in line)
    try:
        return float(vals["duration"]), int(vals["width"]), int(vals["height"])
    except (KeyError, ValueError):
        raise SystemExit(f"ffprobe could not read {path}") from None


def even(x: float) -> int:
    return int(x) // 2 * 2


def sweep_filter(dur: float, out_w: int, out_h: int, work: float = 2.0, zoom=(1.25, 1.51), pan=(0.05, 0.95), y: float = 0.5) -> str:
    """The ffmpeg -vf string. Zoom is the scaled source width as a multiple of the crop width; >= 1 always."""
    cw, ch = even(out_w * work), even(out_h * work)
    z0, z1 = zoom
    a, b = pan
    d = f"{max(dur, 0.04):.3f}"
    return (f"scale=w='trunc({cw}*({z0}+({z1 - z0:.4f})*t/{d})/2)*2':h=-2:eval=frame,"
            f"crop={cw}:{ch}:x='(iw-{cw})*({a}+({b - a:.4f})*(1-cos(PI*t/{d}))/2)':y='(ih-{ch})*{y}',"
            f"scale={out_w}:{out_h},setsar=1")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Post-production camera sweep: per-frame push-in plus a cosine-eased pan, done in ffmpeg.")
    ap.add_argument("src", help="input clip (ideally locked-off and higher resolution than the output)")
    ap.add_argument("out", nargs="?", help="output mp4 (omit with --print-filter)")
    ap.add_argument("--size", default="854x480", help="output WxH (default 854x480: phone-first SD)")
    ap.add_argument("--work", type=float, default=2.0, help="crop window as a multiple of the output size (default 2.0)")
    ap.add_argument("--zoom", type=float, nargs=2, default=(1.25, 1.51), metavar=("START", "END"),
                    help="scaled source width / crop width at the start and end (default 1.25 1.51: a gentle push-in)")
    ap.add_argument("--pan", type=float, nargs=2, default=(0.05, 0.95), metavar=("FROM", "TO"),
                    help="horizontal position as a fraction of the spare width, 0 = left edge (default 0.05 0.95: left to right)")
    ap.add_argument("--y", type=float, default=0.5, help="vertical position as a fraction of the spare height (default 0.5)")
    ap.add_argument("--crf", type=int, default=18)
    ap.add_argument("--print-filter", action="store_true", help="print the -vf string and exit")
    a = ap.parse_args(argv)

    w, h = (int(x) for x in a.size.lower().split("x"))
    if min(a.zoom) < 1.0:
        ap.error("--zoom values must be >= 1.0 (the scaled source must cover the crop window)")
    if not all(0.0 <= p <= 1.0 for p in (*a.pan, a.y)):
        ap.error("--pan and --y are fractions between 0 and 1")
    dur, sw, sh_ = probe(a.src)
    if sh_ * a.zoom[0] * even(w * a.work) / sw < even(h * a.work):
        ap.error("the source is wider than the output aspect at this zoom; raise --zoom START so its height covers the crop")
    vf = sweep_filter(dur, w, h, a.work, a.zoom, a.pan, a.y)
    if a.print_filter:
        print(vf)
        return 0
    if not a.out:
        ap.error("give an output path, or --print-filter")
    r = subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-i", a.src, "-vf", vf, "-c:v", "libx264", "-crf", str(a.crf),
                        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", a.out], capture_output=True, text=True)
    if r.returncode:
        print(r.stderr[-800:], file=sys.stderr)
        return 1
    print(f"wrote {a.out}  {w}x{h}, {dur:.2f}s, zoom {a.zoom[0]}->{a.zoom[1]}, pan {a.pan[0]}->{a.pan[1]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
