---
name: local-models
description: >
  The free, on-device model menu for game asset work on Apple Silicon (32 GB M5 measured):
  local images (Qwen-Image 2.1, research licence, never in shipped assets), an image judge to
  rank best-of-N, TTS with a cloned voice (Qwen3-TTS) and a Kokoro fallback, music (ACE-Step 1.5,
  MIT), speech-to-text to check voice lines (Parakeet, whisper.cpp), and the video digest tool.
  Each entry has licence, RAM, speed, the traps, and when to pay instead. Use when someone asks
  what can run locally for a game, wants placeholder art, temp voice lines, stingers, a free
  transcript, or asks whether local output can ship. Triggers: "local image generation", "free
  TTS", "voice clone locally", "ACE-Step", "mflux", "Qwen-Image", "transcribe voice lines",
  "can I ship this", "what runs on my Mac".
---

# Local models for game asset work

**The one-line case:** on a 32 GB M5, one box ran image, voice, music, judging and transcription for
$0, and the discipline that made it useful was knowing **which outputs may ship and which may
not**. The licence column decides the job, not the quality.

> House thesis: the model judges taste, the harness measures. Every entry below was timed and
> RAM-metered once; where a number is missing, that means we did not measure it, and it says so.

Siblings: 3D meshes are `game-forge:local-3d-gen`; audio direction and shipped voice work are
`game-forge:game-audio`; deciding what art is good enough is `game-forge:art-waves`.

## The menu (all measured on a MacBook Pro M5, 32 GB, 2026-10-22 and 23 unless noted)

| Need | Tool | Licence | RAM | Speed | Ship it? | Pay instead when |
|---|---|---|---|---|---|---|
| Images | Qwen-Image 2.1, 4-bit, Lightning 4-step LoRA, via mflux | **qwen-research (non-commercial)** | 7.2 GB peak | 38 s per 1024 px (40-step: 3.5 min, 7.0 GB) | **No.** Concept boards, decks, placeholders only | the image goes in a sold product |
| Rank N images | UnifiedReward 2.0 on Qwen3-VL 8B, via mlx-vlm | MIT (HF card, checked 2026-10-22) | 20.7 GB peak (bf16) | about 90 s wall per A/B comparison (both orders + pointwise; one pass 19 to 24 s) | n/a (a grader) | you need a calibrated absolute grade; this only ranks |
| TTS, cloned voice | Qwen3-TTS 1.7B Base 8-bit, via mlx-audio | Apache-2.0 per listings, re-check the card before shipped use | not metered | about 4 s for a 5 s line once cached (measured on the voice-description build) | placeholder lines; see traps | final shipped, directed, acted lines |
| TTS, fallback | Kokoro-82M ONNX | not recorded in our notes: read the model card | not metered | about 750 words in about 4.5 min, no truncation | check card | same as above |
| Music | ACE-Step 1.5 turbo 2B DiT + 0.6B LM | MIT code; weights card says MIT | RSS 15.9 GB, **peak 39 GB** (leans on swap) | 34.8 s to make 30 s, 39 s load | MIT, so yes legally; **never listened to** | you need vocals, a mixed song, or known quality (vocals untried here) |
| STT | Parakeet TDT 0.6B v2 on MLX; whisper.cpp small.en | not recorded in our notes | not metered | not timed; whisper runs in 25 s chunks | n/a | never; free is enough |
| Speaker labels | pyannote community-1 (ungated mirror, CC-BY-4.0) | CC-BY-4.0 | about 1.4 GB | about 0.07x realtime | n/a | n/a |
| Video to text | video digest (Parakeet + Apple Vision OCR + two small vision models) | local | one 2 to 3 GB model at a time | about 3 s per described clip | n/a | n/a |

