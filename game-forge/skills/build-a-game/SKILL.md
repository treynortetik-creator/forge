---
name: build-a-game
description: >
  The end-to-end tutorial for building a game with Claude Code agents, from an empty folder to a
  shipped demo, in fourteen ordered phases: stack research, a genre leader to borrow layout from,
  a deterministic sim with a thin renderer plus a CLI and bots, data-driven content, a first
  playable with loud placeholders, art direction and a taste file, art production (waves, 3D
  sprites, local 3D, local models), levels and backgrounds, typography and UI, audio and voice,
  feel and clarity passes, perf budgets tied to real targets, playtest and feedback, a trailer,
  and shipping. Each phase names the skill to load, a measured done-gate and the top traps. Use
  as the entry point when asked to "build a game", "make a game with agents", "plan a game from
  scratch", "what order should I build this in", "game roadmap", "make a demo", or "ship a game".
---

# Build a game

**The one-line case:** two games were built this way by one owner and a team of agents. The tower-defense game went from an
empty folder to a public link in about five hours (243 tests green, 60 fps) because the sim had no renderer in it, content
was data, and every agent tested through a CLI. The roguelite then spent three weeks paying for each shortcut skipped. This
skill is the order of work that avoids that, as a checklist. It does not repeat the sibling skills; it tells you which to
load when, and what "done" means for each phase.

> Forge's thesis applies to every phase: judgment (taste, feel, what the player should understand) stays with the owner and
> the model; anything that is a number (a hash, a fps, a palette share, a LUFS, a byte count) is measured by a command with
> an exit code. An agent's "done" is a claim until you have run the gate and opened the PNG. A green `tsc` is not a game.

## How to use this

1. Work the phases in order. A phase is done only when its gate passes, with the output pasted into the project doc.
2. Load the named sibling skill at the start of the phase, not after the trouble starts.
3. Phases 5 to 9 overlap in time (art, levels, type and audio run in parallel once phase 4 is signed off). Phases 0 to 3 do not.
4. Taste calls (art style, names, story, voice) belong to the human owner: bring two to four options and a recommendation,
   build after they pick. Engineering, fixes and perf are autonomous.
5. Keep one living project doc (state, decisions with dates, open owner-blocked items). It is the memory across sessions.

Siblings: `game-forge:game-lessons`, `game-forge:game-qa-loop`, `game-forge:sprite-pipeline-3d`, `game-forge:local-3d-gen`,
`game-forge:local-models`, `game-forge:art-waves`, `game-forge:levels-and-backgrounds`, `game-forge:typography`,
`game-forge:game-audio`. From design-forge: `design-forge:art-department`, `design-forge:photo-to-3d-loop`, `design-forge:design-audit`.

---

## Phase 0. Stack research, genre leader, real constraints

**Goal:** a written verdict on the stack, one named genre leader, and the real constraints every later number will trace to.

**Load:** `game-forge:game-lessons` section 0.

1. Run a "what would professional developers pick, and why" pass before any spec: how comparable products were built, realistic
   options per layer, what agents write and maintain best. End with a verdict and the road not taken. Our verdict was a
   browser engine (Phaser, TypeScript) for reach, headless agent testing and precedent, with the sim kept pure so a port stays open.
2. Pick a genre leader (tower defense: Kingdom Rush; roguelite: Hades) and name the bar. The rule is "copy the layout and the
   grammar, invent the style and the gameplay"; never copy their art.
3. Write the IP rule once, early (which designs are still protected, a banned-words test for copy).
4. Name the real constraints: target machine (handheld?), store, controller (pad first?), the owner's weekly hours.

**Gate:** project doc contains the verdict, the leader, the IP rule, and a constraints table with a source for each line.

**Traps:**
- Skipping research because the stack is "obvious". The research is also where a native-versus-browser tradeoff gets a recorded reason.
- Copying a leader's layout from a model's memory. An LLM write-up of one game had 108 claims and 8 were right as written; extract frames from
  gameplay video and write percent positions from pixels (`game-lessons` section 5).

## Phase 1. Deterministic sim, thin renderer, CLI, bots

**Goal:** a game that plays itself headless before it has a single real asset.

**Load:** `game-forge:game-qa-loop` (steps 1 to 5), `game-forge:game-lessons` sections 1 to 3.

1. Folder shape: `sim/` (pure, no DOM, no `Math.random`, no `Date`), `data/`, `render/`, `input/`, `bots/`, `cli/`, `tests/`.
2. Fixed timestep; state is plain JSON; named RNG streams; events are the render contract; one input path shared by browser, CLI and bots.
3. A CLI with exit codes (0 ok, 1 assertion failure, 2 usage, 3 game rejected the command), a `validate` command, and a `render`
   command that drives the real renderer in headless Chrome. Order it in the first hour, not the third week.
