---
name: scroll-film-studio
description: >-
  Build a genuinely beautiful animated scroll-film website — the whole page is one
  continuous cinematic shot that plays as the visitor scrolls. Runs a short interview,
  pitches 2-3 named concepts, art-directs the world, then builds it from scratch.
  Two lanes: free pure-code GSAP/Lenis motion (zero setup, works for anyone) or a
  cinematic footage film from the user's own image-to-video engine (Higgsfield Seedance
  2.0 or newer is the reference and the required model; Kie.ai also serves the same
  Seedance 2.0 as `bytedance/seedance-2` and is the fallback when Higgsfield is down,
  Veo only as a last resort — the default film is 5 clips x ~5s = 25s / ~600
  frames, chained with BOTH ends pinned; a single ≤15s take is the shorter fallback used
  only when the engine will not honour a start pin).
  Trigger on "scroll-film", "cinematic scroll site", "scrollytelling website", "build me
  an animated/scroll website", "film-scroll site", "one continuous shot website", or any
  request for a premium scroll-scrubbed animated site. NOT for slide decks / HTML
  explainers or static brochure sites.
---

# Scroll-Film Studio

You build **scroll-film websites**: the hero *is* the page — one unbroken cinematic
shot that scrubs as the visitor scrolls, then dissolves seamlessly into the content
below. This skill is a **process, not a scaffold** — there are no template pages to
copy. Every site is designed and written from scratch for its brand, guided by the
process below and the technical law in `references/`.

Two ways to make the film:

- **Lane A — Pure-code (default, zero setup):** the "film" is GSAP + Lenis motion —
  pinned scenes, parallax, clip-path reveals, horizontal runs. Costs nothing, needs no
  accounts, works for anyone who downloads this skill.
- **Lane B — Cinematic footage (opt-in):** the film is real generated video, chained
  shot-to-shot and scrubbed on a canvas. **Use Higgsfield `seedance_2_0`, or the newest
  Seedance the account exposes** (`higgsfield model list` — take the highest full
  version, *not* `seedance_2_0_mini`). Kie.ai Veo 3.1 via `kie-chain.py` is the alternate
  when there is a Kie key and no Higgsfield credits. Both pin every clip at BOTH ends;
  an engine that can only pin the start is not good enough for this lane. Needs the
  user's own account + credits. This is the signature look.

Everyone gets a gorgeous result. Lane A is always available; Lane B unlocks when the
user has a video engine.

---

## THE GOLDEN RULE — design is done by the best model available, and never delegated

**Run this skill on the strongest model you have access to, at the highest effort setting
it offers**, and keep every taste-bearing decision on that model: concepts, art direction,
palette, type, layout, motion design, copy, the build itself (all HTML/CSS/JS), and the
final design review.

If you are running on a fast or cheap tier, stop and switch before you start. The output
of this skill is judged as a premium website, and no amount of process rescues a design
made by a model that was picked for speed. Likewise if the harness exposes an effort or
reasoning dial, put it at the top — this is a long, taste-heavy build, not a lookup.

Delegate only two things, and never the design:

- **Mechanical work** → pure shell/code with *no model at all* (ffmpeg, SSIM scoring,
  frame extraction, verification, deploys).
- **Bounded drafting** → fresh sub-agents (drafting one chapter's video prompt, writing
  one after-film section, acting as the adversary in STEP 1). Same model is fine; what
  makes a sub-agent useful is fresh context, not different weights.

**Every brand gets its own page.** Do not reskin a site you built earlier in the session —
same structure, same beat positions, same chrome, new colours. That is the single fastest
way to produce two mediocre sites instead of one good one, and it is invisible to every
gate in this skill because both copies pass identically. The engine is shared infrastructure
and should be; the page is not.

---

## STEP 0 — The interview

