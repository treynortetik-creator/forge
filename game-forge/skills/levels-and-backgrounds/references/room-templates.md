# Room templates as data (roguelite)

Everything here was read from the roguelite's room design docs and data files. Numbers are that game's; adapt them, keep the structure.

## 1. The template is ASCII plus a metadata block

One file or object per room: a tile grid (1 char = 1 tile = 64 px) and metadata (id, biome, kind, tags, hazard config, weight, minDepth, mirror flag, camera).

| Rule (v1, first design) | Value |
|---|---|
| Combat room size | 16-26 wide x 14-24 tall tiles |
| Small rooms (shop, rest, trial) | 12-16 x 10-12; stair 12 x 12; vestibule 16 x 10 |
| Hero entry | always bottom edge, centre (`E`); exits are door slots `1 2 3` on the top edge or the upper third of side walls; unused slots render as wall |
| Mirroring | every combat template may flip left-right (50% via the room RNG stream); doors, spawns, hazards and camera hints mirror with it |
| Walkable floor | >= 60% of interior; every floor tile reachable from `E` without dashing (dash-only shortcuts over pits are allowed) |
| Spawn points | 6-10 `S` tiles, each >= 4 tiles from `E`; the spawner skips any `S` within 260 px of the hero |
| Breakables | 3-5 urn tiles per combat room |
| Selection | weighted pick from the biome's templates, never the same template twice in a row, not one used in the last 3 rooms |
| Tags | `water`, `tall`, `open`, `tight` (tight = no big enemies) |

Legend v1: `#` wall, `.` floor, `O` pillar, `L` low wall (blocks movement, not projectiles), `P` pit (blocks walking, dash and flyers pass; 8 damage and respawn on the last safe tile if a dash ends on it), `w` shallow water (x0.8 speed), `W` deep water (blocks walking, 0 fall damage), hazard chars, `S` spawn, `U` urn, `E` entry, `1 2 3` door slots (wall until the run assigns a reward).

### Room kinds in the schema
`combat | elite | boss | rest | shop | hub | treasure | miniboss | vestibule | stair | trial`. A biome plan is data: `rooms: 10, plan: { mini: [5,6,7], vestibule: 9, boss: 10 }` (a 9-room biome shifts to mini [4,5,6], vestibule 8, boss 9), plus a per-room wave `budgets` array and a `budget: { base, perDepth }` fallback. Elite rooms are the same templates at x1.5 budget with every enemy elite.

### Wave budgets (how a room's fight is sized)
A combat room picks 2-3 enemy types from the biome pool by weight, then spends the budget drawing randomly by weight until nothing affordable remains. Cheapest-first fill is explicitly forbidden in the design doc. The next wave spawns when alive enemies' cost is <= 25% of the current wave's budget or 20 s after the wave began. Max alive at once 10/11/12/14 by biome. Clear-time sanity check in the design doc: wave HP / (hero DPS x 1.4 multi-target x ~50% uptime), about 22 s for room 5 of biome 1 and 50 s in biome 4.

## 2. Room kinds beyond combat
- **Rest**: 12 x 10, a fountain that heals 30% once, a loadout swap stand, 3 urns, 2 doors.
- **Shop**: 12 x 10 with 4 slots; the pre-boss vestibule counter has 3 slots. Prices scale x1.0/1.1/1.2/1.3 by biome, rounded to 5.
- **Stair** (after a boss): boss drop on a plinth, a choice of 2 plinths, one door down.
- **Trial** (a cracked picture on a wall in ~12% of rooms, max 1 per biome): a one-wave room at budget x1.2 with exactly one elite, different palette.
- **Mini-boss and boss arenas**: authored as gimmick geometry (v2 special rooms, one per mini-boss, 8 in total) and `mirror: false`.
- **Shop/rest/boss/story/painted-plate rooms set `mirror: false`.** A mirrored painted plate would flip its own art.

## 3. v2 format: why v1 was not enough, and what v2 added

