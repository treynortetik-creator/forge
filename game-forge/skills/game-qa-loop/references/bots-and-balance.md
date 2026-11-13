# Bots, tiers and balance sweeps

## Why bots at all

A bot is the only player that can run 400 seeds before lunch. It does three jobs: a **smoke test** (does a full
run finish without a throw or a softlock), a **balance instrument** (win rate, damage per room, time to kill),
and a **repro generator** (a failing seed is a deterministic bug report). It is not a substitute for a human:
the fresh-eyes playtest (bug-hunt-and-playtest.md) found that a human-like keyboard player died in chambers 1-3
on 4 of 5 runs while the `average` bot cleared the same biome losing 7 HP. The curve was a cliff at the start,
and only the human saw it.

## Bot registry

One file registers bots; the CLI (`--bot`), the browser (`?bot=`) and the sweeps all use the same registry.
`basic` is the smoke-test bot (an alias of the `skilled` tier in the roguelite, so a default run is deterministic and
decent). The tower-defense game's bots differ by build policy: `basic` (fixed order), `greedy` (best estimated
value per gold), `hero` (the smart one, also plays the hero), `frontline` (how most humans play), `novice` (random
towers, few upgrades, no specs), `random` (valid random actions, the fuzzing floor).

## Skill tiers from perception, not from aim cheats

The roguelite's tiers (`novice average skilled perfect random`) make dodging EMERGE from a perception model, so
telegraph length and any "reaction" perk change bot results with no extra code. A threat is "seen" at
`t_start + RT + hick * log2(threats + 1)`, with `RT ~ LogNormal(rtMed, sigma)`; with probability `lapse` it is
never seen. Measured parameters from `src/bots/tiers.ts`:

| Tier | rtMed ms | sigma | hick ms/bit | lapse | dash err deg | aim err deg | attack uptime |
|---|---|---|---|---|---|---|---|
| novice | 430 | 0.30 | 120 | 0.08 | 35 | 12 | 0.55 |
| average | 330 | 0.25 | 80 | 0.025 | 20 | 7 | 0.75 |
| skilled | 250 | 0.20 | 40 | 0.006 | 8 | 3 | 0.95 |
| perfect | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| random | plays blind: random inputs | | | | | | 0.5 |

`perfect` is the **oracle** (reads everything instantly): it answers "is this dodgeable at all", not "is it fun".
Other tier knobs: chance to cancel an action with a dash when threatened, chance to hit a perfect release window,
gift-choice softmax temperature, door-choice policy, whether it shops and breaks urns. The file's header says:
**a tier change is a balance change; recalibrate only from human data.** Device profiles (pad vs keyboard+mouse)
adjust aim and dash error the same way.

## Sweep statistics

`sweep` runs hero x bot cells on **paired seeds** (every cell sees the same seeds) and reports win % with a
**Wilson 95% CI**, median depth / clear time / damage-per-room with **bootstrap CIs**, PASS/WARN/FAIL against a
written target band, hero spread vs the cell mean, and a **McNemar** test vs the best hero; `--strict` exits 1 on
any FAIL. `gifts` is a forced-inclusion outlier report: each item forced at room N vs the same seeds with it
banned, a power score over the window, robust z within the slot, flagged OP (z > 2.5) or Trap (z < -2.5).
`boss` reports fight length, uptime, damage taken, deaths and hits by attack; `ttk` runs a dummy duel.
Speed (from the CLI docs' sample output, not re-measured): `bot --seeds 1..100` took 2.5 s in the roguelite; the
tower-defense game did 200 runs in 11.2 s, about 9,500x real time.
Write the target band down BEFORE the sweep ("skilled, no meta-progress, wants 10-25% wins").

## What the sweeps found (receipts)

- **QA pass after round 2:** 50 seeds x 5 heroes at `skilled`: 0 wins for every hero against a 10-25% band, so all
  FAIL. One boss caused about half of all deaths, and per-room damage was 2-5x the band. Result: the serial
  balance phase starts with `boss` and `room` on that fight, nothing tuned during QA.
- **Timeouts are a softlock detector.** 5 of 250 bot runs timed out; cause: an actor's burrow mound carried it out of
  the room (y grew to millions) so the room never cleared. Fix: put any actor outside the room or inside rock
  back on the nearest floor. After the fix, 0 timeouts. Treat every `timeout` result as a bug until proven otherwise.
- **Bots can break themselves.** Bots attacked right after a dodge dash; the press became a dash attack that ends the
  dash i-frames mid-telegraph. Fix: bots hold attacks until the dodge has played out. When a bot dies in a way no
  human would, suspect the bot first.
- **Invariant sweeps.** The bug hunt ran 450 runs (5 heroes x 3 tiers x seeds 1..30, 2 workers, niced) with
  invariant checks, plus a 60 sim-minute soak in god mode. Invariants are cheap, hard to fool and find
  data bugs (a split enemy child getting 135 HP instead of 31 outside its home biome, a latch status that never expires).
- **Resume equality.** Snapshot at room 3, restore, continue with the same inputs; the hash must equal the
  uninterrupted run. The hunt found the restore dropped every meta-progression option, so the runs diverged at
  tick 660. This check needs a non-trivial meta preset: with an empty meta both runs matched and the bug hid.

## Workers

The sweep runs on worker processes; keep them niced and capped (the bug hunt used 2). A sweep is CPU-bound and
headless (no Chrome), so it is NOT behind the heavy lock, but check `uptime` first.
