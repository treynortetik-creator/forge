# Music pipeline (generated tracks, loops, stingers, ambience)

Receipts: the roguelite's second music pass (34 paid Lyria calls, $2.72, 21 calls shipped a file and
13 shipped nothing for $1.04) and first pass (12 cues, $0.88, all passed on take 1); the
tower-defense game's written prompt list and per-call cost ledger.

## 1. Track inventory (decide before generating)

Per-area structure used in the roguelite (file keys in `music/manifest.json`):

| Role | Keys | Loop? |
|---|---|---|
| Title | `title`, `title-loop` | title plays once then chains into `title-loop` |
| Hub / home | `hub-<name>`, `hub-<name>-b` | loop |
| Combat per area | `combat-<area>`, `combat-<area>-b` (second variant), `combat-<area>-high` (intensity layer for mini-boss rooms) | loop |
| Boss | shared `boss`, then per-boss `boss-<name>`, phase tracks `boss-<name>-p2` (and `-p3`), final boss `boss-final` | loop |
| Rest, shop | `rest-<name>`, `shop` | loop |
| Interlude | `stair` (calm, also reused as post-boss aftermath at -4 dB), `vestibule` (pre-boss tension) | loop |
| Ending | `ending` | one-shot |
| Stings | `sting-victory`, `sting-death` | one-shot |

Fallbacks are code, not files: phase 2 missing falls back to phase 1, missing boss track falls back to
the shared boss track, a missing slot is silence. Code can land before the audio.

The tower-defense game's prompt list used the same shape: `title`, `map`, one battle track per
region/theme (`battle_a` to `battle_d`, then region themes added in a second campaign), one boss
track, a final-boss track written as a multi-phase cue, victory (6 s) and defeat (5 s) stings, a
generic boss-arrival sting (4 s), a dawn sting (5 s), and a 5 s leitmotif sting per boss (each one
instrument-and-mood sentence). Stings are short and cheap, leitmotifs make bosses recognisable.

## 2. Prompt shape

```
Instrumental, <length>, <BPM> BPM, <key>. <instruments, mood, scene>. Seamless loop, no vocals.
```
Examples of the shape (from the tower-defense list): "Instrumental, 3 min, 120 BPM, E minor. Upbeat
gothic battle music: driving strings, harpsichord ostinato, timpani, ... Seamless loop, no vocals."
Stings: "6-second triumphant victory fanfare with organ and brass".

- One original prompt per cue. No artist, song or film names.
- For a phase 2 or 3 cue, prepend the phase 1 prompt verbatim and add an escalation clause.
- The generator does not obey the prompt's tempo or key reliably (traps in SKILL.md), so the prompt
  is a request and the gates are the contract.

## 3. Generation (one take at a time, foreground)

- Endpoint used: OpenRouter chat completions with `modalities: ["text","audio"]`,
  `audio: {"format": "wav"}`, `stream: true`; audio arrives as base64 chunks in
  `choices[0].delta.audio.data`; the final SSE chunk carries `usage.cost`.
- Models: `google/lyria-3-pro-preview` ($0.08 a call, output about 118 to 147 s) and
  `google/lyria-3-clip-preview` ($0.04 a call, fixed output of about 30.77 s regardless of the
  requested duration, per a format probe). 12 of 12 first-pass calls billed exactly those prices.
  Use Pro for loops, Clip only for stings.
- Cost lookup: read `usage.cost` from the stream; the credits endpoint lags.
- Keep at most one raw WAV on disk (about 23 MB each). Check free disk before a batch.
- Log every call (time, key, take, model, cost, running total, gate result) to a ledger JSON and a
  readable log. Hard-stop before the cap with headroom held back (a working stop of $6.00 against an
  $8.00 cap, and a worst case of $5.44 computed in advance; actual spend was $2.72).

## 4. Gates (objective; looser than a human audit on purpose)

| Gate | Rule |
|---|---|
| Duration | at least 90 s of source audio for a loop |
| BPM | estimated BPM within +-6 of the prompt (half and double count as a match). Phase and variant cues: within +-4 of the reference cue's measured BPM (variants allowed +-6 or +-10 in some batches) |
| Key | for phase/variant cues, same tonic or relative major/minor or same chroma argmax as the reference. The estimator is a Krumhansl profile on a 12-bin chroma, crude on dense metal. Standalone cues have no key gate |
| Words | no run of 3 or more real words, whisper small.en over the full take, bracketed tags stripped. Fail closed if whisper or its model is missing. Positive control: a voice line gives a 71-word run |
| Loop body | qualifying stable region of 75 s or more for bosses, 60 s or more otherwise, then seam check |
| Seam | 0.3 s windows either side of the wrap within 3 dB of each other and within 8 dB of the program median |
| Ending (one-shots) | last 3 s RMS falls smoothly to -40 dB or lower, no step over 6 dB in a 100 ms window, piece 100 s or longer |
| Loudness | integrated -16 LUFS +-0.5, true peak <= -2 dBTP (`scripts/lufs-check.sh`) |

Take policy: planned takes first, keep the first take that passes (higher median RMS if two pass). A
retry only when every planned take failed a gate, and the failed gate goes in the log. Priority cues
may take up to 4 takes, others 2. Generate phase 1, gate it, then phase 2/3 against it; if phase 1
never passes, skip that boss's later phases and keep the shared track.

