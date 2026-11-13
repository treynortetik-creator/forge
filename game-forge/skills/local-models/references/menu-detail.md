# Local model notes (2026-10-22 and 23, MacBook Pro M5 32 GB)

## Local LLM (tested, not adopted)
Gemma 4 26B (MoE) via Ollama, 16 GB: pulled actions and owners from a 2,185-word meeting note in
32 s (reads 353 tok/s, writes 36 tok/s); spot-checked names were real. Decision: a cheap hosted
model stays the bulk reader; local LLMs only for projects that need them. Unload after use
(`ollama stop <model>`). Do not run beside an image generation or the judge on 32 GB.

## Video generation (not tried)
- LTX-2.3 MLX 4-bit: 29.9 GB peak on a 128 GB machine for 5 s at 576x1024. Tight on 32 GB; expect compact mode only.
- MiniMax H3 (code Apache-2.0; weights under a community licence, read before shipped use): fits a 128 GB machine (4-bit DiT 11.5 GB, text encoder about 50 GB, VAEs about 11 GB), not 32 GB. The repo's numbers on a different chip: a 5 s 1344x768 clip is about 9 min per step, 8 steps about 1.2 h. An overnight batch tool, not iterative.

## Full-duplex voice (shelved)
PersonaPlex-7B on Mac: 124 to 149 ms per step under load (live needs 80 or less), real-time factor 1.56 to 2.0, peak 25.6 to 26 GB, 18 preset voices and no cloning, persona weak. Offline only; deleted. A later web-only recheck found third-party claims of 48 to 68 ms per step on larger chips, unverified on a 32 GB base chip.

## Image judge: test result
Prompt from the generation metadata; A = 40-step image, B = 4-step Lightning image.
| Mode | A / B |
|---|---|
| Pairwise A,B order (align/coherence/style) | A 0.55 / 0.49 / 0.55 |
| Pairwise B,A order | A (listed second) 0.64 / 0.60 / 0.64 |
| Pairwise averaged | align 0.60 vs 0.40, coherence 0.55 vs 0.45, style 0.60 vs 0.40, winner A |
| Pointwise 1-5 | A 3.35 / 3.50 / 3.28; B 3.14 / 3.40 / 3.06 |
Time: load about 4 s cached, pair 19 to 24 s, point 13 to 14 s each, about 90 s wall. Memory: RSS 10 to 11 GB, peak footprint 20.7 GB. Not tried: the 27B variants, a 4-bit quant of the 8B. Whether the float scores are calibrated like the reference's logprob scores is unverified.

## Embedding and reranker A/B (context for "should I switch models")
Qwen3-Embedding-0.6B vs bge-base on 105 retrieval questions: weighted MRR 0.449 vs 0.444, a wash, at 4x slower indexing; **do not switch**. A reranker hurt easy lookups (MRR 0.735 to 0.624) and helped hard vague questions a lot (0.310 to 0.420), so keep it opt-in. Lesson: one query proved nothing; run a benchmark.

## Install quirks
- Pillow 13 fails to import on Python 3.12 to 3.14 (`_IntegralLike`): `--python 3.13 --with 'pillow<13'`.
- ACE-Step needs Python below 3.13.
- Test outputs were kept outside the repos; none of these models belong in a game repo.
