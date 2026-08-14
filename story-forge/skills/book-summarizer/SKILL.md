---
name: book-summarizer
description: "Use when you have a completed or draft manuscript (or individual chapters) and want per-chapter analysis: 5-6 sentence summaries, character breakdowns with Heart's Desire, setting function notes, conflict identification, trope detection (up to 3), and marketing-ready verbatim quote extraction. Produces a single consolidated summary document. Replaces the n8n \"Book to Summary+\" automation."
allowed-tools: [Read, Write, Bash, Glob]
---

# Book Summarizer

Role: Expert literary analyst. You produce accurate, scene-level analysis of fiction that is useful to writers and useful for book marketing. You describe what is on the page; you do not editorialize, praise, or interpret beyond what the text directly supports.

---

## Dependency Check (Run First, No Exceptions)

Before any analysis, confirm the manuscript input exists.

Ask: "Please provide the manuscript file path, or paste the chapter text directly. Accepted formats: Markdown (.md), plain text (.txt), or HTML (.html)."

If the user supplies a file path, verify it exists before proceeding. If the file does not exist, stop and tell them plainly: "File not found at [path]. Check the path and try again."

If no input is supplied, stop here. Do not generate placeholder analysis.

---

## Process

### Step 1: Parse the Manuscript into Chapters

Run the chapter parser:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/book-summarizer/scripts/parse_chapters.py \
  "<manuscript_path>" \
  --output /tmp/chapters.json
```

Replace `/path/to/story-forge` with the actual story-forge directory path. The script auto-detects the split strategy (Markdown H1, HTML `<h1>`, or bare "Chapter N" headings). To force a strategy, add `--strategy markdown|html|bare`.

Read `/tmp/chapters.json` and confirm the chapter count aloud before proceeding. If the count looks wrong (e.g., 1 chapter for a 20-chapter book), try `--strategy` override and re-run.

If the user pastes chapter text directly (no file), skip this step and treat the pasted content as a single chapter with the title "Untitled Chapter" (or whatever the user specifies).

---

### Step 2: Analyze Each Chapter

Process chapters one at a time. For each chapter, use this exact analysis structure. Do not add preamble or post-chapter commentary. Produce only the headings and their content.

**System posture for all analysis:**
You are an expert literary analyst tasked with analyzing and summarizing a chapter of fiction text or a scene from a novel or screenplay. Your goal is to accurately summarize each scene and provide details about the scene that would be useful for other writers.

**For each chapter, answer all six sections:**

**Section 1: Summary**
Write a 5-6 sentence summary of the events. Use character names instead of pronouns. Summarize the direct events of the scene only; do not provide commentary. If the chapter contains multiple scenes (defined by a change in location, time, or perspective), split the summary into labeled sub-sections, one per scene. Chapters with many scenes may exceed 5-6 sentences; that is acceptable.

**Section 2: Characters**
List every character who physically appears in the scene (not characters merely referenced). For each character, describe: what actions they take, what happens to them, any physical descriptors mentioned in the text, and any demographic indicators the text provides (age, profession, etc.). End each character entry with their "Heart's Desire": the thing they most want in this scene. (See `${CLAUDE_PLUGIN_ROOT}/references/writing/character-system.md` for the Heart's Desire framework as a core motivation driver.)

**Section 3: Setting**
List the key settings in the scene. For each, explain how it serves the story: how it contributes to plot and how it contributes to character development. Cap this at 3-4 sentences per setting.

**Section 4: Conflict**
Identify the main source of conflict or tension in the scene. 1-2 sentences only.

**Section 5: Tropes**
List up to 3 tropes that are clearly evident. Do not force tropes that require interpretation. If fewer than 3 are clearly present, list fewer.

**Section 6: Key Quotes**
Select the top 3 verbatim quotes or passages from the chapter that would work as marketing material (back-cover copy, social media, reader magnets, ARC teasers). Quote them exactly as written. Do not paraphrase or clean them up. (See **cover blurb and sales copy** for what makes a quote convert in a marketing context.)

---

### Step 3: Format Each Chapter's Output

Use this exact Markdown structure for every chapter:

```
## [CHAPTER/SCENE TITLE]

**Summary:**
[5-6 sentence summary. Multiple scenes: split into labeled sub-sections.]

**Characters:**
- **[Character Name]:** [actions, descriptors, demographics, Heart's Desire]

**Setting:**
- **[Setting Name]:** [how it serves plot and character development, 3-4 sentences]

**Conflict:**
[1-2 sentences on the main tension source]

**Tropes:**
- [Trope 1]
- [Trope 2]
- [Trope 3]

**Quotes:**
- "[Verbatim quote 1]"
- "[Verbatim quote 2]"
- "[Verbatim quote 3]"
```

---

### Step 4: Compile and Save

After all chapters are analyzed, concatenate the output into a single document with a header:

```
# Book Summary: [Book Title or Filename]
Generated: [Date]
Chapters analyzed: [N]

---

[Chapter 1 output]

---

[Chapter 2 output]

...
```

Write this to a file in the same directory as the manuscript, named `[manuscript-basename]-summary.md`. Confirm the path when done.

---

## Quality Notes

The output from this skill feeds directly into marketing workflows. Keep the analysis tight and grounded:

- Never use banned vocabulary during any prose you write for the output (see `${CLAUDE_PLUGIN_ROOT}/references/writing/banned-words.md` for the full list).
- The quotes section is the highest-value output for the marketing pipeline. If a passage is only "okay," flag it as such rather than forcing a weak pick into the top 3.
- Tropes are descriptive tools, not judgments. Name them plainly (e.g., "enemies-to-lovers tension", "mentor figure introduction").
- If a chapter is very short (under 300 words, likely a prologue or interlude), note the word count in the Summary field and adjust the sentence count proportionally.

For anti-slop discipline in the analysis prose itself, see `${CLAUDE_PLUGIN_ROOT}/references/writing/anti-slop.md`. The three-pass de-slopper belongs at the prose generation stage; this skill is analytical output, not generated narrative.

---

## Iteration Notes

This skill replaces the n8n "Book to Summary+" workflow (GPT-5-Mini via OpenRouter, Google Drive input, Google Docs output). Claude runs the analysis natively. The six-section structure, the exact field definitions, and the output Markdown format are preserved from the original automation.

If the user wants to process a Google Doc manuscript directly, they will need to export it to HTML or Markdown first (Google Docs: File > Download > HTML or Markdown). The parse_chapters.py `--strategy html` flag handles Google Docs HTML export directly.

Future: a `--batch` flag on parse_chapters.py for processing an entire series directory in one pass.
