#!/usr/bin/env python3
"""wave-pack.py: pack an art wave for the image model, and check what comes back.

  python3 -I wave-pack.py pack  <wave-dir> [--prefix NAME] [--limit-mb 45] [--out DIR]
  python3 -I wave-pack.py check <returned-dir> --brief <WAVE-N.md> [--sheet out.jpg] [--reserve-green]
  python3 -I wave-pack.py check <returned-dir> --count 5 --size 1024x1024 [--bg BFBFBF | --alpha]

Wave folder layout: <anything>/waveN-<slug>-<date>/ holding WAVEN.md (the brief; any file named
CODEX-WAVEN.md or WAVEN.md), optionally <prefix>-waveN/{WAVEN.md,refs/}, later the zip and returned/.

pack:  zips the wave folder as <prefix>-waveN.zip (top folder <prefix>-waveN/). Default prefix: "game".
       If that is over the limit it writes <prefix>-waveN-part1.zip, -part2.zip ... instead; every
       part carries the brief, refs/ goes wherever it fits. Default cap 45 MB (a chat-app file limit was 50 MB;
       change --limit-mb to whatever your real transfer channel allows).
check: counts files, reads dimensions, alpha coverage and corner background colour, optional reserved-colour (green)
       pixel count, and compares them to the brief. A brief is a WAVEN.md: every backticked `name.png` outside refs/ is an expected file;
       a WxH on the same table row is its size; "transparent"/"alpha" on the row means it must have real transparency;
       "#RRGGBB" on the row means a flat opaque background of that colour. Writes a labelled contact sheet via
       ImageMagick. Exit 1 on any FAIL. Zips found in <returned-dir> are extracted in place first (never overwrites).
Needs Pillow and `magick` (ImageMagick 7) for the sheet. Never modifies the wave folder.
The project-specific bits of the original (a prefix, a reserved green) are now flags.
"""
import argparse, os, re, subprocess, sys, zipfile

FONT = next((f for f in ('/System/Library/Fonts/Supplemental/Arial.ttf', '/Library/Fonts/Arial.ttf',
                         '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf') if os.path.exists(f)), None)
IMG_EXT = ('.png', '.webp', '.jpg', '.jpeg')
SKIP = {'.DS_Store'}


def human(n):
    return f'{n / 1048576:.1f} MB'


def wave_number(wave_dir):
    base = os.path.basename(os.path.abspath(wave_dir))
    m = re.match(r'wave(\d+[a-z]?)', base, re.I)
    if m:
        return m.group(1)
    for f in os.listdir(wave_dir):
        m = re.match(r'(?:CODEX-)?WAVE(\d+[a-z]?)\.md$', f, re.I)
        if m:
            return m.group(1)
    sys.exit(f'cannot work out the wave number from {wave_dir}')


def gather(wave_dir, n, prefix):
    """(abs path, arcname) pairs. Prefers the <prefix>-waveN/ subfolder if present."""
    inner = os.path.join(wave_dir, f'{prefix}-wave{n}')
    root = inner if os.path.isdir(inner) else wave_dir
    top = f'{prefix}-wave{n}'
    out = []
    for dp, dn, fn in os.walk(root):
        rel = os.path.relpath(dp, root)
        if root == wave_dir and rel.split(os.sep)[0] in ('returned', 'return', f'{prefix}-wave' + n):
            dn[:] = []
            continue
        dn[:] = [d for d in dn if d not in ('returned', 'return')] if root == wave_dir else dn
        for f in fn:
            if f in SKIP or f.endswith('.zip'):
                continue
            ap = os.path.join(dp, f)
            arc = os.path.normpath(os.path.join(top, os.path.relpath(ap, root)))
            out.append((ap, arc))
    return out


