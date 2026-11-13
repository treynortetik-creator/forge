# Game feel: the spec we wrote and what it taught us

These are the **spec values** from the roguelite's feel document (written 2026-10-15, round 2), a top-down action game with a dash,
a combo, and bosses. They are starting points, not laws; the owner tuned by playing. Hit-stop is part of the deterministic sim
(bots play with it); shake, rumble, flashes and damage numbers are render-only. The bar: **every input answers in under 100 ms;
dash cancels anything; every hit you take was your fault (every attack has a telegraph at least 350 ms long at max difficulty).**

## 1. Hit-stop (sim side)

Freeze the attacker and the victim for N ms (they skip sim ticks); the rest of the world keeps running, except rows marked global.

| Event | ms | Scope |
|---|---|---|
| Light hit (combo 1-2, jabs, bolts) | 40 | local |
| Medium hit (dash attacks, casts, pounce) | 60 | local |
| Heavy hit (combo finisher, slam) | 90 | local |
| Crushing hit (big haymaker, ground pound on 3+ targets) | 120 | local |
| Crit | +30 | local |
| Killing blow | +20 | local |
| Status ticks, hazards, DoTs, chain arcs | 0 | n/a |
| Hero takes damage | 80 | **global** |
| Block | 50 | local |
| Ultimate-style activation | 120 | **global** |
| Boss phase break | 250 | **global** |
| Boss or mini-boss killed | 400 | **global** |

Rules:
1. One hit-stop per attacker per 100 ms window; a multi-target hit uses the largest single value once, not the sum.
2. Never stack local and global: take the larger.
3. **A dash press during any hit-stop the hero is part of ends it on the next tick** and the dash starts; the victim's freeze continues for its remainder.
4. Frozen actors' telegraph timers and hitboxes freeze with them. (A balance pass found enemy telegraphs still ticking during hit-stop and fixed it; it also changed hit-stop to be paid out of the attacker's recovery instead of added on top.)
5. Hit-stop lives in the sim because bots must feel the same game the player does; otherwise balance numbers describe a different game.

## 2. Screen shake (render side)

A noise offset (30 Hz value noise) with amplitude decaying quadratically to 0. Directional shakes bias 70% along the hit direction.

| Event | px at 1080p | ms |
|---|---|---|
| Light / medium hit | 0 | n/a |
| Heavy hit | 4 | 120 (directional) |
| Crushing hit | 8 | 180 (directional) |
| Hero takes damage | 6 | 150 (from the source) |
| Explosion | 6 | 200 |
| Boss slam | 10 | 250 |
| Boss phase break | 14 | 400 |
| Hero death | 8 | 300 |

Concurrent shakes take the max amplitude, not the sum. Slider 0-100% (default 100); "Reduce motion" sets 30% and disables slow-mo zooms.

## 3. Rumble

`Gamepad.vibrationActuator.playEffect("dual-rumble", { duration, weakMagnitude, strongMagnitude })`, feature-detected and silently skipped elsewhere.
A bonus, never the only feedback (Firefox has none; a DualSense on Windows Chrome likely gets none). A new effect replaces the current one only if its strong magnitude is greater or equal.
Examples from the table: light hit 40 ms weak 0.25; heavy 90 ms weak 0.4 strong 0.5; crit 60 ms weak 0.6 strong 0.2; hero damage 160 ms weak 0.5 strong 0.7; low-HP heartbeat (under 25%) two 60 ms pulses 140 ms apart every 1,000 ms at strong 0.25; hero death 700 ms at 1.0/1.0; boss kill 600 ms.

## 4. Input

| Rule | Value |
|---|---|
| Buffer | **150 ms** for attack, special, cast, dash, ultimate. A buffered press fires on the first legal tick |
| Buffer priority, same tick | Dash > Ultimate > Special > Cast > Attack |
| Hold threshold | a press held >= **200 ms** is a hold (brace, charge shot) |
| Dash-attack window | attack during a dash or within **100 ms** after it |
| Cancels | dash cancels anything; special/cast cancel an attack's recovery after 40%; movement cancels recovery after 60%; chained combo hits skip recovery |
| Dash-through | passes through enemy bodies, low walls, low props; ends without a pop if it finishes inside one |
| Corner correction | within **8 px** of a wall corner you are nudged around it |
| Pit grace ("coyote") | a dash ending <= **24 px** past a pit edge snaps back; walking cannot enter pits |
| Sticks | left radial dead zone inner 0.15 / outer 0.95, rescaled; right 0.25 / 0.95; aim uses the right stick above 0.5 deflection |
| Aim assist (pad only, toggle, default on) | melee snap within +-12 degrees and 600 px; ranged/cast +-8 and 1,100 px; never through a wall |
| Menus | ignore input for **250 ms** after a choice screen opens; destructive actions need a 1 s hold |
| Pause | instant, freezes the sim; unpausing has a 200 ms grace where enemies do not advance telegraphs |
| Auto-pause | on tab hidden, blur, leaving fullscreen mid-run, active pad disconnect: pause, clear held and buffered input, reset rumble, duck audio; on return stay paused |

## 5. Telegraphs

