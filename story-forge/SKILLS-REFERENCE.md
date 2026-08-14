# story-forge Skills Reference

Your book-creation pipeline, rebuilt as a Claude Code plugin from the recovered n8n automations. Seventeen skills plus four chaining commands. Claude runs each skill; small python helpers handle the deterministic glue (chunking, wordcount, file assembly).

Every consuming skill has a **dependency check**: if it needs a world, a voice, an outline, or a dossier that does not exist yet, it stops and tells you which upstream skill to run first, instead of guessing.

---

## The main pipeline (idea to drafted chapters)

These run in order. The artifact each one produces is the input to the next.

**1. braindump-to-dossier.** Turns a raw story idea into a structured dossier. Give it a braindump and a title; it generates premises, picks the strongest on logic, originality, and emotional gut-punch, then builds a full dossier (characters, worldbuilding, synopsis, outline plan) through a critique-and-rewrite loop.
- *Needs:* a braindump and a title. *Produces:* the dossier.

**2. dossier-to-outline.** Turns the dossier into the three production documents: a character bible, a worldbuilding sheet, and a chapter-by-chapter outline. Each goes through generate, critique, rewrite.
- *Needs:* a dossier (from step 1). *Produces:* character bible, worldbuilding sheet, outline.

**3. outline-generator.** The advanced outliner. Builds a chapter-by-chapter outline with a six-dimension emotional audit and per-chapter sliders (Tension, Dread, Emotional Intimacy, Relationship Tension, Pacing Energy, Humor), plus a logic check. Use it when you want the richer, instrumented outline before drafting.
- *Needs:* dossier, character sheet, worldbuilding sheet. *Produces:* the advanced outline.

**4. voice.** Extracts an author voice fingerprint, a style sheet, from writing samples. This is the voice spec the drafting skill anchors to, so the prose sounds like a chosen author and not like generic AI.
- *Needs:* writing samples. *Produces:* the voice spec. (Run it any time before drafting.)

**5. outline-to-chapters.** The drafting engine. Runs the full thirteen-step chapter-generation pipeline per chapter: context-slicing selectors for plot, characters, and world; wordcount estimation; a three-part scene brief; chronology checks before and after the draft; first draft; style check; final rewrite.
- *Needs:* an outline, a character bible, a worldbuilding sheet, and a voice spec. *Produces:* drafted chapters.

---

## Short-story path (scene-based, 5,000 to 7,000 words)

A parallel track for short fiction. It replaces the three-stage structural expansion (character bible, worldbuilding sheet, chapter outline) with two lighter stages and a scene-based draft. Voice, de-sloppifier, and logic-check are shared with the novel pipeline unchanged.

**1. short-story-dossier.** Turns a raw idea into a compact short-story-scaled dossier: the single unified effect (Poe), the one central irreversible change (Rust Hills), the protagonist's heart's desire and magic sword (Wulf Moon), a cast of 2 to 6 with moral-function slots, one POV, the conceptual hook, and the target word band. Lighter and tighter than the novel dossier; fits on two pages.
- *Needs:* a braindump and a working title. *Produces:* the short-story dossier.

**2. short-story-outline.** Maps the dossier's 8-Point Plot onto 5 to 8 scenes, each tagged with its structural job and a yes-but/no-and try/fail beat. Specifies the payload first line, the opening contract, and the ending move (one of four). Produces the Chekhov's Gun accounting. For dark-comedy and crime stories, adds a tonal-control and twist architecture pass.
- *Needs:* a short-story dossier (from step 1). *Produces:* the scene outline. Requires human review before drafting.

**3. short-story-draft.** Produces the full story prose, scene by scene (target 5,000 to 7,000 words). Enters each scene late, leaves early, applies Le Guin's crowd-and-leap compression, and locks the narrator's register (critical for deadpan dark comedy). Uses the voice spec if present; anchors to the dossier's genre and tone signal if absent.
- *Needs:* the scene outline (from step 2), the short-story dossier (from step 1), and optionally a voice spec. *Produces:* the story draft.

Then hand off to **de-sloppifier** and **logic-check** exactly as in the novel pipeline.

