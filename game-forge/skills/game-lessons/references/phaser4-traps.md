# Phaser 4 traps and facts (4.2.1)

Everything here was checked against `node_modules/phaser/types/phaser.d.ts` AND the runtime source in
`node_modules/phaser/src/` on Phaser 4.2.1 during the roguelite build (2026-10-19 unless noted). Phaser 4 had been stable
since 4.0.0 shipped on 2026-04-10; 4.2.1 was published 2026-07-09 (both checked with npm). The tower-defense game ran Phaser 3, so nothing below is from it.
When a claim says "untested", we read it but did not run it.

## 0. Where the truth lives

1. `node_modules/phaser/types/phaser.d.ts` (signatures) and `node_modules/phaser/src/` (runtime). They can disagree
   (see "factory names").
2. The **official agent skills ship inside the npm package**: `node_modules/phaser/skills/` held 28 folders on 4.2.1:
   `actions-and-utilities animations audio-and-sound cameras curves-and-paths data-manager events-system filters-and-postfx
   game-object-components game-setup-and-config geometry-and-math graphics-and-shapes groups-and-containers
   input-keyboard-mouse-touch loading-assets particles physics-arcade physics-matter render-textures scale-and-responsive
   scenes sprites-and-images text-and-bitmaptext tilemaps time-and-timers tweens v3-to-v4-migration v4-new-features`.
   The package's repository field points at `github.com/phaserjs/phaser`.
3. Symlink them into the project so every builder and dispatched agent sees them, one folder per skill, named `phaser4-<name>`:
   ```bash
   mkdir -p .claude/skills
   for s in node_modules/phaser/skills/*/; do n=$(basename "$s"); ln -s "../../node_modules/phaser/skills/$n" ".claude/skills/phaser4-$n"; done
   ```
   (We symlinked 28 and wrote a short index skill listing which to read for which job. Skills for systems you do not use, such as
   `physics-arcade`, `physics-matter`, `tilemaps`, should say "NOT used here, do not add" in your index so an agent does not reach for them.)
4. A brief for any Phaser task should say: "read the matching `phaser4-*` skill BEFORE writing the call, then check the type."

## 1. Removed or renamed since v3 (all verified absent in 4.2.1)

| v3 habit | v4 reality |
|---|---|
| `obj.preFX` / `obj.postFX` | Filters: `obj.enableFilters()` once, then `obj.filters.internal` / `.external`. Cameras always have `cam.filters`, no enable step |
| `BitmapMask` | `addMask(textureKeyOrGameObject, invert?)` filter, or a camera viewport |
| `setPipeline` | render nodes / filters |
| `tintFill` | `setTint(c).setTintMode(Phaser.TintModes.FILL)` |
| `camera.setScissor` | a camera viewport |
| `Phaser.Geom.Point` | plain objects / `Phaser.Math.Vector2` |
| `Phaser.Math.PI2` | `Phaser.Math.TAU` (and TAU is now 2*PI; `PI_OVER_2` is PI/2) |
| `Phaser.Structs` | gone |
| `this.tweens.timeline({...})`, `Phaser.Types.Tweens.TimelineBuilderConfig` | `this.tweens.chain({...})` or `this.add.timeline([...])` |
| `sprite.playFromFrame('k', 3)` | `sprite.play({ key: 'k', startFrame: 3 })` |
| `Phaser.Sound.Events.UNLOCK` | `UNLOCKED` |
| `graphics.quadraticCurveTo()` / `bezierCurveTo()` | `Phaser.Curves.QuadraticBezier` / `CubicBezier` + `curve.draw(graphics)`, or a `Path` |
| `body.setOnWorldBounds(true)` | `body.onWorldBounds = true` |

Not an error, though it looks like one: `createGeometryMask()` still exists (Mask component) but works only in the **Canvas** renderer.
In WebGL use the Mask filter or a camera viewport. One community write-up claimed it does not exist; that was wrong.

## 2. Filters and effects

```ts
im.enableFilters();                                   // once, in create(), never per frame
const glow = im.filters!.internal.addGlow(0x8ce01e, 4, 0, 1, false, 0.1, 5); // (color, outer, inner, scale, knockout, quality, distance)
glow.outerStrength = 6;       // live-tweakable. quality and distance are FIXED at creation: recreate to change
glow.setActive(false);        // toggle without removing. filters.internal.remove(glow) destroys it
```

- WebGL only. `internal` is object space (cheaper); `external` is screen space.
- **There is no Bloom filter class.** Use `Phaser.Actions.AddEffectBloom(target, { threshold, blurRadius, blurSteps, blurQuality, blendAmount, blendMode, useInternal })`,
  or by hand `pf = filters.internal.addParallelFilters(); pf.top.addThreshold(0.5, 1); pf.top.addBlur(); pf.blend.blendMode = Phaser.BlendModes.ADD; pf.blend.amount = 0.5`.
