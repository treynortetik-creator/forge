# Performance and size: budgets, measuring, reading the numbers

Sources: the roguelite's perf skill, its round-8 perf report, its `measure.ts` and `fps-run.ts` tools, and the
tower-defense game's CLI doc. Measure first, fix the worst measured thing, and never lower a budget to pass.

## Budgets are a decision someone owns

Write each budget as: number, where it is measured, hard gate or warning. In the roguelite the numbers started as
web limits (first play under 20 MB, 1,000 files for one store, 1,500 for another, entry JS under 260 KB gzip) and
were later demoted to **warnings** by the owner when the target became a desktop/handheld store build. The code
kept the old numbers and added a `--strict-web` flag to make them fail again. Rules that came out of it:

- A builder never raises a budget, loosens an audit threshold, skips a test or deletes a failing assertion to
  get green. Report the failure with numbers; the owner moves a gate.
- When the target changes, add a second target; do not edit the first one's numbers.
- Do not trade quality for a limit nobody ships against (no lean-engine builds or atlas passes just to save file counts).

Example budget table (roguelite, handheld-first; the 60 fps line is INFO because headless is not that GPU):

| Gate | Target | Kind |
|---|---|---|
| frame rate, busy fight, 1280x800 | 60 fps; p50 / p99 / frames over 16.7 ms printed | INFO (real check = real device) |
| texture memory | peak under 1.5 GB over a 20-room soak (about 830 MB measured) | HARD, exit 1 |
| text size floor | 28 px, looked at in 1280x800 shots | visual |
| boot to title from disk | under about 3 s (a local server gives an upper bound) | INFO |
| install size | under 2 GB | HARD |
| first play download / title download / total JS gzip | 20 MB / 4 MB / 900 KB | WARN (web port) |

Say what any art or FX batch adds to texture memory before merging it. Texture bytes are `w * h * 4` per unique source.

## Measuring

| Question | Tool (roguelite names; both games had equivalents) |
|---|---|
| frame p50/p95/p99/worst, frames over 16.7/20/33 ms, update vs render ms, JS garbage per frame, draw calls | `measure.ts --mode fight` against a BUILT dist served by the real server (gzip + cache headers) |
| cold load: bytes, requests, ms to title / hub / first room, split by kind (js, images, audio) | `measure.ts --mode flow` (cache disabled through CDP, third-party requests aborted) |
| memory over a long run: JS heap and texture bytes per room | `measure.ts --mode soak --rooms 20` (bot at 6x sim speed; `--js-flags=--expose-gc` and `--enable-precise-memory-info`, `gc()` before reading the heap) |
| which frames are long, and which sim events were inside them | a long-frames tool: record `{ms, tick, phase, room}` for each frame over 33 ms |
| update vs render split + draw count | a render-cost tool |
| real first-play bytes in a browser | a load-budget tool with a `--max-mb` gate |
| static size / file count / JS gzip per chunk | `budget:check`, reads `dist/`, needs no browser |
| quick fps | `scripts/perf-sample.mjs` (this skill) or the game's own `npm run fps` |

Extras worth copying from `measure.ts`: `--deck` (device viewport plus the device gates), `--throttle N` (Chrome CPU
throttling through CDP; relative numbers only, the GPU is not throttled), CDP `Performance.getMetrics` for main-thread
busy time per frame (robust where a CPU profile's idle share is not), and wrapping GL calls (`createFramebuffer`,
`texImage2D`, `drawElements`...) to count calls and find which room each big texture upload lands in.
The tower-defense harness has `--verify 1`: it hashes sim state around every frame and flags any mutation, proving
render never writes sim state.

`measure.ts` also guards the machine: it waits while another automation Chrome is running or load is above 12,
never kills anything, and closes only its own browser. Its Chrome check matches only a real automation process
(`pgrep -f 'MacOS/Google Chrome .*--remote-debugging'`, via `execFile` so no shell is involved); a bare
`pgrep -f remote-debugging` also matched every agent shell whose command text mentioned it and deadlocked the box.