**/story-forge:short-story.** The full short-story chain: voice (optional) → short-story-dossier → short-story-outline → short-story-draft → de-sloppifier → logic-check.

---

## Editing and QC

**de-sloppifier.** The anti-slop line editor. Runs a three-pass edit on roughly 1,500-word chunks: pacing and rhythm, line-level edits, then AI-pattern removal (kills generic AI tells, cliche, vocabulary inflation, and em-dashes).
- *Needs:* a drafted chapter or passage. *Produces:* cleaned prose.

**logic-check.** The continuity auditor. Runs a six-category logic check plus chapter-level chronology criteria against your story bible, catching plot holes, timeline breaks, convenience failures, information revealed too early, foreshadowing gaps, and worldbuilding contradictions.
- *Needs:* a draft (or outline or dossier) and the story bible. *Produces:* an audit report.

---

## Analysis and source tools (standalone)

These do not need the pipeline. Each just needs its own input text.

**story-hacker.** Reverse-engineers an existing book or script into an anonymized, reusable plot template. Per-chapter scene analysis, then a two-pass structural breakdown into a genre-neutral skeleton you can build a new story on.
- *Needs:* a source text. *Produces:* a reusable plot template.

**short-story-hacker.** The same move for short fiction. Breaks a short story into its structure: the magic sword, the try/fail cycles, the heart's-desire arc, the inciting incident, the conceptual hook, with verbatim prose examples.
- *Needs:* a short story. *Produces:* a structural breakdown.

**book-summarizer.** Per-chapter analysis of a finished or draft manuscript: five-to-six-sentence summaries, character breakdowns with each character's heart's desire, setting-function notes, conflict identification, trope detection, and marketing-ready quote extraction.
- *Needs:* a manuscript or chapters. *Produces:* summaries and pull-quotes.

**public-domain-cleanup.** Preps a raw public-domain text (often OCR-scanned or archaic) by modernizing spelling, fixing OCR errors, and cleaning punctuation in roughly 1,000-word passes, without changing the vocabulary or meaning.
- *Needs:* a public-domain source text. *Produces:* a clean file ready for the pipeline.

---

## Commands (the chains)

Commands wire skills together so you run a whole stage with one call.

**/story-forge:full-book.** The whole pipeline end to end: voice, then braindump-to-dossier, then dossier-to-outline, then outline-to-chapters, passing artifacts between steps.

**/story-forge:short-story.** The full short-story pipeline: voice (optional), then short-story-dossier, then short-story-outline, then short-story-draft, then de-sloppifier, then logic-check. Produces one complete 5,000 to 7,000 word story.

**/story-forge:edit-pass.** The editing chain on a draft: de-sloppifier, then logic-check.

**/story-forge:hack.** story-hacker on a comp title to pull a reusable structure (use short-story-hacker for short fiction).

---

*Tip: the individual skills hold the real prompts and run one transform each. The commands are the orchestration layer that chains them. You can always invoke a single skill directly when you only need that one step.*

## clean-export

**Final export pass.** Strips invisible provenance characters — zero-width, bidi controls, Unicode
TAG payloads (`U+E0000–E007F`, where a whole hidden ASCII message can live), and exotic spaces
normalised to plain spaces. **Never alters a word**: it computes a canonical form of input and
output and refuses to write if anything outside its target set differs.

Preserves ZWJ + variation selectors by default so emoji don't break (`--strip-emoji-glue` to remove).

```bash
python3 "${CLAUDE_PLUGIN_ROOT}"/skills/clean-export/scripts/clean_text.py draft.md                    # report only
python3 "${CLAUDE_PLUGIN_ROOT}"/skills/clean-export/scripts/clean_text.py draft.md -o draft.clean.md
python3 "${CLAUDE_PLUGIN_ROOT}"/skills/clean-export/scripts/clean_text.py chapters/ -o out/
```

⚠️ It does **not** remove statistical/token-choice watermarks (Claude's, from 2026-08-02). Those
require rewriting the text with a model, which for fiction re-slops prose the de-sloppifier just
cleaned. The de-slop + hand-edit pipeline already degrades that signal, and improves the writing
while doing it.

Runs **last**: braindump → dossier → outline → draft → story-hacker → de-sloppifier → edit-pass →
**clean-export**.
