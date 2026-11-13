---
name: game-qa-loop
description: >
  Prove a browser game works without a human watching it. A deterministic sim kept
  separate from the renderer, a CLI that plays it headless, skill-tiered bots for
  smoke and balance runs, URL dev params that jump to any scene, headless Chrome
  screenshots through puppeteer-core, a proof ladder from unit tests to fps, perf
  budgets with measured numbers, a one-heavy-browser lock, a feedback-to-failing-repro
  loop, and recording a gameplay highlight reel or a raw demo video. Use when asked to
  test a game, make a game agent-testable, write a game CLI or bots, playtest, balance
  a game, find why something is slow or broken, triage player feedback, take
  screenshots of a running game, or record a demo video. Triggers: "playtest",
  "prove it works", "bot sweep", "game CLI", "headless screenshot", "fps budget",
  "balance pass", "bug hunt", "demo video", "highlight reel", "it only happens sometimes".
---

# Game QA Loop

**The one-line case:** `tsc` proves the code compiles and says nothing about whether the game runs. Two games
(a Phaser 4 roguelite and a Phaser 3 tower-defense game) were built mostly by agents, and what kept them honest
was a pipeline where every claim ("the boss dies in under 90 s for a skilled player", "first play is under
20 MB", "the hit flashes") is a command with an exit code or a screenshot somebody looked at. Numbers from that
pipeline: a bot sweep of 100 runs in 2.5 s (the CLI doc's sample output); a bug hunt (450 bot runs, a 60 sim-minute soak, scripted browser sessions, code review) that
logged 6 crash/softlock bugs; a perf round that took p99 frame time from 77-99 ms to 27-30 ms and time-to-title from
2,667 ms to 544 ms; a 250-run bot sweep whose 5 timeouts exposed a softlock no human had hit.

> Forge's thesis applies here: **judgment stays with the model, and anything expressed as a number gets
> measured instead of eyeballed.** The reverse also holds: a taste question ("does it feel good", "is it readable")
> is NOT a number. Label it NEEDS OWNER and attach screenshots; do not invent a metric.

Sibling skills: `game-forge:game-lessons` (the failure catalogue), `game-forge:sprite-pipeline-3d` and
`game-forge:art-waves` (art gates that plug into rung 6 below), `game-forge:game-audio`. Visual design gates live in
`design-forge:design-audit`.

Depth lives in `references/`:

| File | Read it when |
|---|---|
| `cli-and-scripts.md` | building the CLI, the session file, the script format, the screenshot harness |
| `bots-and-balance.md` | writing bots, tiers, sweeps, reading balance statistics |
| `perf-playbook.md` | any fps, load size, memory or hitch work |
| `bug-hunt-and-playtest.md` | running a bug hunt, a fresh-eyes playtest or a QA pass; triaging feedback |
| `highlight-reel.md` | recording a demo video or a highlight reel |
| `test-templates.md` | writing the purity, determinism and replay tests |

Scripts (self-contained, in `scripts/`): `record-reel.mjs`, `cut-reel.sh`, `perf-sample.mjs`. The heavy-job lock is
`game-lessons/scripts/heavy-lock.sh` (one canonical copy, N slots).

---

## The workflow

### 1. Build the game so it can be tested (do this first, it is cheap early and ruinous late)

1. **Deterministic sim, separate from render.** `src/sim` is a fixed-step headless simulation (60 Hz in the
   roguelite, 30 Hz in the tower-defense game): no engine, DOM, `Math.random`, `Date`, `performance`. Same
   `(seed, input log)` gives the same state, always. `src/render` reads a read-only view of sim state and sends
   input back; only one controller object steps the sim; effects are render only.
2. **One input path.** The browser, the CLI, scripts and bots all produce the same input frame (or command
   list). A bug then replays from `(seed, hero/level, mode, input log)`.
3. **Enforce the boundary with a test, not a promise.** A purity test scans the sim folders for banned names,
   including `Math.sin/cos/exp/pow...` (engines may approximate them, so Node and Chrome can diverge); the sim
   ships its own trig, tested against `Math.*` within 1e-9. A determinism test hashes state after a run and after a
   replay. Templates: `references/test-templates.md`.
4. **A state hash** (`hashState`) that the CLI, the tests and the browser can all print. Node hash == browser hash
   at the same tick is the proof the two sides agree.
5. **Sim events are the render contract** (hit, death, room clear...). Juice, audio and HUD subscribe; add fields,
   never rename.

### 2. Write the CLI (the agent's hands)

A `bin/<game>` command that replays a session file deterministically across separate shell calls: `new`, `step`,
`input`, `run --until <cond> --bot <b> --max <sec>`, `state --json`, `script <file.json>`, `validate`, `bot --seeds 1..100`,
`render --out x.png`. Exit codes: 0 ok, 1 assertion/validation failure, 2 usage error (3 = game rejected the
command, in the tower-defense CLI). Full spec, script format and the screenshot harness: `references/cli-and-scripts.md`.

A script is a list of steps with `expect`; the metric list is closed (unknown name = exit 2), so a typo cannot
pass silently:

```json
{ "name": "bot clears room 1", "seed": 4,
  "steps": [ { "until": "clear", "bot": "basic", "max": 150, "expect": ["roomsCleared==1", "enemies==0"] } ] }
```

One test file runs every `tests/scripts/*.json`, so a new regression script needs no registration.

### 3. Bots in tiers

`random` (fuzzing floor), `novice`, `average`, `skilled`, `perfect` (oracle). Tiers come from a perception model
(reaction time, per-threat choice time, a lapse chance), not aim cheats, so telegraph changes move the results
with no extra code. `basic` = the smoke-test bot. A tier change is a balance change: recalibrate only from human
data. Details, parameters, sweep statistics (paired seeds, Wilson CI, bootstrap, McNemar) and what the sweeps
caught: `references/bots-and-balance.md`.

### 4. Dev URL params and a debug handle

Make the real game jump anywhere: `?scene=run|hub|ui&seed=7&hero=h&bot=basic&t=12&paused=1&mute=1&room=<template>&biome=N&debug=hitboxes&screen=<ui screen>`.
`t` fast-forwards the sim and pauses (a boss fight is one URL, not twenty minutes). `mute=1` for headless.
Expose `window.__<game>` with `ready`, the game, the controller (live sim state, an event subscription,
`send(cmd)`), `hash()` and a perf object. Every harness waits on `ready` and reads `window.__x.ctl.sim.state`.
A UI preset table (preset name -> query params + a save fixture + key steps) turns every menu screen into one command.

### 5. The headless Chrome harness

System Chrome via `puppeteer-core` (no bundled browser). Serve a **fresh production build from a temp dir**, not the
dev server: other agents' edits trigger HMR reloads that navigate the page mid-shot. Flags and the `openGame()`
shape: `references/cli-and-scripts.md`. Collect `console` and `pageerror` into a `logs` array and print them. Drive input
with real `page.keyboard` / `page.mouse` events so it goes through the actual input path.

### 6. The proof ladder (cheapest rung first; climb as high as the change needs)

| Rung | Proves | Command (roguelite) | Heavy lock? |
|---|---|---|---|
| 1 | pure logic: sim, layout math, render-math helpers | `npm test` (vitest) | no |
| 2 | gameplay end to end, deterministic, no browser | `bin/<game> script tests/scripts/x.json` (also runs in `npm test`) | no |
| 3 | content sanity | `npm run validate` | no |
| 4 | the real renderer at a sim moment | `bin/<game> render --scene run --seed 3 --t 55 --bot basic [--live 400] --out shots/tmp/x.png` | YES |
| 5 | menus and UI screens | `npx tsx tests/ui/shots.ts <preset>` or `all` | YES |
| 6 | look gates: colour/palette audit, silhouette or hatch checks (see the art skills) | shots tool, then an audit script with `--strict` | shots YES |
| 7 | frame rate, load, memory | `npm run fps`, `measure.ts --mode fight/flow/soak`, `npm run budget:check` | YES (not `budget:check`) |
| 8 | the owner's gut check | a preview deploy (integrator only) | |

**Look at every PNG you make** (Read tool), at 1x, the size the player sees. Text that must read on a handheld is
checked in 1280x800 shots. A visual claim without a looked-at screenshot is not proof. Turn acceptance
criteria into assertions:

| Criterion | Assertion |
|---|---|
| "the bolt costs one ammo" | script: press cast, `expect ammo<=2` |
| "the boss dies in under 90 s for a skilled bot" | `boss <id> --bot skilled --runs 20 --json`, read the length |
| "no colour except X in combat" | shots + palette audit `--strict` |
| "first play still under 20 MB" | `budget:check` |
| "it feels better", "is it readable" | a human call: NEEDS OWNER + shots, no invented metric |

### 7. Triage: which side of the wall, then a deterministic repro

Rule zero: read the code and reproduce BEFORE writing a fix; write down the cause. Two failed attempts at one
approach: stop and list 2-3 genuinely different approaches.

| Symptom | Side | Reproduce with |
|---|---|---|
| wrong number, damage, AI choice, room flow, softlock, "the run ended" | **sim** | CLI, no browser: `new --seed N`, `step`, `state --json`, `run --until ...` |
| looks wrong: blank sprite, wrong frame, effect misplaced, colour, depth, HUD | **render** | `render --out`, URL params, UI presets |
| art missing only in some rooms or after a merge | **loader / manifest** | key checks on the manifest, the asset tests; was the key loaded in THIS phase? |
| button does nothing, double fires | **input** | input unit tests with stub pads |
| Node and browser disagree, replay diverges, "session hash mismatch" | **determinism** | print the browser hash, compare with `state --json` after the same input |

Never "fix" a render bug by changing sim timings, hitboxes or damage. Never read the engine or wall clock from the sim.

```bash
bin/<game> new --seed 7 --hero h --room <template>
bin/<game> step 90 --move 1,0
bin/<game> state --json > /tmp/s.json
bin/<game> render --session --out shots/tmp/repro.png    # the same state in the real renderer
```

**"It only happens sometimes."** The sim is deterministic, so "sometimes" is a seed or a render/timing path.
Sweep seeds (`bot --seeds 1..200 --full`) to find a failing one and pin that seed in a `tests/scripts/*.json`. If a
fixed seed still varies, the cause is render-side or reads the wall clock. Write the script so it **fails before the
fix**: a repro that passes first time reproduced nothing.

Silent-failure patterns in a Phaser-style render layer: listeners registered in `create()` without removal on shutdown
(effects or sounds double after a restart); particle pools that drop the oldest at a cap (effects "vanish" in big
fights); handlers firing on destroyed pooled objects; tweens on destroyed objects; the first use of a shader or texture
hitching 60-100 ms; same-string dedup swallowing repeated toasts; two systems writing one stat in one tick.

### 8. Performance and size

Budgets are numbers with an owner, a measurement command and a kind (hard gate, warning, info). Measure first, fix
the worst measured thing, never lower a budget to pass. Compare **p99 and frames over 33 ms** between two runs of the
same command on the same machine, paired back to back; headless fps is never the game's fps. Tools, budget table,
the round-8 case study with receipts and the ordered "where frames go" list: `references/perf-playbook.md`.
Quick sample: `node scripts/perf-sample.mjs --project <repo> --url "<game url>" --seconds 8`.

### 9. One heavy job at a time

A headless Chrome, a production build and a Blender process each take seconds of a whole machine. Across **every
worktree and agent** run only one of each, behind a lock directory (`mkdir` is atomic):

```bash
LOCK=${CLAUDE_PLUGIN_ROOT}/skills/game-lessons/scripts/heavy-lock.sh
bash $LOCK -- npx tsx tools/shots.ts         # waits its turn, always releases, never kills anything
bash $LOCK -n 2 -- npx tsx tools/shots.ts    # two slots on a 32 GB machine
```

Never `pkill`/`killall`: it has killed other agents' work. Close only processes you started, by PID. Note that
`openGame()` runs a `vite build` AND opens Chrome, so every browser tool is heavy. Sim-only runs (`bot`, `script`,
`sweep`, `validate`, vitest) are not.

### 10. The feedback loop: intake, triage, repro, fix, verify, reply, keep the repro

1. **Intake verbatim**, with source. "Sometimes" = a seed or timing claim. "After a while" = accumulation (leak,
   listener doubling, pool cap). "It used to work" = find the commit first (`git bisect` with a script). A screenshot:
   open it and describe it before acting.
2. **Triage into four kinds** (defect, tuning, design, unactionable; table in `references/bug-hunt-and-playtest.md`).
   Never silently upgrade tuning into a defect hunt.
3. **Group by root cause.** One fix that closes three reports beats three special cases; if yours closes one, regroup.
4. **Reproduce and watch it fail** (script, vitest, or a before-shot). If it will not fail you have not understood the
   report: ask for one more detail.
5. **Fix**, then verify: the repro passes (for "sometimes", across the whole seed sweep that found it), types, tests,
   after-shots next to before-shots at 1x.
6. **Reply per item in the reporter's words**: Fixed (what changed in what they see) / Changed, check it (new number and
   where to look) / Needs you (question or 2-3 options with a recommendation) / Couldn't reproduce (what you tried, the
   one detail you need). Never stay silent on an item.
