#!/bin/bash
# queue.sh <pixal3d_generate.py> <input-dir> <out-dir> [name ...]
# Serial generation queue: ONE local 3D job at a time (RAM is the binding constraint on a 32 GB
# Mac; two jobs, or a job plus a Blender bake, make both slow and can freeze the machine).
# Skips any name whose output .glb already exists, so it is safe to re-run after a crash.
# Inputs are <input-dir>/<name>.png (RGBA, already cut out; see cut_grey_bg.py).
# Optional lock so other heavy jobs wait their turn: HEAVY_LOCK=/tmp/heavy.lock
gen=$1; in=$2; out=$3; shift 3
here=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$out"
for n in "$@"; do
  [ -f "$out/$n.glb" ] && continue
  if [ -n "${HEAVY_LOCK:-}" ]; then until mkdir "$HEAVY_LOCK" 2>/dev/null; do sleep 10; done; fi
  "$here/runone.sh" "px-$n" python3 "$gen" "$in/$n.png" "$out/$n.glb" --res 1024 --seed "${SEED:-1}"
  [ -n "${HEAVY_LOCK:-}" ] && rmdir "$HEAVY_LOCK"
done
