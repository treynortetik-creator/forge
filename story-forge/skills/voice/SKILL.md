---
name: voice
description: Use when extracting an author voice fingerprint or style sheet from writing samples, produces the voice spec that all story-forge drafting skills (chapter-generation, de-sloppifier, etc.) consume. Triggers on "build my voice profile", "extract my writing style", "create a style sheet from my samples", "voice fingerprint", or any request to anchor AI generation to a specific author's prose.
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep]
---

# Voice Skill, Author Voice Fingerprint Extractor

**Role:** PRODUCER. This skill generates the voice spec that downstream drafting skills consume. It does not draft prose. It produces a reusable style sheet and fingerprint document.

---

## Dependency Check (Run First, Before Anything Else)

This skill has one required input: **author writing samples**.

Before proceeding, confirm the user has provided (or will paste) prose samples that meet these criteria from `${CLAUDE_PLUGIN_ROOT}/references/writing/voice-matching.md`:

- Minimum 2,000 words of finished, edited fiction prose (3,000-5,000 is better)
- Pull from at least two scene types if possible: action, quiet/reflective, dialogue-heavy
- Fiction prose only: not blog posts, not emails, not non-fiction
- Edited manuscripts outperform raw drafts; the editing pass converges toward the actual voice

If no samples are present, stop here and say:

> "This skill needs author writing samples. Paste 2,000-5,000 words of your finished, edited fiction prose (pull from different scene types if you can). Blog posts and emails do not work for this."

Do not generate or guess a voice. Do not proceed without the samples.

---

## Process

### Step 1, Extraction Pass (Forensic Fingerprint)

With the samples in hand, run the following extraction prompt verbatim (from `${CLAUDE_PLUGIN_ROOT}/references/writing/voice-matching.md`). Feed it the prose directly after the prompt:

> You are a forensic editor and writing analyst. Your job is not to evaluate quality, it is to identify pattern. Below is a body of prose from a single fiction author. Read it carefully, then produce a **voice fingerprint** for this writer. This fingerprint will be used to build a Claude skill that generates new prose in this style. Analyze the following dimensions and be specific, not vague descriptors like "lyrical" or "gritty," but architectural observations that can be turned into instructions: sentence rhythm and length, vocabulary level, dialogue handling, POV approach, naming patterns, how description is distributed.

The output is a structured report covering: sentence length ranges, vocabulary tier, dialogue tag patterns, POV habits, characteristic constructions, and recurring syntactic moves. Capture this as the raw fingerprint.


### Step 1.5, Register Sampling — do not skip this

🔴 **The most commonly skipped stage, and the one that makes the difference.** Handing a model 6,000
unbroken words and asking "what is this author's style" returns an **average**. A voice is most visible
in **how it changes between registers** — the same writer is a different instrument in a quiet
descriptive passage than in an argument or a fight. Averaging that away is how you get a style sheet
that describes nobody.

From **each** sample (up to three; three beats one), extract passages **verbatim**:

| Register | What to look for | Length |
|---|---|---|
| **Calm / descriptive** | Quieter narration, description, interiority. Little dialogue, little action | ~400 words |
| **Dialogue** | A real exchange between characters | ~400 words |
| **Action / high drama** | The most kinetic or highest-stakes passage available | ~400 words |
| **Comedy** *(conditional)* | **Only if the work is genuinely comic.** Omit entirely otherwise — do not manufacture one | ~400 words |

**Quote them exactly.** Paraphrasing here destroys the evidence the next step reasons over. If a
register is genuinely absent from a sample, say so and move on rather than inventing filler.

**Step 2 consumes these extracts, not the raw samples.**

### Step 2, 13-Dimension Style Sheet Pass

Using **the register extracts from Step 1.5** (not the raw samples), generate the full style sheet. The instrument below is a condensed form of the source automation's
`Create the Style Sheet` node; the fuller method, including why the two stages exist, is in
`${CLAUDE_PLUGIN_ROOT}/references/writing/style-guide-prompt.md`:

> You are going to be given writing samples from an author. Draft a prose style sheet giving instructions on how to write like these samples, including small verbatim snippets from the samples as examples. The style sheet is for an LLM to write fiction in the same style. Frame the response as INSTRUCTION (not observation). Rules: (1) base all observations ONLY on the provided samples; (2) describe patterns in general terms AND give specific quoted examples; (3) cover ONLY the 13 elements listed below. Output in Markdown using the exact `# Style Guide` -> `## 1. Narrative Rhythm` structure, each section with the specified sub-bullets (Summary/Key traits, POV distance/Evidence, etc.). For POV, address distance only, not first/third person. For punctuation, explicitly forbid em dashes and name substitutes. End with the do/avoid checklist (complete sentences). Focus on prose style, not characters or plot. Be thorough.

The 13 dimensions to cover (in order):
1. Narrative Rhythm
2. Close-vs-Distant POV (distance only, not first/third person, keeps the spec modular across projects)
3. Formality
4. Overall Tone
5. Emotional Range
6. Average Sentence Length and Rhythm
7. Paragraphing
8. Average Grade Level
9. Dialogue Style (push "said/asked" and action beats)
10. Sentence Openings (push variety)
11. Clause Structure and Complexity
12. Punctuation Habits (NO em dashes, name the substitute patterns explicitly)
13. Emphasis and Cadence Tricks (signature moves)

End with a **Summarized Style Rules checklist**: 8-15 "do" rules + 8-15 "avoid" rules, written as complete sentences.

