---
name: design-loop
description: Takes a goal and a real-world reference, extracts what actually makes the reference good, then runs builder and three fresh-context critics on every piece until all three agree ours wins. Triggers on "/design-loop", "design loop", "run the critic loop", "loop this against".
---

# Design Loop

> **Provenance.** Adapted 2026-08-11 from "The Design Loop: Free Guide" (Notion), which is itself a variation on the **Gauntlet Loop invented by Matt Shumer**. Credit is his. Two deliberate changes for this machine are marked 🔶 below; everything else is faithful to the source.

**The whole idea in one line:** a critic that shares memory with the builder is grading its own homework. Everything else here is detail.

The context that builds a piece is the context that grades it, which is a chef reviewing their own restaurant. Five stars, every time. This moves the judging into fresh contexts that never saw the work being made. Parallel agents buy speed; fresh context buys the result.

Four phases: interview, preflight, teardown, loop. **Do not skip ahead. Do not start building during phases 1 to 3.**

---

## Phase 1: Interview

Ask exactly these three, together, then stop and wait.

1. What are you building, and how long or how big?
2. Name something that already does this brilliantly. A site, a video, a doc, anything I can open. If nothing comes to mind, say skip.
3. Any files I should work from? Design system, brand doc, script, existing draft.

If they name something vague ("Apple's website", "good SaaS design"), **push once** for the specific page or file. A vague bar is the number one reason this method fails: the critic invents a comparison and approves everything on round one.

If they say skip on question 2, propose three candidate bars, one line each on why, and wait. If they do not answer, take the hardest one.

## Phase 2: Preflight

A check, not a question. Run it before any work and report in one block.

- **Fetch the bar now.** Screenshot the URL or read the file. If it is blocked or missing, say so and ask for another.
- **Confirm you can render our output:** screenshots for a site, a filmstrip of frames for animation, a PDF render for a doc. No render means no craft critic.
- **Name any generation tools the goal needs** (image, video, voice) and confirm they are connected.
- **Confirm the input files exist:** design-system.md, brand doc, script.

Then print: what is working, what is missing, and **which critic goes blind** if something is missing. Never carry on quietly with a critic that cannot see.

## Phase 3: Teardown

Read the reference properly and write **5 to 7 mechanisms** to `bar.md`.

**Mechanisms, not adjectives.** This is the step that does the real work and the step people get wrong. Adjectives are unfalsifiable; measurements are not.

❌ Useless: feels premium · clean and modern · good use of whitespace · strong visual hierarchy

✅ Checkable:
- headline is 5x body size, three type sizes total
- one accent colour, used at most twice per screen
- motion always resolves in one direction
- nothing animates for under 400ms
- whitespace above the fold is at least 40% of the frame

Every line must be something a critic can check. Show `bar.md` to the user before continuing.

### Phase 3.5: Coherence check — do the arithmetic on your own bar

**Added 2026-08-13 after a bar shipped that no page could satisfy.** A mechanism must be checkable
**and achievable alongside every other mechanism.** Before building, add up what your own rules demand:

> A bar required display type at **≥12vw** *and* the supporting layer above the fold. Three lines at
> 12vw is ~520px, plus nav, subtext and two CTAs ≈ **800px against a 648px viewport.** Two mechanisms
> contradicted each other. Every round, the loop fixed one and broke the other.

Run this before a single line is built:

1. **Sum the vertical demands** of every above-the-fold rule against a real viewport height (648px is
   a laptop with browser chrome, not 1080).
2. **Count the tiers your rules imply.** If the type ladder is capped at 3 and the layout needs a
   nav, an eyebrow, a headline, body, buttons and a stat rail, you have already spent 6.
3. **Check that no rule is a proxy.** `12vw` was copied from the reference's *rendered size* without
   checking it against the content beside it. The rule that replaced it measured the actual intent:
   glyph aspect ratio ≤0.80.

If two mechanisms collide, **amend the bar and say so in writing.** A bar you refuse to change turns
the loop into a treadmill; a bar you change silently is not a bar.

## Phase 4: Loop

Split the goal into the smallest pieces that can be improved and judged on their own. You choose the pieces. **Keep it to three or four unless told otherwise, because every extra piece multiplies the run.**

