---
name: game-audio
description: >
  Voice, music and audio-engine workflow for a browser or desktop game, built so money is not spent
  blind. Casts every voiced character on purpose before any paid TTS (per-character voice spec,
  measured pitch/F0 audit, cheap auditions, 2-line gate), directs voices to act instead of narrate
  (ElevenLabs v3 tags, clean close-mic), writes a cost plan and checks the commercial licence before
  spend, packs voice and quips under file-count and per-file size caps, generates per-area, boss,
  phase, title and sting music with measurable gates (BPM, key, words, loop seam, LUFS), exports
  ogg+m4a, and wires a Web Audio engine that respects browser autoplay. Use when asked to "cast
  voices", "voice the characters", "record lines", "generate music", "game soundtrack", "loop a
  track", "pack voice", "audio budget", "loudness", "autoplay audio", or before any paid
  voice, music or SFX generation call.
---

# game-audio

The case in one line: audio is where money, licences and taste all get spent without anyone looking,
so every paid call is preceded by a written plan and followed by a measurement, and the ear gets the
last word on what the numbers cannot judge.

Forge's thesis applies: judgment (does this voice fit, does this track feel right) stays with the
model and the owner; anything expressed as a number (pitch in Hz, BPM, LUFS, seam delta, bytes,
dollars) is measured, not guessed. Receipts come from a Phaser 4 roguelite (a 29-voice cast, 505 voice
lines, about 30 music files) and a tower-defense game (a written music prompt list and a per-call cost ledger).

Sibling skills: `game-forge:game-qa-loop` (audit and playtest the finished build),
`game-forge:art-waves` (the same plan-spend-measure shape for art), `game-forge:game-lessons`
(cross-cutting rules). Method depth lives in `references/`:

| File | What it holds |
|---|---|
| `references/voice-casting.md` | spec template, audit method, audition table, the 2-line gate, measured model comparison |
| `references/voice-direction-packing.md` | acting direction, ElevenLabs settings, post chain, bitrates, pack format and size caps |
| `references/music-pipeline.md` | track inventory per game area, prompts, gates and what failed, loop cutting, dual export |
| `references/cost-and-licences.md` | cost-plan template, ledger, commercial terms by tool, Steam disclosure notes |

## Scripts (copied from the roguelite, generalised, none run against a real project in this skill)

| Script | Use |
|---|---|
| `scripts/voice-f0.py` | Praat two-pass median F0 plus spectral centroid per file or pooled. Needs `praat-parselmouth`, `numpy`, ffmpeg. Verified here only as far as `py_compile` and the import error without parselmouth |
| `scripts/loopcut.py` | `analyze` (BPM, key, head/tail level) and `cut` (beat-grid loop body, 1-bar self-overlap, two-pass loudnorm, ogg+m4a, manifest entry). Needs ffmpeg, numpy, scipy. `--help` verified |
| `scripts/lufs-check.sh` | Loudness regression gate: music -16 +-0.5 LUFS and true peak <= -2 dBTP, ambience -20 +-1. `bash -n` verified |
| `scripts/pack-voice.ts` + `scripts/voiceChunks.ts` | One audio sprite per speaker (Opus 40 kbps + AAC 56 kbps), chunked ~40 s by trigger, `pack.json` with start/dur in ms. Run with `npx tsx`. Type-strip syntax check verified; not executed |

## Workflow

### 1. Cast before you spend (voice)

Fires before any first recording, recast, retake, new lines for an existing character, or before
dispatching a helper to do any of those. Full method in `references/voice-casting.md`.

1. **Spec per character, no paid calls.** Fields: who (species, body, age, size), origin and a
   deliberately chosen accent with the reason, pitch range plus a target median F0 in Hz, texture,
   pace and energy, range (angry, tender, afraid), and an Avoid list. Describe sounds, never name
   a real actor. Never default to one accent and never accept the library's first hit.
