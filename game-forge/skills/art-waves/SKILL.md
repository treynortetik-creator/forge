---
name: art-waves
description: >
  Produce 2D game art in batches ("waves") with an external image model (Codex, the
  ChatGPT image app, or an API) without losing consistency or the owner's taste: pre-flight
  (is it really a 2D asset?), the wave brief file, zip handoff, the return check, naming and
  manifests, cut-outs (alpha, trim, pad, cell fit, feet anchors), the ink-redraw post pipeline,
  palette audit and art-measure (numbers, not eyeballs), a taste file the owner maintains,
  labelled proofs, caps that trace to a real constraint, a placeholder guard, the VFX
  three-layer and colour doctrine, portraits with blink patches, and living-ink ambient motion.
  Use for "next batch of art", "write the wave brief", "bundle it for Codex", "check what came
  back", "cut this out", "is this on palette", "measure the outline", "keep a taste file",
  "add glow/blink/shimmer", "art budget", or any 2D art production loop with an image model.
---

# Art Waves

**The one-line case:** an image model gives you a great picture and a terrible asset pipeline. Over
twenty-odd waves on a roguelite, every problem that cost a day was one of five things: asking the model for
something it cannot do (animation strips for a 3D character), a return nobody measured (wrong canvas,
baked background, one-sided alpha), a style rule living only in someone's head, a number that was
eyeballed ("too thick", "too dark", "too much colour"), or a cap nobody could trace to a real constraint.
This skill is the loop that fixed those, with the receipt attached to each rule.

> **House thesis, same as the rest of forge:** judgment stays with the model and the owner; anything
> expressed as a number gets measured. The model decides if it looks right. A script says what the outline
> width is.

Siblings: `game-forge:sprite-pipeline-3d` (3D bake path for characters), `game-forge:local-models` (local image
models), `game-forge:game-qa-loop` (screenshots, bots), `game-forge:game-lessons` (cross-cutting rules). For
HTML/slide visuals see `design-forge:art-department`. For modelling from photos see `design-forge:photo-to-3d-loop`.

Scripts live in `scripts/` (all Python, Pillow + numpy + scipy; Pillow below 13 for `art-measure.py`):

| Script | Job |
|---|---|
| `wave-pack.py` | zip a wave under a size cap; check a returned folder against the brief |
| `cutout-trim.py` | flat background to alpha, trim, pad, scale, fit to a cell with a feet anchor |
| `art-measure.py` | tone, outline, edge feathering, contact shadow, hatch, on sprites and screens |
| `calibrate-thresholds.py` | derive the verdict limits from the owner's good and bad examples |
| `palette-audit.py` | share of a screenshot that is off palette, with a heatmap |
| `contact-sheet.py` | labelled contact sheet (every cell carries its name) |

---

## 1. Pre-flight (all of it, before a word of the brief)

1. **Is every asset really 2D?** Decide per asset class which pipeline owns it. On the roguelite the standing
   rule was: the image model does 2D only (portraits, cards, UI frames, key art, backdrops, room mockups, 2D
   FX stills, icons, paper textures). Anything that is a 3D character in the game gets, from the model, only the
   clean 3D SOURCE image (flat grey background, 3/4 view, limbs apart, props held clear of the body, no glow),
   which then goes to an image-to-3D tool and Blender. Receipt: wave 9 asked the model for animation strips of
   characters that were 3D; the strips were dropped. Unsure which pipeline? Stop and ask, do not pack.
2. **Next wave number.** List the existing wave folders, take the highest plus one. A redo of the same wave
   gets a suffix (`wave10b`). Folder: `waveN-<slug>-<date>/`.
3. **No duplicates.** Grep every earlier brief for each asset name, and look in that wave's `returned/` folder.
   If it already came back, reuse it. Receipt: a wave was sent twice; the second send was pure waste.
4. **Count.** 5 to 13 images per wave, one theme. More than about 15: split into parts. The model drifts
   inside a long batch, and a wave you cannot review in one sitting does not get reviewed.
5. **Read the taste file** (section 8) and the style standard (`references/style-standard.md`). A brief
   that contradicts a recorded owner verdict is a defect before it is sent.
6. **Cost plan first** if the route is paid (section 3). Free route first.

## 2. Write the wave brief (`references/wave-brief-template.md` has the full skeleton)

One file, `WAVEN.md`, in the wave folder. What a brief needs, and why each part exists:

