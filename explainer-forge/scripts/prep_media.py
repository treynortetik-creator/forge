#!/usr/bin/env python3
"""Prepare footage for frame-exact seeking and write the timeline's data file.

  python3 prep_media.py --build build [--src captures/clips] [--media media]

1. Re-encodes every <src>/*.mp4 into <build>/<media>/ with a 6-frame GOP and no B-frames, so a seek lands on the exact
   frame (skips clips already up to date). Audio is dropped; narration is the only soundtrack.
2. Writes <build>/data.js with window.CUES (cues.json), CAPS (captions.json), WORDS (per-line word times from
   whisper/), TRACKS (track/*.json from track_patch.py) and BANDS (track/bands.json from detect_band.py, if present).
Needs ffmpeg on PATH (or $FFMPEG).
"""
import argparse, glob, json, os, subprocess

FF = os.environ.get("FFMPEG", "ffmpeg")
ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--build", required=True); ap.add_argument("--src"); ap.add_argument("--media", default="media")
a = ap.parse_args()
B = a.build
if a.src:
    M = os.path.join(B, a.media); os.makedirs(M, exist_ok=True)
    for src in sorted(glob.glob(os.path.join(a.src, "*.mp4"))):
        dst = os.path.join(M, os.path.basename(src))
        if os.path.exists(dst) and os.path.getmtime(dst) > os.path.getmtime(src):
            continue
        subprocess.run([FF, "-nostdin", "-loglevel", "error", "-y", "-i", src, "-an", "-c:v", "libx264", "-preset", "fast",
                        "-crf", "14", "-g", "6", "-bf", "0", "-pix_fmt", "yuv420p", "-movflags", "+faststart", dst], check=True)
        print("clip", os.path.basename(src))

load = lambda p, d: json.load(open(p)) if os.path.exists(p) else d
cues = json.load(open(os.path.join(B, "cues.json")))
caps = load(os.path.join(B, "captions.json"), [])
words = {}
for l in cues["lines"]:
    w = load(os.path.join(B, "whisper", l["id"] + ".json"), [])
    words[l["id"]] = [[x["w"], round(l["start"] + x["s"], 3)] for x in w]
tracks = {os.path.basename(f)[:-5]: json.load(open(f)) for f in glob.glob(os.path.join(B, "track", "*.json"))
          if os.path.basename(f) != "bands.json"}
bands = load(os.path.join(B, "track", "bands.json"), {})
with open(os.path.join(B, "data.js"), "w") as f:
    for k, v in (("CUES", cues), ("CAPS", caps), ("WORDS", words), ("TRACKS", tracks), ("BANDS", bands)):
        f.write(f"window.{k}={json.dumps(v)};\n")
print("data.js; total", cues["total"], "s;", len(caps), "caption chunks;", len(tracks), "tracks")
