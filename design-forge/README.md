# Design Forge

A design plugin for Claude Code. Seven skills covering critique, measurement, asset generation,
site building, and copy editing.

**The thesis, in one line:** *judgment stays with the model, arithmetic goes to a harness.*

That is not a style preference. Vision models score **58.57%** on trivial geometric tasks and
**56.84% on counting** things in an image. Open-ended AI design audit runs an **80.1% false-positive
rate**, 8.9% of it actively harmful advice. Ask a model whether a page is any good and you get
something useful. Ask it to count accents or verify a hex and you get confident noise.

So this plugin splits the job. `design-audit` computes anything expressed as a number. `design-loop`
spends fresh-context critics on taste, hierarchy, and whether the thing actually works.

<sub>Sources and verification tiers for every figure above: [`references/mechanisms.md`](references/mechanisms.md)</sub>

---

## Install

```bash
git clone <this repo> && cd design-forge
./scripts/install.sh          # plugin only — runs on python3 + a browser
./scripts/install.sh --tools  # + ImageMagick, Inkscape, Graphviz, ffmpeg, DuckDB
./scripts/install.sh --all    # + Higgsfield and Codex CLIs
./scripts/doctor.sh           # what works, what's missing, and what each gap costs
```

The installer validates the manifest before it registers anything, marks every bundled script
executable (a missing executable bit is the classic silent plugin failure), and never installs the
optional toolchain unless you ask.

Restart the session or `/clear` after installing so the skills load.

**Editing the plugin — read this, it will save you an hour.** The install is a **copy**, not a
symlink (`~/.claude/plugins/cache/design-forge-dev/design-forge/<version>/`), and the update is
**version-gated, not content-gated**. Editing a `SKILL.md` and running update does nothing at all:

```
✔ design-forge is already at the latest version (0.3.0).
```

Your change is real, saved, and simply not installed. The full loop:

```bash
claude plugin validate .                                # catch manifest errors first
# bump "version" in .claude-plugin/plugin.json (and the repo-root marketplace.json entry)
claude plugin marketplace update design-forge-dev       # re-read the marketplace
claude plugin update design-forge@design-forge-dev      # note the @marketplace qualifier
```

Two traps in that block: the unqualified `claude plugin update design-forge` errors with *"Plugin not
found"*, and the version must be bumped in **both** JSON files or they disagree. Then restart the
session.

---

## The skills

### Critique and measurement — the core

| Skill | What it does |
|---|---|
| **`design-audit`** | Computes what a screenshot cannot show: type ladder, size floor, **worst-case accent count across every scroll position**, prose measure, shadows, vertical rhythm, alignment axes, WCAG contrast, target size, and WCAG 1.4.8 typography. Read-only, no dependencies. |
| **`design-loop`** | Builder plus three fresh-context critics (Brief / System / Craft), binary verdicts, no scores, no fixed round count. The exit is winning. |

**Why `design-audit` exists.** Three pages went through **four rounds** of `design-loop` and were
declared finished. The harness was then run against them and found **23 real defects in under two
minutes** — a colour that was simply the wrong hex, seventeen WCAG failures, a type-ladder violation,
and interactive targets under the 24px minimum. Not because the critics were lazy. Because the defects
were **not visible**.

Four things a screenshot structurally cannot do:

1. **Verify an exact value.** Two lavenders forty units apart look identical.
2. **Falsify a per-viewport rule.** A screenshot *is* one viewport, and you chose which one. You have
   to slide a window down the whole document and take the worst case.
3. **Compare two numbers far apart in the page.** A 655px hero column and a 688px story column never
   appear in the same frame.
4. **Compute a ratio.** Nobody eyeballs 4.21 against 4.50.

### Visual production

| Skill | What it does |
|---|---|
| **`art-department`** | The visual-deliverable playbook: which tool for which job, the licence gate, house style, and a **61-asset library where every file's licence is recorded along with where it was verified** — 10,775 icons (MIT/ISC), CC0 textures, OFL fonts, public-domain ornament. |
| **`scroll-film-studio`** | Scroll-scrubbed cinematic sites, one continuous shot driven by scroll position. Pure-code GSAP/Lenis lane (free) or a generated film lane. |