def cmd_pack(a):
    wd = os.path.abspath(a.wave_dir)
    n = wave_number(wd)
    files = gather(wd, n, a.prefix)
    if not files:
        sys.exit('nothing to pack')
    limit = int(a.limit_mb * 1048576)
    outdir = os.path.abspath(a.out or wd)
    os.makedirs(outdir, exist_ok=True)
    md = [f for f in files if re.match(r'(CODEX-)?WAVE', os.path.basename(f[0]), re.I)]
    rest = [f for f in files if f not in md]
    mdsize = sum(os.path.getsize(f[0]) for f in md)
    # greedy first-fit-decreasing on raw size (PNG/WebP/JPG barely compress, so raw ~ zipped)
    rest.sort(key=lambda f: -os.path.getsize(f[0]))
    bins = []
    for f in rest:
        sz = os.path.getsize(f[0])
        if sz + mdsize > limit:
            sys.exit(f'FAIL: {f[1]} is {human(sz)}, cannot fit a part under {a.limit_mb} MB')
        for b in bins:
            if b[0] + sz <= limit:
                b[0] += sz
                b[1].append(f)
                break
        else:
            bins.append([mdsize + sz, [f]])
    if not bins:
        bins = [[mdsize, []]]
    names = [f'{a.prefix}-wave{n}.zip'] if len(bins) == 1 else [f'{a.prefix}-wave{n}-part{i + 1}.zip' for i in range(len(bins))]
    # remove stale zips from an earlier pack so parts and a whole never coexist
    for old in os.listdir(outdir):
        if re.match(rf'{re.escape(a.prefix)}-wave{re.escape(n)}(-part\d+)?\.zip$', old) and old not in names:
            os.remove(os.path.join(outdir, old))
    bad = False
    for name, b in zip(names, bins):
        p = os.path.join(outdir, name)
        with zipfile.ZipFile(p, 'w', zipfile.ZIP_DEFLATED) as z:
            for ap, arc in md + sorted(b[1], key=lambda f: f[1]):
                z.write(ap, arc)
        sz = os.path.getsize(p)
        flag = '' if sz <= limit else '  OVER LIMIT'
        bad |= sz > limit
        print(f'{p}  {human(sz)}  {len(b[1])} files{flag}')
    print(f'{sum(len(b[1]) for b in bins)} files (+{len(md)} brief) in {len(bins)} part(s), limit {a.limit_mb} MB')
    sys.exit(1 if bad else 0)


# ---------------------------------------------------------------- check

def parse_brief(path):
    """-> {filename: {'size': (w,h)|None, 'alpha': bool, 'bg': 'RRGGBB'|None, 'optional': bool}}
    Only table rows / bullets that START with a backticked filename count as deliverables."""
    exp = {}
    pat = re.compile(r'^\s*(?:\||[-*]\s)\s*\**`([^`/ *]+\.(?:png|webp|jpe?g))`', re.I)
    for line in open(path, encoding='utf-8'):
        m = pat.match(line)
        if not m or m.group(1).startswith(('STYLE-', 'FORMAT-')):
            continue
        nm, rest = m.group(1), line[m.end():]
        head = rest[:160].lower()
        sz = re.search(r'(\d{3,5})\s*[x×]\s*(\d{3,5})', rest)
        bg = re.search(r'#([0-9a-f]{6})\b', rest, re.I)
        exp.setdefault(nm, {
            'size': (int(sz.group(1)), int(sz.group(2))) if sz else None,
            'alpha': ('transparent' in head or 'alpha' in head) and 'opaque' not in head,
            'bg': bg.group(1).upper() if bg else None,
            'optional': 'optional' in rest[:200].lower(),
        })
    return exp


def measure(path):
    from PIL import Image
    im = Image.open(path)
    w, h = im.size
    rgba = im.convert('RGBA')
    px = rgba.load()
    a = rgba.getchannel('A')
    hist = a.histogram()
    tot = w * h
    transp = sum(hist[:8]) / tot
    opaque = sum(hist[248:]) / tot
    has_alpha = im.mode in ('RGBA', 'LA', 'PA') or 'transparency' in im.info
    corners = [px[0, 0], px[w - 1, 0], px[0, h - 1], px[w - 1, h - 1]]
    c = corners[0]
    corner_same = all(max(abs(c[i] - k[i]) for i in range(4)) <= 6 for k in corners)
    # optional reserved colour (green): art that must not contain it is flagged
    small = rgba.copy()
    small.thumbnail((256, 256))
    sp = list(small.get_flattened_data() if hasattr(small, 'get_flattened_data') else small.getdata())
    green = sum(1 for r, g, b, al in sp if al > 128 and g > 140 and g > r + 50 and g > b + 50)
    return dict(w=w, h=h, has_alpha=has_alpha, transp=transp, opaque=opaque, corner=c, corner_same=corner_same,
                green=green, green_frac=green / max(1, len(sp)))


def find_images(d):
    out = []
    for dp, dn, fn in os.walk(d):
        dn[:] = [x for x in dn if not x.startswith(('_', '.')) and x != '__MACOSX']
        for f in fn:
            if f.lower().endswith(IMG_EXT) and not f.startswith(('.', '_')):
                out.append(os.path.join(dp, f))
    return sorted(out)


