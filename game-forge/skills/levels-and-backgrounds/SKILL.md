---
name: levels-and-backgrounds
description: >
  Build game levels and their art as data plus measured checks: roguelite room templates as ASCII
  (legend, door slots, spawns, kinds, biome plans, wave budgets, mirroring, validation), room drafts as
  Python builders, layered backgrounds (backdrop, haze, cliffs, painted floor, decals, depth-sorted props,
  one centrepiece per room, foreground silhouettes, candle-glow points, occlusion fade, vignette or ink
  pool), hub / home-base scenes painted in full colour with traced collision and measured slots, seams
  and tiling, and tower-defense levels (paths, build pads, painter guide render, wave DSL, bot-tuned
  difficulty). Use for "design the rooms", "room template format", "layered background", "why does my
  room look like a box", "make the wall transparent when I walk behind it", "place candle glows",
  "heal a tiling seam", "measure prop slots", "lay out a tower-defense level", "write waves for a level".
  Triggers: "level design", "room templates", "biome backgrounds", "hub scene", "build pads", "wave design".
---

# Levels and backgrounds

**The one-line case:** a level is data a script can lint, and a background is a stack of layers a script can measure. In two real builds (a Phaser 4 roguelite and a Phaser 3 tower-defense game) every level problem that cost time was a number nobody had computed: a spawn rule that cut room clears about 15% in the bot sweep, a prop that was supposed to show seven seals and showed six, a wall seam at ratio 2.2, a painting that went soft because it shipped at 1920 and the camera zoomed in. Judgment (what the room should feel like) stays with you; anything expressed as a number gets measured.

This skill is method only. Numbers and file names come from those two games and are labelled as theirs. Sibling skills: `game-forge:art-waves` (batch art production and the ink-redraw pass), `game-forge:sprite-pipeline-3d` (baked 3D props and centrepieces), `game-forge:game-qa-loop` (bots, headless screenshots, perf), `game-forge:game-lessons` (architecture and agent workflow). For modelling a real object from photos use `design-forge:photo-to-3d-loop`; for the visual-deliverable decision tree use `design-forge:art-department`.

## What is in the box