- `Phaser.Actions.AddEffectShine(target, { radius, direction, scale, duration, repeatDelay, ease, yoyo, reveal, useExternal })` is a ready shimmer.
- Other filters: `addBlur(quality, x, y, strength, color, steps)`, `addColorMatrix()` (methods are on `.colorMatrix`, e.g. `cm.colorMatrix.sepia()`),
  `addThreshold`, `addMask`, `addWipe(width, direction, axis, reveal, texture)` plus a tween on `progress` (page turns), `addDisplacement` (tiny values like 0.005), `addVignette`,
  `addBlocky({ size: 4 })` (it takes a **config object**; a community write-up showed a bare number).
- **Each active filter is an extra render pass per object.** Twenty glowing enemies = twenty passes. Share one RenderTexture or one camera filter instead; prefer tint for hit flashes.
- **Tint modes:** MULTIPLY (default), FILL, ADD, SCREEN, OVERLAY, HARD_LIGHT, MULTIPLY_TWO (plus `setTint2` for a two-colour gradient). Shapes (`Rectangle`, `Arc`) have no tint: set `fillColor`.
- **Lighting** (`this.lights.enable().setAmbientColor(..)`, `addLight`, `addConeLight`; objects opt in with `setLighting(true)`): a lit object in a scene with no lights enabled renders **dark**. Lit and unlit objects break batches, so group them.
- **Noise and gradient objects exist** (`this.add.noise`, `noisesimplex2d`, `noisecell2d`, `this.add.gradient`).
- **Factory names are lowercase and inconsistent.** The official `v4-new-features` skill lists `noiseSimplex2D()` / `noiseCell2D()`; types AND runtime register
  `noisesimplex2d`, `noisecell2d` (and `noisesimplex3d`, `noisecell3d`, `noisecell4d`). Also `mesh2d`, `stencilreference`, `captureFrame`, `spriteGPULayer`.
  The runtime registers `customcontext` lowercase while the TYPES declare `customContext`: write `new Phaser.GameObjects.CustomContext(scene, x, y, children, cb)` plus `scene.add.existing(obj)` to stay type-safe.
  Rule: when an official skill and the code disagree, trust types plus runtime, and note the error.
- **RenderTexture / DynamicTexture drawing is queued.** Without `rt.render()` it stays empty. A pooled RT with a glow filter is how electric arcs get one halo pass instead of one per line.
- `obj.filters` is `null` until `enableFilters()`. Headless Chrome (SwiftShader) is still WebGL, so filters do run in screenshots.
- Particles: `this.add.particles(x, y, tex, cfg)` works (`explode`, `maxParticles`, `stopAfter`, `addEmitZone`, `addDeathZone`, `createGravityWell`, `startFollow`, `getAliveParticleCount`),
  but for dense combat we wrote our own pool (hand-integrated, global cap of 700 live, oldest dropped, additive particles on their own depth layer).

## 3. Silent failures that cost us time

- **No error, nothing happens:** read the browser console. A throw inside a tween `onComplete` or an event handler can kill a feature quietly. The CLI's browser harness should collect console lines and `pageerror`s and print them.
- **Listeners leak across scene restarts.** Every `scene.events.on`, `game.events.on`, `time.addEvent`, input and `scale.on` registered in `create()` needs an off/remove on `Phaser.Scenes.Events.SHUTDOWN`. Symptom: effects or sounds doubling after a restart.
- **Pools hide failures.** A hard-capped pool that never recycles stalls silently; one that drops the oldest makes effects "vanish" in big fights (the cap, not the effect). Log the free count.
- **Handlers firing on dead objects:** guard with `if (!obj.active || !obj.scene) return;` and `scene.tweens.killTweensOf(obj)` before `obj.destroy()`.
- **A hit flash can outlive its cause.** A tint-FILL flash that clears on a sim timer stays white when the sim is paused. Ours is capped at 90 ms of wall clock.
- **Dedup by string swallows repeats** (toasts, barks): dedup by (message, time window).
- **`sprite.play(newKey, true)`** only no-ops when THAT key is already playing; switching keys works (a community write-up claimed otherwise: untested claim, wrong against the source).
- **Two systems writing one value in a tick.** In the sim, route modifiers through one hook module.
- **Missing art is usually a loader phase problem.** Check, in order: key in the manifest; loaded in this phase (asking before the phase finished falls back to a placeholder or nothing); atlas frame name exactly as packed (a wrong name draws `__MISSING`);
  depth or camera (something "gone" is often under the floor layer); alpha/tint left on; `setVisible(false)` from a pool.
- **Z-order:** keep world depths as named constants in one file; screen-glued things (flashes, cards) in a screen layer with canvas coordinates, HUD in its own scene.

## 4. Performance facts, with numbers (measured in headless Chrome on a laptop, 2026-10-16, bytes exact, frame times noisy)

