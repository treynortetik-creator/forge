# Coworker baritone

A designed, fully synthetic narrator: warm lower baritone, neutral General American accent, calm, like a friendly
coworker explaining something. Made from a written description by a text-to-voice model. No real person's voice was
recorded or cloned. This is the voice of the approved reference cut for the `clay-factory` style.

| File | What it is |
|---|---|
| `reference.wav` | 17 s, mono 24 kHz 16-bit. The designed clip, edge-trimmed, then slowed to 0.75x with pitch kept |
| `reference.txt` | the exact words in `reference.wav` (the clone model needs them) |
| `sample.m4a` | 13.6 s: the reference clip itself, sped up 1.27x to about 207 words per minute while speaking. A clone reading a full script sounds close to this but is not this file |

## Recipe

| Setting | Value |
|---|---|
| Design model | `mlx-community/Qwen3-TTS-12Hz-1.7B-VoiceDesign-bf16` |
| Clone model (reads the script) | `mlx-community/Qwen3-TTS-12Hz-1.7B-Base-bf16` |
| Seed | 7, set before the design and again before the clone |
| Temperature, top_k, language | 0.6, 50, `english` |
| Whole script | ONE generate call, `split_pattern=""`, `max_tokens=9000` (enough for about 900 words; raise it for more) |

Design prompt, word for word:

> A lower-pitched, warm baritone voice, around 40 years old, grounded and relaxed, understated and calm. Speaks American
> English with a neutral General American accent, no British or foreign accent. Adult man. Casual and smooth, warm,
> light and conversational, like a smart friendly coworker walking you through something. Relaxed medium pace, calm
> intonation with modest pitch variation. Not an announcer, not an audiobook reader, not dramatic, not breathy.

Measured: median pitch about 104 Hz. Raw whole-script take: 220.6 words per minute while speaking over 877 words;
shipped at 207.3 after one uniform tempo of 0.9407. Generation took 229 s for a 243 s take on a 10-core, 32 GB Apple
Silicon laptop. Two small flaws were left in the approved take (a stray pause, one muddy phrase).

Siblings auditioned from the same prompt tail and not picked: a mid-range tenor (seed 42) and a brighter young voice
(seed 123).

## Say it this way

"AI" as "A I" and "AI agents", never "AIs"; numbers and clock times as words; names respelled by ear. Put these in the
project's `saymap.json`; captions keep the real spelling. Transcription tools normalise names, so only a person can
check how a name sounds.

## Licence

Same as the plugin (see `../../LICENSE`). The model cards said Apache-2.0 when checked; check again before you rely on
it.
