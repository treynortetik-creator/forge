"""roomdraft.py: ASCII room-drafting helpers (1 char = 1 tile). Draft rooms as Python (shapes, scatter, reachability report),
emit them as `@ key: value` header lines + rows in a .txt, convert the .txt to your engine's data file with your own small script.

Usage as a library (see example_draft.py):
    from roomdraft import C, emit, entry, finish
    c = C(30, 18); c.rect(2, 2, 26, 14, '.'); c.wallify(); entry(c, 15); c.doors([(1, 8, 0)])
    c.scatter(8, 'S'); c.scatter(3, 'U'); print(c.report('my_room')); emit({'id': 'my_room'}, c, 'drafts')
CLI (checks any draft .txt, header lines starting '@ ' are skipped):
    python3 roomdraft.py check drafts/my_room.txt [...]     # size, walkable share, spawns + bbox, urns, door reach, stray floor
        exit 1 on an error (unreachable spawn/urn/door, stray floor, spawn box over 24x13); WARN only (exit 0) for
        walkable share outside 40-65% or a spawn count outside 6-10 (the roguelite validator's error/warning split)
    python3 roomdraft.py mirror drafts/my_room.txt          # print the left-right mirror (swaps / \\ and < >)

Legend used here (adapt freely; WALK / BLOCK below and the sets inside report() decide what counts as walkable):
  ' ' void, '.' floor, ':' variant floor, '#' wall, '=' bridge, P pit, O pillar, o breakable cover, L low wall, T landmark footprint,
  n feature pad, R reward point, w/W shallow/deep water, ^ always spikes, v k z optional trap slots, S spawn, U urn, E entry, 1-3 doors.
Origin: written for a Phaser roguelite (64 px tiles); no engine dependency, pure stdlib.
"""
import math, os, sys

WALK = set('.:=wnRSUEvkz^tbs123')
BLOCK = set('#OoLTWP ')


