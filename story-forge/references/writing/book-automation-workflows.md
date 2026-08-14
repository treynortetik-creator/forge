---
title: "Book Automation Workflows — n8n Implementation Catalog"
type: reference
tags: [automation, n8n, book-pipeline, story-hacker, recovered]
created: 2026-06-29
updated: 2026-06-29
source: `references/writing/book-automation-workflows.md`
status: living
---

# Book Automation Workflows — n8n Implementation Catalog

These are the recovered n8n workflow exports behind the documented Story Hacker / book-creation pipeline. Ten JSON files were found in `references/writing/book-automation-workflows.md` and cataloged 2026-06-29. The raw JSON files are preserved there; this note captures what each one does, how it works, and how they connect.

The implementations correspond to the architecture described in [[storyhacker-pipeline-architecture]] and use the prompt techniques cataloged in [[story-hacker-prompts]].

---

## Workflow Catalog

### 1. Full Book Automation: Braindump to Dossier

**Stage:** Pre-writing, concept development.

**What it does:** Takes a title and a raw braindump via an n8n form, pulls four Google Docs templates (tropes, plot structure, character, worldbuilding), and produces a story dossier: a structured catalog of characters, worldbuilding elements, a selected premise, and an outline plan.

**Flow:** Form trigger captures title + braindump. Pulls four template docs in sequence. "Brainstorm" generates 12 premises from tropes + braindump. "Pick the Best" evaluates them on logic, originality, and emotional gut-punch potential and outputs only the chosen one. "Complete Story Dossier" builds the full dossier. "Dossier Critique" audits it for logical consistency, originality, and emotional impact. "Dossier Rewrite" applies critique suggestions. Saves to a blank Google Doc.

**Model:** Gemini 3 Pro (via OpenRouter) throughout; temperature 1 for generative nodes, 0.7 for critique and rewrite.

**Prompt technique:** Generate-Evaluate-Critique-Rewrite loop. The "Pick the Best" node uses strict selection criteria as evaluation axes. The critique node is explicitly told not to rewrite, only to plan; the rewrite node is told to implement only the suggested changes and nothing else. This separation of roles is the core pattern.

---

### 2. Full Book Automation: Dossier to Full Outline

**Stage:** Pre-writing, from dossier to outline, characters, and worldbuilding.

**What it does:** Reads the completed dossier and produces three parallel outputs: a fleshed-out character sheet (with Myers-Briggs, Enneagram, dialogue samples), a categorized worldbuilding sheet, and a chapter-by-chapter outline.

**Flow:** Form trigger (title + author notes). Pulls all four templates plus the dossier plus blank target docs. "Characters" builds full profiles for major and minor characters. "Critique Characters" + "Rewrite Characters" applies the Generate-Critique-Rewrite cycle. Parallel stream: "Worldbuilding" categorizes all elements, then its own Critique + Rewrite cycle. After both streams write to their docs, "Outline" generates the full chapter summaries pulling from all three populated docs. Uses the last 2000 words trick at outline stage to maintain continuity.

**Model:** Gemini 3 Pro for characters and worldbuilding cycles. Claude Sonnet 4.5 for the outline node (the most creatively demanding task).

**Prompt technique:** Multi-stream Generate-Critique-Rewrite applied independently to characters and worldbuilding before they feed the outline. Character prompts include explicit personality profiling (Myers-Briggs, Enneagram, Clifton Strengths) plus dialogue samples in four emotional states, which forces the model to commit to distinct voices. The outline prompt instructs "~100 word descriptions with specific details, written as though handed to a ghostwriter."

---

### 3. Full Book Automation: Outline to Chapters

**Stage:** Chapter generation (first-generation pipeline, now superseded by the Advanced version).

**What it does:** Takes the outline, character sheet, worldbuilding doc, prose style guide, and a forbidden-words list, then generates chapter drafts one by one in a loop.

**Flow:** Form trigger. Loads prose style, forbidden words, character sheet, worldbuilding, outline, and blank draft doc. Parses chapter names into a JSON array (Gemini Flash). Loops: fetches last 2000 words from the accumulating draft doc (JavaScript extraction). "Scene Brief" generates a per-chapter blueprint: POV, 20-25 scene beats with blocking, character states, setting, tone, continuity notes, symbolism. "First Draft" writes approximately 3000 words from the scene brief. "Improvement Plan" critiques the draft across 12 categories (show vs. tell, clichés, passive voice, dialogue tags, sentence variety, etc.). "Rewrite" applies only the suggested changes. Appends to the Google Doc and loops.

**Model:** Gemini 3 Pro for Scene Brief, First Draft, and Improvement Plan. Gemini 2.5 Flash for the chapter-name parser and the final Rewrite.