| Finding | Number | Fix |
|---|---|---|
| Creating a RenderTexture mid-play (a wall-fade window) caused `checkFramebufferStatus` stalls | 11 stalls of 40-100 ms in 12 s | one game-wide DynamicTexture pool in 128 px buckets, pre-filled under the title card from a survey of room templates |
| HUD called `Text.setColor` / `setFontSize` every frame, re-uploading a canvas | about 80 uploads/s; per-frame text uploads 2.3 to 0.2 | set only on change |
| Additive and normal particles alternated inside one depth band | draw calls 88 to 110 with nine gift effects | additive layer 0.25 above normal: 110 to 99 |
| First use of a shader/texture/filter | 60-97 ms each | `warmUp()` draws one near-invisible instance of each under the title card; every new filter/blend/texture used in combat gets added |
| Render-blocking third-party font | boot downloaded 826 requests / 30.5 MB | self-host (6 files, 95 kB), preload the weights |
| One 2.6 MB JS chunk | 740 kB gzip before title | Phaser as its own chunk, scenes as dynamic imports: blocking JS fell by a quarter |
| p99 frame time in a busy bot fight | 77-99 ms to 27-30 ms | the three fixes above plus a prebaked floor cache |
| JS heap over a 21-room soak | saw-tooth 50 to 190 MB, no growth trend | (no fix needed; the check is what mattered) |
| Texture bytes over the soak | 613 to 884 MB before, 435 to 828 MB after | stream one biome ahead, free two biomes behind |

- **Every frame, allocation is the GC hitch:** no `new`, array literals, closures or `filter/map` in update paths. Our app code was under 3% of the 1.3-1.6 MB per frame allocated; almost all of it was Phaser (batch handler, Graphics, `earcutLinked` for telegraph polygons).
- **Batch breaks are the draw-call tax:** about 70 program switches per frame at baseline from four FILL-tinted outline copies per actor interleaving with normal sprites. Fixing it changes the look, so it was recorded, not done.
- **Texture compression is not free:** images were already lossy WebP; re-encoding is generation loss for a few percent. GPU memory needs KTX2/Basis plus loader work (not done).
- **Headless numbers:** SwiftShader on a shared box. Use paired before/after runs of the SAME command, read p99 and "frames over 33 ms", never quote a headless fps as the game's.

## 5. UI traps that bit

- A fixed 1920x1080 canvas under `Scale.FIT` makes screen-size constants correct; advice against them targets resizable canvases.
- Pointer `topOnly` (default true) sends a click to the top interactive object only: an invisible full-screen zone above buttons swallows every click. Give it a low depth or remove it while a panel is open.
- Rebuild panel CONTENT in place on tab switch or purchase; closing and reopening the whole panel flickers.
- DOM modal clicks leaked into the Phaser canvas in the tower-defense game (a sign-in dialog muted the game; fixed at an integration pass, the exact fix is not recorded in our notes). Suggestion, untested: stop propagation at the DOM layer and test the first click after closing.
- A music-volume tween threw a `pageerror` at an integration pass (cause not recorded in our notes). General rule from the debugging notes: kill tweens with the object, and read `pageerror`s in every browser-driven check.

## 6. Community plugin review (so you can skip it)

We graded all 26 skills, 5 agents, 10 commands and 2 hooks of a public community plugin (`Yakoub-ai/phaser4-gamedev`, commit `1c1bf45`, reviewed 2026-10-19) against 4.2.1.
No LICENSE file in the repo, so we kept the ideas and vendored nothing. Net of the 26 skills: 9 kept in rewritten form, 17 dropped as duplicates of the official skills or irrelevant to a mature codebase.
Its best idea, adopted: triage feedback into defect, tuning, design, unactionable before touching code (see `references/agent-workflow.md`). Its API-check hook never fired:
it read `file_path` at the top level of the hook JSON while Claude Code nests it under `tool_input`, and stdout on exit 0 would not have reached the model anyway (tested 2026-10-19).

API errors found in it (13): twelve wrong API names (the rows in section 1 that cover `playFromFrame`, `tweens.timeline`, `addBlocky(amount)`, `createGeometryMask` "does not exist",
`Math.PI2`, `Sound.Events.UNLOCK`, Graphics `quadraticCurveTo`, `setOnWorldBounds`, plus Matter `setRestitution` (use `setBounce`), `Loader.FileTypes.AtlasJSONFile.JSON_ARRAY`, `Phaser.Math.MoveTowards`, and bare `Math.TAU`/`Math.PI_OVER_2`
which must be `Phaser.Math.*`); the 13th is a set of unverified claims stated as fact (`play(newKey, true)` no-op, "scene CREATE fires before plugins are attached", a `setScissor` instruction).
Lesson: an agent skill written from memory of v3 needs the same grep-the-types audit as any other code. One error was also found in an OFFICIAL skill (the noise factory case, above).
