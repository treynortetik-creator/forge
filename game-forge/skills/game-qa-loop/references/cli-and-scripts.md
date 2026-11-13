# The game CLI and its script format

Both games shipped the same CLI shape (the roguelite's was the second one, copied from the tower-defense game's).
Names below use `bin/<game>`; substitute your own. Everything here was read from the two games' `design/CLI.md`
and `src/cli/*.ts`.

## Contract

- **Session = (seed, hero/level, mode, run-length-encoded input log) in one JSON file.** Every call replays the
  log through the sim from tick 0, so an agent can play step by step across separate shell calls. The file also
  stores a state hash and tick; loading refuses a file whose replayed hash does not match ("Session replay
  mismatch": a determinism bug, or content changed since the session was made). Default path `.<game>-session.json`,
  override with `--session <file>` or an env var.
- **One input path.** The CLI, bots, scripts and the browser all feed the sim the same input frame (roguelite:
  move vector, aim vector, held buttons, latched presses; tower defense: a command list). That is why a bot run
  replays exactly in the browser.
- **Time.** The roguelite sim runs at 60 ticks/s (`step 60` = one second); the tower-defense sim at 30 ticks/s,
  each play command advancing 1 tick so the result is visible at once.
- **Output** is human text by default, `--json` everywhere for machines.
- **Exit codes:** `0` ok, `1` assertion or validation failure, `2` usage error; the tower-defense CLI adds `3` =
  the game rejected the command (not enough gold, on cooldown). A distinct code for "game said no" lets a script
  tell a bug from an illegal move.
- Log entries are run-length encoded: identical consecutive frames collapse into `{n, f}`, commands attach to the
  first tick of an entry. Inputs are quantized before logging so the file replays byte-identically.

## Commands (roguelite flavour; the tower-defense one swaps play verbs for build/upgrade/sell/wave/hero)

| Command | Use |
|---|---|
| `new --seed N [--hero h] [--room <template> [--biome N]] [--hub]` | start a session; `--room` starts directly in one room (jump to a boss in one line) |
| `step N [--move x,y] [--aim x,y] [--hold a,b] [--press a,b]` | advance N ticks; a press fires on the first tick only |
| `input <frames.json>` | append scripted frames: `[{"n":30,"move":[1,0]},{"n":1,"press":["dash"]},{"choose":0}]` |
| `choose <i>` | take option i while a choice is open |
| `run --until C [--bot b] [--max SEC]` | run until `clear`, `choice`, `doors`, `room=N`, `t=SEC`, `dead`/`end`; without `--bot` the hero stands still |
| `state [--json]` | room, wave, hero numbers, enemies with AI state, pickups, doors, pending choice |
| `script <file.json>` | scripted playthrough with assertions; exit 1 on the first failure |
| `validate` | content sanity (hit shapes, behaviour keys, room reachability, spawn counts, prerequisite chains...); exit 1 on errors |
| `bot --seeds 1..100 [--bot b] [--hero h] [--full] [--json]` | many headless runs, aggregate or one line per seed |
| `sweep`, `gifts`, `boss`, `room`, `ttk` | balance reports (see bots-and-balance.md) |
| `render --scene run --seed 3 --t 55 --bot basic [--live 400] [--session] --out x.png` | screenshot of the REAL renderer (heavy) |

`run --until` is the workhorse: "run until the room is cleared with this bot" is one line, and `--max` turns a
hang into `timeout` instead of an infinite loop.

## Script format

```json
{ "name": "bolt spends ammo, bot clears room 1", "seed": 4, "hero": "h1",
  "steps": [
    { "n": 1, "expect": ["hp==110", "ammo==3"] },
    { "n": 1, "aim": [0, -1], "press": ["cast"] },
    { "n": 30, "expect": ["ammo<=2"] },
    { "until": "clear", "bot": "basic", "max": 150, "expect": ["roomsCleared==1", "enemies==0"] }
  ] }
```

- A step is a frame spec (`n move aim hold press choose`), a run (`until` + optional `bot` / `max`), or either with `expect`.
- `expect` is a string, a list, or an object (`{"lives": ">=15", "result": "won"}`). Operators `>= <= > < == !=`.
  `==` and `!=` compare as strings, so `phase==combat` works.
- **Metrics are a closed list.** An unknown metric name is a usage error (exit 2), not a silent pass. Roguelite
  metrics: `hp maxHp ammo dash x y phase result roomNo depth room tick t enemies kills roomsCleared silver
  graveDust gifts damageTaken damageDealt invuln wave doorsOpen choice`. Tower defense adds `hero.<def>.level`,
  `spot.<id>.tier|tower|spec|empty`. Add a metric whenever a bug needs one; it is one line in the CLI.
- The tower-defense format has `{"do": "build s2 gargoyle"}` steps (any play command), and a rejected `do` fails
  the script unless the step says `"allowReject": true`.
- Scripts live in `tests/scripts/`, and ONE vitest file runs every `*.json` in that folder, so each new regression
  script is picked up by `npm test` with no registration:

```ts
import { readdirSync } from 'node:fs';
import { runScript } from '../src/cli/main';          // your CLI's exported runner
describe('cli scripts', () => {
  for (const f of readdirSync('tests/scripts').filter((x) => x.endsWith('.json'))) {
    it(f, () => { expect(runScript(`tests/scripts/${f}`, true)).toBe(0); });
  }
});
```
  (The tower-defense game also keeps a `should-fail.json`: a script that must fail, so the harness itself is tested.)

## Screenshot harness (`render`)

- Serves a fresh production build from a temp dir, NOT the dev server: other agents' edits trigger HMR reloads that
  navigate the page mid-shot. `--dev` opts back into the dev server for speed.
- Launch flags used by every browser tool in both games: `--no-sandbox --enable-webgl --ignore-gpu-blocklist
  --enable-gpu-rasterization --disable-background-timer-throttling --disable-renderer-backgrounding
  --autoplay-policy=no-user-gesture-required`, viewport 1920x1080 at deviceScaleFactor 1, system Chrome through
  `puppeteer-core` (`CHROME_PATH` to override). No bundled browser download.
- Query params it passes: `scene`, `seed`, `bot`, `t` (fast-forward seconds), `paused` (1 unless `--live`), `mute=1`.
  The sim is fast-forwarded to `t` and paused, unless `--live <ms>` keeps it running so FX and swings show.
- `--session` hands the CLI's input log to the page (`window.__BOOT`-style global set before load) so the browser
  replays exactly what you played. It prints the **browser's state hash**; compare with `state --json` after the
  same input to prove Node and Chrome agree.
- The harness collects `console` lines and `pageerror`s into a `logs` array on the handle: print them, a throw in
  an event handler is otherwise invisible.
- The in-page handle (`window.__<game>`): the Phaser game, the controller with the live sim state, an event
  subscription, a `hash()`, and `ready`. Harnesses wait on `window.__x.ready`.