class C:
    def __init__(s, w, h):
        s.w, s.h = w, h
        s.g = [[' '] * w for _ in range(h)]

    def put(s, x, y, ch):
        if not (0 <= x < s.w and 0 <= y < s.h):
            raise ValueError(f'put({x},{y},{ch!r}) outside {s.w}x{s.h}')
        s.g[y][x] = ch
        return s

    def get(s, x, y):
        return s.g[y][x] if 0 <= x < s.w and 0 <= y < s.h else ' '

    def rect(s, x, y, w, h, ch='.'):
        for j in range(y, y + h):
            for i in range(x, x + w):
                s.put(i, j, ch)
        return s

    def ell(s, cx, cy, rx, ry, ch='.'):
        for j in range(s.h):
            for i in range(s.w):
                if ((i + 0.5 - cx) / rx) ** 2 + ((j + 0.5 - cy) / ry) ** 2 <= 1:
                    s.g[j][i] = ch
        return s

    def poly(s, pts, ch='.'):
        """Scanline fill of a polygon given in tile coordinates (tile centres tested)."""
        n = len(pts)
        for j in range(s.h):
            yy = j + 0.5
            xs = []
            for k in range(n):
                (x0, y0), (x1, y1) = pts[k], pts[(k + 1) % n]
                if (y0 <= yy < y1) or (y1 <= yy < y0):
                    xs.append(x0 + (yy - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for a in range(0, len(xs) - 1, 2):
                for i in range(s.w):
                    if xs[a] <= i + 0.5 < xs[a + 1]:
                        s.g[j][i] = ch
        return s

    def tiles(s, pts, ch):
        for x, y in pts:
            s.put(x, y, ch)
        return s

    def line(s, x0, y0, x1, y1, ch='.', th=1):
        """Thick line (brush of th tiles square)."""
        n = int(max(abs(x1 - x0), abs(y1 - y0))) * 2 + 1
        for k in range(n + 1):
            t = k / n
            x = x0 + (x1 - x0) * t
            y = y0 + (y1 - y0) * t
            for j in range(th):
                for i in range(th):
                    xi, yi = int(round(x - th / 2 + i)), int(round(y - th / 2 + j))
                    if 0 <= xi < s.w and 0 <= yi < s.h:
                        s.g[yi][xi] = ch
        return s

    def only(s, region, src, ch):
        """Replace src chars by ch inside region(x,y)."""
        for j in range(s.h):
            for i in range(s.w):
                if s.g[j][i] in src and region(i, j):
                    s.g[j][i] = ch
        return s

    def wallify(s, ymax=None, sides=True, south=False):
        """Turn void tiles that touch floor (8-neighbourhood) into '#', for y <= ymax (north + side walls)."""
        floor = set('.:=wWnRSUEvkz^tbsPOoLT123')
        out = []
        for j in range(s.h):
            for i in range(s.w):
                if s.g[j][i] != ' ':
                    continue
                if ymax is not None and j > ymax:
                    continue
                near = any(s.get(i + dx, j + dy) in floor for dx in (-1, 0, 1) for dy in (-1, 0, 1))
                if near:
                    out.append((i, j))
        for i, j in out:
            s.g[j][i] = '#'
        return s

    def doors(s, spec):
        """spec: list of (slot, x, y): placed on the canvas perimeter, replacing a wall tile."""
        for slot, x, y in spec:
            if not (x in (0, s.w - 1) or y in (0, s.h - 1)):
                raise ValueError(f'door {slot} at ({x},{y}) is not on the canvas perimeter')
            s.put(x, y, str(slot))
        return s

    def rows(s):
        return [''.join(r) for r in s.g]

    # ---- metrics
    def count(s, chars):
        return sum(1 for r in s.g for c in r if c in chars)

    def find(s, ch):
        return [(i, j) for j in range(s.h) for i in range(s.w) if s.g[j][i] == ch]

    def scatter(s, n, ch, zone=None, minE=4.6, near=None, mind=0, avoid=None):
        """Farthest-point scatter of ch over '.' tiles. zone=(x0,y0,x1,y1) inclusive. near: predicate on (x,y) for urns."""
        E = s.find('E')
        ex, ey = E[0] if E else (s.w // 2, s.h - 1)
        seeds = [p for p in s.find('S') + s.find('U')]
        for _ in range(n):
            best, bd = None, -1
            for y in range(1, s.h - 1):
                for x in range(1, s.w - 1):
                    if s.g[y][x] != '.':
                        continue
                    if zone and not (zone[0] <= x <= zone[2] and zone[1] <= y <= zone[3]):
                        continue
                    if math.hypot(x - ex, y - ey) < minE:
                        continue
                    nb = [s.get(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
                    if any(c in '123E' for c in nb):
                        continue
                    if ch == 'S' and any(c in ' P#W' for c in nb):
                        continue   # keep spawns off ragged edges
                    if ch == 'U' and not any(c in '# OWPL' for c in nb):
                        continue
                    if avoid and avoid(x, y):
                        continue
                    d = min([math.hypot(x - a, y - b) for a, b in seeds] + [99])
                    if d > bd:
                        bd, best = d, (x, y)
            if best is None:
                raise ValueError(f'scatter: no room for {ch}')
            s.g[best[1]][best[0]] = ch
            seeds.append(best)
        return s

    def reach(s):
        E = s.find('E')
        if not E:
            return set()
        seen = {E[0]}
        q = [E[0]]
        while q:
            x, y = q.pop()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                p = (x + dx, y + dy)
                if p in seen:
                    continue
                if s.get(*p) in WALK:
                    seen.add(p)
                    q.append(p)
        return seen

    def report(s, name=''):
        walk = s.count(set('.:=wnRSUEvkz^tbs'))
        share = walk / (s.w * s.h)
        S = s.find('S')
        bbox = (max(p[0] for p in S) - min(p[0] for p in S) + 1, max(p[1] for p in S) - min(p[1] for p in S) + 1) if S else (0, 0)
        r = s.reach()
        unreach = [p for ch in 'SRUn123' for p in s.find(ch) if p not in r and not (ch in '123')]
        doors = []
        for ch in '123':
            for (x, y) in s.find(ch):
                adj = any((x + dx, y + dy) in r for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                doors.append((ch, adj))
        # unreachable walkable floor
        allw = {(i, j) for j in range(s.h) for i in range(s.w) if s.g[j][i] in set('.:=wnRSUEvkz^tbs')}
        stray = allw - r
        msg = f'{name:26s} {s.w}x{s.h} walk {share:.0%} spawns {len(S)} bbox {bbox[0]}x{bbox[1]} urns {len(s.find("U"))} doors {"".join(d[0] if d[1] else "!" + d[0] for d in doors)}'
        errors, warns = [], []
        if unreach:
            errors.append(f'UNREACH {unreach}')
        if stray:
            errors.append(f'stray-floor {len(stray)}')
        if any(not d[1] for d in doors):
            errors.append('door-unreachable')
        if S and (bbox[0] > 24 or bbox[1] > 13):
            errors.append('spawn-bbox>24x13')
        if not 0.40 <= share <= 0.65:
            warns.append('WARN walk-outside-40-65%')
        if S and not 6 <= len(S) <= 10:
            warns.append('WARN spawns-outside-6-10')
        s.errors = errors
        return ' '.join([msg] + errors + warns)


def sym(c, x0=None):
    """Mirror the canvas left-right about its centre (copy the left half over the right) for symmetric parts."""
    for j in range(c.h):
        for i in range(c.w // 2):
            if c.g[j][i] != ' ':
                c.g[j][c.w - 1 - i] = c.g[j][i]
    return c


def emit(meta, c, outdir):
    os.makedirs(outdir, exist_ok=True)
    head = [f'@ {k}: {v}' for k, v in meta.items()]
    with open(os.path.join(outdir, meta['id'] + '.txt'), 'w') as f:
        f.write('\n'.join(head) + '\n' + '\n'.join(c.rows()) + '\n')


def box(c, ymax=None, north=True, sides=True, xs=None):
    """Wall the canvas: north row and side columns (only where void), down to ymax."""
    ymax = c.h - 1 if ymax is None else ymax
    for i in range(c.w):
        if north and c.g[0][i] == ' ':
            c.g[0][i] = '#'
    if sides:
        for j in range(0, ymax + 1):
            for i in (0, c.w - 1):
                if c.g[j][i] == ' ':
                    c.g[j][i] = '#'
    return c


def wall_if(c, pred):
    """Void tiles touching floor (8-nbhd) where pred(x,y) is true become '#'."""
    floor = set('.:=wWnRSUEvkz^tbsPOoLT123')
    out = [(i, j) for j in range(c.h) for i in range(c.w) if c.g[j][i] == ' ' and pred(i, j)
           and any(c.get(i + dx, j + dy) in floor for dx in (-1, 0, 1) for dy in (-1, 0, 1))]
    for i, j in out:
        c.g[j][i] = '#'
    return c


def dump(c):
    print('\n'.join(c.rows()))


def entry(c, x, ch='E'):
    """E on the bottom canvas row; carve a 1-wide stem up to the first floor above it (void -> floor, water -> plank)."""
    y = c.h - 1
    c.put(x, y, ch)
    j = y - 1
    while j > 0 and c.g[j][x] in ' Ww':
        c.g[j][x] = '.' if c.g[j][x] == ' ' else '='
        j -= 1
    return c


def finish(c, alcoves=(), thick=True):
    """Thicken the north wall by one row so doors sit in 3-wide recesses (and `alcoves` x-centres get dressing niches).
    Returns a NEW canvas (height + 1); all coordinates below row 0 shift down by one."""
    n = C(c.w, c.h + 1)
    for j in range(c.h):
        n.g[j + 1] = list(c.g[j])
    n.g[0] = ['#'] * c.w
    for i in range(c.w):
        ch = n.g[1][i]
        if ch in '123':
            n.g[0][i] = ch
            for k in (i - 1, i, i + 1):
                if 0 < k < c.w - 1:
                    n.g[1][k] = '.'
            n.g[1][i] = '.'
    for x in alcoves:
        for k in (x - 1, x, x + 1):
            if 0 < k < c.w - 1 and n.g[1][k] == '#':
                n.g[1][k] = '.'
    return n


import math as _m


def blob(c, cx, cy, rx, ry, ch='.', k=0.16, ph=0.0, only_void=False):
    """Organic island: an ellipse whose radius wobbles with the angle (deterministic)."""
    for j in range(c.h):
        for i in range(c.w):
            dx, dy = (i + 0.5 - cx) / rx, (j + 0.5 - cy) / ry
            r = _m.hypot(dx, dy)
            th = _m.atan2(dy, dx)
            lim = 1 + k * (_m.sin(3 * th + ph) * 0.6 + _m.sin(5 * th + ph * 1.7) * 0.4)
            if r <= lim and (not only_void or c.g[j][i] == ' '):
                c.g[j][i] = ch
    return c


def shore(c, ch='w', d=1, src='.', face=None):
    """Turn floor tiles within d tiles (4-nbhd) of void into shallow water (a drowned shoreline)."""
    out = []
    for j in range(c.h):
        for i in range(c.w):
            if c.g[j][i] not in src:
                continue
            for k in range(1, d + 1):
                if any(c.get(i + dx * k, j + dy * k) == ' ' for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    if face is None or face(i, j):
                        out.append((i, j))
                        break
    for i, j in out:
        c.g[j][i] = ch
    return c


def portals(c, arch=2):
    """Doors:  '#' arch pieces beside each perimeter door (only over void); floor stays below/inside it."""
    for ch in '123':
        for (x, y) in c.find(ch):
            if y == 0:
                for k in range(-arch, arch + 1):
                    if k and 0 <= x + k < c.w and c.g[0][x + k] in ' Ww.:':
                        c.g[0][x + k] = '#'
            elif y == c.h - 1:
                for k in range(-arch, arch + 1):
                    if k and 0 <= x + k < c.w and c.g[y][x + k] in ' Ww.:':
                        c.g[y][x + k] = '#'
            else:
                for k in range(-arch, arch + 1):
                    if k and 0 <= y + k < c.h and c.g[y + k][x] in ' Ww.:':
                        c.g[y + k][x] = '#'
    return c


def door_reach(c, slot, x, y, floor='.'):
    """Make sure the tile inside a perimeter door is walkable (carve a stub inward through void and water)."""
    dx = 1 if x == 0 else (-1 if x == c.w - 1 else 0)
    dy = 1 if y == 0 else (-1 if y == c.h - 1 else 0)
    i, j = x + dx, y + dy
    n = 0
    while 0 <= i < c.w and 0 <= j < c.h and c.g[j][i] in ' Ww#' and n < 12:
        c.g[j][i] = '=' if c.g[j][i] in 'Ww' else floor
        i += dx; j += dy; n += 1
    return c


def shoals(c, d=1, ch='w'):
    """Deep-water tiles within d tiles of land or bridge become shallows (foam ring around islands)."""
    land = set('.:=wnRSUEvkz^tbsPOoLT')
    out = [(i, j) for j in range(c.h) for i in range(c.w) if c.g[j][i] == 'W'
           and any(c.get(i + dx, j + dy) in land - {'w'} for dx in range(-d, d + 1) for dy in range(-d, d + 1))]
    for i, j in out:
        c.g[j][i] = ch
    return c


# ---------------------------------------------------------------- mirror + CLI
_FLIP = {'>': '<', '<': '>', '/': '\\', '\\': '/'}


def mirror_rows(rows):
    """Left-right mirror of a room: reverse each row and swap diagonal / ballista-slit characters. Doors, spawns and the entry
    mirror with it (their coordinates are the characters themselves)."""
    return [''.join(_FLIP.get(ch, ch) for ch in reversed(r)) for r in rows]


def from_rows(rows):
    """Build a C canvas from a list of equal-length row strings."""
    w = {len(r) for r in rows}
    if len(w) != 1:
        raise ValueError(f'rows are not all the same length: {sorted(w)}')
    c = C(len(rows[0]), len(rows))
    for j, r in enumerate(rows):
        c.g[j] = list(r)
    return c


def read_draft(path):
    meta, rows = {}, []
    for line in open(path, encoding='utf-8'):
        line = line.rstrip('\n')
        if line.startswith('@ '):
            k, v = line[2:].split(': ', 1)
            meta[k] = v
        else:
            rows.append(line)
    return meta, rows


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] in ('-h', '--help'):
        print(__doc__); sys.exit(0)
    if len(sys.argv) < 3 or sys.argv[1] not in ('check', 'mirror'):
        print(__doc__)
        sys.exit(2)
    bad = False
    for p in sys.argv[2:]:
        meta, rows = read_draft(p)
        if sys.argv[1] == 'mirror':
            print('\n'.join(mirror_rows(rows)))
        else:
            c = from_rows(rows)
            print(c.report(meta.get('id', os.path.basename(p))))
            bad = bad or bool(c.errors)
    sys.exit(1 if bad else 0)
