# The agent workflow: how two people and many agents built two games

Receipts are from the tower-defense game (started 2026-09-27) and the roguelite (started 2026-10-15). "The owner" is the human; "the conductor" is the main agent session that dispatches, integrates and deploys.

## 1. Round structure

| Round | Who | Output |
|---|---|---|
| 1 | an **architect** agent (engine, contracts, CLI, ARCHITECTURE.md with an ownership table for round 2) and a **designer** agent (GDD plus sibling docs: heroes, enemies, rooms, balance, feel) in parallel; an art-director agent in parallel for the look | a vertical slice that builds, a CLI that plays it, bots that play it (roguelite round 1: 34/34 tests, bot won 98/100 on a 6-room slice) |
| 2 | 4-5 **builders by folder ownership**: content owners (towers, heroes, enemies, levels), UI/meta, juice/audio/art integration; the architect is resumed as engine owner and services requests | each builder files engine-hook requests in `design/requests/<area>.md` |
| 3 | integration + QA + deploy: the conductor (or the architect resumed) runs the full definition of done serially | a shareable link |
| 4+ | playtest, owner feedback, balance, polish passes, each a small package | |

What made round 2 safe: **an ownership table** (who edits which folders), pre-populated registry `index.ts` files nobody else edits, "additive optional fields only" on schema/state/event types,
and "need an engine hook? ask, don't patch `systems/`". The tower-defense round 2 (dispatched 17:50) ran 4 Opus builders in parallel on folders: towers were done by 18:30, UI/juice at 18:55, heroes at 19:01.

**Request files** have a status key (OPEN, WORKAROUND, DONE, WONTFIX) and the engine owner appends the commit that closed each one. A builder that needed `onSoldierDeath` shipped a stopgap in its own files, marked WORKAROUND, and removed it when the hook landed.

## 2. Worktrees and git discipline

```bash
git -C <main-checkout> worktree add <project>-wt/<name> -b wp/<n>-<slug> <integration-branch>
cd <project>-wt/<name>
ln -s <main-checkout>/node_modules node_modules                 # never npm install in a worktree
ln -s <main-checkout>/tools/art/node_modules tools/art/node_modules   # EVERY nested node_modules, or the tool silently lacks a dependency
```

1. Builders commit **explicit paths** (`git add <owned paths>`), never `git add -A`. Never push, merge or deploy. Never edit the main checkout (read-only for builders).
2. **Generated outputs have one owner** (the integrator). Art packages commit sources only and discard generated output before committing:
   `git checkout -- public/assets/<gen> art/review && git clean -fd public/assets/<gen> art/review`. A full art re-ingest once could drop manifest keys; diff keys against HEAD after any full ingest and stop if any went missing.
3. **Hand-off note** in the last commit body: what changed, gate results (pass/fail per line), screenshots folder, any change requested in a file the builder does not own.
4. **Verify in a clean worktree before a deploy.** A sparse clean checkout run found a test that read gitignored screenshots (fixed with a skip-if); another run found a parse error at HEAD after a merge.
5. Push the integration branch **daily.** A reconcile found 83 commits not on any remote, a backup problem not a git problem.
6. Delete merged worktrees (keep branches). Before deleting, check they are clean. Disk hit 0 bytes free more than once from agent repo copies, 1 GB base worktrees, and temp build dirs.
7. Past incidents behind "explicit paths": an architect's `git add -A` swept another agent's work-in-progress into its commits (nothing lost, but history was wrong); an art commit swept 557 files of pipeline output.

## 3. One review, then merge

- An Opus-class adversarial reviewer before main. **One fix check. Then only serious bugs block.** Small findings go in a follow-ups file, not another round.
- Evidence the limit is needed: a hub redo went through five review rounds; rounds 3 and 4 both scored 7/10 with a fresh set of low nits each time (mirror tint, chevron, pan ghosts, arrival plates). Round 5 told the reviewer to **separate blockers from polish** and passed at 8/10 with no blockers.
- One enemy-art package failed its review and was merged on the conductor's judgment as a net step up (the conductor's own read: enemies still black blobs, one boss unreadable); the next package replaced the method. Merging on judgment is allowed when the failure is named in the log.
- A reviewer's job also includes **doing what the builder skipped**: one review caught that a HUD file was unparseable at HEAD after a merge.
- Reviews must be handed the code, not the conclusion. A fresh-context reviewer anchored on your summary tends to confirm it.

## 4. Output is a claim

`ls` or Read the artifact before calling it done. Receipts:
- A "stopped" agent never wrote the scorecard the conductor reported (the phantom path was already in two files).
- A builder's full run showed 7 failures under load 22; the conductor re-ran the failing files single-worker at load 12 and all 15 tests in 3 files passed, so they were load timeouts, not bugs. Read the load before reading a red suite.
- "The bots 98/100" at slice time became "0 of 250 wins" after bosses were wired. Report with the denominator and the date.
- Visual claims without a PNG that was opened are not proof. Open every PNG you make, at 1x, at the size the player sees (plus 1280x800 for a Deck target).
- A QA note said two portraits "had no glow"; a zoom check showed they did, and the fix prompts were withdrawn the same day. Correct the record out loud.

## 5. Machine limits: the heavy lock

A 16 GB laptop with nine agents hit load 38 on 8 cores and swap 12.6 of 13.3 GB; the owner's CLI lagged ("it looks like your computer is maxing out"). One orphaned `magick montage` ran 16 hours holding 1.2 GB.
- **One of each at a time across all worktrees:** a Blender process, a headless Chrome, a `vite build`. The CLI's `openGame()` does a fresh vite build AND opens Chrome, so every browser tool is heavy.
  On a 32 GB machine: two slots. `scripts/heavy-lock.sh -n 2 -- <cmd>` implements it with atomic `mkdir`, releases on every exit path, never kills anything.