### 🔴 Measure first, then judge

**Run `design-audit` on the rendered page BEFORE any critic sees it, and hand the critics the numbers
as text.** This is the single highest-leverage rule in this file.

Vision models cannot count or measure from an image, and this is measured, not suspected: four
frontier models average **58.57%** on trivial geometric tasks and **56.84% on counting**. Meanwhile,
open-ended AI design audit runs an **80.1% false-positive rate**, of which 8.9% is actively harmful
advice (Baymard, 257 ground-truth issues, ~50 hours of expert comparison).

So: *"one accent, at most 3 per viewport"* and *"headline ≥3.5× body"* are **correct rules asked the
wrong way.** They require counting and ratio arithmetic from pixels, the two operations with the
best-documented failure rates. The harness settles them in milliseconds and cannot hallucinate.

**Division of labour:** arithmetic to the harness, taste to the critic. A critic asked to verify a
hex is being set up to fail; a critic asked whether the page is any good is doing what it is for.

For each piece: fan out a builder, then three critics, **each with fresh context and no knowledge of how the builder worked.**

- **Brief critic** judges against the stated goal only. Does it do the thing? Ignore aesthetics.
- **System critic** judges against `design-system.md` only. Objective adherence.
- **Craft critic** judges against `bar.md` and rendered output only. Put ours next to the reference blind with labels stripped, say which is better, name the single biggest gap.

**Write each critic's brief yourself, adapted to this specific goal.** Do not reuse generic wording across different goals.

Rules:
- Critics are harsh. Praise is not useful.
- Critics judge **rendered output, never the code.** Reading the implementation makes a critic evaluate intent instead of result.
- **Binary verdicts, not scores.** Scores drift upward every round.
- **All three must pass.** Any fail goes back to the builder with the single biggest gap named.
- **No fixed round count.** The exit is winning, or the user stopping the run.
- 🔴 **One mechanism, one call.** A batched checklist in a single context quietly reintroduces the
  holistic judgment you were trying to avoid. Per-item binary questions lift exact agreement with
  human preference (46.4% → 52.2%) and cut variance. Randomise the order — position bias is worth
  10-15 points of swing.
- 🔴 **The builder's model must not be the critic's model** where you can avoid it. Self-enhancement
  bias runs 10-25%. Fresh context is the floor, a different model is the goal.
- 🔴 **Crop and zoom. Never overlay grid lines.** For any rule about text or a small component, give
  the critic a zoomed crop, not the full page. Measured: a zoomed crop took grounding IoU from 0.120
  to 0.357; a *patch grid* helped slightly (0.222); **grid lines collapsed it to 1.1e-5.** Separately,
  multimodal OCR degrades below 150 ppi, which is exactly what a downsampled full-page screenshot
  does to 16px body text.
- 🔴 **Evidence coverage gate.** Before a critic reports on a region, it must confirm that region is
  *in the frame*. Earned the hard way: a critic correctly refused to clear a page whose statistics
  band had never been screenshotted; the band was then found carrying two defects live since round 1.
  **Evidence-shaped activity is not evidence.**
- 🔴 **Regression pass after every fix.** Re-run the FULL audit, not the check you were fixing. On the
  run that produced these rules, **most defects were introduced by the previous round's fix** — a
  padding shorthand silently cancelled section rhythm on three separate pages, and a proof rail added
  to close a grid gap broke the type ladder it was added to repair.
- **For iteration N vs N-1, ask which is closer to the reference.** Pairwise comparison is the
  reliable primitive (79.3% human agreement); scoring is not, which is why scores are banned.
- **A critic's number is a claim, not a fact.** One craft critic failed a page for "headline strokes
  6× heavier than body" — it had compared a 96px headline to 16px body, and stroke width scales with
  size. Rejecting a finding on method is legitimate; do it in writing, at the time.

Keep a live progress page updating as work evolves: piece status, each critic's verdict, gap history, round count.

---

## The three critics

You never write a critic from scratch. The three roles are fixed so they never converge into the same opinion, but each one's specific brief is written per run, because "does it hit the brief" means something different for an animation than for a pricing page.

