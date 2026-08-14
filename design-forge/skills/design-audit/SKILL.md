---
name: design-audit
description: Measure a rendered page against design mechanisms instead of eyeballing it. Computes type ladder, size floor, worst-case accent count across every scroll position, prose measure, shadows, vertical rhythm, alignment axes, WCAG contrast, and token counts. Use before declaring any page done, as the evidence layer under design-loop, or any time a design claim needs a number instead of an opinion. Triggers on "design audit", "measure this page", "check the design", "is this accessible", "audit the CSS".
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep]
---

# Design Audit

**The one-line case for this skill:** on 2026-08-13 three portfolio pages went through **four rounds
of a three-critic design loop** and were declared finished. This harness was then run against them
and found **23 real defects in under two minutes** — including a colour that was simply the wrong hex,
seventeen WCAG failures, and a type ladder violation on a page nobody had checked for one.

Then a red team found bugs in the harness, and the fixed version found **more still** on the same
"clean" pages: undersized tap targets, a rhythm break, and alignment outliers that the old `report()`
never even ran. **23 was an undercount, and the number is not the point** — the point is that none of
it was visible.

Not because the critics were lazy. Because **the defects were not visible.** No amount of looking at
a screenshot tells you that `#f0c8ff` is not the `#fde9ff` the system specified, or that four accent
elements become co-visible at scroll position 1740.

> **Compute, never eyeball.** Anything expressed as an exact value or a threshold gets measured.
> Looking is for judgment; arithmetic is for facts.

---

## The four things a screenshot structurally cannot do

These are not "hard to see." They are **impossible to see**, and each one shipped through multiple
rounds of human-and-model review.

1. **Verify an exact value.** Two lavenders forty units apart look identical. A spec that names a hex
   can only be checked by sampling the hex.
2. **Falsify a per-viewport rule.** "At most three accents per screen" cannot be disproved by a
   screenshot, because a screenshot *is* one viewport and **you chose which one**. You have to slide
   a window down the whole document and take the worst case.
3. **Compare two numbers far apart in the page.** A hero column at 655px and a story column at 688px
   never appear in the same frame, so the inconsistency is invisible.
4. **Compute a ratio.** WCAG contrast is a formula over relative luminance. Nobody eyeballs 4.21
   versus 4.50.

---

## Running it

The harness is `${CLAUDE_PLUGIN_ROOT}/scripts/audit/measure.js`. It is read-only, has no
dependencies, and defines `window.__DF`.

**1. Serve the page.** `file://` is blocked for scripted evaluation in most browser bridges.

```bash
cd <dir with the html>
cp "${CLAUDE_PLUGIN_ROOT}/scripts/audit/measure.js" .
python3 -m http.server 8899 &
```

**2. Load the harness into the page.** A `<script src>` tag is async — the injection call and the
first measurement call must be **separate** tool calls, or `__DF` will be undefined.

```js
// call 1
(()=>{const s=document.createElement('script');s.src='/measure.js';document.head.appendChild(s);return 'ok';})()
// call 2 (separate round-trip)
JSON.stringify(__DF.report({ accent:'#2b7fff', cap:3, floor:16, measure:680 }))
```

**3. Triage, then drill.** `report()` is deliberately terse because some bridges truncate around 1kB.
Get the summary, then call the individual check for the offender list.

⚠️ **Always cache-bust** (`page.html?v=2`, `measure.js?v=2`) after an edit. A stale copy silently
reports the pre-fix numbers, which reads exactly like a fix that did not work.

---

## The checks

| Call | Answers | Default |
|---|---|---|
| `typeLadder(cap)` | How many distinct type sizes render in the first viewport? | 3 |
| `typeFloor(px, track)` | What text is below the size floor without the uppercase+tracking exemption? | 16px / 0.08em |
| `accentScan(hex, cap)` | **Worst-case** accent count in any viewport-height window | 3 |
| `proseMeasure(max)` | How many distinct prose column widths exist, and do any exceed the cap? | 680px |
| `shadows(allow)` | Any blur-based elevation? ⚠️ **house rule, not normative** | 0 |
| `rhythm(min)` | Section padding values, and any under the minimum | 96px |
| `alignmentAxes()` | Distinct left edges — outliers are usually a shorthand-padding bug | — |
| `contrast(level)` | WCAG 2.2 AA/AAA failures, computed | AA |
| `tokens()` | Distinct radii, weights, families | — |
| `targetSize(min)` | Interactive targets under the minimum (WCAG 2.5.8) | 24px |
| `visualPresentation()` | WCAG 1.4.8: measure, justification, leading, paragraph spacing | — |
| `report(opts)` | All of the above, one line each — **and it now genuinely runs all of them** | — |

### 🔴 Read this before you trust a PASS

A red-team pass on 2026-08-13 found that several checks returned **PASS for things they could not
see**. All are fixed, and the lesson generalises to any check you add:

- **A ceiling without a floor is not a check.** `accentScan` passed `worst <= cap` — trivially true
  when the accent appears **zero** times, which is exactly the wrong-hex defect the harness exists to
  catch. **Absent is not restrained.** It now fails, loudly, and says why.
- **An empty result set is not a pass.** `rhythm()` looked only for `section, header, footer`, so any
  div-based page (most framework output) matched nothing and reported green. Every check now returns
  `checked: n` and refuses to PASS at `n === 0`.
- **`report()` must run what it claims.** It documented `rhythm()` and `alignmentAxes()` and called
  neither — and those two are the *only* checks that catch the padding-shorthand regression this skill
  names as its most common defect. The prescribed regression pass could not catch the prescribed
  regression.
