# Test templates for the deterministic core

Generalised from the two games' `tests/` (vitest). Adjust import paths to your sim. None of this was re-run
outside the original repos; treat it as a starting shape.

## 1. Purity: the sim may not touch the outside world

The roguelite's `purity.test.ts` scans every file under the sim and data folders (comments stripped) and fails on
the banned names. Two layers:

```ts
const code = (f: string) => readFileSync(f, 'utf8').replace(/\/\*[\s\S]*?\*\/|\/\/.*$/gm, '');

it('sim and data never use Math.random, Date, performance, the engine or the DOM', () => {
  for (const f of [...files('src/sim'), ...files('src/data')])
    expect(code(f), f).not.toMatch(/Math\.random|Date\.now|new Date|performance\.now|from 'phaser'|window\.|document\./);
});

it('sim, data and bots use no implementation-approximated Math (cross-engine determinism)', () => {
  const banned = /Math\.(sin|cos|tan|asin|acos|atan|atan2|sinh|cosh|tanh|asinh|acosh|atanh|exp|expm1|log|log1p|log2|log10|pow|hypot|cbrt)\b|\*\*/;
  for (const f of [...files('src/sim'), ...files('src/data'), ...files('src/bots')]) expect(code(f), f).not.toMatch(banned);
});
```

Why the second one: the spec lets engines approximate transcendental functions, so Node and Chrome can disagree in
the last bit and a replay then diverges between them. The fix was the sim's own `sin/cos/atan/atan2/asin` and a test
that they match `Math.*` within 1e-9 over a sweep of inputs (plus `atan2(0,-1)` ~ pi and `asin(1)` ~ pi/2).
The state hash is what catches any such drift.

## 2. Determinism and replay

Tower-defense `determinism.test.ts`, four cases (the sim takes a seed; a bot plays; the sim logs every command):

```ts
it('same seed + same inputs => identical end state', () => { expect(hashState(play(42).state)).toBe(hashState(play(42).state)); });
it('different seeds diverge', () => { expect(hashState(play(1, 'basic', 2000).state)).not.toBe(hashState(play(2, 'basic', 2000).state)); });
it('replaying the command log reproduces the exact state (random bot)', () => {
  const a = play(9, 'random', 5000);
  expect(hashState(replay({ level, seed: 9, log: a.log, tick: a.state.tick }).state)).toBe(hashState(a.state));
});
it('snapshot/restore continues identically', () => { /* snapshot at tick 1500, restore into a fresh sim, step both 1500 more, compare hashes */ });
```

Add the two the bug hunt proved you need: **resume equality with a non-empty progression preset** (an empty one hides
the dropped-options bug), and **browser hash == Node hash** at the same tick (the screenshot tool prints the browser hash).
The "different seeds diverge" case is not decoration: it catches a seed that is silently ignored.

## 3. Render never writes sim state

Give render a deep-readonly view of the state. In dev, hash the state before and after each frame behind a URL flag
(`?verify=1`) and expose `mutationDetected`; the fps tool can then print it (`--verify 1`).

## 4. Script runner

See cli-and-scripts.md: one test file iterates `tests/scripts/*.json`, so new regression scripts need no registration.
