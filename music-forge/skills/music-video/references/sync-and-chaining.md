# Lip sync, mouthed lines and chained shots (2026-10-14)

## Place sung clips by their audio, never by timestamps

Lip-sync models that take an audio reference pass it through into the clip's soundtrack. That soundtrack is the ground truth for where the clip sits in the song. On 2026-10-14 every sung clip placed by its lyric-alignment slot was 0.3-0.6 s off (the generation windows had started away from the slot), and the viewer read it as bad lip sync although every mouth was right.

```bash
# vocal stem for close-ups, the song for wides: whatever the clip was generated from
uv run --with numpy python ${CLAUDE_PLUGIN_ROOT}/scripts/video/sync_offset.py clips/14-*.mp4 --ref stems/vocals.wav --write-sidecar
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/video/cut.py shot-plan.json --out cuts/video.mp4      # enters each measured clip at slot - T
```

- `sync_offset.py` cross-correlates the clip's own audio against the reference (full decode; an AAC `-ss` seek shifted audio by about 50 ms) and reports `T`, the song time at the clip's first frame. `--write-sidecar` stores it as `song_t0`; `cut.py` then enters the clip at `slot_start - T`, holding the first frame when the take starts late. `--no-sync` turns that off.
- A peak under about 0.5 means the clip does not carry the reference audio (it re-sang, or the model made its own soundtrack). The tool refuses to write that T. Check that clip by ear and eye.
- After the slide, residual error was 0 ms (within a frame) on every sung clip.

## Which audio goes in as the reference

| Shot | Reference | Prompt |
|---|---|---|
| Sung close-up | vocal stem slice | "his mouth matches the vocals of the audio" |
| Sung band wide | full mix slice | name who sings; everyone else "mouth closed" |
| Instrumental band shot | instruments-only stem mix (drums + bass + other) | "an instrumental break: nobody sings, all mouths stay closed the entire time" |
| Spoken or mouthed line (not sung) | a TTS clip of the line, padded to the clip length with the line where it should land | "slowly and clearly mouths the words '...'", then drop the generated audio in the edit |

Set it per shot with `audio_ref` (`"mix"`, a key of the plan's `stems`, or a file path) and run `build_clips.py --audio-refs`. Stems come from Demucs (`sung-vs-written` already runs it); check the stems line up with the song before trusting them.

## Chain consecutive shots, then fix the join

Two consecutive shots generated from the same keyframe stutter at the cut: the second one snaps back to the keyframe pose. It happened twice in one video. Chain instead:

1. Cut the outgoing shot, then grab the exact last frame the cut shows: `chain_join.py last-frame <trimmed segment> frames/cNN-from-MM.png` (or `--at <seconds>` on the untrimmed clip).
2. Generate the incoming shot from that frame (put it in `frames/` and point the shot's `frame` at it).
3. Even chained, the new clip came back about 2.5% larger and about 10 px shifted, with a slight regrade. Fix it:
   ```bash
   uv run --with numpy --with opencv-python-headless python ${CLAUDE_PLUGIN_ROOT}/scripts/video/chain_join.py align frames/c13-from-12.png clips/13-*.mp4 clips/13-aligned.mp4
   ```
   ECC affine registration onto the reference frame, one constant per-channel colour gain/offset, the duplicate first frame dropped, a 2-frame dissolve out of the reference. Add `--dedupe` for Hailuo 3 Max output, `--speed` to land an action inside its slot.
4. Measure the join in the cut: `chain_join.py check cuts/video.mp4 44.0`. Normal motion is about 1-3 (mean abs difference, 0-255); a jump is a spike well above its neighbours. Measured: 15.75 and 17.25 before, 1.65 and 2.74 after.

Put the aligned clip where `cut.py` finds it (`--prefer-dir` a redo folder, or replace the clip) and keep the original.
