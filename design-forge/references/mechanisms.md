# The mechanism library

Citable, numeric, binary design rules. Drop these into a `bar.md` instead of inventing thresholds.

**How to read this file.** Every row is marked with how the number was verified:

- ✅ **Normative** — read directly from the standards body. Quote it freely.
- 📗 **Named practitioner** — a real, attributable source with a real number. Cite the person.
- ⚠️ **Convention** — universally repeated, no primary evidence. Use it, but do not claim it is research.
- ❌ **Folklore** — repeated everywhere, primary source does not exist. Do not cite.

The distinction matters because a bar is supposed to be defensible. "WCAG 1.4.3 requires 4.5:1" ends
an argument. "Studies show users prefer 60 characters per line" invites one you will lose.

---

## Accessibility — the only large body of normative, numeric, binary visual rules that exists

Free, official, stable, and reference-independent, which is exactly what a bar induced from a single
design system is not. **Ship the contrast rule in every bar.** It is the most common real defect on
the web and it costs nothing to check.

| Mechanism | Threshold | SC / Level | | Harness |
|---|---|---|---|---|
| Text contrast | **4.5:1** normal, **3:1** large. Exact, not rounded — 4.499:1 fails | 1.4.3 / AA | ✅ | `contrast()` |
| "Large text" | **≥18pt or ≥14pt bold**; spec sets 1pt = 1.333px, so **≈24px, or ≈18.66px bold** | 1.4.3 | ✅ | `contrast()` |
| Enhanced contrast | **7:1** normal, **4.5:1** large | 1.4.6 / AAA | ✅ | `contrast('AAA')` |
| Non-text contrast | **3:1** for UI component boundaries, state and focus indicators, meaningful graphics | 1.4.11 / AA | ✅ | — |
| Target size | **24 × 24 CSS px**, or spacing so a 24px circle on the target hits no other target's circle | 2.5.8 / AA | ✅ | `targetSize()` |
| Target size enhanced | **44 × 44 CSS px** | 2.5.5 / AAA | ✅ | `targetSize(44)` |
| Line width | **≤80 characters** (40 CJK) | 1.4.8 / AAA | ✅ | `visualPresentation()` |
| Not justified | Text must not be aligned to both margins | 1.4.8 / AAA | ✅ | `visualPresentation()` |
| Line spacing | **≥1.5** within paragraphs | 1.4.8 / AAA | ✅ | `visualPresentation()` |
| Paragraph spacing | **≥1.5× the line spacing** | 1.4.8 / AAA | ✅ | `visualPresentation()` |
| Text spacing tolerance | Must survive line-height **1.5×**, paragraph **2×**, letter-spacing **0.12×**, word-spacing **0.16×** | 1.4.12 / AA | ✅ | manual |
| Reflow | No two-dimensional scrolling at **320 × 256 CSS px** (= 1280px at 400% zoom) | 1.4.10 / AA | ✅ | manual, resize |
| Resize text | **200%** without loss of content or function | 1.4.4 / AA | ✅ | manual |
| Focus indicator | Area ≥ a **2 CSS px** perimeter, **3:1** between focused and unfocused states of the same pixels | 2.4.13 / AAA | ✅ | manual |

> **SC 1.4.8 is the single most underused item here** — five binary typographic mechanisms in one
> normative criterion. It is ignored because it is AAA, not because it is wrong.

**Stricter non-W3C tiers**, useful when you want a second gate:
- 📗 Lighthouse tap targets: fails under **48 × 48 px**, or when ≥25% of the target area within 48px
  of its centre overlaps another target. Recommends **8px** minimum separation.
- 📗 **APCA** (candidate for WCAG 3, explicitly **not normative in any published standard**):
  Lc **90** body text · Lc **75** body columns · Lc **60** non-body · Lc **45** headlines ·
  Lc **30** absolute floor · Lc **15** non-text ≥5px.

**Calibration:** WebAIM Million 2026 found low-contrast text on **83.9% of home pages**, averaging 34
instances per page. If your page has zero, you are already in the top sixth of the web. ⚠️ (WebAIM is
high-trust; this figure was not read at the primary source.)

