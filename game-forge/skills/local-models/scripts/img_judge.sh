#!/bin/bash
# img_judge.sh "prompt" a.png b.png : local image judge (UnifiedReward 2.0 on Qwen3-VL 8B, MIT) via mlx-vlm.
# Pairwise in both orders (position bias averaged) + pointwise 1-5. About 90 s wall and 20.7 GB peak on bf16: do
# not run beside an image generation or a local LLM on 32 GB. Free.
# Setup: uv venv --python 3.13 "$JUDGE_VENV"; uv pip install --python "$JUDGE_VENV/bin/python" mlx-vlm 'pillow<13' torch torchvision
# Env:   JUDGE_VENV=<venv dir> (required)
[ $# -eq 3 ] || { echo 'usage: img_judge.sh "prompt" a.png b.png'; exit 1; }
: "${JUDGE_VENV:?set JUDGE_VENV to the venv holding mlx-vlm}"
"$JUDGE_VENV/bin/python" "$(dirname "$0")/judge.py" "$1" "$2" "$3" 2>/dev/null | grep -v '^$'