2. **Audit the current cast (free).** Pull each voice's library metadata
   (`GET /v1/voices/{id}`: accent, age, gender, description). Measure every existing file:
   `python3 scripts/voice-f0.py --pool audio-src/voice/<character>-*.m4a` gives pooled median F0,
   p10/p90 and centroid. Flag each mismatch against the spec with the numbers.
3. **Shortlist from metadata and free previews.** `GET /v1/shared-voices` with accent/age/gender
   filters; download the library preview clips and pitch-screen them before any paid call.
4. **Audition cheaply.** One short in-character line (under ~120 characters) per candidate, the
   same line for the current voice as a control, measure F0 and centroid, transcribe with whisper
   to catch mispronunciations. Log every call's cost from the response header.
5. **Write the casting doc** (spec, current vs chosen with numbers, final voice id, model,
   settings, tags, target F0 and gate band). It is binding for whoever records.
6. **Gate the full set.** Record 2 lines per character first (one calm, one loud). Continue only
   if pooled F0 lands in the gate band, centroid is no more than ~300 Hz brighter than the
   audition, and whisper matches the text. Then priority lines, then the rest.

### 2. Direct the performance (voice)

- Characters act, they do not narrate. Write each design prompt as the person speaking to someone
  in a scene. Avoid "storyteller" and "narrator".
- Every voice-design prompt carries a clean-recording clause: close-mic studio condenser in a
  treated booth, full and dry, no reverb, no distance, no hiss, not lo-fi.
- Render on `eleven_v3` with inline tags (`[growls]`, `[gruff]`, `[sighs]`, `[laughs]`,
  `[shouting]`, `[dry, amused]`), stability 0.0 for barks and booming lines, 0.5 for calm and
  tender, `style` 0.3 to 0.8 (v3 only). Offer 3 or 4 directions per important line.
- Never mix models inside one character's line set.
- Respell names only in the text sent to TTS, and verify by transcript.

### 3. Plan the cost, check the licence (all paid generation)

Write the plan before the first call: item, value to the player, cheapest model/setting that
meets the bar, calls including retries, expected cost, acceptance check, total against the cap.
Cut low-value items. Check the commercial terms of the plan you are generating on before anything
ships (`references/cost-and-licences.md`). Keep a ledger, one line per paid call, with a hard stop
below the cap.

### 4. Make the files (voice and SFX)

1. Generate to a scratch directory, never straight into the shipped folder.
2. Post chain per line: trim silence, optional pitch or tempo, gain-match integrated LUFS to the
   line it replaces (within +-0.2 dB), limiter at -0.4 dBFS, mono 48 kHz, Opus ogg plus AAC m4a.
3. Pack lines into one sprite per speaker so file count stays low:
   `npx tsx scripts/pack-voice.ts --src audio-src/voice --out public/assets/audio/voice`.
4. Check sizes against the caps that actually bind your target (`references/voice-direction-packing.md`).
   If a pack is over a per-file cap, lower the Opus bitrate for that pack only, do not trim lines.

### 5. Music (generated tracks)

Full pipeline in `references/music-pipeline.md`.

1. **Inventory first**: title, hub, one combat loop per area, a second combat variant per area,
   a high-intensity layer per area, boss track per boss, phase 2/3 tracks, rest, shop, interlude
   (stairs, pre-boss tension), ending, stings (victory, death). Decide which cues are loops and
   which are one-shots.
2. **Prompt shape**: "Instrumental, <length>, <BPM>, <key>. <instruments and mood>. Seamless loop,
   no vocals." One original prompt per cue, no artist, song or film names.
3. **Generate one take at a time**, pass it through objective gates (BPM within +-6 of the prompt
   or +-4 of a reference cue, key match for phase variants, no run of 3 or more real words, loop
   seam), keep the first take that passes, log the cost.
4. **Cut loops** on the beat grid: `python3 scripts/loopcut.py cut <take.wav> --key hub --write`
   (with `MUSIC_DIR` or `--out-dir` set). This writes ogg+m4a and the manifest entry
   (`loopStart`, `loopEnd`, `bpm`, `lufs`, `seamDb`).
