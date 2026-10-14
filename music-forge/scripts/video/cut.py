#!/usr/bin/env python3
"""Assemble the cut: every clip trimmed or padded to its frame-exact slot, the ORIGINAL song laid over it.

Slots are whole frames computed from the plan's start times at a fixed fps (shot i runs from
round(start_i*fps) to round(start_{i+1}*fps); the last runs to the audio end), so cuts cannot drift.
Generated clips may re-sing, so their audio is dropped and the real song is used. A shot with no clip falls
back to a slow push-in on its keyframe. A clip whose sidecar JSON carries `song_t0` (the song time at the clip's first
frame, measured by sync_offset.py --write-sidecar) enters at that offset instead of at its first frame, so a sung
take lands on the vocal it was generated from; when the take starts after its slot, its first frame is held for
the gap. Optional burned captions from an SRT: ffmpeg's subtitles filter if
this ffmpeg has it (libass), else ImageMagick PNG overlays. Also writes <out>-small.mp4 under a size target.

Run (stdlib; ffmpeg + ffprobe on PATH; ImageMagick `magick` only for PNG captions):
    uv run python cut.py shot-plan.json --out cuts/video.mp4 [--captions lyrics.srt] [--small-mb 45]
"""
from __future__ import annotations

import argparse
import json
import os
import re
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
    return r


def has_subtitles_filter() -> bool:
    r = subprocess.run(["ffmpeg", "-hide_banner", "-filters"], capture_output=True, text=True)
    return any(re.search(r"\bsubtitles\b", line) for line in r.stdout.splitlines())


def frame_slots(shots: list[dict], fps: int, audio_s: float) -> list[tuple[dict, int]]:
    """[(shot, n_frames)] tiling exactly round(audio_s*fps) frames. Boundaries come from start times only."""
    ordered = sorted(shots, key=lambda s: s["start"])
    total = round(audio_s * fps)
    bounds = [0] + [round(s["start"] * fps) for s in ordered[1:]] + [total]
    out = []
    for s, a, b in zip(ordered, bounds, bounds[1:]):
        out.append((s, max(0, b - a)))
    return out


def find_clip(clips_dir: str, shot: dict, extra_dirs: list[str]) -> str | None:
    name = f"{shot['id']}-{shot['slug']}.mp4"
    for d in extra_dirs + [clips_dir]:
        p = os.path.join(d, name)
        if os.path.isfile(p):
            return p
    return None


def sync_offset_for(clip: str | None, slot_start: float) -> float | None:
    """Seconds into the clip to enter at, from its sidecar's measured song_t0. None when unmeasured."""
    if not clip:
        return None
    side = os.path.splitext(clip)[0] + ".json"
    try:
        with open(side, encoding="utf-8") as f:
            t0 = json.load(f).get("song_t0")
    except (OSError, ValueError):
        return None
    return None if t0 is None else slot_start - float(t0)


def make_segment(shot, n, clip, frame, w, h, fps, pad, work, i, offset: float | None = None) -> tuple[str, bool]:
    out = os.path.join(work, f"seg{i:03d}.mp4")
    enc = ["-c:v", "libx264", "-crf", "17", "-preset", "fast", "-pix_fmt", "yuv420p", "-an"]
    base = f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},fps={fps},setsar=1"
    if clip:
        seek, head = [], ""
        if offset and offset > 0:
            seek = ["-ss", f"{offset:.3f}"]  # the take started before the slot: skip into it
        elif offset and offset < 0:
            head = f",tpad=start_mode=clone:start_duration={-offset:.3f}"  # the take starts late: hold its first frame
        if pad == "loop":
            sh("ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-stream_loop", "-1", *seek, "-i", clip, "-vf", base + head,
               "-frames:v", str(n), *enc, out)
        else:  # hold: freeze the last frame if the clip is shorter than the slot
            sh("ffmpeg", "-nostdin", "-loglevel", "error", "-y", *seek, "-i", clip,
               "-vf", base + head + f",tpad=stop_mode=clone:stop_duration={n / fps + 1:.3f}", "-frames:v", str(n), *enc, out)
        return out, True
    if frame:
        zp = (f"scale={w * 2}:{h * 2}:force_original_aspect_ratio=increase,crop={w * 2}:{h * 2},"
              f"zoompan=z='min(zoom+0.0008,1.12)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={n}:s={w}x{h}:fps={fps},setsar=1")
        sh("ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-loop", "1", "-i", frame, "-vf", zp, "-frames:v", str(n), *enc, out)
    else:
        sh("ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-f", "lavfi", "-i", f"color=c=black:s={w}x{h}:r={fps}",
           "-frames:v", str(n), *enc, out)
    return out, False