- **One paragraph of game context** and why this wave exists. The model has no memory of your game.
- **A rules block per asset class**: canvas size, transparency or flat background colour, safe area, palette,
  camera, no text unless you want it, "original designs only" for IP.
- **One table per part**, rows shaped exactly like this, because the return checker parses them:
  ``| `exact-name.png` | 1024x1024, transparent | what the silhouette must show |``
  The first cell is the backticked filename. The row carries the size (`WxH`) and either `transparent`/`alpha`
  or a `#RRGGBB` flat background. Mark optional files `OPTIONAL`.
- **Geometry the code depends on stated in numbers** (clear ovals, safe rectangles, where the feet sit).
- **Refs, with names burned in.** Copy reference images into `refs/`, burn each file's name into a grey strip
  (`magick in.png -gravity north -background '#777777' -splice 0x40 -font /System/Library/Fonts/Supplemental/Arial.ttf
  -fill white -pointsize 20 -annotate +0+8 'NAME' out.png`; on macOS ImageMagick failed with "unable to read font" until
  `-font` got a real file path), and tell the model to ignore the strip. Include a STYLE target and a FORMAT example that worked in an earlier wave.
  Layout-only refs from other games are labelled layout-only.
- **A checklist and a Return line**: "a zip with exactly N files named ..., plus one line per file that could not
  match". Silhouette checks work well: "squint at it next to the other silhouettes, can you name each from a
  black shadow alone?"
- Say nothing about paid tools or other models, and never ask for a real person's likeness.

Prompt wording that earned its place (`references/style-standard.md` has the full template and the negative list):
the API has no negative-prompt field, so append an `Avoid:` sentence; state the camera in degrees; state what
fills how much of the frame ("about 80%"); say the model must keep the SAME design across every pose.

**Text in images is fine.** Modern image models render lettering well. Spell the exact text verbatim in the
prompt, say "spelled exactly as written", and forbid invented names. Receipt: the first attempt invented a
byline naming a real author. Baked-in text cannot be edited, so always look at the output; a wrong word is a
regenerate. This is the one case where reviewing your own generation is mandatory.

## 3. Route, cost, pack

**Route.** Free first. In our setup the owner's image-app subscription was the default (the desktop ChatGPT app,
or the Codex CLI in a scratch git repo); an image API (OpenRouter) was the fallback, with the fallback named
out loud when used. Session observations, dated 2026-11-04/05 and therefore rot-prone: the Codex CLI route once
produced lower-quality images and hung 17 minutes (suspected: the app was not open); a later verified run made
one high-quality 1254 px PNG in about 12 minutes; driving the desktop app through computer use was blocked by an
OS accessibility permission in that session. Retest before citing any of that as a reason not to try.

**Desktop apps are sandboxed.** A macOS image app could not read the project folder under `~/Documents`
(privacy permissions). Copy the wave folder to an unprotected inbox folder (with an empty `returned/`) and point
the model there.

**API cost, measured** (gpt-image-2.5-flare through OpenRouter, medium quality, from our logs): 1:1 with one
reference $0.022, with two references $0.030; 2:3 $0.019; 16:9 $0.024; high-quality 21:9 $0.04 to $0.05;
an animation row $0.026 to $0.030. The 2D tower-defense game's whole art log: 786 calls, $28.27, against a
planned budget of about $10. The procedure that follows from that: write the cost plan into a log file first,
make ONE priced call, look at it at display size, then batch; log every call (time, file, model, quality,
aspect, cost, running total); stop and get the owner's OK past about $1. A script that caps spend and never
prints the key (it reads it from `.env`) is the only way paid calls leave the machine.

**Pack and send.**

```bash
python3 -I scripts/wave-pack.py pack <wave-dir> --prefix mygame      # default 45 MB cap
```

Prints each part and size. One zip `mygame-waveN.zip`, or `-part1.zip`, `-part2.zip` when over the cap (every
part carries the brief). The 45 MB default existed because a chat bot capped files at 50 MB; set `--limit-mb`
to your real channel. Never modify an old wave folder to make a new one: new folder, new number.

## 4. The return check, every returned zip, same turn

```bash
mkdir -p <wave-dir>/returned && unzip -n <zip> -d <wave-dir>/returned
python3 -I scripts/wave-pack.py check <wave-dir>/returned --brief <wave-dir>/WAVEN.md [--reserve-green]
# without a brief: --count 5 --size 1024x1024 [--bg BFBFBF | --alpha]
```