5. **Loudness gate**: `bash scripts/lufs-check.sh` (music -16 +-0.5 LUFS, TP <= -2 dBTP).
6. **Listen.** Gates are objective only. Every shipped take in the receipts below was "gated,
   unheard" until a human listened, and several cues (key, tempo) may not be what was asked.

### 6. Engine (browser)

- One AudioContext, buses: music, sfx, voice into master, a limiter on master. Volumes per bus.
- Browsers start the context suspended. Unlock on the first `pointerdown`, `keydown`, `touchend`
  or `mousedown` (capture phase, passive), and poll gamepads (a pad press counts as activation in
  Chromium). Queue "play" requests with a `whenUnlocked(cb)` hook so a title screen can ask for
  its track immediately and sound begins on the first press. Design the title so the first press
  is natural ("press any key").
- Suspend on `visibilitychange` hidden, resume on visible. If Web Audio is missing, everything
  becomes a silent no-op.
- Stream music through `<audio>` elements, decode SFX into buffers. A 100 s stereo track decodes
  to about 35 MB of PCM, and a run touches 14 tracks.
- Looping: `el.loop` is not gapless on AAC (priming). Cut loops with a pre-roll
  (`loopStart` 0.75 s in the receipts) and run an A/B pair of elements crossfading linearly over
  the pre-roll, because the overlapped signals are identical (an equal-power fade of identical
  material bulges +3 dB). Browser media clocks jitter by tens of ms, so this is not
  sample-accurate; the crossfade hides offsets below about 30 ms.
- A slot with no file is silence, never an error, so code can land before the audio does.

## Traps

Each rule with the failure that earned it.

1. **Library voices cast by label, not by number.** A huge feral character shipped on a voice
   labelled "British, young, upbeat" and measured 145 Hz median (target about 100) with a bright
   spectrum. The owner heard it instantly. Always measure F0 and centroid against the spec.
2. **Casting on the wrong model.** On the same voice, line and settings, `eleven_v4` measured
   higher than `eleven_v3` for every voice tested (144 Hz vs 72 Hz, 134 vs 121, 225 vs 188,
   131 vs 108, 143 vs 127). Re-run this comparison for any new model before casting; model names
   and behaviour change. One more observed v4 issue: a designed voice drifted about 45 Hz higher
   and repeated a phrase.
3. **Judging a shouty voice on its calm line.** A candidate measured 105 Hz calm and 255 Hz on an
   excited line, which is the thin shriek the owner rejected. Audition a calm line and a bark,
   and compare each against the current voice reading the same line.
4. **Pooling pitch across emotions without a target.** Shouted lines run 40 to 100 Hz above calm.
   Set the target for the whole delivered set, and give a gate band (calm floor, bark ceiling).
5. **Audiobook voices.** Voice-design previews from "storyteller" prompts came back as narration
   with room tone and distance. Describe a scene, add the clean clause, direct at render time.
6. **Stability 0.5 flattens exclamations.** On v3 a booming line came back as a statement
   ("service!" became "service."). Barks use stability 0.0 plus `[shouting]` or `[excited]`.
7. **Tags read aloud or ignored.** Audio tags were never spoken in the tests, but one `[growls]`
   came back as "Argh!" once, which is the intent. Verify tags by transcript and by ear.
8. **Spending without a plan.** The standing rule exists because voices were cast "by
   convenience" from 30+ library voices and then recorded in full. The audition pass for a 29-voice
   cast with 5 recast candidates cost 747 of a 3,000 credit cap (45 calls, 3,389 characters).
9. **Credits are not list price.** The billed rate seen was 0.22 credits per character against a
   list assumption of 1.0. Read the `character-cost` response header per call, not the account
   counter, which lags and is shared with other jobs.
