---
name: sprite-explainer
description: >
  Make a narrated explainer MP4 (or one self-contained HTML page) from transparent sprites on a paused GSAP timeline,
  with ONE voice take for the whole script. Covers the script markdown contract and the show/say respelling map, the
  one-take voice render, the audio build (uniform tempo to a target speaking pace, scene gaps capped at 1.2 s, cues,
  captions), the sprite pipeline (prompt header, item list, reference attachments, alpha trim, height table), the
  engine library (stage, player bar, sprites, belts, tokens, camera, captions), and build, proof, hero still and render.
  Use for "one take narration", "sprite explainer", "animated explainer with a camera", "build the page from cues",
  "tempo to N wpm", "cap the gaps", "hero still", or when the per-line pipeline gives a voice that shifts between lines.
---

# Sprite explainer: one take, one page

Order of work (every step is a script; `scripts/make_onetake_video.sh` chains them). A worked three-scene example lives
in `${CLAUDE_PLUGIN_ROOT}/templates/example/` and builds to a 16 second MP4.

## 1. Script and respellings
`script.md` per `templates/script-template.md`: `## Scene N. Title`, then `**Narration (N words):**`, then optional
bold-labelled notes (`**On screen:**`, ignored). `make_narration.py script.md --out narration.json --say-map saymap.json`
makes one chunk per sentence: `show` (captions) and, only when different, `say` (what the voice reads). The map
(`templates/saymap.example.json`) holds literal replaces, regex replaces and characters to drop. Acronyms spelled out,
numbers and clock times as words, product names by syllable. `--plain` treats a scene's whole body as narration.

## 2. Voice, check, audio
```bash
.venv/bin/python ${CLAUDE_PLUGIN_ROOT}/scripts/voice/one_take.py --narration narration.json --out audio/take-raw.wav
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/take_check.py --take audio/take-raw.wav --narration narration.json
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/audio_build.py --take audio/take-raw.wav --narration narration.json --out audio \
        --wpm 200 --gap-before 6=0.35 --words-json audio/take-raw.stt.json
```
- `one_take.py`: `--ref-wav`, `--ref-text-file` (or `--ref-text`), `--seed`, `--temperature`, `--top-k`, `--max-tokens`;
  no reference given = the bundled narrator. Needs the local models cached (mlx-audio, Apple Silicon).
- `audio_build.py`: speaking pace measured from the take, ONE tempo to `--wpm` (up or down; or `--tempo`), scene gaps
  `--gap-base 0.45` plus `--gap-before N=s`, scene gaps and any pause inside a scene capped by `--max-gap 1.2` (the kept tail pad counts, so `--tail` above 0.85 is capped), head 0.8, tail 0.8, cut at the
  last script word, -16 LUFS. `--words-json` reuses take_check's transcript for the pace; the sped take is transcribed again for
  the cues (`--scale-words` skips that for a draft, at a cost of about 0.45 s mean error). Output `cues.json`: scenes, chunks, captions, wpm, gaps.
- Pace is the owner's call by ear. Two approved cuts measured about 180 and about 207 speaking wpm.
- `sync_check.py` on the final m4a gives the real offsets (plan for about 150 ms; whisper reports a file's first word at 0).

## 3. Sprites
`templates/sprites/README.md`: prompt header + item list (`sprite_prompts.py`), reference attachments for every request,
`prep_sprites.py --src raw --out img --heights sprites.json` (alpha trim, height table x zoom 1.6, WebP q88). A
placeholder set for tests: `templates/example/make_placeholder_sprites.py`. Keeping one character on-model: the same
README ("Your character"); the neutral templates carry none, and a bundled style and mascot are in `styles/` and `mascots/`.

## 4. The page
Engine: `templates/engine/` (`engine.js`, `engine.css`, `filters.svg.html`, `page.html`, README). Write
`scenes.html` (one `<section class="scene" id="scN">` per scene, plus an optional `#world` for a camera set) and
`scenes.js` that hangs every animation off `S(id)`, `E(id)`, `SC(n)`: `sprite`, `popIn`, `squash`, `tagAt`+`tagPop`,
`belt`, `Tok` (ride, hop, loop), `cam`, `capHigh`. Then `project.json` and
`python3 ${CLAUDE_PLUGIN_ROOT}/scripts/build_explainer.py project.json` writes one HTML with everything inlined. GSAP is
found from `--gsap`, `$GSAP_JS`, `vendor/` or node_modules; it is not bundled.

## 5. Proof, hero, render
```bash
node ${CLAUDE_PLUGIN_ROOT}/scripts/proof.mjs --page build/page.html --out proof --cues audio/cues.json --audio audio/narration.m4a
node ${CLAUDE_PLUGIN_ROOT}/scripts/hero.mjs --page build/page.html --out out/hero.png
node ${CLAUDE_PLUGIN_ROOT}/scripts/render_frames.mjs --page build/page.html --audio audio/narration.m4a --out out/explainer.mp4
```
LOOK at every proof still, then three frames of the MP4. A frame costs about 0.3 s: a 16 s video took about 2.5 minutes.

## Private overlay
Logos, brand palettes and real-name lists stay out of the repo. Point `EXPLAINER_FORGE_OVERLAY` (or
`~/.config/explainer-forge/overlay`) at a folder: `names.txt` and `allow.txt` feed `name_check.py`; `theme.css` and
`assets/` feed `build_explainer.py` (`/*ASSET:name*/`, `/*ASSETURI:file*/`). Nothing there is ever required.

## Gotchas
- A line misread in the take cannot be patched alone: re-render the take or reword the line.
- Time-driven only: never wall-clock time in an animation, or stills and renders disagree with playback.
- Check `proof.mjs` output for text under 24 px after the camera scale; raise sizes or ease the zoom.
- Whisper turns spelled letters ("Q R") into one word; the take check shows a harmless replace.
