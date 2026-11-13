# Tower-defense lessons (the monster tower-defense game)

TypeScript + Phaser 3 + Vite, started 2026-09-27 16:55, public link live the same night, then, by the end of the next day, 21 levels in two campaigns, 8 heroes and 6 tower families.
Genre leader and bar: Kingdom Rush. Numbers below are dated; re-run the harness before trusting them for your game. Balance numbers are from the 2026-09-28 round-4 snapshot.

## 1. The grammar we copied

- Fixed build spots on roads; towers have 3 tiers, then a choice between 2 specialisations at tier 3 to 4, then 2 skills per specialisation with 3 ranks each, bought with gold.
- **Barracks-style blockers with a rally point**, a click-to-move hero with auto-cast abilities and a manual ultimate, 20 lives, 3 stars per level (1 = win, 2 = at most 5 lives lost, 3 = no life lost), a "call wave early" button that pays bonus gold, sell refund 60% of everything spent.
- Leak cost 1 life; a tanky brute costs 2; bosses more.
- Heroes: XP persists across the campaign; death respawn timer (15 s, raised to 25 s after the owner found the hero too safe); slots 1 at the start, 2 from level 4, 3 from level 8, each extra deployed hero costs starting gold (about 60) so it is a real choice.
- Meta: stars buy permanent upgrades; a harder remix ("Nightmare") unlocks per level after 3 stars; an endless mode with a local leaderboard; a daily challenge seeded from the UTC date; a codex; about 30 achievements; a share-GIF of the last ~8 s; hotkeys for everything in battle; touch and tablet support.
- Saves: local by default; portable save codes (copy/paste, no account); an optional name-and-password account that backs up to a tiny Node server (only `pg`).

## 2. Engine contract (what made agents productive)

- **Fixed 30 ticks/s, deterministic from `(seed, command log)`.** `WorldState` is plain JSON. Every entity carries previous-tick position so render interpolates.
- **Commands** (`build upgrade specialize buySkill sell setRally moveHero cast levelAbility callWave`) are enqueued, applied at the start of the next tick, in order, and logged for replay. `sim.check(cmd)` dry-runs and returns a rejection reason or null: use it to grey out buttons so the UI never has its own copy of the rules.
- Only one file steps the sim (accumulator loop, speed 1-3x, pause). Render gets a readonly view and `?verify=1` hashes state around every frame to prove it never mutated it.
- **Blocking** (the heart of the genre): soldiers and heroes claim ground enemies within an engage radius of their anchor (rally point or hero stand point). The first claimer becomes the enemy's `blockerId`; once in reach the enemy stops and fights it; up to `maxAttackersPerEnemy` gang up. Flyers are never blocked; a "break free" trait lets hounds escape after N seconds; heroes walking under a move order ignore enemies.
- Projectile kinds: instant (hitscan), homing, lobbed (ground-plane, predicted aim; render adds the arc), chain (hops every 3 ticks).
- Damage: armor and magic-resist fractions, curse, damage-taken buffs, a bonus-vs-monsters factor. Tower skill params sum into `tower.mods`.
- **Behaviour is a string key** referenced from data (`tower skills, enemy traits, ability scripts, gear`); logic lives in registries with hooks (`onHit onKill onTick onAfflictedDeath onSoldierDeath`). Per-tower scratch state is `tower.vars` (numbers only, snapshot-safe).
- A test enforces "no renderer, DOM, Math.random or Date in `src/sim`". `scripts/purity-check.mjs` is the standalone version.

## 3. Counter-design: every tower needs a counter-enemy, every enemy a counterplay

