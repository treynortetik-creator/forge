# Clay factory

A warm, handmade clay world on a cream page: chunky modelling-clay objects, a slate conveyor belt, clay signs for
every word on screen, and a small character who guides the viewer. Reference cut: a 4:22 concept explainer (14 scenes,
877 words), which the owner rated the best yet and chose as the house style.

| Part | Where |
|---|---|
| Objects | `sprites/` (approved sizes), `sprites/large/` (up to 1000 px, for close-ups), `sprites/index.md`, `contact-sheet.webp` |
| Fonts | `fonts/` (SIL OFL 1.1, see `fonts/OFL.txt`) |
| Prompts for new objects | `prompts/` |
| Style anchors to attach to an image request | `refs/` |
| The guide character | `../../mascots/ember/` (swap in your own) |

## Palette

| Token | Hex | Use |
|---|---|---|
| paper | `#F6EFE6` | page, every scene, nothing else behind it |
| ink | `#2E2823` | titles and body text |
| muted | `#5A4F44` | second lines, sources |
| coral | `#C4533B` | problem, stop, "broke" |
| sage | `#5E7F4E` | pass, ok, done |
| teal | `#2F8F86` | neutral tag, the safe place |
| mustard | `#D99A2B` | tools, switches, warmth |
| tag text / ink tag | `#FFF8EE` / `#4C4036` | words on coloured pills; the specialist-word tag |
| plaque | `#F3E6D0` | clay sign board |
| belt / side track | `#70778A` / `#C99468` | main conveyor; a loop back |
| clay shadow | `#3B2A1A` at 20% | the soft disc under every object |
| caption pill | `rgba(46,40,35,.86)`, text `#FFF8EE` | captions |
| player bar | `#2E2823` (dark page: `#1E1A17`), text `#F6EFE6`, focus `#F2C98B` | HTML player |

Meaning is fixed: coral is trouble, sage is success, teal is the safe shared thing. Don't use them as decoration.

## Type (on a 1920x1080 stage)

| Use | Font | Size |
|---|---|---|
| Scene title on a plaque | Source Serif 4 Semibold | 38 to 58 px (default 50) |
| Object label | Source Serif 4 Semibold | 34 px |
| Body on a plaque | Source Sans 3 Regular | 30 px, line height 1.25 |
| Tags, specialist-word tag | Source Sans 3 Semibold | 28 px |
| Second line under a label | Source Sans 3 Regular | 27 px, ink (not grey) |
| Source line for a number | Source Sans 3 | 30 px |
| Caption | Source Sans 3 Semibold | 36 px |
| Floor for anything readable | | 24 px after camera zoom; check it at phone size |

Serif for names of things, sans for everything said about them. No third font.

## Captions

One line when possible, at most 70 characters a piece, split at clause marks first. Bottom centre, 30 px from the
bottom; 70 px when the camera is on the factory so they clear the art. Max width 1500 px, 12 px corner radius. Timed
by character share inside each spoken sentence. Can be switched off in the HTML player. If a caption meets an object,
move the caption up or the object, never shrink the text.

## Layout

Fixed 1920x1080 stage, absolute positions. Title plaque at left 90, top 40 to 60. Objects sit on a belt baseline. Side
labels 290 px wide, centred under their object. Big result plaques between y 700 and 840. Keep 90 px clear on the left.
Everything an object says is on a clay sign (`plaque.webp` as a 9-slice: slice 95 110, border 30px 36px, or 20px 26px
small) or a clay pill, not a flat card.

## Texture

The clay look is baked into the sprites. The page adds an SVG `feTurbulence` grain on the paper (baseFrequency .9, 7%)
and a fingerprint noise on belts and drawn marks (baseFrequency .75, 16%), plus a small emboss on logo marks. One soft
blurred shadow disc per object, light from the top left. Belts are rows of real slat sprites, not a drawn stripe.

## Motion

- Everything hangs off spoken words: an object lands on the word that names it, at most 0.3 s early.
- Objects arrive by `pop` (scale up with a little overshoot); things that take a hit `squash` (scaleY .92, scaleX 1.05,
  elastic back). Signs fade. Nothing spins.
- One change travels as a small tile: rides the belt (46 px/s belt speed), hops in an arc between places, loops when
  it is sent back, cracks and shows a coral dot when it breaks.
- One shared world with a camera. Zoom 1.3 to 1.45 on one place, 1.0 for the whole factory, ease in and out
  (power2.inOut), never a cut inside the world. Scenes outside the world crossfade (0.35 s in, 0.3 s out, starting
  0.15 s before the scene).
- The whole-factory shot, everything moving at once, is the wow moment. It comes after the beginner words are taught.
- The guide character holds one pose per scene, with a small idle wobble; it points at whatever is being said.
- Idle life: lamps glow, belts run, the clock hand turns. Nothing else moves without a reason.

## First and last frame

The first object is on screen by about 1 second (chat apps autoplay the first frame). The last frame holds about a
second after the final word and shows the whole idea.

## Making a new sprite

0. A whole frame for approval uses `prompts/style-frame.txt` instead (fill its `SCENE:` line).
1. `prompts/header.md` first, word for word, then your items from `prompts/items.md` (one line each, one object per
   image, no words, transparent background).
2. Attach `refs/style-reference.webp`, `refs/station-example.webp` and `refs/token-example.webp`; for the character add
   `mascots/ember/refs/`. Save them as PNG first if your image tool can't read WebP.
3. One object per image. Look at each as it lands; redo off-style ones at once.
4. Trim to the alpha edge (threshold 24), scale to about 1.6x the largest on-screen height, WebP quality 88.
5. Add a row to `sprites/index.md`, and rebuild the contact sheet.

## Rejected, and why

| Tried | Verdict | Why |
|---|---|---|
| Dark, neon, glowing circuits, vault doors | rejected at first sight, more than once | cold and unfriendly |
| Papercut and gouache look tests | clay won | picked side by side; the reason was not recorded |
| Boxes-and-arrows flowcharts | rejected hard | unattractive, and beginners can't read them |
| Clay hero image, then flat interface slides | sent back | the world has to hold from first frame to last |
| A clay belt drawn as a flat stripe | fixed | flatter than the sprites beside it; real slats replaced it |
| Open-mouth laughing or angry-brow guide poses | replaced | off-model; neutral closed smile reads friendly |
| Generic person drawings with faces | not used | no real people; a faceless worker or a plain silhouette with a label |
| Icon-font versions of brand marks | caught by the owner | use the real file |
| Small grey labels (22 to 24 px at 40%) | fixed | unreadable on a phone |
| 2 to 3 second empty holds between scenes | fixed | read as broken |
| Very glossy 3D plastic | not tried | unknown; slightly glossier clay was preferred over dull |
