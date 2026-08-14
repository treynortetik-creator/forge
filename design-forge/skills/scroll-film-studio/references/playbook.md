# The Scroll-Film Playbook (Lane B — cinematic footage)

Rules for making the whole page one continuous generated film. These are a
floor, not a ceiling — break them knowingly, never by accident.

## 1. Footage-first law
The film is the source of truth; the website is a player. Design the camera arc first
(one continuous journey, ~5 chapters), then build the page around whatever footage
actually comes back. Never storyboard the site and force footage to match — footage
drifts, copy is cheap to move.

## 1b. The default shape — 5 clips × 5s. Start here, then confirm with the user.

Use this payload comparison as the default planning model:

| | recommended shape | oversized shape |
|---|---|---|
| clips | **5** | 9 |
| per clip | **~5s** | 8s |
| total | **~25s** | 72s |
| frames @24fps | **~600** | 1,728 |
| frames required for native motion | **~600** | 1,728 |
| effective scrub rate if capped at 300 frames | **~12fps** | ~4fps |
| resolution | 1920×1080 | 1920×1080 |
| cost | request current quote | request current quote |

**Propose 5 × 5s = 25s as the default and confirm it with the user before generating.**
Say the number of clips, the seconds each, the total runtime and the credit cost, and
get a yes. Never generate a film shape nobody agreed to.

Why short wins, and it is not taste:

- **A 25s film is about 600 frames. A 72s film is about 1,728.** The page must ship enough
  frames to preserve motion or the scrub degrades in exact proportion. About 600 JPEGs at 1024px is a sane payload; 1,728 is
  not, so someone always "optimises" it down to ~300 — and 300 frames across 72 seconds
  is a **4fps slideshow**. That is the main source of visibly uneven motion. The engine is
  fine; it has nothing to draw.
- **Distance per clip is the thing that breaks continuity.** Five seconds of camera travel
  is a hop the model can actually make. Eight seconds asks it to cross a location, a scale
  and a lighting change at once, so it teleports mid-clip and you get the jump-cut.
- **It is cheaper.** Confirm the current provider quote before generating.

Go longer only when the user asks for it *and* accepts the frame payload. If they want a
longer journey, add **clips**, not seconds per clip — 7 × 5s beats 5 × 7s every time.

---

## 2. Chaining law (flawless joins)

**Use `seedance_2_0`, or the newest Seedance the account exposes.** Run
`higgsfield model list` first and take the highest version. Never silently drop to an
older or non-Seedance model because a call errored — retry, or stop and say the engine
is down.

**THE ONE LAW, TRUE FOR EVERY ENGINE (Higgsfield, Kie, fal, Replicate — all of them):
clip N's start image is clip N−1's ffmpeg-extracted LITERAL LAST FRAME — the actual
rendered pixels — never the keyframe.** Only the far end (`end_image` / `last_frame_url`)
is the next keyframe. The opening keyframe starts clip 1 and nothing else.

### 2a. Which path you are on is decided by the ENGINE, not by the duration

This is the first decision of Lane B and it is the one that decides whether the film is
25 seconds or 15. Get it right before you spend anything.

**The 25s reference shape is the target. It is only reachable by chaining, and chaining only
works on an engine that actually honours a start pin.** So the single question is: does
this engine land on the pixels you pin?

| engine | honours `start_image` / `first_frame_url`? | your path |
|---|---|---|
| **Higgsfield Seedance** | test the current model; require native `start_image` and `end_image` | PATH A when the preflight passes |
| **Kie Seedance/Veo** | provider wrappers can reinterpret pinned frames; measure it | PATH A only when the preflight passes; otherwise Path B |
| anything else | **unknown — measure it** | one clip, one junction, then decide |

**PATH A — the default. Chain to the reference shape.** Follow §1b (5 clips × ~5s), pin **both**
ends of every clip per the command in 2b, and gate each junction in §3. This is the only
way to get the full chaptered journey. Do not shorten the film to avoid the junction work — the junction work *is*
the craft, and §2b tells you exactly how it fails and how to check it for free.

**PATH B — the fallback, and it costs you the back half of the film.** When the engine will
not honour a start pin, chaining cannot produce a clean join at any price, so a single take
is the best available answer — capped at the engine's current maximum duration. Pin the
single take to the opening and final keyframes and write the whole journey as one continuous
move.

Path B is a **rescue, not a style**. It buys continuity by giving up 40% of the runtime and
the ability to art-direct distinct chapters. If Higgsfield credits exist, Path A beats it
when its start-pin preflight passes. Say the tradeoff plainly rather than quietly shipping
the short version.

