---
title: "Worldbuilding Method (Jason Hamilton / Story Hacker)"
type: concept
tags: [writing, ai-writing, n8n, automation, worldbuilding, story-hacker]
created: 2026-06-27
updated: 2026-06-27
source: "https://www.youtube.com/watch?v=s-abfMWOWY8 (worldbuilding automation), https://www.youtube.com/watch?v=y2yam3wlTjE (simple version), https://www.youtube.com/watch?v=obVNsO5XptA (worldbuilding selector in chapter pipeline)"
status: living
---

# Worldbuilding Method (Jason Hamilton / Story Hacker)

Automation 3 in Jason's five-automation chain. It takes the story dossier produced by Automation 1 and produces a fully fleshed worldbuilding sheet — one detailed profile per worldbuilding element, organized by category. The worldbuilding sheet feeds into the `${CLAUDE_PLUGIN_ROOT}/references/writing/outlining-method.md` (Automation 4) and, via the Worldbuilding Selector, into every chapter of the `${CLAUDE_PLUGIN_ROOT}/references/writing/chapter-generation-pipeline.md`.

Worldbuilding is not just for fantasy or sci-fi. Every genre has worldbuilding elements: the layout of a house used in multiple scenes, a workplace, a city neighborhood, the political structure of an organization. Even a contemporary thriller has locations and objects that benefit from this treatment.

See also: `${CLAUDE_PLUGIN_ROOT}/references/writing/chapter-generation-pipeline.md`, `${CLAUDE_PLUGIN_ROOT}/references/writing/outlining-method.md`, **story hacker prompts**, **magic systems sanderson laws**, `${CLAUDE_PLUGIN_ROOT}/references/writing/worldbuilding-consistency.md`

**On-page delivery note:** The worldbuilding sheet this automation produces is reference material for the writer. How it surfaces in prose — without stopping the story — is governed by **exposition and infodumps** (incluing, iceberg model, MRU anchoring) and **setting and place** (the physical-description layer specifically).

---

## What the Worldbuilding Automation Does

It loops through the list of worldbuilding elements identified in the story dossier and generates a detailed profile for each one. For each element, three steps run in sequence: Expand, Logic Check, Rewrite. The expanded profile is appended to the worldbuilding document after the rewrite, then the loop advances to the next element.

---

## Inputs

- **Story dossier** (from Automation 1) — contains the initial list of worldbuilding elements (1 sentence each) that the automation will flesh out
- **Worldbuilding template** — from the Story Hacker genre guide for this book's genre. Full template included (not condensed — this is the central reference for this automation)
- **Genre tropes template** — condensed to a bulleted list to save tokens
- **Themes template** — included as a passive reference for thematic resonance checks
- **Author notes** — optional field presented at workflow launch. Can be left blank
- **Blank worldbuilding document** — the Google Doc (or equivalent) where all expanded profiles will be written

**Template note:** Templates are built from analysis of actual bestsellers in the genre. The worldbuilding template contains a profile format and category expectations specific to that genre. Using genre templates is what separates this system from asking a chatbot to "write worldbuilding for my story" — the templates encode reader expectations for the genre.

---

## Pre-Loop: Parse Worldbuilding Elements

**What it does:** Reads the dossier and extracts a JSON array of all worldbuilding element names.

**Prompt (exact):** "You are a parser given the above book outline text, return a JSON array named `worldbuilding` containing each world building element listed in the dossier above. Do not divide the elements into categories, and make sure all worldbuilding elements are accounted for, and don't add any new worldbuilding elements. Only output valid JSON."

**Output:** A flat list of element names — no categories, no descriptions, just the names to loop over.

**Why flat and nameless:** The category assignment and profiling happen per-element in the loop. Forcing category assignment at this stage would add complexity and introduce errors before the expansion work begins.

The list is then parsed by a vibe-coded code node (JavaScript) that splits the JSON array into individual items the n8n loop can iterate over.

---

## Per-Element Loop: Step 1 — Expand World-Building Element

**What it does:** Generates the full profile for one worldbuilding element.

