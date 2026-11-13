# Voice casting method

Source of every number here: a casting pass on a 29-voice cast, 45 audition calls, 747 credits
spent against a 3,000 credit cap. Tools: ElevenLabs REST (`/v1/voices/{id}`, `/v1/shared-voices`,
text-to-speech), Praat via `parselmouth`, ffmpeg, whisper small.en. Nothing here depends on the
game's story; swap in your own characters.

## 1. Voice spec template (one per speaking character)

| Field | What to decide |
|---|---|
| Who | species or body (a huge feral creature is deep and chesty; a ghost child is small and airy), age, size, health |
| Origin | class and place in the world. Choose the accent deliberately and write why. Never default to posh British or to the library's first hit |
| Pitch | range, a **target median F0 in Hz**, and a gate band |
| Texture | gravel, rasp, breath, wet, nasal, clean; growl or creak where the body calls for it |
| Pace and energy | slow/heavy vs quick; default emotion |
| Range | how they sound angry, tender, afraid (angry should usually be lower and harder, not shriller) |
| Avoid | the specific wrong reads (thin, prim, boyish, "upbeat podcast", generic narrator) |

Rough pitch anchors used in the casting pass (median F0): deep adult male 70 to 110 Hz, typical male
100 to 140, typical female 170 to 230, child 250+. Observed targets for characters: huge creature 55
to 75, farmer 110, old groundsman 90, steward 125, alto heroine 190, bright sprite 280.

**Accent plan.** Write one paragraph that assigns accent on purpose. The pass used accent to code
where characters come from (an old-world household in European-coded voices, a rural family in one
accent family so mother and offspring sound related, posh English only where the character is meant to
be posh). Add the rule "no two characters who share a scene share both a pitch band and an accent"
and check clusters (old low men, grand women, young heroes, big friendly voices).

Describe the sound; never name a real actor or celebrity. Never cast a voice that reads as a famous
film villain impression.

## 2. Audit the current cast (free)

1. Metadata: `GET /v1/voices/{id}` for every cast voice; record accent, age, gender, description.
2. Measure files with `scripts/voice-f0.py`:
   ```bash
   python3 -m venv /tmp/f0venv && /tmp/f0venv/bin/pip install praat-parselmouth numpy
   /tmp/f0venv/bin/python scripts/voice-f0.py --pool audio-src/voice/<character>-*.m4a
   ```
   Output JSON: `f0_med`, `f0_p10`, `f0_p90`, search `range`, `cent_med`, `n_files`, `n_frames`.
   Without `--pool` it prints one entry per file including `dur_s`.
3. Method details (so you can trust it): two-pass Praat autocorrelation. Pass 1 uses 50 to 600 Hz,
   pass 2 sets floor = 0.75 x Q1 and ceiling = 1.5 x Q3 of pass 1 (the Hirst method), 10 ms frames,
   voiced frames only, pooled across every file for a character. Sanity check: a 110 Hz sine reads
   110.0. A numpy YIN tracker agreed within about 8 Hz on most characters.
4. Brightness: median spectral centroid of the energetic frames (1,024-point FFT at 22.05 kHz,
   frames within 30 dB of the peak RMS). Lower is darker and chestier. Gravel raises centroid, so it
   is a texture cue, not only a pitch cue.
5. Rate: characters per second of active speech.
6. Intelligibility: whisper small.en on every audition. Audio tags were not read aloud.
7. Make an audit table: voice labels, line count, F0 median (p10-p90), target, centroid, rate, and a
   status: RECAST (wrong voice), MODEL (right voice, wrong model, fix by re-recording), MINOR
   (drift with few lines, no action), OK.

Result in the pass: 3 of 29 were RECAST, 3 MODEL, 2 swapped (two siblings cast the wrong way round),
several MINOR. A library label like "deep" or "gruff" was not a reliable indicator on its own.

## 3. Fair comparison rule

A shouted line raises pitch by 50 to 100 Hz. Compare each candidate with the **current voice reading
the same line** (a control take), never with the current voice's whole set. Audition at least a calm
line and a bark.

## 4. Auditions (cheap)

- Shortlist 3 candidates per character from `GET /v1/shared-voices` (accent, age, gender filters), 5
  to 16 filtered queries per character in the pass. Download every library preview clip (free) and
  pitch-screen before any paid call. One pass screened 176 previews for one character.
- One test line per candidate under ~120 characters, in character, including a tag the cast will use.
- Measure F0 + centroid, whisper-check text, pick the best fit. Tune stability, similarity, style,
  speed and tags.
- Cap the audition budget (a few thousand credits for a whole cast) and log each call.
- A low-pitch candidate can be a trap: one that read 108 Hz on a female part sounded like a man.
  Compare against the target band, not only "lower is better".

Model check (same voice, same line, same settings, two models). Re-run this for any model update
before locking a cast, because model behaviour changes:

| Voice | v4 F0 / centroid | v3 F0 / centroid | Target |
|---|---|---|---|
| male, old-world | 134 / 1,458 | 121 / 1,075 | 110 |
| female alto | 225 / 1,868 | 188 / 1,695 | 190 |
| male baritone | 131 / 2,070 | 108 / 1,944 | 115 |
| deep American | 144 / 1,709 (calm) | 72 / 1,182 (calm) | 100 median over the set |

The same pass found `eleven_multilingual_v2` also gave a lower pitch (63 Hz) for the deep candidate
but takes no audio tags, so growls would have to come from post.

## 5. The casting doc (binding for whoever records)

Per character: voice id, name, model, settings (stability, similarity, style, speaker boost), tags,
target F0, **gate band** (for example target 100, gate 85 to 120; calm no lower than 70, barks no
higher than 170), and the reason. Add a "Still open" list for unresolved characters (few lines,
low priority) rather than blocking.

## 6. Gate for the generator

1. Per character, record 2 lines first: one calm, one bark.
2. Measure pooled F0 with `voice-f0.py --pool`. Continue only if the pooled pair lands in the gate
   band, the centroid is no brighter than the audition by more than 300 Hz, and whisper small.en
   matches the text.
3. Then priority-1 lines, then the rest. Do not mix models inside one character.
4. Size the job: count text characters per character and add about 15 percent for v3 tags. In the
   pass the required recast set was about 3.4k characters (about 0.8k credits at the 0.22 credits
   per character billed rate; list would be about 3.4k) and an optional re-record set was 6.6k
   characters (about 1.5k credits).
5. Pronunciation: respell names only in the TTS text. Run whisper on every tricky name and on
   homophones (a word like "coal" was heard as "call" by both voices tested). Check by ear.

## 7. Post-processing notes from the pass

- Pitch shift is a last resort. A -2 semitone shift took one candidate's calm and bark takes to 99 to
  112 Hz but left his excited take at 227 Hz. Prefer a voice that stays big when it shouts.
- Pace: if a calm v3 line runs under about 12 characters per second, speed it up with `atempo`
  (pitch-safe) toward the character's target pace (14.5 characters per second for a fast speaker).
- Optional growl layer for combat barks only: a doubled take pitched -5 semitones, low-passed at
  700 Hz, mixed under at -12 dB (the `growl` option in the post chain, `references/voice-direction-packing.md`).
- Loudness-match each line to the integrated LUFS of the line it replaces.

## 8. Final report to the owner

Casting table (character, voice, why, target F0 vs measured), what was re-recorded, spend vs plan,
what is still off with the file to listen to first.