| Critic | Judges against | Model | Why |
|---|---|---|---|
| **Brief** | The stated goal only, ignoring aesthetics | Sonnet | Simple judgment, no vision needed |
| **System** | `design-system.md` only | 🔶 **Sonnet** (source says Haiku) | Mechanical adherence checking |
| **Craft** | `bar.md` + rendered frames, never the code | **Strongest available** (Opus, or Fable for a hero asset) | Never downgrade this one. A cheap craft critic approves everything and the loop dies on round one. |

🔶 **Deviation 1, and it is deliberate.** The source assigns the System critic to Haiku. **Set a hard floor at your second-strongest model instead.** A pinned cheap model ages badly, and a mechanical adherence check that quietly misses violations is the invisible kind of failure. The cost delta is not real money here (see below), and a mechanical adherence check that quietly misses violations is exactly the invisible failure the floor exists to prevent. **Use Sonnet.**

---

## 🔶 Cost, honestly (Deviation 2: rewritten for this machine)

The source is right that a cost line inside a prompt is a wish, not a brake, because the model cannot reliably see its own spend. **Do not print a fabricated dollar figure. Show round count and pieces elapsed instead.**

The source's own reported extreme: a 19-hour F1 game build ran **1.7B tokens, 137 agents, ~$1,200 API**. That is the far end, not a landing page. But it is the honest shape of the trade: **this is powerful because it is expensive.**

**What is different here:** many users run a flat-rate plan, not metered API. So the brake is **not dollars, it is the weekly limit and session capacity.** Controls, in the order that actually works:

1. **Watch it and stop it. You are the brake.** Say this out loud at kickoff.
2. **Cap the pieces to three or four, not the rounds.** Every extra piece multiplies the run.
3. Let the weekly limit be the hard stop.

🔴 **Reserve this for a hero asset.** Every round is a build plus three judgments. Use it on the flagship page, the board-readout deck, the event invite. **Not on routine deliverables** and never on something a plain templated converter already handles well. This is the class of thing to dry-run and confirm before launching, not to fire off casually.

---

## What breaks this

- **A vague bar.** By far the most common failure.
- **The builder judging its own work.** Critics need fresh context.
- **A soft critic.** Binary job, not a score.
- **A fixed round count.** The exit is winning.
- **Over-specifying.** Every extra instruction is one fewer decision the model makes with its own judgment.
- **A bar with no contrast rule.** Checking colour *identity* (is it the right hex) while never
  checking colour *legibility* passes a page with seventeen WCAG failures. Ship the accessibility
  block from `references/mechanisms.md` in every bar; it is normative, numeric and free.
- **No false-positive budget.** Keep a few fixed pages with known verdicts, **including deliberately
  clean ones**, and check what your critics say about them. A clean page that produces zero findings
  is the test that matters. The exposure is not missed defects, it is confident invented ones.

---

## Local wiring (this machine)

- **Rendering for the craft critic:** `claude-in-chrome` screenshots for HTML/sites. For a doc, render via any markdown-to-HTML converter, then screenshot. For 3D or diagram assets, the Blender / Inkscape / Graphviz toolchain in `art-department`.
- **Fetching the bar:** if the reference is a JS app (Notion, Figma, most SPAs), **WebFetch returns the shell and tells you nothing.** Navigate `claude-in-chrome` to it and read `document.body.innerText`, freezing it to a `window.__X` global first so slices stay consistent while the page lazy-renders. `javascript_tool` output caps around 1,000 characters, so slice at ~880.
- **Design system:** if the project has no `design-system.md`, pull a real one with `scripts/tokens.py` (12 first-party sources) or use your house brand kit. **Say which one you used rather than inventing a system**, because an invented system makes the System critic unfalsifiable.
- **Critic isolation:** spawn each critic with the `Agent` tool as a separate subagent. Give it the rendered artifact and the relevant judging file **only**. Never pass it the build transcript, the builder's reasoning, or the other critics' verdicts.
- **Never give a critic a memory-search tool.** It is irrelevant to judging a rendered artifact, and it invites the critic to grade intent instead of result.

## Related

- **`design-audit`**: the measurement layer this loop should always run first
- **`references/mechanisms.md`**: citable numeric rules (WCAG, Bringhurst, Butterick) with each
  source marked normative / practitioner / convention / folklore, so a bar is defensible
- `skills/art-department/`: rendering and asset generation