4. Bots in tiers (a smoke bot first, then skill tiers); URL dev params that jump to any scene.
5. A one-heavy-job lock (`game-lessons/scripts/heavy-lock.sh`) before a second agent exists.
6. Write the definition of done now and give it to every agent: tests green, build green, `validate` 0 errors, a JSON script covering the feature, bots clean over 50 seeds, a render PNG opened and looked at.

**Gate (measured):** `purity-check.mjs` exits 0 on `sim/`; replaying `(seed, command log)` twice gives the same state hash; a
bot run of the vertical slice finishes with 0 timeouts; the browser state hash equals the Node hash at a mid-run tick.

**Traps:**
- Cross-engine drift: `Math.sin/cos/atan2/pow` differ in the last bits between engines. Ban them in the sim and test the ban.
- A bot that plays unlike a human lies. A run cap of 900 s read a 0% skilled win rate that was 45% at 2,400 s. A zero is a claim about your harness.

## Phase 2. Data-driven content

**Goal:** every unit, item, level and wave is a row of data that a validator can reject.

**Load:** `game-forge:game-lessons` section 1 items 7 to 10.

1. Content as data; behaviour as a string key into a registry. Pre-populate the registry index files so parallel builders never edit the same file.
2. `validate` checks ranges, dangling references, unregistered behaviour keys, tier counts, unreachable spots.
3. Damage math with named additive buckets and capped sources from day one; new mechanics get bot support the same day.
4. Make a test that fails when any placeholder texture key shadows a real one.

**Gate:** `validate` exits 0 over every content row, and a feature test runs across EVERY row, not only the one you built.

**Traps:**
- A feature defined for one row only (an ultimate meter that never appeared for four of five heroes). Test the whole table.
- Hand-editing generated data. Drafts are the source; the engine file is generated.

## Phase 3. First playable with placeholders

**Goal:** the full loop from title to win/loss, ugly, with every missing asset visibly missing.

**Load:** `game-forge:game-qa-loop` (rungs 1 to 5 of the proof ladder), `game-forge:art-waves` section 11 (placeholder guard).

1. Primitive shapes and flat colour for art, silent audio hooks, system font text. Placeholders must be loud in dev (a magenta tint, a console warning), never silent.
2. Get an owner playthrough as early as the slice survives it. A bot cannot replace a human first evening.
3. Round structure for agents: an architect agent (contracts, CLI, an ownership table) and a designer agent (GDD) first, then folder-owned builders (see the Agent team workflow below).

**Gate:** a bot plays title to end screen over 50 seeds with no crash or softlock, a human has played it once and their verbatim notes are in the project doc.

**Traps:**
- Rewards with no art or feedback read as bugs ("invisible heal" was stair rooms with no heal pedestal art).
- Deciding the art style before anything is playable. You will redo the slice's layout anyway.

## Phase 4. Art direction and the taste file

**Goal:** a style the owner has actually chosen, written down, and a measuring instrument for it.

**Load:** `design-forge:art-department`, `game-forge:art-waves` sections 1, 7 and 8.

1. Show one style sample first, then a few, then pick. Record the owner's words in the taste file (LOVES / HATES / ALLOWS / WANTS, dated, with the quote; superseded entries stay, marked).
2. Palette file and `palette-audit.py`; calibrate `art-measure` limits from the owner's own good and bad examples (`calibrate-thresholds.py`), never hand-tuned.
3. Decide the art route per asset type: 2D waves from an image model, 3D baked to 2D sprites, or a mix (phase 5).
4. Read the licence of every generator before its output is allowed to ship.

**Gate:** a taste file exists with at least one dated owner verdict per LOVES and HATES; `palette-audit.py --strict` and `art-measure` both run on a real screenshot of phase 3.

**Traps:**
- A style rule that lives only in someone's head. It gets re-litigated every wave.
- "Free" is not "shippable": the best local image model is research-licence (`game-forge:local-models`).

## Phase 5. Art production: waves, 3D sprites, local 3D, local models

**Goal:** every asset type in the first slice has real art through a repeatable pipeline.

**Load, by need:** `game-forge:art-waves` (2D from an image model), `game-forge:sprite-pipeline-3d` (characters in 8 directions from a 3D model), `game-forge:local-3d-gen` (concept art to mesh at $0), `game-forge:local-models` (free local images, TTS, music), `design-forge:photo-to-3d-loop` (a real object from photos).

