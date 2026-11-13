#!/usr/bin/env bash
# Local TTS with fallbacks. Default: Qwen3-TTS 1.7B (mlx-audio) cloned from ONE reference clip, so the
# voice never drifts between lines. Fallbacks: Kokoro-82M, then macOS `say`.
# Usage:
#   bash tts.sh play  "text"             speak through the speakers (afplay)
#   bash tts.sh file  <out.mp3> "text"   render to an audio file
# Env:
#   TTS_ENGINE=qwen3|kokoro|say     (default qwen3)
#   TTS_REF_DIR=<dir holding ref.wav + ref.txt>   ref.txt = the exact words spoken in ref.wav
#                                                  (a clean 5 to 10 s clip of a voice you have the rights to)
#   KOKORO_PY=<python of the kokoro venv>  KOKORO_SCRIPT=<path to kokoro_tts.py>  KOKORO_VOICE=am_michael
#   SAY_VOICE=Daniel
# Install: uv tool install --force --python 3.13 mlx-audio --with 'pillow<13'   (gives mlx_audio.tts.generate)
set -euo pipefail
ENGINE="${TTS_ENGINE:-qwen3}"
QBIN="${QBIN:-$(command -v mlx_audio.tts.generate || echo "$HOME/.local/bin/mlx_audio.tts.generate")}"
QMODEL="mlx-community/Qwen3-TTS-12Hz-1.7B-Base-8bit"
REFDIR="${TTS_REF_DIR:-$HOME/voices/active}"
KPY="${KOKORO_PY:-$HOME/venvs/kokoro/bin/python}"
KSCRIPT="${KOKORO_SCRIPT:-$(cd "$(dirname "$0")" && pwd)/kokoro_tts.py}"
KVOICE="${KOKORO_VOICE:-am_michael}"
SAYVOICE="${SAY_VOICE:-Daniel}"

MODE="${1:?usage: tts.sh play|file ...}"; shift
if [[ "$MODE" == "file" ]]; then OUT="${1:?usage: tts.sh file <out> \"text\"}"; shift; fi
TEXT="$*"
[[ -n "$TEXT" ]] || { echo "ERROR: no text" >&2; exit 1; }

TMP="$(mktemp -t tts)"; WAV="$TMP.wav"; AIFF="$TMP.aiff"
trap 'rm -f "$TMP" "$WAV" "$AIFF"' EXIT

SRC=""
if [[ "$ENGINE" == "qwen3" && -x "$QBIN" && -f "$REFDIR/ref.wav" && -f "$REFDIR/ref.txt" ]]; then
  QDIR="$(mktemp -d -t qtts)"
  if "$QBIN" --model "$QMODEL" --text "$TEXT" --ref_audio "$REFDIR/ref.wav" --ref_text "$(cat "$REFDIR/ref.txt")" \
       --lang_code en --output_path "$QDIR" --file_prefix out --audio_format wav --join_audio >/dev/null 2>&1 \
       && [[ -s "$QDIR/out.wav" ]]; then
    mv "$QDIR/out.wav" "$WAV"; SRC="$WAV"
  fi
  rm -rf "$QDIR"
fi
if [[ -z "$SRC" && "$ENGINE" != "say" && -x "$KPY" && -f "$KSCRIPT" ]]; then
  if "$KPY" "$KSCRIPT" "$WAV" "$TEXT" "$KVOICE" >/dev/null 2>&1; then SRC="$WAV"; fi
fi
if [[ -z "$SRC" ]]; then
  say -v "$SAYVOICE" -o "$AIFF" "$TEXT" 2>/dev/null || say -o "$AIFF" "$TEXT"
  SRC="$AIFF"
fi
case "$MODE" in
  play) afplay "$SRC" ;;
  file) ffmpeg -nostdin -loglevel error -y -i "$SRC" "$OUT"; echo "$OUT" ;;
  *) echo "usage: tts.sh play|file ..." >&2; exit 1 ;;
esac