### Copy

| Skill | What it does |
|---|---|
| **`de-sloppifier`** | Three-pass line edit: pacing and paragraph shape, then line editing, then AI-pattern removal (negative parallelism, rule-of-three padding, em-dashes, inflated vocabulary, abstraction without grounding). |
| **`voice`** | Extracts a voice fingerprint from writing samples so generated copy is anchored to a real person's prose instead of the model's defaults. |
| **`clean-export`** | Strips invisible provenance characters (zero-width, bidi, Unicode TAG payloads, exotic spaces) without altering a word. Run before anything leaves the machine. |

---

## Design tokens without the scraping problem

`scripts/tokens.py` ships a registry of **12 first-party token sources (18 URLs, all verified
resolving)** — each system's *own* published token file on npm/unpkg, under its own MIT/Apache-2.0
licence. No gallery, no scraping, no rate limit, no middleman.

```bash
python3 scripts/tokens.py --list
python3 scripts/tokens.py tailwind --category color
python3 scripts/tokens.py carbon --json > carbon.json
python3 scripts/tokens.py --all --check          # re-verify the registry
```

Tailwind v4 · GitHub Primer · Shopify Polaris · IBM Carbon (true W3C DTCG) · Adobe Spectrum ·
Atlassian · Radix · Open Props · shadcn/ui · Mantine · USWDS · Google Fonts metadata (1,942 families,
keyless, with the `stroke` field that makes pairing a query instead of a vibe).

**Why this exists rather than scraping a design-system gallery:** the gallery this workflow used to
depend on disallows `ClaudeBot`, `anthropic-ai` and `Claude-Web` in robots.txt with a blanket
`Disallow: /`. Verified by fetching it. First-party sources sidestep the question entirely and are
better data — Carbon publishes real DTCG, Atlassian pre-resolves every alias to hex.

Gotchas baked into the tool's notes: **Tailwind v4 is not hex-comparable to v3** (v4 widened chroma —
same hue, different gamut), **Carbon tokens are aliases** needing resolution against the palette file,
**shadcn `themes.css` uses bare HSL channels** that a normal colour regex misses, and **Primer splits
radius and spacing into separate files**.

---

## Using the harness directly

No plugin required — it is one read-only file.

```bash
cp scripts/audit/measure.js .            # next to your html
python3 -m http.server 8899              # file:// is blocked for scripted eval
```

Load it, then measure. The `<script src>` tag is async, so **injection and the first call must be
separate round-trips** or `__DF` will be undefined:

```js
// call 1
(()=>{const s=document.createElement('script');s.src='/measure.js';document.head.appendChild(s);return 'ok'})()
// call 2
JSON.stringify(__DF.report({ accent:'#2b7fff', cap:3, floor:16, measure:680 }))
```

```
typeLadder    3/3 PASS [16,20,72]
typeFloor     0 under 16px PASS
accent        worst 3/3 @y=2880, 3 total PASS
shadows_house 0 PASS (house rule, not normative)
proseMeasure  1 measure(s) PASS [668]
contrast      0 WCAG AA failures PASS
wcag148       0 failures PASS
targetSize    0 under 24px PASS
rhythm        5 sections, 0 under 96px PASS
alignment     11 left edges
tokens        radii[8,12] weights[400,500,900]
viewport      [1440,648]
caveat        One page, one state, one width...
```

⚠️ **Always cache-bust after an edit** (`page.html?v=2`). A stale copy reports the pre-fix numbers,
which looks exactly like a fix that did not work.

### What it does not see

`report()` prints this caveat itself: **one page, one state, one width.** No hover or focus states (SC
2.4.7 Focus Visible is Level AA and is unchecked), no dark mode, no error/empty/loading states, no
mobile width, no RTL, no print, no keyboard order, and nothing about the accessibility tree. Two AA
criteria are implemented out of roughly fifty-five. A green report means *conformant on the axes
measured* — not *accessible*, and not *good*.

