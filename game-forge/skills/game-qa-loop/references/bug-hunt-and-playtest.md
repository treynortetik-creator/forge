# Bug hunts, fresh-eyes playtests and QA passes

Three report styles the roguelite used, with what each caught. Read them as templates for your own.

## 1. Bug hunt (read-only, evidence-tagged)

Method of the 2026-10-15 hunt (nothing was fixed during it): two read-only code reviewers (one on render/ui/input/audio,
one on sim/save/meta/bots), a 450-run bot sweep with invariant checks, a 60 sim-minute god-mode soak, two scripted
headless-Chrome sessions (title > hub > run > clears + gifts through the UI > pause > settings > back > die > hub >
run 2 > gamepad), and a save/resume + save-code harness. One Chrome at a time.

**Tag every finding with how you know it:** `BROWSER` (seen live in Chrome, shot attached), `NODE` (reproduced with
a script or the CLI), `CODE` (found by reading, no repro yet). Rank into crash/softlock, player-visible wrong, feel/polish,
tooling. Each row: bug, repro, evidence, likely cause, owner. Counts from its own table: 6 crash/softlock, 27
player-visible, 12 feel/polish, 6 bots/tooling. A later pass marked each row FIXED with a commit, PARTIAL or DEFERRED
with the reason.

Bug classes it found (generic shapes, each worth a grep in your own game):

| Class | Example shape | How it was caught |
|---|---|---|
| menu stack / scene lifecycle | "Back" from a sub-menu freezes the game: sim paused, no menu, Esc does nothing; from the title it leaves a black screen | BROWSER (active scenes and `paused` flag read through the debug handle; the tick stayed constant over 3 more Esc presses) |
| stale state keyed on an old object | an offer screen stays open after the sim resolved the choice a different way (reroll) | BROWSER via a bot; the offer showed an exhausted-reroll button while the sim choice was null |
| restore drops options | resuming a saved run loses all meta-progression options, run diverges at tick 660 | NODE (snapshot/restore/continue vs uninterrupted, with a non-empty meta preset) |
| merge type-guard | a saved string value dropped because the default was `null` (type 'object') | CODE + reviewer probe |
| unregistered keys silently ignored | 12 pacts and 9 trinkets pushed mod keys no handler registered, so they did nothing | CODE |
| missing call | trigger plates emitted a burst but never damaged anyone | CODE + probe (HP 62 -> 62) |
| double increment / two owners of one moment | boss encounters counted twice; each boss got two intros; offer opened twice in one frame | CODE; BROWSER logged "Cannot pause non-running Scene" 2-4 times every session |
| timer-order races | a fade cancelled by a later-registered timer that ran first (death banner faded early about 70% of the time) | CODE |
| lingering state across rooms | a status with duration -1 never cleared; zones carried to the next room at old coordinates; queued summons spawned after the boss died | CODE |
| data mismatch | two places each added a support wave, so some fights got two | CODE |
| depth/gate computed from stale value | entry rooms of later biomes ignored the difficulty gate | CODE |
| cheap perf bugs | a save read (localStorage + JSON + CRC) about 7 times per frame; looping tweens leaking on every menu close | CODE |
| menus drawn under the HUD | the health bar drew over "Paused" because scene order put the HUD on top | BROWSER shot |

Evidence lesson: a `CODE`-only finding is a hypothesis. Several were later confirmed by a probe, and the fixes
that stuck all had a regression test.

## 2. Fresh-eyes playtest (report only)

An agent plays the real build through the real input path (puppeteer key and mouse events) with ONE fresh browser
profile kept for the whole session, so saves, deaths and unlock spends carry over like a real first evening.
Method that worked: play 5 runs by hand with a crude "player" loop; for the 6th, hand ONLY the fighting to a
mid-tier bot (swapped onto the controller mid-run and removed after each clear) so every menu, offer, door, shop and
settings screen still gets exercised manually. Use the URL jump params once at the end to reproduce a bug,
never to progress. Number the screenshots and cite them. Rank the top 10 by pain, each with priority (P0/P1/P2),
problem, fix, files and size.

What it caught that no sweep could:

- **P0:** forcing a controller prompt family disabled keyboard movement and mouse aim and persisted (reproduced twice
  plus a control run where Automatic mode moved 1504 -> 1286 and the override did not move at all). Cause: "which
  prompts to draw" and "which device is live" were one variable.
- **P0:** the first three rooms punished a new player before they could read anything (idle 3 s in room 1 = 54 -> 14 HP).
  The bot cleared the biome losing 7 HP, so the curve was a cliff at the start, not overall. Fix scope: onboarding only
  (min depth for trap rooms, spawn distance, a first-attack hold), then re-run the sweep, leave deeper rooms alone.
- readability: an ambient bark rendered as a big modal box with a confirm glyph; a panel covering the reward chips
  you are meant to plan with; a landmark painted over a door so it read as blocked; text collisions.
- time sinks: the walk from spawn to the descend point after every death was 16-22 s.

Also list "what works (keep)". It stops the next pass from "fixing" the good parts.

## 3. Serial QA pass (definition of done on the integration branch)

Run after every builder has stopped, one headless Chrome at a time. Table of Check | Result | Numbers:
`npm test` (46 files, 500 passed, 1 skipped), build, `validate`, determinism (browser hash == Node hash;
snapshot -> restore -> continue == uninterrupted), bot runs (50 seeds x 5 heroes), fps in a heavy fight and at a
boss (avg 56-58 fps, p95 about 19.8 ms, worst 85-97 ms), first-play download and file count. Then "fixed during this
pass" (the softlock found by timeouts, a bot flaw, placeholders that stayed after art streamed in, a 70-120 ms floor
prebake now only run behind menus), the bot table, every screenshot with a one-line judgment ("opened and looked
at"), and a ranked top 15 (bugs, then readability, then polish). Nothing is tuned in a QA pass: balance numbers
are reported for the balance phase.

Definition of done used by every builder of the tower-defense game: `npm test` green, `validate` 0 errors, a
`tests/scripts/*.json` covering the feature passes, a render screenshot was looked at, fps still 60 on the stress
level if render was touched.

## Triage kinds (for player feedback)

| Kind | The game... | Needs | Who decides |
|---|---|---|---|
| Defect | does something nobody designed | failing repro, then a fix | the builder |
| Tuning | does what the code says, numbers feel wrong | a numeric target, then a value change | the owner |
| Design | works as designed, design unwanted | a change to the plan | the owner |
| Unactionable | "the shop is weird" | one specific question back | the owner |

Never invent a metric for a taste question; label it NEEDS OWNER and attach screenshots with options.