| Enemy | What it does to you | What answers it |
|---|---|---|
| Torch-bearer (ignite) | halves the nearest tower's attack speed for 3 s | kill it first; range |
| Exorcist (elite priest) | disables one tower for 4 s | silence/stun/charm it |
| Witch-hunter mage / mage boss | dispels tower buffs and specialisation auras in a radius for 4 s; tower falls back to its bare tier attack | silence, stun or charm the mage; kill it with physical damage |
| Siege catapult crew | wrecks towers from range; a wrecked tower does nothing and a wrecked barracks stops respawning | a 300-range sniper outranges the catapult's 250; a barracks rally or a knight reaches it; chain lightning |
| Lancer (mounted) | charge passes THROUGH blockers and knocks soldiers aside | a `brace` tag: the knight is never knocked aside and stops a charge within 45 px (stun 1 s, once per 4 s per knight) |
| Paladin cavalry | armor aura to nearby humans, holy aura vs monsters | true damage ignores the armor aura |
| Alchemist | -50% armor on blockers for 5 s | damage-reduction auras, more blockers |
| Hound | fast; blockers do not hold it | break-free counter, brace |
| Balloonist | flyer; only anti-air hits it | one tower family hits flyers |

Design target: a **tower/spec x scenario matrix** (swarm, armor, pack, cavalry, mages, siege, air, rush, healers, boss, support) where each tower has a column it tops and **at least one column under 30%**.
Receipts from the matrix: only the gargoyle family hit flyers (61% at best); one organ-style tower scored 0% against fast cavalry and rushes (it needs dwell time) and 0% against mages (dispel): a real target for the new humans, kept on purpose. A chain effect that let one tower's big hit set off neighbours wiped any clump (swarm 88% with it, 18% without), so it now primes neighbours up to 4 stacks and never fires them.

## 4. Balance harness: bots are the instrument

**The bot ladder** (all play through the same commands as a human):

| Bot | Policy | Stands for |
|---|---|---|
| `novice` | random towers at tiers 1-3, no specs | a first-time player |
| `greedy` | best value per gold; never moves the hero | an economy-only player |
| `frontline` | greedy economy, heroes parked on the front line and left there | **how most humans play** |
| `hero` ("smart") | greedy economy plus a kill-zone hero, interceptions and ultimates | a good player |

**Targets we wrote for Normal difficulty:** novice wins about 60% of levels 1-3 and under 35% of levels 7-9; the frontline bot loses a hero at least once in most runs from level 3; the smart bot wins nearly always and three-stars 50-60%;
Veteran is hard (frontline under 50%); Nightmare about 30% for the smart bot.

**The lesson that produced the frontline bot:** the owner beat the whole campaign and "never died once". Our bots had never parked a hero in front, so every balance report said the hero was fine. Add the bot that plays like the owner BEFORE shipping a balance claim.
After the nerf round the harness reported (2026-09-28): Nightmare smart 28% averaged (target ~30%), Veteran frontline 45% and smart 67%, and **three listed misses**: Nightmare 10% on one level, Nightmare 55% on another, and smart three-stars 69% averaged against a 50-60% target.
The report lists its misses; do not hide them.

**Report format that worked** (one page per level, 200 seeds per level per bot on Normal, 100 on Casual/Veteran): a summary table of win and 3-star rates per bot and difficulty; per bot stars 0/1/2/3 %, average lives lost, hero deaths per run, the killer wave and its share of defeats, top leakers per game, defeats by wave, and gold at each wave start per bot.
Gold-at-wave-start rows exposed economy problems (a novice bot holding 469 unspent gold at the last wave) faster than win rates did.

**Parity methods:**
1. Novice-bot damage shares: after a hero nerf the hero's share fell from about 45% to 26-36%; towers near parity (6.5-18%, a barracks low by design since its value is blocking).
2. Mono-tower runs on one level (20 seeds, same tower on every pad): damage per gold stayed in a 3.9-5.9 band. One bad plan: all-sniper (it cannot stop big waves).
3. A situational arena: 2,200 gold on 2 spots of one tower/spec, 7 seeds, scored as percent of spawned enemy HP killed. HP multipliers are self-calibrated so the median build kills about 60%, except a boss (fixed) and a deliberately hard "pack" scenario.
4. Do the tuning in the content owner's lane and file requests to the level owner (waves) instead of editing across lanes.