Per file it reports: dimensions against the brief row, real transparency (percent of fully transparent
pixels), whether the four corners agree on one flat background colour and match the brief, and, with
`--reserve-green`, stray green (for a game where green belongs to one character). Missing required files are FAIL,
missing OPTIONAL ones WARN, unexpected files WARN. It writes a labelled contact sheet (name and WxH on every
cell, 30 per sheet) and exits 1 on any FAIL. A file with an alpha channel is not a file with
transparency, so a transparent row demands at least 1% fully transparent pixels.

**Then look.** The script cannot see style. Open the contact sheet and every source at full size, next to the
STYLE ref. What the eyes caught that the numbers could not: thick dark outlines, a painted or photo look instead
of the engraving look, a hidden feature (a mask beak lost inside a hood), streak padding on strips (wave 8), a
plastic render with garbled text.

- Wrong size or a missing file: redo as `waveNb` with only the failures.
- Style miss: tell the owner BEFORE wiring anything. A style call is theirs (section 8).
- Hand-off: copy accepted files into the wave's `returned/`, never into the game's asset folder by hand. Send the
  owner the labelled contact sheet with one verdict per file (PASS / PASS WITH NOTE / REDO), and only after their
  OK hand it to the builder who wires it. Log the wave: number, parts, accepted, redo.

## 5. Ingest: names, cut-outs, anchors, packing

Return files are not game assets. A small ingest stage (the roguelite's was a Node package that reads a folder
of originals and is idempotent and cached) does the rest. What it checked, as a spec to copy:

1. **Names against a spec list.** A hard list of expected filenames (176 in the first four batches); an unknown
   name gets a "did you mean", a missing one is listed per batch.
2. **Pixels by asset kind.** Characters, props, icons and UI need real alpha: error if absent, or if under 3%
   transparent (a baked background), warn if the subject touches the border. Floors and walls must be opaque.
3. **Trim and anchor.** The feet anchor is the alpha centroid of the bottom 12% of the content, on the bottom of the
   bounding box. All poses of one character share ONE scale and one cell (hero example: idle height 288 px in a
   448x448 cell, feet at 85% of the height, anchor `[0.5, 0.85]` for every pose). Enemies, bosses and doors were
   scaled by a fixed canvas factor so the relative sizes the model drew survive (bosses 1536 to 576, enemies 768 to
   256); icons were not trimmed. Use `scripts/cutout-trim.py` for the same moves on any set.
4. **Seams on tiles.** Edge-column difference divided by the typical neighbour difference; limit 1.6; failures
   tagged mirror-tile in the manifest. Walls checked left-right only.
5. **Encode and pack.** WebP (lossless alpha, colour q86; floors q84), atlases in Phaser JSON-hash format, a
   manifest written only when its content changes, and a contact sheet per group.
6. **Hash and cache** every source; originals are read-only.

```bash
python3 -I scripts/cutout-trim.py returned/*.png --out cut/ --height 200 --cell 256x256 --anchor-y 0.85
python3 -I scripts/contact-sheet.py --out review/cut.png --cols 4 --cell 256x256 --bg checker cut/*.png
```

