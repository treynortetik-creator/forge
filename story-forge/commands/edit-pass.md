---
name: edit-pass
description: "Run the full editing chain on a draft: 3-pass de-sloppifier then logic-check continuity audit."
argument-hint: <chapter-or-manuscript-file>
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep]
---

# edit-pass

Run the full editing chain on a draft file. Two skills run in sequence: de-sloppifier (3-pass line edit), then logic-check (continuity and chronology audit). Each step hands its output to the next. If a required artifact is missing at any step, the chain stops and tells you what to build first.

**Input:** `$ARGUMENTS` (path to a chapter or manuscript file)

---

## Step 0: Validate Input

Confirm `$ARGUMENTS` points to a readable file. If the path is missing or unreadable, stop and say: "Provide a path to the chapter or manuscript file you want to edit."

---

## Step 1: Dependency Check

Before running either skill, check for the story bible. The logic-check skill requires it. Run:

```bash
ls *.md story-bible/ 2>/dev/null   # dossier, character sheet, worldbuilding sheet, outline
```

Look in the PROJECT directory for the story bible that `dossier-to-outline` writes there: dossier, character sheet, worldbuilding sheet, and outline. It is not stored inside the plugin. If no story bible exists, note it now. Do not stop the chain yet. The de-sloppifier runs without it. You will stop at Step 3 instead if it is still missing.

---

## Step 1.5: Author-Diff Taste Extraction (Conditional)

Before any machine editing, ask: does the author have hand-edited passages of this manuscript (a marked-up file, a partial pass, tracked changes)? If yes:

1. Diff the author's version against the base text.
2. Reverse-engineer the taste: classify every edit into moves (what gets cut, what gets swapped, what gets added back), note what the author leaves alone, and write the result down as a short doctrine block before proceeding.
3. The extracted doctrine OVERRIDES the skills' default rules wherever they conflict. The author's hand is the ground truth for this manuscript; the pipeline's job is to apply that taste at scale, not its own.

If no author hand-edits exist, skip this step and proceed with the skills' defaults (which already encode the 13 author-pass edit moves; see the de-sloppifier skill).

---

## Step 2: Run the de-sloppifier skill

Run the de-sloppifier skill on `$ARGUMENTS`.

**Sweep discipline (census, judge, apply).** Any banned-word, banned-family, or repetition sweep inside this step runs in three separate stages: census (flag every instance mechanically, no judgment), judge (rule each hit in its voice context; load-bearing hits survive), apply (implement only the judged edits). Before any vague-word or hedge sweep, tag the PROTECTED class first: deliberate withholds and reveal machinery (a narrator refusing to name a thing the book has not revealed yet is design, not slop). Never run a blind find-and-replace.

The skill uses `${CLAUDE_PLUGIN_ROOT}/skills/de-sloppifier/scripts/chunk.py` to split the file into chunks of roughly 1500 words on paragraph boundaries, runs all three passes on each chunk in order (Pass 1: pacing and paragraph structure; Pass 2: line editing; Pass 3: slop removal), then reassembles the output. Follow the skill's own chunking instructions exactly.

The output file from this step is the input to Step 3. Write it to a clearly named path, for example: `<original-stem>-deslopped.md` alongside the source file. Confirm the path before continuing.

---

## Step 3: Dependency Check for logic-check

Check again whether the story bible is present (dossier, character sheet, worldbuilding sheet, and outline produced by `dossier-to-outline`).

If it is still missing, stop the chain here and say:

> "De-sloppifier complete. Logic-check requires the story bible (dossier, character sheet, worldbuilding, and outline). Build it first by running the `dossier-to-outline` skill, then re-run `edit-pass` or run `logic-check` directly on the deslopped file at `<output path>`."

Do not proceed to Step 4 without the story bible.

---

## Step 4: Run the logic-check skill

Run the logic-check skill on the deslopped file from Step 2, passing the story bible as the reference document.

The skill runs the Full Six-Category Audit (premise logic, character-world fit, worldbuilding coherence, plot setup plausibility, convenience flags, and specific fixes). If the input is a scene brief or chapter draft, it also runs the Chapter Chronology Layer.

Follow the logic-check skill's own dependency check at the top of that skill. If it surfaces any additional missing prereqs beyond the story bible, stop and report them.

---

## Step 4.4: Semantic-Damage Check

Before the repeat scan, prove the wave did not delete anything load-bearing:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}"/skills/de-sloppifier/scripts/edit_diff.py <original> <deslopped>
```

🔴 **Any DELETION finding stops the chain.** A missing citation, quote, cross-reference or number is
not a style outcome — restore it and re-run. MEANING findings (flipped negation, dropped hedge,
widened quantifier) need a human decision each; they are often legitimate tightening, and sometimes a
reversal of what the author actually claimed.

## Step 4.5: Post-Wave Repeat Scan

Edit waves introduce repeats, especially when chunks or chapters were edited in parallel: independent editors converge on the same replacement phrasing. After all edits are applied:

1. Scan the edited text for repeated distinctive phrases (shared n-grams of 4+ words across chunks/chapters; a diff against the pre-edit text isolates what the wave ADDED).
2. Triage the hits: ritual refrains and deliberate echoes are design; identical fresh phrasing appearing in two or more places the wave touched is a defect.
3. Fix the defects and re-scan. Target: the wave introduces zero new repeats.

Do not skip this on multi-chunk runs. A clean per-chunk edit can still produce a dirty book.

---

## Step 5: Present results

After both skills complete, present:

1. The path to the deslopped output file.
2. The logic-check audit report inline.
3. A brief summary of the most critical findings from each step (three to five bullets total).

If either skill surfaced issues that require another editing cycle before the draft is usable, say so plainly. Do not bury it.

---

## Notes for the orchestration layer

- This command is the orchestration layer only. The real prompts live in the individual skills. Do not reproduce or paraphrase the skill instructions here; invoke the skills by name and follow them.
- Preserve all filenames and Markdown formatting across steps. Do not rename files beyond the `-deslopped` convention above.
- If the input file is a full manuscript (multiple chapters), chunk and process each chapter independently through the de-sloppifier before passing the full reassembled output to logic-check.
- Em dashes are banned. The de-sloppifier removes them in Pass 3. If any survive into the final output, flag them in the summary.
