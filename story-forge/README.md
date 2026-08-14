# story-forge

A long-form fiction pipeline, built as a Claude Code plugin.

It is the same system documented in the writing wiki ([[chapter-generation-pipeline]], [[anti-slop]], [[story-hacker-prompts]], [[voice-matching]]) and recovered from the n8n book-automation exports (`references/writing/book-automation-workflows.md`, cataloged in `${CLAUDE_PLUGIN_ROOT}/references/writing/book-automation-workflows.md`). The n8n version orchestrated LLM calls externally. This version runs natively in Claude Code, where the agent **is** the orchestrator, so it is smarter, can read the craft wiki while it works, and does not need n8n.

## Architecture

- **Skills** (`skills/<name>/SKILL.md`) are the LEGO bricks. Each is one focused craft transform: persona + rules + the actual prompts pulled from the n8n workflow, plus iteration notes. Some bundle a small **python helper** for the deterministic glue (chunking a draft into ~1500-word windows, wordcount estimation, chronology diffing, file assembly). Python is the glue; Claude is the brain.
- **Commands** (`commands/<name>.md`) are the chains: a named workflow that invokes a sequence of skills with artifacts passed between them (e.g. the full braindump -> dossier -> outline -> chapters pipeline).
- **The plugin** is the box: install once, get the whole pipeline.

## Skills (planned set, from the 10 recovered workflows)

| Skill | From workflow | Stage |
|---|---|---|
| **de-sloppifier** ✅ (proof) | Line Editor and De-sloppifier | post-draft editing (3 passes) |
| story-hacker | Book/Script Story Hacking | analyze a comp title into a reusable plot template |
| braindump-to-dossier | Braindump to Dossier | pre-writing concept (novel) |
| dossier-to-outline | Dossier to Full Outline | outlining (novel) |
| outline-generator | Advanced Outline Generator | advanced outlining (emotional audit + sliders) |
| outline-to-chapters | Advanced Outline to Chapters | drafting (selectors, slider briefs, chronology checks) |
| logic-check | (chronology/logic nodes) | continuity audit |
| book-summarizer | Book to Summary+ | summaries + marketing quotes |
| public-domain-cleanup | Public Domain (Cleaned-up) | source prep |
| short-story-hacker | Short Story Hack | short-fiction structural breakdown |
| **short-story-dossier** ✅ | Short-Story Dossier | pre-writing concept (short fiction): effect, change, heart's desire, magic sword, cast |
| **short-story-outline** ✅ | Short-Story Outline | scene-based outline (short fiction): 8-Point Plot mapped to 5-8 scenes, opening/ending specs |
| **short-story-draft** ✅ | Short-Story Draft | scene-by-scene prose draft (short fiction): enter-late, crowd-and-leap, register lock |

## Workflows (planned commands)

- `/story-forge:full-book` — braindump-to-dossier → dossier-to-outline → outline-to-chapters, artifacts on disk between steps.
- `/story-forge:short-story`: short-story-dossier, short-story-outline, short-story-draft, de-sloppifier, logic-check. Produces one complete 5,000 to 7,000 word story. Voice step is optional (novel pipeline requires it; short story does not).
- `/story-forge:edit-pass` — the 3-pass de-sloppifier across a chapter or manuscript.
- `/story-forge:hack` — story-hacker on a comp title to extract a reusable structure.

## Status

v0.2.0. **de-sloppifier** was the first skill, built as the pattern proof. The short-story track (short-story-dossier, short-story-outline, short-story-draft, and the /short-story command) is now live. The remaining novel-pipeline skills continue to fill in from the same pattern.

## Notes

- Naming is a placeholder; rename the plugin if you want.
- The n8n exports it descends from carry credential references only (no secrets); safe to version.
