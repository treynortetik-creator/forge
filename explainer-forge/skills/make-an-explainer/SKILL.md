---
name: make-an-explainer
description: >
  The end-to-end recipe for an instructional or explainer video, from a topic, ticket, feature or doc to a verified
  MP4 with captions or one self-contained interactive HTML explainer. Ordered steps with a gate at each: brief and
  length cap, a script fact-checked against the source, a style sample the owner approves before any build, a voice
  spec and cost plan before any paid generation, narration stitched to exact cues, real product footage on fake data,
  a frame-exact render, and a proof pass that looks at every scene. Use as the entry point when asked to "make an
  explainer", "explainer video", "instructional video", "tutorial video", "how-to video", "product demo video",
  "walkthrough video", "narrated explainer", "training video", or "turn this ticket/doc into a video".
---

# Make an explainer

**The case in one line:** the owner approved a product demo on its second cut ("You nailed it") after the first was
too slow, too small and too loose. Every gate below exists because a cut failed it. This skill is the order of work;
the sibling skills hold the method.

> Forge's thesis: judgment (what to say, what to show, how it feels) stays with the owner and the model. Anything
> that is a number (wpm, runtime, sync offset, ring position, word error rate, dollars) is measured by a script. An
> agent's "done" is a claim until the PNGs are open.

Siblings: `narrator-voice` (the voice), `app-footage` (screen capture), `render-and-caption` (MP4 + SRT),
`explainer-proof` (the detail pass). Also useful: `design-forge:art-department` (images, house style),
`design-forge:design-audit` (measure a page), `proof-forge:render-diff` (compare two cuts), the `hyperframes` skill
if the owner prefers that renderer (this plugin's engine is a dependency-light alternative, not a replacement).

## The steps

1. **Brief (5 min).** Who watches, what they should be able to do after, where it plays (chat, wiki, a live
   meeting, an upload). Pick the format now (`${CLAUDE_PLUGIN_ROOT}/references/formats.md`): MP4 for watching,
   interactive HTML for exploring. Set the length cap: default 3:00-3:30, hard cap 5:00; a talk someone delivers live
   stays under 10 minutes with three ideas.
2. **Read the source.** The ticket and every link, the spec, the product itself. Search public vendor docs without
   naming the requester's organisation. Write `sources.md`.
3. **Outline: about 7 scenes, one idea each.** Hook (the everyday pain) · what it is · show it · how it works ·
   the safeguard or decision · close. Merge rather than repeat.
4. **Script** from `${CLAUDE_PLUGIN_ROOT}/templates/script-template.md`: `## n Title` per scene, one line per clip.
   About 180 wpm means about 540 words for 3:00. Plain friendly sentences. Then **fact-check every claim against the
   source** (a reviewer caught three overstatements in one draft) and **ask the owner how every product name is said**.
   Convert to `lines.json` (`templates/lines.example.json`): `caption` = real spelling, `text` = TTS spelling.
5. **GATE: style sample.** One image and one rendered scene in the proposed look; the owner approves before you build
   the rest. Default look: light, warm, off-white, soft clay 3D or flat illustration, one or two accents, no dark
   neon. Label every image you send.
6. **GATE: voice spec + cost plan.** Before any paid call: per item, cost, retries, acceptance check, cap. The local
   voice and all SVG/CSS/GSAP graphics cost nothing; image-to-3D props ran about $0.40 each.
7. **Voice** (`narrator-voice`): audition 3 designed candidates, the owner picks by ear, clone every line, check
   every line, then set the speed by ear in the stitch.
8. **Footage** (`app-footage`), if the subject is software: sample data only, human-paced input, a manifest.
   Start it in parallel with step 7.
9. **Build the timeline** from `templates/stage.html` + `timeline.js`. Animations hang off spoken words
   (`W(id, word)`), never typed seconds. Callouts from boxes measured on the frame.
10. **Render** (`render-and-caption`): frame-exact MP4 with burned captions and an SRT; or `inline_build.py` for
    the interactive file.
11. **GATE: proof** (`explainer-proof`): every 2 s sheet read, every ring crop read, sync under 50 ms, runtime
    under the cap, `name_check.py` at zero, facts re-read.
12. **Deliver a draft to the owner only**, as one file plus the SRT, with the runtime and what changed. The owner
    shares it. Expect one round of notes; re-render only what changed (`--only`, `SKIP_AUDIO=1`).

## Traps

- **A slow, "calm" narration.** The first cut ran about 120 wpm and was rejected as "a snail". Calm comes from the
  voice prompt; speed comes from the stitch.
- **Stock or dramatic voices.** Presets had an accent the owner hated; a cloned house voice was "overly intense".
- **Footage in little browser cards.** Rejected. Full screen, zoom only to read a number.
- **Rings placed by eye.** A few pixels off reads as sloppy. Measure on the frame, then check each ring.
- **Skipping the 2-second pass.** That is where the ring left on after its cut and the caption over a callout hide.
- **Real names anywhere**: narration, captions, footage, notes. Grep, do not trust memory.
- **Real-time screen recording of the page.** Drops frames. Render frame by frame.
- **Old job titles and feature names.** Check them with the owner; teams rename things.

## Done means

The MP4 (or HTML) plays start to finish at the agreed length; `explainer-proof` passed with every sheet read; the
owner has heard the product names said right; nothing went to the audience before the owner saw it.
