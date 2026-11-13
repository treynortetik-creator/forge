#!/usr/bin/env python3
"""loopcut: repair / cut music loops, and measure BPM + key for the music gates.
Needs ffmpeg, numpy, scipy. Output dir: --out-dir, else $MUSIC_DIR, else ./public/assets/audio/music.

  loopcut.py analyze <file>                      bpm, key, rms profile (no writes)
  loopcut.py cut <in> --key NAME [--write] [--max-body 120] [--bpb 4] [--out-dir DIR]
      body = [S, E): S first beat-grid point after the RMS reaches within 6 dB of the program median,
      E = S + whole bars, before the RMS falls >6 dB. A 1-bar equal-power overlap blends the end of the
      body into its own start, so the written file loops with no fade hole. Loudnorm two-pass
      I=-16 TP=-2 LRA=11, libopus 96k .ogg + aac 128k .m4a. With --write, updates manifest.json (this key only).
Acceptance: the 0.3 s windows either side of the wrap within 3 dB of each other and within 8 dB of the median;
a cue with no qualifying 60 s region is flagged, never forced.
"""
import argparse, json, os, subprocess, sys, tempfile
import numpy as np
from scipy.signal import stft

SR = 48000
MUSIC = os.environ.get('MUSIC_DIR', os.path.join(os.getcwd(), 'public', 'assets', 'audio', 'music'))  # --out-dir overrides; manifest.json lives here


def decode(path, sr=SR):
    cmd = ['ffmpeg', '-v', 'error', '-i', path, '-f', 'f32le', '-ac', '2', '-ar', str(sr), '-']
    raw = subprocess.run(cmd, check=True, capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32).reshape(-1, 2).copy()


def rms_db(x, a, b, _=None):
    seg = x[int(a * SR):int(b * SR)]
    if len(seg) == 0:
        return -120.0
    return 10 * np.log10(float(np.mean(seg ** 2)) + 1e-12)


def rms_profile(x, win=0.4, hop=0.1):
    n = int(win * SR); h = int(hop * SR)
    out = []
    for i in range(0, max(1, len(x) - n), h):
        out.append(10 * np.log10(float(np.mean(x[i:i + n] ** 2)) + 1e-12))
    return np.array(out), hop


def onset_env(mono, sr=SR):
    f, t, Z = stft(mono, fs=sr, nperseg=2048, noverlap=2048 - 480, boundary=None)  # 10 ms hop
    mag = np.log1p(np.abs(Z) * 10)
    flux = np.maximum(0, np.diff(mag, axis=1)).sum(axis=0)
    flux = flux - np.convolve(flux, np.ones(50) / 50, mode='same')
    return np.maximum(flux, 0), 0.01


def estimate_bpm(x):
    mono = x.mean(axis=1)
    env, dt = onset_env(mono)
    env = env - env.mean()
    n = len(env)
    ac = np.correlate(env, env, mode='full')[n - 1:]
    ac /= (ac[0] + 1e-9)
    lo, hi = int(60 / 200 / dt), int(60 / 60 / dt)
    best, bs = None, -1
    for lag in range(lo, hi):
        bpm = 60 / (lag * dt)
        w = np.exp(-0.5 * ((np.log2(bpm / 125)) / 0.7) ** 2)  # mild prior around 125
        s = ac[lag] * w
        if s > bs:
            bs, best = s, lag
    # refine period by comb-sum over a fine grid
    best_bpm, best_sum, best_phase = 60 / (best * dt), -1, 0.0
    ar = np.arange(n)
    for bpm in np.arange(60 / (best * dt) * 0.97, 60 / (best * dt) * 1.03, 0.05):
        p = 60 / bpm / dt
        fold = np.bincount((ar % p).astype(int), weights=env, minlength=int(p) + 1)[:int(p) + 1]
        fold = np.convolve(np.concatenate([fold[-2:], fold, fold[:2]]), np.ones(3) / 3, mode='same')[2:-2]
        ph = int(fold.argmax()); s = fold[ph] / (n / p)
        if s > best_sum:
            best_sum, best_bpm, best_phase = s, bpm, ph * dt
    return float(best_bpm), float(best_phase), env, dt


KS_MAJ = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
KS_MIN = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']


