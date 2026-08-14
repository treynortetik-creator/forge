---
name: dossier-to-worldbuilding
description: "Build the worldbuilding sheet from a story dossier, one element at a time. Extracts a flat element list, then for each element classifies it into a category, applies that category's full profile format, logic-checks it against everything already written, and rewrites before moving on. Use after the character bible and before outlining. Triggers on worldbuilding sheet, build the world, flesh out the setting, magic system."
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep]
---

# Dossier to Worldbuilding

**Why this exists as its own skill.** Like the character bible, the source automation loops **one
element at a time** — and critically, it **re-reads the world built so far on every iteration** so
each new element is checked against the ones already written. That accumulating-consistency mechanism
has no single-pass equivalent. It is the difference between a world and a list.

**Required input:** a story dossier. **Strongly recommended:** the finished character bible, as
context.
**Optional:** a worldbuilding template, genre tropes, author notes.

---

## Step 0: Extract the element list

Produce a **flat** list of every worldbuilding element the dossier implies. 🔴 **Do not categorise
here** — classification happens per element during expansion, deliberately, because an element often
turns out to belong to a different category than it first appears.

**Trim before you start.** If the dossier over-identifies elements, cut to what the story actually
needs — every element you keep costs context downstream. More than 20-25 is usually scope creep.

---

## THE LOOP — run Steps 1-3 for EACH element, appending before the next

### Step 1: Classify and expand one element

Classify into one of the eleven categories, then follow **that category's full profile format** from
`${CLAUDE_PLUGIN_ROOT}/references/writing/worldbuilding-categories.md`. Each has its own document
structure — Hard Rules vs Soft Rules for a magic system, The Truth Behind the Myth for a deity,
Details to Use in Prose for a culture or language.

**3-4 generic sentences is not a profile.** That produces a glossary.

### Step 2: Logic-check that one element — against the world so far

🔴 **Re-read everything already written before checking.** This is the whole point of the loop: the
second criterion below asks whether this element is consistent with the elements already generated,
and it cannot be answered without that read.

```
=<worldbuilding_template>
[supplied]
</worldbuilding_template>

<dossier>
[supplied]
</dossier>

<author_notes>
[supplied]
</author_notes>

<worldbuilding_so_far>
[supplied]
</worldbuilding_so_far>

<worldbuilidng_element>
GENERATED WORLDBUILDING ELEMENT TO CHECK:
[supplied]
</worldbuilding_element>

## YOUR CHECKLIST - Flag ANY issues for the <worldbuilding_element> above. Check for the following:

1. **Dossier Consistency**: Does every element align with the worldbuilding, character, and plot details in the Dossier? No contradictions with story events, character roles, or other worldbuilding elements?

2. **Worldbuilding So Far Consistency**: Is the element aligned with the other fleshed out worldbuilding elements that have been generated already so far (if any). These can be found in the <worldbuilding_so_far> info.

3. **Author Notes Alignment**: Does the profile honor specific instructions from Author Notes (if any)

4. **Worldbuilding Template Fit**: Does the profile feel appropriate for the genre and fit the description of this element's role in the Worldbuilding Template (if any)

5. **Internal Logic & Consistency**
- Do the rules of this element hold up under scrutiny? 
- Are there any logical contradictions within the element itself?
- If this element has limits or costs, are they consistently applied, or do they bend conveniently for plot reasons?

6. **Plausibility & Cause/Effect**
- Do the social, political, economic, or physical consequences of this element make sense? (e.g., a deadly plague should affect labor, trade, and religion — not just one character)
- Does history flow logically from cause to effect, or do events happen because the plot needs them to?
- Are the power structures realistic given the resources, geography, and technology available?

7. **Story Integration**
- Does this element create meaningful pressure, stakes, or choices for the characters — or is it just set dressing?
- Is it appropriately developed for its role in the story? 
- Does it connect to at least one other worldbuilding element in a way that makes the world feel interconnected rather than modular?

10. **Thematic Resonance**
- Does this element reflect or reinforce the story's central themes?
- Could it serve as a metaphor or lens through which characters explore the story's core questions?
- Does it feel intentional, or like it was added for color without deeper purpose?

## OUTPUT FORMAT:

Output a list of anything you might flag and create an improvement plan on how to improve the worldbuilding element, while still making it fit within the story and genre.
This is a complex task. You are not allowed to perform at a mediocre level. You are performing a rigorous LOGIC CHECK on a generated profile for a worldbuilding element. Your job is to ensure it is **100% consistent, plausible, and logical**, as well as consistent with the Story Dossier, Author Notes, Worldbuilding Template, etc.
```

Change list only. Do not rewrite here.

### Step 3: Rewrite that one element

Implement only the flagged changes. Append to the sheet. Return to Step 1.

---

## Output

`[project-name]-worldbuilding.md` in the project directory, elements in the order processed.

## Related

`dossier-to-characters` (run first; feed its bible in as context) ·
`references/writing/worldbuilding-categories.md` (the twelve formats) · `dossier-to-outline`
