---
title: "Outlining Method (Jason Hamilton / Story Hacker)"
type: concept
tags: [writing, ai-writing, n8n, automation, outlining, story-bible, story-hacker]
created: 2026-06-27
updated: 2026-06-27
source: "https://www.youtube.com/watch?v=SHryZh7CcQs (outline automation), https://www.youtube.com/watch?v=_TgfGquyuLY (advanced outline), https://www.youtube.com/watch?v=y2yam3wlTjE (simple version), https://www.youtube.com/watch?v=BDPfyuVuHfk (system overview)"
status: living
---

# Outlining Method (Jason Hamilton / Story Hacker)

The pre-writing system Jason builds before running the `${CLAUDE_PLUGIN_ROOT}/references/writing/chapter-generation-pipeline.md`. The outline — and the story bible it depends on — is the primary input for "Find Chapters" and everything downstream. Garbage outline → garbage chapters. 

The outline itself is the output of automation 4 in a five-automation chain. It depends on three prior automations: Brain Dump to Story Dossier, Dossier to Characters, and Dossier to Worldbuilding (see `${CLAUDE_PLUGIN_ROOT}/references/writing/worldbuilding-method.md`).

See also: `${CLAUDE_PLUGIN_ROOT}/references/writing/chapter-generation-pipeline.md`, `${CLAUDE_PLUGIN_ROOT}/references/writing/worldbuilding-method.md`, **story hacker prompts**, **genre conventions and promises**

---

## The Five-Automation Chain (Big Picture)

1. **Brain Dump → Story Dossier** — takes everything the author knows about the book, identifies pitches, picks the best one, runs emotional + name checks, produces a story dossier (a checklist of all elements needed)
2. **Dossier → Characters** — loops through every character in the dossier and fully fleshes each one out
3. **Dossier → Worldbuilding** — loops through every worldbuilding element and fleshes each out (see `${CLAUDE_PLUGIN_ROOT}/references/writing/worldbuilding-method.md`)
4. **All docs → Outline** — takes the dossier, character sheet, worldbuilding sheet, plus genre templates, and generates the full chapter-by-chapter outline with sliders
5. **Outline + docs → Chapters** — the `${CLAUDE_PLUGIN_ROOT}/references/writing/chapter-generation-pipeline.md`

Automation 4 (the outline) is what this note covers. Automations 1-3 produce the inputs it needs.

---

## Automation 1: Brain Dump → Story Dossier

**Purpose:** Turn any raw idea (or nothing) into a structured list of everything the book needs before real development begins.

**Input:** Author's brain dump — anything already known about the book. Optional. Can be blank.

**Also inputs (templates):** Genre tropes doc, plot template, character template, worldbuilding template, themes doc. These are Jason's Story Hacker genre guides — one per genre. Templates drive quality. Without them, the automation produces generic results.

**The brainstorming pitch cycle:**
1. Identify the subgenre from the loaded templates (cheap model — just classification)
2. Brainstorm five story pitches using the hook rubric, the genre tropes, the plot template, and the author's brain dump
3. Pick the best pitch (medium-to-powerful model — pick accuracy is ~80% consistent across models)
4. Strip the picked pitch down to clean text only (cheap model — just extraction)

**Dossier creation:**
- Takes the winning pitch + all templates + brain dump
- Creates a story dossier: log line, synopsis, character list (names + roles, 1-2 sentences each), worldbuilding elements (1 sentence each), key outline moments (opening image, inciting incident, midpoint, climax, closing image)
- This is NOT the fleshed-out story bible yet — it is a "call sheet," a master list of everything that needs to be developed

**Checks run on the dossier (before finalization):**

1. **Emotional Check:** "Analyze this dossier for theme cohesion and emotional payoff quality. Identify the primary and secondary themes, then list any major moment where the theme should show up but currently doesn't or feels weak." Produces an improvement plan.

2. **Character Name Check:** Runs the dossier against a list of AI-common names to avoid (Marcus, Sarah, Chen, Elara, Lyra, Nora, Aara, Vesper, Blackwood, etc. — see `${CLAUDE_PLUGIN_ROOT}/references/writing/banned-words.md`). Proposes three alternatives for any flagged name; each alternative must fit character culture/setting/social status, be memorable but not melodramatic, and not appear on the banned list. Explicitly exempts names the author provided in the brain dump.