### It reports honestly, which matters more than it sounds

- **`contrast` returns `indeterminate` separately.** Text over a gradient has no CSS background colour
  to measure against. The harness refuses to invent a ratio and lists those elements for manual
  sampling. **An indeterminate is not a pass.** (An earlier version walked past the gradient and
  reported a button as 1.01:1 against the section behind it.)
- **`accentScan` dedupes by subtree.** `<div>4-12<span>hrs</span></div>` is one accent use, not two.
- **`proseMeasure` reports, it does not judge.** Two measures can be legitimate — a lede column and a
  table cell are different components. Two measures on the *same* component is the defect.

---

## What the evidence changed

[`references/mechanisms.md`](references/mechanisms.md) is a citable rule library. Every entry is
tagged **normative** (read from the standards body), **practitioner** (attributable, real number),
**convention** (universally repeated, no evidence), or **folklore** (primary source does not exist).

A few things worth knowing before you write a bar:

- **WCAG SC 1.4.8** is five binary typographic mechanisms in one normative criterion — line width
  ≤80 characters, not justified, line-height ≥1.5, paragraph spacing ≥1.5× line spacing. Almost
  nobody cites it because it is AAA.
- **Modular scale ratios have no evidence base.** 1.25, 1.333, 1.618 are borrowed from musical
  intervals. The checkable rule is *"every size is a member of one declared scale,"* never *"the
  scale is 1.25."* Import the constraint, not the mysticism.
- **"NN/g says 50–70 characters per line" appears to be folklore.** No such article could be found.
  Use Bringhurst, Butterick, or WCAG 1.4.8 — all real, all citable.
- **Crop and zoom for any rule about small type. Never overlay grid lines** — measured, a patch grid
  helped slightly and grid *lines* collapsed grounding accuracy to near zero.

---

## Hard-won operational notes

Each of these cost real time on the run that produced this plugin.

- **A CSS shorthand beats a longhand it never mentions.** `.wrap{padding:0 40px}` silently zeroes
  `section{padding:120px 0}` because class beats element. This bit **three times, once per page.**
  Write longhand for anything a container might also set.
- **Most defects come from the previous round's fix**, not the original build. Re-run the full audit
  after every change, not just the check you were fixing.
- **Evidence-shaped activity is not evidence.** Scrolling, screenshotting and moving on is not the
  same as confirming the region you care about is in the frame.
- **Verify your bar is satisfiable before building.** One bar demanded display type at ≥12vw *and*
  the supporting layer above the fold: ~800px of content into a 648px viewport. No page could pass
  both rules, so every round fixed one and broke the other.

---

## Layout

```
design-forge/
├── .claude-plugin/plugin.json
├── skills/            7 skills
├── scripts/
│   ├── install.sh     validate → register → install (+ optional toolchain)
│   ├── doctor.sh      dependency report, exits 0 always
│   └── audit/measure.js
└── references/mechanisms.md
```

## Licence and credits

The original work here — skills, scripts, docs, the harness — is **MIT** (`LICENSE`).

The bundled assets under `skills/art-department/library/` are **not**. They stay under their own
licences: MIT (Health Icons, Tabler), ISC (Lucide), OFL-1.1 (16 Google Fonts webfonts), CC0
(ambientCG textures, Cleveland Museum of Art), Public Domain (Art Institute of Chicago). MIT, ISC and
OFL all require their text to travel with the files, so it does — `library/licenses/`, fetched from
upstream rather than recited. Per-file detail including **where each licence was verified** is in
`library/manifest.json`, and `fetch.py` refuses to add a file without one.

Obligations, and the two caveats worth reading before you reuse the museum images or the textures
commercially: **`THIRD-PARTY-NOTICES.md`**.

`design-loop` is adapted from *The Design Loop*, itself a variation on the **Gauntlet Loop originated
by Matt Shumer** — the method is his. `de-sloppifier`, `voice` and `clean-export` come from
**story-forge**.
