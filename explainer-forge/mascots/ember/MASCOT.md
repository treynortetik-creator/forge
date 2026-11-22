# Ember (sample mascot)

Ember is a small clay flame who guides the viewer. It ships here as a sample of how to keep a character on-model; swap
in your own by making a folder beside this one with the same parts and naming it in `new_project.py --mascot <name>`.

| Part | Files |
|---|---|
| References to attach to every image request | `refs/ember-ref.webp` (clean, no props), `refs/ember-current.webp` (the approved pose) |
| Sheets | `sheet/character-sheet.webp`, `sheet/turnaround.webp`, `sheet/expressions.webp` |
| Poses, transparent | `poses/` (360 px tall), `poses/large/` (up to 1000 px), picture: `contact-sheet.webp` |

| Pose | Use |
|---|---|
| `ember-point` | points to the viewer's right, at the thing being said; the workhorse |
| `ember-wave2` | hello and goodbye, calm closed smile; use this wave |
| `ember-wave` | laughing wave; not for explainers (see below) |
| `ember-clipboard` | foreman, checking |
| `ember-wrench` | fixing |
| `ember-sit` | watching, waiting, the quiet scene |

## On-model rules

1. Orange-to-coral flame head, yellow glow on the face, two simple dark dot eyes, a small curved closed mouth, chunky
   teal knitted scarf with fringe, round orange body, stubby arms and legs. Same proportions every time.
2. Neutral or gently happy. No angry brows: the "focused" face on the expression sheet reads as angry at small size, so
   ask for neutral. No open-mouth laugh in an explainer.
3. Scarf ends hang on the viewer's left. Never mirror a pose: mirroring moves the scarf.
4. Matte clay, same light (top left), no ground shadow in the file (the page adds one).
5. Beside a brand's logo, never instead of it.
6. Always attach the references and restate the character in words. Redraw anything off-model at once.

## Character block for prompts (`character.txt`, for `sprite_prompts.py --character`)

```text
The character is Ember: see ember-ref and ember-current. Keep it exactly ON-MODEL: orange-to-coral flame head with a
yellow glow on the face, two simple dark dot eyes, a small calm closed-mouth smile (NEUTRAL, not laughing, eyes open),
chunky teal knitted scarf with fringe, round orange clay body with stubby arms and legs. Same proportions and colours as
the reference. Full body, facing the viewer.
```

Then one line per pose, for example `ember-point.png : Ember pointing to the viewer's RIGHT with one arm stretched out,
friendly smile, like a guide showing the way.`

## How the sheets were made

Turnaround: "Four full-body views of the SAME character side by side in one row, evenly spaced, same size and same
ground line: front, three-quarter, side profile facing right, back. Neutral standing pose, empty hands. Plain flat warm
off-white background (#FAF5F0). NO props, NO text." Expressions: four head-and-shoulders portraits in one row (happy,
focused, surprised, sleepy), same rules. Labels were added afterwards. Swap in your own character with the same two
prompts and one clean reference image.
