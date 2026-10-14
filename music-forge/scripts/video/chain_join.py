#!/usr/bin/env python3
"""Make a chained shot join invisibly: chain from the real last frame, then align, colour-match and dissolve the join.

Two consecutive shots generated from the same keyframe stutter at the cut (the pose snaps back). The fix is to chain:
generate the next shot from the previous shot's ACTUAL last shown frame. Even then the chained clip came back about
2.5% larger and about 10 px shifted, with a slight regrade, which reads as a one-frame jump. This script:

  last-frame   writes the exact frame the cut shows last (give it the trimmed segment, or --at a time), to chain from
  align        registers the incoming clip onto that frame (ECC affine: scale + shift), applies one constant per-channel
               colour gain/offset so its first frame matches, drops the incoming first frame (it repeats the reference),
               and dissolves the next frames out of the reference (default 2); --dedupe drops padded duplicate frames
               (Hailuo 3 Max repeats about every 4th) and re-interpolates
  check        mean absolute frame difference (0-255, grey 214x120) for each frame pair around a join. Normal motion
               is about 1-3; a jump shows as a spike well above its neighbours, a duplicate as about 0

Run (numpy + OpenCV via uv; ffmpeg on PATH):
    uv run --with numpy --with opencv-python-headless python chain_join.py last-frame clips/12.mp4 frames/c13-from-12.png
    uv run --with numpy --with opencv-python-headless python chain_join.py align frames/c13-from-12.png clips/13.mp4 clips/13-aligned.mp4
    uv run --with numpy --with opencv-python-headless python chain_join.py align ref.png in.mp4 out.mp4 --dedupe --speed 1.2
    uv run --with numpy python chain_join.py check cuts/video.mp4 44.0 187.0 --fps 24
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys

np = None  # imported in _need_np() so --help works without numpy


def _need_np():
    global np
    if np is None:
        try:
            import numpy
        except ImportError:
            sys.exit("chain_join.py needs numpy (and OpenCV for align): uv run --with numpy --with opencv-python-headless python chain_join.py ...")
        np = numpy
    return np


FF = ["ffmpeg", "-nostdin", "-loglevel", "error"]


def _cv2():
    try:
        import cv2
        return cv2
    except ImportError:
        sys.exit("align needs OpenCV: uv run --with numpy --with opencv-python-headless python chain_join.py align ...")


def probe_fps(path: str) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate", "-of", "csv=p=0", path],
                       capture_output=True, text=True)
    num, _, den = r.stdout.strip().partition("/")
    try:
        return float(num) / float(den or 1)
    except ValueError:
        return 24.0


def last_frame(src: str, out: str, at: float | None = None) -> None:
    if at is None:  # decode everything and keep the final frame: exact, unlike -sseof seeks
        subprocess.run(FF + ["-y", "-i", src, "-update", "1", "-q:v", "1", out], check=True)
    else:
        subprocess.run(FF + ["-y", "-i", src, "-ss", f"{at:.4f}", "-frames:v", "1", "-q:v", "1", out], check=True)


def read_frames(path: str, w: int, h: int):
    _need_np()
    raw = subprocess.run(FF + ["-i", path, "-vf", f"scale={w}:{h}:flags=bicubic", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                         capture_output=True, check=True).stdout
    return list(np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3))


def align(ref_path: str, inc_path: str, out_path: str, fps: float = 24.0, speed: float = 1.0, dissolve: int = 2,
          dedupe: bool = False, dedupe_thresh: float = 0.6, crf: int = 15) -> dict:
    _need_np()
    cv2 = _cv2()
    ref = cv2.imread(ref_path)
    if ref is None:
        raise SystemExit(f"cannot read reference frame {ref_path}")
    h, w = ref.shape[:2]
    frames = read_frames(inc_path, w, h)
    if len(frames) < dissolve + 2:
        raise SystemExit("incoming clip is too short")
    src_fps = probe_fps(inc_path)
    gr = cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY).astype(np.float32)
    g0 = cv2.cvtColor(frames[0], cv2.COLOR_BGR2GRAY).astype(np.float32)
    warp = np.eye(2, 3, dtype=np.float32)
    try:
        _, warp = cv2.findTransformECC(gr, g0, warp, cv2.MOTION_AFFINE,
                                       (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 300, 1e-6), None, 5)
    except cv2.error:
        print("ECC did not converge; continuing with no geometric correction", file=sys.stderr)
    before = float(np.abs(gr - g0).mean())
    al = [cv2.warpAffine(f, warp, (w, h), flags=cv2.INTER_CUBIC + cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REFLECT) for f in frames]
    a0 = al[0].reshape(-1, 3).astype(np.float32)
    r0 = ref.reshape(-1, 3).astype(np.float32)
    gain = r0.std(0) / np.maximum(a0.std(0), 1e-3)
    off = r0.mean(0) - gain * a0.mean(0)
    al = [np.clip(f.astype(np.float32) * gain + off, 0, 255).astype(np.uint8) for f in al]
    after = float(np.abs(gr - cv2.cvtColor(al[0], cv2.COLOR_BGR2GRAY).astype(np.float32)).mean())
    n_src = len(al)
    if dedupe:
        small = [cv2.cvtColor(cv2.resize(f, (214, 120)), cv2.COLOR_BGR2GRAY).astype(np.float32) for f in al]
        keep = [0] + [i for i in range(1, n_src) if np.abs(small[i] - small[i - 1]).mean() >= dedupe_thresh]
        al = [al[i] for i in keep]
    rate = src_fps * speed * len(al) / n_src  # keeps real-time duration after dedupe; speed > 1 plays faster
    al = al[1:]  # the first frame re-shows the reference frame: a held frame at the join
    for k in range(min(dissolve, len(al))):
        t = (k + 1) / (dissolve + 1)
        al[k] = (ref.astype(np.float32) * (1 - t) + al[k].astype(np.float32) * t).astype(np.uint8)
    vf = f"minterpolate=fps={fps:g}:mi_mode=mci:mc_mode=aobmc:vsbmc=1" if dedupe else f"fps={fps:g}"
    p = subprocess.Popen(FF + ["-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{w}x{h}", "-r", f"{rate:.4f}", "-i", "-",
                               "-vf", vf, "-c:v", "libx264", "-crf", str(crf), "-pix_fmt", "yuv420p", out_path], stdin=subprocess.PIPE)
    for f in al:
        p.stdin.write(np.ascontiguousarray(f).tobytes())
    p.stdin.close()
    if p.wait():
        raise SystemExit("ffmpeg failed writing the aligned clip")
    scale = float(np.sqrt(abs(np.linalg.det(warp[:, :2]))))
    return {"scale": round(scale, 4), "shift_px": [round(float(warp[0, 2]), 1), round(float(warp[1, 2]), 1)],
            "gain": [round(float(x), 3) for x in gain], "offset": [round(float(x), 1) for x in off],
            "first_frame_diff_before": round(before, 2), "first_frame_diff_after": round(after, 2),
            "frames_in": n_src, "frames_written": len(al)}


def frame_diffs(path: str, t: float, fps: float, before: int = 4, after: int = 4) -> list[tuple[int, float]]:
    """[(pair index relative to the join, mean abs diff)]: pair 0 = last outgoing frame -> first incoming frame."""
    _need_np()
    w, h = 214, 120
    t0 = max(0.0, t - before / fps)
    raw = subprocess.run(FF + ["-ss", f"{t0:.4f}", "-i", path, "-frames:v", str(before + after + 1),
                               "-vf", f"scale={w}:{h},format=gray", "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
    f = np.frombuffer(raw, np.uint8).reshape(-1, h, w).astype(np.float32)
    return [(i - before + 1, float(np.abs(f[i + 1] - f[i]).mean())) for i in range(len(f) - 1)]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Chain shots without a stutter: grab the last frame, align + colour-match + dissolve the "
                                             "incoming clip, and measure the join.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("last-frame", help="write the clip's final frame (or the frame at --at seconds) as a still to chain from")
    p.add_argument("src")
    p.add_argument("out")
    p.add_argument("--at", type=float, help="take the frame at this time instead of the last one")
    p = sub.add_parser("align", help="register, colour-match and dissolve an incoming chained clip onto the reference frame")
    p.add_argument("ref", help="the outgoing shot's last shown frame (the still the incoming clip was chained from)")
    p.add_argument("incoming")
    p.add_argument("out")
    p.add_argument("--fps", type=float, default=24.0, help="output fps (default 24)")
    p.add_argument("--speed", type=float, default=1.0, help="retime: > 1 plays faster (e.g. to land an action inside its slot)")
    p.add_argument("--dissolve", type=int, default=2, help="frames dissolved out of the reference frame (default 2)")
    p.add_argument("--dedupe", action="store_true", help="drop padded duplicate frames and motion-interpolate back to --fps")
    p.add_argument("--crf", type=int, default=15)
    p = sub.add_parser("check", help="frame-difference profile around one or more join times in a cut")
    p.add_argument("video")
    p.add_argument("times", type=float, nargs="+", help="join times in seconds")
    p.add_argument("--fps", type=float, help="video fps (default: probed)")
    a = ap.parse_args(argv)
    _need_np()

    if a.cmd == "last-frame":
        last_frame(a.src, a.out, a.at)
        print(f"wrote {a.out}")
    elif a.cmd == "align":
        r = align(a.ref, a.incoming, a.out, a.fps, a.speed, a.dissolve, a.dedupe, crf=a.crf)
        print(f"wrote {a.out}: scale {r['scale']}, shift {r['shift_px']} px, colour gain {r['gain']} offset {r['offset']}, "
              f"first-frame diff {r['first_frame_diff_before']} -> {r['first_frame_diff_after']}, "
              f"{r['frames_written']} of {r['frames_in']} frames")
    else:
        if not os.path.isfile(a.video):
            print(f"no such video: {a.video}", file=sys.stderr)
            return 2
        fps = a.fps or probe_fps(a.video)
        for t in a.times:
            d = frame_diffs(a.video, t, fps)
            join = dict(d).get(0)
            others = [x for i, x in d if i != 0]
            ratio = join / max(np.median(others), 0.05) if join is not None and others else 0.0
            verdict = "JUMP" if ratio > 3 and join > 4 else "ok"
            print(f"join {t:.3f}s: " + "  ".join(f"[{i:+d}] {x:.2f}" for i, x in d) + f"   -> {verdict} (join/median {ratio:.1f})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
