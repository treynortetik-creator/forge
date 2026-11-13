#!/usr/bin/env bash
# Loudness regression gate. Music: integrated -16 +-0.5 LUFS and true peak <= -2 dBTP. Ambience beds: -20 +-1 LUFS.
# Run in the builder's acceptance step (not in vitest). Exit 1 on any miss.
# usage: run from the project root; override dirs with MUSIC_GLOB / AMB_GLOB (defaults below)
MUSIC_GLOB=${MUSIC_GLOB:-public/assets/audio/music/*.ogg}
AMB_GLOB=${AMB_GLOB:-public/assets/audio/sfx/amb_*.ogg}
fail=0
meas() { ffmpeg -hide_banner -nostats -i "$1" -af ebur128=peak=true -f null - 2>&1 | awk '/Summary:/{s=1} s&&/ I:/{i=$2} s&&/Peak:/{p=$2} END{print i, p}'; }
for f in $MUSIC_GLOB; do
  read -r i p <<<"$(meas "$f")"
  ok=$(awk -v i="$i" -v p="$p" 'BEGIN{print (i>=-16.5 && i<=-15.5 && p<=-2.0) ? "ok" : "FAIL"}')
  printf '%-4s %-48s I=%s TP=%s\n' "$ok" "$f" "$i" "$p"; [ "$ok" = ok ] || fail=1
done
for f in $AMB_GLOB; do
  case "$f" in *amb_spot_*) continue;; esac
  read -r i p <<<"$(meas "$f")"
  ok=$(awk -v i="$i" 'BEGIN{print (i>=-21 && i<=-19) ? "ok" : "FAIL"}')
  printf '%-4s %-48s I=%s TP=%s\n' "$ok" "$f" "$i" "$p"; [ "$ok" = ok ] || fail=1
done
exit $fail
