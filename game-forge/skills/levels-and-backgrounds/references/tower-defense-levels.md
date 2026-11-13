# Tower-defense levels: paths, build pads, waves, painted maps

From a Phaser tower-defense game (genre bar: Kingdom Rush: fixed build spots, roads, click-to-move hero, 3 stars per level). Read from its GDD, level design docs, level data files, validator, balance tools and asset contract. Numbers are that game's.

## 1. A level is data, drawn from a design doc
The data (`LevelDef`): `id`, `name`, `map { width: 1920, height: 1080, background, theme }`, `startGold`, `lives`, `waveGap`, `earlyCallBonusPerSec` (gold per second left when the player calls a wave early), `paths[]`, `buildSpots[]`, `waves[]`, `heroSpawn`, `castle`, optional `allowedTowers`, `music`, `night { dawnAfter }`, `regions[]`, `fullMoon`, `nightmareOf`. World space is the 1920 x 1080 map, origin top-left, y down, and **every coordinate (paths, pads, castle, hero) uses it**.

Each level also has a design doc with the same sections, written for the painter and the balancer:
1. Layout sketch in ASCII (road `.`, second path `:`, pads `o`, castle `C`, hero `S`, special pads `x`).
2. Paths: control points per path (`[x, y]` lists), lanes (3), lane width (16 px). The on-screen road is the Catmull-Rom curve through the control points (uniform, 10 samples per segment), about 70 px wide at 1x. Control points are the source of truth.
3. Build pads table: id, x, y, which path each pad covers.
4. Castle and hero spawn.
5. HUD keep-clear zones (no important art there): top-left 640 x 60, top-right 260 x 90, bottom-left 420 x 160.
6. Mood and palette; landmarks to keep clear of road and pads; the level's new enemy mechanic.

## 2. Paths and pads (what made levels readable)
- **Shared stretches**: a second path that merges into the first must share every control point from the join to the castle. The painter paints one road with two feeders, not three roads.
- **Pads sit off the road**: in the hairpin level every one of the 12 pads is exactly 100 px from the smoothed road (measured with `scripts/td_level.py check`, so it is a designed offset, not an accident). Tier-1 towers reach ~150 px, so a pad at 100 covers a chunk of road. The check also prints road length within range per pad and per path, which tells you at a glance which pads are strong (a pad near a join covers both roads: 285 + 295 px) and which are weak (159 px).
- **Mixed-lane pressure**: waves put groups on different paths at once (`main` and `side` groups in the same wave) so a defence that covers one road fails. From level 3 on, waves are 1.5-2x bigger than the early levels.
- **Validator rules** (engine-side, lifted into `td_level.py`): error when a pad is farther than the longest tower range from every road ("unreachable build spot"); warn above 160 px; warn under 40 px (overlaps the road); warn when two pads are closer than 70 px; warn when a path ends > 120 px from the castle; error on a missing path id in a wave group; warn when a campaign level has fewer than 12 or more than 20 waves.
- **Special pads and regions**: later levels add region mechanics as data, `regions: [{ type, params }]`: a blizzard every 50 s for 10 s from 30 s (params `rangeMult 0.75` and `slow 0.25`; read as tower range and enemy speed, inferred from the names), `icePads: 's5@8,s8@11,s10@14'` (those pads break after waves 8, 11, 14), shifting dune routes (each wave uses one or two of three routes; the engine exposes `activePaths` and a `nextPaths` preview), sandstorms that cut tower sight and blind the mob. Lesson: put the mechanic in data the level file declares, and make the UI preview it (next paths) so it is a fair puzzle.
- **Dawn timer**: each level has a night clock; dawn breaks `dawnAfter` seconds (80) after the final wave spawns and weakens night-tagged units, so the player is pushed to finish. A full-moon flag strengthens 'lunar' units and lengthens curses.

## 3. The painted map handoff
Asset contract rules that kept art and code in sync:
- Deliver the map at 3840 x 2160 (2x), JPG or WebP q85, registered under `level.map.background`.
- **A guide render is the contract**: the engine renders the exact road, pads, castle and hero start (`render --level <id> --t 0 --out guide.png`) and the painter traces it. `scripts/td_level.py guide` draws the same thing from a JSON export (road polyline, pad circles, castle box, hero dot, HUD keep-clear in red) with no engine.
- Paint a pad centred on every build spot. When a painted map exists the placeholder pad outline is hidden (only shown on hover), so a missing painted pad shows up immediately.
- Towers stand bottom-centre on the pad: the tower's anchor point (default [0.5, 0.92]) is placed at (spot.x, spot.y + 22), the front base line on the painted pad.
- Camera is a 3/4 view: Blender orthographic camera, rotation X = 55, Z = 0, key light top-left, candle-amber rim. Palette: night blues, candle amber, blood crimson, moonlight silver.
- Missing art never blocks: anything not in the manifest renders as a generated placeholder; a shopping-list command lists live status (129 keys at the time).
- Mood notes per level change the read of the same road: retaining walls and torchlit markers at switchbacks, night blue darkening toward the castle, castle silhouette growing across the late levels.
- **Leave room near the castle end** for boss effects; the doc says so in the painter note.