def cmd_check(a):
    rd = os.path.abspath(a.returned_dir)
    for dp, _, fn in os.walk(rd):
        for f in fn:
            if f.lower().endswith('.zip'):
                with zipfile.ZipFile(os.path.join(dp, f)) as z:
                    for m in z.namelist():
                        if m.startswith('__MACOSX') or m.endswith('.DS_Store'):
                            continue
                        if not os.path.exists(os.path.join(dp, m)):
                            z.extract(m, dp)
                            print(f'extracted {m}')
    imgs = find_images(rd)
    if a.brief:
        exp = parse_brief(a.brief)
    else:
        exp = {}
    g_size = tuple(int(x) for x in a.size.lower().split('x')) if a.size else None
    fails, warns = 0, 0
    by_name = {os.path.basename(p): p for p in imgs}
    want_n = sum(1 for v in exp.values() if not v['optional']) if exp else a.count
    print(f'{len(imgs)} image(s) in {rd}; expected {want_n if want_n is not None else "?"}')
    for nm in sorted(exp):
        if nm not in by_name:
            if exp[nm].get('optional'):
                print(f'WARN  optional file not returned: {nm}')
                warns += 1
            else:
                print(f'FAIL  missing: {nm}')
                fails += 1
    if exp:
        for nm in sorted(by_name):
            if nm not in exp:
                print(f'WARN  not in brief: {nm}')
                warns += 1
    elif a.count is not None and len(imgs) != a.count:
        print(f'FAIL  count {len(imgs)} != {a.count}')
        fails += 1
    rows = []
    for p in imgs:
        nm = os.path.basename(p)
        m = measure(p)
        e = exp.get(nm, {})
        size = e.get('size') or g_size
        want_alpha = e.get('alpha') or a.alpha
        want_bg = e.get('bg') or (a.bg.upper().lstrip('#') if a.bg else None)
        msgs = []
        if size and (m['w'], m['h']) != size:
            msgs.append(f'FAIL size {m["w"]}x{m["h"]} != {size[0]}x{size[1]}')
        if want_alpha:
            if not m['has_alpha'] or m['transp'] < 0.01:
                msgs.append(f'FAIL no real transparency (transparent px {m["transp"]:.1%})')
        elif want_bg:
            r, g, b, al = m['corner']
            hexc = f'{r:02X}{g:02X}{b:02X}'
            if m['opaque'] < 0.99:
                msgs.append(f'FAIL not opaque ({m["opaque"]:.1%})')
            if not m['corner_same'] or max(abs(int(hexc[i:i + 2], 16) - int(want_bg[i:i + 2], 16)) for i in (0, 2, 4)) > 12:
                msgs.append(f'FAIL background #{hexc} (corners {"agree" if m["corner_same"] else "differ"}) != #{want_bg}')
        if a.reserve_green and m['green_frac'] > 0.001:
            msgs.append(f'WARN green {m["green_frac"]:.2%} of pixels (green is reserved in this project)')
        for s in msgs:
            fails += s.startswith('FAIL')
            warns += s.startswith('WARN')
        status = 'ok  ' if not msgs else ('FAIL' if any(s.startswith('FAIL') for s in msgs) else 'WARN')
        print(f'{status}  {nm}  {m["w"]}x{m["h"]}  alpha={"Y" if m["has_alpha"] else "n"} transp={m["transp"]:.0%} '
              f'corner=#{m["corner"][0]:02X}{m["corner"][1]:02X}{m["corner"][2]:02X}')
        for s in msgs:
            print(f'        {s}')
        rows.append(p)
    sheet = a.sheet or os.path.join(os.path.dirname(rd), f'contact-sheet-{os.path.basename(rd)}.jpg')
    if rows:
        make_sheet(rows, sheet)
    print(f'{fails} FAIL, {warns} WARN')
    sys.exit(1 if fails else 0)


def make_sheet(paths, out, per=30, cols=6, cell=256):
    """Labelled contact sheet(s). More than `per` images -> out, out-2, ... ; label = filename + WxH."""
    base, ext = os.path.splitext(out)
    for i in range(0, len(paths), per):
        chunk = paths[i:i + per]
        dest = out if i == 0 else f'{base}-{i // per + 1}{ext}'
        cmd = ['magick', 'montage'] + (['-font', FONT] if FONT else []) + ['-pointsize', '14', '-fill', 'white', '-background', '#555555',
               '-gravity', 'center']
        for p in chunk:
            cmd += ['-label', '%f\n%wx%h', p]
        cmd += ['-tile', f'{cols}x', '-geometry', f'{cell}x{cell}+6+6', '-quality', '88', dest]
        subprocess.run(cmd, check=True, capture_output=True)
        print(f'contact sheet: {dest}')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('pack')
    p.add_argument('wave_dir')
    p.add_argument('--limit-mb', type=float, default=45)
    p.add_argument('--out')
    p.add_argument('--prefix', default='game')
    c = sub.add_parser('check')
    c.add_argument('returned_dir')
    c.add_argument('--brief')
    c.add_argument('--count', type=int)
    c.add_argument('--size')
    c.add_argument('--bg')
    c.add_argument('--alpha', action='store_true')
    c.add_argument('--reserve-green', action='store_true', help='flag green pixels (use when green is a reserved colour)')
    c.add_argument('--sheet')
    a = ap.parse_args()
    {'pack': cmd_pack, 'check': cmd_check}[a.cmd](a)


if __name__ == '__main__':
    main()