## Reading headless numbers

- **Bytes and request counts are exact. Frame times are noisy.** The round-8 write-up says the box was shared, the
  harness capped near 48 fps, and a loaded run read 25-35 fps. Compare p99 and "frames over 33 ms" between two
  runs of the SAME command on the same machine, paired back to back.
- Never quote a headless fps as the game's fps. Print the GPU string (`WEBGL_debug_renderer_info`,
  `UNMASKED_RENDERER_WEBGL`) with every run: the round-8 report says it measured on a real Metal GPU, while the later
  skill text says headless Chrome runs through SwiftShader and is far slower. Which backend you got is part of the result.
- At 60 Hz a count of frames over 16.7 ms is mostly vsync jitter (a trivial 2D page read 52 of 120 in this skill's
  smoke test). Use "over 33 ms" and p99.
- Check `uptime` first. Another process's Chrome or Blender skews everything.
- Abort third-party requests in every run. Before round 8, a render-blocking web-font stylesheet decided results and
  the game would not boot without the network.
- In-page code must be a STRING in `page.evaluate`: a TypeScript runner (tsx/esbuild) injects `__name()` helpers into a
  function literal and the page throws.

## Case study: round 8 (all from the round-8 report; local server, one machine)

| | Before | After |
|---|---|---|
| time to title card | 2,667 ms | 544 ms |
| requests / bytes before the title card | 826 / 30.5 MB | 60 / 1.8 MB |
| p99 frame time, busy bot fight | 77-99 ms | 27-30 ms |
| frames over 33 ms per 12 s | 9-19 | 2-4 |
| texture memory at title / first room | 572 / 699 MB | 333 / 611 MB |
| JS update per frame p50 | 1.2-1.4 ms | 0.7-0.8 ms |
| text-canvas uploads per frame | 2.3 | 0.2 |

What did it:

1. Three loading phases (title / hub / per-biome streaming one biome ahead, freed two behind).
2. The 2.6 MB JS chunk split into the engine, a boot chunk and lazy scene chunks.
3. Self-hosting the font.
4. A GL call timer exposed 11 `checkFramebufferStatus` stalls of 40-100 ms in 12 s, caused by creating a render
   texture the first time each wall piece was covered, so a texture pool is pre-filled under the title card. The same
   pass found the HUD calling `setColor` / `setFontSize` every frame, about 80 canvas re-uploads per second; now only on change.
5. Floor bakes stepped a few ms at a time behind menus, with the next room predicted by the sim's own pick (state
   restored, hash unchanged).
6. Cache headers `max-age=900` for art, audio and fonts instead of `no-cache`.

Soak over 21 rooms at 6x: JS heap saw-toothed 50 -> 190 MB with no growth trend; texture bytes 435 -> 828 MB as the
next biome streamed in.
Honest negative from the same report: a nine-item build read 42.7 / 41.3 fps vs 44.1 with none, "within about 5%", and
the 45 fps target was "not demonstrable in this harness" because the no-item baseline itself read 44-49.

## Where frames go (ordered by what actually cost us)

1. Batch breaks: alternating additive and normal blend in one depth band, mixing lit and unlit objects, many
   interleaved textures, every active filter. Nine items once cost 88 -> 110 draws per frame; putting additive
   particles a fraction above the normal ones in the band gave 99.
2. First use of a shader or texture: a 60-100 ms hitch. Warm it under the title card.
3. Text canvas uploads: update text only when the value changes.
4. Per-frame allocation: no `new`, array literals, closures or `filter/map` in update paths.
5. Room builds and bakes: do not add synchronous work to room entry; a cold build was 93-140 ms, 43 ms with the
   floor prebaked.
6. Leaks over a run: listeners and timers registered in `create()` without removal on shutdown, tweens left on
   destroyed objects, textures of biomes already left.
7. Sim cost was small (0.134 ms/tick with no items, 0.140 with nine). Profile before blaming the sim.