**Bot results depend on bot policy.** A second smart-bot variant weighting lanes by lives-at-risk instead of enemy HP changed three-star rates by up to 57 points on a level (90% vs 33%). Report a bracket, not a point.
**New mechanics need bot support the same day:** pads that break on ice made the stock bots stall until the harness reported broken pads as occupied.
A level where the smart bot three-starred 0% (a railway level with a second path) was an outlier worth a design note, not a rounding error.

## 5. Wave and level design

- A **level file** is a contract with the painter: layout sketch (road, pads, castle, hero start), road control points (Catmull-Rom smoothed; the road rendered about 70 px wide at 1x), a pad table (id, x, y), the castle and hero spawn, HUD keep-clear zones (top-left 640x60, top-right 260x90, bottom-left 420x160), mood and palette, landmarks that must stay clear of road and pads, and the new mechanic this level teaches.
- Coordinates are 1920x1080 map pixels; a painted background is 2x (3840x2160) and must match the road exactly. **Render a guide image from the path data** (`render --t 0`) and have the painter trace it. The first art pass shipped a road crossing the castle wall, a pad over the moat, and a level with two bridges.
- `validate` checks pads for reachable, on-map, non-overlapping; add a check for every bug class you find in art (the same check would have caught the first art pass).
- Level 1 is the tutorial: gentle curves, a slow wave 1 the hero can clear alone, the first special enemy at wave 4, waves 4/8/12 as the spikes. Waves are 1.5-2x bigger from level 3 on with mixed-lane pressure; HP ramps from x1 on wave 1 to the level's value by 70% of the level.
- **A boss on every level with a distinct mechanic and a phased health bar** (a rallying leader, a burrower, a mage that dispels in a cone, a healer you must silence, an executioner, a mounted charger).
  Bosses also exposed a bug: an "enraged" phase-change message fired on every boss (found in a 2026-09-29 sweep).
- Region mechanics (blizzard range cuts, overheating towers, fog that hides targets unless lit) each added a harness line item. Budget bot work with each new mechanic.
- Dawn timer (a push to finish before a weakness kicks in), a full-moon night boost, and castle abilities with cooldowns (a boiling-oil AoE at the gate, a stun slam, bat turrets) gave players agency without new towers.

## 6. Performance and integration bugs

- Target: 60 fps with 200+ enemies. Measured 59.8 fps under stress and 60 fps with 294 enemies; at one point one map rendered at 44 fps. The sim ran at about 9,500x real time headless.
- Integration QA found (2026-09-28): a sign-in dialog's DOM clicks leaked into the canvas and muted the game; a music-volume tween threw a pageerror; boss phase art was missed when the sim fast-forwarded; hero bark files missing; the server sent no caching validators; a double slash in a URL returned 500.
- **~87 optional `*.anims.json` sidecar requests per load received the SPA fallback** (200 text/html): missing files look fine in the network panel. Check content-types in the deploy verification.
- A balance nerf waits for the owner's playtest; do not tune blind after a good playtest.

## 7. Art and audio decisions that stuck

- Maps: painted backgrounds from an image model, composited, native 4K. Characters: an A/B of upgraded 3D vs a 2D cut-out rig vs image-model strips judged in the game; the strips won at about $0.16 per character. Gap: characters faced sideways only until front and back walk frames were added.
- IP: original designs only; a banned-phrase test on voice barks; an icon that resembled another franchise's was regenerated.
- Music via a model through OpenRouter (9 cues, $1.24, a crossfade loop builder, a transcription check for stray vocals, about -16 LUFS). SFX through ElevenLabs (24 sounds, about 144 credits; loudness-checked). Barks in six voices, each transcribed and checked. See `game-forge:game-audio`.
- Art spend cap history $10 to $60, ledgered per call; a cost log that exposed account balances had to be stripped before the repo went public.
- A day of work as a timeline (local time, 2026-09-27): 16:55 start, 17:08 architect and art director dispatched, 17:46 round 1 verified (31/31 tests, bot 84% wins), 17:50 round 2, 19:12 owner reaction, 20:34 levels done, 21:42 integration done (243/243 tests, 60 fps), 21:5x live, 22:05 public repo. Next morning the owner beat the campaign and asked for more; that playtest drove the biggest balance round.
