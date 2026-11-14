#!/usr/bin/env python
"""Design the candidate voices (A/B/C by default) with VoiceDesign and write audition samples plus clone references.

  .venv/bin/python design_voices.py [--out .] [--voices A B C]

Writes, under --out:
  raw/design-<k>.wav          untouched VoiceDesign output
  ref/ref-<k>.wav, .txt       the clone reference (edge-trimmed, slowed by REF_TEMPO) and its transcript
  samples/candidate-<k>.m4a   the audition sample to play to the owner
  samples/report.json         prompt, pitch (F0), wpm and whisper WER per voice

Play all candidates to the owner and let them pick by ear. The numbers only rule out broken takes.
"""
import argparse, json, os, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import voice_common as vc
from analyze_clip import analyze

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--out", default=".")
ap.add_argument("--voices", nargs="*", help="voice keys from VOICES (default: all)")
a = ap.parse_args()
O = a.out
for d in ("samples", "ref", "raw"):
    os.makedirs(os.path.join(O, d), exist_ok=True)

t = time.time(); m = vc.load(vc.DESIGN_MODEL)
report = {"design_model": vc.DESIGN_MODEL, "load_s": round(time.time() - t, 1),
          "params": dict(seed=vc.SEED, temperature=vc.TEMPERATURE, top_k=vc.TOP_K, ref_tempo=vc.REF_TEMPO,
                         target_wpm=vc.TARGET_WPM), "voices": {}}
for k, prompt in vc.VOICES.items():
    if a.voices and k not in a.voices:
        continue
    y, dt = vc.gen(m, vc.PASSAGE, instruct=prompt)
    raw = os.path.join(O, "raw", f"design-{k}.wav"); vc.write_wav(raw, y)
    vc.write_wav(os.path.join(O, "ref", f"ref-{k}.wav"), vc.atempo(vc.trim(y), vc.REF_TEMPO))
    open(os.path.join(O, "ref", f"ref-{k}.txt"), "w").write(vc.PASSAGE)
    s, tempo, wpm_raw = vc.normalize_pace(y, vc.PASSAGE)
    cw = os.path.join(O, "samples", f"candidate-{k}.wav"); vc.write_wav(cw, s)
    vc.m4a(cw, os.path.join(O, "samples", f"candidate-{k}.m4a"))
    r, rr = analyze(cw, vc.PASSAGE), analyze(raw, vc.PASSAGE)
    report["voices"][k] = dict(prompt=prompt, gen_s=round(dt, 1), pace_tempo_applied=tempo,
                               raw_wpm_trim=rr["wpm_trim"], raw_f0_med=rr["f0_med"], **r)
    print(k, {kk: v for kk, v in report["voices"][k].items() if kk != "prompt"}, flush=True)
json.dump(report, open(os.path.join(O, "samples", "report.json"), "w"), indent=1)