Take-saving rule: a take that failed only the soft musical gates (tempo, key, ending shape; never the
words gate) is kept as a 160 kbps Opus file so a human can accept it later for $0 with
`loopcut.py cut <file> --key <key> --write`.

What the gates did in the second pass:

- Shipped: phase 1 and 2 for two bosses and phase 1 for a third, ending (2 takes), 4 combat variants,
  1 of 4 intensity layers, a hub variant, two interlude loops, a title loop.
- Failed and fell back: one boss's phases 2 and 3 and three intensity layers (key gate, two takes
  each); the final boss's three forms (four takes all failed BPM: measured 150, 160, 160, 160 against
  a prompted 168), which kept the shared final-boss track.
- Observed: a take prompted for D minor measured F major; a prompted 96 BPM, 3/4 F major ending
  measured 100 BPM and B minor; a "calm" interlude measured 141 BPM by the cutter and 102 by the
  checker. Treat all of these as "unheard until a human listens".

## 5. Loop cutting (`scripts/loopcut.py`)

```bash
export MUSIC_DIR=public/assets/audio/music   # or pass --out-dir
python3 scripts/loopcut.py analyze take.wav               # JSON: bpm, phase, key, head/tail/median dB
python3 scripts/loopcut.py cut take.wav --key combat-a --write [--bpm 150] [--max-body 120] [--min-body 60] [--bpb 4] [--preroll 0.75]
```
How `cut` works: BPM from onset-envelope autocorrelation refined by a comb sum (prior around 125
BPM); the body starts on the first beat-grid bar after the RMS has been within 6 dB of the median for
at least 10 s and ends after a whole number of bars before it falls more than 6 dB; a one-bar
equal-power overlap of the body end into its own start removes the fade-out/fade-in hole; the file is
`[last preroll seconds of the loop][loop]`; loudnorm two-pass to I=-16 TP=-2 LRA=11; Opus 96 kbps ogg
and AAC 128 kbps m4a; then `manifest.json` gets `loop`, `durationSec`, `lufs`, `loopStart`,
`loopEnd`, `bpm`, `seamDb`. It flags `regenerate` (no qualifying 60 s region) or `seam-fail` instead
of forcing a bad loop.

Before the fix: 10 of 11 loops had faded heads/tails at -35 to -49 dB (median about -18.5), a 25 dB
hole every wrap. After: seam deltas 0.1 to 2.3 dB.

Manifest entry shape:
```json
"combat-a": { "ogg": "combat-a.ogg", "m4a": "combat-a.m4a", "loop": true, "durationSec": 99.96,
  "lufs": -16.0, "loopStart": 0.75, "loopEnd": 99.95, "bpm": 150.0, "seamDb": 0.8 }
```
`musicKey` and `argmax` are optional extras recorded by the generator script for later reference gates.

## 6. Dual export, ogg + m4a

Every file is exported twice, Opus-in-Ogg and AAC-in-M4A, and the manifest lists both. The runtime
picks the one the browser supports (the reason for shipping both is inferred: some browsers lack Opus
or AAC support; not tested here). When file count matters, ship ogg-only for the web build.

## 7. Ambience beds and spot sounds

- Beds: 28 s loops, -20 +-1 LUFS (music is -16), mono. Rebuilt as codec-safe seamless loops: trim
  100 ms ends, 1.5 s equal-power self-crossfade, rotate so the wrap sits at the quietest 80 ms on a
  low-slope zero crossing, file = `[60 ms margin][loop][60 ms margin]`, then measure each codec's
  real offset by cross-correlation and write `loopPts` per codec so the runtime can set loop points.
  (The original 6 s beds measured -24.1 and -28.3 LUFS, and with their gain handling were effectively
  inaudible at -32 to -40 LUFS.)
- Spots: 1 to 2 s one-shots on a random timer over each bed (a drip every 3 to 9 s).
- Loudness regression: `lufs-check.sh` excludes `amb_spot_*` from the -20 gate.

## 8. Mix and runtime rules

- Per-slot trims (calm rooms 3 to 4 dB under combat).
- Hold a boss theme until the boss-intro beat, with a 6 s safety timer, so the downbeat lands on the
  slam. A mid-fight save restore starts at once.
- Resume a looping slot's position after short interludes (shop, rest, stairs) for 10 minutes.
- Room-clear: low-pass 20 kHz to 800 Hz over 400 ms with -6 dB, opening back over 600 ms.
- Boss victory and run end must not share a sting without thought: both played the same victory
  sting, and run end replayed it into silence, so the ending got its own cue.
- Major-key victory cadence mid-fight was a real bug: a generated final-boss track resolved to a
  victory cadence every 147 s.
- Bug class found by reading code, not listening: `contextSlot` only resolved two boss slots, so
  five new boss files would have been dead until the routing was added. Wire routing before paying
  for cues.

## 9. Visual check

Render a waveform contact sheet of every file (ffmpeg `showwavespic=s=900x70` per file, labelled and
montaged with ImageMagick) and look at it. Envelope shape shows seam holes and dead tails faster than
numbers.