Two design rules to preserve (from the source):
- POV covers distance only, so this spec stays modular and reusable across projects with different POV choices
- The em-dash ban is baked in here at the style layer, reinforcing `${CLAUDE_PLUGIN_ROOT}/references/writing/banned-words.md` and `${CLAUDE_PLUGIN_ROOT}/references/writing/anti-slop.md`

### Step 3, Prose Anchor

Pull one short passage (100-200 words) from the supplied samples that best represents the author's characteristic voice at its most recognizable. This becomes the anchor example embedded in the output file. It is not analyzed, it is a reference signal for the model during generation.

### Step 4, Assemble the Voice Spec File

Write the output to: `./voice-[author-or-penname].md`

Structure of the output file:

```
# Voice Spec: [Author / Pen Name / Series Name]
Generated: [date]
Samples word count: [count]
Scene types sampled: [list]

---

## Voice Fingerprint
[Step 1 output]

---

## Style Guide
[Step 2 output, full 13-dimension sheet with do/avoid checklist]

---

## Prose Anchor
[Step 3, the 100-200 word passage, blockquoted]

---

## Usage Notes
- Load this file into any story-forge drafting skill before generating prose
- One spec per pen name or distinct series voice
- Revise after each project as the voice develops
- Pairs with: `${CLAUDE_PLUGIN_ROOT}/references/writing/banned-words.md` (prohibited vocabulary), `${CLAUDE_PLUGIN_ROOT}/references/writing/anti-slop.md` (deslop pass)
```

Write it beside the samples you analysed, in the current working directory.

### Step 5, Confirm and Report

Tell the user:
- The file path where the spec was written
- The word count of samples processed
- The scene types sampled
- One sentence on any notable voice trait the extraction surfaced

---

## Draft-Time Doctrine (Write Like the Edit)

Fold these into every generated style sheet's do/avoid checklist, alongside the sample-derived rules. They come from a 131-edit author hand-pass (2026-07-18) and encode what a line edit would otherwise have to remove. A spec that carries them produces drafts that need less surgery.

1. Never narrate the narration (no "the truest thing," no "I want you to understand," no explaining why the telling matters).
2. One figure per beat; no cute similes; a plain verb beats a simile that outweighs its noun.
3. Stop when the image lands; no re-describing clauses, no end-of-paragraph imagery recap.
4. Name the noun; no vague "thing/something" hedges; violence gets its real verb.
5. Split at the pivot; payoffs get their own short sentence; fragments legal.
6. Diction plainer or crueler, never fancier.
7. Concrete props over abstractions; declared acts get a hand doing them.
8. Dialogue does the work; narration never duplicates what a line already carries.
9. Flourishes come from the story's established coinage, never fresh ornament.
10. An aphorism needs a concrete mechanism proved by its scene; it never grades itself; one per scene.
11. Keep the first rhetorical reversal in a paragraph, cut the third (antithesis density cap).
12. Order beats in performance chronology, the order the room experiences them.
13. No emotional summary after the emotion already landed.

**Banned families (state them in dimension 12/13 territory of the sheet).** ⚠️ *Example set from one manuscript — derive your own from the samples:* the word "ledger" and any order/counting meta-narration (concrete counts of real objects are exempt); emotion sitting/settling in the chest + "cold" as an emotion descriptor (physical cold exempt); "held breath" as emotional shorthand; generic "coat" as default garment (name the specific garment or cut it; plot/character garments exempt); in multi-POV work, no cross-voice idiom leakage between narrators.

---

## Related Craft Notes (Reference, Do Not Duplicate)

These wiki notes govern how the voice spec is used downstream. Do not copy their content into the spec file; link or reference them:

- `${CLAUDE_PLUGIN_ROOT}/references/writing/voice-matching.md`, method and quality rules for this extraction process
- `${CLAUDE_PLUGIN_ROOT}/references/writing/style-guide-prompt.md`, the 13-dimension instrument this step operationalizes
- `${CLAUDE_PLUGIN_ROOT}/references/writing/banned-words.md`, the prohibited vocabulary list; pairs with the em-dash ban in dimension 12
- `${CLAUDE_PLUGIN_ROOT}/references/writing/anti-slop.md`, the 7-rule strategic framework and 3-pass deslop automation; the Style Check step downstream uses this
- `${CLAUDE_PLUGIN_ROOT}/references/writing/humanizing-ai-prose.md`, root-cause theory for why AI defaults to generic prose; voice injection is one of three methods in that stack
- `${CLAUDE_PLUGIN_ROOT}/references/writing/chapter-generation-pipeline.md`, the downstream consumer of this spec (First Draft step 10, Style Check step 12)

---

## Key Rules Enforced by This Skill

1. No generation without samples. The skill produces nothing if samples are absent or below 2,000 words.
2. Observations are turned into INSTRUCTIONS in the style sheet, not descriptive notes.
3. The POV dimension covers distance only. POV person (first/third) is decided at a later pipeline stage.
4. Em dashes are banned in the output spec and flagged as banned in dimension 12 with explicit substitutes named.
5. One spec per pen name or series voice. Do not mix voices from different projects.
6. The spec is a living document. Note at the bottom of the file when it was last revised and from what samples.

---

## Iteration Notes

This is a living skill. After each project:
- Add a dated revision note at the bottom of the voice spec file
- If the author's voice shifted meaningfully across the project, re-run steps 1-3 with the new manuscript as the sample source
- If a pattern shows up in three or more revision passes, promote it into the fingerprint as a standing rule
