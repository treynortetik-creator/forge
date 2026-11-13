# Voice direction, post chain, packing

Receipts from the roguelite's voice pipeline (ElevenLabs text-to-speech, a Python post chain, a
TypeScript packer). Command and parameter names below come from scripts the project wrote and from
the ElevenLabs text-to-speech skill. Settings that are marked "inferred" were not directly tested.

## 1. Acting, not narrating

- Describe a person speaking to someone in a scene, not "a storyteller".
- Clean-recording clause in every design prompt: close-mic studio condenser in a treated booth, full
  and dry, no reverb, no distance, no hiss, not lo-fi. Without it, default previews carried room tone
  and sounded "10 feet from the microphone".
- Fixing a liked voice's sound: Voice Design remix with `text-to-voice/design`, `reference_audio_base64`
  set to the liked preview, `prompt_strength` 0.5, model `eleven_ttv_v3` and the clean clause. Then
  measure the noise floor (lower is cleaner) and median F0 (should stay near the original).
- Direct the performance at render time on `eleven_v3` with inline tags and stability 0.0. Offer 3 or
  4 directions per line.
- Stability 0.0 is the floor. Next levers: `style` 0.6 to 0.8 (v3 only), capital letters for
  emphasis, ellipses for pauses. One owner verdict after trying them: v3 + style 0.8 + hard tags was
  "much better" than the alternative.
- Observed on a newer `eleven_v4`: more animated but a designed voice drifted about 45 Hz higher and
  repeated a phrase. v4 supports only `stability` and `similarity_boost` (no `style`, no `speed`) per
  the ElevenLabs skill. Re-test before choosing a model; this changes.
- Last-resort fallback for lines that will not land: speech-to-speech (voice changer) on a performance
  the owner records. Untested in the game.

Inline tags used on lines: `[gruff]`, `[growls]`, `[growls softly]`, `[sighs]`, `[laughs]`,
`[shouting]`, `[excited]`, `[gravelly]`, `[chuckles]`, `[conspiratorial]`, `[dry, amused]`.

Per-character settings used (all on `eleven_v3`): stability 0.5 for story/idle/tender, 0.0 for barks
and booming lines; similarity 0.75 to 0.8; style 0.1 to 0.4 (0.1 to de-theatricalise a voice that
read as a pirate); speaker boost on.

## 2. Generating (REST shape used)

```
POST https://api.elevenlabs.io/v1/text-to-speech/{voice_id}?output_format=mp3_44100_128
header xi-api-key: $ELEVENLABS_API_KEY
body {"text": "...", "model_id": "eleven_v3",
      "voice_settings": {"stability": 0.5, "similarity_boost": 0.8, "style": 0.3, "use_speaker_boost": true}}
```
- Spend per call: read the response header `character-cost` (the SDK equivalent is
  `x-character-count`). The account counter (`GET /v1/user/subscription`) lags.
- Pay-as-you-go output is capped at `mp3_44100_128`; `mp3_44100_192` needs Creator or higher.
- SFX use `POST /v1/sound-generation` with `model_id: eleven_text_to_sound_v2`, `duration_seconds`
  and `prompt_influence` (0.4 used). A good prompt prefix: "Stylised game sound effect, clean, dry,
  close-mic, no music, no voice unless stated."

## 3. Post chain per line (the roguelite's `voicegen.py post`)

1. Trim silence: front threshold -45 dB with 0.04 s keep, then reverse and trim the tail with 0.12 s
   keep.
2. Optional pitch (`asetrate`, `aresample`, `atempo` combo) and tempo (`atempo`).
3. Optional growl layer (barks only): doubled take -5 st, 700 Hz low-pass, -12 dB, `amix` with
   `normalize=0`.
4. Gain-match integrated LUFS (ebur128) to the file being replaced, then `alimiter=limit=0.954`
   (about -0.4 dBFS, attack 3, release 40).
5. Mono 48 kHz. Encode Opus ogg 72 kbps and AAC m4a 96 kbps (`-movflags +faststart`).
6. Report `ms`, `lufs`, reference LUFS and gain applied.

Local ffmpeg had no libvorbis, so ".ogg" here is Opus in an Ogg container (`-c:a libopus`). Both
projects did the same.

## 4. SFX loudness (match to a mean, not a peak)

