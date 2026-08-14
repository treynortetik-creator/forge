---
name: deck-builder
description: "Build PowerPoint decks from shape primitives so they survive a Google Slides import fully editable, with the legibility floor enforced at build time. Use when creating, generating, or writing a .pptx deck or presentation."
---

# Deck Builder

You build decks that survive the trip to Google Slides. That constraint decides the
architecture, so read why before you write any code.

## The constraint

A native PowerPoint chart **flattens into a static image** on Google Slides import, and
there is no workaround inside an uploaded `.pptx`. Slides only keeps a chart live when it
is linked to a Sheet, and that link cannot exist in a file you upload. Google rebuilds the
slide rather than copying it, so anything it cannot represent is approximated or dropped.

So the chart arrives as a dead picture: not editable, not restylable, not selectable as
data. The recipient cannot fix a typo in an axis label.

**The response is not a style guide telling people to avoid charts. Style guides lose.**
`scripts/deck_build.py` has no `add_chart`; every component builds from rectangles, ovals,
text boxes and tables — the primitives that survive editable.

⚠️ **This is a strong default, not a sealed box.** `Slide.s` and `Deck.prs` are public
attributes holding the live python-pptx objects, so `s.s.shapes.add_chart(...)` reaches a
native chart in one hop. An earlier version of this file claimed there was "no way to reach
one" and that compliance was "structural"; that was false. What the round trip actually
guarantees is narrower and still worth having: **the component library never creates a
chart, and `deck-audit` catches one if you reach around it.**

Also affected on import, for the same rebuild reason — and these follow **opposite** rules,
so do not lump them together:

- **Fonts Google lacks** are substituted; metrics shift and layout moves.
- **Transitions:** supported ones carry over; unsupported ones are removed with **no substitute**.
  Morph does not survive.
- **Animations:** unsupported ones **are** substituted, usually with Fade.
- **Embedded video:** unverified. Do not assert it either way without testing.

## Use it

```python
import sys; sys.path.insert(0, "${CLAUDE_PLUGIN_ROOT}/scripts")
from deck_build import Deck, Theme

d = Deck(Theme.load("theme.json"))          # or Theme() for the neutral default
s = d.slide("Headline", "optional subtitle")
s.bars([("Q1", 42), ("Q2", 61), ("Q3", 88)], unit="%")
s.stats([("88%", "of the thing"), ("4.5:1", "minimum contrast")])
s.bullets(["first point", "second point"])
s.callout("A line worth pulling out.", "attribution")
s.table([["Header", "Header"], ["cell", "cell"]])
d.save("out.pptx")
```

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/deck_build.py --print-theme > theme.json
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/deck_build.py --demo demo.pptx
```

## Two properties you should not remove

**Every run gets an explicit size and colour.** Inherited formatting is why
`run.font.size` returns `None` on a normal deck and why a naive checker reports it clean.
Setting both explicitly is what makes the deck measurable by `deck-audit`.

**The legibility floor raises an exception, not a warning.** Ask for 8pt and you get
`DeckError`. This is deliberate: a warning you can scroll past is how 8pt footnotes ship.
The first draft of the bundled theme had 18pt labels and **the builder rejected its own
defaults on the first run**, which is the behaviour working.

If you genuinely need smaller type you are authoring a document to be read up close, not a
slide to be projected. Set `viewing_need` to `analytical` (2%EH) — but only if the screen
really is that large relative to the room, because the tool cannot verify that and you are
asserting it. ⚠️ Note this tier is **not** DISCAS Analytical Decision Making, which is a
*more* demanding category, not a lighter one.

## Branding

The theme is a JSON file the user supplies. Colours (`bg`, `ink`, `muted`, `accent`,
`accent2`, `rule`, `on_accent`), type sizes, family, margins, and `viewing_need`. Never
hard-code a brand into the library. If the user has brand colours, check the pairs clear
4.5:1 before you build — `accent` against `on_accent` is the one that usually fails.

## The honest trade-off — state it to the user once

Shape bars are not data-driven. Changing a value means resizing a rectangle and editing its
label. The library does that for you on a rebuild; Google Slides will not do it on its own.
That is the price of surviving the import editable, and the recipient should know they need
to come back to you rather than typing over a number.

## Always close the loop

Building is half the job. Audit what you built:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/deck_audit.py out.pptx
```

The demo deck is checked into the round trip for this reason — it is built by the library
and passes the harness clean, so a regression in either half shows up immediately. Do not
hand a deck to the user without running the audit and reporting what it said.
