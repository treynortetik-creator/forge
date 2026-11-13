#!/usr/bin/env bash
# cut-reel.sh: trim + concat recorded segments into one small mp4 (720p x264), optional music, size check.
#
# Usage:
#   cut-reel.sh -o reel.mp4 [-m music.mp3] [-w 1280] [-c 22] [-r 3200k] [-l 35] seg1.webm[,START,DUR] seg2.webm ...
#     START/DUR (seconds) trim a segment:  c-run.webm,4,10  = 10 s starting 4 s in. No trim = whole file.
#     -w  output width (default 1280, height follows, even)      -c  x264 CRF (default 22)
#     -r  x264 maxrate (default 3200k; bufsize = 2x)             -l  size limit in MB (10^6 bytes), exit 1 over it (default 35)
#     -m  music file, faded out over the last 2 s; omit for a silent reel
# Receipt: 1920x1080 / 30 fps webm segments, -w 1280 -c 22 -r 3200k gave 78 s in 24.9 MB.
# Demo rules (SKILL.md): a "demo" is the raw uncut take, no cards; use this script for highlight reels the owner asked for.
set -euo pipefail
OUT=""; MUSIC=""; W=1280; CRF=22; MAXRATE=3200k; LIMIT=35
while getopts "o:m:w:c:r:l:" o; do
  case $o in o) OUT=$OPTARG;; m) MUSIC=$OPTARG;; w) W=$OPTARG;; c) CRF=$OPTARG;; r) MAXRATE=$OPTARG;; l) LIMIT=$OPTARG;; *) exit 2;; esac
done
shift $((OPTIND-1))
[ -n "$OUT" ] && [ $# -ge 1 ] || { sed -n '2,12p' "$0"; exit 2; }
command -v ffmpeg >/dev/null || { echo "ffmpeg not found" >&2; exit 1; }
BUF=$(( ${MAXRATE%k} * 2 ))k
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
LIST="$TMP/list.txt"; : > "$LIST"
i=0
for spec in "$@"; do
  IFS=, read -r f ss dur <<<"$spec"
  i=$((i+1)); part=$(printf '%s/%02d.mp4' "$TMP" "$i")
  trim=(); [ -n "${ss:-}" ] && trim+=(-ss "$ss"); [ -n "${dur:-}" ] && trim+=(-t "$dur")
  ffmpeg -v error -y ${trim[@]+"${trim[@]}"} -i "$f" -an -vf "scale=$W:-2,fps=30,format=yuv420p" \
    -c:v libx264 -preset medium -crf "$CRF" -maxrate "$MAXRATE" -bufsize "$BUF" "$part"
  echo "file '$part'" >> "$LIST"
done
# every part has identical encode settings, so the concat demuxer can copy
if [ -n "$MUSIC" ]; then
  ffmpeg -v error -y -f concat -safe 0 -i "$LIST" -c copy "$TMP/silent.mp4"
  D=$(ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$TMP/silent.mp4")
  FADE=$(awk -v d="$D" 'BEGIN{printf "%.2f", (d>2? d-2 : 0)}')
  ffmpeg -v error -y -i "$TMP/silent.mp4" -i "$MUSIC" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 96k \
    -af "afade=t=out:st=$FADE:d=2" -shortest -movflags +faststart "$OUT"
else
  ffmpeg -v error -y -f concat -safe 0 -i "$LIST" -c copy -movflags +faststart "$OUT"
fi
BYTES=$(stat -f%z "$OUT" 2>/dev/null || stat -c%s "$OUT")
DUR=$(ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$OUT")
MB=$(awk -v b="$BYTES" 'BEGIN{printf "%.1f", b/1000000}')
echo "$OUT: ${DUR}s, ${MB} MB"
awk -v m="$MB" -v l="$LIMIT" 'BEGIN{ if (m+0 > l+0) { print "WARNING: over the " l " MB limit: raise -c (CRF) or lower -r / -w" > "/dev/stderr"; exit 1 } }'