def parse_srt(path: str) -> list[tuple[float, float, str]]:
    with open(path, encoding="utf-8-sig") as f:
        raw = f.read()
    caps = []
    for block in re.split(r"\n\s*\n", raw.strip().replace("\r\n", "\n")):
        lines = block.strip().splitlines()
        m = next((re.match(r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)", ln) for ln in lines if "-->" in ln), None)
        if not m:
            continue
        g = [int(x) for x in m.groups()]
        a, b = g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000, g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000
        text = " ".join(ln for ln in lines if "-->" not in ln and not ln.strip().isdigit()).strip()
        if b - a >= 0.2 and text and not (text.startswith("[") and text.endswith("]")):
            caps.append((a, b, text))
    return caps


def caption_pngs(caps, w, font, work) -> list[tuple[float, float, str]]:
    if not shutil.which("magick"):
        raise RuntimeError("PNG captions need ImageMagick (`magick`) because this ffmpeg has no subtitles filter; install it or drop --captions")
    font = font or next((f for f in FONT_CANDIDATES if os.path.exists(f)), None)
    res = []
    for i, (a, b, text) in enumerate(caps):
        png = os.path.join(work, f"cap{i:03d}.png")
        cmd = ["magick", "-background", "none", "-fill", "white", "-stroke", "black", "-strokewidth", "3"]
        if font:
            cmd += ["-font", font]
        cmd += ["-pointsize", str(max(18, w // 34)), "-size", f"{int(w * 0.875)}x", "-gravity", "center", f"caption:{text}", png]
        sh(*cmd)
        res.append((a, b, png))
    return res


def esc_filter_path(p: str) -> str:
    return p.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'").replace(",", "\\,").replace("[", "\\[").replace("]", "\\]")


def encode_final(picture, audio, out, total_s, caps_mode, srt, caps, w, h, crf, font, work):
    inputs = ["-i", picture, "-i", audio]
    fc, vmap = None, "0:v"
    if srt and caps_mode == "subtitles":
        style = f"FontSize={max(16, h // 22)},Outline=2,Alignment=2,MarginV={h // 15}"
        fc, vmap = f"[0:v]subtitles='{esc_filter_path(srt)}':force_style='{style}'[vout]", "[vout]"
    elif srt:
        pngs = caption_pngs(caps, w, font, work)
        for _, _, png in pngs:
            inputs += ["-i", png]
        chain, last = [], "[0:v]"
        for k, (a, b, _) in enumerate(pngs):
            chain.append(f"{last}[{k + 2}:v]overlay=(W-w)/2:H-h-{h // 15}:enable='between(t,{a:.3f},{b:.3f})'[v{k}]")
            last = f"[v{k}]"
        fc, vmap = (";".join(chain), last) if chain else (None, "0:v")
    cmd = ["ffmpeg", "-nostdin", "-loglevel", "error", "-y", *inputs]
    if fc:
        cmd += ["-filter_complex", fc]
    cmd += ["-map", vmap, "-map", "1:a", "-c:v", "libx264", "-crf", str(crf), "-preset", "medium", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-t", f"{total_s:.4f}", "-movflags", "+faststart", out]
    sh(*cmd)


def make_small(src, dst, target_mb, dur):
    """Re-encode under target_mb with a bitrate budget; drops resolution when the budget is thin; retries tighter."""
    audio_bps = 96_000
    budget = target_mb * 1024 * 1024 * 8 * 0.94 / dur - audio_bps
    for attempt in range(4):
        vbps = int(budget * (0.88 ** attempt))
        height = 720 if vbps >= 1_500_000 else 480 if vbps >= 700_000 else 360
        sh("ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-i", src, "-vf", f"scale=-2:{height}", "-c:v", "libx264",
           "-preset", "medium", "-b:v", str(vbps), "-maxrate", str(int(vbps * 1.3)), "-bufsize", str(vbps * 2), "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", f"{audio_bps // 1000}k", "-ac", "2", "-movflags", "+faststart", dst)
        if os.path.getsize(dst) <= target_mb * 1024 * 1024:
            return height, os.path.getsize(dst)
    return height, os.path.getsize(dst)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Frame-exact music-video cut: clips to slots, original song on top, optional burned captions.")
    ap.add_argument("plan", help="shot-plan.json")
    ap.add_argument("--clips-dir", help="clips (default <plan dir>/clips)")
    ap.add_argument("--prefer-dir", action="append", default=[], metavar="DIR", help="check these directories for a clip before --clips-dir (redo folders); repeatable")
    ap.add_argument("--frames-dir", help="keyframes for the still fallback (default <plan dir>/frames)")
    ap.add_argument("--audio", help="song file (default: the plan's 'audio')")
    ap.add_argument("--out", help="output mp4 (default <plan dir>/cuts/<title-slug>.mp4)")
    ap.add_argument("--fps", type=int, help="override the plan's fps (default 30)")
    ap.add_argument("--size", help="WxH (default 1280x720, or 720x1280 for aspect 9:16)")
    ap.add_argument("--pad", choices=["hold", "loop"], default="hold", help="clip shorter than its slot: freeze the last frame (default) or loop")
    ap.add_argument("--captions", help="SRT file to burn in")
    ap.add_argument("--caption-mode", choices=["auto", "subtitles", "png"], default="auto",
                    help="auto = ffmpeg subtitles filter if this ffmpeg has it, else ImageMagick PNG overlays")
    ap.add_argument("--font", help="font file for PNG captions")
    ap.add_argument("--crf", type=int, default=19)
    ap.add_argument("--small-mb", type=float, default=45.0, help="also write <out>-small.mp4 under this size (default 45)")
    ap.add_argument("--no-small", action="store_true")
    ap.add_argument("--keep-work", action="store_true", help="keep the temporary segment folder")
    ap.add_argument("--no-sync", action="store_true", help="ignore measured song_t0 offsets in clip sidecars (enter every clip at frame 0)")
    a = ap.parse_args(argv)

    plan = pl.load_plan(a.plan)
    fps = a.fps or int(plan.get("fps", 30))
    default_size = "720x1280" if plan.get("aspect") == "9:16" else "1280x720"
    w, h = (int(x) for x in (a.size or default_size).lower().split("x"))
    frames = a.frames_dir or os.path.join(plan["_dir"], "frames")
    clips = a.clips_dir or os.path.join(plan["_dir"], "clips")
    audio = a.audio or pl.resolve_path(plan, plan.get("audio"))
    if not audio or not os.path.exists(audio):
        print(f"song not found: {audio}", file=sys.stderr)
        return 2
    audio_s = pl.probe_duration(audio)
    slug = re.sub(r"[^a-z0-9]+", "-", plan.get("title", "video").lower()).strip("-") or "video"
    out = a.out or os.path.join(plan["_dir"], "cuts", f"{slug}.mp4")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    work = os.path.join(os.path.dirname(os.path.abspath(out)), "_work-" + os.path.splitext(os.path.basename(out))[0])
    os.makedirs(work, exist_ok=True)

    # refuse a plan that does not tile the song; gaps would silently shift every later cut
    import plan_check
    res = plan_check.check(plan, frames, audio, routing=None)
    gaps = [e for e in res["errors"] if e.startswith(("GAP", "OVERLAP", "TOTAL")) or "starts at" in e]
    if gaps:
        print("plan does not tile the song:\n  " + "\n  ".join(gaps), file=sys.stderr)
        return 1

    slots = frame_slots(plan["shots"], fps, audio_s)
    segs, stills, synced = [], [], []
    slot_start = 0
    for i, (shot, n) in enumerate(slots):
        start_s, slot_start = slot_start / fps, slot_start + n
        if n <= 0:
            continue
        clip = find_clip(clips, shot, a.prefer_dir)
        off = None if a.no_sync else sync_offset_for(clip, start_s)
        if off is not None:
            synced.append(f"{shot['id']} {'+' if off >= 0 else ''}{off:.3f}s")
        seg, real = make_segment(shot, n, clip, pl.resolve_frame(shot, frames), w, h, fps, a.pad, work, i, off)
        segs.append(seg)
        if not real:
            stills.append(shot["id"])
    lst = os.path.join(work, "concat.txt")
    with open(lst, "w") as f:
        f.writelines(f"file '{p}'\n" for p in segs)
    picture = os.path.join(work, "picture.mp4")
    sh("ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", picture)

    mode = a.caption_mode
    if a.captions and mode == "auto":
        mode = "subtitles" if has_subtitles_filter() else "png"
    caps = parse_srt(a.captions) if a.captions and mode == "png" else []
    total_s = round(audio_s * fps) / fps
    encode_final(picture, audio, out, total_s, mode, a.captions, caps, w, h, a.crf, a.font, work)
    vdur = pl.probe_duration(out)
    print(f"wrote {out}  {vdur:.3f}s (audio {audio_s:.3f}s, {1 / fps:.3f}s per frame)  "
          f"captions: {mode if a.captions else 'none'}  stills instead of clips: {', '.join(stills) or 'none'}")
    if synced:
        print(f"entered at measured sync offsets (clip seconds; negative = first frame held): {', '.join(synced)}")
    if not a.no_small:
        small = os.path.splitext(out)[0] + "-small.mp4"
        height, size = make_small(out, small, a.small_mb, total_s)
        print(f"wrote {small}  {size / 1024 / 1024:.1f} MB at {height}p (target {a.small_mb:g} MB)")
    if not a.keep_work:
        shutil.rmtree(work, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