**How much a checker actually catches — with a real primary source.** 📗 The **UK Government Digital
Service accessibility tool audit** seeded a page with **142 known barriers** and ran 13 checkers:
**SortSite 40% · WAVE 30% · axe 29%**. (2018, and overdue for replication — treat the figure as dated,
not as folklore. It measures *criteria coverage*; vendor claims nearer 57% measure *issue volume*, a
different denominator. Both can be honest.)
<https://alphagov.github.io/accessibility-tool-audit/>

**The reason a harness is worth building at all, quantified.** ⚠️ A 2026 survey of 1,000 US workers
found **46% say fixing AI output takes as long as doing the work manually** and 11% say longer —
**57% report the time saving vanishes once corrections are needed.** METR's RCT is the sharpest version:
experienced developers ran **19% slower while believing they were 20% faster.**

> **The reconciling story, and it is this repository's thesis in practitioners' own terms: AI collapses
> generation time and inflates verification time. The harness decides which one wins.**

**The single best illustration of what a harness sees and a person cannot:** an Amazon listing was
suppressed because the background was `RGB(255,253,252)` instead of pure white. No human eye resolves
that. Three lines of code do.

⚠️ **axe-core `color-contrast` skips text over background images, obscured text, and images of text.**
Those are exactly the cases a looking critic *can* judge. The tools are complementary, not redundant —
and the harness reports them as `indeterminate` rather than passing them silently.

---

## Typography

📗 **Bringhurst, via Richard Rutter:** *"Anything from 45 to 75 characters is widely regarded as a
satisfactory length of line for a single-column page."* 66 characters ideal; 40–50 for multi-column.
Note the hedge — Bringhurst offers no data. Cite it as craft consensus, not evidence.

📗 **Butterick, *Practical Typography*:** point size **15–25px** on web · line spacing **120–145%** of
point size · line length **45–90 characters** · paragraph separation either a **1–4× point size**
first-line indent *or* **4–10pt** of space, never both · **5–12% extra letterspacing on all caps and
small caps**.

That last one is the source of the standard label-tier exemption: small uppercase type is legible
below the body floor *only when it is tracked out*. The harness uses ≥0.08em.

📗 **Baymard:** cites Emil Ruder at 50–60 characters, accepts up to 75, endorses WCAG's 80 ceiling,
and gives the implementation directly: `max-width: 70ch` or `34em`.

❌ **"Nielsen Norman Group says 50–70 characters per line."** Widely attributed, and no such NN/g
article could be found. **Stop repeating it.** Use Bringhurst, Butterick, or WCAG 1.4.8, all of which
are real and citable.

⚠️ **Modular scale ratios have no evidence base.** 1.2 minor third, 1.25 major third, 1.333 perfect
fourth, 1.5, 1.618 — these are borrowed from musical intervals. No study shows one reads better than
another. **Import the constraint, not the mysticism:** the checkable rule is *"every font-size on the
page is a member of one declared scale,"* never *"the scale is 1.25."*

⚠️ **The 8pt grid is convention.** Its honest justification is arithmetic, not perception: 8 divides
cleanly at 1×/1.5×/2×/3× without fractional pixels.

⚠️ **Refactoring UI:** *"no two values in your scale are ever closer than about 25%"*, and 2–3 colours
with 2 font weights. Genuinely useful and it converts cleanly to a mechanism, but the wording comes
from reader notes on a paid book, not the book.

❌ **Optical alignment.** No published numeric standard exists that converts to a screenshot-checkable
binary. If you want the rule, invent the threshold and **label it as invented.**

❌ **Line-height as a function of measure.** Everyone asserts longer lines need more leading. No
credible published formula. Butterick's flat 120–145% is the defensible version.

---

## Vocabulary worth stealing from computational aesthetics

⚠️ Miniukovich & De Angeli (CHI 2015) report 8 automatic metrics explaining up to **49% of variance**
in webpage aesthetics: visual clutter, colour range, dominant colour count, figure-ground contrast,
**contour congestion**, symmetry, **grid quality**, white space. Ngo et al. add 14 more (balance,
equilibrium, cohesion, density, regularity, economy, rhythm, order/complexity).

Implementing these is a project, not a rule import. But the **names** are the useful part: they give
you precise language for defects that would otherwise come out as "feels cluttered."

---

## What the evidence says about the loop itself

This is the part that changes how you *run* a critique, not what you check.

**Models cannot count or measure from an image, and this is measured.** ⚠️ "Vision language models are
blind" (ACCV 2024): 4 SOTA models average **58.57%** on seven trivial geometric tasks; **56.84% on
counting line intersections**; best model 74% against a human ceiling of 100%.

