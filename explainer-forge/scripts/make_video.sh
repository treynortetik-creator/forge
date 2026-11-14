#!/usr/bin/env bash
# One command from rendered voice clips to a verified MP4. Run from the project folder.
#
#   PLUGIN=<plugin root> VOICE_PY=voice/.venv/bin/python scripts/make_video.sh
#   SKIP_AUDIO=1 ...      visual-only change: reuse narration, captions and cues
#
# Expects (names are overridable with the env vars in brackets):
#   lines.json [LINES]            the script, one entry per line (templates/lines.example.json)
#   voice/out/<id>.wav [CLIPS]    clips from scripts/voice/render_lines.py (natural pace)
#   captures/clips/*.mp4 [SRC]    app footage, if any
#   build/stage.html [PAGE]       the timeline page (templates/stage.html + timeline.js + your scenes)
# Speed: TARGET_WPM (default 180) or TEMPO (a fixed multiplier, set by ear). Workers: WORKERS (default 8).
set -euo pipefail
PLUGIN="${PLUGIN:-${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}}"; S="$PLUGIN/scripts"
VOICE_PY="${VOICE_PY:-python3}"; LINES="${LINES:-lines.json}"; CLIPS="${CLIPS:-voice/out}"; SRC="${SRC:-captures/clips}"
BUILD="${BUILD:-build}"; PAGE="${PAGE:-$BUILD/stage.html}"; NAME="${NAME:-explainer}"
if [[ -z "${SKIP_AUDIO:-}" ]]; then
  if [[ -n "${TEMPO:-}" ]]; then SPEED=(--tempo "$TEMPO"); else SPEED=(--target-wpm "${TARGET_WPM:-180}"); fi
  EXTRA=(); [[ -f gaps.json ]] && EXTRA=(--extra gaps.json)
  python3 "$S/stitch_narration.py" --lines "$LINES" --clips "$CLIPS" --out "$BUILD" "${SPEED[@]}" ${EXTRA[@]+"${EXTRA[@]}"}
  "$VOICE_PY" "$S/captions.py" --build "$BUILD" --name "$NAME" > /dev/null
fi
if [[ -d "$SRC" ]]; then python3 "$S/prep_media.py" --build "$BUILD" --src "$SRC"; else python3 "$S/prep_media.py" --build "$BUILD"; fi
node "$S/render_frames.mjs" --page "$PAGE" --audio "$BUILD/narration.m4a" --out "$BUILD/$NAME.mp4" --workers "${WORKERS:-8}"
bash "$S/verify_video.sh" "$BUILD/$NAME.mp4" "$BUILD/cues.json" "$BUILD/proof"
