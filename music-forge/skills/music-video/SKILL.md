---
name: music-video
description: "Turn a finished song, a shot plan and one keyframe still per shot into a frame-exact cut music video using OpenRouter video models and ffmpeg: validate the plan, write the still prompts, animate each shot (routed by model, resumable, cost-capped), cut it to the original song with burned captions, make vertical teasers, and review the result by looking at frames and checking the singing. Use when asked to make a music video, animate keyframes to a song, lip-sync shots to a track, cut a lyric video, or make social teasers from a finished video."
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep]
---

# Music Video

You turn a finished song into a cut video. You do not trust your own arithmetic or your own eyes on a clip you have not looked at. The split:

| Computed by the scripts | Judged by you (and the user) |
|---|---|
| shot timing: gaps, overlaps, total vs audio length, missing frames | whether the shots tell the song, which moments get a lip-sync shot |
| model choice from the routing table, clip length, estimated and real cost | whether a clip is any good: identity drift, extra people, dead faces |
| frame-exact slots, trimming and padding, caption burn-in, teaser windows | which shots to redo, which teaser windows are the gags |
| a whisper transcript of what a clip actually sang | whether the mouth and the song really line up |

Scripts live in `${CLAUDE_PLUGIN_ROOT}/scripts/video/`: `plan_check.py`, `still_prompts.py`, `build_clips.py`, `cut.py`, `review_frames.py`, `teasers.py`. They are standard-library Python 3.11+ plus `ffmpeg`/`ffprobe` (and `magick` for PNG captions and end cards). Run them with `uv run python ...` or plain `python3`.

> **Video models change weekly.** `scripts/video/data/model-routing.json` holds the routing rules and prices; every entry carries `checked: 2026-10-10`. Treat anything older than a few weeks as a hypothesis: re-read `GET https://openrouter.ai/api/v1/videos/models`, and test with a real paid submit before a large run. When the table and the live API disagree, the API wins and you update the table.

## The pipeline

```
song + lyric timestamps -> shot-plan.json -> plan_check.py -> keyframes (you + any image model)
   -> build_clips.py (--dry-run first) -> cut.py -> review frames + singing check -> redo bad shots -> teasers.py
```

Work in one project folder: `shot-plan.json`, `frames/`, `clips/`, `cuts/`, the song. Every script takes the plan path and defaults to folders beside it.

## Step 1: Shot plan

Ask for, or find, the song file and its timing: lyric timestamps (an SRT, embedded caption track, or a whisper transcript with times) and the section layout. If there are no timestamps, run `sung-vs-written` or `track-check` first to get section boundaries; do not invent times.

Write `shot-plan.json` (schema in `scripts/video/data/shot-plan.schema.json`, worked example in `scripts/video/fixtures/example-plan.json`):

```json
{"title": "...", "audio": "song.m4a", "fps": 30, "aspect": "16:9",
 "style": "one line prepended to every prompt",
 "identities": {"Maren": "a weathered lighthouse keeper with a grey beard and a yellow oilskin coat"},
 "shots": [{"id": "03", "time": "00:12.50-00:20.00", "slug": "keeper-sings", "frame": "03-keeper-sings",
            "description": "Close-up of Maren singing into a brass speaking tube, locked camera.",
            "sing": true, "face": "human"}]}
```

Rules for the plan:
- **Shots tile the whole song.** First starts at `00:00.00`, each starts where the last ends, the last ends at the audio length. No gaps, no overlaps.
- **Cut on lyric lines and section changes.** A shot is usually 3 to 8 seconds. Longer than the model's maximum clip (see the routing table) means the cut will hold or loop the last frames: split the shot instead.
- `sing: true` only for shots where a mouth must match the vocal. Everything else is `false`: more shots are cheaper and safer silent.
- `face`: `human` for a photoreal person's face on screen, `creature` for a non-human character, robot or animal, `none` for no face. Routing uses it. Leave it out if unsure and it is treated as unknown.
- **Looks, not names.** Put every recurring character in `identities` as a physical description and use the name only as a handle in `description`; the scripts swap in the look. A video model has never heard of your character's name.