- Before a fan-out: `uptime` and `sysctl vm.swapusage`. Queue if load > 20 or swap > 8 GB. At most two agents on headless Chrome, screenshots, fps runs, full suites, balance sweeps or ImageMagick batches.
- **Never `pkill` or `killall`.** Close only processes you started, by PID. It killed another agent's work.
- Throttle by text: "code and targeted tests only, no Chrome, screenshots, sweeps or builds until load < 12" is a real instruction that worked.
- Two balance workers each launching three sweep workers took the box to load 30; cap workers at 2 and pause sweeps while load > 16.

## 6. Owner feedback triage (adapted from a community plugin's best idea)

Loop: intake, triage, group, reproduce (failing), fix, verify, reply, keep the repro.

1. **Verbatim intake.** Words carry facts: "sometimes" is a seed or timing claim; "after a while" is accumulation (leak, listener doubling, pool cap); "on the preview" vs "in the build" says which deploy; "it used to work" means find the commit.
2. **Four kinds, written down before touching code:** *defect* (nobody designed it), *tuning* (numbers feel wrong; needs a numeric target from the owner), *design* (works as designed, unwanted; changes the plan), *unactionable* (one specific question back).
   Never invent a metric for a taste question; label it NEEDS OWNER and bring options with screenshots. Never silently upgrade tuning into a defect hunt.
3. **Group by root cause.** If a fix closes only one of three reports, your grouping was wrong. Receipts: a "dark screen after menus" report was one dim that cleared only on one event; "invisible heal" was missing stair-room art;
   "the candles often don't appear" was a rite meter defined for only one hero; "doorways don't line up" was east/west doors drawing a north arch.
4. **Reproduce and watch it fail.** A gameplay claim becomes a JSON script with an `expect`; layout becomes a unit test; visual becomes a before-shot with a measured quantity; "sometimes" becomes a seed sweep. A repro that passes first time reproduced nothing; ask for one more detail instead of fixing a guess.
5. **Two failed attempts at one approach: stop and propose 2-3 different approaches.**
6. **Reply per item in his words:** fixed (what he will see), changed (check it; the number and where to look), needs you (the 2-3 options plus a recommendation), could not reproduce (what you tried). Never stay silent on an item. Commit the repro with the fix.
7. **A numeric reading of an ambiguous request can reverse a design.** "Do nerf it" was read literally (make it easier), the balance agent was redirected, and a minute later the owner corrected it ("don't nerf it, sorry"). Ask once when the sign is ambiguous, or state your reading and offer to flip.

## 7. Spend, voice and cost gates

- Paid generation goes through ONE script that logs every call and stops at a USD cap; keys come from `.env` and are never printed. Cap history on the tower-defense art: $10, then $25, $40, $60, each raised by the owner after seeing the work.
- The owner's complaint that a lead voice sounded like "a little British" led to a **plan phase before any spend**: a planner agent per category writes value-per-dollar, cheapest model, retries and an acceptance check; only then does a builder run. Voice work gets a spec, an audition with 3 cheap candidates, and a 2-line gate before bulk (`game-forge:game-audio`).
- That run was stopped twice and restarted with the plan phase added; the stop was cheaper than the spend it prevented.
- Standing spend approvals are recorded with the owner's words and the cap; "relatively inexpensive, not worried" is permission to log and report totals, not to skip the log.

## 8. Pipelines that worked

- **Audit then build then adversarially review, sequentially:** 3 report-only auditors (boss, combat feel, hub/meta/onboarding) -> one builder per audit, run sequentially to protect the box -> an adversarial reviewer -> one fix pass -> a fresh-eyes playtester who plays a full run like a new player -> a fixer and review -> a final integration with the gates.
- **Spike with an honest verdict:** a cut-out rig spike (segment, rig, export GIFs) produced a written "12-16 days to ship all, stills show smeared shards and joint gaps" verdict; the image-model strip path was chosen instead. Time-box spikes and require a verdict document and side-by-side clip.
- **A/B in game, not in a viewer:** a character-quality A/B (3D upgrade vs 2D cut-out rig vs image-gen strips) was judged inside the game at game scale; image-gen strips won at about $0.16 per character.
- **Research agents before building a screen or system:** five researchers (leader teardown, genre landscape, open-source options, balancing math, feel and controller) ran for about 13 minutes at the start; the balancing research found two of our own targets wrong.
- **Cheap bulk agents with a spot check:** three small-model research passes on VFX technique, free resources and AI-VFX, then a stronger model spot-checked and synthesised. Never ship the cheap tier's output as-is.
- **Decision ledger:** log big judgment calls with a falsifiable grading condition written before the outcome.
- **Living project doc per game** (decisions with dates and the owner's words, current state, open items), not session dumps. Every handoff reads it.

## 9. Anti-patterns we paid for

- Dispatching more agents because the box looked idle. The load check decides, not the idle feeling.
- A dozen files owned by "everyone" (manifest, schema). Give each shared file one writer.
- Letting a builder "fix" a gate. It reports; the owner moves gates.
- Calling the integration done without a deploy verification: new bundle name in the live index, the health endpoint, and asset content-types.
- Re-asking closed questions or re-testing killed ideas. Record "decided, with date and words" and do not reopen them.
- Rewriting the plan weekly without re-reading what shipped. See the sprint reconcile in `references/shipping.md`.