1. Pre-flight every request: is it really a 2D asset? Animation strips for a 3D character are something an image model cannot do; bake them.
2. Build the sprite pipeline against the free stand-in mannequin before any model exists, then feed real meshes (default generator: Pixal3D; Hunyuan3D is out on licence for a worldwide release).
3. One heavy job at a time. Log every paid call; stop at a cap; price the first call before batching.
4. Return check on every returned batch the same turn: canvas size, baked background, one-sided alpha, names against the manifest.

**Gate:** per sprite pack, the `sprite-pipeline-3d` gates exit 0 (height and feet registration across directions, loop seam, penetration); per 2D wave, the return check and `art-measure` pass; `palette-audit` on in-game shots is under the limit you calibrated.

**Traps:**
- Letting a builder loosen a gate to pass. Builders report failures with numbers; only the owner moves a limit.
- Image-model idle loops that "boil". Use one still frame plus a runtime breath.

## Phase 6. Levels and backgrounds

**Goal:** levels that are data a script can lint, backgrounds that are a stack of measured layers.

**Load:** `game-forge:levels-and-backgrounds`.

1. Roguelite: room templates as ASCII drafts built by script, a biome plan, wave budgets. Tower defense: path control points, pad table, a guide render for the painter, a wave DSL.
2. Layers: backdrop, haze, floor, depth-sorted props, one centrepiece per room, foreground silhouettes, hand-placed light points.
3. Measure what a prompt cannot promise: counts (`measure_slots.mjs --expect`), seams (`heal_seam.mjs`), pad-to-road distances (`td_level.py check`).

**Gate:** room or level `check` exits 0 for every file; seam metric under its gate on every tiling asset; bots clear every level inside the target band (not by playing it yourself).

**Traps:**
- A closed rectangle reads as a box. Start with void, diagonals and bridges so the painted world shows.
- Do not tune waves by playing. Set targets per bot tier, then bisect.

## Phase 7. Typography and UI

**Goal:** text that reads at the real target size, loads without blocking boot, and a UI usable with a pad alone.

**Load:** `game-forge:typography`, `game-forge:game-lessons` sections 5 to 7, `design-forge:design-audit` for any HTML surface.

1. Pick the route per text role (stock webfont, an own font, or lettering from an image model); bundle fonts for offline play.
2. Copy the leader's layout from your frame-based spec. One UI base class that owns focus and the prompt bar; card text layout is a pure function tested at every item x rarity x level.
3. A clarity pass: one word, one meaning, plain player units, every number on screen checked against the sim.

**Gate:** text floor met at the target resolution (we used 28 px on a handheld target); `build_hand.py` ink coverage >= 99.5% and drift <= 0.01 em if you use the pen effect; first-play bytes under the budget you derived in phase 10; every screen usable with the pad alone.

**Traps:**
- A font that blocks boot. Self-host it and name a fallback stack.
- The same word for two mechanics (five collisions in one game). A banned-words test for engineer terms catches the rest.

## Phase 8. Audio and voice

**Goal:** music, voice and sound that were planned, priced, licence-checked and measured before they were generated.

**Load:** `game-forge:game-audio`, `game-forge:local-models` for free placeholders.

1. Cast every voiced character on paper first: spec, measured pitch audit, cheap auditions, a 2-line gate before any bulk generation.
2. Cost plan and licence check before spend. A pay-as-you-go plan did not carry a commercial licence on the day we checked; confirm in writing.
3. Music per area, boss, phase, title: pin tempo, time signature and key; cut loops on the beat grid; export ogg and m4a.
4. A Web Audio engine that starts after the first user press and stops when the tab is hidden.

**Gate:** `lufs-check.sh` exits 0 (music -16 +-0.5 LUFS, true peak <= -2 dBTP); loop seams, BPM and key logged per track; no console autoplay error on a cold browser; a human has listened to every shipped track at least once and the unheard ones are listed.

**Traps:**
- Generating a full line set before the voice passed the 2-line gate.
- Local TTS auto-falling through to a worse voice without a message. Log which voice actually spoke.

## Phase 9. Feel, juice and clarity passes

**Goal:** every input answers in under 100 ms, every attack is readable, nothing glowing is still.

**Load:** `game-forge:game-lessons` sections 3, 4 and 7 and `references/game-feel.md` there.

1. Hit-stop and shake live in the sim or are driven by sim events; effects are render-only and never change a hitbox.
2. Every enemy attack gets a body wind-up and a ground telegraph that ends exactly when the wind-up does.
3. Settings honoured everywhere: shake slider, flashes toggle, reduce-motion. Rumble is a bonus, never the only feedback.
4. Ambient motion on every screen the player lingers on, from one update source with a phase offset per instance.

