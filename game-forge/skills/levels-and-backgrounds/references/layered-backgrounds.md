# Layered room backgrounds (roguelite, 3/4 top-down, Phaser)

The tile grid is only the gameplay layer. A room is drawn as a stack of separate pieces, each from its own art file, so an irregular island of floor can float over a painted world instead of a rectangle sitting on a flat colour. Everything below is from the render code headers, the art kit spec and the art logs.

## 1. The layer stack

| Layer | What | Depth / parallax (as shipped) |
|---|---|---|
| L0 backdrop | one 2560 x 1440 painting of what lies beyond the floor, camera-locked | parallax 0.3, depth -200004 |
| L1 haze | two tileable fog sheets (2048 x 512) + a few dust motes | fog parallax 0.55 / 0.75, depth -200003 / -200002; motes at depth 54500 |
| L2 cliffs and hanging pieces | masonry strips hung under every south-facing floor edge; "below the floor" pieces (stumps, chains, roots) | baked into the floor texture (it reaches 192 px left/right and 288 px below the room box) |
| L3 floor | baked ONE canvas texture per room: contour of the floor silhouette, rim stones on the lip, painted floor chunks stamped with jitter, bridges | depth -200000 |
| L4 decals | bones, rubble, wax, stains, puddles | depth -150000 (decals), shadows -100000 |
| L5 depth-sorted objects | walls, pillars, low walls, doors, landmarks, props, actors | y-sorted: depth = the tile's bottom edge (feet y for actors) |
| L6 foreground | 3-8 near-black painted silhouettes (chains, lanterns, arch fragments, banners) at parallax 1.12-1.2 | depth 56000; fade to 35% alpha when the hero or a telegraph is behind them |
| L7 screen | god-ray sheets, a very light colour grade | depth 56200 / 56300 |

Rules the stack taught:
- **Backdrop, fog and foreground are dark and low contrast**, never a bright focal point in the middle third of the backdrop. The art brief states it as "they are layers, not scenery": gameplay readability beats painting quality. Cliffs are lit at the top lip and fade to near black (and to transparent) at the bottom.
- **Procedural stand-ins are only a bridge.** The render code builds a procedural plate until `env-<biome>-backdrop` lands; real art "wins automatically" by key. Later the procedural near-black foreground stand-ins were deleted once painted art existed (flat arcs and bars looked like placeholders).
- **Parallax values are separate data per layer**, not one global; fg moving faster than the floor (1.12-1.2) is what sells depth.
- **Floor baking is staged** (a generator that yields between steps) and costs real time: baking the darkened backdrop took ~85 ms the first time (QA measurement), so it is pre-warmed under the hub-to-run fade.

## 2. The floor silhouette (why rooms stop looking like boxes)
`Terrain` (pure, no Phaser): classify each tile (void / ground / pit / diagonal) from the template chars and the sim cells; build a 16 px sub-sampled coverage field, blur it twice, add seeded edge noise; run marching squares with directed loops, Chaikin-smooth the contour; hang cliff strips under south-facing edges; stamp floor chunks with jitter instead of one tiled pattern. A short lip under every edge gives the slab thickness ("a floor with depth, not a sticker").

## 3. The painted kit per biome (one source of truth)
One JS module (`env-spec`) feeds three consumers: the prompt document for the image model, the API generator, and the ingest spec. Per biome it lists: `backdrop` (2560x1440 opaque), `fog` x2 (2048x512, tileable in x), `cliff` x2 (512x256, tileable in x), `rim` (512x48), `floor-chunk` x3 (512x384), `bridge-h` (256x192) and `bridge-v` (192x256, tileable in y), `below` x2, `fg` x3 (512x1024 / 768x768 / 1024x640), `edge` x3 (256x256 rim props), `decal` x4, `island` x2 (768x512), `landmark` (512x640). Plus shared `godrays` and `motes`, and the flooded biome adds a tileable `water` and `shore` strip.