Then validate before spending anything:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/video/plan_check.py shot-plan.json
```

It reports `GAP`, `OVERLAP`, `TOTAL` (shots vs audio length), missing keyframes, duplicate ids, and shots too long for their model. Fix every ERROR; `cut.py` refuses a plan that does not tile the song.

## Step 2: Keyframes

The user generates one still per shot with any image model (the scripts do not call one). You write the words:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/video/still_prompts.py shot-plan.json --out still-prompts.md
```

This writes a character-sheet prompt for each recurring character, then one prompt per shot with the look strings substituted and the exact filename to save under. Advice to pass on:
- Generate a character sheet first and attach it to every still that includes that character. Copy the look string word for word between prompts; re-wording it drifts the face.
- One scene per still, never a collage. State the exact head count ("exactly three people") when a shot has several characters.
- Save stills into `frames/` under the plan's `frame` names (png, jpg or webp).

Run `plan_check.py` again; it must find every frame.

## Step 3: Animate

Always dry-run first and show the user the table and the total:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/video/build_clips.py shot-plan.json --dry-run
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/video/build_clips.py shot-plan.json --max-usd 15            # silent, keyframes only
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/video/build_clips.py shot-plan.json --max-usd 15 --audio-refs   # singing shots get the song slice
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/video/build_clips.py shot-plan.json --only 03 07 --force        # redo specific shots
```

It needs `OPENROUTER_API_KEY` in the environment (never print it, never put it in the plan). Per shot it picks a model (shot `model` override, then the routing rules, then the default), sends the keyframe, polls, downloads to `clips/<id>-<slug>.mp4`, and writes `clips/<id>-<slug>.json` with the job id, model, prompt and cost. It is resumable (existing clips are skipped; `--force` moves the old take to `clips/_old/`), runs 5 workers, and enforces `--max-usd`: it refuses a run whose estimate is over the ceiling and stops submitting if actual spend reaches it. Estimates come from the routing table and are approximate; the sidecar cost is what the API reported.

> **Test status:** `build_clips.py` has been tested only against a local mock of the video API, not against live OpenRouter. The routing rules come from live runs with earlier scripts. Before a large run, do one cheap live shot (`--only <id> --max-usd 1`) and check the clip and its sidecar.

### `--audio-refs` uploads your song to a public host

Singing shots can take a slice of the song as an audio reference, but the video provider needs a public https URL for it. With `--audio-refs`, the script temp-uploads each slice (a few seconds of the song) to **uguu.se** (primary) or **litterbox.catbox.moe** (fallback, 1 hour expiry). Anyone with the URL can fetch it until it expires. **It is off by default.** Say this plainly to the user and get a yes before using it, especially for an unreleased song. Without the flag, singing shots are generated silent on the same model (the mouth will not match, and the cut lays the original song over everything anyway). Keyframes are never uploaded; they go inline.

### Dated observations (2026-10-10, one project, re-check before relying on them)

These are OBSERVATIONS from a single project, not guarantees. They are the reason the routing table looks the way it does.

- **Lip-sync shots go to Hailuo 3.** A shot that must sing to the song kept the real vocal on Hailuo 3. Seedance 2.5 audio references re-sang unreliably and sometimes ignored the song entirely (worst on wide shots of a whole band).
- **Seedance 2.5 refused photoreal human faces** with `400 InputImageSensitiveContentDetected.PrivacyInformation` ("may contain real person"). Refusals were **per image, not per character**; non-human faces passed. Re-prompting the shot as "fictional" did not help. Route human-face shots to Hailuo 3 (song or silent) or Seedance 1.5 Pro (silent, first frame only).
- **Seedance audio only works with the keyframe sent as `input_references`.** Pinning it as `first_frame` silently drops the audio. `build_clips.py` sends it that way; do not "fix" it.
- **A free 1-second validation probe is not a face-filter test.** The audio validation fails first, so every image appears to pass. Test the filter with a real submit (cheap: one short silent clip).
- **Wide shots with camera moves can hallucinate a duplicate character.** Lock the camera ("locked-off, the camera does not pan or move") and state the head count in the description ("exactly four musicians, only ONE of the drummer").
- **Kling 3 held identity well but ignored audio. Veo 3.1 Fast drifted identity.** HeyGen Video 1 was cheap (see the table's `price_note`) but stiffer.
- **Cost of record:** a video of roughly two and a half minutes and about thirty shots took one day of iteration and about $27 in total, including redos. Plan for redos; budget well above the first-pass estimate.

A refusal prints a hint and costs nothing; set that shot's `face` to `human`, or give it a `model` override, and re-run with `--only`.

## Step 4: Cut

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/video/cut.py shot-plan.json --out cuts/video.mp4 --captions lyrics.srt
```