**Registration beats everything for strips.** The sprite-sheet test prompt said it plainly: feet on the same
baseline in every frame (y = 450 of a 512 cell), body centre at x = 256 except where the motion moves it on
purpose, and "if you cannot keep the character consistent across frames, generate them one at a time, each from
the reference plus the previous frame, then assemble the row yourself". Findings from the test: character
consistency was excellent, but the six idle poses barely differed (push each frame's motion harder), and wide rows
of four to six figures were faster and more consistent than single frames, so we slice and register them
ourselves. The ingest finds N figures by connected components on alpha at thresholds 20, 40, 80, 8, 160, merges
fragments under 12% of the biggest figure, falls back to erosion-seeded splitting and then column valleys, and
turns every fallback into a warning. For the 2D tower-defense game the same idea ran per strip: cut at the
emptiest column near each boundary, keep the biggest blob per frame, one global scale per character, feet on a
baseline; FX bleeding between frames was the main failure, and the fix was re-rolling that one clip.

**Swapping returned art over shipped art** (wave 9 swapped 42 room PNGs and 35 enemy strips): same-name swap only
after checking the canvas size AND byte-identical alpha against the file being replaced; run every check before
writing anything (never half-swapped); the swap tool snapshots unrelated outputs that an ingest would re-derive and
puts them back. And the trap: an older tool that rebuilt those files from the painted base would have silently wiped
the wave, so it now refuses to write them unless forced.

## 6. Ink-redraw post pipeline for enemies (`references/ink-redraw.md`)

For a 2D enemy set that must share one engraved look, the pipeline took the existing painted strips and had the
model redraw them in an approved style, then gated the result in numbers (silhouette IoU against the painted
frame, frame flicker ratio, zebra banding by FFT) and forced the redrawn pixels back into the painted alpha mask
so hitboxes and timing never changed. Read the reference for the gates. **Honest status: on 2026-10-23 the owner ruled
that enemies should look like the Blender-baked sketch renders and recorded a dislike of thick or washed-out
outlines on 2D model-drawn enemies; the taste file marks the 2D redrawn strips SUPERSEDED. I did not trace whether
this exact pipeline's output ever shipped, so treat it as a tested method for when the 2D route is the right one,
not as the house look.** The gates and the mask-lock idea survive; the style did not.

## 7. Measure, do not eyeball (`references/measure-and-audit.md`)

Three instruments, in the order you reach for them:

```bash
uv run --with "pillow<13" --with numpy --with scipy scripts/art-measure.py sprite.png --thresholds th.json
python3 -I scripts/calibrate-thresholds.py --good good/ --bad too-thick=bad1/ --bad too-dark=bad2/ --out th.json
python3 -I scripts/palette-audit.py shots/ --palette palette.json --strict
```

- **art-measure** rescales a sprite to a fixed calibration size before measuring, so export size cannot change the
  verdict; judges tone (median, p10, near-black share), outline (ink weight, coverage, contour luminance), edge
  feathering (ramp width in px), contact shadow, and hatch; on screenshots it masks the HUD and reports per
  64 px tile hatch and thin black ink and writes a heatmap. `--selftest` runs synthetic images that must each trip
  their own metric.
- **calibrate-thresholds** derives the limits from the owner's own good and bad examples: worst good value `g`,
  10th percentile of the bad values `b`; if they do not separate by 10% the metric is INFO; otherwise warn at
  `g + 0.5(b-g)`, fail at `g + 0.75(b-g)`. Nothing is hand-tuned. Receipt: the shipped calibration (64 good
  frames, bad frames from other looks) put near-black share at 14.3% worst-good versus 24.3% bad-p10, and ink weight
  at 1.66 px versus 2.41 px. Poses it was not fitted on (hurt, strike, windup) were judged without a refit and the
  good set still passed 64 of 64 on tone; caveat recorded with it: same model, render and directions, so that only
  catches pose overfit, and there was no independent hold-out.
- **palette-audit** counts pixels whose Lab chroma is over 12, not within delta-E 9 of the neutral ramp polyline,
  and not within the hue and chroma band of an allowed colour. Limit in the shipped run: 0.5% off palette per combat
  shot; a separate budget for warm (orange/amber) pixels, also 0.5%. A builder never raises it.

**Never lower a gate.** A builder who is failing a measured gate reports the failure with numbers; only the owner
moves the limit. Receipt: this one rule appears first in the repo's hard-rules list.

## 8. The taste file (`references/taste-file.md`)

A file the owner's words go into, which every builder and reviewer checks a proof against before showing it. Its
whole value is that it contains only recorded verdicts, each with a date and a source, and that superseded ones
are marked, not deleted. The structure is in the reference. The rules that kept it honest:

- Only the owner's recorded words. An agent's paraphrase is labelled as one. "He has not rejected it" is not
  "he said it".
- Each entry: LOVES / HATES / ALLOWS / WANTS / PRIORITY, the date, the quote, the source key.
- Outranked entries stay, marked SUPERSEDED with the date and what replaced them. The history is how you stop
  re-proposing a dead style.
- Measured limits come FROM the verdict entries (the outline limit exists because of a HATES entry), and the file
  says which script enforces it.
- Creative calls are the owner's. Bring two to four options and a recommendation, build after they pick;
  engineering, fixes and perf stay autonomous.

## 9. Show your work: labelled, at display size

- **Label every image you show** (burned-in name per cell, BEFORE/AFTER, state). Receipt: the owner could not tell
  which enemy was being discussed in an unlabelled lineup, and named the reason plainly. `scripts/contact-sheet.py`
  does it; for a one-off use `magick ... -gravity north -annotate`. Put the same names in the message text.
- Look at the proof at the size the player sees it, next to its neighbours and the owner's reference. A stranger
  should not be able to tell which asset is new.
- Check what the owner's device plays. Receipt: motion proofs went out as mp4, never gif, because he reviewed on a phone.
- Run `art-measure` on the proof before showing it, and say the numbers.

## 10. Caps must trace to a real constraint

Before a size or count cap forces a trade-off on an art choice, find where it came from. A real target
(console-class memory and fps, install size, a store's review rules) gets stated with the measured number. A
leftover self-imposed cap becomes warn-only for that target and is never brought to the owner as a cost. Receipt:
a combo animation was 0.27 MB over a 2.7 MiB cap that the code itself described as "a post-1.0 web-port
concern"; the owner's answer was that those limits were self-imposed unless they existed so it would run on the
Steam Deck. Real quality gates (face check, penetration, tests) stay gates; a builder still cannot delete one.

What the real constraints were for the roguelite after the owner moved to a Steam-first target (2026-10-21):
install size of the build under 2 GB (hard gate); 60 fps at 1280x800 in a busy fight on the weakest target
(Steam Deck); peak texture memory under 1.5 GB across a 20-room soak (measured about 830 MB); text floor 28 px;
boot to title under about 3 s. Web-port limits (file counts of 1000 and 1500 for two web portals, first-play MB,
JS gzip) were printed as warnings and never failed a build. Before any art or FX merge, say what it adds to
texture memory. And for a web build, first-load size is real: the tower-defense game wrote a `.webp` copy of every
atlas (`cwebp -q 90`, lossless alpha, skip if it saves under 15%) and pointed the manifest at it, keeping PNG masters.

## 11. Placeholder guard

A game should never wait for art. The 2D tower-defense game's asset contract: anything missing from the manifest
renders as a generated placeholder, and a shopping-list command (`bin/md assets`, 129 keys when written) shows
each art key as present or missing. The rule that makes this safe: placeholders exist only as a load-failure
fallback a normal load never shows. If a screenshot of normal play shows one, that is a bug, logged in the
current art audit. In the roguelite's standard a placeholder is: drawn in code with flat fills and a single-colour
stroke; a letter-in-a-circle or `?` disc; an OS or browser default; or painted but the wrong asset for the slot
(off-model, wrong perspective, the same icon reused for different things). Grade every audited asset 1 to 5
(5 = could be in the trailer, 1 = placeholder or wrong asset), so "art is bad" becomes a list.

## 12. VFX: three layers, colour as information (`references/vfx-and-living-ink.md`)

| Layer | Use for | How | Files added |
|---|---|---|---|
| 1. Runtime glow | pulses, flicker, shimmer, auras | engine filters and additive sprites from a pool | 0 |
| 2. Procedural arcs | lightning, chain zaps: must never repeat | a jagged polyline rebuilt every frame (midpoint displacement) plus a glow | 0 |
| 3. Baked 3D flipbooks | big rare moments readable across the room | Blender renders through the same camera as the characters, inked, ALL in one shared atlas | 1 to 2 |

Small and constant is layer 1; moves between two points and must never look the same twice is layer 2; big and
rare is layer 3. AI-generated animated VFX: no (frame drift, frames bleeding into each other); concept stills only.
Colour doctrine: in the ink-and-paper style, effects are ink and paper unless the effect belongs to a colour
owner; every colour ships in three tones (core for UI, lighter glow over dark, darker deep with an ink rim over lit
floor); colour is earned (a power turns the move its colour); each power has its own SHAPE so colour-blind players
can tell them apart. Fade glows by alpha, never through mid chroma, or the palette audit flags the halo.

## 13. Portraits, blink patches, living ink (`references/portraits-and-blinks.md`)

Portraits are painted on flat paper, cut out by border-connected background removal, cropped to the top 70% of the
figure, packed in ONE atlas, with emissive and gold masks derived from colour (hue/saturation/value rules, at half
resolution). A blink is not a new portrait: it is the changed-pixel box of an eyes-closed version, cut with the
SAME cut-out and crop, feathered, stored as a trimmed frame whose `spriteSourceSize` places it on the eyes. Ambient
motion rules ("nothing glowing is ever still"): glows pulse, gold shimmers on a 2.8 s period, portraits blink at
random 3 to 7 s for 110 ms, the advance mark bobs, mood swaps the whole pose with a 120 ms crossfade; all of it goes
static under a reduce-motion setting.

---

## Traps

Each is a rule plus the failure that earned it.

- **Asking the model for what it cannot do.** Animation strips of 3D characters were dropped (wave 9). Ask 2D-only
  things of the 2D model; send 3D sources through the 3D pipeline.
- **A brief that does not parse.** The checker reads rows whose first cell is a backticked filename and whose row
  carries `WxH` and `transparent` or `#RRGGBB`. Prose-only briefs get a "0 files expected" pass.
- **Trusting "it has an alpha channel".** The mode says nothing about the pixels. Count transparent ones: the
  return check wants at least 1% fully transparent, and the ingest errors below 3% (a baked background).
- **Flat-colour backgrounds that are not flat.** The check compares all four corners to each other (tolerance 6
  per channel) and to the brief colour (tolerance 12), and fails a flat-background file that is under 99% opaque.
- **Hidden features.** A key character feature (a beak) vanished inside a hood. Check each return against the
  canon reference at full size, not only the thumbnail sheet.
- **Streak padding on strips.** Edge frames padded with smeared pixels (wave 8). Look at every strip's first and last cell.
- **Pasted-looking props.** No contact shadow plus feathered edges reads as a floating sticker. Hard alpha, a
  contact shadow, tone matched to the neighbours; the example calibration warned at a feather ramp over about 8 px.
- **Dark pits and mush.** Pits came back at luma 0.41 when the brief wanted the darkest thing in the room; a
  darken pass (RGB times 0.5 to 0.6, alpha untouched) was applied by script and re-applied on every run, so the
  fix survives a re-ingest. Put such a fix in the pipeline, not in a hand edit.
- **A tool that regenerates from a base wipes later swaps.** See section 5; make it refuse.
- **Shared assets change in more than one place.** A swapped prop or door was also used by two later biomes. List
  where an asset is used before swapping it, and say so in the hand-off.
- **Orange pumpkin fire is not free.** The warm-pixel budget exists because legitimate orange still blows a
  monochrome style. Shoot it and run the audit; ADD blending a colour over pale paper shifts it toward yellow.
- **Colour vs shape.** Orange vs gold at full strength in one effect collapse for many viewers. One is saturated
  flame tongues, the other pale metallic glints, and each power has its own silhouette.
- **Unlabelled lineups.** See section 9.
- **Moving a gate to get green.** Never. See section 7.
- **A style standard that goes stale in place.** The first standard (painted gilt and crimson) was superseded by
  an ink-and-engraving bible, whose first lines say what it supersedes; the old standard opened with its date and
  "when this file and an older prompt doc disagree, this file wins". Put the date and the successor at the top of
  every standard so agents never mix two looks.

## Licences / cost

- Nothing here vendors third-party code or weights. `art-measure.py`, `wave-pack.py`, `cutout-trim.py`,
  `palette-audit.py`, `calibrate-thresholds.py` and `contact-sheet.py` are original to this project's authors (MIT).
- The shipped `art-measure.thresholds.example.json` is calibrated on one dark ink style: a format example, not a limit.
- Image-model terms: output rights and commercial use differ per route. Local research-licence models must not
  make assets that ship; check before the first paid or shipped asset (`game-forge:local-models`).
- Free CC0 packs used for glyphs and VFX came with a `LICENSES.md` in their folder; keep one per pack.

## Unverified or deliberately left out

- The Phaser filter-API details used by the VFX layer are in the reference only as written in the project's own
  skill, checked there against the engine's type definitions (4.2.1); not re-verified here.
- Living-ink ambient particle caps (40 drift, 24 risers, 28 dust) were "in flight" on a branch when read; treat as
  design numbers, not shipped facts.
- No game-specific canon, character names or palette tokens beyond the palette example file are reproduced.
- `ink-redraw.py` (1,000 lines, tied to one repo's git history) and the portrait packer are described, not vendored.
- The `uv run` invocation of `art-measure.py` is copied from the original and not re-run here; the scripts were smoke-tested
  with plain `python3 -I` (Pillow 12.2, numpy 2.5, scipy 1.18).