**Prompt technique:** The Scene Brief is the key innovation: it is a structured chapter blueprint with 20-25 numbered scene beats and physical blocking before any prose is written. The First Draft prompt contains an explicit no-em-dash rule, a sentence-variety mandate, and a no-metaphors rule. The improvement plan deliberately separates critique from rewriting into two distinct nodes to prevent the rewriter from making unauthorized changes.

---

### 4. Advanced Book Automation: Outline Generator

**Stage:** Outline generation (the "Advanced" replacement for the simple outline step in workflow 2).

**What it does:** Generates a complete chapter-by-chapter outline brief with per-chapter content ratings (Spice/Violence/Swearing), then runs an emotional audit and a logic check before adding six quantified "emotional sliders" per chapter.

**Flow:** Form trigger (author notes only). Pulls tropes, themes, plot template. Fetches dossier, character sheet, worldbuilding. "Condense Tropes Template" compresses the tropes doc to one sentence per trope (cheap model). "Write Outline" generates 2-3 sentence summaries per chapter including POV, Spice/Violence/Swearing levels. "Emotional Check" runs a six-dimension emotional audit (emotional setup vs. payoff, grief and loss, climax readiness, relationship arcs, tonal whiplash, protagonist interior arc). "Rewrite 1" implements emotional fixes. "Sliders" annotates each chapter with six quantified narrative-tension sliders (Tension/Dread/Emotional Intimacy/Relationship Tension/Pacing Energy/Humor, each scored 1-10 with a one-sentence rationale). "Logic Check" runs a seven-category logic audit (dossier consistency, plot template consistency, internal logic, plausibility, thematic resonance, jumping the gun, slider consistency). "Rewrite 2" implements logic fixes. Saves the final outline with all metadata to Google Doc.

**Model:** Gemini 3 Flash (cheap) for trope condensing, Gemini 3 Flash (cheap) for rewrite nodes. Claude Opus 4.6 for Write Outline. Kimi K2 Thinking (reasoning model) for Emotional Check and Logic Check. Claude Sonnet 4.6 for Sliders. Model tiering is intentional: the most expensive model writes the outline, reasoning models do the audits, cheap models apply fixes.

**Prompt technique:** The slider system is the distinguishing innovation: instead of vague outline quality checks, each chapter gets six quantified narrative-tension dimensions. The Emotional Check prompt operates entirely in the emotional lane, explicitly told to ignore plot logic. The Logic Check is instructed to use a developer/QA mindset ("100% consistent, plausible, and logical"). Separation prevents audit bleed between emotional and logical concerns.

---

### 5. Advanced Book Automation: Outline to Chapters

**Stage:** Chapter generation (current production version, more sophisticated than workflow 3).

**What it does:** The full chapter generation loop with context-slicing, slider-aware character states, dynamic word-count estimation, separate chronology checks on both the scene brief and the draft, and a style check pass.

**Flow:** Form trigger (which chapters, tense, author notes). Loads prose style, character sheet, worldbuilding, outline, blank draft doc. Parses chapter names. Loops per chapter: fetch last 2000 words. "Plot Selector" extracts only this chapter's outline entry verbatim. "Character Selector" identifies active vs. mentioned characters and reproduces only relevant profiles. "Worldbuilding Selector" does the same for settings and worldbuilding. "Wordcount Estimator" picks a target (1000-5000). "Wordcount Estimator 2" multiplies by 1.25 (capped at 6000) to give the first draft room. "Plot Scene Brief" builds beats+blocking + cliffhanger design. "Character Scene Brief" produces chapter-specific character snapshots with all 15 sliders adjusted for this scene's emotional state. "Worldbuilding Scene Brief" strips forward-looking content. "Chronology Check" (on the three briefs combined) checks for reveal-too-early, already-revealed details, and cliffhanger continuity. "Scene Brief Rewrite" applies fixes. "First Draft" writes from the cleaned brief. Fetches last 20,000 words for continuity. "Chronology Check 2" (on the draft) checks against full outline and previous text. "Style Check" compares against the prose style guide. "Rewrite" applies both improvement plans. Saves and loops.

**Model:** Gemini Flash / Gemini 3.1 Flash Lite for cheap extraction tasks. Gemini 3.1 Pro for scene briefs and rewrites. Claude Haiku 4.5 for character and worldbuilding selectors. Claude Sonnet 4.6 for first draft (the creative center of the pipeline).

**Prompt technique:** Context-slicing is the core architectural improvement over workflow 3: instead of injecting the entire character sheet and worldbuilding doc into every node, dedicated selector nodes pre-filter to only the characters and elements relevant to each chapter. This reduces context noise. The 15-slider Character Scene Brief adjusts each character's baseline slider values (+/-10 scale) for this specific scene's emotional state, giving the first-draft node granular behavioral guidance. The cliffhanger design in the plot scene brief uses an explicit guide with five cliffhanger types and four anti-patterns. Two separate chronology checks (one before writing, one after) catch different classes of continuity error.

