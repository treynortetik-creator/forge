# explainer-forge

Make instructional and explainer videos with Claude Code: a narrated MP4 with captions, or one self-contained
interactive HTML explainer. Built from two real runs: a set of narrated interactive explainers and a product-demo
video approved on its second cut.

It follows the Forge rule: **judgment stays with the model, and anything expressed as a number gets measured
instead of eyeballed.** Words per minute, cue times, sync offsets, ring positions, word error rates and runtime are
computed by scripts. What to say, what to show and whether it feels right stay with the owner and the model.

## Install

```bash
claude plugin marketplace add treynortetik-creator/forge
claude plugin install explainer-forge@forge
```

Needs `ffmpeg`/`ffprobe`, Node 18+ with Playwright (`npm i playwright` in your project), and Python 3.11+ with
numpy. The narrator voice runs locally on Apple Silicon through `mlx-audio` (Python 3.12 venv; see
`skills/narrator-voice`). Pillow for `inline_build.py` images; Blender only for `decimate_glb.py`.

## Five skills

| Skill | Use it when |
|---|---|
| **make-an-explainer** | starting from a topic, ticket, feature or doc. The ordered recipe with gates: length cap, fact-checked script, style sample first, voice spec and cost plan before spend, proof before send |
| **narrator-voice** | you need the voice. Design 3 candidates, the owner picks, clone every line, whisper-check, fix pronunciation in a TTS-only spelling, set speed once by ear |
| **app-footage** | the subject is software. Sample data with a badge, fake cursor, human-paced typing, time-lapsed waits, a manifest, tracked patches over ugly UI text |
| **render-and-caption** | turning clips and a timeline page into a frame-exact MP4 with word-timed captions and an SRT, or one inlined HTML file |
| **explainer-proof** | before anyone else sees it: 2-second review sheets, ring crops, A/V sync, names grep, slide and sync tests for interactive files |

## Scripts

| Script | Does |
|---|---|
| `scripts/voice/design_voices.py` | VoiceDesign 3 candidates → audition samples + clone references + report |
| `scripts/voice/render_lines.py` | clone every line from the reference; `--check` whisper/pitch/wpm per line |
| `scripts/voice/analyze_clip.py`, `drift_test.py` | measure one clip; prove the clone holds steady across lines |
| `scripts/stitch_narration.py` | trim, ONE tempo for all clips, fixed gaps → narration + exact cues + wpm table |
| `scripts/captions.py` | whisper word times → 2-row caption chunks + SRT |
| `scripts/prep_media.py` | short-GOP footage for frame-exact seeks + the page's data file |
| `scripts/track_patch.py`, `detect_band.py` | follow scrolling text; time a cover over a panel |
| `scripts/render_frames.mjs` | seek-per-frame parallel render → H.264 + AAC |
| `scripts/ring_check.mjs`, `verify_video.sh`, `name_check.py`, `deck_proof.mjs` | the proof pass |
| `scripts/inline_build.py`, `decimate_glb.py` | one-file HTML; web-sized 3D props |
| `scripts/make_video.sh` | stitch → captions → prep → render → verify in one command |

Voice: `voices/default-narrator/`. Templates: `stage.html` + `timeline.js` (the timeline engine), `scenes.example.js`, `lines.example.json`,
`script-template.md`, `voice.example.json`. Lessons and numbers: `references/`.

**Bundled:** one default narrator voice, `voices/default-narrator/` (a designed, fully synthetic reference clip, its transcript and a 29 s sample at about 180 wpm). Use it as is or design your own with `narrator-voice`.

**Not included:** brand assets, fonts, model weights.

## Test status (0.1.0 draft)

Scripts are generalised from the two runs' tooling. Checked: Python compiles, JavaScript passes `node --check`,
shell passes `bash -n`, JSON parses. Not yet run end to end on a fresh project after generalising.