## 4. Waves
### The wave DSL
Waves as object literals buried the design. One helper turned each wave into one line (`scripts/wave_dsl.py` is a Python port of the grammar):
`"!exorcist villager 10 .6; exorcist 2 1.5 @4 >lower; BOSS captain @10"`
- group = `enemy count interval [@delay] [>path | >all] [xHP]`; `>all` puts a copy on every path (count per path); `!enemy` flags the callout banner for a new enemy's first appearance; `BOSS id` spawns one unscaled boss.
- One knob `K` scales every group count, minimum 1; per-enemy `COUNT_CAP` stops fast or wall-breaking units from growing unfairly in bulk (hounds 12, villagers 36, lancers 8, cavalry 5, catapults and wagons 3).
- A second knob `H`: HP ramps linearly from x1 on wave 1 to xH by 70% of the level, flat after; bosses are never scaled. Early waves stay learnable and the back half gets the weight.
- Every level has 12-20 waves, a boss on every level (a region finale is bigger), a "call wave early" button that pays bonus gold. A callout wave introduces each new enemy so the player gets a warning, not an ambush.
- A level introduces ONE new mechanic through an enemy (a priest-type elite that disables the nearest tower for 4 s every 8 s, introduced on wave 3) and pays it off in a boss wave with phases (charge every 6 s, calls a squad at 66% HP up to three times).

### Balancing waves with bots, not feel
- Bots: `novice` (first-time player), `greedy` (value per gold, never moves the hero), `frontline` (greedy economy, heroes parked at the front: how most humans play), `hero` (the smart bot: kill-zone hero, intercepts, ultimates). See `game-forge:game-qa-loop`.
- Targets written before tuning (round 4, Normal): frontline hero dies at least once in most runs from level 3 on; novice ~60% win on levels 1-3 and under 35% on 7-9; smart bot wins nearly always and 3-stars 50-60%; Veteran hard (frontline < 50%); Nightmare ~30% for the smart bot.
- `tune <level> <target>` bisects the K (or H) multiplier on a scaled copy of the content until a chosen bot metric hits the target (6 bisection steps, 40 runs each by default), prints the multiplier to fold into the level's K. `report` runs every level x bot x N seeds in parallel (one worker per CPU) and writes a markdown table with win rate, stars, hero deaths, killer wave and top leakers per enemy; it lists "Misses" against the targets. Example from the 2026-09-28 report: smart bot 3-star rate averaged 69% against a 50-60% target, flagged as a miss, along with two Nightmare levels.
- Re-run the report after any tower, hero or enemy change; levels share numbers.
- **Nightmare** per level is real level data (`<id>_nightmare`, `nightmareOf`): same map and paths, remixed waves (bigger groups, faster spawns, promoted enemy types, extra late groups, less starting gold), tuned per level to ~30% smart-bot wins. A stat-multiplier stand-in stacked on top would have made it unwinnable, so launch the real level instead.
- A `stress` level exists and is excluded from the 12-20 wave check (inferred: a performance fixture, not play).

## 5. Campaign shape
Campaign 1: nine levels (eight plus a final boss level), each a distinct place with its own road logic (two paths, a bridge, a hairpin climb, gates). Hero slots 1 at the start, 2 from level 4, 3 from level 8. Campaign 2: 3 regions x 4 levels, each region with a mechanic (ice cracking under pads, shifting dune routes, train line as a second path). Region mechanic parameters live in the level file; the UI previews them.

## Traps
- **Do not tune a level by playing it.** Targets first, then bots, then K/H.
- **Never scale bosses with K or H.** Their phases are the design.
- **Do not paint before the road is frozen.** The guide render is generated from the same control points the engine uses; repainting for a moved control point is the cost.
- **A pad that sits on the road or beyond the longest range is a bug**, caught by the check, not by a player.
- **Do not describe a region mechanic only in the level doc.** Put it in the level's `regions` data so the sim, the UI preview and the bots all see it.