---

### 6. Book/Script Story Hacking

**Stage:** Analysis of existing works.

**What it does:** Takes any novel or screenplay, runs a per-chapter summary pass (Summary+), then runs a full structural analysis to extract a reusable, anonymized story template.

**Flow:** Manual trigger. Gets blank Story Hack doc. Downloads novel/script from Google Drive as HTML. JavaScript splits by H1 headers (one item per chapter). Loops: "Create Summary+" generates per-chapter summary, characters with Heart's Desire, setting, conflict, tropes, and intensity/spice/violence/swearing ratings. Saves each to the doc. After all chapters, "Analysis Part 1" reads the accumulated summaries and generates: genre, common tropes, character arcs, character archetypes, theme identification, plot devices and foreshadowing, key structural beats (inciting incident, midpoint, climax, denouement), worldbuilding, magic system, and average ratings. "Analysis Part 2" produces a "plot template" with each chapter described in non-identifying terms (protagonist/antagonist/etc. instead of names) plus structural-beat flags (hook, pinch points, all-is-lost, etc.).

**Model:** Gemini 3 Flash for per-chapter summaries (cheap, high-volume). Gemini 3 Pro for both analysis passes.

**Prompt technique:** Two-tier analysis pattern: ground-level chapter summaries first (data collection), then structural synthesis second. The "Analysis Part 2" template anonymization is deliberate: it produces a genre-agnostic structure skeleton that can be applied to any new book. The spice/violence/swearing rating scales are embedded verbatim in the per-chapter summary prompt, with 10-point rubrics for each.

---

### 7. Editing: Line Editor and De-sloppifier

**Stage:** Post-draft editing and AI-slop removal.

**What it does:** Takes a finished draft and runs a three-pass editing pipeline: sentence/paragraph pacing first, then traditional line edits, then AI-pattern removal.

**Flow:** Manual trigger. Gets blank output doc. Downloads original draft from Drive. JavaScript converts HTML formatting tags to semantic markup (bold/italic/underline). Markdown converter. JavaScript splits into 1500-word chunks. Loops per chunk: "Sentence/Paragraph Pacing" analyzes sentence variety, repeated sentence-starters, dense paragraph blocks, uniform sentence length, formulaic paragraph architecture, and a 200+ item AI-filler-word list. "Rewrite 1" applies pacing changes. "Various Line Edits" audits adverbs (intensity adverbs, emotional-label adverbs, modified absolutes), dialogue tags (flags non-said/non-asked), action beat opportunities, passive voice (six categories: was+ing, be+past participle, get-passives, filter words, weak/hedging verbs, dummy subjects), clichés, redundancies, and repetitions. "Rewrite 2" applies line edits. "De-sloppify" flags AI-specific patterns: negative parallelisms, rule-of-three overuse, em-dash overuse (all em-dashes flagged for removal), safe/predictable word choices, abstract language, flat transitions, unearned personifications. "Rewrite 3" applies de-slop changes. Saves each processed chunk to the output doc.

**Model:** Alternates Claude Sonnet 4.6 and Gemini 3.1 Pro across the six analysis/rewrite nodes; high timeout settings (700 seconds) with retry logic.

**Prompt technique:** Three-stage separation of concerns is the core architecture. Each audit node explicitly does not rewrite; it produces a change log. Each rewrite node implements only the changes listed, nothing more. The pacing audit uses a burstiness framing (short sentences for shock, mixed cadence for narrative). The De-sloppify node has an explicit "ALWAYS REMOVE EM DASHES, ALL OF THEM" instruction embedded. This implements the same anti-slop rules documented in [[anti-slop]] and de-sloppifier's Pass 3 list.

---

### 8. Book to Summary+

**Stage:** Analysis utility.

**What it does:** Lighter-weight chapter-by-chapter summary generator. Produces a Summary+ doc covering each chapter's summary, characters, setting, conflict, tropes, and top three key quotes.

**Flow:** Manual trigger. Gets blank Summary+ doc. Downloads book from Drive as HTML. Splits by H1 headers. Loops: "Run Summary+" generates the per-chapter output. Saves each entry to the doc.

**Model:** GPT-5 Mini (via OpenRouter). The cheapest model in the fleet; appropriate for the simpler extraction task.

**Prompt technique:** Simplified single-pass extraction; no multi-stage analysis. Adds "Key Quotes" field (top 3 verbatim passages with marketing potential) that is absent from the fuller Story Hacking workflow. Designed for quick reference generation, not deep structural analysis.

---

### 9. Public Domain (Cleaned-up Version)

**Stage:** Source preparation / utility.

**What it does:** Modernizes spelling and grammar in public domain texts without changing vocabulary or meaning, handling OCR errors and archaic spellings, producing a clean modern-English version suitable for study or Story Hacking.

