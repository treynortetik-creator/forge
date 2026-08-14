---
name: deck-audit
description: "Measure a .pptx deck instead of eyeballing it: type legibility at viewing distance, WCAG contrast with z-order backdrop resolution, native charts that will flatten on Google Slides import, and off-slide geometry. Use when reviewing, checking, or QA-ing a PowerPoint or Google Slides deck."
---

# Deck Audit

You measure decks. You do not have opinions about them.

A person looking at a slide cannot tell whether 18pt text will be legible from the back
row, whether a colour pair clears 4.5:1, or whether a chart is about to flatten into a
dead image on import. All three are arithmetic. Run the arithmetic; report what it says;
say plainly what it does not cover.

## Run it

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/deck_audit.py deck.pptx
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/deck_audit.py deck.pptx --room-depth 40
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/deck_audit.py deck.pptx --viewing-need analytical
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/deck_audit.py deck.pptx --json
```

Needs `python-pptx` (`pip3 install python-pptx`). Exit 1 on a hard failure.

## What it checks, and what each one means

| Check | Fails when | Why it is not a matter of taste |
|---|---|---|
| `nativeCharts` | a real PowerPoint chart exists | it becomes a **static image** on Google Slides import, permanently |
| `legibility` | a run is below the computed floor | derived from angular subtense, not from folklore |
| `contrast` | below 4.5:1, or 3:1 for large text | WCAG 1.4.3, computed against the **actual** backdrop |

**Large text in a deck is 18pt, or 14pt bold.** The familiar 24px / 18.66px figures are
those same sizes in CSS pixels at 96dpi. A `.pptx` is measured in points, so applying the
pixel numbers to points is a 1.333x error that holds everything between 18pt and 24pt to
4.5:1 when the spec asks 3:1. This harness shipped with exactly that bug, copied from its
browser sibling where the pixel figures are correct.
| `offSlide` | geometry crosses the slide edge | includes shapes nested in groups, in slide coordinates |
| `emptyPlaceholder` | a placeholder was left blank | ships as "Click to add text" |
| `unresolvedSize` | no size anywhere in the chain | reported separately; never silently assumed |
| `unmeasured` | contrast could not be computed | **not a pass** — say so rather than guessing |

## The three traps it is built around

**1. `run.font.size` returns `None` for inherited sizes.** This is the normal case for
placeholder text. A naive reader sees `None`, skips the run, and reports a clean deck. The
script walks the real chain — run → paragraph → shape `lstStyle` → layout placeholder →
master placeholder → master `txStyles` → 18pt default — and tells you which link supplied
the answer. Text colour resolves through the same chain.

**2. Points are not a physical size.** A point is a document unit; its height on the wall
depends entirely on how large the slide is projected. Treating points as inches gives a
~185pt floor for a 30ft room, off by an order of magnitude. The real chain:

```
fraction_of_image = (pt / 72) * 0.70 / slide_height_in     # 0.70 = cap height
physical_cap_in   = fraction_of_image * screen_height_in
require             physical_cap_in >= viewing_distance_in / 200
```

Derive screen height from the AV **4/6/8 rule** (farthest viewer at most 4x, 6x or 8x the
screen height away, for analytical / basic / passive viewing) and **the viewing distance
cancels** — screen size scales with room depth. The floor becomes a property of the viewing
need and the slide's aspect, not the room. On a 7.5in-tall slide it lands at **23.1pt for
basic viewing**, which is where the folk "minimum 24pt" rule came from.

Pass `--screen-height` (inches) with `--room-depth` to measure a real room instead.

**3. A shape with no fill is not necessarily on the slide background.** Text laid over a
coloured panel is one of the most common ways a real deck is built. Resolving the backdrop
by z-order — walk down from the text and take the first filled shape that contains it — is
what stops the tool reporting white-on-white at 1.0:1 for perfectly legible text. A false
positive is worse than no check, because it teaches people to ignore the output.

## Reporting

Lead with the counts, then the individual findings. For every finding give the slide, the
measured number, the threshold, and for type sizes **where the size came from** — "18pt
from master txStyles/body" is actionable in a way that "18pt" is not.

Always carry the caveat through to the user: this is static file analysis. It says nothing
about whether the deck is any good, whether the story works, or how it reads projected in a
lit room. Name the axes it covers and stop there.

Never report a pass on zero measurements. If `checked runs` is 0 the deck is image-only or
the reader failed, and either way that is a failure, not a clean bill of health.

## Fixing what it finds

For native charts, rebuild the visual from shapes — see the `deck-builder` skill, whose
component library cannot express a native chart. For type below the floor, raise the size or
cut the words; shrinking to fit is how the problem got there. For contrast, change the
colour pair, not the opacity.

## Tests

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/test_deck_audit.py
```

27 cases. Every one is a bug that was live in this harness and shipped green — including a
version that reported "0 runs, all PASS, exit 0" on a deck built entirely from grouped
shapes and tables, which is exactly the construction this plugin tells you to use.
