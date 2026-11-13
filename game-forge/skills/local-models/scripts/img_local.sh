#!/usr/bin/env bash
# Free local image generation: Qwen-Image 2.1 (4-bit) + a Lightning 4-step LoRA via mflux.
# Measured on a 32 GB M5: about 38 s per 1024 px image including load, peak 7.2 GB.
# RESEARCH LICENCE (qwen-research, non-commercial): never ship the output in a sold product.
# Use it for concept boards, deck visuals, placeholders, prompts-to-test. See SKILL.md.
#
# Usage: img_local.sh "prompt" out.png [width] [height] [seed]
# Env:   LORA=<path to the 4-step Lightning LoRA .safetensors>  (required; see SKILL.md for the
#        key-rename it needed before mflux would load it)
# Install: uv tool install --force --python 3.13 mflux --with 'pillow<13'
set -euo pipefail
PROMPT="${1:?usage: img_local.sh \"prompt\" out.png [w] [h] [seed]}"; OUT="${2:?out.png}"
W="${3:-1024}"; H="${4:-1024}"; SEED="${5:-$RANDOM}"
LORA="${LORA:?set LORA to the converted lightning-4step.safetensors}"
exec mflux-generate-qwen-2.1 -q 4 --low-ram --width "$W" --height "$H" --seed "$SEED" --steps 4 --guidance 1.0 \
  --lora "$LORA" 1.0 --prompt "$PROMPT" --output "$OUT"
# Slow full-quality alternative (40 steps, about 3.5 min, 7.0 GB):
#   mflux-generate-qwen-2.1 -q 4 --low-ram --width 1024 --height 1024 --seed 7 --prompt "..." --output out.png
