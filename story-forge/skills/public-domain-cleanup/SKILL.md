---
name: public-domain-cleanup
description: Use when you have a raw public-domain source text (plain text or Markdown, possibly OCR-scanned or typeset in archaic English) and need to modernize its spelling, fix OCR errors, and clean up punctuation in ~1000-word passes WITHOUT changing vocabulary or meaning. Produces a clean Markdown file ready for the story-forge pipeline.
allowed-tools: [Read, Write, Edit, Bash]
---

# Role

Source prep specialist. You take a raw public-domain text (full of archaic spellings, OCR artifacts, Victorian footnotes, or inconsistent punctuation) and produce a clean, readable Markdown document. No new words. No paraphrasing. Spelling and punctuation only. The vocabulary stays exactly as the author wrote it.

---

## Dependency Check

This is a standalone entry skill. It requires exactly one input.

**Before doing anything else**, check whether the user has provided a source text file path.

If no source file was provided, stop and say:

> This skill needs a public-domain source text file. Provide the file path (plain text or Markdown) and re-run the skill.

Do NOT proceed without it. Once a path is confirmed, verify the file exists with Read before continuing.

---

## Process

### Step 1. Confirm target spelling convention

Ask (or infer from context): is the target modern American English or British English? Default to American if not specified. Record the choice -- it governs Step 3, criterion 1.

### Step 2. Chunk the source

Run the bundled chunker to split the source into ~1000-word segments, always breaking on paragraph boundaries:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/public-domain-cleanup/scripts/chunk.py split <source_file> --words 1000 --output-dir ./pd-chunks/
```

Note the chunk count. Confirm no chunk is empty before continuing.

### Step 3. Clean each chunk

Read each chunk file in order. Apply the cleanup pass to its contents. Write the cleaned output to `./pd-chunks-cleaned/chunk_NNN.md`.

Apply these criteria exactly, in this priority order:

**1. Spelling modernization (spelling only, not vocabulary).**
Change archaic or non-standard spellings to modern equivalents for the chosen English variant. The word itself must not change. "Colour" becomes "color" (American); "hath" stays "hath" (that is the word). If unsure whether a form is archaic spelling or a deliberate word choice, err toward keeping the original.

**2. Remove footnotes and footnote references.**
Delete inline footnote markers (superscripts, asterisks, daggers, numbered references) and any footnote or endnote blocks. Do not integrate footnote content into the running text.

**3. Grammar and punctuation per modern Chicago Manual of Style.**
Adjust punctuation to conform to modern CMOS (serial comma, quotation mark placement, em dash usage, etc.). Do NOT change sentence structure, word order, or meaning. If a grammatical pattern is ambiguous between "original style" and "CMOS correction," keep the original style.

**4. Poetry: preserve structure exactly.**
When the chunk contains verse, preserve the original line breaks and stanza boundaries. Never collapse verse lines into prose. Maintain the same blank-line spacing between stanzas as the source.

**5. Preserve original capitalization.**
Do not normalize mid-sentence capitalization or title case. If the author capitalized "Nature" or "Virtue" mid-sentence, keep it.

**6. Fix OCR errors.**
Identify and correct OCR artifacts: misread characters (rn misread as m, fi ligatures broken into f1, etc.), broken words, stray punctuation from page margins. After correction, apply spelling modernization and punctuation rules to the corrected text.

**7. Format chapter and section headers as H1 Markdown.**
Any title that functions as a chapter or section divider (Chapter I, Canto III, Prologue, Epilogue, Preface, Part One, Book II, etc.) goes on its own line as a Markdown H1:

```
# Chapter I
# Canto III
# Prologue
# Part One
```

**8. Output format.**
Return clean Markdown text only. No commentary, no "cleaned version:" labels, no diff annotations.

### Step 4. Reassemble

After all chunks are cleaned, stitch them back:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/public-domain-cleanup/scripts/chunk.py reassemble ./pd-chunks-cleaned/ --output <source_name>-cleaned.md
```

### Step 5. Final spot-check

Read three locations: the beginning, a chapter/section boundary, and the end. Confirm:

- No footnote markers remain.
- All chapter/section titles are formatted as `# Header`.
- No visible OCR artifacts (stray characters, broken words).
- No vocabulary substitutions (the words match the original; only spellings changed).

Deliver the absolute path to the final output file.

---

## Helper Script

`scripts/chunk.py` handles all chunking and reassembly. It splits on paragraph boundaries and never cuts mid-sentence. Default target is 1000 words (matching the original automation). Adjust with `--words N`. Use the `reassemble` subcommand to stitch cleaned chunks back together.

This chunker is adapted from the same pattern used by the de-sloppifier skill. The 1000-word default here matches the source n8n automation.

Run `python3 "${CLAUDE_PLUGIN_ROOT}"/skills/public-domain-cleanup/scripts/chunk.py --help` for full usage.

---

## Connection to the Pipeline

The cleaned output is plain Markdown source, ready to feed downstream story-forge skills. If the text is being adapted rather than reproduced verbatim, the next step is typically voice work: see the `${CLAUDE_PLUGIN_ROOT}/references/writing/voice-matching.md` note in the writing wiki. If AI-generated prose based on this source enters the pipeline later, see `${CLAUDE_PLUGIN_ROOT}/references/writing/anti-slop.md` for the cleanup pass that applies to generated content (a different problem from what this skill solves).

---

## Iteration Notes

- Criteria sourced from the n8n "Public Domain (Cleaned-up Version)" automation, migrated to Claude Code June 2026.
- British vs. American English: confirm before every run. The original automation assumed American English as default.
- Footnote formats vary (numbered, asterisked, endnote blocks, sidenotes). Use judgment on edge cases and log unusual patterns below.
- OCR quality varies widely. Heavily degraded scans may need a manual pre-pass before this skill can do reliable work.
- Verse and drama have irregular line structures. When in doubt on poetry formatting, preserve the source layout exactly.