- **Frame-exact.** Slots are whole frames computed from the plan's start times at a fixed fps (default 30), so cuts cannot drift; the output is the audio length to within one frame.
- Each clip is trimmed, or padded when short (`--pad hold` freezes the last frame, `--pad loop` loops), to its slot. Clip audio is discarded: the **original song** is laid over the whole video, because generated clips may re-sing.
- A shot with no clip falls back to a slow push-in on its keyframe and is listed in the output.
- **Captions** (optional SRT, section tags like `[Chorus]` skipped): uses ffmpeg's `subtitles` filter when this ffmpeg build has it (libass), otherwise renders each caption as an ImageMagick PNG overlay. Many ffmpeg builds lack the filter; the script detects it, so do not assume.
- Also writes `video-small.mp4` under `--small-mb` (default 45) for chat apps by lowering resolution and bitrate. Check the real size.
- `--prefer-dir clips/redo` lets a folder of redone clips override `clips/` without moving files.

## Step 5: Review loop (do not skip it)

Never ship a cut you have not looked at.

1. Extract a frame at each shot's midpoint (add `--edges` for shots with camera moves, `--sing-audio` to dump each singing clip's audio):
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/video/review_frames.py shot-plan.json cuts/video.mp4 --edges --sing-audio
   ```
2. **Look at every frame** (Read the images). Check for: **duplicate characters** (a second drummer), a **camera pan that invented extra people**, **identity drift** between shots (hair, coat, face), hands and instruments, text or logos that should not be there, a dead or frozen face on a singing shot.
3. **Singing check** on every `sing: true` shot (`review/<id>.wav` from `--sing-audio`): confirm the clip actually sang the song.
   ```bash
   whisper-cli -m /path/to/ggml-small.en.bin -f review/03.wav -nt          # or: sung_check.py review/03.wav --vocals review/03.wav --lyrics shot-lines.txt
   ```
   Compare the transcript with that slice of the lyrics. Seedance 2.5 audio references sometimes ignore the song or sing different words; that is the failure this catches. A transcript is a model's guess at sung audio: a mismatch means "listen to this clip", not a verdict.
4. List the bad shots with the reason, tell the user, and **redo only those**: edit the description (lock the camera, state the head count), change `face` or `model`, then `build_clips.py --only <ids> --force --max-usd <small>` and re-cut. Old takes sit in `clips/_old/`.
5. When the user approves, they decide what ships. Report the real total cost from the sidecars.

## Step 6: Teasers

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/video/teasers.py cuts/video.mp4 \
    --window hook=0:00-0:12 --window chorus=1:05-1:20 \
    --end-card art/banner.jpg --title "Song Title" --outdir cuts/teasers
```

Each window is rendered as 16:9 and as a 9:16 vertical with a blurred copy filling the frame, a 0.3 s fade in and 0.8 s fade out, and an optional end card (image and/or title text, 1.5 s). Windows can also come from `--windows file.json`. Pick windows that each carry one idea (one gag, or pure performance), on shot boundaries when possible, and look at the first and last frame of each before posting.

## Output contract

Finish by telling the user: the output paths (`cuts/video.mp4`, `-small.mp4`, teaser folder), shots still on keyframe stills, shots that failed review, real total spend (sum the sidecars), and that any `--audio-refs` upload went to a public temp host.
