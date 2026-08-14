/* design-forge measurement harness — v1
 *
 * WHY THIS EXISTS
 * ---------------
 * A design critic looking at a screenshot cannot see:
 *   - whether #f0c8ff is the #fde9ff the system specified   (it looks lavender either way)
 *   - how many accent elements are co-visible at the WORST scroll position
 *   - that two prose columns differ by 33px
 *   - that a nav is 45px off the content axis
 * Every one of those shipped through multiple rounds of screenshot review on
 * 2026-08-13. All of them are one line of arithmetic. Compute, never eyeball.
 *
 * USAGE
 *   1. Inject this whole file once (javascript_tool / page console).
 *   2. Call individual checks — each returns compact JSON.
 *        __DF.report()            // everything, terse
 *        __DF.typeLadder()        // distinct sizes in first viewport
 *        __DF.accentScan('#2b7fff')
 *   3. Output is deliberately short: some tool bridges truncate around 1kB.
 *      Use __DF.report() for triage, then the specific check for detail.
 *
 * Reads only. Never mutates the page (except a temporary scroll restore).
 */
(() => {
  const px = (v) => parseFloat(v) || 0;
  const rnd = (n, d = 1) => +n.toFixed(d);
  // el.className on an SVG element is an SVGAnimatedString, so String() gave
  // "[object SVGAnimatedString]" in every offender list containing SVG.
  const cls = (el) => {
    const c = el.className;
    const v = typeof c === 'string' ? c : (c && c.baseVal) || '';
    return v ? '.' + v.split(/\s+/)[0] : '';
  };

  // Elements that carry their own visible text (not wrapper divs inheriting it).
  const SKIP = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE', 'TITLE']);
  const shown = (el) => {
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden' || Number(cs.opacity) === 0) return false;
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0;
  };
  // Own visible text only. Without the SKIP set a <script> tag was being reported
  // as a line-height violation; without `shown` a display:none div was reported
  // as the worst contrast failure on the page.
  const textNodes = () =>
    [...document.querySelectorAll('body *')].filter((el) => {
      if (SKIP.has(el.tagName)) return false;
      if (!el.textContent.trim()) return false;
      if (![...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim())) return false;
      return shown(el);
    });

  const visibleIn = (el, top, bottom) => {
    const r = el.getBoundingClientRect();
    const t = r.top + scrollY, b = r.bottom + scrollY;
    return t < bottom && b > top && r.height > 0 && r.width > 0;
  };

  // Returns [r,g,b,a]. Dropping alpha scored `rgba(0,0,0,.3)` as pure black at
  // 21:1 when it actually composites to ~2.1:1 -- a hard AA failure reported as
  // the best contrast on the page.
  // ONLY parse rgb()/rgba(). Chrome preserves oklch()/lab()/color() in computed
  // style, and scraping digits out of `oklch(0.95 0.02 250)` yielded [0.95,0.02,250]
  // read as RGB -> a fabricated 8.8:1 for a real 1.16:1 failure. Never coerce a
  // colour space you cannot parse; return null and let the caller mark it unknown.
  const rgb = (s) => {
    if (!s) return null;
    const t = String(s).trim();
    if (t === 'transparent') return [0, 0, 0, 0];
    if (!/^rgba?\(/i.test(t)) return null;
    const m = t.match(/[\d.]+/g);
    if (!m) return null;
    const v = m.slice(0, 3).map(Number);
    v[3] = m.length > 3 ? Number(m[3]) : 1;
    return v;
  };
  const over = (fg, bg) => (fg[3] === undefined || fg[3] >= 1 ? fg
    : [0, 1, 2].map((i) => Math.round(fg[i] * fg[3] + bg[i] * (1 - fg[3]))));
  const hexToRgb = (h) => {
    const s = h.replace('#', '');
    const f = s.length === 3 ? s.split('').map((c) => c + c).join('') : s;
    return [0, 2, 4].map((i) => parseInt(f.slice(i, i + 2), 16));
  };
  // Compare RGB only. `rgb()` now returns a 4th alpha channel, and comparing it
  // element-wise against a 3-channel hex target made every comparison NaN --
  // silently turning every accent scan into "not found". Regression caught by
  // the probe page, not by reading.
  const sameColor = (a, b, tol = 2) =>
    a && b && [0, 1, 2].every((i) => Math.abs(a[i] - b[i]) <= tol) && (a[3] === undefined || a[3] > 0.5);

  // WCAG 2.x relative luminance + contrast ratio.
  const lum = ([r, g, b]) => {
    const f = (c) => {
      c /= 255;
      return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
    };
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
  };
  const contrast = (a, b) => {
    const [l1, l2] = [lum(a), lum(b)].sort((x, y) => y - x);
    return (l1 + 0.05) / (l2 + 0.05);
  };

  // Walk up for the first non-transparent background — what the text actually sits on.
  const effectiveBg = (el) => {
    let n = el;
    while (n && n !== document.documentElement) {
      const cs = getComputedStyle(n);
      // A gradient or image background carries no backgroundColor. Walking past it
      // measures the text against whatever is BEHIND the button, which is a
      // fabricated number. Bail out honestly instead.
      const c = cs.backgroundColor;
      const cv = rgb(c);
      // An opaque background-color is measurable even with an image on top of it.
      // Only give up when there is an image AND nothing solid behind it.
      if (cv && cv[3] > 0.5) return cv;
      if (cs.backgroundImage && cs.backgroundImage !== 'none') return null;
      n = n.parentElement;
    }
    return [255, 255, 255];
  };

  const visualPresentation = {};

  const API = {
    /* U1 — distinct rendered type sizes in the first viewport.
       Most systems allow 3. Counts SIZES, not elements. */
    typeLadder(cap = 3) {
      const vh = innerHeight;
      const sizes = new Set();
      textNodes().forEach((el) => {
        if (visibleIn(el, 0, vh)) sizes.add(rnd(px(getComputedStyle(el).fontSize)));
      });
      const list = [...sizes].sort((a, b) => a - b);
      return { sizes: list, count: list.length, cap, checked: list.length, pass: list.length > 0 && list.length <= cap };
    },

    /* U5 — minimum body size, with the standard uppercase+tracking exemption
       for caption/label tiers. Returns the offenders, not just a count. */
    typeFloor(floor = 16, minTrack = 0.08) {
      const bad = [];
      textNodes().forEach((el) => {
        const cs = getComputedStyle(el);
        const fs = px(cs.fontSize);
        if (fs >= floor) return;
        const upper = cs.textTransform === 'uppercase';
        const track = px(cs.letterSpacing) / fs;
        if (upper && track >= minTrack) return; // exempt label tier
        bad.push({
          sel: el.tagName.toLowerCase() + cls(el),
          size: rnd(fs), upper, track: rnd(track, 3),
          text: el.textContent.trim().slice(0, 24),
        });
      });
      return { floor, checked: textNodes().length, violations: bad.length,
               pass: textNodes().length > 0 && bad.length === 0, offenders: bad.slice(0, 8) };
    },

    /* THE IMPORTANT ONE.
       A per-viewport rule ("accent at most N times per screen") cannot be
       falsified by a screenshot, because a screenshot IS one viewport and you
       picked it. Slide a viewport-height window down the whole document and
       return the worst case. This found defects on two separate pages that
       three rounds of screenshot review had walked past. */
    accentScan(accent, cap = 3, step = 20) {
      const target = typeof accent === 'string' && accent.startsWith('#') ? hexToRgb(accent) : rgb(accent);
      if (!target) return { error: 'pass a hex like #2b7fff or an rgb() string' };
      const raw = [...document.querySelectorAll('body *, svg *')].filter((el) => {
        const cs = getComputedStyle(el);
        // fill/stroke matter: the house style tells you to hand-author SVG charts
        // where one bar takes the accent, and colour/background never sees those.
        return ['color', 'backgroundColor', 'fill', 'stroke', 'borderTopColor', 'outlineColor']
          .some((k) => sameColor(rgb(cs[k]), target));
      });
      // Subtree dedup: `<div class=n>4-12<span>hrs</span></div>` is ONE accent use,
      // not two. Keep only the outermost element of each accent-coloured subtree.
      // (Learned the hard way -- the naive text-compare version reported 5 for 3.)
      const els = raw.filter((el) => !raw.some((o) => o !== el && o.contains(el)));
      const boxes = els.map((el) => {
        const r = el.getBoundingClientRect();
        const fixed = /fixed|sticky/.test(getComputedStyle(el).position);
        // Fixed/sticky elements are in frame at EVERY scroll position. Treating
        // them as living at one y is a false PASS on the check this file calls
        // the important one.
        return fixed
          ? { t: -Infinity, b: Infinity, fixed: true, x: el.textContent.trim().slice(0, 18) || '(fixed)' }
          : { t: r.top + scrollY, b: r.bottom + scrollY, x: el.textContent.trim().slice(0, 18) };
      });
      const vh = innerHeight, doc = document.documentElement.scrollHeight;
      let worst = 0, at = 0, who = [];
      for (let y = 0; y <= Math.max(0, doc - vh); y += step) {
        const vis = boxes.filter((o) => o.t < y + vh && o.b > y);
        if (vis.length > worst) { worst = vis.length; at = y; who = vis.map((o) => o.x); }
      }
      // 🔴 A CEILING WITHOUT A FLOOR IS NOT A CHECK. `worst <= cap` is trivially
      // true when the accent appears ZERO times -- which is precisely the
      // wrong-hex defect this harness exists to catch. Absent != restrained.
      const absent = boxes.length === 0;
      return {
        accent, totalOnPage: boxes.length, worstCaseInOneViewport: worst, atScrollY: at, cap,
        absent, pass: !absent && worst <= cap,
        note: absent ? 'ACCENT NOT FOUND ON PAGE — either the wrong hex is shipping, or this page does not use the accent at all. Not a pass.' : undefined,
        elements: who,
      };
    },

    /* P5 — one prose measure per page. Two columns 33px apart reads as sloppy
       and is invisible unless you measure both. */
    proseMeasure(maxWidth = 680, tolerance = 8) {
      const w = new Map();
      // Establish the modal body size first, so we can exclude display type.
      const freq = new Map();
      textNodes().forEach((el) => {
        const f = rnd(px(getComputedStyle(el).fontSize));
        freq.set(f, (freq.get(f) || 0) + el.textContent.trim().length);
      });
      // Weight by text VOLUME, not element count: 12 labels outvoted one real
      // paragraph and set body=13, after which the 1.3x cutoff excluded the prose
      // the check exists to measure.
      const body = [...freq.entries()].sort((a, b) => b[1] - a[1])[0]?.[0] || 16;
      const DISPLAY = new Set(['H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'BLOCKQUOTE', 'Q', 'FIGCAPTION']);
      textNodes().forEach((el) => {
        const cs = getComputedStyle(el);
        const fs = px(cs.fontSize);
        if (fs < 15) return;
        if (DISPLAY.has(el.tagName)) return;      // headings are not prose measure
        if (fs > body * 1.3) return;              // nor is display type at body-ish length
        const t = el.textContent.trim();
        if (t.length < 120) return;               // a real paragraph, not a label or a stat caption
        // Content box, not border box: padding was inventing a second measure on
        // the check whose entire job is spotting a second measure.
        const width = rnd(el.getBoundingClientRect().width - px(cs.paddingLeft) - px(cs.paddingRight)
          - px(cs.borderLeftWidth) - px(cs.borderRightWidth));
        if (width < 200) return;
        const key = [...w.keys()].find((k) => Math.abs(k - width) <= tolerance) ?? width;
        w.set(key, (w.get(key) || 0) + 1);
      });
      const measures = [...w.entries()].map(([px_, n]) => ({ width: px_, blocks: n })).sort((a, b) => b.blocks - a.blocks);
      const over = measures.filter((m) => m.width > maxWidth);
      return {
        distinctMeasures: measures.length, measures, maxWidth, checked: measures.length,
        overCap: over,
        pass: measures.length === 1 && over.length === 0,
        note: measures.length === 0 ? 'NO PROSE MEASURED — not a pass. Either the page has no body copy, or the size filter excluded it.' : undefined,
      };
    },

    /* HOUSE RULE, not normative. Some real systems (Carbon, Spectrum) ship shadow
       elevation ramps, and this would fail a correct implementation of them.
       Pass allow>0 to permit a bounded number. */
    shadows(allow = 0) {
      const hits = [...document.querySelectorAll('body *')]
        .filter((el) => {
          const sh = getComputedStyle(el).boxShadow;
          if (!sh || sh === 'none') return false;
          // A zero-blur ring (`0 0 0 1px #ddd`) is a hairline border, which is the
          // technique this rule RECOMMENDS. Only blur counts as elevation.
          return /(-?[\d.]+px)\s+(-?[\d.]+px)\s+(-?[\d.]+)px/.test(sh)
            && parseFloat(RegExp.$3) > 0;
        })
        .map((el) => el.tagName.toLowerCase() + cls(el));
      return { tier: 'house', count: hits.length, allow, pass: hits.length <= allow, elements: [...new Set(hits)].slice(0, 8) };
    },

    /* U6 — vertical rhythm. Flags sections whose padding drifts, which is the
       classic symptom of a shorthand rule clobbering a longhand one. */
    rhythm(min = 96, sel = 'section, header, footer, main > div, [class*="section"]') {
      // The old selector was 'section, header, footer' only, so ANY div-based page
      // (i.e. most framework output) returned an empty set and a green PASS.
      const rows = [...document.querySelectorAll(sel)].map((el) => {
        const cs = getComputedStyle(el);
        return { el: el.tagName.toLowerCase() + (el.id ? '#' + el.id : ''), top: rnd(px(cs.paddingTop)), bottom: rnd(px(cs.paddingBottom)) };
      });
      const vals = rows.flatMap((r) => [r.top, r.bottom]).filter((v) => v > 0);
      const under = rows.filter((r) => (r.top && r.top < min) || (r.bottom && r.bottom < min));
      return { sections: rows, checked: rows.length, distinctValues: [...new Set(vals)].sort((a, b) => a - b),
               min, underMin: under, pass: rows.length > 0 && under.length === 0,
               note: rows.length === 0 ? 'NO SECTIONS MATCHED — not a pass, pass a selector that fits this page.' : undefined };
    },

    /* The nav-axis bug: a shorthand `padding: 24px 0` on a flex child silently
       cancels the horizontal padding it was inheriting, so the nav sits on a
       different left edge than every other element. Invisible at a glance,
       obvious in a list of x-positions. */
    alignmentAxes(tolerance = 2) {
      const edges = new Map();
      textNodes().forEach((el) => {
        const r = el.getBoundingClientRect();
        if (r.width < 40 || r.height < 6) return;
        const cs = getComputedStyle(el);
        if (cs.textAlign === 'center' || cs.textAlign === 'right') return;
        const x = rnd(r.left);
        const key = [...edges.keys()].find((k) => Math.abs(k - x) <= tolerance) ?? x;
        edges.set(key, (edges.get(key) || 0) + 1);
      });
      const axes = [...edges.entries()].map(([x, n]) => ({ x, elements: n })).sort((a, b) => b.elements - a.elements);
      return { distinctLeftEdges: axes.length, axes: axes.slice(0, 8), note: 'Outliers with 1-2 elements are usually a shorthand-padding bug, not a design choice.' };
    },

    /* WCAG 2.2 contrast, computed. 4.5:1 normal text, 3:1 large
       (>=24px, or >=18.66px when bold). */
    contrast(level = 'AA') {
      const need = { AA: [4.5, 3], AAA: [7, 4.5] }[level] || [4.5, 3];
      const fails = [], indeterminate = [];
      textNodes().forEach((el) => {
        const cs = getComputedStyle(el);
        const fg0 = rgb(cs.color);
        if (!fg0) { indeterminate.push(el.tagName.toLowerCase() + ' (unsupported colour space)'); return; }
        // Element opacity renders near-identically to an equivalent rgba alpha and
        // was not being composited.
        const op = Number(cs.opacity);
        if (op < 1) fg0[3] = (fg0[3] === undefined ? 1 : fg0[3]) * op;
        const bg = effectiveBg(el);
        const fg = bg ? over(fg0, bg) : fg0;
        if (!bg) { indeterminate.push(el.tagName.toLowerCase() + cls(el)); return; }
        const fs = px(cs.fontSize), wt = parseInt(cs.fontWeight) || 400;
        const large = fs >= 24 || (fs >= 18.66 && wt >= 700);
        const ratio = contrast(fg, bg);
        const min = large ? need[1] : need[0];
        if (ratio < min)
          fails.push({
            sel: el.tagName.toLowerCase() + cls(el),
            ratio: rnd(ratio, 2), need: min, size: rnd(fs), large,
            text: el.textContent.trim().slice(0, 22),
          });
      });
      return {
        level, checked: textNodes().length, failures: fails.length,
        // "An indeterminate is not a pass" -- stated twice in the docs, and the
        // code disagreed. A page with a body gradient reported PASS with every
        // real failure parked in `indeterminate`.
        pass: textNodes().length > 0 && fails.length === 0 && indeterminate.length === 0,
        worst: fails.sort((a, b) => a.ratio - b.ratio).slice(0, 8),
        // Over a gradient/image the ratio is not computable from CSS alone.
        // These need a pixel sample, and must never be silently reported as passing.
        indeterminate: [...new Set(indeterminate)],
      };
    },

    /* WCAG 2.2 SC 1.4.8 Visual Presentation (AAA) — five binary typographic
       mechanisms in one normative criterion, and almost nobody cites it.
       Line width <=80 chars, not justified, line-height >=1.5 within a
       paragraph, paragraph spacing >=1.5x the line spacing.
       https://www.w3.org/WAI/WCAG22/Understanding/visual-presentation.html */
    visualPresentation(maxChars = 80) {
      const out = { maxChars, justified: [], longLines: [], tightLeading: [], paraSpacing: [] };
      textNodes().forEach((el) => {
        const cs = getComputedStyle(el);
        const fs = px(cs.fontSize);
        const t = el.textContent.trim();
        if (t.length < 120 || fs < 12) return;
        const sel = el.tagName.toLowerCase() + cls(el);

        if (cs.textAlign === 'justify') out.justified.push(sel);

        // Characters per line, from the rendered box and the real average glyph
        // advance (measured on the element's own font, not assumed at 0.5em).
        const w = el.getBoundingClientRect().width;
        const cvs = visualPresentation._c || (visualPresentation._c = document.createElement('canvas').getContext('2d'));
        cvs.font = `${cs.fontStyle} ${cs.fontWeight} ${fs}px ${cs.fontFamily}`;
        const adv = cvs.measureText('abcdefghijklmnopqrstuvwxyz ').width / 27;
        const chars = Math.round(w / adv);
        if (chars > maxChars) out.longLines.push({ sel, chars, width: rnd(w) });

        const lh = cs.lineHeight === 'normal' ? fs * 1.2 : px(cs.lineHeight);
        if (lh / fs < 1.5) out.tightLeading.push({ sel, ratio: rnd(lh / fs, 2) });

        const mb = px(cs.marginBottom);
        // `mb > 0` skipped margin:0 entirely -- the worst possible case passed.
        if (mb < lh * 1.5) out.paraSpacing.push({ sel, margin: rnd(mb), need: rnd(lh * 1.5) });
      });
      const fails = out.justified.length + out.longLines.length + out.tightLeading.length + out.paraSpacing.length;
      return { ...out, failures: fails, pass: fails === 0, sc: '1.4.8 (AAA)' };
    },

    /* WCAG 2.2 SC 2.5.8 Target Size Minimum (AA) = 24x24 CSS px.
       SC 2.5.5 Enhanced (AAA) = 44x44. Lighthouse is stricter still at 48x48.
       Inline links in a text block are exempt from 2.5.8. */
    targetSize(min = 24) {
      const small = [];
      const ROLES = 'button,link,checkbox,radio,switch,tab,menuitem,menuitemcheckbox,option,slider,combobox,spinbutton';
      const sel = 'a, button, input, select, textarea, summary, [tabindex]:not([tabindex="-1"]), [onclick], '
        + ROLES.split(',').map((r) => `[role="${r}"]`).join(', ');
      document.querySelectorAll(sel).forEach((el) => {
        const r = el.getBoundingClientRect();
        if (r.width === 0 || r.height === 0) return;
        // Exemption: a link inline within a sentence of text.
        if (el.tagName === 'A' && getComputedStyle(el).display.includes('inline')) {
          const p = el.parentElement;
          if (p && p.textContent.trim().length > el.textContent.trim().length + 20) return;
        }
        if (r.width < min || r.height < min)
          small.push({
            sel: el.tagName.toLowerCase() + cls(el),
            w: rnd(r.width), h: rnd(r.height), text: el.textContent.trim().slice(0, 20),
          });
      });
      const n = document.querySelectorAll(sel).length;
      return { min, checked: n, undersized: small.length, pass: small.length === 0, offenders: small.slice(0, 8), sc: '2.5.8 (AA)',
               note: n === 0 ? 'no interactive elements found' : undefined };
    },

    /* Two radii and two weights is a system. Six of each is an accident. */
    tokens() {
      const radii = new Set(), weights = new Set(), families = new Set();
      [...document.querySelectorAll('body *')].forEach((el) => {
        const cs = getComputedStyle(el);
        const r = px(cs.borderTopLeftRadius); if (r > 0) radii.add(rnd(r));
        if (el.textContent.trim()) {
          weights.add(parseInt(cs.fontWeight) || 400);
          families.add(cs.fontFamily.split(',')[0].replace(/["']/g, '').trim());
        }
      });
      return {
        radii: [...radii].sort((a, b) => a - b),
        weights: [...weights].sort((a, b) => a - b),
        families: [...families],
      };
    },

    /* Triage. Run this first, then drill into whatever fails. */
    report(opts = {}) {
      const { accent, floor = 16, cap = 3, measure = 680 } = opts;
      const t = this.typeLadder(cap), f = this.typeFloor(floor), s = this.shadows();
      const m = this.proseMeasure(measure), c = this.contrast(), k = this.tokens();
      const vp = this.visualPresentation(), ts = this.targetSize();
      // rhythm + alignmentAxes were documented as part of report() and not called.
      // They are the ONLY checks that catch the padding-shorthand regression this
      // skill names as its most common defect, so the prescribed regression pass
      // could not catch the prescribed regression.
      const rh = this.rhythm(), ax = this.alignmentAxes();
      const a = accent ? this.accentScan(accent, cap) : null;
      return {
        typeLadder: `${t.count}/${t.cap} ${t.pass ? 'PASS' : 'FAIL'} [${t.sizes}]`,
        typeFloor: `${f.violations} under ${floor}px ${f.pass ? 'PASS' : 'FAIL'}`,
        accent: a ? (a.absent ? `NOT FOUND ON PAGE — FAIL (wrong hex, or unused)` : `worst ${a.worstCaseInOneViewport}/${a.cap} @y=${a.atScrollY}, ${a.totalOnPage} total ${a.pass ? 'PASS' : 'FAIL'}`) : 'not checked (pass {accent:"#hex"})',
        proseMeasure: (m.distinctMeasures === 0 ? 'NO PROSE MEASURED — FAIL' : `${m.distinctMeasures} measure(s) ${m.pass ? 'PASS' : 'FAIL'} ${JSON.stringify(m.measures.map((x) => x.width))}`),
        contrast: `${c.failures} WCAG AA failures ${c.pass ? 'PASS' : 'FAIL'}` + (c.indeterminate.length ? ` — ${c.indeterminate.length} NOT MEASURABLE (gradient/unsupported colour space); sample by hand, this is not a pass` : ''),
        wcag148: `${vp.failures} failures ${vp.pass ? 'PASS' : 'FAIL'} (measure/justify/leading/para-spacing)`,
        targetSize: `${ts.undersized} under 24px ${ts.pass ? 'PASS' : 'FAIL'}`,
        rhythm: `${rh.checked} sections, ${rh.underMin.length} under ${rh.min}px ${rh.pass ? 'PASS' : 'FAIL'}`,
        alignment: `${ax.distinctLeftEdges} left edges` + (ax.axes.filter((x) => x.elements <= 2).length ? ` — ${ax.axes.filter((x) => x.elements <= 2).length} outlier(s), usually a shorthand-padding bug` : ''),
        shadows_house: `${s.count} ${s.pass ? 'PASS' : 'FAIL'} (house rule, not normative)`,
        tokens: `radii[${k.radii}] weights[${k.weights}]`,
        viewport: [innerWidth, innerHeight],
        caveat: 'One page, one state, one width. Says nothing about hover/focus, dark mode, error/empty states, mobile, RTL or print.',
      };
    },
  };

  window.__DF = API;
  return 'design-forge harness ready — __DF.report({accent:"#hex"})';
})();
