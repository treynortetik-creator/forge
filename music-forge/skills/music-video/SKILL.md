---
name: music-video
description: "Turn a finished song, a shot plan and one keyframe still per shot into a frame-exact cut music video using OpenRouter video models and ffmpeg: validate the plan, write the still prompts, animate each shot (routed by shot type, resumable, cost-capped), sync sung clips to the vocal by their own audio, chain and align consecutive shots, add camera sweeps in post, cut it to the original song with burned captions, make vertical teasers, and review the result by looking at frames and checking the singing. Use when asked to make a music video, animate keyframes to a song, lip-sync shots to a track, cut a lyric video, or make social teasers from a finished video."
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
| where a sung clip sits in the song (audio cross-correlation), join smoothness | whether the story and the characters read right |

Scripts live in `${CLAUDE_PLUGIN_ROOT}/scripts/video/`: `plan_check.py`, `still_prompts.py`, `build_clips.py`, `sync_offset.py`, `chain_join.py`, `post_sweep.py`, `cut.py`, `review_frames.py`, `teasers.py`. They are standard-library Python 3.11+ plus `ffmpeg`/`ffprobe` (and `magick` for PNG captions and end cards), except `sync_offset.py` (numpy) and `chain_join.py` (numpy + OpenCV), which run through `uv run --with numpy [--with opencv-python-headless] python ...`. Every script has `--help`.

> **Video models change weekly.** `scripts/video/data/model-routing.json` holds the routing rules and prices; every entry carries `checked: 2026-10-14`. Treat anything older than a few weeks as a hypothesis: re-read `GET https://openrouter.ai/api/v1/videos/models` (free, no key), and test with a real paid submit before a large run. When the table and the live API disagree, the API wins and you update the table.

References, read when the step needs them: `references/routing.md` (model per shot type, prices, long clips, refusals, spend), `references/prompt-rules.md`, `references/sync-and-chaining.md`, `references/post.md` (sweeps, crops, grades, text, retiming).

## The pipeline

```
song + lyric timestamps + stems -> shot-plan.json -> plan_check.py -> keyframes (you + any image model; check hands)
   -> build_clips.py (--dry-run first) -> strips -> sync_offset.py (sung) -> chain_join.py / post_sweep.py (free fixes)
   -> cut.py -> review with the user -> note rounds (one retry per shot) -> teasers.py
```

Work in one project folder: `shot-plan.json`, `frames/`, `clips/`, `cuts/`, `stems/`, the song. Every script takes the plan path and defaults to folders beside it.

## Hard-won rules (from a 3:39 video made 2026-10-14; the why is in `references/`)