def estimate_key(x):
    mono = x.mean(axis=1)[::2]  # 24 kHz
    f, t, Z = stft(mono, fs=SR // 2, nperseg=8192, noverlap=4096, boundary=None)
    mag = np.abs(Z)
    sel = (f >= 55) & (f <= 2000)
    fr = f[sel]; m = mag[sel].sum(axis=1)
    chroma = np.zeros(12)
    midi = 69 + 12 * np.log2(fr / 440.0)
    pc = np.round(midi).astype(int) % 12
    for p, v in zip(pc, m):
        chroma[p] += v
    argmax = int(chroma.argmax())
    best = (-2, 0, 'maj')
    for tonic in range(12):
        for name, prof in (('maj', KS_MAJ), ('min', KS_MIN)):
            c = np.corrcoef(chroma, np.roll(prof, tonic))[0, 1]
            if c > best[0]:
                best = (c, tonic, name)
    return {'argmax': NOTES[argmax], 'key': f'{NOTES[best[1]]} {best[2]}', 'tonic': NOTES[best[1]], 'mode': best[2], 'corr': round(float(best[0]), 3)}


def bpm_match(measured, target, tol):
    """half and double speed count as a match"""
    return any(abs(measured * k - target) <= tol for k in (1, 0.5, 2))


def find_region(x, bpm, phase, bpb=4, max_body=120.0, thresh=6.0):
    prof, hop = rms_profile(x)
    med = float(np.median(prof))
    loud = np.where(prof >= med - thresh)[0]
    # first start: first window with level within 6 dB of the median AND staying so for >= 10 s
    ok = prof >= med - thresh
    first = None
    for i in range(len(ok)):
        if ok[i:i + 100].all():
            first = i * hop; break
    last = None
    for i in range(len(ok) - 1, -1, -1):
        if ok[max(0, i - 99):i + 1].all():
            last = i * hop + 0.4; break
    if first is None or last is None:
        return None, med, prof
    beat = 60 / bpm; bar = beat * bpb
    # first downbeat >= first on the beat grid (bar grid anchored at the strongest-onset beat phase)
    k = np.ceil((first - phase) / bar)
    S = phase + k * bar
    avail = last - S
    nbars = int(np.floor(avail / bar))
    nbars = min(nbars, int(max_body / bar))
    if nbars < 3:
        return None, med, prof
    return (S, S + nbars * bar, bar), med, prof


def build_loop(x, S, E, bar):
    xf = int(round(bar * SR))
    s, e = int(round(S * SR)), int(round(E * SR))
    n = np.arange(xf) / xf
    fo, fi = np.cos(n * np.pi / 2)[:, None], np.sin(n * np.pi / 2)[:, None]
    blend = x[e - xf:e] * fo + x[s:s + xf] * fi
    return np.concatenate([x[s + xf:e - xf], blend]).astype(np.float32)


def write_wav(path, y):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ac', '2', '-ar', str(SR), '-i', '-', path], input=y.tobytes(), check=True)


def loudnorm_encode(wav, out_base, I=-16, TP=-2, LRA=11):
    m = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', wav, '-af', f'loudnorm=I={I}:TP={TP}:LRA={LRA}:print_format=json', '-f', 'null', '-'], capture_output=True, text=True).stderr
    j = json.loads(m[m.rindex('{'):m.rindex('}') + 1])
    af = (f"loudnorm=I={I}:TP={TP}:LRA={LRA}:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}"
          f":measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true,aresample={SR}")
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', wav, '-af', af, '-c:a', 'libopus', '-b:a', '96k', out_base + '.ogg'], check=True)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', wav, '-af', af, '-c:a', 'aac', '-b:a', '128k', out_base + '.m4a'], check=True)


def ebur(path):
    r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', path, '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
    tail = r[r.rindex('Summary:'):]
    g = lambda k: float(tail.split(k)[1].split()[0])
    return {'I': g('I:'), 'LRA': g('LRA:'), 'TP': g('Peak:')}


def duration(path):
    return float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path], capture_output=True, text=True).stdout.strip())


def seam_check(path):
    """window 0.3 s either side of the wrap, vs program median"""
    x = decode(path)
    d = len(x) / SR
    # strip codec priming: check the decoded stream ends
    head = rms_db(x, 0.0, 0.3); tail = rms_db(x, d - 0.3, d)
    prof, _ = rms_profile(x); med = float(np.median(prof))
    return {'head': round(head, 1), 'tail': round(tail, 1), 'median': round(med, 1), 'seamDb': round(abs(head - tail), 1),
            'ok': bool(abs(head - tail) <= 3.0 and abs(head - med) <= 8 and abs(tail - med) <= 8)}


def cmd_analyze(a):
    x = decode(a.file)
    bpm, ph, _, _ = estimate_bpm(x)
    k = estimate_key(x)
    prof, hop = rms_profile(x); med = float(np.median(prof))
    d = len(x) / SR
    out = {'file': a.file, 'dur': round(d, 2), 'bpm': round(bpm, 1), 'phase': round(ph, 3), 'key': k,
           'head': round(rms_db(x, 0, 0.3), 1), 'tail': round(rms_db(x, d - 0.3, d), 1), 'median': round(med, 1)}
    print(json.dumps(out))


