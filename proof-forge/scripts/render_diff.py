#!/usr/bin/env python3
"""
render_diff.py — find WHERE two exports differ, and put a marker on it.

WHY THIS EXISTS
---------------
The strongest single request in a dig through practitioner forums, verbatim:

    "I need to compare two exports and make sure they are exact visual replicas...
    the only way I know how is to drop a video file into the top layer and compare
    it one clip at a time. This is incredibly tedious and isn't even foolproof --
    my human eyes can easily miss a minor discrepancy... Sometimes the difference is
    just one little corner of the frame for one second in a two-hour sequence."

And the explicit spec for the fix, from the same person:

    "even if there was a tool that just did the difference-mode scanning for you and
    **added markers where the differences appeared**, that would be a big step."

The commercial equivalent starts in the mid five figures, and even its owner says it
is often still faster to check the files by hand. This is the same operation done
with ffmpeg, which everyone already has.

THE HARD PART IS NOT THE DIFF. IT IS THE THRESHOLD.
---------------------------------------------------
Two exports of the same timeline are never bit-identical -- a different encoder, a
different bitrate, or a different colour pipeline moves every pixel slightly. An
absolute PSNR threshold therefore either flags the whole file or nothing, depending
on the codec, and a tool that cries wolf on a re-encode is one you stop running.

So the threshold is derived from THIS PAIR of files: measure per-frame similarity
across the whole comparison, take the median as the encoding-noise floor, and flag
frames that fall far below their own file's baseline. A uniform re-encode has a
tight distribution and produces nothing. One bad corner for one second is an
outlier, which is exactly what the person above needs found.

`--absolute` overrides this when you genuinely want a fixed bar.

USAGE
    python3 render_diff.py a.mov b.mov                  # video, marker list
    python3 render_diff.py a.mov b.mov --edl out.edl    # markers for an NLE
    python3 render_diff.py a.png b.png --out diff.png   # stills, with a heat map
    python3 render_diff.py a.wav b.wav                  # audio null test
    python3 render_diff.py a.mov b.mov --json

Needs ffmpeg/ffprobe for video and audio. Stills need Pillow.
"""
import argparse
import json
import math
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

VIDEO_EXT = {".mov", ".mp4", ".mkv", ".avi", ".mxf", ".webm", ".m4v", ".prores"}
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp", ".gif"}
AUDIO_EXT = {".wav", ".aif", ".aiff", ".flac", ".mp3", ".m4a", ".aac"}


class DiffError(Exception):
    pass


def need(tool):
    if not shutil.which(tool):
        raise DiffError(f"{tool} not found on PATH. Install ffmpeg.")
    return tool


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


# ── probing ──────────────────────────────────────────────────────────────────

