#!/usr/bin/env bash
# Proof pass on a rendered explainer MP4.
#
#   scripts/verify_video.sh <video.mp4> <cues.json> [proof_dir] [line_id ...]
#
# Prints duration and stream info, then writes into proof_dir (default: proof/ beside the video):
#   contact-sheet.png      1 frame every 8 s, 5x5
#   review/sheet-NN.png    1 frame every 2 s, 12 per sheet: LOOK AT EVERY SHEET (stray rings, overlapping
#                          crossfades, text overflow, blank flash frames, captions over callouts)
#   final/sceneN-mid.png   the middle frame of each scene
# and measures A/V sync: for each line id given (default: the first line of the first, middle and last scene), the
# gap between the cue time and the nearest speech onset in the MP4. Keep every gap under about 50 ms.
# Needs ffmpeg/ffprobe on PATH (or $FFMPEG / $FFPROBE) and python3.
set -euo pipefail
if [[ $# -lt 2 || "$1" == "-h" || "$1" == "--help" ]]; then sed -n '2,13p' "$0" | sed 's/^# \{0,1\}//'; exit 0; fi
FF="${FFMPEG:-ffmpeg}"; FP="${FFPROBE:-ffprobe}"
M="$1"; C="$2"; P="${3:-$(dirname "$M")/proof}"; shift 2; if [[ $# -gt 0 ]]; then shift; fi
echo "duration: $("$FP" -v error -show_entries format=duration -of csv=p=0 "$M") s"
"$FP" -v error -show_entries stream=codec_name,width,height,pix_fmt,r_frame_rate -of compact "$M"
mkdir -p "$P"; rm -rf "$P/review" "$P/final"; mkdir -p "$P/review" "$P/final"
"$FF" -loglevel error -y -i "$M" -vf "fps=1/8,scale=480:-1,tile=5x5:padding=6:color=white" -frames:v 1 "$P/contact-sheet.png"
"$FF" -loglevel error -y -i "$M" -vf "fps=1/2,scale=640:-1,tile=3x4:padding=4:color=white" "$P/review/sheet-%02d.png"
FF="$FF" python3 - "$M" "$C" "$P" "$@" <<'EOF'
import json, os, subprocess, sys
M, C, P, ids = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:]
FF = os.environ["FF"]; L = json.load(open(C))["lines"]
sc = {}
for l in L: sc.setdefault(l["scene"], []).append(l)
for s, ls in sc.items():
    mid = (ls[0]["start"] + ls[-1]["end"]) / 2
    subprocess.run([FF, "-loglevel", "error", "-y", "-ss", f"{mid:.3f}", "-i", M, "-frames:v", "1", f"{P}/final/scene{s}-mid.png"], check=True)
if not ids:
    keys = list(sc); ids = [sc[k][0]["id"] for k in (keys[0], keys[len(keys) // 2], keys[-1])]
out = subprocess.run([FF, "-hide_banner", "-i", M, "-map", "0:a", "-af", "silencedetect=n=-40dB:d=0.12", "-f", "null", "-"],
                     capture_output=True, text=True).stderr
ends = [float(x.split("silence_end: ")[1].split()[0]) for x in out.splitlines() if "silence_end" in x]
worst = 0
for i in ids:
    t = next(x for x in L if x["id"] == i)["start"]; on = min(ends, key=lambda e: abs(e - t)) if ends else float("nan")
    d = 1000 * (on - t); worst = max(worst, abs(d))
    print(f"sync {i}: cue {t:.3f}s, speech onset {on:.3f}s, diff {d:+.0f} ms" + ("  <<< OVER 50 ms" if abs(d) > 50 else ""))
sys.exit(1 if worst > 50 else 0)
EOF
ls "$P/review"
