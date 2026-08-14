# House style — the wow-factor file

What separates a deliverable that looks *made* from one that looks *emitted*. Assembled from the
Anthropic html-effectiveness reference set, a working house brand kit, and every design correction
earned on real deliverables since 2026-05-30.

---

## 🔴 The three looks AI design keeps landing on — verbatim from Anthropic's `frontend-design` skill

> *"AI-generated design right now clusters around three looks: (1) a warm cream background (near
> #F4F1EA) with a high-contrast serif display and a terracotta accent; (2) a near-black background
> with a single bright acid-green or vermilion accent; (3) a broadsheet-style layout with hairline
> rules, zero border-radius, and dense newspaper-like columns."*

> *"All three are legitimate for some briefs, but they are **defaults rather than choices**, and they
> appear regardless of subject… Where it leaves an axis free, don't spend that freedom on one of these
> defaults."*

**If the brief explicitly asks for one of them, give them that** — the brief's own words always win.
Otherwise, landing on one is a tell.

## The anti-convergence ledger — differ on at least four

Adapted from a catalogue of web-effect patterns. Before building, name what the **previous**
deliverable used on each axis, then differ on **at least four**:

1. **Palette family** — hard ban on a repeat
2. **Type pairing** — no repeating the same display face twice running
3. **Hero architecture** — image-as-canvas / split / masked / rail / instrument / schematic
4. **Signature element** — the one thing the page is remembered by
5. **Corner and border language** — sharp / soft / pill / hairline-ruled / dashed
6. **Motion or its deliberate absence**

**First build with nothing to differ from?** Then the enemy is your own statistical default. Derive all
six from the subject's material world — *the nouns the thing actually touches* — and say so. If a
choice would look at home in a generic template, re-roll it.

## The two-pass process — plan, critique the plan, then build

Also from `frontend-design`, and it is the discipline that makes the difference:

**Pass 1 — a compact token system**, written out before any code:
- **Color:** 4-6 named hex values
- **Type:** faces for 2+ roles — a characterful display used with restraint, a body face, a utility
  face for captions and data
- **Layout:** one-sentence prose plus an ASCII wireframe
- **Signature:** the single element this page will be remembered by

**Pass 2 — critique the plan against the brief before writing code.** Ask: *would I have produced
this for any similar prompt?* If yes for any part, revise that part and say what changed and why.
Only then build, deriving every color and type decision from the revised plan.

**Spend your boldness in one place.** Let the signature be the one memorable thing and keep everything
around it quiet. Then Chanel's rule: before leaving the house, look in the mirror and **remove one
accessory.**

**Not taking a risk is itself a risk.** Take one real aesthetic risk you can justify.

## Structure must encode something true

Numbered markers (01 / 02 / 03), eyebrows, dividers and labels should carry information, not decorate.
**Only number things that are actually a sequence.** A numbered list of three unrelated principles is
decoration pretending to be structure.

---

## Visual slop — the seven tells

Same idea as the prose desloppifier, aimed at pixels. Each one is the statistically obvious choice.

| Tell | The fix |
|---|---|
| **Purple-to-blue gradient on everything** | One flat accent. Gradients only inside the brand scale, and only when they describe something (a range, a fade) |
| **Every category a different color** | **One accent, plus at most two semantic colors** (good/bad), each meaning exactly one thing everywhere. Recolor only the bar that matters; mute the rest |
| **Drop shadows and glows for separation** | **1.5px hairline borders + border-radius.** Shadows are near-useless on dark and read as 2014 |
| **Emoji as iconography** | Real icons from Iconify. Emoji are fine as a marker in text, never as the icon system |
| **Mermaid diagrams** | Hand-authored inline SVG under 12 nodes; Graphviz above it. Mermaid on branded work reads "Windows 95" and drags a ~250KB CDN behind it |
| **CSS-approximated texture and depth** | A real Poly Haven texture at low opacity, or a real Blender render. Free, one call, and the eye can tell |
| **Perfectly even rhythm** — every card the same size, every section the same length | Vary it. One oversized number, one full-bleed image, one short section. Visual burstiness is the same virtue as sentence burstiness |
| **The blueprint/telemetry look** — drafting grid, mono type, cyan hairlines, corner ticks | Logged 2026-08-07, on exactly that: *"D looks too vibe coded."* It is the house style of every AI coding demo, which makes it read as machine-made no matter how well executed. Fine when the subject genuinely IS a schematic; never as a general dark treatment |
| **Photos cropped by `center/cover` without checking** | Look up the subject position first, and keep a per-image crop map so you never guess twice. Faces cut at the chin is the single most damaging defect available, and it is invisible in the source |

