---
name: house-style
description: >
  The house rules for explainer videos: how scripts are worded, how the voice sounds and how fast it goes, what the
  picture must and must not look like, what goes on screen, length, facts and privacy, and how a cut is approved and
  delivered. Built from owner notes on real cuts, each rule with a one-line why, plus a list of rules that no longer
  apply. Use before writing a script, briefing a builder, judging a cut, or when someone asks "what are our rules",
  "house style", "why did we do it that way", "is this on-style", or "does the owner like X". Also loads a private
  overlay when one is configured (brand, names list, pronunciations, extra rules).
---

# House style

Read these, in this order, before you brief or write anything:

1. `${CLAUDE_PLUGIN_ROOT}/skills/house-style/rules.md`: every in-force rule with its reason, and what was superseded.
2. `${CLAUDE_PLUGIN_ROOT}/styles/clay-factory/STYLE.md`: the look in numbers (hex, fonts, sizes, captions, motion).
3. The profile for this kind of video in `${CLAUDE_PLUGIN_ROOT}/profiles/` (`concept-video`, `compliance-connector`,
   `product-demo`, `story-film`, `deck-voiceover`).
4. The private overlay, if there is one (below). Overlay rules win over plugin rules; the newest approved cut wins
   over both.

## The private overlay

A folder outside this repo that holds what must not be public: brand, logo files, a names list, pronunciations, extra
rules, extra profiles. The plugin works without it. It is found in this order:

1. `EXPLAINER_FORGE_OVERLAY=<folder>`
2. `~/.config/explainer-forge/overlay` (usually a symlink to the folder)

| File in the overlay | Used for |
|---|---|
| `house.md` | read it first; private rules and brand |
| `names.txt` | people who must not appear; merged into a project's `names.txt` |
| `allow.txt` | capitalised pairs that are fine; merged into `allow.txt` |
| `say-map.json` | pronunciations; merged into a project's `saymap.json` |
| `public-terms.txt` | words that must never reach a public repo, one per line |
| `profiles/*.md` | extra profiles, or replacements with the same file name |
| `brand/`, `sprites/` | logos and trademark art |
| `lessons.md` | lessons that are too private to go in this plugin |

`scripts/new_project.py` reads it on its own. To check what it would use:
`python3 ${CLAUDE_PLUGIN_ROOT}/scripts/new_project.py --show-overlay`.

## Writing a brief for another agent

Paste in, every time: the profile numbers, the superseded list's top five lines, the known traps from the last cut's
retro, and the folder of the last approved build. A brief built from a written recipe alone repeats old mistakes.

## Judging a cut

Walk `rules.md` section by section against the cut and report: rule number, time code, what is wrong, the smallest
fix. Rules marked *(generalised)* are weaker than the others: raise them as questions, not defects. Anything the owner
has already ruled on stays ruled (D6).

## Changing a rule

New rules come from the owner's words on a cut. Use `lessons-loop`: it checks for a conflict first, then moves the old
rule to Superseded in the same edit. Never keep two rules that disagree.