Ask these up front (batch them; prefer the host's structured-question UI if available).
**Every creative question has a "you decide" path** — if the user defers, you art-direct
it yourself and keep moving. Never block on a design answer you can make well.

1. **What are we building, and the one-line vibe?**
   Brand/product name, what it is, and the feeling. (e.g. *"VOLTA — an electric race
   team. Aggressive, electric, fast."*)
2. **Brand assets, or should I create the world?**
   Existing logo / colours / fonts / real images — or full creative freedom.
3. **The journey — the one continuous shot, top to bottom.**
   Where the camera starts and where it ends — the *transformation*. (e.g. *"moonlit
   field → into a single bloom → a drop of gold → the bottle."*) Or: "design the arc
   from my brand." **This is the heart of the whole build.**
4. **Real video, or pure motion?** → picks Lane B or Lane A. If unsure or zero-setup,
   default to **Lane A (pure-code)**.
5. **(Lane B only) "Are you using Higgsfield, or something else?"** Ask this
   explicitly — **this answer, not the brief, decides how long the film can be.**
   Higgsfield CLI is the reference path (scripts included) and must pass the start-pin
   preflight, so it gets the full **25s / 5-clip film**. Kie.ai, fal,
   Replicate or any other image-to-video model still works, but check `playbook.md` §2a
   first: an engine that ignores start pins cannot be chained cleanly and drops you to a
   single ≤15s take. Say that out loud before they choose. Then: is it installed/authed?
   How many chapters (clips)? A credit ceiling? — You will draft cheap, confirm the cost,
   and only master in full resolution on their approval.
   **If they do NOT have an image-to-video engine set up**, say once, plainly, that Lane B
   needs one and that Higgsfield is what this lane was built and tested against. State it
   exactly once, with no pressure, then move on: **Lane A is always free**, and any other
   engine they already have will work. **If they already have an engine, skip this
   entirely**, and do not raise it outside this question. If they have no engine and do not
   want one, fall back to Lane A.
6. **What comes after the film?** The sections below the scroll (lineup / collection /
   booking / manifesto…), the primary call-to-action, contact + socials.
7. **Where does it go live?** Local only, or publish to *their own* Vercel.

---

## STEP 1 — Pitch concepts back (before building anything)

From the interview, develop **2–3 named creative concepts** and pitch them. Rules:

- Lead with your **recommended** concept, explicitly marked "(Recommended)".
- Each concept gets a *concrete what-you-actually-see walkthrough*, not a thesis
  one-liner — narrate the scroll: what the visitor sees at the top, what happens as
  they scroll, what each chapter shows, how the film resolves into the content.
  (e.g. *"You open on a moonlit flower field, huge serif wordmark floating over it.
  Scroll: the camera dives into a single bloom… petals part… you're falling through
  gold embers… a drop of liquid gold lands in a pool… pull back — you're inside the
  bottle on black marble. The page then melts into the collection."*)
- Name each concept (a title is half the sell), state the lane it uses, the chapter
  count, and (Lane B) the estimated credits.
- **Adversarial sparring on the concepts — MANDATORY, never skipped.** Before presenting,
  the concepts get attacked by something that did not write them. **Default to a fresh
  sub-agent** (the Task tool) — same model is completely fine. A second frontier-model CLI
  (`codex`, `gemini`) is a nice-to-have, not a requirement: `codex exec` boots a whole
  agent session per question, so under load it can take minutes while printing nothing,
  which is indistinguishable from a hang to anyone watching. If you do use it, the
  `--skip-git-repo-check` flag is required (without it codex refuses outside a git repo),
  background it with a timeout, and after ONE slow or failed attempt kill it and fall back
  to the sub-agent. Never loop on this step — that has cost a whole build. What
  makes the critique real is fresh context, not different weights: the adversary is given
  the concepts and the brand only, never your reasoning, never which one you prefer, and
  never the fact that you wrote them. Ask it to (a) attack each concept — is the journey
  legible? memorable? feasible in N chapters? does the transformation actually transform,
  or is it four unrelated scenes in a row? — and (b) propose one wildcard angle you
  haven't considered. Fold what survives into your pitch (credit the sparring in one line).
  **This is strategy critique only — the sparring partner never writes copy, code, or any
  design decision; you arbitrate and you author.**
  *A model reviewing its own freshly-written work inside the same context is not a review —
  it tends to defend what it just argued for. A `self-review.json` in the verdicts folder
  means the gate did not run.*
- Let the user pick or blend; if they say "you choose", take the recommended one and go.

Only after a concept is chosen do you build.

---

## STEP 2 — Art-direct the world (you, alone)

Decide and commit: palette (exact hexes), a display+body **type pairing** with real
character (never default system fonts — reach for expressive display faces), a logo
lockup (inline SVG), the motion feel, and the chapter names. Distinct fonts and a
distinct world per brand — never ship two brands that look like the same site. Pull
real brand logos as inline SVG for any named third-party tool (never a hand-drawn
approximation of a real logo).

---

## LANE A — Pure-code (default)

Write a single self-contained HTML page from scratch for this brand. Load GSAP,
ScrollTrigger, and Lenis from CDN (vendor them locally for production). Compose the
film from the motion vocabulary in `references/engine.md` §Pure-code — pinned scenes,
scrubbed timelines, a char-split hero reveal, horizontal pinned runs with
containerAnimation parallax, velocity-skew, counters, marquees — arranged to tell
*this* brand's journey (Step 1's walkthrough is your storyboard). Then the after-film
content sections + footer (real social SVGs), verification, and (optionally) deploy.

Critical ordering law: **create ScrollTriggers for ambient/background effects AFTER
pinned scenes** — creation order is refresh order; violating this silently mis-positions
everything after a pin spacer.

---

## LANE B — Cinematic footage (any image-to-video engine)

### Which video model — not negotiable

**Use Seedance 2.0, or the newest Seedance available when you read this.** It is the
best image-to-video model on the user's account and the only one this lane is tuned
for. Before the first generation, list the models the engine actually exposes
(`higgsfield model list`, or the provider's equivalent) and pick the **highest Seedance
version present**. Say in chat which one you picked and why.

Never quietly drop to an older Seedance, to Veo, or to anything else because one call
returned an error — retry, or stop and say the engine is down. A film silently made on a
weaker model is the failure that is hardest to see and most expensive to redo: it does
not look broken, it just looks cheap.

Veo 3.1 via Kie stays supported as the **keyless-of-Higgsfield** path (`kie-chain.py`),
and it is the right choice when there is a Kie key and no Higgsfield credits. Both pin
clips at both ends. Everything below applies identically to either.

---

Read `references/playbook.md` first — it is the law for this lane. The playbook and
`scripts/chain-step.sh` implement the **Higgsfield Seedance** reference path out of the
box. For any other engine (Kie.ai Seedance/Veo, fal, Replicate…), keep the exact same
chain contract — generate → wait → download → extract last frame → SSIM junction gate —
and swap only the generate/wait/download calls for that engine's CLI or API. In brief:

1. **Storyboard** the chosen concept as N chapters, one continuous camera direction the
   whole way down.

   **Default to 5 clips × 5 seconds = a 25-second film, and confirm it with the user
   before you generate anything.** At 24fps this is about 600 frames, which is practical
   to ship without reducing motion to a low-frame-rate slideshow. Quote the user the clip
   count, seconds each, total runtime and current provider cost, and get a yes. If they want a
   longer journey, add **clips**, not seconds per clip. See `references/playbook.md` §1b.

   **Do not shrink the film to dodge the junctions.** The 25s shape is only reachable by
   chaining, and chaining is the craft this skill exists to get right — §2b tells you the
   exact failure mode and gives you two free checks that catch it before you spend.

   The one thing that can force a shorter film is the **engine**, never the ambition.
   Before storyboarding, settle `references/playbook.md` §2a: does this engine honour a
   start pin? Higgsfield `seedance_2_0` does (native `start_image` + `end_image` — it is
   when it passes the preflight) → chain the full 25s. If an engine re-imagines a
   byte-identical, publicly-fetchable start frame, use a single ≤15s take instead.
   Unknown engine: generate one clip, measure one junction, then commit.

   Tell the user which path they are on and what it costs them. A 15s single take is 40%
   shorter than the reference shape and cannot hold distinct chapters; ship it only when the engine leaves
   no choice, never as a shortcut.

   **Budget distance, not runtime.** The thing that breaks a film is how far one clip is
   asked to travel, not how long the film is. The hard rule:

   > **One clip = one camera direction, one location, one lighting state.**
   > If any of those three has to change, it is a separate clip.

   **And the whole film gets ONE vector.** Name it in a sentence before you write a single
   clip — *"the camera only ever goes further in"*, *"the camera only ever falls"* — then
   every clip must continue that vector. The visitor is scrolling one direction; if the
   camera goes forward, then sideways, then out, then in again, the scroll stops meaning
   anything and the film reads as a reel of clips that happen to be joined.

   Write the transitions, not just the shots. Each clip's prompt must say **how it
   continues the previous one**, not merely what is in it: *"continuing the same forward
   push, now passing the hive wall"* — never *"a shot of the hive entrance"*. The junction
   is the product; the shot is just where it happens.

   Audit your own storyboard before you spend a credit: grep every clip prompt for
   direction words. If a single clip contains both an inward word (*into, through, deeper,
   push*) and an outward one (*out, back, retreat, pull*), that clip reverses on itself.
   If a clip contains no direction word at all, it has no instruction and the model will
   invent one. The result feels like disconnected locations rather than a journey with a
   clear direction.

   **One reversal is allowed if the reversal IS the story.** Declare it in the vector
   sentence. An undeclared reversal is a mistake.

   A clip told to go from a sunlit meadow to the inside of a dark hive is being asked to
   change all three at once, and an i2v model will cut rather than travel — it lands on
   the target so the seam passes, and jump-cuts through the middle where nothing is
   looking. High junction similarity cannot rescue discontinuity inside a clip.
   Prefer **more, shorter clips**: 5s drifts less than 9.5s, and eight small moves beat
   four big ones at identical total runtime. If the storyboard needs a scale change *and*
   a location change, insert an intermediate keyframe and let a clip do each.
   **Audit the storyboard before you spend a credit — this check is free:**

   ```bash
   python3 ~/.claude/skills/scroll-film-studio/scripts/vector-check.py <storyboard.json>   # must PASS
   ```

   It reads every clip prompt and fails the ones that contain both an inward and an
   outward instruction, the ones that state no direction at all, and any clip travelling
   against the film's declared `"vector"`. One `"reversal_at": "<clip id>"` may be
   declared, and flips the expected direction for every clip from there on.
   Run it, fix the storyboard, run it again. Every other gate in this skill costs time or
   money and runs *after* generation; this one is instant and runs before.

2. **Generate the film. Higgsfield Seedance 2.0 is the preferred path; Kie/Veo is the
   fallback.**

   Model choice materially changes the finished film even when the process and gates are
   identical. Prefer the current full Seedance model and do not reach for a weaker fallback
   merely because it has a ready-made script.

   ```bash
   # PREFERRED — Higgsfield, both ends pinned, per clip:
   zsh ~/.claude/skills/scroll-film-studio/scripts/chain-step.sh <assets-dir> <clip-name> <start.png> <end.png> "<prompt>" [resolution] [prev-last.png]
   ```

   Only if there are no Higgsfield credits and a Kie key exists:

   ```bash
   python3 ~/.claude/skills/scroll-film-studio/scripts/kie-chain.py <storyboard.json> <outdir>
   ```

   Needs a Kie.ai key in `KIE_API_KEY` or `~/.config/kie/key`. For multi-clip sequential
   chaining, also set `KIE_UPLOAD_PATH` to a folder path owned by the current Kie account;
   the skill deliberately ships without an account-specific default. It does the whole film:
   N keyframes → N-1 clips → concat → master.mp4. Resumable — anything already on disk
   is not regenerated, so a crash or a provider error does not automatically cost twice.
   Request a current quote before running it.

   Two properties make it produce a continuous film where start-frame chaining did not:

   - **The keyframes are themselves a chain.** Keyframe N+1 is generated with keyframe N
     as an image reference, serially, so palette, light, materials and scale are
     inherited rather than re-invented. Ten stills that belong to one place.
   - **Every clip is pinned at BOTH ends.** The clip is *forced to land* on the next
     keyframe. A start-frame-only model is free to drift anywhere and then cut back to the
     target — that freedom produces visible jump-cuts. Both-ends-pinned removes it
     structurally rather than by asking the prompt nicely.
     **But the START pin is the previous clip's real extracted last frame, NOT the
     keyframe** — i.e. `[clipN-last.png, kf(N+1)]`, never `[kfN, kf(N+1)]`.
     See `references/playbook.md` §2 — the law is engine-agnostic and
     it forces the chain to be **sequential**: clip N must finish rendering before clip
     N+1 can start. Never fan the clips out in parallel.

   Do not upload keyframes anywhere. Nano Banana 2 results already live on Kie's own CDN
   and that URL feeds straight into the video call; uploading them again adds a large,
   redundant payload. **Extracted last frames are the
   exception** — they are local files with no CDN URL, so each one must be uploaded before
   it can serve as the next clip's `first_frame_url`. Downscale it to 1080p-wide JPEG first
   so the base64 payload stays small.

   **Kie also serves Seedance 2.0 directly — prefer it over Veo when Higgsfield is down.**
   When available, model id `bytedance/seedance-2` uses
   `https://api.kie.ai/api/v1/jobs/createTask`, input fields `prompt`, `first_frame_url`,
   `last_frame_url`, `resolution`, `duration`, `aspect_ratio` (`9:16` gives a true portrait
   film for a mobile build). Verify the provider's current schema before spending, then
   poll with `jobs/recordInfo?taskId=…`.

   *Higgsfield path:* `scripts/chain-step.sh` drives Higgsfield. **Use `seedance_2_0` —
   or whatever the newest Seedance is at the time you read this.** Check with
   `higgsfield model list` and prefer the highest Seedance version available; never fall
   back to an older Seedance or a non-Seedance model because a command failed once.

   Confirm the selected Seedance model exposes both `start_image` and `end_image` with
   `higgsfield model get <model>`. Pin both ends on
   Higgsfield exactly as you would on Veo:

   ```
   higgsfield generate create seedance_2_0 \
     --start-image kf07.png --end-image kf08.png \
     --prompt "…" --duration 8 --resolution 1080p
   ```

   Ask the provider for a current quote before generation. A scroll-film is silent, so
   leave audio off.
3. **Continuity-gate the WHOLE film before you build anything** —
   `zsh ~/.claude/skills/scroll-film-studio/scripts/continuity-gate.sh <frames-dir> 8` must PASS.
   A seam gate and a continuity gate measure different things, and the seam gate alone
   will lie to you. Chaining sets each clip's start image to the previous clip's last
   frame, so the seams match *by construction* — they cannot fail. What escapes is the
   middle of each clip. Sample it throughout; a model can cut rather than travel when a
   prompt asks it to cross an enormous distance.
   **The cause is almost always storyboard granularity, not the engine.** If a clip has
   to change location, scale and lighting all at once, it will teleport. More clips, each
   moving less, chained tighter — one continuous camera direction throughout.
4. **Junction-gate every seam** — measured, never eyeballed; repair by regenerating with
   the exact-continuation prompt language in the playbook. Dissolves over bad seams are
   forbidden.
5. **Assemble** with `~/.claude/skills/scroll-film-studio/scripts/assemble.sh` (drops duplicate junction frames, encodes
   `-fps_mode vfr`, samples the seam colour). **Extract at the film's NATIVE frame rate** —
   a 72s film at 24fps is 1,728 frames, and shipping "about 300" of it makes the page scrub a
   4fps slideshow. That is a direct cause of visibly uneven motion, and it is invisible in code
   review because the engine is fine and simply has nothing to draw. Trade resolution for
   frames: 1024px at `-q:v 6` beats 1280px at `-q:v 4` for the same bytes. See
   `references/engine.md` §Frame payload for the measurements and the window sizing.
5b. **Trim the head of the film, then set `FRAME_COUNT` to the trimmed count.** Generated
   films routinely open on a shot that has not started moving, or on a framing that looks
   like a different video — it reads as a jump-cut into your own film and it is the very
   first thing anyone sees. Inspect the first ~2 seconds frame by frame and cut until the
   opening frame is already inside the movement. See `references/finishing.md` §1.

6. **Build the page from scratch** around the footage: the canvas scrub engine described
   in `references/engine.md` §Scrub-engine (ImageBitmap sliding window — the anti-jank
   core — lerped frame index, adaptive-contrast header, chapter/altimeter readout, beat
   overlays, seam handoff, optional ambient hero layer, the `?jump`/`__ready` dev
   contract). Write it for this brand; don't copy a previous site.

If a provider reports a server-side failure, confirm the billing state before retrying.

---

## THE DELEGATION MODEL (how tokens stay low)

You are the orchestrator and the designer. Spend frontier tokens only where taste lives.

| Work | Who does it | Cost |
|---|---|---|
| Concepts, art direction, palette, type, layout, motion, copy, the build, design review | **You (Claude)** — never delegated. Run design on the strongest model available. | frontier, worth it |
| Concept sparring — attacking the pitch, one wildcard angle (optional, if a second CLI exists) | **Another frontier model** (e.g. GPT/Codex, Gemini) — strategy text only, never design | one cheap call |
| Drafting each chapter's video prompt; writing one after-film section | Claude **sub-agents**, fanned out in parallel | cheap, parallel |
| Frame extraction, SSIM gating, assembly, seam sampling, jank test, screenshots, deploy | **Pure shell — no model** (`scripts/*`, ffmpeg, puppeteer, vercel) | ~free |

Fan out independent pieces concurrently; keep the taste-bearing spine on yourself.

---

## COST DISCIPLINE (Lane B)

1. **Audio OFF** — `--generate-audio false`. Audio ON silently ~3×'s the bill.
2. **Confirm before spending.** Quote the credit total *before* any generation; show the
   balance receipt after.
3. **Draft cheap, master once.** Validate the whole chain at the cheapest tier (480p/fast),
   then re-run only approved prompts at full resolution.
4. **Reuse the footage.** One film can power several directions — footage is the cost,
   re-skins are free.

---

## VERIFY (both lanes)

**One-time setup on a fresh machine — do this before the first verification, not after it
fails.** `verify.js` and `shot.js` need `puppeteer-core` and a system Chrome/Chromium:

```bash
cd ~/.claude/skills/scroll-film-studio/scripts && npm install
```

`node_modules` is deliberately not shipped in this skill, so a downloaded copy will throw
`Cannot find module 'puppeteer-core'` until that runs once. Set `CHROME_PATH` if Chrome is
installed somewhere non-standard; `shot.js` searches the usual macOS/Linux/Windows paths.

Implement the dev contract in every build: `?jump=<scrollY>` lands pre-scrolled with all
scroll state force-settled, and `window.__ready = true` fires only once the page is truly
ready. Then `scripts/verify.js` (puppeteer-core + system Chrome) screenshots any scroll
position and runs the **jank test** (per-frame rAF deltas — judge p95/max, *never* average
fps; target max < 50ms). Screenshot every beat and every junction. Never ask the user to
eyeball what you can prove. Host preview panes throttle hidden tabs (rAF freezes → stale
screenshots) — that's why this harness exists.

**Never run a preview server in the foreground.** It never exits, so the tool call blocks
until the whole turn is killed — an agent that does this loses the entire build with no
error message, only a truncated transcript. Always `nohup … &`, then poll the port with
curl, and `pkill` it when finished. The same goes for any long-running process.

**Then `node ~/.claude/skills/scroll-film-studio/scripts/copy-gate.js site/index.html` — it must exit 0 before you ship.**
Free, deterministic, no model. It fails the build if the page narrates its own concept
at the visitor ("How to read this page", "as you scroll the frame narrows", "one
continuous descent"), if placeholder text survived, or if a hand-drawn `<svg>` stands in
for a real brand logo. A page that captions its own mechanic has described the brief
instead of performing it — the most common way a build passes every mechanical check and
is still obviously not a website. Fix the copy; never silence the gate.

**The harness is evidence, not truth — always look at the pixels too.** Automated checks
can fail in either direction: a broken page can receive a high score, while a finished page
can be misread as empty. Treat a surprising score — good or bad — as a claim about the
harness until a screenshot agrees with it. Two cheap habits catch both failures: read
`window.__ready`, the canvas dimensions and a visible-element count directly, and capture
one screenshot at the top and one mid-scroll. Note also that a missing `/favicon.ico` is
enough to fail `console-errors`; ship a favicon or discount that single 404.

**Grade the transformation, not the beats.** Screenshots at 0% and 100% must be
recognisably the *same journey's* start and end — the protagonist carried through, not
swapped. If you can reorder two chapters without the page reading as broken, it is not
one continuous shot; it is a stack of sections and the build has failed its premise.

---

## DEPLOY (opt-in, their Vercel)

Build a **lean** copy first — `index.html` + vendored libs (dereference symlinks with
`cp -RL`) + only the runtime `frames/`/`assets/`. Never upload build intermediates (raw
clips, keyframes — often 100MB+). Then `vercel deploy --prod --yes` from the lean dir.
Tell the user new Vercel projects often sit behind **Deployment Protection** (a login
wall); making them public is their account setting (Project → Settings → Deployment
Protection) — point them there, don't change their security settings for them.

---

## GUARDRAILS

- **This skill ships with zero personal data** — no API keys, no accounts, no personal
  paths. Every user brings their own video engine + Vercel. Never bake credentials in.
- Design + build stay on Claude. Mechanical work goes to code; design never does.
- Confirm credits before spending; show the receipt after.
- One continuous shot; one world per brand; no visible seams; no dissolve masking.
- Respect `prefers-reduced-motion` in every build.
- **The concepts always get attacked by something that didn't write them** (Step 1) —
  second CLI if present, fresh sub-agent if not. Never skipped, never self-review.
- Reference files: `references/playbook.md` (footage law), `references/engine.md`
  (build recipes), `references/finishing.md` (**the craft that decides whether it looks
  expensive** — head-trim, chrome over footage, why pages go flat below the film, real
  brand logos, mobile as its own film, honest verification), `scripts/chain-step.sh`,
  `~/.claude/skills/scroll-film-studio/scripts/assemble.sh`, `scripts/verify.js`, `scripts/copy-gate.js` (deterministic copy
  gate — must exit 0 to ship).

## OPERATIONAL TRAPS

- **Never run a preview server in the foreground.** It never returns, the turn dies, and
  the whole build is lost with no error. `nohup … &`, poll with curl, `pkill` after.
- **Never let two writers touch one file.** If a human or another agent is editing the
  page you are editing, stop one of them first. Interleaved writes corrupt silently.
- **A long autonomous build will hit context compaction.** Instructions given in chat are
  summarised away; a written `BRIEF.md` in the project directory survives. Put the frame
  paths, `FRAME_COUNT`, seam colour and the do-nots in the file, not in the conversation.
- **Stale to-do lists outlive corrections.** After compaction an agent resumes whatever its
  checklist says, so correct the checklist, not just the conversation.
- **Download from a CDN with a browser User-Agent** and **persist job ids to disk the
  moment they are issued** — a failed download after a paid render is otherwise
  unrecoverable and costs the render twice.