---

## The type system that does the most work

**Three fonts, and the family itself encodes register:**

- `--mono` (SF Mono / Menlo) → labels, IDs, pills, metadata, code. **Reads as machine/data.**
- `--serif` (Georgia) → headings and big numbers. **Reads as human/editorial.**
- `--sans` (system-ui) → body prose.

Headings at **weight 500, not bold 700**, with slight negative letter-spacing. Bold-700 headings are
the single fastest way to look like a default template.

**On house-branded work, fix the stack and do not improvise.** A worked example: Poppins (display,
800), Open Sans (body), Roboto (UI labels and footnotes). Substitute your own, but write it down.

### The font-delivery question, answered

A templated converter can load Poppins and Open Sans via a Google Fonts `<link>` **with system
fallbacks** — the docstring's own words: *"renders fine offline, brand-perfect online."* So the
"no external CDNs" rule was never about fonts.

**The rule that actually applies:**
- **A font `<link>` with a real fallback stack is fine.** Worst case it degrades.
- **A CDN that carries behavior or layout is not.** A JS chart library or a CSS framework from a CDN
  breaks the self-contained promise, and the file arrives broken rather than degraded.
- **When it must be pixel-perfect offline** — an email attachment, a file going into Drive, anything a
  customer opens — **base64 the WOFF2 into the CSS.** One extra step, zero network dependency.

---

## Palettes

**Your house palette — the shape that works,** using a teal system as the worked example. One deep
shade for headlines and text (never pure black), one mid, one bright for accent/CTA, a tint ramp of
four, and **one warm accent used at most once per page. Never body text, never structural, never in
diagram edges.** Derive extra chart shades from inside the ramp, not from outside it. Pull real token
values with `scripts/tokens.py` rather than inventing them.

🔴 **CORRECTED 2026-08-07. An earlier version of this file told you to default unbranded work to
the warm-ivory register (`#FAF9F5` bg, `#141413` text, `#D97757` clay accent). That is wrong, and
Anthropic's own `frontend-design` skill says why: it is AI-default look #1.** See the next section.
The ivory palette is a fine *choice* for an editorial brief that calls for it. It is not a default.

**Unbranded work has no default.** Pick a direction from the brief's own subject
matter. Four worked dark directions live in the reference renders you keep — instrument, archival plate, lecture
board, blueprint — with the generator in `your own build script`.

**Dark mode for free.** Define raw brand tokens once in `:root`, then a **semantic layer**
(`--fg / --muted / --line / --panel`) that every component consumes. Dark mode then overrides four
tokens: `--fg:#F0EEE6; --muted:#9C9A93; --line:#3D3D3A; --panel:#1F1E1B` on `#141413`. Panel sits a
hair lighter than background so cards lift **without shadows**. Token-first construction is the whole
reason a one-line swap converts light to dark.

**Open Props** (500+ MIT design tokens, inlineable, no build step) is the fastest way to stop
hand-picking spacing and radius values that end up all slightly wrong. Remap its colour layer to your
own scale and keep its spacing, easing, and shadow ramps.

---

## Charts and diagrams, zero dependencies

Hand-author the SVG. It is not hard and it is the technique that makes a report look built:

- `viewBox`, never fixed pixels — it scales into a deck, an email, a phone
- Faint gridlines as `<line>`, bars as `<rect rx="6">`
- **Only the single most important bar takes the accent.** Everything else muted
- Document the geometry in an HTML comment so the next pass can recompute it
- Diagram edges carry meaning: **solid muted = sync, dashed accent = async or failure.** Two arrow
  colors maximum, via `<defs>` markers. Coral never appears in an edge
- Edge labels in the UI font at 11px muted; hand-place every coordinate and check nothing overlaps

🔴 **The `viewBox` trap, hit on 2026-08-06:** content laid out beyond the declared viewBox is silently
clipped. A target pill and an entire year-totals row rendered off the edge of a finished slide. **The
source looked correct.** Only the screenshot showed it. This is why the render-and-look gate exists.