On either path, write the prompt as one unbroken sentence-chain through the chapters it
covers ("begins on X… falls past Y… continues down to Z"), and on Path B add *"one single
unbroken shot, no cuts, no edits, continuous camera move throughout"* explicitly.

### 2b. Chaining — how to do it, and the trap that makes it fail

Chaining works when the engine honours pinned pixels. Read this section as a preflight,
not as a reason to give up on Path A.

**Do not assume an engine lands exactly on the frames you pin.** Whether you chain
keyframe→keyframe in parallel, or sequentially off each clip's real extracted last frame,
both strategies rest on the same premise: that `first_frame_url` / `start_image` means
*"begin on exactly these pixels."* Some provider wrappers treat the pin as a visual
suggestion rather than a byte-faithful starting frame. This behavior is provider-specific
and must be measured.

The decisive test is simple: extract clip 1's last frame, confirm the uploaded file is
byte-identical and publicly fetchable, then use it as clip 2's start frame. If clip 2 opens
on a visibly different image, the engine re-imagined the pin.

So on this engine a pin is a *suggestion*. Two clips pinned to the same keyframe are two
independent renderings of one idea, which can match each other far worse than either
matches the target. **No prompt, ordering, or upload trick fixes that** — it is why
2a exists. If you must chain, verify on the FIRST junction before paying for the rest.

Sequential chaining off literal last frames remains correct on engines that *do* honour the
start pin. Verify which kind you have — one clip,
one junction measurement — before committing a film's budget to it.

**A prompt that disagrees with the end pin will also break the join.** A common failure is
to use start-keyframe descriptions as motion prompts. The clip then describes where it
already is instead of travelling toward the destination, so it stalls or invents a cut.

> **A clip's prompt describes the JOURNEY from its start pin to its end pin — never the
> state of either end.** *"Continue the same descent and travel toward the dark opening"*
> moves. *"The subject rests at the starting point"* does not.

Two cheap checks before spending, both free:

- **Off-by-one audit.** If the storyboard has N keyframes it has N−1 clips. If your clip
  array is N long, or its entries are named `kf*`, you are about to send keyframe
  descriptions as motion prompts. Print `clip[i].prompt` next to `kf[i] -> kf[i+1]` and
  read them as a sentence: *does this text get me from the first image to the second?*
- **Destination words.** Every clip prompt must name something visible in its END keyframe
  that is absent from its start.

For URL-based engines (Kie et al.) the extracted last frame is a **local** PNG, so it must
be uploaded to get a URL before it can be a `first_frame_url` — keyframes already live on a
CDN, but real last frames do not. Kie's uploader is
`https://kieai.redpandaai.co/api/file-base64-upload` (see `scripts/kie-chain.py:upload`).
Set `KIE_UPLOAD_PATH` to a folder path owned by the current Kie account; never package an
account-specific path.

Each clip's `--start-image` is the **ffmpeg-extracted literal last frame** of the previous
clip — not a lookalike keyframe, the actual pixels. And **pin the far end too**:

```bash
ffmpeg -sseof -0.05 -i clipN.mp4 -update 1 -q:v 1 clipN-last.png
higgsfield generate create seedance_2_0 --prompt "..." \
  --start-image clipN-last.png --end-image kf(N+1).png \
  --duration 5 --resolution 1080p --mode std --generate-audio false
```

**Both ends, always.** Confirm the selected model exposes both `start_image` and
`end_image` with the provider's model-inspection command. A clip pinned at one end only is free to wander and then
cut back to wherever it needs to be, and that cut is the jump the viewer sees. Pinning
both ends removes the freedom structurally instead of asking the prompt nicely.

Only the opening keyframe starts the chain; every later start-image is a
real last frame. Keep one continuous camera direction (always descending / always pushing
in) — reversals read as cuts. Uniform clip length = constant scrub speed.

Request a current provider quote before generating. Audio off — a scroll-film is silent.

## 2c. Reading SSIM without crying wolf

A low score between two frames means **look**, not **fail**. Fast camera motion can drop
consecutive-frame SSIM substantially even when the pixels show a perfectly smooth move.
Sampling every 8th frame exaggerates this further.

Distinguish the two cases by looking at three consecutive samples:

- **Fast motion** — same objects, same light, same world, progressively transformed. Fine.
- **Teleport / cut** — different composition, different lighting state, or an object that
  appears or vanishes. Real failure.

Inside a single generation a true cut is rare by construction; between two separately
generated clips it is the default. Judge junction scores strictly and within-clip scores
generously.