> **Direct consequence:** *"one accent used at most 3 times per viewport"* and *"headline ≥3.5× body"*
> ask a model to count and to compute ratios from pixels — the two operations with the best-documented
> failure rates. **The rules are right. Asking the model's eyes to evaluate them is wrong.** Run the
> harness, hand the critic the numbers as text.

**Open-ended AI design audit is mostly noise.** 📗 Baymard ran GPT-4 against 12 e-commerce pages with a
ground-truth set of 257 expert-identified issues (6 trained benchmarkers, ~50 hours of comparison):
**80.1% false positives**, 19.9% accuracy. Of the false positives, **8.9% were actively harmful** and
71.1% were wasted time. It found 14.1% of real issues on the live page, and only 25.5% of the issues
**visible in the screenshot it was given**. Nielsen's ROI math: 0.8 hours of expert time saved, 1.0
hour spent rejecting hallucinations — **net −0.2 hours per screenshot.**

> That study used open-ended *"find the problems."* **A fixed rulebook with binary verdicts is the
> intervention**, because a rule the page passes generates no output at all. This is the strongest
> available argument for mechanisms over vibes.

**Binary beats scoring, and one question per call beats a checklist.** ⚠️ MLLM-as-a-Judge: ~70% human
agreement overall but **79.3% on pairwise comparison**, with significant divergence on scoring and
batch ranking. TICK: per-item YES/NO checklists raise exact agreement **46.4% → 52.2%**. CheckEval:
decomposed binary questions improve agreement and cut score variance.

> Two changes follow. **Fire each mechanism as its own call**, because a batched checklist quietly
> reintroduces the holistic mode you were trying to avoid. And **for iteration N vs N−1, ask which is
> closer to the reference** — pairwise is the reliable primitive, scoring is not.

**Crop and zoom. Never overlay grid lines.** ⚠️ UICrit measured grounding: coordinate markers gave IoU
0.186, a **patch grid overlay 0.222**, and **grid *lines* 1.1e-5 — they destroyed performance.**
Feeding a zoomed crop of the region under judgment took grounding IoU from **0.120 → 0.357**.
Separately, multimodal OCR degrades below **150 ppi**. A full-page screenshot downsampled to fit an
encoder is exactly the regime where 14–16px body text becomes unjudgeable.

**Do not let the builder be the critic.** ⚠️ MT-Bench: self-enhancement bias **10–25%**, position bias
**10–15 points** of winrate swing, verbosity bias **15–30 points**. Fresh context is the minimum;
a different model is better. Randomise rule order to blunt position bias.

**Zero-shot critique is mostly invalid.** ⚠️ UICrit: zero-shot Gemini produced 5,927 comments of which
**776 (13.1%) were judged valid**; few-shot plus visual prompting lifted quality 0.31 → 0.48. Examples
sampled by *visual similarity* beat random examples (0.44 vs 0.31). Human-human agreement on critique
validity is only **Fleiss' κ ≈ 0.30**, which is the real ceiling.

**Keep a false-positive budget.** Hold 5–10 fixed pages with known verdicts, **including deliberately
clean ones**, and measure the critic's FP rate against them. A clean page that generates zero findings
is the test that matters, because the exposure is not missed defects — it is confident invented ones.

---

## Prior art

📗 **OneRedOak `claude-code-workflows/design-review`** is the de facto community standard prompt.
Worth stealing: its **7 phases** (prep, interaction, responsiveness at **1440 / 768 / 375**, visual
polish, accessibility, robustness, code health) and its **4-bucket severity taxonomy**
(Blocker / High / Medium / Nitpick), with no numerical scoring.

**Worth rejecting:** its "Problems Over Prescriptions" rule, whose own example is *instead of "Change
margin to 16px", say "The spacing feels inconsistent with adjacent elements, creating visual clutter."*
That is an adjective generator. Prefer the number.

---

## Deterministic CSS gates (no model involved)

- **Project Wallace `css-analyzer` + `constyble`** (open source) — extracts every colour, font-size,
  shadow and spacing value with 200+ metrics, then fails a build on thresholds you declare
  (`"values.colors.totalUnique": 25`). Turns palette and type-scale discipline into a CI gate that
  runs in milliseconds and cannot hallucinate.
