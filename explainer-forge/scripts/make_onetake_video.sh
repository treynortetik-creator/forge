#!/usr/bin/env bash
# The one-take pipeline, step by step, from a script to a verified MP4. Run from the PROJECT folder (the one that holds
# script.md, saymap.json and project.json). Every step is a script you can run alone; this only chains them.
#
#   PY=.venv/bin/python scripts/make_onetake_video.sh [steps]      steps: narration take check audio sync sprites build proof hero render verify all
#
# Env (all optional):  PLUGIN  plugin root (default: this script's parent)     PY  python with mlx-audio, mlx-whisper,
#   soundfile, numpy, Pillow (default python3)     WPM  target speaking pace (default 200, set by ear)   SYNC_LIMIT_MS  verify limit (default 150)
#   GAP_BEFORE  e.g. 6=0.35,13=0.4      SEED  voice seed (default 42)      REF_WAV / REF_TEXT_FILE  reference clip
#   (default: the bundled narrator)     GSAP_JS, PLAYWRIGHT_PATH, CHROME_PATH  see build_explainer.py / pw_common.mjs
#   WORKERS render workers (default 6)  NAME output name (default explainer)
# Folders it makes: audio/ (take, final audio, cues), img/ (sprites), build/ (page), proof/ (stills), out/ (mp4, srt).
set -euo pipefail
PLUGIN="${PLUGIN:-${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}}"; S="$PLUGIN/scripts"
PY="${PY:-python3}"; NAME="${NAME:-explainer}"; WPM="${WPM:-200}"
if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then sed -n '2,15p' "$0" | sed 's/^# \{0,1\}//'; exit 0; fi
STEPS=("$@"); [[ ${#STEPS[@]} -eq 0 || "${STEPS[0]}" == "all" ]] && STEPS=(narration take check audio sync sprites build proof hero render verify)
mkdir -p audio img build proof out
for step in "${STEPS[@]}"; do
  echo "== $step"
  case "$step" in
    narration) SAY=(); [[ -f saymap.json ]] && SAY=(--say-map saymap.json)
      python3 "$S/make_narration.py" script.md --out narration.json ${SAY[@]+"${SAY[@]}"} ;;
    take) rm -f audio/take-raw.stt.json     # a new take must never reuse the old take's transcript
      REF=(); [[ -n "${REF_WAV:-}" ]] && REF=(--ref-wav "$REF_WAV"); [[ -n "${REF_TEXT_FILE:-}" ]] && REF+=(--ref-text-file "$REF_TEXT_FILE")
      "$PY" "$S/voice/one_take.py" --narration narration.json --out audio/take-raw.wav --seed "${SEED:-42}" ${REF[@]+"${REF[@]}"} ;;
    check) "$PY" "$S/take_check.py" --take audio/take-raw.wav --narration narration.json ;;
    audio) GB=(); [[ -n "${GAP_BEFORE:-}" ]] && GB=(--gap-before "$GAP_BEFORE")
      WJ=(); [[ -f audio/take-raw.stt.json ]] && WJ=(--words-json audio/take-raw.stt.json)
      "$PY" "$S/audio_build.py" --take audio/take-raw.wav --narration narration.json --out audio --wpm "$WPM" ${GB[@]+"${GB[@]}"} ${WJ[@]+"${WJ[@]}"} ;;
    sync) "$PY" "$S/sync_check.py" --audio audio/narration.m4a --cues audio/cues.json --narration narration.json ;;
    sprites) [[ -d raw ]] && "$PY" "$S/prep_sprites.py" --src raw --out img --heights sprites.json ;;
    build) "$PY" "$S/build_explainer.py" project.json --out "build/$NAME.html" ;;
    proof) node "$S/proof.mjs" --page "build/$NAME.html" --out proof --cues audio/cues.json --audio audio/narration.m4a ;;
    hero) node "$S/hero.mjs" --page "build/$NAME.html" --out "out/$NAME-hero.png" ;;
    render) node "$S/render_frames.mjs" --page "build/$NAME.html" --audio audio/narration.m4a --out "out/$NAME.mp4" --workers "${WORKERS:-6}"
      cp audio/captions.srt "out/$NAME.srt" ;;
    verify) SYNC_LIMIT_MS="${SYNC_LIMIT_MS:-150}" bash "$S/verify_video.sh" "out/$NAME.mp4" audio/cues.json proof ;;
    *) echo "unknown step: $step" >&2; exit 2 ;;
  esac
done
