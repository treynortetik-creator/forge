#!/bin/bash
# rigone.sh <name> <in.glb>
# Auto-rig one mesh with SkinTokens (VAST-AI, MIT) and clean the skin weights.
# Set before running:
#   SKINTOKENS=<path to the SkinTokens clone, with its .venv>
#   CLEAN_WEIGHTS=<path to a clean_skin_weights.py>   (optional; AssetFurnace ships one in scripts/)
#   OUT=<output dir>                                   (default ./rig)
# Output: $OUT/<name>-rig.glb, <name>.log, <name>.time. ~50-75 s and 5-7 GB on the bake-off's
# 947k-tri Pixal3D meshes (see references/bakeoff-report.md).
set -u
: "${SKINTOKENS:?set SKINTOKENS to the SkinTokens clone}"
OUT=${OUT:-$PWD/rig}; mkdir -p "$OUT"
n=$1; in=$(realpath "$2")
cd "$SKINTOKENS" || exit 1
HF_HUB_OFFLINE=1 /usr/bin/time -l -o "$OUT/$n.time" ./.venv/bin/python demo.py \
  --input "$in" --output "$OUT/$n-rig.glb" --use_transfer > "$OUT/$n.log" 2>&1
echo "exit=$?" >> "$OUT/$n.time"
if [ -n "${CLEAN_WEIGHTS:-}" ]; then
  ./.venv/bin/python "$CLEAN_WEIGHTS" --in "$OUT/$n-rig.glb" --out "$OUT/$n-rig.glb" >> "$OUT/$n.log" 2>&1
fi
