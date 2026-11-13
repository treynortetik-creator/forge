#!/usr/bin/env bash
# Local STT via whisper.cpp: transcribe any audio file, e.g. to check that a generated voice line says
# the words it was given. Usage: bash stt.sh <audio-file> [model-name]   (default small.en)
# Env: WHISPER_MODEL_DIR=<dir holding ggml-<model>.bin> (default ~/models/whisper); install: brew install whisper-cpp
# Long files go in 25 s pieces: one pass on a 159 s clip silently dropped 60% of the words.
set -euo pipefail
AUDIO="${1:?usage: stt.sh <audio-file> [model-name]}"
MODEL_NAME="${2:-small.en}"
MODEL="${WHISPER_MODEL_DIR:-$HOME/models/whisper}/ggml-${MODEL_NAME}.bin"
WHISPER="$(command -v whisper-cli || command -v whisper-cpp || true)"
[[ -n "$WHISPER" ]] || { echo "ERROR: whisper-cli not found (brew install whisper-cpp)" >&2; exit 1; }
[[ -f "$MODEL" ]]   || { echo "ERROR: model missing: $MODEL" >&2; exit 1; }
[[ -f "$AUDIO" ]]   || { echo "ERROR: audio not found: $AUDIO" >&2; exit 1; }
TMPWAV="$(mktemp -t stt).wav"
trap 'rm -f "$TMPWAV"' EXIT
ffmpeg -nostdin -loglevel error -y -i "$AUDIO" -ar 16000 -ac 1 -c:a pcm_s16le "$TMPWAV"   # whisper.cpp wants 16 kHz mono PCM
DUR="$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$TMPWAV" | cut -d. -f1)"
if [[ "${DUR:-0}" -le 30 ]]; then
  "$WHISPER" -m "$MODEL" -f "$TMPWAV" -nt -np -l en 2>/dev/null | sed 's/^[[:space:]]*//'
else
  SEGDIR="$(mktemp -d -t stt-seg)"; trap 'rm -f "$TMPWAV"; rm -rf "$SEGDIR"' EXIT
  ffmpeg -nostdin -loglevel error -i "$TMPWAV" -f segment -segment_time 25 -c copy "$SEGDIR/s%03d.wav"
  for SEG in "$SEGDIR"/s*.wav; do "$WHISPER" -m "$MODEL" -f "$SEG" -nt -np -l en 2>/dev/null | sed 's/^[[:space:]]*//'; done
fi
