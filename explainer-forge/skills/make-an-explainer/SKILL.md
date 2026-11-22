---
name: make-an-explainer
description: >
  The one entry point for any narrated video: concept explainer, review explainer for a tool or connector, product demo,
  story film or voiced deck. Runs it in order with a gate at each step: brief, fact pack, beginner-proof script, cold
  script review, style frame, voice pick, owner go, one-take voice, build, proof, independent review, owner viewing, batched edits,
  teaser post, retro. Says what the owner approves, which model tier does what, and when money may be spent. Use for
  "make an explainer", "explainer video", "instructional video", "how-to video", "tutorial video", "product demo",
  "training video", "narrated video", "voiced deck", "turn this ticket or doc into a video".
---

# Make an explainer

One recipe, five shapes. Judgment (what to say, what to show, how it feels) stays with the owner and the strongest
model. Anything that is a number (words per minute, runtime, sync, size, dollars) is measured by a script. An agent's
"done" is a claim until the frames are open and the numbers are printed.

Siblings: `house-style` (the rules, read first), `narrator-voice` (the voice), `app-footage` (screen capture),
`sprite-explainer` (the page engine), `render-and-caption` (MP4 and captions), `explainer-proof` (the detail pass), `lessons-loop` (the retro).

## Start

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/new_project.py --list-profiles
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/new_project.py --title "Your title" --profile concept-video --out <folder>
```

It makes the project folder: `brief.md`, `script.md`, `facts.md`, `names.txt`, `owner-notes.md`, `saymap.json`,
`retro.md`, `env.sh`, and `run.md` with a section per step. Work from `run.md`; every block sources `env.sh` first, so it
works in a fresh shell. Keep every prompt, raw image, take and command in that folder, never a temp folder.

Pick the profile from `${CLAUDE_PLUGIN_ROOT}/profiles/`:

| Profile | For | Build path scripted in `run.md` |
|---|---|---|
| `concept-video` | teach one idea to beginners; 4:00 to 5:00, about 900 words | complete: sprite page, HTML and MP4 |
| `compliance-connector` | help a committee decide on one tool; 3:00 to 3:30 | partial: the same page works; click-for-detail is hand-written |
| `product-demo` | show real software working; 2:30 to 3:30 | complete: your footage on the stage page |
| `story-film` | a told story with drawn characters; about 2:00 | partial: voice, cues, prompts and proof; drawings and motion are hand work |
| `deck-voiceover` | a short deck that plays itself; one to three slides | partial: the same page works; no slide engine is bundled |

## The order

| # | Step | Who | Gate (what the owner approves, or what must be true) |
|---|---|---|---|
| 1 | **Brief.** Who watches, what they can do after, where it plays, the length, the last approved build's folder | strongest model with the owner | owner OK on the one-page brief |
| 2 | **Fact pack.** Every claim with its source, opened that day; numbers counted fresh | cheaper model gathers, strongest checks | no claim without a source line |
| 3 | **Script.** Write the scaffolded `script.md` (it is already in the parser's format); beginner-proof; house-style rules W1 to W18 | strongest model | every word a beginner would not know is gone, defined or tagged; `make_narration.py` parses it |
| 4 | **Cold script review.** A reader who has seen nothing else reads the narration only and reports where they got lost | separate strongest model, no context | findings fixed, or ruled out by the owner |
| 5 | **Style frame.** One image of the wow scene in the chosen style (`${CLAUDE_PLUGIN_ROOT}/styles/clay-factory/STYLE.md`), from `prompts/style-frame.txt` with the files in `refs/` attached | image tool plus strongest model | owner approves look, labelled image |
| 6 | **Voice pick.** The profile's bundled voice, or an audition: both bundled samples plus three designed candidates, labelled | cheaper model runs | owner picks by ear |
| 7 | **Owner go.** Script, style frame, voice letter and cost plan in one message. Story films add the storyboard | owner | an explicit go. Nothing is built or bought before it |
| 8 | **Voice, one take.** The whole script in one pass, checked word for word against the script, one tempo set by measured pace | cheaper model runs, owner listens | no word missing or added; owner heard the product names |
| 9 | **Build.** Sprites, scenes and the page (or footage, or drawings); every animation hung on a spoken word | strongest model for design, cheaper for mechanical work | first object by 1 s, no gap over 1.2 s |
| 10 | **Proof.** Stills of every sentence and every camera move, sync, names grep, runtime | cheaper model runs, strongest reads | every still opened, sync numbers printed, 0 names |
| 11 | **Independent review.** Someone who did not build it, with the owner's ruling list | strongest model, fresh | SHIP or FIX FIRST, at most 8 findings |
| 12 | **Owner viewing.** The draft goes to the owner only, flaws listed first | owner | notes |
| 13 | **Batch edits.** Wait for all notes, say them back, then one rebuild | strongest model | owner says go, then ship |
| 14 | **Post.** Draft a teaser (one line on what it is, one image). The owner posts | strongest model drafts | owner posts |
| 15 | **Retro.** `lessons-loop`: rules, numbers, traps | whoever led | rules updated or a reason why not |

`run.md` has a section with the same number for every step, with the commands.

## What the owner approves, and only these

1. The brief. 2. The script. 3. The style frame. 4. The voice. 5. The go. 6. Anything that costs money. 7. The cut.
Everything else is ours. Never ask them to check fake data, find a file or rerun a step.

## Model tiers

| Tier | Work |
|---|---|
| Strongest | brief, script, reviews, scene design, motion, judging stills, the teaser |
| Middle | building from a clear spec, capture, page code, tests |
| Cheapest | bulk reading, fact gathering to a list, transcripts. Never anything shipped as is |

## Cost rule

Free first: local voice, local drawing, bundled sprites and code. Before any paid call, write item, price, retries and a
cap, and get a yes. Over about 1 dollar always needs the yes. Re-check a price on the day; listed prices are not what
you pay.

## What to say to a builder

Paste: the profile numbers, the house-style rules that apply, the last approved build's folder, the fact pack, the
owner's ruled-out list, the exact commands in `run.md`, and what done means. Rules from a recipe alone drift; point at
the last build.

## Traps that cost a pass

- **Percent speed.** Say words per minute while speaking, measured.
- **A take made from an old script.** Rename stale takes; diff the take against the script before building.
- **Stitching the voice from pieces.** Tone changes at joins.
- **Boxes-and-arrows charts.** Show the thing moving.
- **Building on the first note.** More notes are coming.
- **A still frame that looks right, and motion that doesn't.** Send early; the owner's viewing is the motion review.
- **Reviewer suggestions that break an owner ruling.** Give the reviewer the list.
- **Real names anywhere.** `name_check.py` on script, captions, page and post.
- **Real-time screen recording.** Render frame by frame.

## Done means

The file opens on a double-click and plays start to finish at the agreed length; every proof still was opened; the
owner has seen it and approved it; the teaser is drafted; the retro is filled in. Nothing reached the audience before
the owner.