7. **Commit the repro with the fix.** It is the regression test that stops the report coming back.

### 11. Bug hunts, playtests, QA passes

Three reusable report styles (evidence-tagged bug hunt, fresh-eyes playtest with a ranked top 10, serial QA pass
with a pass/fail table) are in `references/bug-hunt-and-playtest.md` with the bug classes each caught.
A bot cannot replace a human first-evening player: the playtest found a cliff at the start that a bot sailed past.

### 12. Demo video and highlight reel

A **demo** is the raw uncut live playthrough, no title cards, no on-screen text, 720p, under about 35 MB. A
**highlight reel** (only when asked) is recorded as segments with `scripts/record-reel.mjs` (`page.screencast`, 30 fps,
1920x1080) and cut with `scripts/cut-reel.sh` (720p x264 CRF 22, maxrate 3200k, music, size gate): 78 s in 24.9 MB.
Procedure and traps: `references/highlight-reel.md`.

### 13. Report honestly

Report what you ran and what it printed: command, exit code, key numbers, the shots folder. A green typecheck plus
a failing run means NOT done. A gate you could not run (lock held for an hour, Chrome missing) is reported as not
run, with the reason. If you did not run the game, say so.

---

## Traps (each earned by a failure)

- **Builders cannot delete or weaken tests.** Never skip or `.only` a test, loosen an audit threshold, raise a budget
  or delete a failing assertion to get green. Report the failure with numbers; the owner moves a gate. (Hard rule 1 of the
  roguelite's toolbox skill.)
- **A passing build is not a working game.** A missing manifest key, a throw halfway through `create()`, an effect
  drawn under the floor: all type-check.
- **Timeouts are bugs.** 5 of 250 bot runs timed out because an actor was carried out of the room; zero after the fix.
  Give every `run` a `--max`, and treat `timeout` as a finding.
- **Suspect the bot first** when it dies in a way no human would (bots attacked straight after a dodge dash and cancelled
  their own i-frames).
- **A bot clearing a biome proves nothing about a new player.** The fresh-eyes playtest: human-like play died in rooms
  1-3 on 4 of 5 runs while the `average` bot lost 7 HP.
- **Headless numbers are not device numbers.** Print the GPU string with every run; use paired
  before/after only; check `uptime`; do not quote them as device fps.
- **The dev server reloads under you.** Shoot from a fresh production build in a temp dir.
- **Same-frame key press and release is lost** by input polled per frame: hold for ~160 ms across frames.
- **Third-party requests decide runs.** A render-blocking web font once made load numbers (and boot) depend on the
  network. Self-host, and abort third-party requests in the harness.
- **`page.evaluate` takes a string when your runner is tsx/esbuild**: it injects `__name()` helpers into function
  literals and the page throws.
- **A resume/restore test with an empty progression preset passes while the bug lives.** Use a full preset.
- **A bare `pgrep -f remote-debugging` matches every agent shell that mentions it** and deadlocks the machine; match the
  real Chrome path with `execFile`.
- **Same fixed seed, still flaky = render side or wall clock.** Never "fix" it in the sim.
- **Do not invent a metric for taste.** NEEDS OWNER plus screenshots plus options.
- **Raw demo, not a cut with cards**, unless the cut was requested (a 79 s cut with cards at 48 MB was the wrong deliverable).
- **A screenshot you did not open is not evidence.** Read the PNG.

## Licences and cost

- Everything here is free and local: system Chrome, `puppeteer-core` (npm, Apache-2.0 per the upstream project; check
  before redistributing), Vite, Vitest, ffmpeg. No paid APIs, no model weights.
- `page.screencast` requires `ffmpeg` on PATH. ffmpeg's licence depends on how your build was configured (GPL if built
  with x264): fine for recording your own game, check it before redistributing the binary.
- Music for a reel must be yours or properly licensed.
- Machine cost: a sim-only sweep is cheap; every browser or build job is heavy, so one at a time (step 9).

## Smoke checks (this skill's scripts)

`node --check` on both `.mjs` files and `bash -n` on `cut-reel.sh` pass. `cut-reel.sh` was run on synthetic clips
(trim, concat, music, size gate exit 1). The shared `game-lessons/scripts/heavy-lock.sh` was run for acquire, release on success and on failure.
`record-reel.mjs` and `perf-sample.mjs` each ran once against a trivial local page (one headless Chrome), not against a real game.
