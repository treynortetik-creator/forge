# Recording gameplay: demo videos and highlight reels

Two different deliverables. Decide which one was asked for before recording anything.

## Rule: a "demo" is raw, uncut, small

When the owner asks for a demo video of a game, send **the raw live playthrough: no title cards, no on-screen text,
720p, compressed under about 35 MB** so it can be attached to a chat. Origin: a 79 s cut with title cards came in at
48 MB, was slow to arrive, and the response was to send the full thing with no text and a lower resolution.

- Default encode: 1280 wide, H.264 at about 1.3 Mbps plus 96k AAC, `-movflags +faststart`.
- Make a cut-with-cards or music version only if it is asked for. (A promo video for a different game was explicitly
  asked to have type cards and music; the rule is about what was requested, not a ban on cards.)
- 35 MB is a chat-attachment ceiling, not a quality target. Check the size before sending; `cut-reel.sh` exits 1 over it.

## Highlight reel (asked for: a cut of the best moments)

Receipt: five short segments recorded at 1920x1080 / 30 fps, trimmed into 10 clips, concatenated, scaled to 720p,
x264 CRF 22 with `-maxrate 3200k`, music added: **78 s in 24.9 MB** (verified with ffprobe: h264 1280x720 30 fps + aac).

### Step 1: plan segments

Use the game's URL dev params to jump straight to scenes (seed, scene, bot, room, boss, fast-forward `t`), and
let a bot play so the footage shows competent play. A segment is `{name, q, pre, dur, keys}`:

```json
[
  { "name": "a-title", "q": "scene=ui&screen=title&mute=1", "pre": 1500, "dur": 6000,
    "keys": [ { "at": 3000, "click": [960, 540] } ] },
  { "name": "b-fight", "q": "scene=run&seed=7&bot=skilled&t=40&mute=1", "pre": 1500, "dur": 20000 },
  { "name": "c-boss",  "q": "scene=run&room=boss_room_id&bot=skilled&mute=1", "pre": 1500, "dur": 25000,
    "keys": [ { "at": 500, "down": "KeyW" }, { "at": 1500, "up": "KeyW" } ] }
]
```

`mute=1` is on because the screencast records video only (puppeteer's `ScreenRecorder` type has no audio option; the
soundtrack comes from the music file in step 3). A key is `down` / `up` / `press`, or `click: [x, y]` in page pixels;
`at` is ms from the start of recording.

### Step 2: record

```bash
SK=${CLAUDE_PLUGIN_ROOT}/skills/game-qa-loop/scripts
bash ${CLAUDE_PLUGIN_ROOT}/skills/game-lessons/scripts/heavy-lock.sh -- node $SK/record-reel.mjs --project <game repo> --out reel-raw --segments segments.json \
     --serve "node server/index.mjs" --serve-env DIST_DIR=dist
# or against a server you already run:  --url http://localhost:5173/
```

`--serve` gives your command a random `PORT`; adapt the env to how your server reads its port and directory.
The recorder opens one page per segment (so a crash costs one segment), waits for the ready flag, pauses `pre` ms,
starts `page.screencast({ path, fps: 30 })`, plays the key timeline, waits out `dur`, stops. Requirements:
`puppeteer-core` in the game repo, system Chrome, and `ffmpeg` on PATH (puppeteer's screencast needs it).

### Step 3: look, cut, encode

1. Make a contact sheet or extract frames from each raw segment and LOOK at them (`ffmpeg -i seg.webm -vf fps=1,scale=480:-1,tile=6x3 sheet.png`;
   this tile command was smoke-tested on a synthetic clip). Dead time at the start, a loading veil, or a bot standing
   still gets cut. Raw screencast `.webm` files have no duration header (`ffprobe` prints N/A); that is normal, and
   trimming with `-ss`/`-t` still works.
2. Cut and encode:
   ```bash
   bash $SK/cut-reel.sh -o reel.mp4 -m music.mp3 -w 1280 -c 22 -r 3200k \
        reel-raw/a-title.webm,0.5,5 reel-raw/b-fight.webm,2,12 reel-raw/c-boss.webm,0,20
   ```
   Each `file,START,DUR` is one clip (a segment can appear several times with different trims). Every clip is encoded
   with identical settings so the concat can stream-copy; music is faded out over the last 2 s.
3. Check: `ffprobe` size/duration, under the limit, plays from the start. Look at a few frames of the FINAL file.

### Music

Use music you made or are licensed to use (see game-forge's audio skill for generating a track). Never drop in a
commercial track for a reel that will be posted.

## Traps

- **Headless frame rate.** Screencast records what the headless GPU renders; a slow software renderer gives a
  choppy reel. Record at the same settings you profiled, check one segment before recording all of them, and
  prefer a bot run that shows the game's best moments over a long idle stretch.
- **Key timing.** A same-frame press/release can be lost to input that is polled per frame: hold across frames
  (`down` ... 160 ms ... `up`). The perf harness for the roguelite found this when driving menus.
- **One browser at a time.** Recording is a heavy job: run it under the heavy lock (`game-lessons/scripts/heavy-lock.sh`).
- **Do not narrate with text cards by default** (see the demo rule above).