- **Chrome DevTools CSS Overview** (built in) — one-click audit of a *rendered* page: all colours by
  role, low-contrast text, and every font size with occurrence counts grouped by weight and
  line-height.
- **stylelint + `stylelint-declaration-strict-value`** — forces declared properties to use tokens
  rather than raw values, at source rather than at render.
- **Playwright `toHaveScreenshot()`** — useful as a *fix-verification* gate, never as a critic: it
  answers "did this change," not "is this good." Steal its anti-flake defaults regardless
  (`animations: "disabled"`, `caret: "hide"`, `scale: "css"`, `threshold: 0.2`).

---

## Sources

WCAG 2.2 Understanding docs (w3.org) for every ✅ row · Lighthouse tap-targets (developer.chrome.com) ·
APCA (git.apcacontrast.com) · axe-core rule descriptions (github.com/dequelabs/axe-core) ·
webtypography.net/2.1.2 · practicaltypography.com/summary-of-key-rules.html ·
baymard.com/blog/line-length-readability · baymard.com/blog/gpt-ux-audit ·
jakobnielsenphd.substack.com/p/ai-ux-evaluation · UICrit arxiv.org/abs/2407.08850 ·
arxiv.org/html/2412.16829 · MLLM-as-a-Judge arxiv.org/abs/2402.04788 · TICK arxiv.org/abs/2410.03608 ·
CheckEval arxiv.org/abs/2403.18771 · UI-Bench arxiv.org/abs/2508.20410 · vlmsareblind.github.io ·
MT-Bench arxiv.org/abs/2306.05685 · CHI 2015 dl.acm.org/doi/10.1145/2702123.2702575 ·
github.com/projectwallace/constyble · github.com/OneRedOak/claude-code-workflows

Compiled 2026-08-13. Verification tier per row is the researcher's own, and ⚠️ items were found
referenced but not opened at the primary source. **Re-verify before quoting a ⚠️ number in anything
that matters.**

---

## Prose mechanisms (for `de-sloppifier`)

**The durable machine signature is grammatical, not lexical.** Word lists date fast, get trained out,
and survive light editing. Sentence structure does not. Order your passes accordingly.

| Mechanism | Finding | | Source |
|---|---|---|---|
| **Present participial clauses** | Instruction-tuned models use them at **5.3× the human rate** (GPT-4o); all four models tested showed the preference | 📗 | Reinhart et al., *PNAS* 122(8):e2422455122 (2025), 67 Biber features |
| Nominalizations | **1.5–2×** human rate | 📗 | same |
| Sentence-length **CV** | Human 78.1% vs machine 50.3%, with **near-identical means** (21.0 vs 21.7 words). The signal is entirely in dispersion | 📗 | Labbé, Labbé & Savoy, *DSH* 40(2) 2025 |
| "Burstiness" | ❌ **Drop the word.** Three incompatible meanings; the popular one is a mutation of a vendor coinage. The only peer-reviewed test found it unreliable | ❌ | Chakraborty et al., EMNLP 2023 (best paper) |
| AI-text detectors | **No tool exceeded 80% accuracy**; only 5 of 14 beat 70%, with systematic bias toward calling output human | 📗 | Weber-Wulff et al., *Int. J. Educational Integrity* 19(1) 2023 |
| Detector fragility | A paraphraser dropped DetectGPT from **70.3% → 4.6%** at 1% FPR | 📗 | Krishna et al., NeurIPS 2023 |

⚠️ **Two widely circulated citations that do not say what people claim.** Desaire et al. (2023)'s
famous **AUC 0.98 is for *paragraph*-length SD, not sentence-length SD** — the sentence-level claim in
that paper is qualitative with no AUC. And O'Sullivan (2025) cannot be cited for sentence rhythm at
all: the word "burstiness" does not appear in it, and it states it *deliberately excludes* measures of
sentence length and syntactic complexity.

❌ **Unverified numbers in circulation — do not repeat:** "edits of 10–15% drop detection below 30%"
and Weber-Wulff's "74% raw / 26% after modification." Both trace to marketing blogs, not the papers.

**Bias correction worth knowing:** the well-known non-native-speaker false-positive result indicts
**2023 commercial detectors**, not detection as such — Binoculars (ICML 2024) shows 99.67% equal
accuracy on corrected and uncorrected essays. Cite the finding with its scope.
