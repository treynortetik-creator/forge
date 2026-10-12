#!/usr/bin/env python3
"""Look at a song without ears: tempo, key, loudness and brightness over time, section boundaries, a spectrogram PNG.

Decodes with ffmpeg first (libsndfile, and so librosa, cannot read m4a/aac). Tempo is a guess: beat trackers
often land on half or double time, so the half/double values are printed beside it. Key comes from a
Krumhansl-style chroma template fit and the fit score is printed; below about 0.6, treat it as unknown.
Sections come from timbre change (agglomerative clustering on MFCCs): boundaries, not labels.

Run (needs ffmpeg on PATH):
    uv run --with librosa --with matplotlib --with numpy python song_scan.py song.m4a [more.m4a ...] [--outdir DIR] [--sections 8] [--json]
For lyrics from a dense mix, separate the vocal first (see skills/track-check/SKILL.md), then transcribe the stem.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile

MAJ = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
MIN = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
NOTES = "C C# D D# E F F# G G# A A# B".split()


def key_of(chroma, np):
    c = chroma.mean(axis=1)
    best = max((np.corrcoef(np.roll(np.array(p), i), c)[0, 1], f"{NOTES[i]} {m}")
               for p, m in ((MAJ, "major"), (MIN, "minor")) for i in range(12))
    return best[1], float(best[0])


def scan(path: str, outdir: str | None, n_sections: int, make_png: bool) -> dict:
    import librosa
    import librosa.display
    import matplotlib
    import numpy as np
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    wav = os.path.join(tempfile.mkdtemp(), "a.wav")
    subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-i", path, "-ac", "1", "-ar", "22050", wav], check=True)
    y, sr = librosa.load(wav, sr=22050, mono=True)
    dur = len(y) / sr
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    tempo = float(np.atleast_1d(tempo)[0])
    harm, perc = librosa.effects.hpss(y)
    key, fit = key_of(librosa.feature.chroma_cqt(y=harm, sr=sr), np)
    rms = librosa.feature.rms(y=y)[0]
    cent = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    t = librosa.times_like(rms, sr=sr)
    mf = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    bounds = [float(b) for b in librosa.frames_to_time(librosa.segment.agglomerative(mf, n_sections), sr=sr)]
    db = 20 * np.log10(rms + 1e-9)
    w = 5
    energy = [float(np.mean(db[(t >= s) & (t < s + w)])) for s in np.arange(0, dur, w)]
    res = {"file": os.path.basename(path), "seconds": round(dur, 1), "tempo_bpm": round(tempo, 1),
           "tempo_alternatives": [round(tempo * 2, 1), round(tempo / 2, 1)], "key": key, "key_fit": round(fit, 2),
           "loudness_db_p10_p95": [round(float(np.percentile(db, 10)), 1), round(float(np.percentile(db, 95)), 1)],
           "brightness_median_hz": round(float(np.median(cent))), "percussive_share": round(float(np.sum(perc ** 2) / np.sum(y ** 2)), 2),
           "section_boundaries_s": [round(b, 1) for b in bounds], "energy_db_per_5s": [round(e) for e in energy]}
    if make_png:
        fig, ax = plt.subplots(2, 1, figsize=(16, 7), sharex=True)
        S = librosa.amplitude_to_db(np.abs(librosa.stft(y, n_fft=2048, hop_length=512)), ref=np.max)
        librosa.display.specshow(S, sr=sr, hop_length=512, x_axis="time", y_axis="log", ax=ax[0], cmap="magma")
        ax[0].set_title(f"{os.path.basename(path)}  ~{tempo:.0f} bpm  {key} (fit {fit:.2f})")
        ax[1].plot(t, db, lw=0.7, label="loudness dB")
        ax[1].plot(t, 20 * np.log10(cent / cent.max()), lw=0.5, alpha=0.6, label="brightness (relative dB)")
        for b in bounds:
            ax[0].axvline(b, color="cyan", lw=0.8)
            ax[1].axvline(b, color="gray", lw=0.8, ls="--")
        ax[1].legend(loc="lower right")
        ax[1].set_xlabel("seconds")
        plt.tight_layout()
        png = os.path.join(outdir or os.path.dirname(os.path.abspath(path)), os.path.splitext(os.path.basename(path))[0] + ".scan.png")
        plt.savefig(png, dpi=80)
        plt.close(fig)
        res["png"] = png
    return res


def show(r: dict) -> None:
    mm = lambda s: f"{int(s // 60)}:{s % 60:04.1f}"  # noqa: E731
    print(f"\n== {r['file']}  {r['seconds']:.0f}s  tempo~{r['tempo_bpm']:.0f} bpm (or {r['tempo_alternatives'][0]:.0f}/{r['tempo_alternatives'][1]:.0f})  "
          f"key~{r['key']} (fit {r['key_fit']:.2f}{', weak' if r['key_fit'] < 0.6 else ''})")
    print(f"   loudness {r['loudness_db_p10_p95'][0]:.0f} to {r['loudness_db_p10_p95'][1]:.0f} dB | brightness median {r['brightness_median_hz']} Hz | percussive share {r['percussive_share']:.0%}")
    print("   section boundaries:", " | ".join(mm(b) for b in r["section_boundaries_s"]))
    print("   5 s energy (dB):", " ".join(str(e) for e in r["energy_db_per_5s"]))
    if r.get("png"):
        print("   spectrogram:", r["png"])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Tempo, key, loudness/brightness curve, sections and a spectrogram PNG for one or more songs.")
    ap.add_argument("songs", nargs="+", help="audio files (anything ffmpeg can decode)")
    ap.add_argument("--outdir", help="where to write <song>.scan.png (default: beside each song)")
    ap.add_argument("--sections", type=int, default=8, help="number of timbre-based segments (default 8)")
    ap.add_argument("--no-png", action="store_true")
    ap.add_argument("--json", action="store_true", help="print JSON instead of the text summary")
    a = ap.parse_args(argv)
    if a.outdir:
        os.makedirs(a.outdir, exist_ok=True)
    out = [scan(p, a.outdir, a.sections, not a.no_png) for p in a.songs]
    if a.json:
        print(json.dumps(out, indent=2))
    else:
        for r in out:
            show(r)
    return 0


if __name__ == "__main__":
    sys.exit(main())
