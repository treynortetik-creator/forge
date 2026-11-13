# VFX doctrine and engine notes

Doctrine from a short research note on effects for a 2D engine game (owner-approved 2026-10-19), with the
engine details from the project's own skill, stated there as checked against the Phaser 4.2.1 type definitions. I did
not re-run those checks; treat API names as "as written in the source skill".

## The three layers
| Layer | Use for | How | Files added |
|---|---|---|---|
| 1. Runtime glow | pulses, flicker, shimmer, auras | engine filters (glow, bloom via parallel filters), additive sprites from our particle pool, tweens | 0 |
| 2. Procedural arcs | electricity, lightning between two points, chain zaps | a jagged polyline rebuilt every frame (midpoint displacement) drawn with Graphics into one small pooled RenderTexture that carries a glow filter: a white-hot 1 px core over a 2 px coloured body; never repeats | 0 |
| 3. Baked 3D VFX | boss attacks, signature casts, death moments, reward beam bursts | Blender (meshes or geometry nodes, emission) rendered to flipbooks through the SAME orthographic camera as the 3D characters, R/G/B channels = three different effects, then inked and packed into ONE shared VFX atlas (two at most) | 1 to 2 |

Decision rule: small and constant is layer 1; moves between two points and must never look the same twice is layer 2;
big, rare and readable across the room is layer 3. AI-generated animated VFX: no (frame drift, frames bleeding into each
other); concept stills only. One Blender process at a time on a shared machine.

## Colour: what an effect may look like (restricted-palette style)
- In the restricted style, effects are ink and paper unless the effect belongs to a colour owner (a hero, a power).
- Every colour has three tones: core (icons, UI), a lighter glow (over dark), a darker deep with an ink rim (over a lit floor).
- Enemy projectiles: paper-hot core with an ink rim, never a colour. Enemy telegraphs: ink hatch fill with a hard ink
  border (shape, not colour). Hero base attacks before any power: bold ink strokes. Colour is EARNED: a power turns the move its colour,
  and recolours go through one function (`tint(verb, base)`), never a hard-coded palette in an effect.
- Flames and lamps in runs are white paper, not orange. Light is the absence of ink.
- Hard pairs: orange vs gold never both at full strength in one effect (orange = saturated flame tongues, gold = pale
  metallic glints); every power has its own SHAPE so it survives colour blindness.
- Palette-audit implications are in `measure-and-audit.md`: fade glows by alpha, budget warm pixels, ADD over paper shifts yellow.

## Phaser 4.2.1 effects, as written in the source skill
- **Filters** are WebGL only. A game object needs `obj.enableFilters()` once (in create, not per frame), then
  `obj.filters.internal` (object space, cheaper) or `.external` (screen space). Cameras always have `cam.filters`.
  `addGlow(color, outerStrength, innerStrength, scale, knockout, quality, distance)`: outer strength is live-tweakable;
  quality and distance are fixed at creation. `setActive(false)` toggles; `filters.internal.remove(f)` destroys.
- There is no Bloom filter class: `Phaser.Actions.AddEffectBloom(target, cfg)` or by hand `addParallelFilters()` with a
  threshold plus blur on `.top` and an ADD blend on `.blend`.
- Others named in the source: `addBlur`, `addColorMatrix` (methods live on `.colorMatrix`), `addThreshold`, `addMask`,
  `addWipe` (tween `progress` for a page turn), `addDisplacement` (tiny values like 0.005), `addVignette`,
  `addBlocky` (takes a config object, not a number), `addShadow`, `addGradientMap`, `addQuantize`, `addKey`.
- **Not in v4:** `preFX`, `postFX`, `BitmapMask`, `setPipeline`, `tintFill`, `camera.setScissor`. `createGeometryMask()`
  exists but works only in the Canvas renderer; in WebGL use `addMask` or a camera viewport.
- **Tint:** `setTint(c).setTintMode(Phaser.TintModes.FILL)` is a hit flash with no filter (cap the flash at 90 ms of
  wall clock so a paused sim never leaves a white silhouette). Shapes have no tint: set `fillColor`.
- **RenderTexture / DynamicTexture:** draw calls are queued; call `rt.render()` after drawing or nothing appears.
- **Noise factories are lowercase** in the types (`add.noisesimplex2d`, ...); the official skill's camelCase was wrong.
- **Particles:** the engine emitter exists, but combat effects used a hand-written pool (global cap 700, oldest dropped,
  ADD particles on one depth layer so they batch). Use an engine emitter only for a self-contained effect, always with a
  max particle count and one emitter re-exploded, never one per hit.

## Budgets and comfort
- Each active filter is an extra render pass per object: twenty glowing enemies is twenty passes. Share one RT or one
  camera filter; prefer tint over filter for flashes.
- **Warm-up:** each first use of a shader, tint mode or filter cost 60 to 97 ms in a fight. Draw one near-invisible
  instance of each under the title card so shaders link before the first fight, and add any new filter, blend or
  texture used in combat to that warm-up list.
- Effect timing comes from sim ticks and sim events, never wall clock, except cosmetic loops, so a replay or a render
  command stays repeatable and hit-stop freezes effects.
- Headless fps (software rendering) is a RELATIVE signal: compare to the previous run on the same machine; never quote it as the game's fps.
- Reduced motion: loops and drifts stop or go static; flashes obey a flashes setting, shake a shake setting.
  Information-carrying effects (telegraphs, hit confirms) stay, without motion.
- Runtime textures cost zero shipped files; baked VFX go into the one shared atlas.

## Proof
Type-check and run the tests; shoot combat frames and look at them at 1x; run the palette audit with `--strict` and read
the heatmaps; compare before and after fps from the same command; check the build's size and file-count report.

*Pointer:* the ambient-motion table and portrait blink format live in `portraits-and-blinks.md`.