10. **A commercial-licence surprise after the fact.** The account in use was pay-as-you-go, which
    on the date checked ran on free-plan terms with no commercial licence, and content made before
    upgrading could not be used commercially. All shipped voice and SFX had to be regenerated on a
    paid plan. Check terms before generating anything that ships (`references/cost-and-licences.md`).
11. **Output format limits.** Pay-as-you-go output tops out at `mp3_44100_128`; `mp3_44100_192`
    needs Creator or above. Do not plan a quality chain around a format you cannot get.
12. **Loop seams.** Ten of eleven generated loops had first/last 0.3 s at -35 to -49 dB against a
    program median near -18.5 dB: a fade-out into a fade-in on every wrap (a 25 dB hole every
    ~2 minutes). Cut loops on the beat grid with a self-overlap and check the 0.3 s windows.
13. **A generator that ignores the prompt.** Asked for D minor, a take measured F major. Asked for
    168 BPM, four takes measured 150 to 160. Phase-2 takes came back at about 2/3 of the prompted
    tempo. Gate on measurement, and for phase variants gate against the phase-1 take's measured
    BPM and key, not the prompt.
14. **Whisper hears words in wordless choirs.** A naive "any word fails" gate trips on "you" from
    noise. Fail on 3 or more real words in a row, strip bracketed tags, and make the gate fail
    closed (whisper missing counts as a fail, never a pass).
15. **Trusting your own key estimator.** A Krumhansl chroma estimator was crude on dense metal and
    rejected same-key phase variants. A cosine second opinion did not separate same-key from
    unrelated pairs (unrelated up to 0.945, same-key 0.954 to 0.998), so the gate was kept and
    losers fell back to the base track. Do not loosen a gate to make a batch pass.
16. **The title that cannot loop.** The first title track had only a 58 s stable region, under the
    60 s minimum. loopcut flags it instead of forcing; the title plays once, then chains into a
    separate loop cut.
17. **Peak overshoot after encode.** A vestibule cue measured -1.5 dBTP and had to be re-limited to
    -2.7. Measure true peak on the encoded file, not the source WAV.
18. **Caps that outlive their reason.** A 30 KB-per-quip-pack cap and a low Opus bitrate were web
    download limits. When the target moved to Steam (whole game installed to disk), the review
    listed them under "loosen". Tie every size cap to a real distribution constraint, otherwise make
    it a warning.
19. **File-count caps.** 505 voice lines times two formats was 1,011 files against a 1,000-file
    web-host cap. Sprites per speaker (one pack per speaker, chunked by scene) fixed it, at the cost
    of a lazy-load marker lookup in the runtime.
20. **Re-encoding untouched files.** ffmpeg re-encodes unchanged packs to different bytes, which
    pollutes diffs. When re-packing one speaker, restore the others from git afterwards (the
    roguelite used a tiny wrapper that ran `git checkout` on every pack not named).
21. **Do not default songs to spoken-word intros.** When making sung AI songs (not game music),
    an owner flagged `[Spoken Word]` intros as overused after they appeared on most tracks. Open with
    an instrumental tag or the sung hook, vary structure, check earlier tracks first.
22. **Deleted raw takes.** Raw generation WAVs are about 23 MB each; keep at most one on disk,
    delete after encoding, and check free disk before a batch.
23. **Leaking the key.** Never print the API key. Scripts read it from the environment or
    a `.env` file and the logs record cost per call only.

## Done when

- Casting doc exists with numbers, and every recorded character passed its 2-line gate.
- Cost plan written before spend; ledger totals match the response headers; spend reported.
- Licence of the generating plan confirmed in writing at generation time and noted in the doc.
- Voice packs under the file-count and size caps that bind your distribution target.
- Every music file: seam, BPM, key (where gated) and words gates logged; `lufs-check.sh` passes;
  a human has listened to each track at least once, and the unheard ones are listed in the report.
- Audio begins after the first user press on a cold browser, with no console autoplay error,
  and nothing plays while the tab is hidden.