Not adopted or not tried: a local 26B LLM via Ollama (tested: 32 s to pull actions from a 2,185-word
note; **not adopted**, a cheap hosted model stays the bulk reader), local video generation (LTX-2.3
MLX 4-bit, MiniMax H3: **not tried**, the latter does not fit 32 GB), a full-duplex voice model
(18 preset voices, no cloning, 124 to 149 ms per step vs the 80 ms live needs: **shelved**), an
ACE-Step "XL turbo" (4B DiT, **not tried**, risky at a 39 GB peak). Sound effects: nothing
MLX-native was found; use a paid SFX tool. More detail: `references/menu-detail.md`.

## Workflow

### 1. Check licence first, then pick the tool
1. Will the output ship in a sold game? If yes, only MIT/Apache/CC0-style outputs qualify, and even
   then read the card. **Qwen-Image output never ships.** Cloned-voice output of a person you lack
   rights to never ships.
2. Check free RAM (`memory_pressure`, `df -h /`). Run **one heavy model at a time**. Three loaded at
   once froze the Mac on 2026-11-12.
3. Say in the asset's filename or manifest that it is a placeholder, so it gets replaced.

### 2. Local images (`scripts/img_local.sh`)
```bash
LORA=models/lightning-4step.safetensors bash scripts/img_local.sh "a stone urn, game concept, plain grey background" out.png 1024 1024 7
```
- Install: `uv tool install --force --python 3.13 mflux --with 'pillow<13'`. Weights (33 GB, Qwen/Qwen-Image-2.1) cache in the Hugging Face cache and are quantized to 4-bit at load.
- The Lightning LoRA needed its keys renamed (`lora.down/up` to `lora_A/B`) before mflux would load it. We kept a converted copy; the conversion script was not saved, so expect to redo it.
- Short sign text rendered nearly right on the first try. **Long text does not:** on a text-heavy infographic about 70 percent of lines came out exact and the SAME words failed on every seed ("lookup" became "loop"); 40 steps did not help. Typeset text in HTML/CSS and use the model only for spot illustrations with one shared style prefix.
- Best-of-N: generate 4 to 8 seeds, rank with the judge, then look at the top two yourself.

### 3. Judge images (`scripts/img_judge.sh`)
```bash
JUDGE_VENV=venvs/judge bash scripts/img_judge.sh "the prompt" a.png b.png
```
- Setup: `uv venv --python 3.13 venvs/judge; uv pip install --python venvs/judge/bin/python mlx-vlm 'pillow<13' torch torchvision`. The 8B bf16 weights are 8.6 GB.
- It runs the pair in both orders and averages, because position bias is real (the same winner scored 0.55 listed first and 0.64 listed second). On the one test, a 40-step image beat a 4-step one by 0.60 to 0.40 on alignment, but nobody confirmed that by eye. Use it to shortlist, then decide by looking.

### 4. TTS (`scripts/tts.sh`, `scripts/tts_doc.sh`, `scripts/kokoro_tts.py`)
```bash
TTS_REF_DIR=voices/narrator bash scripts/tts.sh file line-001.mp3 "Hold the door."
bash scripts/tts_doc.sh narration.txt out.mp3      # long form, +2 s tail pad
```
- Install: `uv tool install --force --python 3.13 mlx-audio --with 'pillow<13'` (provides `mlx_audio.tts.generate`). Model `mlx-community/Qwen3-TTS-12Hz-1.7B-Base-8bit`.
- The voice is cloned from ONE reference clip (`ref.wav` plus `ref.txt` holding its exact words), so it does not drift between lines. Keep one approved clip per character and never swap it mid-project.
- A voice-description build of the same model (6-bit) was also tested: a voice described in words, a 5 s clip in 3.9 s once cached, transcribed back word-perfect.
- Chain: Qwen3 clone, then Kokoro, then macOS `say`; the script falls through silently, so check which engine actually ran.
- Write narration for the ear: no markdown, tables, URLs or em-dashes.
- Checking a line: run `scripts/stt.sh line-001.mp3` and diff against the script text (this check is our usual practice; the diff script is not included).
- Shipped voices: use a paid tool with directed, acted delivery and a licence that covers your use. We flagged that a pay-as-you-go ElevenLabs plan did not cover commercial use at the time; verify current terms before shipping.

