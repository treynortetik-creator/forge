---
title: Character anchors — how to stop illustration drift
type: reference
tags: [illustration, character-consistency, picture-book, image-generation]
created: 2026-08-16
updated: 2026-08-16
source: diagnosed and fixed on a real 13-spread book, 2026-08-16
status: living
---

# Character anchors

**The problem this solves:** across separately-generated illustrations, characters drift. Clothes
change colour, haircuts change, a vehicle comes out malformed. It reads as a weak model. It usually
is not.

## First, the cause is almost always the sheet, not the model

Audited on a real book that drifted badly: **0 of 11 spreads specified a garment colour**, and the
mother's entry read *"a tall slender woman with very long straight DARK BROWN hair, fair skin, warm
smile."* **No clothing at all.** The model invented an outfit on every call, so the changing sweater
was guaranteed before any tool was chosen.

> **A character sheet controls only the attributes it actually enumerates. Everything it leaves
> unstated is re-rolled on every single call.**

Fix the text before reaching for tooling:

- **Every garment gets a colour and a form.** Not "a sweater" but "a rust-orange knit sweater."
  Not "simple pyjamas" but "butter-yellow pyjamas patterned with small white five-pointed stars."
- **Every recurring object gets a spec.** A truck that is only "a parked pickup truck" comes out
  malformed. Give it era, class, colour, condition: *"a 1980s American full-size pickup, faded
  forest-green with a white roof, single cab, chrome bumper, light dust on the lower panels."*
- **Never park a named object at the frame edge.** In the audited book, the ONE spread that said
  *"at the edge of frame"* was the one spread with a mangled vehicle. Partial occlusion plus thin
  specification is where these models fall apart.
- **Watch for self-contradiction.** *"long wavy brown shoulder-length hair"* asks for two lengths.

## Then: the anchor image

Generate a reference sheet ONCE, save it as a real file, and attach it to every downstream call.

**This is the same technique Higgsfield's own engineers use for invented characters** — their
non-photoreal pipeline builds a style-key image and carries it forward, under the hard rule *"attach
the same style-key image to every clip."* Their trained-identity feature (Soul) is the wrong tool
here: real people only, one identity per model, and a hard resolution cap.

**Generate the whole cast in ONE image.** This is the load-bearing trick and it is not optional when
style consistency matters. Characters painted in a single pass share one attention context, so they
share brushwork, facial-simplification level and detail density. Generate them separately and you
get an anime child standing beside a Charlie Brown father. Put them in one row, at **true relative
scale**, on a flat background, in flat neutral light, with no props and no ground shadows.

**One anchor per character PER COSTUME.** A single anchor locks one outfit, which is why a
pyjama-anchored toddler turned up barefoot in pyjamas on a daytime road. A book with a day and a
night needs day-<character> and night-<character> as separate sheets, or consistency and story logic
fight each other.

## Attaching it

The mechanism differs by provider; verify before assuming.

- **OpenRouter Images API** — `POST /api/v1/images` with `input_references`. Reference support is
  NOT advertised in the chat-completions docs; check the model's `input_modalities` rather than the
  prose docs.
- **Codex CLI** — `codex exec --image <file>` on the built-in tool. 🔴 **`--image` is variadic
  (`<FILE>...`), so a prompt passed as a trailing positional argument is silently swallowed as a
  second filename and the process then blocks on stdin with no error and no output.** Pipe the
  prompt instead: `cat prompt.txt | codex exec --image ref.png -`. Built-in generation exposes no
  size control (1536×1024 landscape observed); the bundled CLI script goes to 3840px but requires
  `OPENAI_API_KEY`, i.e. metered billing rather than a ChatGPT plan.

## Do not use a contact-sheet grid as the delivery format

Generating all spreads as one grid and slicing it holds character well, and loses on the two things
that matter: a 3×3 slice off a 2K sheet is a fraction of the pixels a page needs, and you cannot fix
one panel without rerolling all nine. **Use a grid as a reference-image factory and a thumbnailing
tool, then throw its pixels away.**

## Checklist before generating any spread

- [ ] Every character's wardrobe has an explicit colour
- [ ] Every recurring object has era / colour / condition
- [ ] The cast sheet was generated as ONE image, at true relative scale
- [ ] A separate sheet exists per costume state
- [ ] No named object sits at the frame edge
- [ ] The character sheet is scoped to the act it belongs to — a sheet attached to every prompt will
      paint characters into scenes that precede their reveal (logged failure, 2026-08-14)