| Path | What |
|---|---|
| `references/room-templates.md` | roguelite room format v1 and v2, legend, rules, validation, drafting, special room systems |
| `references/layered-backgrounds.md` | the layer stack, the painted kit per biome, clutter, occlusion, light and depth, centrepieces, seams, swapping art safely |
| `references/hub-scenes.md` | home-base scenes: painted plate + traced collision, door warps, colour vs ink, generation recipe, stations |
| `references/tower-defense-levels.md` | paths, pads, painter handoff, wave DSL, knobs, bot-tuned balance, regions |
| `scripts/roomdraft.py` | ASCII room builder (rect, ellipse, polygon, blobs, scatter, doors, entry), report, `check` and `mirror` CLI. Stdlib only |
| `scripts/example_draft.py` | runnable 30 x 19 example that writes a draft `.txt` |
| `scripts/preview_rooms.py` | contact sheet of draft rooms, name burned in (Pillow) |
| `scripts/heal_seam.mjs` | seam metric + two heals (edge mirror-average, offset blend) for tiling floors and walls (needs `npm i sharp`) |
| `scripts/measure_slots.mjs` | count and locate coloured marks on a generated prop, as image fractions; `--expect N` gate (needs sharp) |
| `scripts/glow_points.py` | 1:1 crops with coordinate ticks, then bake hand-placed light points to TS/JSON + verification overlay (Pillow) |
| `scripts/td_level.py` | tower-defense `check` (pad/road distances, spacing, path ends, waves) and `guide` (painter's trace PNG) |
| `scripts/wave_dsl.py` | one-line-per-wave DSL parser with a K scale and per-path table |

Smoke-tested for this skill: `py_compile` on every Python file; `example_draft.py` -> `roomdraft.py check` / `mirror` -> `preview_rooms.py`; `heal_seam.mjs` (measure, mirror, offset) and `measure_slots.mjs --expect` (pass and fail exit codes) on synthetic images; `glow_points.py` bake and crops on a synthetic plate; `td_level.py` check and guide on a real level exported to JSON; `wave_dsl.py` on a two-line file. Not run: any engine, browser, or paid image call.

---

## Workflow A: rooms for a roguelite

1. **Pick the room kinds and the biome plan first, as data.** Kinds: combat, elite, miniboss, boss, shop, rest, vestibule, stair, trial, treasure, hub. A biome plan is `rooms: 10, plan: { mini: [5,6,7], vestibule: 9, boss: 10 }` plus a budget per room index. Decide the mirror policy now: combat rooms mirror, boss/shop/story/painted-plate rooms set `mirror: false`.
2. **Fix the legend and rules in one doc** before drawing anything (see `references/room-templates.md`): one `E` on the bottom edge, doors as numbered slots that stay wall until the run assigns rewards, 6-10 spawns each >= 4 tiles from `E`, all spawns inside one screen (24 x 13 tiles at the default zoom), walkable share 40-65%, every floor tile reachable from `E`.
3. **Use void, diagonals and bridges from the first room.** A closed rectangle reads as a box; void edges let the painted background show and give knockback a use (an enemy knocked into a wall or void edge takes a slam).
4. **Draft rooms as code, not by hand.**
   ```bash
   python3 scripts/example_draft.py drafts          # writes drafts/demo_hall.txt and prints the report
   python3 scripts/roomdraft.py check drafts/*.txt  # size, walkable %, spawns + bbox, urns, door reach, stray floor; exit 1 on errors
   python3 scripts/preview_rooms.py drafts sheet.png # look at the sheet before reading ASCII
   python3 scripts/roomdraft.py mirror drafts/demo_hall.txt
   ```
   Draft files (`@ key: value` header + rows) are the source; convert them to your engine's data file with a small script and never hand-edit the generated file.
5. **Validate in CI with an engine command** (`validate`): the error/warning list is in `references/room-templates.md` section 4. Add one test that mirrors one room per archetype and one that walks from `E` to every door.
6. **Place props and breakables by rule**, not coordinates (distance from entry, doors, spawns, urns; 6 of 8 open neighbours). Give each room ONE centrepiece (a `T` footprint plus a `compose.centre` key); keep random clutter to ~30% and cluster urns.
7. **Size fights with a budget, not a list.** Draw 2-3 enemy types from the biome pool by weight and spend the budget randomly (cheapest-first is a bug). Next wave when alive cost <= 25% of the wave's budget or after 20 s.
8. **Turn a new spawn or encounter rule on per biome behind a kill switch**, and measure it with bots first. A switched-off biome must draw nothing from the RNG so seeds do not reshuffle.

## Workflow B: a layered background for one biome

1. **List the layers** (`references/layered-backgrounds.md` section 1): L0 backdrop (parallax 0.3), L1 two fog sheets (0.55 / 0.75) + motes, L2 cliffs and hanging pieces under floor edges, L3 baked floor with rim and chunks, L4 decals, L5 depth-sorted props and walls (depth = bottom edge), L6 foreground silhouettes (parallax 1.12-1.2, fade to 35% when something is behind), L7 god rays.
2. **Write the kit list once** as one module that feeds the prompt doc, the generator and the ingest spec: backdrop 2560x1440, fog 2048x512, cliff 512x256, rim 512x48, floor chunks 512x384, bridges, below/hanging pieces, 3 fg silhouettes, 3 edge props, 4 decals, 2 islands, 1 landmark per biome. Shared STYLE string + per-biome block; attach the biome's existing floor/wall/prop art as references on every call.
3. **Generate, then check the numbers** (value rules: backdrop, fog, foreground dark and low contrast; cliffs lit at the top lip fading to black; no bright focal point in the backdrop's middle third). Hard caps and one log row per call; sequential calls; `--repost` to re-run post-processing with no spend.
4. **Seams**: tiling floors and walls must wrap. Measure, then heal for free before regenerating:
   ```bash
   npm i sharp
   node scripts/heal_seam.mjs wall.png --measure                  # before { x: 2.2 }
   node scripts/heal_seam.mjs wall.png --out wall.healed.png      # mirror-average heal (x: 0.03 on our walls)
   node scripts/heal_seam.mjs floor.png --mode offset --band 80 --axes xy --out floor.healed.png
   ```
5. **Light points** (candles, torches): hand-place from 1:1 crops, bake, verify with the overlay. Do not auto-detect.
   ```bash
   python3 scripts/glow_points.py crops backdrop.png crops/ --size 640
   python3 scripts/glow_points.py bake backdrop.png points.json src/data/glow.ts --overlay overlay.png
   ```
   In the engine: one additive blob per point, scaled with the plate, two-sine flicker; paste the untouched painting back through a small soft disc at each flame after any darkening ramp.
6. **Occlusion**: register every wall, pillar, low wall and landmark with its art rect and draw depth; where an occluder would be drawn over an actor, erase a soft elliptical window (35% core, 56 px feather, ~120 ms ease) instead of fading the whole rectangle. Foreground silhouettes just fade to 35%.
7. **Depth and light**: bake a horizontal multiply ramp into the backdrop texture (recessed 0.68, nearer columns 1.0), skip the soft vignette in a paper-ink biome and use a clipped lit ellipse (70% of the walkable area) closed by one thin broken line.
8. **Prove it with screenshots**: a fixed-seed, paused overview per room (a labelled contact sheet with the centrepiece id burned in) and targeted shots (hero parked 30 px behind a wall / pillar / low wall; hero beside each decal kind). See `game-forge:game-qa-loop`.

## Workflow C: a hub / home-base scene

1. Paint one plate per room (2560x1440), ship it at full size, and join rooms with door warps, the camera clamped to the current room, a solid gap between paintings (`references/hub-scenes.md`). Never stitch separately generated paintings in one view.
2. Trace collision from the final painting (one walkable rectangle minus solid polygons and circles; a debug overlay to tune). Write a test that walks from every spawn to every stand spot and proves the gap is not standable.
3. Generate with a free layout guide drawn in ImageMagick as reference 1, then look at the raw PNG next to a hero sprite at the real zoom (scale is the usual failure).
4. Make each service one physical object with a measured slot table (`measure_slots.mjs --expect N`), at least 230 px between interact points, one prompt plate at a time, nothing floating at rest.
5. The hub is the one place in colour if your runs are ink: keep ink tools off it with an allowlist.

## Workflow D: a tower-defense level

1. Write the level as data (map, paths with control points, pads, castle, hero start, waves) and a design doc with a layout sketch, pad table, HUD keep-clear zones and mood.
2. `python3 scripts/td_level.py check level.json` before anything else (unreachable or overlapping pads, close pads, path ends, wave counts), and read its per-pad "road length in range" column.
3. `python3 scripts/td_level.py guide level.json guide.png --scale 0.5` and hand that to the painter; paint at 2x (3840x2160) with a pad centred on every build spot; leave HUD zones quiet.
4. Write waves with the DSL (`scripts/wave_dsl.py waves.txt --paths main,side --K 1.5`), one line per wave, one new mechanic per level introduced on a callout wave, a boss at the end that is never scaled.
5. Set targets before tuning (win rates per bot tier, a hero dying at least once in most runs from level 3), then bisect K (counts) and H (HP ramp x1 -> xH by 70% of the level) against the bots. See `references/tower-defense-levels.md`.

---

## Traps (rule + the failure that earned it)

- **A closed rectangle reads as a box.** The first room format was walled rectangles; the second added void, diagonals and bridges so a painted world shows through. Start with v2 ideas.
- **A spawn rule that needs the camera needs rooms that fit one screen.** Applying the "spawn inside the view" rule to old rooms cut room clears ~15% in the bot sweep (the design doc's wording), so it waited for rooms authored for it.
- **Never hand-edit generated room data.** Drafts (`.txt` from Python builders) are the source; the engine file is generated. Mirrored copies are generated too, and a mirror must flip every x in the metadata (dress, camera, hazards) or a landmark ends up over a wall.
- **Do not trust a count or a scale from a prompt.** A prop asked for seven seals drew six twice; niche openings came back 410-460 px against a 260-310 spec. Count with `measure_slots.mjs`, view the raw PNG next to a hero sprite at the real zoom, then fix the prompt with an explicit tail.
- **A floor reference leaks into clutter.** Painted bone/rubble/wax generated with the floor as a style reference drew a cobble slab under the object. Redo with no reference and feather the alpha rim (full inside 0.78 of the radius, zero at the rim).
- **No procedural stand-in for clutter.** A manifest rebuild dropped the painted keys and a flat beige glyph came back into every room. When the painted texture is missing, place nothing.
- **Seams before regeneration.** Three walls failed the tile gate at ratio ~2.2. The free edge heal brought them to 0.03; the regeneration it replaced was budgeted at about $0.12.
- **A pipeline stage that rebuilds from a base will wipe newer swaps.** The ink-pass script now refuses to write props/env unless given an explicit undo flag. Every swap tool also compares canvas size and byte-identical alpha to the file being replaced and writes only after all checks pass. A full ingest would have changed ~150 unrelated files.
- **Hand-place light points.** Automatic candle detection was tried twice and rejected: luminance blobs picked skulls and ribs; snapping seeds to the brightest blob drifted 10-30 px.
- **Do not ship a 2560 painting at 1920 when the camera zooms to 1.4.** It went soft and furniture looked washed out. Ship at the painting's size and draw props at native size.
- **Frames and double frames.** A rectangular frame around a portrait that already had its own oval frame made two frames. Match the opening to the art, flood-fill the opening to alpha 0, and check it.
- **Side walls sort at the top of their image.** Sorting by bottom edge painted a side wall over every sprite leaning into that column.
- **Vignette and hatching are style decisions.** In an ink biome, the soft vignette and hatch rings across lit paper read as messy and were removed; hatch belongs on individual stones.
- **One centrepiece per room.** A busy layout with many small pillars drew the same complaint twice; one memorable set piece, 30% of the random clutter, clustered urns.
- **Do not tune waves by playing.** Targets per bot tier first, then bisection on K or H. Bosses are never scaled.
- **A pad on the road or out of range is a bug the check finds**, not a player. Pads in our hairpin level were all designed at exactly 100 px from the smoothed road.
- **Put region mechanics in the level's data** (`regions`), so sim, UI preview and bots all see them.
- **Run a generator once.** One art script ran twice (also started in the background) and wasted three calls; the log makes it visible.

## Licences and cost

- Scripts here are original to the two games' tooling (MIT, like the plugin). `sharp` (Apache-2.0) and Pillow (HPND) are installed by you, not vendored.
- The image model used for art was `gpt-image-2.5-flare` via OpenRouter at medium quality: medium 16:9 about $0.015-0.024 per call, medium transparent props $0.015-0.03, high about 2.6x medium. Real totals: one hub job $0.68 of a $5.00 cap (script cap $2.50), the environment kit under a $10.00 cap, floor clutter under $0.75. Price the first call and read it before batching; prices drift between batches (one came out 1.6x the prior batch's figure).
- Check the licence of any image model before its output ships in a game.
- Original designs only in prompts: "nothing from [any studio]" was a hard line in every art brief.
