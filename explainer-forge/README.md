# explainer-forge

Make instructional and explainer videos with Claude Code: a narrated MP4 with captions, or one self-contained
interactive HTML explainer. Built from real runs: a set of narrated interactive explainers, a product-demo video
approved on its second cut, and (0.2.0) a four-minute sprite-world explainer with one voice take for the whole script.

It follows the Forge rule: **judgment stays with the model, and anything expressed as a number gets measured
instead of eyeballed.** Words per minute, cue times, sync offsets, ring positions, word error rates and runtime are
computed by scripts. What to say, what to show and whether it feels right stay with the owner and the model.

## Install

```bash
claude plugin marketplace add treynortetik-creator/forge
claude plugin install explainer-forge@forge
```

Needs `ffmpeg`/`ffprobe`, Node 18+ with Playwright (`npm i playwright` in your project, or `PLAYWRIGHT_PATH=<dir>`),
a Chrome or Playwright's Chromium (`CHROME_PATH=<exe>` to pick one), GSAP (`npm i gsap`, or `GSAP_JS=<file>`; not
bundled) and Python 3.11+ with numpy, soundfile and Pillow. The narrator voice runs locally on Apple Silicon through `mlx-audio` (Python 3.12 venv; see
`skills/narrator-voice`). Pillow for `inline_build.py` images; Blender only for `decimate_glb.py`.

## Skills

| Skill | Use it when |
|---|---|
| **make-an-explainer** | starting from a topic, ticket, feature or doc. The ordered recipe with gates: length cap, fact-checked script, style sample first, voice spec and cost plan before spend, proof before send |
| **narrator-voice** | you need the voice. Audition the two bundled voices (a man, a woman) or design 3 candidates, the owner picks, record the whole script in ONE take, whisper-check, fix pronunciation in a TTS-only spelling, one tempo to a measured pace. One clip per line is the named fallback |
| **app-footage** | the subject is software. Sample data with a badge, fake cursor, human-paced typing, time-lapsed waits, a manifest, tracked patches over ugly UI text |
| **render-and-caption** | turning clips and a timeline page into a frame-exact MP4 with word-timed captions and an SRT, or one inlined HTML file |
| **explainer-proof** | before anyone else sees it: 2-second review sheets, ring crops, A/V sync, names grep, text size after camera scale, dead air, slide and sync tests for interactive files |
| **sprite-explainer** | one voice take for the whole script, a uniform tempo to a target pace, capped scene gaps, a sprite pipeline, the engine, proof, a hero still and the render (new in 0.2.0) |
| **house-style**, **lessons-loop** | the rules each cut taught, with their reasons, and the loop that turns a finished video into the next video's rules |

## Scripts

| Script | Does |
|---|---|
| `scripts/voice/design_voices.py` | VoiceDesign 3 candidates → audition samples + clone references + report |
| `scripts/voice/render_lines.py` | fallback: clone every line from the reference; `--check` whisper/pitch/wpm per line |
| `scripts/voice/analyze_clip.py`, `drift_test.py` | measure one clip; prove the clone holds steady across lines |
| `scripts/stitch_narration.py` | fallback: trim, ONE tempo for all clips, fixed gaps → narration + exact cues + wpm table |
| `scripts/captions.py` | whisper word times → 2-row caption chunks + SRT |
| `scripts/prep_media.py` | short-GOP footage for frame-exact seeks + the page's data file |
| `scripts/track_patch.py`, `detect_band.py` | follow scrolling text; time a cover over a panel |
| `scripts/render_frames.mjs` | seek-per-frame parallel render → H.264 + AAC; `--frames DIR` makes it resumable |
| `scripts/ring_check.mjs`, `verify_video.sh`, `name_check.py`, `deck_proof.mjs` | the proof pass (`name_check.py` and the build read an optional private overlay) |
| `scripts/inline_build.py`, `decimate_glb.py` | one-file HTML; web-sized 3D props |
| `scripts/make_video.sh` | stitch → captions → prep → render → verify in one command (the per-line fallback route) |
| `scripts/make_narration.py` | script markdown → `narration.json`: a chunk per sentence, `show` (captions) apart from `say` (spoken), from a respelling map |
| `scripts/voice/one_take.py` | the whole script as ONE voice-clone take; reference, seed, temperature, top_k are arguments (default: bundled narrator) |
| `scripts/take_check.py` | whisper the take, diff against the spoken text, list long silences |
| `scripts/audio_build.py` | one uniform tempo to a target speaking wpm, mid-gap scene cuts, gaps capped at 1.2 s, tail trim, -16 LUFS, `cues.json` + SRT |
| `scripts/sync_check.py`, `dead_air.py` | re-transcribe the final audio and measure every scene opening against the measured speech onset; find silences over 1.2 s |
| `scripts/sprite_prompts.py`, `prep_sprites.py` | style header + item list → prompts; alpha trim + height table → WebP |
| `scripts/build_explainer.py` | engine + scenes + sprites + fonts + audio + cues → one self-contained page (optional private overlay) |
| `scripts/proof.mjs`, `hero.mjs` | stills per cue chunk, page errors, text under 24 px after camera scale, dead air; a hero still from the same page |
| `scripts/make_onetake_video.sh` | narration → take → check → audio → sprites → build → proof → hero → render, one step at a time or all |
| `scripts/pw_common.mjs`, `overlay.py` | find Playwright and Chrome without hard-coded paths; find the private overlay folder |

Voices: `voices/coworker-baritone/` (a man) and `voices/default-narrator/` (a woman). Templates: `stage.html` + `timeline.js` (the per-line fallback timeline), `engine/` (the sprite-world
engine: stage, player, camera, belts, tokens, captions), `example/` (a three-scene parcel example that builds to a 16 s
MP4), `sprites/` (prompt header, item list, the reference-attachment pattern, a placeholder for your own character),
`saymap.example.json`, `scenes.example.js`, `lines.example.json`, `script-template.md`, `voice.example.json`.
Lessons and numbers: `references/` (60 lessons).

**Bundled:** two synthetic narrator voices (designed from a text description, no real person): `voices/coworker-baritone/` (a man, seed 7, about 207 wpm sample) and `voices/default-narrator/` (a woman, seed 42, about 180 wpm sample), each with its reference clip and transcript; a house style, `styles/clay-factory/` (palette, rules, prompts, 2 SIL OFL font families with `fonts/OFL.txt`, a sprite library); a mascot, `mascots/ember/`; and format profiles in `profiles/`. Use them as is or add your own style, mascot or voice beside them.

**Not included:** third-party brand assets or logos, model weights, GSAP, a click-through slide engine (profiles `deck-voiceover` and `compliance-connector` are marked partial for that).

## Test status (0.2.0)

Run on 2026-11-22: `scripts/test_narration_lib.py` (pure functions: script parser, say map, alignment, tempo, gap cap,
cut points, captions, sync) plus `test_audio_and_checks.py` (a 48 kHz take, pause squeeze, name check on a long single line); `audio_build.py` on a real 243 s, 877-word take (262.3 s output, the same as the pipeline it replaced; scene-opening cues now within 30 ms of the measured speech onset, where whisper-only times led the sound by 0.1 to 0.5 s); the example built, proofed (0 page errors, 0 small text, 0 dead air),
rendered to a 15.9 s 1080p30 MP4 with the bundled narrator and checked frame by frame. Not tested: Intel or Linux
(the voice and whisper need Apple Silicon), the interactive page's phone layout on a real phone, `--frames` resume after
a real interruption, a camera-heavy 4-minute page through the new `render_frames.mjs` (the old v3 renderer did it).
