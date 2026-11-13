#!/usr/bin/env bash
# tts_doc.sh <narration.txt> <out.mp3> : render a spoken narration to mp3 through tts.sh, plus 2 s of
# trailing silence so players and encoders do not clip the last word.
# The input must be written FOR THE EAR (conversational, no markdown, tables, URLs or em-dashes). A raw
# markdown read is unlistenable.
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
NARR="${1:?usage: tts_doc.sh <narration.txt> <out.mp3>}"; OUT="${2:?out.mp3}"
[[ -f "$NARR" ]] || { echo "ERROR: narration not found: $NARR" >&2; exit 1; }
RAW="${OUT%.mp3}.raw.mp3"
bash "$DIR/tts.sh" file "$RAW" "$(cat "$NARR")" >/dev/null
ffmpeg -nostdin -v error -y -i "$RAW" -af "apad=pad_dur=2" -c:a libmp3lame -q:a 4 "$OUT" && rm -f "$RAW" || mv -f "$RAW" "$OUT"
DUR="$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$OUT" 2>/dev/null | cut -d. -f1)"
echo "rendered: $OUT (${DUR}s, +2s tail pad)"