def probe(path):
    need("ffprobe")
    r = run(["ffprobe", "-v", "error", "-print_format", "json",
             "-show_format", "-show_streams", str(path)])
    if r.returncode:
        raise DiffError(f"ffprobe could not read {path}: {r.stderr.strip()[:200]}")
    d = json.loads(r.stdout)
    v = next((s for s in d["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in d["streams"] if s["codec_type"] == "audio"), None)
    fps = None
    if v and v.get("r_frame_rate", "0/0") != "0/0":
        n, _, den = v["r_frame_rate"].partition("/")
        fps = float(n) / float(den or 1)
    return {
        "path": str(path),
        "duration": float(d["format"].get("duration") or 0),
        "video": bool(v),
        "width": int(v["width"]) if v else None,
        "height": int(v["height"]) if v else None,
        "fps": fps,
        "vcodec": v.get("codec_name") if v else None,
        "pix_fmt": v.get("pix_fmt") if v else None,
        "audio": bool(a),
        "channels": int(a["channels"]) if a else None,
        "sample_rate": int(a["sample_rate"]) if a else None,
        "acodec": a.get("codec_name") if a else None,
    }


def compare_containers(pa, pb):
    """Structural differences, reported BEFORE any pixel work.

    If two files are different lengths or different sizes, that is the finding. Running
    a frame diff first and reporting a thousand differing frames buries it.
    """
    out = []
    if pa["video"] and pb["video"]:
        if (pa["width"], pa["height"]) != (pb["width"], pb["height"]):
            out.append({"kind": "resolution", "a": f'{pa["width"]}x{pa["height"]}',
                        "b": f'{pb["width"]}x{pb["height"]}',
                        "why": "different frame sizes; a pixel comparison would be meaningless "
                               "without a scale, and scaling invents differences of its own"})
        if pa["fps"] and pb["fps"] and abs(pa["fps"] - pb["fps"]) > 0.01:
            out.append({"kind": "framerate", "a": f'{pa["fps"]:.3f}', "b": f'{pb["fps"]:.3f}',
                        "why": "frames will not line up; every marker after the first would drift"})
    if pa["duration"] and pb["duration"]:
        delta = abs(pa["duration"] - pb["duration"])
        if delta > 0.5:
            out.append({"kind": "duration", "a": f'{pa["duration"]:.2f}s',
                        "b": f'{pb["duration"]:.2f}s',
                        "why": f"{delta:.2f}s apart; the shorter file ends early or the longer "
                               "one has extra material"})
    if pa["video"] != pb["video"] or pa["audio"] != pb["audio"]:
        out.append({"kind": "streams",
                    "a": f'video={pa["video"]} audio={pa["audio"]}',
                    "b": f'video={pb["video"]} audio={pb["audio"]}',
                    "why": "one file is missing a whole stream"})
    if pa["audio"] and pb["audio"] and pa["channels"] != pb["channels"]:
        out.append({"kind": "channels", "a": str(pa["channels"]), "b": str(pb["channels"]),
                    "why": "channel counts differ; a null test would compare the wrong pairs"})
    return out


# ── video ────────────────────────────────────────────────────────────────────

PSNR_LINE = re.compile(r"n:\s*(\d+).*?psnr_avg:\s*([\d.]+|inf)")


def video_psnr(a, b, limit=None):
    """Per-frame PSNR via ffmpeg's own filter. Returns [(frame_index, psnr_db)]."""
    need("ffmpeg")
    with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as tf:
        log = tf.name
    cmd = ["ffmpeg", "-v", "error", "-nostdin"]
    if limit:
        cmd += ["-t", str(limit)]
    cmd += ["-i", str(a)]
    if limit:
        cmd += ["-t", str(limit)]
    cmd += ["-i", str(b),
            "-lavfi", f"psnr=stats_file={log}", "-f", "null", "-"]
    r = run(cmd)
    text = Path(log).read_text("utf-8", "replace") if Path(log).exists() else ""
    Path(log).unlink(missing_ok=True)
    if not text.strip():
        raise DiffError("ffmpeg produced no PSNR data. "
                        + (r.stderr.strip()[:300] or "check that both files decode."))
    out = []
    for line in text.splitlines():
        m = PSNR_LINE.search(line)
        if m:
            val = float("inf") if m.group(2) == "inf" else float(m.group(2))
            out.append((int(m.group(1)), val))
    if not out:
        raise DiffError("PSNR log had no parseable frames; ffmpeg's stats format may have changed. "
                        f"First line was: {text.splitlines()[0][:120]!r}")
    return out


def median(xs):
    s = sorted(xs)
    n = len(s)
    if not n:
        return 0.0
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def flag_frames(frames, absolute=None, drop_db=6.0):
    """Which frames differ MORE than this pair's own encoding noise.

    Returns (flagged, baseline, threshold). A finite PSNR of 'inf' means identical.
    """
    finite = [v for _, v in frames if math.isfinite(v)]
    if not finite:
        return [], float("inf"), None          # every frame identical
    baseline = median(finite)
    if absolute is not None:
        thr = absolute
    else:
        # A frame is interesting when it is meaningfully worse than the file's own
        # typical frame, not when it is worse than some number picked for a codec
        # this file may not use.
        thr = baseline - drop_db
    flagged = [(n, v) for n, v in frames if math.isfinite(v) and v < thr]
    return flagged, baseline, thr


def group_ranges(flagged, fps, gap_frames=6):
    """Collapse flagged frames into contiguous ranges, so a one-second problem is ONE
    marker rather than twenty-four."""
    if not flagged:
        return []
    runs, start, prev, worst = [], flagged[0][0], flagged[0][0], flagged[0][1]
    for n, v in flagged[1:]:
        if n - prev <= gap_frames:
            prev, worst = n, min(worst, v)
        else:
            runs.append((start, prev, worst))
            start, prev, worst = n, n, v
    runs.append((start, prev, worst))
    out = []
    for s, e, w in runs:
        out.append({
            "start_frame": s, "end_frame": e, "frames": e - s + 1,
            "start_tc": timecode(s, fps), "end_tc": timecode(e + 1, fps),
            "worst_psnr_db": round(w, 2),
        })
    return out


def timecode(frame, fps):
    if not fps:
        return f"frame {frame}"
    total = frame / fps
    h = int(total // 3600)
    m = int(total % 3600 // 60)
    s = int(total % 60)
    f = int(round((total - int(total)) * fps))
    if f >= round(fps):
        f, s = 0, s + 1
    return f"{h:02d}:{m:02d}:{s:02d}:{f:02d}"


def write_edl(ranges, fps, path, title="RENDER DIFF"):
    """A marker EDL an NLE can import. CMX3600-ish; markers only."""
    lines = [f"TITLE: {title}", "FCM: NON-DROP FRAME", ""]
    for i, r in enumerate(ranges, 1):
        lines.append(f"{i:03d}  AX       V     C        "
                     f"{r['start_tc']} {r['end_tc']} {r['start_tc']} {r['end_tc']}")
        lines.append(f" * DIFF {r['frames']} FRAME(S)  WORST {r['worst_psnr_db']} dB")
        lines.append("")
    Path(path).write_text("\n".join(lines), "utf-8")
    return path


# ── stills ───────────────────────────────────────────────────────────────────

def image_diff(a, b, out=None, tiles=24):
    try:
        from PIL import Image, ImageChops
    except ImportError:
        raise DiffError("stills need Pillow.  pip3 install Pillow")
    ia, ib = Image.open(a).convert("RGB"), Image.open(b).convert("RGB")
    if ia.size != ib.size:
        raise DiffError(f"different sizes: {ia.size} vs {ib.size}. Scaling would invent "
                        "differences; resize deliberately and re-run.")
    d = ImageChops.difference(ia, ib)
    bbox = d.getbbox()
    w, h = ia.size
    # Per-tile mean difference, so the report can say WHERE, not just how much.
    tw, th = max(w // tiles, 1), max(h // tiles, 1)
    hot = []
    for ty in range(0, h, th):
        for tx in range(0, w, tw):
            box = (tx, ty, min(tx + tw, w), min(ty + th, h))
            # tobytes() rather than getdata(): getdata is deprecated in Pillow 12 and
            # emits a warning on every tile, which is a lot of noise for a 24x24 grid.
            raw = d.crop(box).tobytes()
            if not raw:
                continue
            mean = sum(raw) / len(raw)
            if mean > 2.0:
                hot.append({"box": box, "mean_delta": round(mean, 2)})
    hot.sort(key=lambda x: -x["mean_delta"])
    allraw = d.tobytes()
    overall = sum(allraw) / len(allraw) if allraw else 0.0
    peak = max(allraw) if allraw else 0
    if out:
        # Autocontrast makes a 1-level difference visible; without it a real
        # difference can render as an all-black image and read as "no difference".
        from PIL import ImageOps
        ImageOps.autocontrast(d.convert("L")).save(out)
    return {"identical": bbox is None, "bbox": bbox, "mean_delta": round(overall, 6),
            "peak_delta": peak, "hot_tiles": hot[:12], "size": ia.size,
            "diff_image": str(out) if out else None}


# ── audio ────────────────────────────────────────────────────────────────────

def audio_null(a, b):
    """Phase-invert null test: sum A with -B and measure what is left.

    This is the check audio practitioners already do by hand, and it is exact --
    identical audio nulls to silence. The residual level IS the answer.
    """
    need("ffmpeg")
    # `volume=-1` multiplies the samples by -1, which is a phase invert, and it works
    # per-channel on any layout. Summing that with the original cancels everything the
    # two files share; whatever is left is the difference, exactly.
    #
    # -v info, NOT -v error: astats writes its summary at INFO level, so quieting the
    # log to error throws away the only output this function reads. That looks
    # identical to "the tool is broken" and cost a debugging pass to find.
    r = run(["ffmpeg", "-v", "info", "-nostdin", "-i", str(a), "-i", str(b),
             "-filter_complex",
             "[1:a]volume=-1[inv];[0:a][inv]amix=inputs=2:normalize=0,astats[out]",
             "-map", "[out]", "-f", "null", "-"])
    peak = rms = None
    for line in r.stderr.splitlines():
        # Take the OVERALL block's values, which come last, so later hits win.
        if "Peak level dB" in line:
            try:
                peak = float(line.rsplit(":", 1)[-1].strip())
            except ValueError:
                pass
        elif "RMS level dB" in line:
            try:
                rms = float(line.rsplit(":", 1)[-1].strip())
            except ValueError:
                pass
    if peak is None and rms is None:
        raise DiffError("astats returned no levels; " + (r.stderr.strip()[-400:] or "unknown"))
    if peak == float("-inf") or (peak is not None and peak < -300):
        peak = float("-inf")
    return {"residual_peak_db": peak, "residual_rms_db": rms,
            "nulls": (peak is not None and peak < -90),
            "why": "identical audio cancels to digital silence; anything above about "
                   "-90 dBFS peak is a real difference, and above -60 is audible"}


# ── driver ───────────────────────────────────────────────────────────────────

def kind_of(p):
    e = Path(p).suffix.lower()
    if e in IMAGE_EXT:
        return "image"
    if e in AUDIO_EXT:
        return "audio"
    if e in VIDEO_EXT:
        return "video"
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("a", type=Path)
    ap.add_argument("b", type=Path)
    ap.add_argument("--out", type=Path, help="write a difference image (stills only)")
    ap.add_argument("--edl", type=Path, help="write a marker EDL (video only)")
    ap.add_argument("--absolute", type=float, metavar="DB",
                    help="fixed PSNR threshold instead of one derived from this pair")
    ap.add_argument("--drop", type=float, default=6.0, metavar="DB",
                    help="dB below the pair's own median that counts as a difference (default 6)")
    ap.add_argument("--limit", type=float, metavar="SEC", help="only compare the first N seconds")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    for f in (a.a, a.b):
        if not f.exists():
            print(f"ERROR: file not found: {f}", file=sys.stderr)
            return 2
    ka, kb = kind_of(a.a), kind_of(a.b)
    if ka is None or kb is None:
        print(f"ERROR: unrecognised extension ({a.a.suffix} / {a.b.suffix}).", file=sys.stderr)
        return 2
    if ka != kb:
        print(f"ERROR: comparing a {ka} against a {kb}.", file=sys.stderr)
        return 2

    try:
        result = {"a": str(a.a), "b": str(a.b), "kind": ka}
        if ka == "image":
            result.update(image_diff(a.a, a.b, a.out))
            differs = not result["identical"]
        else:
            pa, pb = probe(a.a), probe(a.b)
            result["container"] = compare_containers(pa, pb)
            blocking = [c for c in result["container"]
                        if c["kind"] in ("resolution", "framerate", "streams")]
            if ka == "audio" or (not pa["video"] and not pb["video"]):
                result.update(audio_null(a.a, a.b))
                differs = not result["nulls"]
            elif blocking:
                # Refuse rather than produce markers that are wrong in a way that
                # looks right. The structural finding IS the finding.
                result["frames"] = None
                differs = True
            else:
                frames = video_psnr(a.a, a.b, a.limit)
                flagged, baseline, thr = flag_frames(frames, a.absolute, a.drop)
                ranges = group_ranges(flagged, pa["fps"])
                result.update({
                    "compared_frames": len(frames),
                    "identical_frames": sum(1 for _, v in frames if not math.isfinite(v)),
                    "baseline_psnr_db": None if baseline == float("inf") else round(baseline, 2),
                    "threshold_db": None if thr is None else round(thr, 2),
                    "ranges": ranges,
                })
                if a.edl and ranges:
                    result["edl"] = write_edl(ranges, pa["fps"], a.edl)
                differs = bool(ranges) or bool(result["container"])
    except DiffError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    if a.json:
        print(json.dumps(result, indent=2, default=str))
        return 1 if differs else 0

    report(result)
    return 1 if differs else 0


def report(r):
    print(f"\n{Path(r['a']).name}  vs  {Path(r['b']).name}   [{r['kind']}]")
    for c in r.get("container") or []:
        print(f"\n  🔴 {c['kind'].upper()}: {c['a']}  vs  {c['b']}")
        print(f"      {c['why']}")

    if r["kind"] == "image":
        if r["identical"]:
            print("\n  IDENTICAL — every pixel matches.\n")
            return
        print(f"\n  DIFFERS. mean delta {r['mean_delta']:g}/255, peak {r['peak_delta']}/255")
        print(f"  bounding box of all differences: {r['bbox']}  (image {r['size'][0]}x{r['size'][1]})")
        bw, bh = r['bbox'][2]-r['bbox'][0], r['bbox'][3]-r['bbox'][1]
        print(f"  that box is {bw}x{bh}px of a {r['size'][0]}x{r['size'][1]} frame")
        if not r["hot_tiles"]:
            print("\n  No REGION exceeded the tile threshold — the difference is too small or too")
            print("  localised to raise a tile average. The bounding box above is where it is.")
        if r["hot_tiles"]:
            print("\n  worst regions (x0,y0,x1,y1):")
            for t in r["hot_tiles"][:6]:
                print(f"    {str(t['box']):<28} mean delta {t['mean_delta']}")
        if r.get("diff_image"):
            print(f"\n  difference map written to {r['diff_image']}")
            print("  (autocontrasted — a 1-level difference is invisible otherwise)")
        print()
        return

    if "nulls" in r:
        v = "NULLS TO SILENCE — identical" if r["nulls"] else "DOES NOT NULL — the audio differs"
        print(f"\n  {v}")
        print(f"  residual peak {r['residual_peak_db']} dBFS   rms {r['residual_rms_db']} dBFS")
        print(f"  {r['why']}\n")
        return

    if r.get("frames", 0) is None:
        print("\n  Refusing to compare frames while the files differ structurally.")
        print("  Fix the mismatch above, or the markers would be confidently wrong.\n")
        return

    n, ident = r["compared_frames"], r["identical_frames"]
    print(f"\n  compared {n} frames · {ident} bit-identical")
    if r["baseline_psnr_db"] is None:
        print("  every frame identical — nothing to mark.\n")
        return
    print(f"  this pair's own baseline: {r['baseline_psnr_db']} dB PSNR "
          f"(the encoding-noise floor)")
    print(f"  flagging frames below:    {r['threshold_db']} dB")
    if not r["ranges"]:
        print("\n  NO OUTLIERS. The two files differ only by uniform encoding noise.")
        print("  That is what a re-encode of the same timeline looks like.\n")
        return
    print(f"\n  🔴 {len(r['ranges'])} region(s) differ beyond encoding noise:\n")
    for x in r["ranges"]:
        print(f"    {x['start_tc']} → {x['end_tc']}   {x['frames']} frame(s), "
              f"worst {x['worst_psnr_db']} dB")
    if r.get("edl"):
        print(f"\n  markers written to {r['edl']}")
    print("\n  caveat: PSNR is a whole-frame number. It finds WHERE to look; it does not")
    print("  tell you what changed, and it cannot tell an intended change from a mistake.\n")


if __name__ == "__main__":
    sys.exit(main())
