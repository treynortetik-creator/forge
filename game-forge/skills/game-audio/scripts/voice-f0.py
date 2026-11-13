#!/usr/bin/env python3
# Voice F0 gate for casting. Needs Praat bindings and ffmpeg:
#   python3 -m venv /tmp/f0venv && /tmp/f0venv/bin/pip install praat-parselmouth numpy
#   /tmp/f0venv/bin/python voice-f0.py --pool audio-src/voice/<character>-*.m4a
"""Praat two-pass F0 (Hirst: floor=0.75*Q1, ceiling=1.5*Q3 of a wide first pass) + spectral centroid.
Usage: voice-f0.py [--pool] files...  (decodes via ffmpeg to wav)"""
import sys, json, subprocess, tempfile, os
import numpy as np
import parselmouth

args = sys.argv[1:]
pool = False
if args and args[0] == '--pool':
    pool = True; args = args[1:]


def load(path):
    tmp = tempfile.mktemp(suffix='.wav')
    subprocess.run(['ffmpeg', '-v', 'quiet', '-y', '-i', path, '-ac', '1', '-ar', '22050', tmp], check=True)
    s = parselmouth.Sound(tmp); os.remove(tmp); return s


def f0_values(s, lo, hi):
    p = s.to_pitch_ac(time_step=0.01, pitch_floor=lo, pitch_ceiling=hi)
    v = p.selected_array['frequency']
    return v[v > 0]


def centroid(s):
    x = s.values[0]; sr = s.sampling_frequency
    win = np.hanning(1024); freqs = np.fft.rfftfreq(1024, 1 / sr)
    rms = [np.sqrt(np.mean(x[i:i + 1024] ** 2)) for i in range(0, len(x) - 1024, 512)]
    if not rms: return None
    gate = max(rms) * 10 ** (-30 / 20); c = []
    for j, i in enumerate(range(0, len(x) - 1024, 512)):
        if rms[j] < gate: continue
        m = np.abs(np.fft.rfft(x[i:i + 1024] * win)); c.append((freqs * m).sum() / (m.sum() + 1e-12))
    return float(np.median(c)) if c else None


sounds = {a: load(a) for a in args}
# pass 1, wide
first = {a: f0_values(s, 50, 600) for a, s in sounds.items()}
out = {}
if pool:
    allv = np.concatenate([v for v in first.values() if len(v)])
    q1, q3 = np.percentile(allv, 25), np.percentile(allv, 75)
    lo, hi = max(40, 0.75 * q1), 1.5 * q3
    vals = np.concatenate([f0_values(s, lo, hi) for s in sounds.values()])
    cents = [c for c in (centroid(s) for s in sounds.values()) if c]
    out['_pool'] = {'f0_med': round(float(np.median(vals)), 1), 'f0_p10': round(float(np.percentile(vals, 10)), 1),
                    'f0_p90': round(float(np.percentile(vals, 90)), 1), 'range': [round(lo), round(hi)],
                    'cent_med': round(float(np.median(cents))) if cents else None, 'n_files': len(sounds),
                    'n_frames': int(len(vals))}
else:
    for a, s in sounds.items():
        v1 = first[a]
        if len(v1) < 10:
            out[a] = {'err': 'few voiced'}; continue
        lo, hi = max(40, 0.75 * np.percentile(v1, 25)), 1.5 * np.percentile(v1, 75)
        v = f0_values(s, lo, hi)
        out[a] = {'f0_med': round(float(np.median(v)), 1), 'f0_p10': round(float(np.percentile(v, 10)), 1),
                  'f0_p90': round(float(np.percentile(v, 90)), 1), 'range': [round(lo), round(hi)],
                  'cent_med': round(centroid(s) or 0), 'dur_s': round(s.duration, 2)}
json.dump(out, sys.stdout)