- **Alpha is not decoration.** Contrast dropped the alpha channel, scoring `rgba(0,0,0,.3)` as pure
  black at 21:1 when it composites to **2.1:1**, a hard AA failure. `rgba()` is how most systems author
  a muted tier, so this under-reported the most common real defect on the axis the harness is proudest
  of.
- **Invisible elements are not defects.** A `display:none` div was being reported as the worst contrast
  failure on the page, and a `<script>` tag as a line-height violation.
- **Selectors rot.** `targetSize` keyed off `[onclick]`, which no framework has emitted since ~2014, so
  it passed vacuously on every custom control. It now covers ARIA roles and `tabindex`.

**And one I introduced while fixing the others:** widening `rgb()` to carry alpha broke `sameColor`,
which compared element-wise against a 3-channel target — `undefined` in the 4th slot made every
comparison `NaN`, silently turning every accent scan into "not found." **Caught by the probe page, not
by re-reading the diff.** Keep `scripts/audit/test-contrast.js` and a probe page in the loop.

### Tiers — not every rule is a standard

`shadows()` is a **house rule**, and it is now labelled `tier: 'house'` in its output. IBM Carbon and
Adobe Spectrum both ship shadow elevation ramps, so a correct implementation of either would "fail"
it. Normative (WCAG) rules, house taste, and per-project rules all print with the same PASS/FAIL
grammar, and that is how a taste becomes invisible. **Say which tier a rule belongs to.**

### Reading the results honestly

- **`accentScan` dedupes by subtree.** `<div class=n>4-12<span>hrs</span></div>` is **one** accent
  use, not two. An earlier version compared text instead and reported 5 for 3.
- **`contrast` returns `indeterminate` separately.** Text over a gradient or image has no CSS
  background colour to measure against. The harness refuses to invent a number and lists those
  elements for manual pixel sampling. **An indeterminate is not a pass.**
- **`proseMeasure` reports, it does not judge.** Two measures can be legitimate (a lede column and a
  table cell are different components). Two measures on the *same* component is the defect. Look
  before you fix.
- **Everything is worst-case at the current viewport width.** Re-run at mobile and at a wide desktop;
  a 4-across stat grid that passes at 900px can fail the accent cap at 1440px.

### 🔴 The honest limit: one page, one state, one width

`report()` now prints this caveat in its own output, because it is the biggest thing the harness
cannot see. Every number here describes **a single static render**. Design quality is a property of a
*set* of renders. The harness says nothing about:

**hover / focus / active / disabled** (SC 2.4.7 Focus Visible is **Level AA** and is not checked
anywhere) · **dark mode** · **error, empty, loading and partial states** · **mobile and tablet
widths** · **long-content overflow and truncation** · **RTL and i18n** · **print** (a dark board
readout prints as white-on-white) · **keyboard operability and focus order** · **the accessibility
tree** — headings, landmarks, `alt`, labels, accessible names, `lang`.

Two AA success criteria are implemented out of roughly fifty-five in WCAG 2.2. Treat a green report as
*"conformant on the axes measured,"* never as *"accessible"* and never as *"good."*

---

## Where this sits in a design loop

`design-loop` runs builders and fresh-context critics. This is the **evidence layer beneath the
critics**, and it changes what a critic is for.

- **Before a critic runs:** audit the page. Anything the harness settles is settled — do not spend a
  critic's judgment on arithmetic it will do worse.
- **What critics are actually good at:** taste, hierarchy, whether the thing is any good, whether the
  copy earns its claims. Give them the judgment and take the measurement away from them.
- **When a critic reports a number, check it.** A craft critic once failed a page for "headline
  strokes 6× heavier than body" — it had compared a 96px headline to 16px body. Stroke width scales
  with size. The finding was rejected on method and later vindicated by a correct stem-to-cap
  measurement. **A critic's number is a claim, not a fact.**

### The regression pass, which is the one people skip

On the run that produced this harness, **most defects were introduced by the previous round's fix**,
not present in the original build. A `padding: 0 40px` shorthand silently cancelled section rhythm on
three separate pages. A proof rail added to fix a grid gap broke the type ladder it was added to
repair.

**So: after every fix, re-run the FULL report, not just the check you were fixing.** The cost is one
tool call. The alternative is shipping a page that passes the mechanism you were looking at and fails
two you were not.

---

## Writing mechanisms the harness can check

The point of a bar is that a fresh context can check it. Three tests before a mechanism goes in:

1. **Is it checkable?** "Feels premium" is not. "One accent, at most 3 per viewport" is.
2. **Is it achievable *alongside the other rules*?** This is the one that gets missed. A bar once
   required display type at `≥12vw` *and* the supporting layer above the fold. Three lines at 12vw
   plus nav and CTAs is ~800px against a 648px viewport. **Two mechanisms contradicted each other and
   no version of the page could pass both.** Before building, do the arithmetic on your own rules.
3. **Does it measure the thing, or a proxy for it?** `12vw` was copied from a reference's *rendered
   size* without checking it against the content that had to sit beside it. The rule that replaced it
   measured the actual intent: glyph aspect ratio ≤0.80.

**Ship a contrast mechanism in every bar.** A bar that checks colour *identity* (is it the right hex)
but never colour *legibility* will pass a page with seventeen WCAG failures. That happened.

---

## Related

- `design-loop` — the builder/critic loop this feeds
- `art-department` — the visual-deliverable playbook and asset library
- `de-sloppifier` — the copy equivalent: mechanisms for prose instead of pixels