## 3. The junction gate (measured, never eyeballed)
```bash
ffmpeg -i A-last.png -i B-first.png -lavfi ssim -f null - 2>&1 | grep All
```
- **≥ 0.88 pass** · 0.80–0.88 watch it in motion · a true fail is **structural**.
- SSIM under-reads on stochastic texture (clouds ~0.66, embers ~0.72, liquid caustics
  ~0.60 can all be seamless). The number says *where* to look; the side-by-side decides.
- The #1 real failure is **grade/geometry drift** (an invented sunrise, a new horizon).
  Fix by regenerating with: *"Continue the exact same shot from the reference frame,
  identical framing, identical colour grade. Do not change the colour grade."*
- **Dissolves/crossfades over a bad junction are forbidden** — the scrub lets the user
  park on the seam, which exposes the mask instantly. Fix the join, don't hide it.

## 4. Billing truths (verify by balance delta, not docs)
- `--generate-audio false` is *the* cost lever — audio ON silently ~3×'s the bill.
- Confirm the current price ladder with `higgsfield generate cost` before quoting.
- **Draft the whole chain at 480p/fast to validate, then re-run approved prompts at
  1080p.** A regen at draft tier costs a fraction of a full one.
- If a job fails server-side, confirm the billing state before retrying the same call.

## 5. Assembly
- Concat dropping the duplicate junction frame (`select='gte(n,1)'` on clips 2+), and
  **always `-fps_mode vfr`** on the master encode — default CFR sync pads ~5 dup frames per
  junction = frozen scrub zones.
- Extract **every frame** at the film's native rate — a 25s/24fps film ships all
  **601** JPEGs — at **1024px, `-q:v 6`**. Never decimate: halving the frames halves
  the scrub to 12fps and is the fastest way to make a correctly-shot film feel cheap.
  If the payload is too heavy, reduce **width and quality, never frame count**.
- Sample the final frame's edge colour → the seam hex for the film→content handoff.

`scripts/chain-step.sh` and `scripts/assemble.sh` do all of this.

## 6. The scrub engine (why it's jank-free)
- **Canvas + pre-extracted JPEGs**, never `<video currentTime>` scrubbing (seek stutter).
- **ImageBitmap sliding window**: `drawImage(HTMLImageElement)` forces a *synchronous* JPEG
  decode on first paint (and after cache eviction) — that decode spike *is* the frame-by-
  frame jank. `createImageBitmap` decodes off-thread; keep a window of decoded bitmaps
  around the playhead (±18 ahead, evict/close beyond ±28) so every draw is a pure GPU blit.
- Lerp the frame index (`current += (target-current)*0.14`) for butter. Cap DPR at ~1.5.
- Lenis smooth scroll; a concurrency-capped image pump; `nearestFrame()` fallback so a
  missing frame never blanks the canvas.
- **Measure jank with rAF deltas (p95/max), not average fps.** Target max < 50ms.

## 7. Chrome, seam, and the ambient layer
- **Adaptive header**: sample the drawn frame's top strip luminance (~every 180ms) → toggle
  a `.on-light` class. Fixed chrome over changing film can't be one hard-coded colour.
- **Seamless handoff**: start the next section's background gradient at the *sampled* final-
  frame colour. No visible line between film and content.
- **Ambient hero layer** (optional, free): sprite-based canvas particles themed to the world
  (snow glisten, gold pollen) over the static first frame, fading out across the first ~7%
  of scroll — the hero feels alive before the scrub starts. Use one offscreen radial-gradient
  sprite + `drawImage` per particle (never `shadowBlur`); stop rendering entirely at alpha 0.
- Film grain + vignette sell the "one shot" feel; fade both out with the handoff.

## 8. Verification harness
Host preview panes throttle hidden tabs (rAF freezes → stale screenshots). The reliable path:
puppeteer-core + system Chrome + a page dev-contract:
- `?jump=<scrollY>` → land pre-scrolled and force-settle all scroll state.
- `window.__ready = true` only after frames are decoded and settled.
- Capture: `goto → waitForFunction(__ready) → wait ~1200ms → screenshot`. Shoot every beat
  position *and* every junction. Hide any cursor-follower until first real mousemove or it
  photobombs captures at 0,0.

`scripts/verify.js` does capture + jank-test.

## 9. Governance
Design taste and design code are done by the Claude model only. Mechanical steps (ffmpeg,
SSIM, puppeteer, vercel) are pure code — no model. Quote credits before spending; show the
receipt after. One continuous shot, one world per brand.
