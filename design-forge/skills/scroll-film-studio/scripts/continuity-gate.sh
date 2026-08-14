#!/bin/zsh
# continuity-gate.sh <frames-dir> [step]
#
# Proves the film is ONE CONTINUOUS CAMERA MOVE — not a sequence of shots.
#
# WHY A SEAM GATE IS NOT ENOUGH. Chaining sets each clip's start image to the
# previous clip's last frame, so the seams match BY CONSTRUCTION and cannot fail.
# What escapes is the middle of each clip, where a generated shot can jump-cut
# or freeze despite perfect junction scores.
#
# WHY ABSOLUTE SSIM IS ALSO NOT ENOUGH — the mistake this script made first.
# SSIM measures pixel similarity, not continuity. A fast but perfectly smooth
# dolly changes most of the frame and scores ~0.49; a hard cut between two
# visually similar frames scores high. A fixed threshold therefore REJECTS good
# fast camera work and can WAVE THROUGH cuts. The first version of this gate
# failed a flawless Veo 3.1 shot at median 0.49 — a single unbroken push from a
# meadow into a hive interior — and would have thrown the best footage away.
#
# WHAT ACTUALLY SEPARATES A CUT FROM MOTION is the LOCAL SHAPE of the curve:
#   • smooth motion  → values consistent with their neighbours, however low
#   • a hard cut     → a sudden collapse far below the LOCAL median
#   • a freeze       → ~1.0, the camera stopped: a dead scroll zone
# So every pair is judged against its own local baseline, never a global constant.
#
#   PASS  no pair below 45% of its local median, and at most 2 frozen pairs
#   FAIL  otherwise — regenerate; do NOT build on it
#
set -u
DIR=${1:?usage: continuity-gate.sh <frames-dir> [step]}
STEP=${2:-4}
[[ "$STEP" == <-> && "$STEP" -gt 0 ]] || {
  echo "step must be a positive integer"; exit 1
}
command -v ffmpeg >/dev/null || { echo "missing dependency: ffmpeg"; exit 1; }

FRAMES=("$DIR"/f_*.jpg(N.on))
(( ${#FRAMES} < 4 )) && { echo "no frames in $DIR"; exit 1 }
echo "continuity gate — $DIR  (${#FRAMES} frames, every $STEP)"

SCORES=(); NAMES=(); prev=""
for ((i=1; i<=${#FRAMES}; i+=STEP)); do
  f=${FRAMES[$i]}
  if [[ -n "$prev" ]]; then
    s=$(ffmpeg -i "$prev" -i "$f" -lavfi ssim -f null - 2>&1 | grep -o 'All:[0-9.]*' | cut -d: -f2)
    [[ -n "$s" ]] && { SCORES+=($s); NAMES+=("$(basename $prev)->$(basename $f)") }
  fi
  prev=$f
done

(( ${#SCORES} < 3 )) && {
  echo "  FAIL measured ${#SCORES} pairs — too few to judge."
  echo "  A gate that passes without measuring anything is worse than no gate."
  exit 1
}

med(){ printf '%s\n' "$@" | sort -n | awk '{a[NR]=$1} END{print (NR%2)?a[(NR+1)/2]:(a[NR/2]+a[NR/2+1])/2}' }
MEDIAN=$(med $SCORES)

CUTS=(); FROZEN=()
for ((i=1; i<=${#SCORES}; i++)); do
  lo=$(( i-3 < 1 ? 1 : i-3 )); hi=$(( i+3 > ${#SCORES} ? ${#SCORES} : i+3 ))
  LM=$(med ${SCORES[$lo,$hi]})
  s=${SCORES[$i]}
  awk "BEGIN{exit !($s < 0.45*$LM)}" && CUTS+=("${NAMES[$i]}  $s vs local $LM")
  awk "BEGIN{exit !($s > 0.995)}"    && FROZEN+=("${NAMES[$i]}  $s")
done

echo "  median $MEDIAN over ${#SCORES} pairs — absolute value is NOT the test; local shape is"
(( ${#CUTS} ))   && { echo "  ${#CUTS} hard cuts (collapse vs local baseline):"; printf '    %s\n' ${CUTS[1,6]} }
(( ${#FROZEN} )) && { echo "  ${#FROZEN} frozen pairs (camera stopped — dead scroll zone):"; printf '    %s\n' ${FROZEN[1,6]} }

FAIL=0
(( ${#CUTS} ))       && { echo "  FAIL ${#CUTS} cuts — a sequence of shots, not one move"; FAIL=1 }
(( ${#FROZEN} > 2 )) && { echo "  FAIL ${#FROZEN} frozen pairs — the scroll will stall here"; FAIL=1 }

if (( FAIL )); then
  echo
  echo "REJECTED. Do not build on this footage — regenerate it."
  echo "The cause is almost always storyboard distance: a clip asked to change"
  echo "location, scale and lighting at once will teleport. Shorten the move, add"
  echo "an intermediate keyframe, and pin BOTH ends (Veo 3.1"
  echo "FIRST_AND_LAST_FRAMES_2_VIDEO) so the clip is forced to land."
  exit 1
fi
echo "  PASS — one continuous move"
