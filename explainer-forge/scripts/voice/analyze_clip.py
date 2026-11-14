#!/usr/bin/env python
"""Measure one narration clip: duration, words per minute (three ways), pitch (F0) and a whisper word error rate.

  .venv/bin/python analyze_clip.py clip.wav "the text it should say"

Also importable: analyze(path, ref_text) -> dict. `hyp` is what whisper heard: read it. Words you did not write mean
the model hallucinated; re-render or reword. Whisper cannot confirm how a name is pronounced: a person must listen.
"""
import re, sys

import numpy as np

WHISPER = "mlx-community/whisper-large-v3-turbo"


def norm(s):
    return re.findall(r"[a-z0-9']+", s.lower().replace("-", " "))


def wer(ref, hyp):
    r, h = norm(ref), norm(hyp)
    d = np.zeros((len(r) + 1, len(h) + 1), int); d[:, 0] = range(len(r) + 1); d[0, :] = range(len(h) + 1)
    for i in range(1, len(r) + 1):
        for j in range(1, len(h) + 1):
            d[i, j] = min(d[i - 1, j] + 1, d[i, j - 1] + 1, d[i - 1, j - 1] + (r[i - 1] != h[j - 1]))
    return d[-1, -1] / max(1, len(r))


def analyze(path, ref_text):
    import librosa, soundfile as sf, mlx_whisper
    y, sr = sf.read(path, dtype="float32")
    if y.ndim > 1:
        y = y.mean(1)
    y16 = librosa.resample(y, orig_sr=sr, target_sr=16000)
    f0, vf, _ = librosa.pyin(y16, fmin=70, fmax=400, sr=16000, frame_length=1024)
    f = f0[vf & ~np.isnan(f0)]
    st = 12 * np.log2(f / np.median(f))
    iv = librosa.effects.split(y16, top_db=30, frame_length=512, hop_length=128)
    merged = [list(iv[0])]          # merge gaps under 0.12 s (stops inside words); the rest are pauses
    for s, e in iv[1:]:
        if (s - merged[-1][1]) / 16000 < 0.12: merged[-1][1] = e
        else: merged.append([s, e])
    speech = sum(e - s for s, e in merged) / 16000; total = len(y) / sr; span = (merged[-1][1] - merged[0][0]) / 16000
    hyp = mlx_whisper.transcribe(path, path_or_hf_repo=WHISPER, language="en")["text"].strip()
    n = len(norm(ref_text))
    return dict(dur=round(total, 2), speech_s=round(speech, 2), wpm_total=round(n / total * 60),
                wpm_trim=round(n / span * 60), wpm_speech=round(n / speech * 60),
                f0_med=round(float(np.median(f))), f0_p10=round(float(np.percentile(f, 10))),
                f0_p90=round(float(np.percentile(f, 90))), f0_sd_st=round(float(st.std()), 2),
                f0_range_st=round(float(np.percentile(st, 95) - np.percentile(st, 5)), 1),
                wer=round(float(wer(ref_text, hyp)), 3), hyp=hyp)


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] in ("-h", "--help"):
        print(__doc__); sys.exit(0 if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help") else 2)
    import json
    print(json.dumps(analyze(sys.argv[1], sys.argv[2]), indent=1))
