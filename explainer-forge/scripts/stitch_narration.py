#!/usr/bin/env python3
"""Stitch per-line narration clips into one track with exact cue times (the per-line FALLBACK; the default is one take: see audio_build.py). Speed is set HERE, once, for every line.

  python3 stitch_narration.py --lines lines.json --clips voice/out --out build [--target-wpm 180 | --tempo 1.21]
                              [--gaps 0.3,0.15,0.35,1.0] [--extra gaps.json]

Each clip is edge-trimmed, then ONE pitch-preserving atempo is applied to all of them (so the voice keeps one pace),
then they are joined with fixed silences: head, between lines, between scenes, tail. Cue times are exact sums of
measured clip lengths and gaps, so no alignment step is needed.

Speed: --target-wpm solves the tempo so the narration runs at that rate on the base gaps (180 was one product demo's approved
pace, not a default for other formats). --tempo sets the multiplier directly, for "make it 20% faster" by ear. A tempo
above 1.25 is flagged: listen for clipped words.
--extra gaps.json: {"<line id>": seconds} adds a pause before that line for a footage beat. It never changes tempo.

Writes <out>/clips/<id>.wav (tempo'd clips, used by captions.py), narration.wav (48 kHz, -16 LUFS),
narration.m4a, cues.json ({total, fps, tempo, scenes, lines:[{id, scene, title, start, dur, end, caption}]}),
and cue-table.md (per-line and per-scene wpm). Needs ffmpeg and ffprobe on PATH (or $FFMPEG / $FFPROBE).
"""
import argparse, json, os, re, shutil, subprocess, tempfile

FF = os.environ.get("FFMPEG", "ffmpeg"); FP = os.environ.get("FFPROBE", "ffprobe")
TRIM = ("silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,areverse,"
        "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.08,areverse")

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--lines", required=True); ap.add_argument("--clips", required=True); ap.add_argument("--out", required=True)
g = ap.add_mutually_exclusive_group()
g.add_argument("--target-wpm", type=float, default=180.0); g.add_argument("--tempo", type=float)
ap.add_argument("--gaps", default="0.3,0.15,0.35,1.0", help="head,line,scene,tail seconds (tail was 2.6 s before 0.2.0: that read as dead air)")
ap.add_argument("--extra", help="JSON {line_id: extra seconds before it}")
ap.add_argument("--fps", type=int, default=30)
a = ap.parse_args()

HEAD, GAP, SGAP, TAIL = map(float, a.gaps.split(","))
EXTRA = json.load(open(a.extra)) if a.extra else {}
lines = json.load(open(a.lines))
dur = lambda p: float(subprocess.check_output([FP, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p]))
words = lambda s: len(re.findall(r"[A-Za-z0-9']+", s))
run = lambda *x: subprocess.run([FF, "-nostdin", "-loglevel", "error", "-y", *x], check=True)
T = tempfile.mkdtemp(prefix="stitch-"); V = os.path.join(a.out, "clips"); os.makedirs(V, exist_ok=True)

nat = {}
for ln in lines:
    q = os.path.join(T, ln["id"] + "-trim.wav")
    run("-i", os.path.join(a.clips, ln["id"] + ".wav"), "-af", TRIM, "-ar", "24000", "-ac", "1", "-c:a", "pcm_s16le", q)
    nat[ln["id"]] = (q, dur(q))
W = sum(words(l["caption"]) for l in lines)
gaps = sum((SGAP if lines[i]["scene"] != lines[i - 1]["scene"] else GAP) for i in range(1, len(lines)))
S = sum(d for _, d in nat.values())
if a.tempo:
    tempo = a.tempo
else:  # W / ((S / t + gaps) / 60) = target  ->  t = S / (60 W / target - gaps)
    tempo = round(S / (60 * W / a.target_wpm - gaps), 3)
print(f"natural speech {W / S * 60:.0f} wpm; atempo {tempo}" + ("  <<< ABOVE 1.25, LISTEN FOR CLIPPED WORDS" if tempo > 1.25 else ""))

parts, t, cues, last = [], 0.0, [], None
def sil(s):
    global t
    p = os.path.join(T, f"sil{len(parts)}.wav")
    run("-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", f"{s:.4f}", "-c:a", "pcm_s16le", p)
    parts.append(p); t += dur(p)

sil(HEAD)
for ln in lines:
    i = ln["id"]
    if last is not None:
        sil((SGAP if ln["scene"] != last else GAP) + EXTRA.get(i, 0))
    q = os.path.join(V, i + ".wav")
    run("-i", nat[i][0], "-af", f"atempo={tempo}", "-ar", "24000", "-ac", "1", "-c:a", "pcm_s16le", q)
    d = dur(q)
    cues.append({"id": i, "scene": ln["scene"], "title": ln.get("scene_title", ""), "start": round(t, 3),
                 "dur": round(d, 3), "end": round(t + d, 3), "caption": ln["caption"]})
    parts.append(q); t += d; last = ln["scene"]
speak = cues[-1]["end"] - cues[0]["start"]
sil(TAIL)
lst = os.path.join(T, "concat.txt"); open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
raw = os.path.join(T, "raw.wav")
run("-f", "concat", "-safe", "0", "-i", lst, "-c", "pcm_s16le", raw)
nw = os.path.join(a.out, "narration.wav")
run("-i", raw, "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", nw)
run("-i", nw, "-c:a", "aac", "-b:a", "160k", os.path.join(a.out, "narration.m4a"))
total = dur(nw)
scenes = {}
for c in cues:
    scenes.setdefault(str(c["scene"]), c["start"])
json.dump({"total": round(total, 3), "fps": a.fps, "tempo": tempo, "scenes": scenes, "lines": cues},
          open(os.path.join(a.out, "cues.json"), "w"), indent=1)

with open(os.path.join(a.out, "cue-table.md"), "w") as f:
    f.write("| line | scene | start s | clip s | words | wpm | caption |\n|--|--|--|--|--|--|--|\n")
    for c in cues:
        w = words(c["caption"]); f.write(f"| {c['id']} | {c['scene']} | {c['start']} | {c['dur']} | {w} | {round(w / c['dur'] * 60)} | {c['caption'][:60]} |\n")
    f.write("\n| scene | seconds | words | wpm incl. gaps |\n|--|--|--|--|\n")
    for s in dict.fromkeys(c["scene"] for c in cues):
        cs = [c for c in cues if c["scene"] == s]; span = cs[-1]["end"] - cs[0]["start"]; w = sum(words(c["caption"]) for c in cs)
        f.write(f"| {s} | {span:.1f} | {w} | {round(w / span * 60)} |\n")
    f.write(f"\nTOTAL {total:.1f} s ({int(total // 60)}:{total % 60:04.1f}), {W} words, tempo {tempo}\n")
shutil.rmtree(T, ignore_errors=True)
base = speak - sum(EXTRA.values())
print(f"{W / base * 60:.0f} wpm while speaking on base gaps; total {total:.2f} s ({int(total // 60)}:{total % 60:05.2f}); {W} words")
