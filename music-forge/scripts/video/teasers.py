#!/usr/bin/env python3
"""Cut short teasers from a finished video: each window as 16:9 and as a 9:16 blurred-fill vertical, with short
audio fades and an optional end card (image and/or title text).

Windows: repeat --window name=START-END (MM:SS.ss or plain seconds), or --windows file.json holding either
{"name": [start, end], ...} or [{"name": "...", "start": "0:42.8", "end": "0:55.4"}, ...].
Text on the card is drawn with ImageMagick (`magick`), because many ffmpeg builds lack drawtext.

Run (stdlib; ffmpeg on PATH; ImageMagick only when an end card is used):
    uv run python teasers.py cuts/video.mp4 --window hook=0:00-0:12 --window chorus=1:05-1:20 \\
        --end-card art/banner.jpg --title "Lamp Room" --outdir cuts/teasers
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys

import plan_lib as pl

FONT_CANDIDATES = ("/System/Library/Fonts/Supplemental/Arial Black.ttf", "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
                   "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf")


def sh(*cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(f"{cmd[0]} failed ({r.returncode}): {r.stderr.strip()[-600:]}")


def load_windows(window_args: list[str], json_path: str | None) -> list[tuple[str, float, float]]:
    out = []
    if json_path:
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)
        items = ([{"name": k, "start": v[0], "end": v[1]} for k, v in data.items()] if isinstance(data, dict) else data)
        out += [(i["name"], pl.parse_time(i["start"]), pl.parse_time(i["end"])) for i in items]
    for w in window_args:
        name, sep, rng = w.partition("=")
        if not sep:
            raise ValueError(f"--window wants name=START-END, got {w!r}")
        a, _, b = rng.rpartition("-") if rng.count("-") == 1 else (None, None, None)
        if a is None:
            raise ValueError(f"--window {w!r}: use exactly one '-' between START and END")
        out.append((name, pl.parse_time(a), pl.parse_time(b)))
    for name, a, b in out:
        if b <= a:
            raise ValueError(f"window {name}: end must be after start")
    return out


def make_card(w, h, image, title, font, path):
    if not shutil.which("magick"):
        raise RuntimeError("end card needs ImageMagick (`magick`)")
    font = font or next((f for f in FONT_CANDIDATES if os.path.exists(f)), None)
    cmd = ["magick", "-size", f"{w}x{h}", "xc:black"]
    if image:
        cmd += ["(", image, "-resize", f"{w}x{h}", ")", "-gravity", "center", "-composite"]
    if title:
        if font:
            cmd += ["-font", font]
        cmd += ["-fill", "white", "-stroke", "black", "-strokewidth", "2", "-gravity", "center", "-pointsize", str(max(24, int(min(w, h) * 0.06))),
                "-annotate", f"+0+{int(h * 0.30) if image else 0}", title]
    sh(*cmd, path)
    return path


def render(src, name, a, b, w, h, vertical, outdir, work, card_img, title, card_secs, fps, fade_in, fade_out, font, has_card):
    out = os.path.join(outdir, f"{name}-{'9x16' if vertical else '16x9'}.mp4")
    d = b - a
    if vertical:  # blurred copy fills the frame; the real picture sits in the middle
        v = (f"[0:v]split[x][y];[x]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},boxblur=24:2[bg];"
             f"[y]scale={w}:-2[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2,fps={fps},setsar=1,format=yuv420p[m]")
    else:
        v = f"[0:v]scale={w}:{h},fps={fps},setsar=1,format=yuv420p[m]"
    afx = f"afade=t=in:d={fade_in},afade=t=out:st={max(0.0, d - fade_out):.3f}:d={fade_out}"
    cmd = ["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-ss", f"{a:.3f}", "-t", f"{d:.3f}", "-i", src]
    if has_card:
        png = make_card(w, h, card_img, title, font, os.path.join(work, f"card-{w}x{h}.png"))
        cmd += ["-loop", "1", "-framerate", str(fps), "-t", str(card_secs), "-i", png]
        fc = (f"{v};[1:v]scale={w}:{h},fps={fps},setsar=1,format=yuv420p[card];[m][card]concat=n=2:v=1:a=0[vid];"
              f"[0:a]{afx},apad=pad_dur={card_secs}[aud]")
    else:
        fc = f"{v};[m]null[vid];[0:a]{afx}[aud]"
    cmd += ["-filter_complex", fc, "-map", "[vid]", "-map", "[aud]", "-c:v", "libx264", "-crf", "20", "-preset", "medium",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out]
    sh(*cmd)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Cut N teaser windows from a finished video, each in 16:9 and 9:16 blur-fill.")
    ap.add_argument("source", help="finished video (captions already burned in)")
    ap.add_argument("--window", action="append", default=[], metavar="NAME=START-END", help="repeatable")
    ap.add_argument("--windows", metavar="FILE.json", help="windows from JSON")
    ap.add_argument("--outdir", default="teasers")
    ap.add_argument("--end-card", metavar="IMAGE", help="end-card image (letterboxed on black)")
    ap.add_argument("--title", help="title text on the end card (also makes a text-only card if no image)")
    ap.add_argument("--card-secs", type=float, default=1.5)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--fade-in", type=float, default=0.3)
    ap.add_argument("--fade-out", type=float, default=0.8)
    ap.add_argument("--font", help="font file for the card title")
    ap.add_argument("--no-vertical", action="store_true")
    ap.add_argument("--no-landscape", action="store_true")
    a = ap.parse_args(argv)
    try:
        windows = load_windows(a.window, a.windows)
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as e:
        print(f"bad windows: {e}", file=sys.stderr)
        return 2
    if not windows:
        print("give at least one --window name=START-END or --windows file", file=sys.stderr)
        return 2
    dur = pl.probe_duration(a.source)
    if dur is None:
        print(f"cannot read {a.source}", file=sys.stderr)
        return 2
    for n, s, e in windows:
        if e > dur + 0.05:
            print(f"window {n} ends at {e:.2f}s but the video is {dur:.2f}s", file=sys.stderr)
            return 2
    os.makedirs(a.outdir, exist_ok=True)
    work = os.path.join(a.outdir, "_work")
    os.makedirs(work, exist_ok=True)
    has_card = bool(a.end_card or a.title)
    sizes = []
    if not a.no_landscape:
        sizes.append((1280, 720, False))
    if not a.no_vertical:
        sizes.append((1080, 1920, True))
    for name, s, e in windows:
        for w, h, vert in sizes:
            print(render(a.source, name, s, e, w, h, vert, a.outdir, work, a.end_card, a.title, a.card_secs, a.fps,
                         a.fade_in, a.fade_out, a.font, has_card))
    shutil.rmtree(work, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
