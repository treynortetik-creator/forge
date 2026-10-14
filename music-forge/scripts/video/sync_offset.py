#!/usr/bin/env python3
"""Find where a generated sung clip sits in the song, from its own soundtrack, so the cut can slide it into place.

Lip-sync models that take an audio reference (HeyGen Video 1, Hailuo 3) pass that audio through into the clip's
soundtrack. Cross-correlating the clip's audio against the stem (or song) it was made from gives T, the song time at
the clip's first frame. Never place sung clips by lyric timestamps or by the window you asked for: generation windows
came back 0.3-0.6 s off their slots, which reads as bad lip sync even when the mouth is perfect.

    T          song time at clip pts 0 (seconds)
    enter_at   = slot_start - T: seconds into the clip the cut should start (negative = hold the first frame)
    peak       normalised cross-correlation at T (1.0 = the clip carries that audio exactly)

A low peak (under about 0.5) means the clip does not carry the reference audio (it re-sang, or the model writes its
own soundtrack): the number is meaningless, so check that clip by eye and ear instead.

Run (numpy via uv; ffmpeg on PATH):
    uv run --with numpy python sync_offset.py clips/14-sings.mp4 --ref stems/vocals.wav --nominal 48.0
    uv run --with numpy python sync_offset.py clips/14-sings.mp4 --ref stems/vocals.wav --slot 48.0 --write-sidecar
    uv run --with numpy python sync_offset.py clips/*.mp4 --ref song.m4a --json

--nominal defaults to the clip sidecar's audio_ref_start (written by build_clips.py), then its plan_time start.
--write-sidecar stores song_t0 and sync_peak in the clip's sidecar JSON; cut.py then enters the clip at the offset.
Decodes the full reference file (no -ss seek): AAC seeks were seen to shift audio by about 50 ms.
"""
from __future__ import annotations

import argparse
import json
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
            sys.exit("sync_offset.py needs numpy: run it with  uv run --with numpy python sync_offset.py ...")
        np = numpy
    return np


SR = 8000


def decode(path: str, sr: int = SR):
    """Mono float64 PCM of a whole file at sr Hz (full decode, never seeked)."""
    _need_np()
    r = subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-i", path, "-vn", "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
                       capture_output=True)
    if r.returncode:
        raise RuntimeError(f"ffmpeg could not decode {path}: {r.stderr.decode(errors='replace')[-300:]}")
    return np.frombuffer(r.stdout, np.float32).astype(np.float64)


def xcorr(needle, hay) -> tuple[int, float]:
    """Normalised cross-correlation of needle sliding over hay. Returns (best offset in samples, peak NCC)."""
    _need_np()
    n = len(needle)
    if n == 0 or len(hay) < n:
        raise ValueError("reference window is shorter than the clip audio")
    size = 1 << int(np.ceil(np.log2(len(hay) + n)))
    a = needle - needle.mean()
    c = np.fft.irfft(np.fft.rfft(hay, size) * np.conj(np.fft.rfft(a, size)), size)[: len(hay) - n + 1]
    cs = np.concatenate([[0.0], np.cumsum(hay)])
    cs2 = np.concatenate([[0.0], np.cumsum(hay ** 2)])
    win_var = (cs2[n:] - cs2[:-n]) - (cs[n:] - cs[:-n]) ** 2 / n
    ncc = c / (np.sqrt(np.maximum(win_var, 1e-12)) * np.sqrt((a ** 2).sum()) + 1e-12)
    k = int(np.argmax(ncc))
    return k, float(ncc[k])


def measure(clip_audio, ref_audio, nominal: float, search: float = 8.0, sr: int = SR) -> dict:
    """Search +-search seconds around nominal in ref for the clip's audio."""
    lo = max(0, int((nominal - search) * sr))
    hi = min(len(ref_audio), int((nominal + search) * sr) + len(clip_audio))
    k, peak = xcorr(clip_audio, ref_audio[lo:hi])
    return {"T": round((lo + k) / sr, 3), "peak": round(peak, 3), "nominal": round(nominal, 3),
            "clip_audio_s": round(len(clip_audio) / sr, 3)}


def sidecar_path(clip: str) -> str:
    return os.path.splitext(clip)[0] + ".json"


def read_sidecar(clip: str) -> dict:
    try:
        with open(sidecar_path(clip), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Cross-correlate each sung clip's own audio against the stem or song it was made from; report the song time "
                    "at the clip's first frame (T) and where the cut should enter it.",
        epilog="A peak under ~0.5 means the clip does not carry the reference audio; do not trust T for that clip.")
    ap.add_argument("clips", nargs="+", help="generated clip(s) with an audio track")
    ap.add_argument("--ref", required=True, help="the audio the clip was generated from: vocal stem for close-ups, song for wides")
    ap.add_argument("--nominal", type=float, help="song time the generation window started at (default: sidecar audio_ref_start, then plan_time)")
    ap.add_argument("--search", type=float, default=8.0, help="seconds either side of nominal to search (default 8)")
    ap.add_argument("--slot", type=float, help="song time the clip's slot starts in the cut; prints enter_at = slot - T")
    ap.add_argument("--min-peak", type=float, default=0.5, help="flag results below this peak (default 0.5)")
    ap.add_argument("--write-sidecar", action="store_true", help="store song_t0 and sync_peak in each clip's sidecar JSON for cut.py")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    _need_np()

    ref = decode(a.ref)
    results, low = {}, False
    for clip in a.clips:
        side = read_sidecar(clip)
        nominal = a.nominal
        if nominal is None:
            nominal = side.get("audio_ref_start")
        if nominal is None and side.get("plan_time"):
            nominal = side["plan_time"][0]
        if nominal is None:
            print(f"{clip}: no --nominal and no sidecar window; pass --nominal", file=sys.stderr)
            return 2
        audio = decode(clip)
        if audio.size < SR // 2:
            results[clip] = {"error": "no audio track (or under 0.5 s)"}
            continue
        r = measure(audio, ref, float(nominal), a.search)
        if a.slot is not None:
            r["enter_at"] = round(a.slot - r["T"], 3)
        r["ok"] = r["peak"] >= a.min_peak
        low |= not r["ok"]
        if a.write_sidecar and r["ok"]:
            side.update({"song_t0": r["T"], "sync_peak": r["peak"], "sync_ref": os.path.basename(a.ref)})
            with open(sidecar_path(clip), "w", encoding="utf-8") as f:
                json.dump(side, f, indent=1)
            r["sidecar"] = sidecar_path(clip)
        results[clip] = r
    if a.json:
        print(json.dumps(results, indent=1))
    else:
        for clip, r in results.items():
            if "error" in r:
                print(f"{os.path.basename(clip)}: {r['error']}")
                continue
            enter = f"  enter_at {r['enter_at']:+.3f}s" if "enter_at" in r else ""
            drift = r["T"] - r["nominal"]
            flag = "" if r["ok"] else "  LOW PEAK: clip does not carry this audio, T unreliable"
            print(f"{os.path.basename(clip)}: T {r['T']:.3f}s (asked {r['nominal']:.3f}, off {drift:+.3f}s)  peak {r['peak']:.2f}{enter}{flag}"
                  + ("  [sidecar updated]" if r.get("sidecar") else ""))
    return 1 if low else 0


if __name__ == "__main__":
    sys.exit(main())