---

## Motion

**Dignified only:** opacity plus ≤16px translateY, 180-500ms ease. **No scale, no bounce, no
parallax.** Every animation guarded by `prefers-reduced-motion`.

**Content must stay visible if JS fails.** Gate the hidden state behind a JS-added class (`.armed`),
never hide by default — otherwise a blocked script ships a blank page.

---

## Structure — lead with the answer

Inverted pyramid, every time:

1. **TL;DR** — the finding in one or two sentences
2. **A 4-up stat band** of big numbers, serif, oversized
3. **Highlights** — each bullet opens with a bold one-line takeaway, detail after
4. Supporting detail
5. **Loose ends** — open questions with owners, and "what I deliberately did NOT do"

**Surface what is undecided.** A deliverable that names its own gaps is trusted; one that implies
completeness it does not have gets caught once and distrusted forever.

**Machine-authorship marker:** an "auto-generated" pill plus a footer citing sources and the
generation timestamp. Honest about origin, auditable to its inputs. Ground every claim in a real
specific — `file:line`, a hard number, a named source. **Never fake completeness.**

---

## When NOT to build HTML

**Match the format to the information's shape.** HTML earns its keep through engagement, not
decoration.

- **Yes:** diffs, tables, timelines, charts, comparisons, call graphs, anything with 2D structure.
  *"Diffs and call-graphs are spatial information; markdown flattens them."*
- **No:** plain prose. HTML for its own sake is flair.
- **Best return:** recurring documents — status updates, post-mortems, review decks. The format
  investment compounds every time the doc repeats.

A standing preference worth adopting: **read-while-acting deliverables** (cue cards, briefs, SOPs,
presentation notes) are **terse bullets, not full sentences.** He is holding the thing while doing
something else.

---

## Process traps that have actually cost time

1. **WebFetch drops `<style>` blocks.** Crawling a page to study its design returns markdown with the
   entire CSS gone, and the model then hallucinates "no CSS, standard blue." **Read the raw HTML
   source.** Same failure class as WebFetch returning the SPA shell for YouTube.
2. **f-string braces in generated CSS.** A single `{` where `{{` was needed makes the patch silently
   not apply. The script exits 0. Only the render shows it.
3. **`magick -trim` per frame on an animation** makes the subject wobble, because the bounding box
   moves. Compute the **union** bbox across sampled frames, then apply that one crop to all of them.
4. **Boolean ops in Inkscape silently drop `fill`** — result paths render SVG-default black. Reapply
   fills by id after the chain, and patch the XML with `ElementTree`, never a regex.
5. **`soffice --convert-to` exits 0 on failure.** Always `ls` the output file.

---

## The volume rule

Anti-Slop Rule 3, and it transfers straight from prose to design: **AI for volume, human for
judgment.** Generate 6 variations of a hero image, 4 layouts, 3 palettes at a few cents each — then
put the best two in front of the person deciding. Do not iterate toward one "correct" answer alone. Comedians
write 100 jokes to keep 10.

---

## Using the ornament library — two rules learned by rendering it

Both of these came out of building a local-assets proof page and looking at the screenshot.

**1. Museum scans are artwork, not seamless tiles.** They have edges, margins, and backdrops. CSS
`repeat` on one produces visible seams and reads as a mistake. Use them **contained** (`center/cover`
in a bordered box), full-bleed behind a scrim, or masked. For an actual repeating pattern, use a
CC0 *material* from `library/textures/` or your brand's own pattern assets.

**2. Public domain does not mean on-brand.** A brown 1937 wallpaper dropped into a teal-branded page
fought the palette and looked like a mistake, even though the artwork is good. On branded work the
decorative band should be **your brand's own pattern**; save the museum material for neutral or
editorial contexts, or pick a scan whose palette already sits inside your ramp.

**The general form of both:** an asset being free, legal, and beautiful does not make it *correct
here*. Render it in place and look before you commit to it.

## Worked example

Build one page entirely from local assets and keep it as your reference: display weight base64'd from
`library/fonts/`, your own logo and any cleared photography, a CC0 grain from `library/textures/`, a
brand pattern band, and icons pulled through `icon.py`. **Zero network calls.** The exercise is the
point — it proves the library covers a real deliverable end to end, and it gives you a starting file
that is already correct instead of a blank page.
