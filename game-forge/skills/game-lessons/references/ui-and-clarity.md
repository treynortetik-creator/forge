# UI layout from a genre leader, the clarity pass, and living motion

Source: the roguelite (layout copied from Hades and Hades II; both are public games). Percentages are of a 1920x1080 frame.
Hades layouts are described here as facts about a public game's screens; the art is never copied.

## 1. The rule and why

The owner's instruction (2026-10-18): the leader's team had a whole staff and chose those layouts because they work better, so lean on what exists instead of reinventing.
Copy: HUD placement, menu structure, dialogue box, screen flow, interaction prompts. Invent: gameplay, story, art style, small details.
Before designing ANY screen, find the leader's equivalent and copy its structure. Propose a departure only when their version cannot fit your mechanics, and say why in the spec.

## 2. How to extract a layout spec that is true

1. Capture 30-50 frames of the leader's actual gameplay and menus (we used 41 frames, with a separate set for menus). Keep them out of git (a `refs/` folder ignored by `*.jpg`, `*.png`, video).
2. Write a spec file: each screen mapped to the leader's screen, with % positions, timings and a "top 15 to copy" list. Cite the frame file for each claim.
3. **Do not accept a model's write-up of the leader's UI without checking.** An LLM-written spec had 108 claims; 8 were right as written (one section described the previous game in the series). Verify against frames or mark the claim unverified.
4. Where your own style document and the leader's placement conflict on position, the leader's placement wins (our style doc said health top-left; the leader's is bottom-left, and that shipped).
5. Keep a list of deliberate departures with the reason (ours: shop items show name, price and effect on walk-up, because players could not tell what an item did).

## 3. Anchors we copied (roguelite HUD and screens)

- **Health** bottom-left (x 1-31%, y ~94.5-98.5%), a second bar stacked directly above. **Currency** bottom-right (x 93-99.5%, y 95-99.5%) with a red spend delta beside it. **Boss** name plus thin bar top-centre, never bottom.
- **Pickup column** on the far-left edge (x 0.5-5%), fixed slot order, fills top-down, empty slots dim.
- **Dialogue:** one portrait at a time in the LEFT slot (big, bottom-cropped, ~4-44% x, head ~5% from the top); speaker change swaps in place; a name plate centred above the box with a title line under it; box x ~35-85%, y ~65-92%, 2-3 lines left-aligned; a small advance mark bottom-right that bobs;
  the world behind stays visible, dimmed, not blurred; no player portrait. Our first portraits were 13% of screen width against the leader's ~45%; a size round fixed it.
- **Choice screen (reward pick):** three stacked full-width rows; rarity is a label plus ornament, not colour.
- **Interaction prompt:** one bottom-centre slot for every interaction, stacked when several. Interact on a shoulder button.
- **Shop room:** prices float over every item, always visible.
- **Region card** at the top for 2.5-3 s (ours holds 2.5 s and pauses). **Death:** hard cut to black on the blow, the hero lit alone, a banner after ~2 s.
- **Keepsake/inventory cabinet:** an 11 x 3 grid of square slots with a rank footer; the selected slot glows with a progress bar; a bottom panel with icon, name, rank, one-line effect with bold keywords, "from" plus a quote; glossary tooltips stacked right.
- **Menu spec (title, pause, settings with remap as a tab, hero select by walking up to the portrait, run summary only after a win)** came from a second pass over menu frames.

## 4. UI kit shape that let agents build screens fast

- One base class for every controller-navigable screen: owns the focus ring, prompt bar and input loop; pauses a host scene while open; screens register `Widget`s (rect + callbacks) instead of hand-rolling pointer handling.
- Spatial focus is a **pure function** with unit tests: held-direction repeat 400 ms then 90 ms (50 ms after 1.5 s), a 250 ms input ignore after a screen opens, 1 s hold-to-confirm for destructive actions, focus never lost when items change.
- `txt()` with a minimum text size floor (28 px at 1080p for Steam Deck legibility; dialogue 18 px or larger) and a user text-size setting; `glyph()` prompts that follow the live device; widgets (buttons, option rows, sliders, meters); theme tokens.
- **Card layout is a pure function tested at every item x rarity x level with real font metrics**, so new copy that overflows fails a test instead of being found by the owner.
- HUD helpers (`hudModel`) pure and tested; the HUD scene only draws.
- Comfort: menu camera flash/shake/zoom go through one module that honours Flashes, Shake and Reduce motion.
- UI proof: a preset-driven screenshot tool (`shots <preset>|all`) that presses keys and holds buttons; open the PNGs. A "UI check" that clicks through the real UI (67/67, later 107/107 in the tower-defense game) is a cheap regression net.

## 5. Style traps

- Generic widget defaults (green/yellow health bars, rounded boxes) contradict a style; write the style rules down once (frames, fonts, text colours, rarity as ornament) and have the UI base class enforce them.
- A second font family loaded from a CDN is a boot risk: the game could not boot without Google Fonts until the fonts were self-hosted (6 files, 95 kB).
- Do not leave dead plates around: old UI plates "retire" in a doc but stay in code until a package replaces them; list them.
- Two overlapping pieces of text in the same slot (a shop chip under a title plate; a boss card ghost showing under Pause) were found only by shooting 28 menus; shoot all menus after any shared-widget change.
- "Nothing explains the number": say what each currency buys once, on one screen, plus a one-time tip on first gain.

## 6. The clarity pass (copy, tips, glossary)

**The trigger:** the owner played and could not tell what half the words meant. Causes, in order: (1) six power-granting factions with two names each and nothing tying a name to what it does; (2) the same word used for two things;
(3) flavour lines that announce a mechanic and never state it; (4) internal ids and jargon on screen; (5) unbuilt features that looked like an in-fiction puzzle.

**Process (one Opus-class copy agent, spec only, no source edits, then a builder applies it in two ownership lanes):**
1. Inventory every player-facing term with: what it is, where first met, whether it is explained there (file:line), verdict (keep / rename / keep + explain).
2. Top-15 most confusing terms with a fix each.
3. Naming rules for all new copy.
4. A machine-readable twin (`tips[]`, `glossary[]`, `rewrites[]`, each tagged with its owner) where every `old` string was checked verbatim against the source.
5. Apply in two lanes (HUD/barks/in-world overlays; menus/cards/Grimoire). Result: 120 of 121 rewrites applied, 46 one-time tips, a Rules tab with a 106-entry glossary.

**Naming rules that held:**
1. **One word, one meaning.** Fix collisions by renaming the weaker use (a no-hit bonus door shared a word with the post-win goal: renamed).
2. **Say the effect with the name** the first time per screen ("Fire gifts: Burn"). Titles are flavour, never the only name.
3. **Flavour, then plain.** Any line that announces a mechanic gets a plain sub-line stating it. The plain line never jokes.
4. **Player units only:** seconds not milliseconds, percent, "nearby", "room", "region", "attack warning". Not px, ticks, biome, i-frames, DPS, weight, budget. Enforce with a banned-words test over data and copy.
5. **Unbuilt is unbuilt:** "Not in this build yet", never an in-fiction "not yet awake".
6. Every number on a card comes from the sim, not from a hand-typed string.

**What the pass found that was not about words:**
- A keyword said "next hit is a guaranteed critical"; the sim gave +20% crit chance for 5 s. A second keyword (Chain) was also wrong. The game taught wrong rules.
- Number mismatches between door labels and item text (25% vs 30%); an item healed 30% over the cap with no feedback (a `heartsFull` event was added).
- An assist-mode offer asked "Will you take it?" and offered no way to answer. Fixed by saying where to turn it on in Settings.
- A flavour banner ("Something stirs") announced an unlock, fired for two different kinds of unlock, and never said what had unlocked.
- Unexplained corners of the UI: an "invisible heal" (stair rooms with no art) and an ultimate that needed a gift nobody told you to pick. A UX audit counted 11 P0 / 29 P1 / 14 P2 across 69 shots; 11 P0 included barks that block input and cover the HUD, hidden door rewards, invisible shop items, and silent state changes.
- **Decline buttons matter:** the owner wanted to reject a reward offer; a 0.6 s hold-to-decline with a small consolation reward fixed it.

## 7. Living motion (ambient)

The lesson (from studying the leader): **nothing glowing is ever still, and nothing is static on a screen the player lingers on.**

| Rule | Detail we shipped |
|---|---|
| Glowing things pulse | a slow breath with a small wobble, never a clean sine (~1 s for energy, irregular value noise for fire; no `Math.random` per frame); each instance gets a phase offset |
| Gold shimmers | anything gold: a diagonal bright band every 2,800 ms, sweep 600 ms, masked to gold pixels, phase-offset so stacked UI does not flash in lockstep |
| Portraits blink | one eyes-closed patch per mood, swapped for ~110 ms at random 3-7 s; each blink patch checked by script to differ from the base only inside the eye box (0.2-0.8% of pixels) |
| Mood swaps change the whole pose | 6 full-body moods per character, 120 ms cross-fade |
| The advance mark bobs | 5 px over a 1,400 ms period |
| Drift particles | pooled, capped (caps 48 / 36 / 24 per layer), runtime textures only, visible 3-5 px motes in clusters; the first round was too faint and had to be made visible; in stills it still reads subtle |
| Pickups are never static | a tall thin beam readable across the room, a ring on the floor, shards, rising motes, a slow bob; later made a constant-width beam with an upward shimmer because the top was too wide |
| Box style by class, not per character | each faction class gets one dialogue box style; ask before shipping a third |

How to build one:
1. Find the existing helper first and extend it; do not fork.
2. Prefer runtime textures (canvas, Graphics, masks derived from an existing atlas frame) and pooled additive images over new files. A new image goes into an existing atlas.
3. **One update source:** drive loops from the scene clock in one update, or one tween per object created once; never a tween per frame.
4. **Reduce motion:** every loop checks the setting and goes static (resting frame, no bob, no sweep, no drift). Glows may hold a steady level.
5. Colour only for colour owners; check with a palette audit if the art direction limits colour.
6. Prove it: two shots at different times or a GIF, look at them, check frame time against the previous run.
