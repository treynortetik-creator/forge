---
name: game-lessons
description: >
  The cross-cutting playbook for building a game with Claude Code agents, distilled from two
  real builds: a Phaser 4 + TypeScript Hades-like roguelite and a Phaser 3 tower-defense game.
  Covers architecture (pure deterministic sim + thin renderer, data-driven content, a CLI and a
  validate command), Phaser 4 specifics and traps, copying UI layout from a genre leader,
  gamepad-first input, game feel and hit-stop, clarity passes, living ambient motion, the agent
  workflow (builders in worktrees, one review then merge, the main session deploys, a heavy-job
  lock, owner-feedback triage), budgets tied to real constraints, shipping (Electron, Windows zip,
  Steam scoping and AI disclosure), and a dedicated tower-defense section. Use when starting,
  planning, reviewing or shipping any game with agents. Triggers: "build a game with agents",
  "Phaser 4", "game architecture", "hit-stop", "game feel", "gamepad", "Steam page", "Steam Deck",
  "tower defense", "game balance bots", "how should agents work on a game".
---

# Game lessons

**The one-line case:** two games, one set of mistakes. The tower-defense game went from empty folder to a
public link in about five hours (project doc started 16:55, live URL at 21:5x the same day, 243 tests green,
60 fps) because the simulation had no renderer in it, content was data, and every agent tested through a CLI.
The roguelite then spent three weeks paying for every shortcut we skipped: a bot that lied, a cap nobody chose,
a deploy path that failed six times, a UI the owner could not read. Every rule below is one of those, with the receipt.

> **House thesis, applied to games:** judgment stays with the model and the owner; anything expressed as a number
> gets measured by a harness (a bot sweep, a frame-time run, a palette audit), not eyeballed. A green `tsc` is not
> a working game. An agent's "done" is a claim until you have run the thing and looked at the PNG.

Sibling skills: `game-forge:build-a-game` (the phase-by-phase tutorial that orders all of these), `game-forge:sprite-pipeline-3d`,
`game-forge:local-3d-gen`, `game-forge:local-models`, `game-forge:art-waves`, `game-forge:game-qa-loop` (the playtest and bot
harness in depth), `game-forge:levels-and-backgrounds`, `game-forge:typography`, `game-forge:game-audio`.
From design-forge: `design-forge:photo-to-3d-loop`, `design-forge:art-department`. This skill is the spine they hang from.

Depth lives in `references/`:

| File | What is in it |
|---|---|
| `references/phaser4-traps.md` | Phaser 4.2.1 API facts, removed v3 APIs, 13 errors found in a community plugin, silent failures, perf traps with numbers |
| `references/game-feel.md` | Hit-stop, shake, rumble, input buffer, camera and telegraph tables (spec values), the beats |
| `references/ui-and-clarity.md` | Copying a genre leader's layout, the UI kit shape, the clarity pass (naming rules, glossary, card-fit test), ambient motion rules |
| `references/agent-workflow.md` | Round structure, folder ownership, worktree rules, review limit, feedback triage, machine limits, with failures |
| `references/tower-defense.md` | The tower-defense section: blockers, counter-enemies, bot ladder, balance targets, level files |
| `references/shipping.md` | Electron wrapper, Windows zip, Steam scoping (page, demo, Next Fest, EA), AI disclosure and licence checks, web deploy |

Scripts (smoked, no dependencies): `scripts/heavy-lock.sh`, `scripts/purity-check.mjs`, `scripts/gamepad-detect.ts`.

---

## 0. Before any code

1. **Stack research first.** For every new game or major component run a "what would professional developers pick,
   and why" pass before the spec: how comparable products were built, realistic options per layer, which languages
   and frameworks agents write and maintain best. End with a verdict. We chose a browser engine over a native one
   because of reach, agent-driven headless testing, and precedent, and kept the pure-TypeScript sim so a port stays
   open. Native would only have bought adaptive triggers and console reach.