v1 produced walled rectangles, which read as boxes. The v2 design goal (quoted from the render code's header) was "a place floating in a world, not a box". A template opts in with `v: 2` and old templates keep working unchanged.

New in v2 (legend extras): ` ` void (invisible edge; blocks walkers, dash, pounce, knockback; flyers and projectiles pass; nobody falls), `:` variant floor zone, `/ \` diagonal edges (half floor, half wall or void, smooth 45-degree edge), `=` bridge/causeway, `o` breakable cover (a solid prop, 3 hits, rubble on break damages nearby enemies), `T` landmark footprint (connected `T` tiles become one set piece), `n` feature pad, `R` reward point (max 1; the drop lands 110 px from the hero toward `R`), `v k z` optional trap slots (spikes, plates, falling points) that a seeded roll turns on at room entry (`slots.traps: roll | all | fixed | none`).

Other v2 fields: `archetype` (13 named shapes: broken hall, ring pit, twin islands, archipelago, diagonal gallery, crescent, terraces, hourglass, long approach, L bend, cloister, apse, field), `size` (small/medium/large/field; sets default zoom and the depth window the template may appear at), `entry` side (S, SW, SE, W, E; sets the walk-in direction and mirrors), `camera { zoom, introFrom, weights, clamp }`, `dress { landmarks, fg, lights }` render-only overrides, `compose { clutter, breakables, urnClusters, centre }`. Canvas up to 60 x 40.

### v2 rules worth copying
- **Doors go on any floor-to-outside edge**; the door's side comes from which neighbour is floor. Floor on more than one side is a warning: frame doors with wall or void.
- **Spawns sit inside one screen**: all `S` within a 24 x 13 tile box (the default zoom shows 25 x 14 tiles). The reason (inferred from the fallback chain in the doc): the "spawn donut" rule puts enemies 300-900 px from the hero and inside the view (inset 48 px), which only works if every `S` can be on screen.
- **Spawn donut waited for v2 rooms.** Applied to v1 rooms it "cut v1 clears by ~15% in the bot sweep" (the doc's wording; read as fewer clears), so v1 kept the older rule (any `S` >= 300 px away). Measure a spawn rule against bots before turning it on globally.
- **Void and slams**: an enemy whose knockback (>= 300 px/s) is cut short by a wall, pillar, landmark, cover, door or void edge takes `clamp(10% max HP, 10, 30)` damage (bosses 10), once per 30 ticks, and the knockback cancels. Edges become a weapon, which is why a void edge is not just scenery.
- **Zoom table**: boss 1.02, mini-boss 1.10, shop/rest/vestibule/stair/trial/treasure 1.30, small 1.25, medium/large 1.20 (1.12 in the later biomes), field 1.05. View = (1920/zoom) x (1080/zoom) world px, centred on the hero and clamped to the room box + 128 px.
- **Camera hints are data**: `introFrom` tile for a vista pan, `weights` to lean toward points of interest, `clamp` rect.

## 4. Validation (a `validate` CLI command; run it in CI)
Errors: unknown chars; v2 chars in a v1 template; canvas > 60 x 40; not exactly one `E`; no door; a door with no floor neighbour backed by wall/void/canvas edge; ambiguous diagonal; more than one `R`; a door, `E` or spawn unreachable on foot from `E` (dash-only gaps over `P`/`W` are allowed, never over void); spawn box > 24 x 13 (combat/elite). Warnings: a door with floor on 2+ sides; walkable share outside 40-65% of the canvas; a v2 combat room with no `R`; wrong-way diagonal; spawn count outside 6-10; spawn within 4 tiles of `E`.

`scripts/roomdraft.py check` is a small stand-alone version of the reachability, share, spawn-box and door checks for drafts, so a draft is judged before it reaches the engine.

## 5. Drafting rooms as code
Hand-aligning 22 x 16 character rows is where mistakes live. The roguelite's pipeline: a Python builder per biome (`cat.py`, `crypt.py`, `cath.py`, `cit.py`, `spec.py` for specials) draws shapes into a canvas (rect, ellipse, polygon, thick line, wobbling `blob` islands, `shore`, `shoals`, `bridge`), scatters spawns/urns with a farthest-point rule, runs a report, and `emit`s `<biome>/<id>.txt` (`@ key: value` header + rows). A small converter (`tots.py`) turns those into the TypeScript data file. Rules that came out of it:
- Draft files are the source; the TS file is generated. Never hand-edit the generated file.
- `scatter(n, 'S')` farthest-point placement keeps spawns off ragged edges and beyond a minimum distance from `E`; urns only go next to something solid.
- `finish()` thickens the north wall by one row so doors sit in 3-wide recesses, with optional alcoves for dressing niches. Coordinates below row 0 shift down by one, so run it last.
- Water rooms: islands via `blob`, causeways via `bridge`, then `frays` (dry tiles touching deep water thin into shallows on a fixed pattern) and `shoals`, so the shoreline is organic but deterministic.
- A contact-sheet preview (`scripts/preview_rooms.py`) colours every tile and burns the room name above it. Look at the sheet before reading any ASCII.
- Mirrored copies are generated (`id~m`), never authored. The mirror swaps `/` with `\`, `<` with `>`, flips `entry` (SW<->SE, W<->E), and mirrors every x coordinate in `dress`, `compose.urnClusters`, `camera` and hazard rects. Miss one and a mirrored room has a landmark floating over a wall.

Counts shipped: 16 + 14 + 14 + 14 combat templates for four biomes (each also served mirrored unless flagged `mirror: false`), v2 specials (shop, rest, vestibule per biome plus 8 mini-boss arenas).

## 6. Props and breakables are placed by rule, not by hand
Placed at room entry from a seeded stream, 2-4 per combat room (or `compose.breakables`): 2-3 tiles in from the outer wall, never within 4 tiles of the entry, 3 of a door, 2 of a spawn, 1.6 of an urn, and each needs 6 of 8 open neighbours, so no corridor is ever sealed. Bots and enemies path around prop tiles. Breakable defs carry `hp` (1 for vases and bone piles, 2 for lights and banners, 3 for statues and coffins), collider `r` (hero radius 22: a one-tile gap must stay passable), a `low` flag (the hero's dash passes through low props; statues and coffins stay solid), debris colours, and a small silver drop (chance, min..max). Urns can be stacked into clusters of 4-5 so one swing breaks several; playtest feedback asked for exactly that.

## 7. Special room systems that sat on top of templates (each behind a per-biome kill switch)
- **Field rooms** (one per biome, takes a room slot): a large open map with three sealed cages, each a separate fight with its own budget share (field total = room budget x 2.4, split 30/30/40 by open order), a few sleeping roamers, free pickups, doors open only when every cage is won and every reward collected.
- **Hub biome** (courtyard with N wing doors): each wing is 1-2 rooms and returns to the yard; "wards" count down so the mini-boss wing can never be skipped.
- **Locked side exits**: a spare door slot becomes a locked reward behind a reward-free one-wave fight.
- **Encounter variety**: race, survival, seal, trial specials with a `GAP` so two never run back to back, per-biome max, and every switch off draws nothing from the RNG (so turning one off never reshuffles a seed).
Each had a state block in the run state, a sim module, a render overlay, a bot navigator and tests. Design lesson: add special rooms as *flagged variants of generated rooms* (a door flag, a field block on a template), not as new room kinds the flow code must learn.

## Traps
- **Never make a room a closed rectangle by default.** v1 rooms read as boxes; add void, diagonals and bridges or the painted background cannot show through.
- **Do not count tiles by eye.** The authoring report prints walkable share, spawn bbox, urn count and door reach; a draft with `stray-floor` unreachable tiles is a draft with a bug.
- **A mirrored room is a different room for every coordinate in the metadata.** Test the mirror of one template per archetype.
- **Spawn rules that depend on the camera need the room to fit one screen**, or the fallback chain (inside view >= 300 px, any `S` >= 300 px, any `S`) is what actually runs.