Every enemy attack shows BOTH a body wind-up and a ground decal, for the full telegraph time.
- Decal: outline appears at start; a fill grows from the origin (lines outward from the enemy; circles from the centre) and reaches the edge **exactly** at telegraph end; the last **120 ms** flash the outline; then the hit.
- Body wind-up: tint ramps toward white over the last 40% of the time; single-pose enemies also squash to 92% height.
- Projectile preview: a 2 px dotted path, a solid line in the last 300 ms for locked aims.
- Off-screen attacks that will touch the hero get an edge arrow in the decal colour.
- Draw order: floor < your zones < enemy decals < boss decals < characters < projectiles < numbers.
- **Colour is a language:** amber outline + red fill = enemy attack; crimson = boss; silver-white = holy/order; your own zones use the owner's effect colour and are **never red, red-orange or amber**.
- Colour-blind mode adds diagonal stripes to enemy fills; shapes never rely on colour alone.
- A later art direction (black ink on paper) replaced the colours with shapes: ink hatch fills and hard borders. The lesson held: telegraphs are shapes first.

## 6. Hit feedback and numbers

- Enemy hit: white flash 60 ms, knockback, 4-8 particles. Hero hit: red vignette 250 ms, white flash 2 ticks, then alpha pulse at 10 Hz for the 600 ms of i-frames. Low HP: 1 Hz vignette pulse plus heartbeat audio.
- Dash: 4 afterimages and a dust puff; i-frames get no extra flash (the afterimages are the tell). A dash attack gets its own look: forward stretch, tapered streak, crescent at the tip.
- Damage numbers (toggle, default on): normal 22 px, crit 30 px gold with a 120 ms pop 1.3 to 1.0, status tick 16 px, heal 22 px green with "+", damage taken 26 px red, blocked 18 px grey with the word. Rise 40 px over 600 ms, 2 px dark outline.
  **Merge numbers:** hits on the same target within 300 ms add into one number that re-pops.

## 7. Camera

Orthographic 3/4 view, zoom 1.0 shows 1920x1080 world px. Follow lerp 0.18 per tick, snaps on room entry. Lead: pad 80 px toward aim; mouse 25% of hero-to-cursor, capped 160 px.
Clamp to room with a 2-tile margin; boss rooms zoom 0.9; round the camera position after shake (no shimmer). Interpolate every entity AND the camera from the sim (`prev + (cur - prev) * alpha`);
never interpolate across a teleport or room change.

## 8. Beats (sequenced moments, in ms)

- **Room clear:** killing-blow hit-stop, 150 ms slow-mo at 30% speed, a chime, music low-pass (20 kHz to 800 Hz over 400 ms) with -6 dB, reward falls in with a 400 ms bounce; music opens back over 600 ms when the next room starts.
- **Choice screen:** world dims 40% over 150 ms, cards deal in 60 ms apart, input accepted from 250 ms.
- **Boss intro:** door seals, camera pans over 600 ms, name card 1,200 ms, camera returns 400 ms, boss music, skippable after first view.
- **Boss phase break:** 250 ms global stop, 14 px shake, flash, 1.5 s invulnerable roar, projectiles cleared.
- **Boss death:** 400 ms global stop, 1.5 s slow-mo at 25% with zoom 1.1, 100 ms white flash, dissolve over 2 s, victory sting, rewards drop.
- **Hero death:** 300 ms global stop, rumble 700 ms, 800 ms slow-mo at 20% with desaturation, hard cut to black, a compact summary card at ~2.4 s. Death without a menu wall: the dash skips it.
- The first version of the clear beat hid the HUD for a 0.5 s hero freeze, reward reveal at 750 ms, drums low-passed and dipped -7 dB (tuned in play).

## 9. Receipts: what the feel work actually found

- **Playtest first impression:** idle animation "jitters", bosses "too big, blown-up pixels", gifts invisible on attacks, walking through tables. Fixes: idle hysteresis, static pose plus breath, boss size fields (bosses 1.2x hero, hitbox radii shrunk), a per-gift visual language (an audit found all 126 gift x verb cells scored below 2 on a 0-3 visibility scale, 45 of them zero; after the pass 84 cells scored 3).
- **"Doorways don't line up with walls; fade walls when the hero is behind them."** Root cause: east/west doors drew a north arch straddling floor and wall. The occlusion fade first rendered as a hard rectangle, then as a soft radial window (RenderTexture erase, ~56 px falloff, 35% alpha over 120 ms), and cost a stall until pooled.
- **Perf is feel.** A 60-100 ms hitch from first use of a shader reads as a missed input; see `references/phaser4-traps.md` section 4.
- **Bots were the feel instrument and they were wrong first.** About 20 bot bugs were fixed in one balance pass, including: 44% of damage was the bot's own dash-attacks, the basic bot attacked right after its dash and ended its own i-frames, and a 900 s run cap made a skilled bot read 0% instead of 45%.
  Bots read sim state directly and are deliberately handicapped by tier (reaction-time medians 430 / 330 / 250 ms for novice / average / skilled, plus a missed-telegraph rate) so "skilled" is not "perfect".
- **Do not tune by taste with a metric.** "Does it feel good" is a human call: label it NEEDS OWNER, attach clips, bring options. A numeric complaint ("too small", "too slow") gets a numeric target from the owner first.
