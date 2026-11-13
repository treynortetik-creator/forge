#!/usr/bin/env python3
"""Local STT with Parakeet TDT 0.6B v2 on MLX (word timestamps). Usage: python parakeet_stt.py <audio> <out.json>
Setup: pip/uv install parakeet-mlx. Output: {"text", "sentences":[{"start","end","text","tokens":[...]}]}.
Chunks of 120 s with 15 s overlap so long files do not run out of memory."""
import json, sys
from parakeet_mlx import from_pretrained
m = from_pretrained("mlx-community/parakeet-tdt-0.6b-v2")
r = m.transcribe(sys.argv[1], chunk_duration=120, overlap_duration=15)
out = {"text": r.text, "sentences": [{"start": s.start, "end": s.end, "text": s.text,
       "tokens": [{"t": t.text, "start": t.start, "end": t.end} for t in s.tokens]} for s in r.sentences]}
json.dump(out, open(sys.argv[2], "w"))
print(len(r.sentences), "sentences")
