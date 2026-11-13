# Hub / home-base scenes (painted, full colour, between runs)

The roguelite's hub went through three designs. This file keeps the method and the failures. Everything is from the hub build spec, the redo plan, the art-gen logs and the hub data file.

## 1. A hub is not a room template
- **Painted plate at 1:1, collision traced from the painting.** The hub is a 2560 x 1440 painting; walking space is ONE big walkable rectangle with solid polygons and circles laid on top for everything that is not floor, all in game px of that painting (`shapes: { walk, solids, circles }`). No tile grid. Tune with a `?debug=collision` overlay. The build spec estimated about 2 hours to retrace one front-on painting (a skewed diagonal one is slower; that is an estimate, not a measurement).
- **Several rooms in one sim world, joined by door warps.** The final layout put three 2560-wide paintings at world x = 0, 3072, 6144 with a never-on-screen solid gap of 512 between them. Walking into a door plays a short fade (0.35 s) and warps the hero to the paired door. The camera is clamped to the room the hero is in, so two paintings are never on screen together and **a seam cannot exist**.
- Why: the first hub stitched three separately generated paintings (a hall plus two wings). The judge's verdict on that design: still "stitches three paintings... the same mismatch that fails today" (AI images matched to a painted room). The winning proposal kept one coherent painting per room and used a door between them, the way the genre's reference game moves between its house rooms.
- A tile marker (`1` for the way down) still exists in the hub grid; a door slot may stand on open floor (`floorDoor`: reached by standing on its tile centre).
- Coordinate convention to pick on day one: points measured in the painting's own view, converted by one constant (K = 1.28 from a 2000-px view to 2560), world = game px + room x offset. Every later station coordinate is "a starting point: tune against the final art".

## 2. Colour versus ink
The runs use an ink-and-paper engraving look; the home base is the one place in full colour (a design ruling from the art bible: "runs are ink, the house is in colour", entering a run drains the house to ink). Consequences that bit:
- Style references differ: hub plates are "rich hand-painted digital oil look, warm candle-amber pools against cool blue moonlight, polished dark marble with red and gold carpets"; run art is graphite/ink on paper tokens.
- Any batch ink pass must skip hub art. Two coffin props returned from a run-art batch were deliberately NOT swapped because the hub is in colour and they are hub props.
- Hub art is shipped at full painting size (2560 wide webp). The source was 2560 but shipped as 1920; at camera zoom 1.4 that went soft, and playtest said the furniture looked "washed out from the image being blown up". Fix: ship the hub at 2560 and draw props at native size (or as 3D).
- The standing art bar for hub props: the hub's own camera (high 3/4, 35-40 degrees, turned to the wall or landing they stand on) and a code-drawn contact shadow. A straight front elevation in a diagonal hall is called out as a defect in the art standard; the front-on wing takes front-on props.

## 3. Painted hub backgrounds: the generation recipe that worked
1. **A free layout guide first.** Draw a flat-colour layout image with ImageMagick from the design bands (wall-foot line, hearth, bay panels, niche arches, doorway, runner), pass it as reference 1 with an existing painting as style references, and write "paint the exact layout of reference 1". Cost $0; fixed most composition drift.
2. **Scale is the usual failure.** Round 1 followed the layout but the niche openings came out 410-460 game px tall against a spec of 260-310, so the room read huge. Round 2 added a scale tail to the same prompt ("low, intimate room, niche openings about 2.5 persons high, crop tight") and landed 350-370 px. Always look at the raw PNG beside a hero sprite at the real zoom.
3. **Count props by script.** A prop asked to show "exactly seven seals" drew six, twice. Round 2 with an explicit tail ("exactly seven: one top, three each side") gave seven in a 1+2+2+2 arrangement. `scripts/measure_slots.mjs --expect 7` counts blobs of a mark colour and prints their centres as fractions of the image: that same output became the placement table (`SEAL_POINTS`, `MEMENTO_SLOTS`: 11 cushions counted regular and recorded).
4. **Frames and double frames.** A talent frame needs a transparent opening (flood-fill from the centre to alpha 0, checked). A rectangular opening around a portrait that already carries its own painted oval frame gives two frames, so the final frame has an oval opening and the portrait is cropped to the inside of its own oval.
5. **Order**: painting first (it gates collision and layout), then route props (arch, desk, cabinet), then the rest. Place each accepted asset in the game next to the hero BEFORE generating the next category.
6. **Run the generator once.** One arch was generated twice because the script also started in the background: 3 wasted calls. Log rows make this visible; the log's running total is re-read from the last row.
7. **Price the first call and read it** before batching (a $0.0237 medium 16:9 call was 1.6x the figure the plan assumed from an earlier batch). Spec price table: medium 16:9 ~$0.015-0.024, medium transparent prop $0.015-0.03, high 21:9 $0.04-0.05. Planned first tries about $0.41, ceiling with every retry about $0.74, script hard cap $2.50 inside a $5.00 job; the job finished at $0.68 including a fix pass.
8. **Fallback per asset, written before generating** (ledger prop -> none; cabinet -> shop counter art; effigy -> tilted coffin; Keeping wall -> the previous painting with frames hung over its upper band, flagged degraded).

