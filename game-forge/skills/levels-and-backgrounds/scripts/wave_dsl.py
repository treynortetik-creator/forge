#!/usr/bin/env python3
"""wave_dsl.py: a one-line-per-wave DSL for tower-defense waves, parsed to JSON, with one difficulty knob K.
Lifted (re-written in Python, same grammar) from the TypeScript helper that wrote twelve levels as readable scripts.

  python3 wave_dsl.py waves.txt --paths shore,ice [--K 1.5] [--json out.json]     # one wave per line; prints a per-wave, per-path unit table

Grammar, one wave per line:  [!enemy[|Title]] group; group; ...
  group  = enemy count interval [@delay] [>path|>all] [xHP]
           interval = seconds between spawns, @delay = seconds before the group starts, >all = one copy on EVERY path (count is per path),
           xHP = a per-group hit-point multiplier.
  BOSS id [@delay] [>path]        one boss; never scaled by K
  !enemy                          flags the wave's callout banner (the first appearance of a new enemy); |Title overrides the banner text
  count is scaled: max(1, round(count * K)). The first path is the default path.
Example:  "!exorcist villager 10 .6; exorcist 2 1.5 @4 >lower; BOSS captain @10"
Why a DSL: waves in raw object literals buried the design; as lines, a whole level's escalation fits one screen and re-tunes with K (the level
scripts also had per-enemy count caps for fast or wall-breaking units that must not grow in bulk; add yours in COUNT_CAP below).
"""
import json, re, sys

COUNT_CAP = {}   # e.g. {'hound': 12}: after K scaling, no single group grows past this


def parse(lines, paths, K=1.0):
    out = []
    for line in lines:
        w = {'groups': []}
        body = line.strip()
        m = re.match(r'^!(\w+)(?:\|(\S+))?\s+', body)
        if m:
            w['callout'] = {'enemy': m[1], **({'title': m[2].replace('_', ' ')} if m[2] else {})}
            body = body[m.end():]
        for raw in [s.strip() for s in body.split(';') if s.strip()]:
            tok = raw.split()
            if tok[0] == 'BOSS':
                delay, path = 0.0, paths[0]
                for t in tok[2:]:
                    if t.startswith('@'): delay = float(t[1:])
                    if t.startswith('>'): path = t[1:]
                w['groups'].append({'enemy': tok[1], 'count': 1, 'interval': 1, 'delay': delay, 'path': path})
                continue
            enemy, count, interval = tok[0], float(tok[1]), float(tok[2])
            if not (count > 0 and interval > 0):
                raise ValueError(f'bad wave group {raw!r}')
            delay, path, hp = 0.0, paths[0], None
            for t in tok[3:]:
                if t.startswith('@'): delay = float(t[1:])
                elif t.startswith('>'): path = t[1:]
                elif t.startswith('x'): hp = float(t[1:])
            for p in (paths if path == 'all' else [path]):
                if p not in paths:
                    raise ValueError(f'unknown path {p!r} in {raw!r}')
                g = {'enemy': enemy, 'count': min(COUNT_CAP.get(enemy, 10**9), max(1, round(count * K))), 'interval': interval, 'delay': delay, 'path': p}
                if hp: g['hpMult'] = hp
                w['groups'].append(g)
        out.append(w)
    return out


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] in ('-h', '--help'):
        print(__doc__); sys.exit(0)
    a = sys.argv[1:]
    if not a or '--paths' not in a:
        print(__doc__); sys.exit(2)
    paths = a[a.index('--paths') + 1].split(',')
    K = float(a[a.index('--K') + 1]) if '--K' in a else 1.0
    lines = [l for l in open(a[0], encoding='utf-8').read().split('\n') if l.strip() and not l.lstrip().startswith('#')]
    ws = parse(lines, paths, K)
    print('wave  ' + '  '.join(f'{p:>8}' for p in paths) + '   callout')
    for i, w in enumerate(ws, 1):
        n = {p: sum(g['count'] for g in w['groups'] if g['path'] == p) for p in paths}
        print(f'{i:>4}  ' + '  '.join(f'{n[p]:>8}' for p in paths) + '   ' + (w.get('callout', {}).get('enemy', '')))
    if '--json' in a:
        json.dump(ws, open(a[a.index('--json') + 1], 'w'), indent=1)
        print('json ->', a[a.index('--json') + 1])