### 5. Music (`scripts/ace_music.py`)
```bash
ACE_REPO=vendor/ACE-Step-1.5 venvs/acestep/bin/python -I scripts/ace_music.py "dark waltz, solo piano and cello" --out music --seconds 30 --bpm 110 --timesig 3
```
- Setup: clone `github.com/ACE-Step/ACE-Step-1.5`; `uv venv --python 3.12` (the repo needs Python below 3.13); `uv pip install -e . 'pillow<13'`. About 11 GB of checkpoints download on first run.
- Tested run: turbo 2B DiT, 0.6B LM on the MLX backend, 8 steps, 30 s instrumental, seed 7. Output checked by file only: 30.0 s, 48 kHz stereo, mean -19.7 dB, peak -1.0 dB, not silent. **Nobody listened.**
- Peak footprint 39 GB exceeds the 32 GB of RAM: close everything else.
- **With "thinking" on, the built-in LM rewrote the caption and picked a tempo** (a waltz brief became "somber cinematic" at 30 bpm in G minor). A waltz is 3/4, about 90 to 130 bpm. Pin tempo, time signature and key, and turn thinking off. The pinned path in `ace_music.py` is untested.
- A faster community "mlx-serve" build was skipped on purpose: its Homebrew tap was untrusted and brew refused it. Do not override that.

### 6. Speech to text (`scripts/stt.sh`, `scripts/parakeet_stt.py`)
- whisper.cpp (`brew install whisper-cpp`, model `ggml-small.en.bin`): **a single pass on a 159 s clip silently dropped 60 percent of the words**, so the script cuts into 25 s pieces above 30 s. Count words in versus out on any long file.
- Parakeet TDT 0.6B v2 (`parakeet-mlx`) gives word timestamps; 120 s chunks with 15 s overlap.
- Speaker labels: pyannote community-1 from the ungated mirror `pyannote-community/speaker-diarization-community-1` (no token needed). The original repo is gated (401). A threshold-based fallback over-split badly (14 to 60 "speakers") when given no speaker count.

### 7. Video digest (read a video without watching it)
The tool turns a video into a text digest at roughly half the tokens of sending frames. Shape: speech
(the video's own captions if present, else Parakeet), Apple Vision OCR on every frame at 1 frame per
second, a pixel-change bar with a floor of one frame per 30 s, a small vision model (about 2 GB) that
labels each candidate head / slide / demo / title, slides re-read by OCR at full resolution, and a
second small model (about 3 GB) describing the 6 s around a hands-on frame (about 3 s per clip).
- Score on one coffee tutorial, 12 visual questions answered by a small hosted model: transcript only 0.5 of 12; transcript plus 36 evenly spaced frames 8 of 12; the digest text only 10 of 12. **One video, one grader: weak evidence.**
- Trust levels: speech and OCR text are reliable ("1G" read as "16" once); the `shows:` sentence is a small model's guess and **invented scale readings**. Never quote a number from it.
- The script itself is not shipped here (it depends on locally installed models and helper scripts).

## Traps
- **"Free" is not "shippable".** The most capable local image model is research-licence. We accepted
  it for decks and placeholders only. Write the licence class into the asset record on day one.
- **Pillow 13 breaks Python 3.12 to 3.14 here** (`_IntegralLike` import error). Install uv tools
  with `--python 3.13 --with 'pillow<13'`.
- **Peak RAM beats average RAM.** ACE-Step's RSS was 15.9 GB but its peak 39 GB. Read the peak.
- **Do not trust a judge's small deltas.** 0.55 vs 0.49 is position bias plus noise.
- **Image models and text:** same words fail on every seed; do not re-roll, typeset instead.
- **Auto-fallthrough hides failures.** `tts.sh` falls through to a worse voice without a message.
- **Re-check licences before shipped use.** Several rows above carry "per listings" or "not
  recorded": we did not read those cards.