**Flow:** Manual trigger. Gets blank cleaned-up doc. Gets original public domain text from Google Docs. JavaScript splits into 1000-word sentence-safe chunks (with a 1600-word hard cap, handles mid-sentence boundaries). Loops: "Create Cleaned-Up Version" modernizes spellings (no word substitutions), removes footnote references, applies Chicago Manual of Style grammar, preserves original line breaks and stanza structure for poetry, fixes OCR errors, formats chapter/section titles as H1 Markdown headers. Saves each chunk to the cleaned-up doc.

**Model:** Gemini 3 Flash. Low-complexity task; cheap model sufficient.

**Prompt technique:** Explicit preservation rules: "change spelling only, not the word itself," "if there is a conflict, err on the side of the original style." The chunk splitter uses sentence-boundary detection to avoid splitting mid-sentence, which matters for poetry.

---

### 10. Short Story Hack

**Stage:** Analysis of short fiction.

**What it does:** Applies the Story Hacking analysis framework to short stories, with adaptations for the form: adds a "Conceptual Hook" analysis, a "Magic Sword" identification, and a try/fail cycle breakdown not present in the novel version.

**Flow:** Manual trigger. Creates a new Google Doc for output. Downloads a file of short stories from Drive as HTML. Splits by H2 headers (one story per section). Loops: "Analyze Each Short Story" generates the full analysis. Saves each to the doc.

**Model:** Gemini 3 Pro.

**Prompt technique:** Extends the novel Story Hacking prompt with short-fiction-specific additions. "Magic Sword" asks what ability/item/knowledge the protagonist gains that could theoretically solve the inciting incident's problem. Try/Fail Cycles maps each attempt/failure explicitly before the climax. Heart's Desire tracking asks not just what the character wants but whether they get it, and whether they learn their desire was misaligned. Ends with Prose Examples: five or six verbatim passages demonstrating excellent line-level craft, making each analysis double as a style reference.

---

## How They Chain

The ten workflows form a production pipeline with branches for utility tasks:

```
BRAINDUMP
    |
Braindump to Dossier (1)
    |
Dossier to Full Outline (2) -----> Advanced Outline Generator (4)
    |                                           |
    +--------------------------------------------+
                        |
            [Full Outline with sliders, character sheets, worldbuilding]
                        |
Outline to Chapters (3) -----> Advanced Outline to Chapters (5) [CURRENT]
                        |
                [Chapter drafts]
                        |
        Line Editor and De-sloppifier (7) [POST-DRAFT]

PARALLEL / STANDALONE BRANCHES:
Book/Script Story Hacking (6)  ---  analysis of any existing novel/script
Short Story Hack (10)          ---  analysis of short fiction collections
Book to Summary+ (8)           ---  quick summary generation for any book
Public Domain Cleanup (9)      ---  modernizes source texts for study/hacking
```

Workflows 3 and 4/5 represent two generations: workflows 1-3 are the "Full Book" (first generation) series using simpler scene briefs. Workflows 4 and 5 are the "Advanced" replacements. Workflow 4 (Advanced Outline Generator) adds the emotional audit and slider system on top of what workflow 2 produces. Workflow 5 (Advanced Outline to Chapters) replaces workflow 3 with context-slicing, character scene briefs, and dual chronology checks.

The editing workflow (7) is downstream of any generation pipeline and operates independently on a finished draft.

---

## Maps to Existing Notes

- [[storyhacker-pipeline-architecture]] documents the architecture these workflows implement. This catalog note provides the ground-truth implementation details that note was written without.
- [[factory-workflow-vs-storyhacker-pipeline]] records that these workflows are reference architecture, not the process that drafted G. Rench; read it before assuming any of this ran in production.
- [[chapter-generation-pipeline]] describes the 13-step per-chapter loop that workflow 5 implements. Nodes 1-3 = selectors; 4 = Wordcount Estimator; 5-7 = scene briefs; 8 = Chronology Check; 9 = Scene Brief Rewrite; 10 = First Draft; 11 = Chronology Check 2; 12 = Style Check; 13 = Rewrite.
- [[story-hacker-prompts]] is the prompt library. These n8n exports are the automation wrappers that deploy those prompts.
- [[anti-slop]] and de-sloppifier's Pass 3 list both feed directly into workflows 5 and 7. Workflow 7 (De-sloppifier) is the automated implementation of the three-pass process described in anti-slop.
- [[outlining-method]] describes what the Advanced Outline Generator (workflow 4) builds, including the slider framework.
- [[self-editing]] describes the principles that workflow 7's three editing passes implement.

---

## Related

[[storyhacker-pipeline-architecture]] [[chapter-generation-pipeline]] [[story-hacker-prompts]] [[outlining-method]] [[anti-slop]] de-sloppifier's Pass 3 list [[self-editing]]