1. **Sync sung clips by their audio, never by timestamps.** Generation windows came back 0.3-0.6 s off their slots. `sync_offset.py --write-sidecar`, then `cut.py` slides each clip into place.
2. **Pick the audio reference by shot:** vocal stem for sung close-ups, full mix for sung wides, an instruments-only mix plus "nobody sings, mouths closed" for instrumental band shots, a TTS clip of the line for a spoken or mouthed line (drop its audio in the edit).
3. **Chain consecutive shots** from the previous shot's real last frame, never from the same still twice (it stutters). Then `chain_join.py align` the join (chained gens came back ~2.5% larger and ~10 px shifted) and `check` it.
4. **Describe only what is in the first frame.** A wardrobe item named only in the prompt appeared mid-shot.
5. **No size words in action prompts** ("towering" doubled a character's size); say "same size and proportions throughout".
6. **Looks, never names; exact head count; "two hands each".** Check every non-human character's hands in every keyframe: the model copies a human hand on a werewolf.
7. **Perspective trap:** a figure walking toward a far doorway shrinks to child size. Use a tracking shot behind them, or a few steps only.
8. **Camera moves and text happen in post.** Prompted sweeps on wides were ignored; `post_sweep.py` is free. Generate signs and programmes blank and set the type in post.
9. **Look at a strip of every clip, one retry max per shot, keep the rejects.** Then the user watches the cut: they catch story and character problems you will not (who has the power in a scene, whether a face reads as heartbroken). Plan for several note rounds, each with its own `--max-usd`.
10. **Story canon becomes prompt constraints.** Keep a running canon list (example: "the creature is effortlessly strong; his creator fears him") and paste it into every shot it touches.
11. **Check the provider key's spend limit before a big batch.** A key's monthly cap halted a round mid-run.

## Step 1: Shot plan

Ask for, or find, the song file and its timing: lyric timestamps (an SRT, embedded caption track, or a whisper transcript with times) and the section layout. If there are no timestamps, run `sung-vs-written` or `track-check` first to get section boundaries; do not invent times.

Write `shot-plan.json` (schema in `scripts/video/data/shot-plan.schema.json`, worked example in `scripts/video/fixtures/example-plan.json`):

```json
{"title": "...", "audio": "song.m4a", "fps": 30, "aspect": "16:9",
 "style": "one line prepended to every prompt",
 "stems": {"vocals": "stems/vocals.wav", "instrumental": "stems/instrumental.wav"},
 "identities": {"Maren": "a weathered lighthouse keeper with a grey beard and a yellow oilskin coat"},
 "shots": [{"id": "03", "time": "00:12.50-00:20.00", "slug": "keeper-sings", "frame": "03-keeper-sings",
            "description": "Close-up of Maren singing into a brass speaking tube, locked camera.",
            "sing": true, "face": "human", "framing": "close", "audio_ref": "vocals"}]}
```

Rules for the plan:
- **Shots tile the whole song.** First starts at `00:00.00`, each starts where the last ends, the last ends at the audio length. No gaps, no overlaps.
- **Cut on lyric lines and section changes.** A shot is usually 3 to 8 seconds. Longer than the model's maximum clip (see the routing table) means the cut will hold or loop the last frames: split the shot instead.
- `sing: true` only for shots where a mouth must match the vocal. Everything else is `false`: more shots are cheaper and safer silent.
- Routing fields (leave any out if unsure): `framing` `close`/`medium`/`wide`; `kind` `acting` (silent emotion), `action` (physical action, a state change), `performance`, `insert`, `establishing`; `face` `human`/`creature`/`none`; `audio_ref` `mix` (default), a `stems` key, or a file path (a TTS line). See the routing table below.
- **Render SD for phone-first social.** 480p is the default wherever the model offers it; it cuts the price per second.
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
- Draw closed mouths on anyone who must not sing; open mouths in the still stay open for the first second of the clip.
- Save stills into `frames/` under the plan's `frame` names (png, jpg or webp).

**Check every still before animating** (Read it): hands on every non-human character, head count, props, text (there should be none), and whether the still shows exactly what the shot description says, because the motion prompt must describe only what is in the first frame. Fix a bad still with an edit prompt that changes one thing and keeps the rest, saved as a new file. More in `references/prompt-rules.md`.

Run `plan_check.py` again; it must find every frame.

## Step 3: Animate

Always dry-run first and show the user the table and the total:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/video/build_clips.py shot-plan.json --dry-run
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/video/build_clips.py shot-plan.json --max-usd 15            # silent, keyframes only
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/video/build_clips.py shot-plan.json --max-usd 15 --audio-refs   # sung and audio_ref shots get their audio
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/video/build_clips.py shot-plan.json --only 03 07 --force        # redo specific shots
```

It needs `OPENROUTER_API_KEY` in the environment (never print it, never put it in the plan). Per shot it picks a model (shot `model` override, then the routing rules, then the default), sends the keyframe, polls, downloads to `clips/<id>-<slug>.mp4`, and writes `clips/<id>-<slug>.json` with the job id, model, prompt and cost. It is resumable (existing clips are skipped; `--force` moves the old take to `clips/_old/`), runs 5 workers, and enforces `--max-usd`: it refuses a run whose estimate is over the ceiling and stops submitting if actual spend reaches it. Estimates come from the routing table and are approximate; the sidecar cost is what the API reported.

> **Test status:** `build_clips.py` has been tested only against a local mock of the video API, not against live OpenRouter. The routing rules come from live runs with project-specific runners. Before a large run, do one cheap live shot (`--only <id> --max-usd 1`) and check the clip and its sidecar. Check the key's own limit too (`GET https://openrouter.ai/api/v1/key`): it can run out while the account has credit.

A refusal ("may contain real person") prints a hint and costs nothing. Give that shot a `model` override (Hailuo 3 Max for silent acting, Hailuo 3 for sung) and re-run with `--only`. Never alter the image to get it past a filter.

### `--audio-refs` uploads your song to a public host

Sung shots, and any shot with an `audio_ref`, can take an audio reference (a slice of the song or a stem, or a file such as a TTS line), but the video provider needs a public https URL for it. With `--audio-refs`, the script temp-uploads each piece (a few seconds of audio) to **uguu.se** (primary) or **litterbox.catbox.moe** (fallback, 1 hour expiry). Anyone with the URL can fetch it until it expires. **It is off by default.** Say this plainly to the user and get a yes before using it, especially for an unreleased song. Without the flag, singing shots are generated silent on the same model (the mouth will not match, and the cut lays the original song over everything anyway). Keyframes are never uploaded; they go inline.

### Routing table (checked 2026-10-14; depth and caveats in `references/routing.md`)

| Shot | Model (480p unless noted) | Audio reference | Price |
|---|---|---|---|
| sung close-up / medium | HeyGen Video 1 | vocal-stem slice; image + audio both as `input_references` (it rejects `first_frame` plus references) | ~$0.035-0.07/s |
| sung band wide, hero performance | Hailuo 3 (2K only) | full-mix slice, so hands and drums move to the music | $0.13/s + $0.04/image |
| band shot in an instrumental | Hailuo 3 | instruments-only stem mix + "nobody sings, mouths closed" | as above |
| silent emotional acting (fear, grief) | Hailuo 3 Max | none | $0.05/s |
| action, state changes, no-face physics | Seedance 2.5 (may refuse photoreal faces as "real person") | none | $0.08-0.10/s |
| cheap silent shots, simple inserts, photoreal faces | Seedance 1.5 Pro (default) | none | ~$0.012/s |

Not routed: HeyGen Avatar IV (exact sync, but a static talking head), Grok Imagine (morphs instead of cutting), Wan 3.0 and Seedance 2.5 long multi-scene clips (cuts land on the beat, but identity drifts after scene 1 and bodies or scale go wrong: at most one scene set per request, about 13 s, or single shots).


## Step 4: Sync, chain and sweep (free)

Before cutting, make a frame strip of every new clip and look at it (`ffmpeg -i clip.mp4 -vf "fps=2,scale=320:-2,tile=6x3" -frames:v 1 strip.jpg`); one mid-shot frame misses scale jumps and extra people.

```bash
uv run --with numpy python ${CLAUDE_PLUGIN_ROOT}/scripts/video/sync_offset.py clips/14-*.mp4 --ref stems/vocals.wav --write-sidecar   # sung close-ups
uv run --with numpy python ${CLAUDE_PLUGIN_ROOT}/scripts/video/sync_offset.py clips/30-*.mp4 --ref song.m4a --write-sidecar          # sung wides
uv run --with numpy --with opencv-python-headless python ${CLAUDE_PLUGIN_ROOT}/scripts/video/chain_join.py align frames/c13.png clips/13-x.mp4 clips/redo/13-x.mp4
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/video/post_sweep.py clips/22-band-wide.mp4 clips/redo/22-band-wide.mp4
```

- `sync_offset.py` measures where each sung clip's own soundtrack sits in the reference (the audio it was generated from) and stores `song_t0` in its sidecar; `cut.py` enters the clip there. A LOW PEAK result means the clip does not carry that audio: listen to it instead. Details: `references/sync-and-chaining.md`.
- `chain_join.py` grabs the last shown frame to chain from (`last-frame`), aligns the incoming clip (`align`), and measures the join in the cut (`check`).
- `post_sweep.py` adds a push-in and an eased pan to a locked-off wide. Crops, regrades and retiming recipes: `references/post.md`.

## Step 5: Cut

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/video/cut.py shot-plan.json --out cuts/video.mp4 --captions lyrics.srt
```

- **Frame-exact.** Slots are whole frames computed from the plan's start times at a fixed fps (default 30), so cuts cannot drift; the output is the audio length to within one frame.
- Each clip is trimmed, or padded when short (`--pad hold` freezes the last frame, `--pad loop` loops), to its slot. Clip audio is discarded: the **original song** is laid over the whole video, because generated clips may re-sing.
- A shot with no clip falls back to a slow push-in on its keyframe and is listed in the output.
- **Captions** (optional SRT, section tags like `[Chorus]` skipped): uses ffmpeg's `subtitles` filter when this ffmpeg build has it (libass), otherwise renders each caption as an ImageMagick PNG overlay. Many ffmpeg builds lack the filter; the script detects it, so do not assume.
- Also writes `video-small.mp4` under `--small-mb` (default 45) for chat apps by lowering resolution and bitrate. Check the real size.
- `--prefer-dir clips/redo` lets a folder of redone clips override `clips/` without moving files.
- **Sync.** A clip whose sidecar has `song_t0` enters at `slot start - song_t0` (first frame held if the take starts late), and the output lists the offsets used. `--no-sync` ignores them.

## Step 6: Review loop (do not skip it)

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
4. List the bad shots with the reason, tell the user, and **redo only those**: edit the description (lock the camera, state the head count), change `face` or `model`, then `build_clips.py --only <ids> --force --max-usd <small>` and re-cut. **One retry per shot**; after that, fix it in post (crop, regrade, retime) or cut it. Old takes sit in `clips/_old/`; keep them, a rejected take is sometimes the fallback.
5. **The user watches the whole cut** and you plan for several note rounds: they catch story and character problems frame checks cannot (a power dynamic that reads backwards, a face that is not sad enough). Turn each story note into a canon line and apply it to every affected shot. Each round gets its own budget.
6. When the user approves, they decide what ships. Report the real total cost from the sidecars.

## Step 7: Teasers

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/video/teasers.py cuts/video.mp4 \
    --window hook=0:00-0:12 --window chorus=1:05-1:20 \
    --end-card art/banner.jpg --title "Song Title" --outdir cuts/teasers
```

Each window is rendered as 16:9 and as a 9:16 vertical with a blurred copy filling the frame, a 0.3 s fade in and 0.8 s fade out, and an optional end card (image and/or title text, 1.5 s). Windows can also come from `--windows file.json`. Pick windows that each carry one idea (one gag, or pure performance), on shot boundaries when possible, and look at the first and last frame of each before posting.

## Output contract

Finish by telling the user: the output paths (`cuts/video.mp4`, `-small.mp4`, teaser folder), shots still on keyframe stills, shots that failed review, real total spend (sum the sidecars), and that any `--audio-refs` upload went to a public temp host.