Prompt discipline that held across four biomes:
- One shared STYLE string + a per-biome block (`look`, `backdrop`, `fog`, `cliff[]`, ...). The biome block names materials and palette, never characters.
- Every call attaches the biome's existing floor, wall and prop art as references (`refs`), and the generation log records which.
- Camera words by layer: floors and floor decals "straight down", walls/cliffs/rims "front elevation strips tiling left-right", props/doors "3/4 about 35 degrees, verticals stay vertical".
- **Fog, rays, motes and shore are generated opaque on black and converted to alpha** in post (no model gives clean soft alpha for smoke).
- Tileable pieces must wrap: left edge continues into right (top into bottom for vertical bridges; all four edges for water).
- Calls are sequential, price-logged, hard-capped: `CAP` in the script (kit job $10.00, floor clutter $0.75, one hub job $2.50 script cap inside a $5.00 job). A call is refused when `total + ESTIMATE` would pass the cap. Medium quality was the default; one real measurement: high costs ~2.6x medium.
- `--repost` re-runs the post-processing from the saved raw output with no API call, so a trim/feather bug costs nothing.

## 4. Floor clutter: painted pieces, no procedural fallback
Painted bones (5 variants), rubble (3), wax (2) in `floorfx/`, per-biome multiply tint, stains and puddles as soft procedural blotches (no glyph). Receipts:
- **Never keep a procedural stand-in for clutter.** A manifest rebuild once dropped the painted keys and a flat beige skull glyph came back into every room. Now a slot with no painted texture places nothing.
- **A floor reference leaks.** Passing the floor as a style reference made the model draw a cobble slab under the object, so the generator has `--noref` for the redo.
- **Feather after trim**: the post step trims alpha, then multiplies alpha by a smoothstep of elliptical distance (full inside 0.78 of the radius, zero at the rim) so any halo dissolves into the floor.
- Prompt specifics that mattered: aged bone about #b9a98a ("NOT white, NOT bright"), "a soft dark contact shadow beneath so the pile sits INTO the stone floor", "low value range, nothing bright or white".
- Contact shadows are code: `addFoot` / `addAlphaFoot` under every prop, with per-art base fractions.
- Proof tool: `r8-floor-shots` teleports the hero beside each distinct decal kind and screenshots it (optional debris burst).

