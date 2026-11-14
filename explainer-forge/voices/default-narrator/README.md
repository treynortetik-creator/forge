# Default narrator

A designed, fully synthetic narrator voice: a mid-range, mellow General American alto, calm and conversational.
It was made from a written description by a text-to-voice model. No real person's voice was recorded or cloned.

| File | What it is |
|---|---|
| `reference.wav` | 33 s, mono 24 kHz 16-bit: the narrator reading a neutral settings-walkthrough passage |
| `reference.txt` | the exact transcript of `reference.wav` (the clone model needs it) |
| `sample.m4a` | 29 s sample of the voice at the approved pace, about 180 words per minute |

## Model and licence

Clones are rendered with `mlx-community/Qwen3-TTS-12Hz-1.7B-Base-bf16` (upstream `Qwen/Qwen3-TTS-12Hz-1.7B-Base`),
licence Apache-2.0 as stated on the model card. Apache-2.0 covers the model weights and code and puts no restriction
on the audio they generate; check the card again before you rely on it. Settings: seed 42, temperature 0.6,
top_k 50, English, 24 kHz mono. Keep model, precision and seed the same to get the same voice.

## Pace

Render lines at natural pace, then set one tempo at stitch time. The approved pace is about 180 words per minute
(`--target-wpm 180`). Check by ear.

## Use it with the narrator-voice skill

The render script reads `<ref-dir>/ref-<voice>.wav` and `.txt`, so give the bundled clip the voice name `default`:

```bash
mkdir -p ref
cp ${CLAUDE_PLUGIN_ROOT}/voices/default-narrator/reference.wav ref/ref-default.wav
cp ${CLAUDE_PLUGIN_ROOT}/voices/default-narrator/reference.txt ref/ref-default.txt
.venv/bin/python ${CLAUDE_PLUGIN_ROOT}/scripts/voice/render_lines.py ../lines.json --voice default --ref-dir ref --out out --check
```

Skip the design and audition steps. To audition others instead, run `design_voices.py` and pick by ear.

## Licence

Released under the same licence as the plugin (see `../../LICENSE`).