def cmd_cut(a):
    x = decode(a.input)
    bpm, ph, _, _ = estimate_bpm(x)
    if a.bpm: bpm_use = a.bpm; _, ph, _, _ = estimate_bpm(x)  # phase from measured; period forced
    else: bpm_use = bpm
    reg, med, prof = find_region(x, bpm_use, ph, a.bpb, a.max_body)
    res = {'key': a.key, 'bpm': round(bpm_use, 1), 'measuredBpm': round(bpm, 1), 'median': round(med, 1)}
    if not reg or (reg[1] - reg[0]) < a.min_body:
        res.update(flag='regenerate', reason=f'no qualifying region >= {a.min_body}s' + (f' (best {reg[1]-reg[0]:.1f}s)' if reg else ''))
        print(json.dumps(res)); return 2
    S, E, bar = reg
    # pre-check the seam on the float loop; slide S later / E earlier by whole bars until it passes
    pick = None
    nb = int(round((E - S) / bar))
    for ds in range(0, 5):
        for de in range(0, 5):
            n2 = nb - ds - de
            if n2 * bar < a.min_body: continue
            S2, E2 = S + ds * bar, S + ds * bar + n2 * bar
            y = build_loop(x, S2, E2, bar)
            hd, tl = rms_db(y, 0, 0.3, 1), rms_db(y, len(y) / SR - 0.3, len(y) / SR, 1)
            if abs(hd - tl) <= 3.0 and abs(hd - med) <= 8 and abs(tl - med) <= 8:
                pick = (S2, E2, y, hd, tl); break
        if pick: break
    if not pick:
        res.update(flag='seam-fail', reason='no bar-aligned cut passes the 3 dB / 8 dB seam gate'); print(json.dumps(res)); return 3
    S, E, y, hd0, tl0 = pick
    od = a.out_dir or MUSIC
    pre = int(round(a.preroll * SR))
    L = len(y) / SR
    # file = [last `preroll` s of the loop] + [loop]: the A/B crossfade in MusicManager starts the next voice at 0, which
    # is the same audio the outgoing voice is playing at loopEnd - preroll (identical signal, so a linear fade is flat)
    yf = np.concatenate([y[-pre:], y]) if pre else y
    res.update(S=round(S, 2), E=round(E, 2), body=round(E - S, 2), loop=round(L, 2), preroll=a.preroll)
    with tempfile.TemporaryDirectory() as td:
        wav = os.path.join(td, 'loop.wav'); write_wav(wav, yf)
        base = os.path.join(td, a.key)
        loudnorm_encode(wav, base)
        sc = {'head': round(hd0, 1), 'tail': round(tl0, 1), 'median': round(med, 1), 'seamDb': round(abs(hd0 - tl0), 1), 'ok': True}
        res['seam'] = sc
        q = ebur(base + '.ogg'); res['ebur'] = q
        if a.write:
            os.makedirs(od, exist_ok=True)
            for ext in ('ogg', 'm4a'):
                os.replace(base + '.' + ext, os.path.join(od, f'{a.key}.{ext}'))
            dur = duration(os.path.join(od, f'{a.key}.ogg'))
            mp = os.path.join(od, 'manifest.json')
            man = json.load(open(mp)) if os.path.exists(mp) else {}
            e = man.get(a.key, {'ogg': f'{a.key}.ogg', 'm4a': f'{a.key}.m4a'})
            e.update(loop=True, durationSec=round(dur, 2), lufs=round(q['I'], 1), loopStart=round(a.preroll, 3), loopEnd=round(a.preroll + L, 3), bpm=round(bpm_use, 1), seamDb=sc['seamDb'])
            man[a.key] = e
            json.dump(man, open(mp, 'w'), indent=2); open(mp, 'a').write('\n')
            res['written'] = True
    print(json.dumps(res)); return 0


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest='cmd', required=True)
    p = sp.add_parser('analyze'); p.add_argument('file'); p.set_defaults(fn=cmd_analyze)
    p = sp.add_parser('cut'); p.add_argument('input'); p.add_argument('--key', required=True)
    p.add_argument('--write', action='store_true'); p.add_argument('--max-body', type=float, default=120.0)
    p.add_argument('--min-body', type=float, default=60.0); p.add_argument('--bpb', type=int, default=4)
    p.add_argument('--bpm', type=float, default=None); p.add_argument('--preroll', type=float, default=0.75); p.add_argument('--out-dir'); p.set_defaults(fn=cmd_cut)
    a = ap.parse_args(); sys.exit(a.fn(a) or 0)