2. **Pick a genre leader and name the bar.** Tower defense: Kingdom Rush. Roguelite: Hades. "Copy the layout and
   the grammar, invent the style and the gameplay" is a rule, not a vibe (section 5).
3. **Write the IP rule down before the first prompt.** If you adapt public-domain characters, check which designs
   are still protected (a studio's film look is not public domain just because the book is). Add a banned-words test
   for barks and copy. Do it once, early; art models will otherwise reproduce the famous silhouette.
4. **Name the real constraints.** Target machine (a Steam Deck?), store (Steam? itch?), controller (pad first?).
   Every budget in the project must trace to one of these (section 9).

## 1. Architecture that made agents fast

```
src/sim/      pure TypeScript. NO renderer, DOM, Math.random, Date, performance, raw Math.sin/cos
src/data/     content as data (units, items, levels, waves) + schema + a validator
src/render/   reads sim state, interpolates, sends commands. Never writes sim state
src/input/    browser input -> ONE InputFrame / Command path shared with CLI, scripts and bots
src/bots/     scripted players, pluggable
src/cli/      the game from a terminal: new, step, state, run, bot, script, validate, render
tests/        unit tests + JSON scripts with assertions
```

1. **Fixed timestep, deterministic from `(seed, command log)`.** Tower defense ran 30 ticks/s; the roguelite 60 Hz.
   One accumulator loop in one controller file steps the sim; render draws `lerp(prev, cur, alpha)` so 144 Hz is smooth.
   Headless it runs 100x+ real time: 200 bot runs of a 12-wave level in 11.2 s (about 9,500x).
2. **Cross-engine determinism is not free.** `Math.sin/cos/atan2/exp/log/pow/hypot` and `**` are implementation-
   approximated; V8 and JavaScriptCore can differ in the last bits. We wrote polynomial trig over `+ - * / sqrt`,
   tested it against `Math` within 1e-9, and enforced the ban with a test. Receipt: the browser state hash printed by
   the render command matched the Node hash at tick 3,840 of a bot run. Run `scripts/purity-check.mjs src/sim --strict-math src/sim`.
3. **Named RNG streams** (`rooms`, `rewards`, `gifts`, `combat`, `ai`, `loot`). A stream is never shared, so a bot
   taking a different reward does not reshuffle the next room. We have a test proving it.
4. **State is plain JSON.** Snapshot = `structuredClone`; hash it; resume from a mid-run snapshot and assert
   "resume == uninterrupted". Render gets a `DeepReadonly` view; a `?verify=1` mode hashes state around every frame and
   flags any mutation by render code.
5. **Events are the render contract.** `step()` returns the tick's events; juice, audio and HUD subscribe. Add event
   types and optional fields freely; never rename or remove one. Same for the content schema.
6. **Effects are render-only.** Never change a hitbox, timing or damage to make an effect look right.
7. **Content is data; behaviour is a string key.** Data references `behavior: 'statMod'` or `script: 'x'`; the logic
   lives in a registry (`registerEnemyAi`, `registerMod`, `registerStatus`). Pre-populate the registry index files so
   parallel builders never edit the same file (section 8).
8. **A CLI so every agent tests through the game, not around it.** Session file + `--json` everywhere + exit codes
   (0 ok, 1 assertion/validation failure, 2 usage, 3 game rejected the command). Commands: `new`, `step`, `state`,
   `events`, `run --until`, `bot`, `script file.json` (steps with `expect` operators), `validate`, `render` (the real renderer
   in headless Chrome, then LOOK at the PNG). The tower-defense CLI was ordered about 25 minutes into the project; it paid for itself that evening.
9. **`validate` is a gate.** Schema ranges, dangling references, unregistered behaviour keys, towers without exactly
   the right tier count, unreachable or overlapping build spots. Content bugs die here, not in a playtest.
10. **Damage math with named additive buckets.** `round(Base x (1+Power) x CritMult x (1-Guard))`, every "+%" lands in
   exactly one bucket and adds inside it; caps on crit chance (60%), Guard (70%) and Ward (60%). Our research notes say a
   leader shipped multiplicative stacking first and saw 6x blow-ups (unverified here); either way, bucket from day one.
11. **Definition of done, same for every agent:** tests green, build green, `validate` 0 errors, a JSON script covering
   the feature passes, bots show no timeouts or crashes over 50 seeds, a render screenshot opened and looked at, fps still ~60 if render was touched.

## 2. Phaser 4 (details in `references/phaser4-traps.md`)

- **Source of truth is the installed package.** `node_modules/phaser/types/phaser.d.ts` for signatures and
  `node_modules/phaser/src/` for runtime (`grep -rn "GameObjectFactory.register('" node_modules/phaser/src/gameobjects/<name>`).
  Never trust a blog, a model's memory or a community plugin over the types.
- **Official Phaser 4 skills ship inside the package:** 28 folders in `node_modules/phaser/skills/` (checked on 4.2.1),
  from the `phaserjs/phaser` repository. Symlink them into the project's `.claude/skills/` as `phaser4-<name>` so a builder reads the
  matching one BEFORE writing the call: `ln -s ../../node_modules/phaser/skills/filters-and-postfx .claude/skills/phaser4-filters-and-postfx`.
  Start with `v3-to-v4-migration`, `v4-new-features`, `filters-and-postfx`, `render-textures`.
- **Our experience is v4.2.1** (Phaser 4.0.0 shipped 2026-04-10, 4.2.1 on 2026-07-09, checked with npm). The tower-defense game
  shipped on Phaser 3 and held 60 fps with 294 enemies; every v4 trap in the reference came from the roguelite.
- **Top traps** (each has a receipt in the reference): v3 APIs that no longer exist (`preFX/postFX`, `BitmapMask`,
  `setPipeline`, `tintFill`, `camera.setScissor`, `Phaser.Geom.Point`, `Phaser.Math.PI2`); filters need `enableFilters()`
  once and cost a render pass per object; `RenderTexture` draws nothing until `render()`; creating a RenderTexture in play
  stalled frames 40-100 ms; first use of a shader or texture hitches 60-97 ms (warm it under the title card); additive and
  normal sprites alternating in one depth band break batches (88 to 110 draws with nine effects); `Text.setText`
  per frame re-uploads a canvas (80 uploads/s from one HUD bug); listeners registered in `create()` leak across restarts.
- **Pick one canvas size and FIT it.** A fixed 1920x1080 under `Scale.FIT` made every layout number a constant.

## 3. Pure-sim animation and effects

- **Which frame shows is decided by sim state, not Phaser's clock.** Pick the animation from sim state each tick, so hit-stop and pause
  freeze it and the render command is repeatable. When the wrong clip plays, the sim state says so: fix the mapping,
  do not add a render-side override flag.
- **Idle = one still frame plus a runtime breath.** Image-model idle loops played as ping-pong between different poses
  (neighbour overlap 44-73%) and the figure "boiled". Regenerated 8-frame breathing loops reached 89-95% overlap, but the new
  idle rendered 15-20% smaller than the old one, so idle to run would pop. Measure registration, bake offsets, check scale across clips.
- **Three effect layers:** runtime glow (filters, additive pooled sprites, zero files), procedural arcs (jagged polylines rebuilt per
  frame, never the same twice), baked 3D flipbooks for rare big moments in ONE shared atlas. AI-animated VFX: concept stills only (frames drift and bleed).
- Pipelines for the art itself: `game-forge:sprite-pipeline-3d`, `game-forge:art-waves`.

## 4. Game feel (spec tables in `references/game-feel.md`)

The bar: **every input answers in under 100 ms, dash cancels anything, kill anything floaty.**

- **Hit-stop lives in the sim** (bots play with it on). Local: attacker and victim skip ticks. Global: hero hurt, phase break,
  boss kill. Our spec: light 40 ms, medium 60, heavy 90, crushing 120, crit +30, killing blow +20, hero hurt 80 global.
  One stop per attacker per 100 ms; never stack local and global, take the larger; **a dash press breaks hit-stop.**
- **Hit-stop must pause everything it implies.** A balance pass found telegraph timers kept running during hit-stop and had to
  freeze them; another found hit-stop should be paid out of the attacker's recovery, not added to it.
- **Shake is amplitude-by-event, not a constant.** 0 on light hits, 4 px heavy, 8 px crushing, 10 px boss slam, 14 px phase break;
  concurrent shakes take the max, not the sum. Settings: shake slider, flashes toggle, reduce-motion. Honour them everywhere.
- **Rumble is a bonus, never the only feedback** (Firefox has none; a DualSense on Windows Chrome likely gets none).
- **Input buffer 150 ms**, hold threshold 200 ms, dash-attack window 100 ms, corner correction 8 px, pit "coyote" grace 24 px.
- **Every enemy attack gets a telegraph:** a wind-up on the body AND a ground decal that fills to the edge exactly when the
  wind-up ends, last 120 ms flash. Telegraph colours are a language (enemy danger vs your zones); never use danger colours for friendly zones.
- **A hit flash must not outlive the sim.** Ours was capped at 90 ms of wall clock after white blobs appeared when the sim paused mid-flash.
- **Hitch work is part of feel:** pre-bake the next room's floor in idle slices, pool RenderTextures, warm shaders. p99 frame time 77-99 ms
  fell to 27-30 ms from those three changes, not from "optimising the sim" (0.14 ms/tick).

## 5. UI: copy a leader's layout, invent the rest (`references/ui-and-clarity.md`)

- **Rule (the owner's, 2026-10-18):** teams chose those layouts because they work; lean on what exists. Copy HUD
  placement, menu structure, dialogue box, screen flow. Reinvent gameplay, story, art style. Never copy their art.
- **Get the layout spec from the pixels, not from a model's memory.** We extracted 41 frames from gameplay video and wrote a
  layout spec with percent positions; an LLM write-up of the same game had 108 claims and only 8 were right as written
  (one note described the previous game). Verify against frames, or label the claim unverified.
- Departures are allowed when the leader's version cannot fit your mechanics: write down the departure and why (ours: shop items
  show effect text on walk-up). When your own style doc and the leader's placement disagree, the leader's placement won (health bottom-left).
- **One UI base class, pure layout.** Every controller-navigable screen extends one base that owns focus, prompt bar and
  input loop. Spatial focus is a pure, unit-tested function. Card text layout is a pure function tested at EVERY item x rarity x
  level with real font metrics, not "looks fine on one card".
- **Pad-first means pad-only:** every screen usable with the pad alone; mouse second.

## 6. Gamepad-first input (`scripts/gamepad-detect.ts`)

- **Read the raw Gamepad API yourself for gameplay** (`navigator.getGamepads()` polled each render frame) plus DOM keyboard/mouse,
  and produce ONE `InputFrame` per sim tick. The CLI, scripts and bots produce the same frame, which is why replays are exact.
  Phaser's input plugins are fine for pointer events on UI objects only.
- **Latch presses between ticks and consume once.** A press shorter than a tick still counts; a press consumed by a menu must not leak
  into the game (we have a dialogue input-gate test).
- **Bindings: pad first** on W3C standard indices, keyboard second. **Prompts follow the last-used device** (PS shapes, Xbox letters, Deck, keyboard);
  never hard-code "Press E". Add a Settings override (Auto / PlayStation / Xbox / Keyboard), because Steam Input disguises pads.
- **Detect by vendor id, then name, and test the order.** Sony 054c, Microsoft 045e, Nintendo 057e, Valve 28de. A name regex for
  "wireless controller" placed before "xbox" gave Xbox pads PlayStation glyphs; macOS Chrome/Safari ids may carry no vendor hex.
  On a Deck, Steam Input presents a virtual Xbox pad: detect the Deck from the shell, not the pad.
- **Menu discipline:** a screen ignores input for 250 ms after it opens (a mashed attack once could pick a card); destructive actions need a
  1 s hold; held-direction repeat 400 ms then 90 ms.
- **Auto-pause** on tab hidden, window blur, leaving fullscreen mid-run, or the active pad disconnecting. Clear held and buffered inputs. On return stay paused.
- **Accessibility lives between device and sim:** hold-to-repeat attack, toggle-charge. The sim only ever sees ordinary bits, so replays stay exact.
- Dead zones: radial, left 0.15 inner / 0.95 outer, right 0.25. Pad-only aim assist (snap within +-12 degrees, 600 px; never through a wall).

## 7. Clarity pass and living motion (`references/ui-and-clarity.md`)

- **The owner played and could not tell what half the words meant.** Causes, in order: six power-granting factions with two names each; the same word
  for two things (Seal, Guardian, Favour, Ward, Trial: five collisions in one game); flavour lines that announce a mechanic and never state it; internal ids on screen.
  The fix was a spec: top-15 confusing terms, naming rules, a 106-entry glossary, 26 one-time tips, 121 verified rewrites (120 applied).
- **Rules:** one word, one meaning; flavour first, then a plain line that never jokes; player units only (seconds, "nearby", never ms or px);
  "not built yet" says so in plain words; ban engineer words in game text (i-frames, DPS, ticks, biome) with a test.
- **The clarity pass found wrong rules taught by the game.** A card said "guaranteed crit"; the sim gave +20% crit chance for 5 s. Door
  labels and item text disagreed on numbers (25% vs 30%). Check every number on screen against the sim.
- **Nothing glowing is ever still; nothing is static on a screen the player lingers on.** Pulses are a slow breath with a wobble (never a clean sine,
  ~1 s), gold shimmers every ~2.8 s with a 600 ms sweep, portraits blink for 110 ms every 3-7 s, the advance mark bobs 5 px over 1.4 s, drifting
  motes are pooled and capped. One update source, a phase offset per instance, reduce-motion goes static. Receipt: the ambient layer cost 0 files and left frame p50 flat at 16.8 ms.

## 8. The agent workflow (`references/agent-workflow.md`)

1. **Round 1 is two agents:** an architect (engine, contracts, CLI, ARCHITECTURE.md with an ownership table) and a designer (GDD and siblings).
   Round 2 is builders split by FOLDER ownership; engine hooks are requested in `design/requests/<area>.md`, not patched.
2. **Builders work in git worktrees** (`<project>-wt/<name>`), branched from an integration branch. Dependencies symlinked, never `npm install`.
   Commit explicit paths, never `git add -A` (an architect's `git add -A` swept another agent's work-in-progress into its commits; one art commit swept 557 files).
   Builders never push, merge or deploy. **Never edit the main checkout.**
3. **One review, then merge.** An Opus-class reviewer before main, one fix check, then only serious bugs block; small findings go in a follow-ups file.
   Unbounded review loops return endless low nits (two rounds scored 7/10 with fresh nits each time; the round that told the reviewer to separate blockers from polish passed at 8/10).
4. **The main session integrates and deploys.** Builders' output is a claim: `ls` the artifact, run the gates in a clean worktree, look at the shots.
   Receipt: a review caught a HUD file that did not parse at HEAD after a merge.
5. **Heavy-job lock.** One of each across all worktrees (Blender, headless Chrome, a vite build) on a 16 GB laptop; TWO slots on 32 GB. `scripts/heavy-lock.sh -n 2 -- <cmd>`.
   Check `uptime` and swap before a fan-out; queue if load > 20 or swap > 8 GB. Never `pkill`/`killall` (it killed other agents' work).
   Receipts: nine parallel agents hit load 38 and 12.6/13.3 GB swap; the disk hit 0 bytes free more than once from agent repo copies and worktrees.
6. **Owner feedback is triaged before it is fixed:** verbatim intake, four kinds (defect, tuning, design, unactionable), group by root cause,
   reproduce as a FAILING script/test/shot first, fix, verify, reply per item in his words, keep the repro as a regression test.
7. **Spend caps and logs.** Paid generation goes through a script that logs every call and stops at a cap. Voice: spec and audition before bulk generation (`game-forge:game-audio`).
8. **Deploy from version control, not by uploading a build.** Section 10 and `references/shipping.md`.

## 9. Budgets and caps: trace every number to a real constraint

- Early on we gated on web-port numbers (itch 1,000 files, CrazyGames 1,500, 20 MB first play, 900 KB JS gzip) because the plan was a browser release.
  When the plan became Steam-first, those gates were still failing builds and had cost a risky lean-engine build, a q66 icon re-encode and a lossy 3D byte ladder.
  The owner's rule: **a self-imposed cap is not a constraint.** Trace it to a real target (Deck frame rate, Deck memory, store review) or make it warn-only.
- **Real gates we kept for a Steam Deck target:** 60 fps at 1280x800 in a busy fight; texture memory peak under 1.5 GB over a 20-room soak (measured ~830 MB, 971.7 MB on a later build);
  text floor 28 px; boot to title under ~3 s; install size under a 2 GB sanity line (the Electron build was 340-393 MB).
- **Builders never lower a gate.** No raising a budget, loosening an audit threshold, skipping a test. They report the failure with numbers; the owner (or the main session, with a note) moves a gate.
- **Measure before you optimise.** Headless Chrome renders through a software GPU: bytes and request counts are exact, frame times are noisy. Compare p99 and "frames over 33 ms" between paired runs, never quote a headless fps as the game's.
- Receipt for doing it right: boot to title 2,667 ms to 544 ms, 826 requests / 30.5 MB to 60 / 1.8 MB, by splitting load into three phases (title, hub, biome one ahead) and self-hosting a font that was render-blocking.

## 10. Shipping (details and dates in `references/shipping.md`)

- **Desktop wrapper: Electron.** Same Chromium you tuned on, so gamepads and perf match; ~393 MB unsigned mac app, 338 MB Windows zip cross-built from a Mac. Saves must be JSON files for Steam Auto-Cloud;
  `localStorage` in Electron flushed only on clean quit. Bundle fonts for offline play. **A Windows build you have never run on Windows is not a build:** add a CI smoke test that launches the exe, writes and reads a save, and fails on console errors.
- **Steam scope (as checked 2026-10-19, re-verify before acting):** $100 fee recouped at $1,000 adjusted gross; 21 days from payment before release; tax check up to 30 days; Coming Soon page public 2+ weeks;
  plan 7 business days for each review; Next Fest once per game, ever; demo is a separate free app; wishlist "demo is out" notification once, within 14 days of the demo's first release.
- **Start the paperwork first.** Every Steam clock starts when the owner pays and finishes forms; a reconcile found the code ahead of plan and the store side stuck for want of a fee and two app ids.
  Owner-blocked items are the critical path, so surface them in week 1.
- **AI disclosure is part of the build.** Steam's Content Survey asks about pre-generated and live-generated AI content. Check each generator's licence for commercial use BEFORE the page goes live
  (on 2026-10-20 a pay-as-you-go ElevenLabs account did not carry a commercial licence, so the advice was to regenerate everything that ships after subscribing). Disclose plainly; never market the game as "the AI game".
- **Web deploy:** deploy from the git repo (auto-deploy on push), not by uploading a 127 MB `dist/` over a 10.7 Mbps uplink (timeout, then HTTP 524, six failed deployments one night). Verify asset content-types: a SPA fallback
  answers any missing file with 200 and `text/html`.
- **Open-sourcing a game repo:** publish a fresh squashed snapshot, not the history (local `.git` was 747 MB); run a secret scanner and a hand grep for paths, emails and cost logs; use an independent audit agent. The audit removed four cost logs that exposed account balances.

## 11. Tower-defense lessons (full section: `references/tower-defense.md`)

1. **Bots are the balance instrument, and a bot that plays unlike a human lies.** The owner beat the whole campaign without his hero dying
   ("a bit easy, hero is OP"). Root cause: our bots never parked a hero on the front line. A `frontline` bot became the balance target: heroes must die at least once in most runs from level 3 on.
2. **A bot ladder, not one bot:** `novice` (random towers), `greedy` (value per gold, never moves the hero), `frontline` (how most humans play), `hero` (the smart bot). Report a bracket, not a point; a second smart-bot variant disagreed with the first by up to 57 points on a level (90% vs 33% three-star).
3. **Every tower needs a counter-enemy and every enemy a counterplay.** Torch-bearer halves tower attack speed, exorcist disables a tower, mages dispel specialisation buffs, catapults wreck towers, lancers charge through blockers. Publish a tower/spec x scenario matrix; "each tower has at least one column under 30%" is a design target.
4. **Level files are a contract with the painter.** Layout sketch, smoothed road control points, pad table, HUD keep-clear zones, landmark list, and a guide render from the path data for the art model to trace. After the first art pass: a road crossed the castle wall, a pad sat on the moat, one level had two bridges.
5. **New mechanics need bot support the same day.** Pads that break on ice stalled the stock bots until the harness showed broken pads as occupied.
6. **Fixed build spots, roads, barracks blockers with a rally point, a click-to-move hero, 3 stars per level** is the grammar. Hotkeys for everything in battle, touch support, a "call wave early for gold" button.

---

## Traps

- **Trusting the instrument.** Our bot run cap (900 s) deflated win rates: skilled win rate read 0% at the cap and 45% at 2,400 s, so the game had been "balanced" while about twice too easy. A zero is a claim about your harness.
  Also: 44% of damage in one balance report was the bot's own dash-attacks. Print raw output before declaring a number.
- **A state cleared by one event only.** The screen stayed dark after menus because the dim stack only cleared on `giftTaken`. Overlays need a stack, a room-entry clear, and a timeout.
- **Defined for one hero only.** An ultimate-style meter never appeared for four of five heroes because only one hero's data defined it. Test the feature across every content row, not the one you built.
- **Rewards with no art or no feedback read as bugs.** An "invisible heal" was stair rooms with no art for the heal pedestals. Placeholders must be loud in dev and never silent.
- **A stand-in atlas claiming a texture key** hid real art for two bosses. Test that no placeholder key shadows a real one.
- **Shared-file collisions.** Two builders on `manifest.json` or the schema. Give generated outputs one owner (the integrator) and commit sources only.
- **Web-era caps steering art choices** (section 9). Ask where a cap came from before it costs the owner a creative trade.
- **Re-running a closed question.** Record decisions with the date and the owner's words; never re-ask. Mark estimates and unverified claims as such inside the deliverable.
- **Headless fps quoted as truth.** See section 9.
- **A sprint plan that outruns the owner's hours.** 59 of 61 non-merge commits over two weeks were art and FX while script, settings and Steam work barely moved. Re-reconcile plan vs reality weekly and push the integration branch daily (83 unpushed commits is a backup problem).

## Licences and cost

- Phaser (MIT), Electron (MIT). The community Phaser plugin we audited had no LICENSE file: we reviewed it, kept the ideas, vendored nothing. Link it, do not copy it.
- Fonts under the SIL OFL ship with a licence file; music, voice and image generators each need a commercial-use check (`references/shipping.md`).
- Spend we actually saw: art cap $10, raised to $25, $40, $60 on the tower-defense game as the owner approved; one music pass of 9 cues $1.24; on the roguelite, animating 12 monsters and 4 bosses with an image model $2.30 (95 calls).
  Rule: over about $1, dry-run and ask; log every call.