**Gate:** a scripted run asserts the hit-stop and telegraph timings from the spec table; reduce-motion makes the ambient layer static (a screenshot pair); p50 frame time is unchanged with the ambient layer on.

**Traps:**
- Hit-stop that does not pause everything it implies (telegraph timers kept running).
- A hit flash that outlives the sim (white blobs after a pause). Cap it in wall clock.

## Phase 10. Perf budgets tied to real targets

**Goal:** a budget table where every number traces to a real device, store or review rule.

**Load:** `game-forge:game-qa-loop` step 8 and `references/perf-playbook.md`.

1. Write each budget as number, measurement command, kind (hard gate, warning, info). A cap you chose yourself is warn-only.
2. Measure paired runs back to back; compare p99 and frames over 33 ms. Headless fps comes from a software GPU, so it is never the game's fps.
3. Split load into phases (title, hub, next area), pre-bake hitchy work under the title card, warm shaders.

**Gate:** each hard budget has a command that exits non-zero (we kept: 60 fps at 1280x800 in a busy fight on the handheld, texture memory peak under 1.5 GB over a 20-room soak, boot to title under about 3 s, install under a 2 GB sanity line); the table is in the project doc.

**Traps:**
- Web-port caps (file counts, first-play MB) left on after the plan became Steam-first: they cost a lean-engine build and a lossy asset ladder.
- Optimising the sim when the frames went to hitches. p99 fell from 77-99 ms to 27-30 ms from room pre-baking, RenderTexture pooling and shader warm-up, not from sim work.

## Phase 11. Playtest and the feedback loop

**Goal:** a standing loop that turns a player's words into a failing repro and then a kept regression test.

**Load:** `game-forge:game-qa-loop` steps 7, 10 and 11.

1. Run a bug hunt (bot sweeps, a long soak, scripted browser sessions) then a fresh-eyes human playtest with a ranked top 10.
2. Intake verbatim; triage into defect, tuning, design, unactionable; group by root cause; reproduce as a FAILING script first; fix; verify with before and after shots; reply per item in the reporter's words; commit the repro.
3. Report what you ran and what it printed. A gate you could not run is reported as not run.

**Gate:** zero open crash or softlock bugs from the sweep; every feedback item has a reply and every defect has a committed repro.

**Traps:**
- Upgrading a tuning note into a defect hunt.
- Quoting a count from memory. Re-read the instrument's raw output before declaring any number.

## Phase 12. Trailer and highlight reel

**Goal:** a short, honest cut of real gameplay for the store page and for sharing.

**Load:** `game-forge:game-qa-loop` step 12 and `references/highlight-reel.md` (the simple route: `record-reel.mjs` + `cut-reel.sh`).