## 5. Occlusion: walls fade where they cover an actor
Playtest feedback: "when the character goes behind a wall, make that wall transparent." Implementation (`Occlusion.ts`): every wall tile, masonry cluster, pillar, low wall and landmark registers its art rect and draw depth. An actor is covered exactly when the engine would draw the occluder over it (occluder depth > actor feet y, and the actor's box overlaps the rect). The cut is a soft elliptical **window**, not a faded rectangle: the occluder swaps to a pooled RenderTexture and a shared radial-gradient brush is ERASED around each covered actor (35% left at the core, feather 56 px, eases in over ~120 ms: time constant 40 ms). The brush is world-anchored so neighbouring tiles line up into one hole. Foreground silhouettes use a plain 35% fade.
- Test it with `r8-occlusion-shots`: it finds a wall run, a single wall, a pillar and a low wall that has floor directly north of it, parks the hero 30 px above the block, and screenshots each (and an enemy beside the hero).
- A real bug class (QA round 4): a SIDE wall (floor east or west of it) sorted by its bottom edge painted over every sprite leaning into that column, so actors against a side wall were cut off. Fix: sort side walls at the top of their own image. A tile's pieces register with the fader as ONE occluder.

## 6. Light and depth
- **Backdrop depth ramp.** Playtest said the off-floor background read too bright and flat. Fix at texture-bake time: a horizontal multiply ramp in PLATE space (so it follows the parallax): recessed chambers x0.68, the two big skull towers x1.0 (closer to the viewer, lighter, contrast), a 3% ramp between. Tune in one constant object.
- **Candle glow points.** The backdrop has 41 painted candles (41 points in the baked list); each gets an additive warm blob with a two-sine flicker, and "flames keep their painted brightness" by pasting the untouched painting back through a 16 px soft disc at each flame after the multiply. The points are HAND-PLACED from 1:1 crops (`scripts/glow_points.py`): automatic detection was tried twice and rejected (luminance blobs pick skulls and ribs; snapping to the brightest blob drifted 10-30 px).
- **Vignette vs ink pool.** The soft vignette (radial gradient plus stacked inner-edge strokes along the whole contour) is skipped in the engraving-style biome. There the lit arena is a clipped ellipse of lit floor over the shadow floor, sized so its area is 70% of the walkable area with the walkable bbox aspect, closed by ONE thin broken graphite line (1.5 px, 55% alpha, dashed). History: hatching rings laid across the lit paper were removed after feedback that large hatched areas "look messy"; hatch belongs on individual stones in the floor art.
- **Lights as data**: `dress.lights[{x,y,kind: torch|candle|brazier|moon}]`; additive blend except in the paper-ink biome, where lights use normal blend (additive glow breaks a paper look).
- Biome tint tables: a `TINT` per biome for fog, grade, rays, motes; `FLOOR_FX_TINT` multiplies shared clutter art into each biome's palette.

## 7. One distinct centrepiece per room
Playtest taste rulings: the room felt busy ("all the little pillars and similar details look messy"), and each room should have ONE thing to remember. The data:
- The template reserves a `T` block (the landmark footprint). `compose.centre` names which set piece it draws (a key into a table of centrepieces; absent = the default bier). Unknown keys fall back to the default, so a typo never crashes a room.
- `compose.clutter: 0.3` keeps 30% of random decals; `compose.breakables: 1`; four covers frame the centrepiece; two stacked urn clusters (`urnClusters`) replace scattered single urns.
- Centrepieces and props can be baked 3D renders (`prop3d`): several variants per slot, the pick is hashed from position so a cluster walks the variants in order and never repeats a bake, height jittered +-7% stable per seed. See `game-forge:sprite-pipeline-3d` for the bake.
- Proof sheet: `centres-shots` screenshots every room's overview (fixed seed, paused, 1280x800) and `centres-sheet.py` burns room name + centrepiece id into each cell of a labelled 4x4 grid, plus a turnaround sheet of the baked centrepieces on paper. Never commit the outputs.

## 8. Tiling and seams
- Floors (1024x1024) and walls (1024x512) must tile; ingest downsizes to 512 and checks **edge-column difference / typical neighbour difference** (limit 1.6; `scripts/heal_seam.mjs` is that metric plus the two heals). Failing floors were tagged `tile: "mirror"` in the manifest (the renderer presumably mirrors alternate tiles to hide the seam: inferred from the tag, not read); walls are checked left-right only.
- **Receipts**: three walls failed at ratio ~2.2. A free edge mirror-average heal took them to 0.03 and dropped the mirror tag; the alternative was a $0.12 regeneration. A second heal (offset blend, 80 px band) exists for busy art where mirroring smears detail.
- Re-check the seam after any recolour pass (inference: a per-image tone map can reintroduce an edge difference; the shipped floors were tone-mapped in place once).
- Painted pieces that are not tiles (decals, chunks) get the elliptical feather instead, so they never have an edge to match.

## 9. Swapping art without breaking the pipeline (receipts)
- A later ink-pass stage rebuilt shipped env files from the painted base, which would silently wipe a newer swap. The fix: the stage refuses to write props/env unless `--force-undo-<wave>` is passed. Any batch tool that regenerates from a base needs a refusal like that once something newer exists.
- Art ingest for a swap checks canvas size and **byte-identical alpha** against the file being replaced before writing anything, and writes only after every check passes (never half swapped). A full ingest would have changed ~150 unrelated files because shipped art was no longer a pure function of the sources.
- Pits came back from the model lighter than the backdrop (luma ~0.41 vs 0.44 while the brief said pits are the darkest), so the swap tool multiplies pit pieces x0.5 and x0.6 on every run (alpha untouched). Say so in the tool, and keep the multiplier in a table.
- Shared art changes in every biome that reuses it (props, hazards and doors were shared); list the sharers before approving a swap.
