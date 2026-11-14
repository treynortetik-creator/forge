#!/usr/bin/env python
"""Render every narration line in ONE consistent voice (Qwen3-TTS Base clone of your reference clip).

  .venv/bin/python render_lines.py lines.json [--voice A] [--ref-dir ref] [--out out] [--pace] [--check] [--only id ...]

lines.json: [{"id": "s1c0", "scene": 1, "scene_title": "Hook", "caption": "Shown text", "text": "Spoken text"}, ...]
`text` is the TTS spelling (respellings, spelled-out letters); `caption` keeps the real spelling. If `text` is missing,
`caption` is used.

Default: natural pace, no trim (stitch_narration.py trims and applies ONE tempo to all clips; that is how the speed
is set). --pace trims and slows each clip toward TARGET_WPM on its own (older method; uneven across lines).
--check runs analyze_clip on every rendered clip -> out/check.json; flags WER over 0.10. Read every `hyp`.
Same text + same reference + same model and settings = identical audio, so re-render single lines with --only.
"""
import argparse, json, os, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import voice_common as vc

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("lines")
ap.add_argument("--voice", default=vc.DEFAULT_VOICE)
ap.add_argument("--ref-dir", default="ref", help="folder with ref-<voice>.wav and ref-<voice>.txt")
ap.add_argument("--out", default="out")
ap.add_argument("--pace", action="store_true", help="trim + slow each clip toward TARGET_WPM")
ap.add_argument("--only", nargs="*", help="render only these ids")
ap.add_argument("--check", action="store_true")
a = ap.parse_args()

lines = json.load(open(a.lines)); os.makedirs(a.out, exist_ok=True)
ref = os.path.join(a.ref_dir, f"ref-{a.voice}.wav")
ref_text = open(os.path.join(a.ref_dir, f"ref-{a.voice}.txt")).read().strip()
t = time.time(); model = vc.load(vc.CLONE_MODEL); load_s = round(time.time() - t, 1)
mpath = os.path.join(a.out, "manifest.json")
manifest = json.load(open(mpath)) if (a.only and os.path.exists(mpath)) else {}
manifest.update(model=vc.CLONE_MODEL, voice=a.voice, ref=ref, voice_design_prompt=vc.VOICES.get(a.voice),
                seed=vc.SEED, temperature=vc.TEMPERATURE, top_k=vc.TOP_K,
                target_wpm=vc.TARGET_WPM if a.pace else None, load_s=load_s)
manifest.setdefault("clips", {})
for ln in lines:
    if a.only and ln["id"] not in a.only:
        continue
    say = ln.get("text") or ln["caption"]
    y, dt = vc.gen(model, say, ref_audio=ref, ref_text=ref_text)
    info = dict(gen_s=round(dt, 1), text=say)
    if a.pace:
        y, info["tempo"], info["wpm_before"] = vc.normalize_pace(y, say)
    path = os.path.join(a.out, f"{ln['id']}.wav"); vc.write_wav(path, y); info["dur_s"] = round(len(y) / vc.SR, 2)
    manifest["clips"][ln["id"]] = info; print(ln["id"], {k: v for k, v in info.items() if k != "text"}, flush=True)
json.dump(manifest, open(mpath, "w"), indent=1)

if a.check:
    from analyze_clip import analyze
    cpath = os.path.join(a.out, "check.json")
    res = json.load(open(cpath)) if os.path.exists(cpath) else {}
    for ln in lines:
        if a.only and ln["id"] not in a.only:
            continue
        say = ln.get("text") or ln["caption"]
        r = analyze(os.path.join(a.out, f"{ln['id']}.wav"), say); res[ln["id"]] = r
        print("CHECK", ln["id"], "wer", r["wer"], "wpm", r["wpm_trim"], "f0", r["f0_med"],
              "<<< READ hyp" if r["wer"] > 0.10 else "", flush=True)
    json.dump(res, open(cpath, "w"), indent=1)