3. **Dossier Rewrite 1:** Implements both the emotional check and name check suggestions. Cheap model — it is implementing a plan, not inventing.

4. **Logic Check:** Checks for logical inconsistencies, implausible motivations, character/world mismatches, "because the plot needs it" elements with no in-world logic, and spoiler-level reveals that should not be in the early outline. Medium-to-advanced model needed — this is reasoning-intensive.

5. **Dossier Rewrite 2:** Implements the logic check suggestions. Outputs the final story dossier to the document.

---

## Automation 2: Dossier → Characters

**Purpose:** Fully flesh out every character in the dossier.

**How it works:** A loop. The automation parses the dossier for character names, then runs a three-step sequence on each character:
1. **Expand** — generates the full character profile
2. **Logic Check** — checks the new profile against the dossier, the plot template, and any already-generated characters for consistency
3. **Rewrite** — implements logic check suggestions

**Character profile contents (major characters):**
- Physical description
- Role in story (protagonist, antagonist, love interest, etc.)
- Myers-Briggs profile, Enneagram, Clifton Strengths
- Core motivation (heart's desire driving them most of the time)
- Background before the story begins
- A quirk, hobby, or trait that makes them three-dimensional and doesn't fit neatly into the plot
- Dialogue style
- **Slider baselines** — 15 sliders rated on a −10 to +10 scale: Stress/Calm, Fear/Courage, Suspicion/Trust, Callous/Empathic, Impulsivity/Self-Control, Dominance/Submission, Pessimism/Optimism, Introverted/Extroverted, Gut/Logic, Detail-Focused/Big-Picture, Cautious/Risk-Taker, Seriousness/Humor, Deception/Honesty, Stability/Sensitivity, Shame/Self-Worth. These baselines shift per scene in the Character Scene Brief step of the `${CLAUDE_PLUGIN_ROOT}/references/writing/chapter-generation-pipeline.md`.
- **Character arc** — how they begin, how they change by the end, what pushes them into the plot, their midpoint moment, their climax moment

After all individual profiles are generated, the automation establishes relationship dynamics between all characters.

**Minor characters:** 2-3 sentences only — background, core desire, relationship to the plot.

---

## Automation 4: All Docs → Outline

**Purpose:** Produce the full chapter-by-chapter outline that "Find Chapters" in the `${CLAUDE_PLUGIN_ROOT}/references/writing/chapter-generation-pipeline.md` will parse. This is what the chapter loop reads from.

### Inputs

- Story dossier (from automation 1)
- Character sheet (from automation 2)
- Worldbuilding sheet (from automation 3, see `${CLAUDE_PLUGIN_ROOT}/references/writing/worldbuilding-method.md`)
- Genre tropes template (condensed to a bulleted list to save tokens — the full tropes doc can be 7,000+ words)
- Themes template (not condensed — shorter doc, and themes need to stay present throughout)
- **Plot template** — the most important input. A chapter-by-chapter structural template built from analysis of actual bestsellers in the genre. Each chapter in the template specifies: primary narrative purpose, structural beats, scene intensity (1-10), spice level (1-10), violence level (1-10), swearing level (1-10). Jason has 30+ genre-specific plot templates. A 40-chapter general template ("Plot Module") exists for non-romance genres.

### Step 1: Write the Initial Outline

**Prompt logic:** "Using the above worldbuilding, characters, dossier, plot template, themes, and tropes, generate a simple outline for this book. Make sure to use the plot template to inform you of the kind of things that should happen in the chapters you are outlining. The summary for each chapter should be only two to three sentences per chapter. The goal is not to flesh out every detail, but to get a general blueprint for the story as a whole. The outline should have the same number of chapters found in the plot template."

Per chapter, the outline includes:
- 2-3 sentence summary (specific details, not vague allusions — written as if handing it to a ghostwriter)
- Viewpoint character (just the name — no tense or POV type, that comes later)
- Spice, violence, and swearing levels from the plot template (must match the template exactly)

**Reason for starting short (2-3 sentences):** At the outline stage, the author needs to approve the overall shape of the story before locking in details. Longer chapter descriptions overwhelm the review and introduce specifics that conflict with the author's vision. Flesh out in the "Find Chapters" step later.

### Step 2: Emotional Check

**Prompt logic:** Reads the outline as a whole. "Is there enough emotion here? Are there genuine gut punches? Or is this a string of events?" Produces a list of recommended changes.

### Step 3: Outline Rewrite (Emotional)

Implements the emotional check suggestions. Cheap model task — implementing a plan.

### Step 4: Add Sliders (Per Chapter)

**What sliders are:** Scene-level narrative controls that determine the intensity of specific qualities in each chapter. They are separate from character sliders (which measure personality baselines). Scene sliders control how the chapter should FEEL.

**The six scene sliders (5-point rubrics from 1 to 10):**
- **Tension** — immediate in-the-moment threat or conflict (1 = complete stillness, 10 = maximum immediate threat, life or identity on the line)
- **Dread** — anticipated tension, the shadow of future danger (a scene can have low tension and high dread simultaneously)
- **Emotional Intimacy** — how close the reader is to the protagonist's inner experience (high intimacy ≠ high action; a character crying alone is high emotional intimacy)
- **Relationship Tension** — the tension between characters present in the scene, regardless of whether it is romantic
- **Pacing Energy** — how fast the scene moves at the prose level (high = short sentences, short paragraphs, rapid dialogue; low = longer sentences, more time given to description)
- **Humor** — how much levity is appropriate given the scene's context

**Prompt logic:** "Analyze the outline above as well as the plot template and determine the slider levels for each chapter. Reproduce the text of each chapter verbatim, but add the sliders beneath each chapter."

**Why this step exists:** Establishing slider targets at the outline stage gives the Chapter Scene Brief step (Steps 5-6 in `${CLAUDE_PLUGIN_ROOT}/references/writing/chapter-generation-pipeline.md`) concrete targets rather than leaving pacing/tone to the model's discretion. The sliders in the chapter plot selector are what the Character Scene Brief uses to determine where character sliders sit for that specific scene.

### Step 5: Logic Check (Final)

Checks the full outline for:
- Consistency with character sheet, worldbuilding sheet
- Consistency with the plot template
- Internal logic and plausibility of cause and effect
- Theme resonance across the arc
- "Jumping the gun" — revealing information (e.g., mystery killer's identity) before it should be revealed
- Ratings and slider consistency — do the slider values match what the 2-3 sentence summary actually describes?

Produces an improvement plan.

### Step 6: Final Outline Rewrite

Implements the logic check. Outputs the finished outline to the outline document.

---

## Human Review After the Outline Automation

Jason's stated practice: he reviews the outline heavily before moving to chapter generation. This is the most human-intensive point in the process.

Recommended review actions:
- Check every chapter for alignment with your vision
- Adjust the slider levels where the AI's assessment diverges from your intent
- Expand the 2-3 sentence summaries for chapters you have strong opinions about
- Update/correct any worldbuilding or character details that drifted
- As you generate chapters and edit them, loop back and add specifics to the next 2 chapters in the outline before triggering that generation batch

Jason does NOT recommend running all chapters at once. He runs 2-3 chapters at a time and reviews/edits before advancing, specifically to catch problems before they compound across the draft.

---

## Simple Version (No n8n)

The simple version uses Claude Projects (one project per step). No automation, no loop — manual handoff between steps. Five projects: Novel Brainstormer, Novel Characters, Novel World Building, Novel Outliner, Novel Chapter Writer. Each project's Instructions field holds the relevant prompt from **story hacker prompts**. Files are added via Claude's project file upload. This version requires manual copy-paste between steps but requires no technical setup. The tradeoff is time: the n8n version runs the whole loop unattended; the simple version requires active management.

---

## Related

- `${CLAUDE_PLUGIN_ROOT}/references/writing/chapter-generation-pipeline.md` — downstream execution; the outline is the primary input
- `${CLAUDE_PLUGIN_ROOT}/references/writing/worldbuilding-method.md` — automation 3; feeds into the outline
- **story hacker prompts** — the raw prompt library this system runs
- **jason structure extraction** — the upstream analysis step; reverse-engineers a comp title into a structure skeleton that becomes the outline template
- **story structure frameworks** — which structural framework (BS2, Hero's Journey, Seven-Point, etc.) to choose before building the plot template
- **character arcs** — arc endpoints must be defined before the chapter-by-chapter breakdown
