#!/usr/bin/env python
"""Drift test: is each candidate the same person across different sentences?

  .venv/bin/python drift_test.py [--ref-dir ref] [--out samples] [--voices A B C]

For each voice, renders 3 test sentences twice: designed fresh per line (VoiceDesign + prompt) and cloned from the
reference clip (Base + ref). Reports the spread of median pitch in semitones and the wpm per line. On the run this
came from, designing per line spread 4.1 semitones and 174-258 wpm for one voice; cloning spread 2.7 semitones and
146-194 wpm. That is why every line is cloned. Writes <out>/drift.json and the clips under <out>/drift/.
"""
import argparse, json, os, sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import voice_common as vc
from analyze_clip import analyze

S = ["Tap your card on the kiosk, choose a bike from the rack, and the dock lets go with a soft click.",
     "Rain moving in? The screen warns riders early and points to a covered return spot nearby.",
     "Bring the bike back ahead of schedule, and the spare minutes roll over to your next trip."]

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--ref-dir", default="ref"); ap.add_argument("--out", default="samples")
ap.add_argument("--voices", nargs="*")
a = ap.parse_args()
dd = os.path.join(a.out, "drift"); os.makedirs(dd, exist_ok=True)
VD, CL = vc.load(vc.DESIGN_MODEL), vc.load(vc.CLONE_MODEL)
out = {}
for k in vc.VOICES:
    if a.voices and k not in a.voices:
        continue
    ref_text = open(os.path.join(a.ref_dir, f"ref-{k}.txt")).read().strip()
    for mode in ("design_per_line", "clone_from_ref"):
        rows = []
        for i, t in enumerate(S):
            y, _ = (vc.gen(VD, t, instruct=vc.VOICES[k]) if mode == "design_per_line" else
                    vc.gen(CL, t, ref_audio=os.path.join(a.ref_dir, f"ref-{k}.wav"), ref_text=ref_text))
            p = os.path.join(dd, f"{k}_{mode}_{i}.wav"); vc.write_wav(p, y); r = analyze(p, t)
            rows.append(dict(f0_med=r["f0_med"], wpm_trim=r["wpm_trim"], wer=r["wer"], f0_sd_st=r["f0_sd_st"]))
        f = [r["f0_med"] for r in rows]
        out[f"{k}/{mode}"] = dict(rows=rows, f0_med_spread_hz=max(f) - min(f),
                                  f0_med_spread_semitones=round(float(12 * np.log2(max(f) / min(f))), 2))
        print("DRIFT", k, mode, "f0 med", f, "spread st", out[f"{k}/{mode}"]["f0_med_spread_semitones"],
              "wpm", [r["wpm_trim"] for r in rows], flush=True)
json.dump(out, open(os.path.join(a.out, "drift.json"), "w"), indent=1)
