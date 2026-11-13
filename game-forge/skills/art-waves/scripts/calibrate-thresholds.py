#!/usr/bin/env python3
"""calibrate-thresholds.py: derive art-measure.thresholds.json from YOUR labelled good and bad sprites.

  python3 -I calibrate-thresholds.py --good DIR_OF_GOOD_SPRITES --bad LABEL=DIR [--bad LABEL2=DIR2 ...] \\
        [--about metric=LABEL,LABEL2 ...] [--out art-measure.thresholds.json]

The rule (same for every metric, nothing hand-tuned):
  g = worst value over the GOOD set; b = 10th percentile of the pooled BAD values (worst-side, for the BAD sets the
  metric is "about"; by default every BAD set). If g and b do not separate by at least 10% of the larger value the
  metric is INFO (printed, never judged). Otherwise warn = g + 0.5 (b - g), fail = g + 0.75 (b - g), mirrored for
  "min" metrics. ref_tolerance (for art-measure --ref) = the p5..p95 spread of the GOOD set.
Why: a limit invented by eye drifts; a limit read off the owner's own good and bad examples can be defended.
Feed it frames the owner has actually judged (good = "more like this", bad = "this is wrong"), at least ~10 each, from
the same model/render, and pose-split: fit on some poses, check others (a fit on one pose overfits that pose).

--about narrows a metric to the BAD sets that show that defect (a "too dark" set should not set the outline limit).
Needs art-measure.py beside this file, plus Pillow < 13, numpy, scipy. Only sprite metrics are calibrated here;
screen thresholds (hatch/ink tiles) follow the same rule, see references/measure-and-audit.md.
"""
import argparse, glob, importlib.util, json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('am', os.path.join(HERE, 'art-measure.py'))
am = importlib.util.module_from_spec(spec); spec.loader.exec_module(am)

# metric -> direction of badness ("max": bigger is worse; "min": smaller is worse)
DIRS = {
    'tone.near_black_pct': 'max', 'tone.L_p10': 'min', 'tone.L_median': 'min', 'tone.sat_mean': 'max', 'tone.moss_pct': 'max',
    'outline.ink_weight_px': 'max', 'outline.coverage_pct': 'max', 'outline.contour_L_mean': 'min', 'outline.width_px': 'max',
    'feather.ramp_px': 'max', 'feather.partial_ring_pct': 'max',
}
HATCH = ('hatch.hatch_pct', 'hatch.largest_area_pct')


def images(d):
    out = []
    for e in ('png', 'webp'):
        out += glob.glob(os.path.join(d, f'**/*.{e}'), recursive=True)
    return sorted(out)


def measure_set(d):
    rows = []
    for f in images(d):
        arr, _ = am.load(f)
        rows.append(am.flat(am.measure_sprite(arr)))
    if not rows:
        sys.exit(f'no png/webp images in {d}')
    return rows


def derive(good, bad, d):
    if d == 'min':
        good, bad = [-x for x in good], [-x for x in bad]
    g = max(good); b = float(np.percentile(bad, 10))
    if b - g <= 0.1 * max(abs(g), abs(b), 1e-9):
        return None
    w, f = g + 0.5 * (b - g), g + 0.75 * (b - g)
    if d == 'min':
        w, f, g, b = -w, -f, -g, -b
    return {'dir': d, 'warn': round(w, 3), 'fail': round(f, 3), 'good_worst': round(g, 3), 'bad_p10': round(b, 3)}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--good', required=True)
    ap.add_argument('--bad', action='append', required=True, metavar='LABEL=DIR')
    ap.add_argument('--about', action='append', default=[], metavar='METRIC=LABEL,LABEL')
    ap.add_argument('--out', default=os.path.join(HERE, 'art-measure.thresholds.json'))
    a = ap.parse_args()
    good = measure_set(a.good)
    bads = {}
    for b in a.bad:
        lab, _, d = b.partition('=')
        if not d:
            sys.exit('--bad needs LABEL=DIR')
        bads[lab] = measure_set(d)
    about = {}
    for x in a.about:
        m, _, labs = x.partition('=')
        about[m] = [l for l in labs.split(',') if l]
        for l in about[m]:
            if l not in bads:
                sys.exit(f'--about names unknown BAD label {l}')
    th = {'_provenance': f'calibrate-thresholds.py: good={len(good)} sprites, bad sets={ {k: len(v) for k, v in bads.items()} }',
          'sprite': {'metrics': {}, 'info_only': [], 'ref_tolerance': {}},
          'screen': {'hatch_tile_pct': 35, 'moss_tile_pct': 3, 'metrics': {}, 'info_only': []}}
    for m, d in DIRS.items():
        gv = [r[m] for r in good]
        bv = [r[m] for l in (about.get(m) or list(bads)) for r in bads[l]]
        t = derive(gv, bv, d)
        if t:
            th['sprite']['metrics'][m] = t
        else:
            th['sprite']['info_only'].append(m)
        g = np.array(gv)
        th['sprite']['ref_tolerance'][m] = round(float(np.percentile(g, 95) - np.percentile(g, 5)) + 1e-3, 3)
    for m in HATCH:  # no bad hatched sample assumed: warn-only at the worst good value
        gm = max(r[m] for r in good)
        th['sprite']['metrics'][m] = {'dir': 'max', 'warn': round(gm, 3), 'fail': 1e9, 'good_worst': round(gm, 3), 'bad_p10': None,
                                      'note': 'warn only: no bad hatched sprite in the calibration set'}
        g = np.array([r[m] for r in good])
        th['sprite']['ref_tolerance'][m] = round(float(np.percentile(g, 95) - np.percentile(g, 5)) + 1e-3, 3)
    json.dump(th, open(a.out, 'w'), indent=1)
    print(f'wrote {a.out}: {len(th["sprite"]["metrics"])} judged metrics, INFO only: {", ".join(th["sprite"]["info_only"]) or "none"}')
    for m, t in th['sprite']['metrics'].items():
        print(f'  {m:28s} {t["dir"]}  good_worst {t["good_worst"]}  bad_p10 {t["bad_p10"]}  warn {t["warn"]}  fail {t["fail"]}')


if __name__ == '__main__':
    main()
