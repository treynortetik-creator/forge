# Camera, scale and directions

All numbers are from the pilot spec we wrote for a 1920x1080 Phaser game with 64 px tiles; the spec was
checked against the repo at the time. Re-derive them for your canvas, but keep the method.

## Measure the game camera first

- 1 world px = 1 screen px at zoom 1. Zoom range 1.15-1.4 plus a "closer camera" option of +0.12, so max 1.52.
- Display height: hero ~111 world px, enemy ~92, so on screen 128-169 px for a hero.
- We found our existing painted figures were 448 px cells downscaled 2-3x at runtime: wasted bytes. 3D bakes
  should be rendered at the size they display, with super-sampling doing the quality work.
- View angle: measured from a vase ellipse (14/34) and pillar caps (~0.42) in a screenshot, ~25 degrees. Old
  animation metadata said 35. Floors were painted near top-down and props oblique, so characters must match the props.
- The spec proposed 30 degrees; `render.py` defaults to 25 and every build script we shipped used 25. Pick from
  25/30/35 by rendering the stand-in beside real props in a real screenshot, not by argument.

## Camera and light (all static; only the model turns)

- Orthographic, camera rotation X = 90 - elev, looking +Y, +X = screen east, +Y = screen north, feet at origin.
- `ortho_scale = cell_w / (64 x scale)` (2.5 units for a 256 cell at scale 1.6). `shift_y = 0.35 x cell_h / cell_w` so
  the origin lands at y = 0.85 of the cell (the anchor). Gate G0 proves it with a 0.5-unit cube.
- Scale: heroes 1.6 render px per world px (176 px figure in a 256 cell); enemies and bosses 1.35 (124 px). Wide
  clips (a special, a mounted boss) get a per-clip larger cell (384x256).
- Do not compute model height; FIT it: render S idle frame 0, scale the armature until the alpha box = target
  height (`bake_sprites.py` does 3 iterations, caches `fit.json`, invalidates on elev/fit-height/cell/scale change).
- Render 2x or more and down-sample; EEVEE (`BLENDER_EEVEE`, the only valid EEVEE key in Blender 5.x), 1-2 TAA
  samples for toon, transparent film, view transform Standard, 8-bit RGBA PNG. No cast shadows (the game draws its own).
- Light for toon: warm key from screen upper-left (about 50 degrees up), cool fill ~0.35, thin warm rim upper right.
  Hatch look: white key only, tiny fill, black world.

## Directions and yaw

- 8 directions named e, ne, n, nw, w, sw, s, se (screen angle 0, 45, ... 315). Heroes: all 8 rendered. Enemies
  and bosses: the spec rendered 5 (E, NE, N, S, SE) and mirrored W/NW/SW, budget-neutral.
- Mirroring swaps the weapon hand mid-combo and any asymmetric feature; at 176 px we judged all 8 affordable for heroes.
- Yaw rule. The sim moves isotropically on screen but the camera foreshortens the ground, so the spec derived
  `w = atan2(sin s / sin elev, cos s)` for screen angle s (63.4 degrees for NE at elev 30). The renderer supports
  `plain` (true 45-degree steps), `corrected` (that formula) and `blend` (halfway). The build scripts we shipped
  never passed `--yaw`, so they used plain 45 steps; the spec said to flag it and switch if diagonals read back-on at the turn test.
- glTF faces -Y (screen S). `--facing x` for a rig that rests facing +X, `--facing y` for +Y. Rig and mesh can disagree
  by an arbitrary angle: use `--yaw-offset`.

## Runtime direction pick (so the bake is used correctly)

Source: aim vector in an action, dash direction in a dash, else facing (sim y is down, so screen angle = -angle).
- Attack/cast/dash start: snap to the nearest sector.
- Otherwise hysteresis: keep the sector while within 22.5 + 10 degrees of its centre; hold a new sector at least 5
  ticks (60 Hz) before switching.
- Turns of 135 degrees or more pass through the middle sector for 2 ticks.
- Tick-driven, never wall-clock, so the deterministic headless render stays repeatable.
- Fallback chain: own direction -> `mirrorOf` (flipX) -> nearest loaded direction -> old art -> static pose. Mixed
  rosters (some characters 3D, some painted) must keep working.

## Per-character consistency (what the gates enforce)

- `--pivot sockets`: turn about the midpoint of the two foot bones.
- `--dir-fit`: equalise standing height across directions (up to ~6% otherwise).
- `centerBone`: re-centre root-motion clips on their own mean.
- Sockets (`hand_l`, `hand_r`, `head`, `weapon_tip`, `foot_*`) are projected to 2D per frame into `meta.json`, so the
  engine can attach projectiles, trails and sparks to a baked body.
