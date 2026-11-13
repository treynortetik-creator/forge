# Portraits, masks, blink patches, living-ink motion

Source: the roguelite's portrait packer (about 340 lines Python, not vendored; it reads a game-specific character list
and colour file) and its ambient-motion helper module. The design is general; the numbers are what that game used.

## Portraits: from painting to atlas
Source art: a painted figure on cream paper, 1024x1536, six mood poses per character (neutral, serious, angry,
wry, sad, surprised). Mood swaps the WHOLE pose, not just the face.

1. **Cut the figure out of the paper.** Near-paper pixels CONNECTED TO THE BORDER become transparent, with a soft
   edge, and the paper colour is un-mixed from the fringe so there is no cream halo over a dark scene. The paper
   colour is measured per image (median of the bright border-connected region), because one portrait came back on
   whiter paper (254,254,251 against 249,246,239). Patches of true paper trapped inside the figure (between an arm and
   the body; gaps between hair strands, 30 px or more) go too. `scripts/cutout-trim.py` implements the same idea.
2. **Crop** to the top 70% of the figure (the reference product crops at the thighs) and scale by 0.5, so the packed
   frame is 512x538 and is drawn about 2x larger in game. Reason: first-play download cannot pay for 1:1 pixels.
3. **Trim and shelf-pack** into ONE atlas (Phaser JSON-hash trimmed frames); `sourceSize` is the untrimmed frame, so every
   mood of a character registers identically and a patch can be placed with the same convention. WebP quality 44 (an
   environment variable), 4096 px page width, 2 px padding. Further atlases (a boss set, a second cast) stream on
   demand and never load on first play.
4. **Emissive and gold masks.** Derived from colour, per character, by hue / saturation / value rules (each rule is
   hue low, hue high, minimum saturation, minimum value; optional maximum saturation and maximum warmth to separate silver
   from cream). A 0.08 ramp on each threshold avoids a staircase edge. Glow masks are grey-closed 3x3; gold masks (engraved
   hatching) are Gaussian-smoothed 2.2 and re-thresholded with a soft ramp so the shimmer has round edges. Specks under 6 px
   (glow) or 12 px (gold) are dropped. Masks are stored as extra frames `<char>-<mood>-glow` and `-gold` at HALF
   resolution (RGB = the figure's own colour, A = the mask) and drawn at 2x.

## Blink patches
A blink is NOT a second portrait. Ask the model for an eyes-closed version of each mood, then:

1. Diff the blink image against the open image over the cropped region; any pixel whose max channel difference exceeds 8
   of 255 counts as "the eye changed". The bounding box of those pixels, padded 12 source px (6 atlas px), is the patch.
2. Cut the blink image out of its paper EXACTLY like the portrait (same cut-out, same crop, same resize), so edges match.
3. Take only the patch region, feather its alpha over 3 atlas px (so a lossy-codec difference at the border cannot show as a box).
4. Store it as frame `<char>-<mood>-blink` (or `<char>-blink` for every mood) whose `spriteSourceSize` is where the patch
   sits inside the FULL frame and whose `sourceSize` equals the full frame, exactly like the portrait frames. The engine
   draws the patch image with the same position, origin and scale as the portrait and it lands on the eyes. A character
   with no blink frame (one whose eyes are a flame) never blinks.
5. Swap it in for 110 ms at random 3 to 7 s intervals, never during a mood cross-fade, off under reduce motion.

Why diff rather than ask for "just the eyes": the model cannot hold registration; the diff finds the real changed pixels.

## Living ink: ambient motion rules
Source of the lesson: a play-through of a reference game, written up as notes. "Nothing glowing is ever still, and
nothing is static on a screen the player lingers on."

| Rule | Implementation as built |
|---|---|
| Glowing things pulse | every emissive bit pulses or flickers: an additive copy of the glow-mask frame; pulses are a slow breath with a small wobble (never a clean sine); flames flicker irregularly from value noise, no per-frame random; a phase offset per instance |
| Gold shimmers | anything gold: a bright diagonal band sweeps bottom to top; period 2800 ms, sweep 600 ms, masked to the gold pixels, a `phase` offset so stacked UI does not flash in lockstep |
| Portraits blink | as above |
| Mood swaps the whole pose | six full-body moods, cross-fade 120 ms; free-text emotions mapped to the six |
| The advance mark bobs | 5 px over a 1400 ms period; no-op under reduce motion |
| Drift particles | per-area dust, ash, leaves over the floor; motes in light shafts; flecks on pick screens. Pooled, hard caps (the design said 40 drift, 24 risers, 28 hub dust: design numbers when read, on a branch), runtime textures only, one master switch = the Ambient setting AND NOT reduce motion |
| Pickups are never static | a tall thin beam visible across the room, a ring on the floor, rising motes, a slow bob, a periodic shimmer, all in the reward's colour |
| Backdrop carries the personality | a speaking character gets their own scene behind them |
| Box style by class, not per character | one box style per kind of speaker |

How to build one: find the helper first and extend it; prefer runtime textures (canvas, Graphics, masks derived from an
existing atlas frame) and additive pooled images over new files; drive loops from ONE update source (scene time in the
scene's update, or one tween per object created once, never a tween per frame); under reduce motion every loop goes
static (resting frame, no bob, no sweep, no drift; glows may hold a steady level); colour belongs to colour owners only;
prove it with two shots at different times or a GIF, run the palette audit on run screens, and compare fps with the
previous run.