**Context passed (in order — context before instructions per Anthropic's prompt engineering recommendation):**
1. Condensed genre tropes (bulleted list)
2. Full worldbuilding template
3. Full themes template
4. Full story dossier
5. Author notes (if any)

**Prompt logic:**

"Given the above brain dump information, genre tropes, worldbuilding template, themes template, and story dossier, I want you to create a fleshed out world building sheet for this specific world building element: [current element name]."

Then:
1. **Determine the category** — assign the element to one of the 12 categories below
2. **Apply the category-specific instructions** — each category has its own profile format

**The 12 categories:**

| Category | What it covers |
|---|---|
| High-Level Worldbuilding | The foundational rules of how this world works |
| Settings and Locations | Physical spaces where scenes take place |
| Objects and Artifacts | Items with narrative significance |
| Magic Systems and Technology | How magic or advanced tech works in this world |
| Groups and Races | Factions, species, organizations, institutions |
| Gods and Deities | Divine or supernatural entities |
| Geography and Nature | Landscape, climate, ecology |
| Population and Politics | Social structures, governance, power dynamics |
| Culture | Customs, art, food, daily life |
| History and Lore | Backstory and mythology |
| Religion and Beliefs | Spiritual systems and how they shape behavior |
| Languages | Communication systems, dialects, scripts |

Not all categories apply to every genre. A contemporary thriller has no Magic Systems and probably no Gods and Deities. The automation selects only the applicable category.

---

## Category-Specific Profile Format: Settings and Locations (Example)

The most common category across all genres. Profile structure:

**Header:** `# Setting and Location: [Name]`

**Tagline:** A single italicized sentence immediately below the header — one evocative line capturing the essence of the place. ("A city that climbs towards sunlight it will never share equally.")

**Then these H2 sections, written in 1-2 sentences of prose each (no bullet points except under "Secrets and Hidden Layers"):**
- Physical Description and Layout
- Atmosphere and Emotional Tone
- Who Lives Here or Who Passes Through
- Purpose and Function in the World
- Purpose and Function in the Story
- Secrets and Hidden Layers (short bulleted list)
- History and How It Has Changed
- Connections to Other Locations

**Key instruction on setting:** "Make it feel lived in and three-dimensional, not like a stage backdrop. Cover its physical reality and layout, emotional resonance, the people who inhabit it, its secrets, and its larger role in the story."

All other categories have equivalent structured profiles tailored to their type.

---

## Per-Element Loop: Step 2 — Logic Check

**What it does:** Audits the newly expanded element against the full context for consistency.

**Input:** Expanded element profile (from Step 1), plus:
- Story dossier
- Worldbuilding elements already generated (all previous loop iterations — the doc is being built incrementally)
- Author notes
- Full worldbuilding template

**Checks it runs:**
- Consistent with the dossier?
- Consistent with worldbuilding elements already established (no internal contradictions)?
- Consistent with author notes?
- Fits the worldbuilding template for this genre?
- Good internal logic and plausibility — does cause and effect hold?
- Thematic resonance — does it reinforce the story's themes?

**Output:** A list of flagged issues plus an improvement plan.

---

## Per-Element Loop: Step 3 — Rewrite

**What it does:** Implements the improvement plan from the Logic Check. Not a full rewrite — targeted changes only.

**Prompt logic:** "Here is the original world building element and here is the improvement plan. Implement the changes listed in the improvement plan. Rather than do a full rewrite, just implement the changes." The word "implement" is intentional. "Rewrite" triggers the model to start from scratch and lose the quality of the original.

**Output:** Final polished profile for this element. Appended to the worldbuilding document. Loop advances to next element.

---

## How the Worldbuilding Sheet Feeds Into Chapters

In the `${CLAUDE_PLUGIN_ROOT}/references/writing/chapter-generation-pipeline.md`, Step 3 is the **Worldbuilding Selector**. For each chapter, it reads the full worldbuilding sheet and selects only the elements relevant to that specific chapter, outputting verbatim excerpts. Step 7 is the **Worldbuilding Scene Brief**, which takes the selected elements and removes any future-leaning details — ensuring the prose is not accidentally foreshadowed by worldbuilding info about events that have not yet happened in the story.

The worldbuilding sheet is never passed in full to the First Draft step. The Selector → Brief chain condenses it to exactly what the chapter needs.

---

## Worldbuilding in the Simple (No-Automation) Version

In the Claude Projects workflow (source: y2yam3wlTjE), the worldbuilding step runs manually:

1. Create a "Novel World Building" Claude Project
2. Set the Instructions to the Worldbuilding Project Prompt from **story hacker prompts**
3. Paste in the story dossier and submit
4. The project generates the full worldbuilding sheet in one pass (no per-element loop)
5. Copy the output into a document; review and edit before proceeding

The simple version produces a shallower sheet (no per-element logic checks, no category-specific profile formats) but requires zero technical setup. Quality gap is significant for books with complex worldbuilding; for a contemporary novel with simple settings, the simple version is usually sufficient.

---

## Practical Notes

- **Worldbuilding scope creep is a real risk.** The automation will flesh out every element in the dossier. If the dossier over-identifies worldbuilding elements (listing 40 things when the story only needs 15), the automation generates profiles for all 40 and most are wasted context in later steps. Trim the dossier before running this automation.
- **For genres with minimal worldbuilding** (contemporary fiction, thrillers), most elements will fall into Settings/Locations and Objects/Artifacts. The automation handles this correctly — "not all stories will have all of these categories" is baked into the prompt.
- **Reuse the worldbuilding sheet across a series.** Once generated for book 1, the sheet carries forward. Only new elements introduced in subsequent books need to be added.
- **Context first, instructions last** — Jason explicitly credits this to Anthropic's prompt engineering guidance. All context (tropes, templates, dossier) is injected before the task instructions in every prompt in this automation.