`loudmatch.py` pattern: compress (`acompressor=threshold=-26dB:ratio=4:attack=2:release=80`), apply
gain to a target mean volume measured with `volumedetect`, then `alimiter=limit=0.891` (about -1
dBFS), re-encode ogg 64 kbps (mono 48 kHz) and m4a 96 kbps (44.1 kHz). Durations do not change, so the
manifest needs no edit.

## 5. Packing voice into sprites

Why: 505 lines times two formats was 1,011 files, over a 1,000-file web-host cap, and each line is a
separate network request.

`scripts/pack-voice.ts` input: `<src>/manifest.json` mapping `id -> {ogg, m4a, durationMs, speaker}`.
Output per speaker: `<out>/<speaker>.ogg` (Opus 40 kbps) and `<speaker>.m4a` (AAC 56 kbps), joined
with 250 ms of silence, mono 48 kHz, and `<out>/pack.json`:

```json
{ "version": 1,
  "packs": { "speaker": { "ogg": "speaker.ogg", "m4a": "speaker.m4a", "ms": 41230 } },
  "lines": { "line-id": { "speaker": "speaker", "start": 1250, "dur": 1900 } } }
```
A runtime plays a line by loading its speaker's pack once (lazy) and playing the `[start, start+dur]`
marker. Chunking (`scripts/voiceChunks.ts`): a speaker over 60 s total is split into about 40 s chunks
(`<speaker>-1`, `-2`, ...), grouped by trigger so a scene loads one small chunk instead of a 5 minute
sprite. A trigger group is never split unless it is itself longer than the target. Hub NPCs that talk
one scene at a time can use a longer 48 s target (list them in `NPC_SPEAKERS`, which ships empty).
Pass `--bank <lines.json>` (array of `{id, trigger}`) to group by scene; without it, chunks follow id
order.

Options: `--encode a,b` re-encodes only those speakers (ffmpeg gives different bytes on re-encode,
so you do not want untouched packs rewritten). `pack.json` is always rebuilt. Stale chunk files left
by an earlier split are removed (a speaker that dropped from 9 chunks to 7 would otherwise ship
dead files that count against the file budget).

Syntax-checked here, not executed.

## 6. Bitrates and size caps (the "bitrate switch")

| Asset | Codec and rate in the roguelite |
|---|---|
| Voice line (loose) | Opus 72 kbps + AAC 96 kbps, mono |
| Voice pack sprite | Opus 40 kbps + AAC 56 kbps, mono 48 kHz |
| SFX | Opus 64 kbps (mono 48 kHz) + AAC 96 kbps (mono 44.1 kHz) |
| Music | Opus 96 kbps + AAC 128 kbps, loudnorm I=-16 TP=-2 LRA=11 |
| Placeholder TTS quips (Kokoro, free, local) | Opus 20 kbps default, `-application voip` |

Placeholder-then-real pattern: ship free local Kokoro-82M narration as placeholders with a
`placeholder: true` flag in the manifest, and replace clips later by id. The project's placeholder script took three env vars: an override directory (real recordings take
precedence), an only-these-packs list (rewrite named packs only) and an Opus bitrate (applies to the
packs written in that run). Real takes run
longer than placeholders, so a pack over its per-file cap gets a lower bitrate for that pack only:
one quip pack was written at 17 kbps (default 20) to stay under a 30 KB per-pack cap. That script
was not copied into this skill because it is tied to the game's data modules; the pattern is here.

Do not invent a cap. In the roguelite the file-count, per-pack KB and "first play 20 MB" limits were
self-imposed for web hosts; when the target became Steam (whole game on disk) the review listed the
VO bitrate and 30 KB cap under "loosen to full quality". Caps are worth keeping only when tied to a
real constraint (host file count, patch size, Steam Deck memory). Otherwise keep them as warnings.

## 7. Repack without churn

When regenerating one speaker, re-run the packer, then restore every other pack from version control
so unchanged speakers keep identical bytes:

```bash
npx tsx scripts/pack-voice.ts | tail -1
cd public/assets/audio/voice
for f in *.ogg *.m4a; do  # keep only the named speakers, checkout the rest
  keep=0; for s in "$@"; do [ "$f" = "$s.ogg" ] || [ "$f" = "$s.m4a" ] && keep=1; done
  [ $keep = 0 ] && git checkout -q -- "$f"
done
```