Two deliverables, never mixed: a **demo** is the raw uncut playthrough (no cards, no text, 720p, under about 35 MB); a **trailer** is a
produced cut and is only made when asked. For a trailer, the method we used (a rough cut v1 built by a small script plus a
frame-by-frame capture tool in the roguelite repo; read, not vendored, because it is tied to that game's scenes and paths):

1. **Capture footage deterministically.** Boot the game with a capture flag, install a virtual clock before the game loads (replace
   `requestAnimationFrame`, `performance.now` and `Date.now` so time advances exactly 1/60 s per driver step), run a fixed seed, step
   N frames, screenshot each frame as high-quality JPEG, then encode with ffmpeg (60 fps, x264 CRF 14). Result: perfect 60 fps
   footage however slow the software GPU is, and two runs of one scene give identical frames. One clip per beat (combat, hub, a
   choice screen, a boss intro), driven by scripted key presses. This is a heavy job: take the lock.
2. **Paper title cards.** A paper texture resized to 1920x1080, with the title typeset on it by ImageMagick in your display font
   (never ask an image model to draw the text). One card early as a title, one at the end with the call to action ("demo coming soon").
3. **Cut list as data.** A list of `(kind, source, start, duration)` rows: clips and cards interleaved, the strongest combat first, a
   quieter exploration middle, the end card last. Total about 60 s.
4. **Crossfades.** One ffmpeg `filter_complex`: trim and `fps=60` each segment, chain `xfade` with a 0.3 s fade, each offset = running total minus 0.3.
5. **Game music, not stock.** Gameplay music under the footage, faded out ahead of the title card, then the game's own title piece started from its
   first bar at the card's time, faded in 0.6 s and out over the last 3 s; `amix` the two with `normalize=0`.
6. **Label rough cuts** with a "ROUGH CUT, NOT FINAL" overlay badge, write the timeline to a JSON next to the output, print length and size.
7. Encode 1080p x264 CRF 18 with AAC 192k for the master; make the 720p under-35 MB copy for chat.

Not run for this skill: the capture tool and the cut script were read, not executed. The method is stated as the source files do it.

**Gate:** `ffprobe` shows the target length and resolution, the file size is under its limit, and someone opened the file and watched it with sound.

**Traps:**
- Real-time screen capture on a slow software GPU gives stutter. Drive the clock instead.
- Music you do not have the licence for. Use the game's own cleared tracks.

## Phase 13. Shipping: desktop wrapper, store page, demo, disclosure

**Goal:** a build that runs on the target OS, a store page the platform accepted, and honest AI disclosure.

**Load:** `game-forge:game-lessons` section 10 and `references/shipping.md` there.

1. Start the paperwork in week 1: store clocks start when the owner pays and finishes forms, and owner-blocked items are the critical path.
2. Desktop wrapper (Electron: the same Chromium you tuned on). Saves as JSON files, not `localStorage`; bundle fonts.
3. A Windows build you never ran on Windows is not a build: a CI smoke test launches it, writes and reads a save, and fails on console errors.
4. Demo as a separate free app; Coming Soon page public early; one festival slot per game, ever. Re-verify every store rule and date before acting.
5. AI disclosure is part of the build: check each generator's commercial licence before the page goes live, disclose plainly, do not market it as "the AI game".
6. Open-sourcing the repo: a fresh squashed snapshot, a secret scan plus a hand grep for paths, emails and cost logs, and an independent audit.

**Gate:** the packaged build launches on a clean machine of the target OS with a save round-trip; the store page is submitted; the disclosure answers are written and match the licence log.

**Traps:**
- Uploading a 127 MB build over a slow link (HTTP 524, six failed deploys one night). Deploy from version control.
- Cost logs in a public repo exposed account balances.

---

## Agent team workflow

All from `game-lessons/references/agent-workflow.md`; read it before dispatching more than one agent.

- **Roles:** the human owner decides taste and moves gates. A conductor session (the main agent) dispatches, integrates, deploys, and checks every claim. Builders build in worktrees. Reviewers review and change no files.
- **Builder and reviewer are different agents.** Builders are build-class; the reviewer is judgement-class and reads the diff cold. One review before main, one fix check, then only serious bugs block; small findings go in a follow-ups file (unbounded review loops return endless nits).
- **Worktrees:** one per builder, branched from an integration branch, dependencies symlinked (never `npm install` in a worktree, and symlink EVERY nested `node_modules`). Never edit the main checkout.
- **Git discipline:** commit explicit paths, never `git add -A` (one sweep committed 557 files); builders never push, merge or deploy; generated outputs have one owner, the integrator.
- **One heavy job at a time:** one Blender, one headless Chrome, one build across all worktrees (two slots on 32 GB), behind `heavy-lock.sh`. Check load and swap before a fan-out (nine parallel agents hit load 38 and 12.6 GB swap). Never `pkill`/`killall`; close only PIDs you started.
- **Main-first merges:** the integration branch moves daily; the conductor merges, runs the gates in a clean worktree, and looks at the shots. A builder's output is a claim: `ls` it, run it. Push daily (83 unpushed commits is a backup problem).
- **Folder ownership:** an ownership table in the architecture doc, registry index files pre-populated, additive-only schema changes, and engine-hook requests filed in a requests folder rather than patched in.
- **Disk:** the disk hit 0 free more than once from agent repo copies and worktrees. Check free space before dispatching builders and before big downloads.

## Adding a lesson

This tutorial stays alive by appending, not rewriting. When a failure costs real time, add it to the owning phase's **Traps** (or, if it is
cross-cutting, to `game-lessons` Traps) in this form:

```
- **<Rule, in the imperative or as the mistake named>.** <The failure that earned it, with a number, a file or a count>. (<YYYY-MM-DD>)
```

Rules for a lesson: one rule per bullet; the failure must be real and one you can point at (no hypotheticals); include the receipt
(a measurement or a count) or say "no measurement"; date it with the day it happened; if it contradicts an older lesson, edit the
older one to say "superseded <date> by ..." instead of deleting it; keep game-specific names out. If the lesson needs a script, add the
script to the sibling skill that owns the phase, not here.

## Licences and cost

- This skill has no scripts and no dependencies. Its cost is the sum of the sibling skills it points to; the free route covers a first playable (local models, local 3D, headless Chrome), and every paid step (image API, voice, music, 3D credits) has a cap and a dry-run in its own skill.
- Spend we actually saw is listed in `game-lessons` (Licences and cost). Over about $1, dry-run and ask the owner.