## 4. Stations: what a hub needs
The design problem the rebuild solved: "where I access everything in the hall sucks" (the playtest verdict on the first hub). Every service became one physical object in the world with one rule set:
- At rest: no text on the floor or in the air. Only a small mark over something with news (a "!" over a person/frame/object that has a story line; a quill-sparkle emitter for a station with news).
- Within 260 px: a small name plate fades in. Within reach (120 px, nearest wins, facing breaks ties, 20 px hysteresis): rim glow plus ONE world-anchored prompt plate `[glyph] Verb · reason`, clamped on screen and kept off HUD boxes.
- Off-screen: an edge pip only when something has news. A station that is not useful yet shows nothing (sealed unlocks state their rule).
- **At least 230 px between interact points**, and an "anchor is on screen from its stand spot" test.
- Each station has a signature light colour that swells on approach (a lectern violet, a ledger warm green-gold); a gallery frame's picture light brightens when something is affordable.
- Return-loop budget is a design number: wake -> descend was 16-22 s before the rebuild and targeted ~6-9 s (estimates from geometry; "the shots harness must measure them").
- Non-modal arrival lines (barks on top of the screen) instead of blocking boxes: the old ones blocked Interact for 6.5 s each.
- Hide what is not useful yet; keep the HP bar hidden in the hub; first-visit ember motes lead along the route (render-only particles along a polyline), with a timed fallback arrow if the player has not reached the stairs in 20 s.
- Residents ("folk") are area-local, seeded per visit, never collide with the hero, stop and face within 150 px, and are drawn at the played hero's size: one function `drawHeight(hero)` serves the played hero, the folk and the mirror reflection. A "folk is smaller" bug was a measurement, not a guess: the folk's run row is 1.071 of its idle pose and its idle row 1.170, so a walking folk draws 8% small; fixed with a per-frame relative-size table and a per-clip height multiplier clamped 0.8-1.4 (run) and 0.88-1.12 (attack/cast).

## 5. The redo: a hub is the thing that gets changed after play-testing
The hall painting was redone after play-testing (a rebuild of most of the hall) while the bedchamber wing with coffins and the portrait wall stayed. Practical protections:
- Keep station logic data-driven (`STATIONS` with `area`, `anchor`, `reach`, `light`) so a repaint re-traces collision and re-measures slots without touching behaviour.
- Keep every decision in a numbered table with its source and date (the redo plan listed decisions D1 to D12 with who said what); a hub rewrite touches many systems and old assumptions resurface.
- Check what production actually ships before analysing: the plan's first finding was that the live build ran the full content, not the cut-down demo (the plan itself labels this an inference from one asset request), which explained part of the complaints.
- Painted-hall tests: a collision test walks from every hero's spawn to every stand spot; door -> warp -> arrival -> exit; and the void gap is never standable.

## Traps
- **Do not stitch separately generated paintings in one view.** Rooms joined by warps, camera clamped, gap solid.
- **Do not trust a prop's count or scale from a prompt.** Count by script, compare to the hero at the real zoom.
- **Do not trace collision before the painting is final.** The painting gates it; retrace costs hours.
- **Do not ship a 2560 painting at 1920** when the camera zooms in.
- **Do not let an ink-pass tool touch the colour hub.** Give the tool an allowlist.
