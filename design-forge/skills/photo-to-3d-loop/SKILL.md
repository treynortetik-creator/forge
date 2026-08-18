---
name: photo-to-3d-loop
description: >
  Model a real object in Blender from reference photographs, by iteration: write a
  script, run it, render fixed views, measure the silhouettes against the photos,
  send a FRESH critic that never saw the build, revise. Carries the acceptance gate,
  the measurement recipes that work on white-on-white product shots, and about
  twenty traps that each cost an hour. Use for photo-to-3D, photogrammetry-by-hand,
  product reconstruction, turntable deliverables, or any build-render-critique loop
  judged against real images. Triggers: "model this from photos", "build this in
  Blender", "photo to 3D", "reconstruct this product", "turntable of this thing".
---

# Photo to 3D Loop

**The one-line case:** twenty rounds against seven photographs took a block-out to **91.9% mean
silhouette IoU**, 95.7% across the four views whose camera pose is actually knowable. Roughly half
of those rounds were spent not on the model but on **discovering that an instrument was lying**, and
every rule below is one of those discoveries with the receipt attached.

> **The division of labour that held for all twenty rounds:** critic for form, ruler for ratios, and
> your own eyes only for *"does this render look like that photograph."* A critic sees what a number
> cannot. A number settles what a critic will confidently get wrong.

This is the 3D sibling of `design-loop`. Same thesis — **judgment stays with the model, arithmetic
goes to a harness** — but the arithmetic here is silhouette geometry instead of CSS, and the
reference is a photograph instead of a bar.

---

## Provenance

Adapted from **VIGA** (arXiv 2601.11109, MIT; repo `Fugtemypt123/VIGA`). Three of its ideas carry
their weight and are non-negotiable:

1. **Pin the reference images OUTSIDE the sliding memory window.** They are the ground truth; they
   must never be the thing that ages out of context.
2. **Always regenerate the COMPLETE script, and make the model state its edit in a diff field that
   is never parsed.** The code *is* the memory. A full regeneration is lossless truncation; the
   unparsed diff field buys minimal-edit discipline without letting a patch apply half-cleanly.
3. **On a crash, feed the FULL traceback back and skip the critic that round.** A traceback is worth
   more than any critique, and there is nothing to critique — the run produced no render.

⚠️ **One VIGA-adjacent idea was deliberately NOT adopted: generating 2-3 candidate meshes per round
and rendering all of them.** By the time the model was good, the silhouette metric was demonstrably
blind to the remaining class of edit, so parallel candidates would have been scored by an instrument
that could not tell them apart. The decisive comparison was visual and needed one render each, not
three. **Revisit this only if your metric can still see your edits.**

---

## The loop, one round

The harness ships with this skill, in `scripts/`. 🔴 **Run it from YOUR project root** — the
directory holding `refs/` and `renders/` — because that is what the scripts anchor their
paths to. `cd` there first, or set `P23D_ROOT`.

```bash
P23D=${CLAUDE_PLUGIN_ROOT}/skills/photo-to-3d-loop/scripts

cd /path/to/your/project                     # refs/ and renders/ live here
python3 $P23D/driver.py check                # bridge alive? which Blender? which project?
cp model_v20.py model_v21.py                 # ALWAYS fork; never edit a shipped version
#   ... ONE coherent set of changes to ONE named component ...
python3 $P23D/driver.py iterate v21 model_v21.py   # reset, run, render all views, sheet, snapshot
python3 $P23D/driver.py masks v21            # alpha-matte pass — what gets scored
python3 $P23D/loop.py score v21              # per-view IoU + W:H error
python3 $P23D/loop.py judge v21 v20          # ACCEPT or REJECT, with reasons
python3 $P23D/overlay.py v21                 # red/blue silhouette difference map
python3 $P23D/loop.py trend                  # per-view history + oscillation flags
```

Then **dispatch a fresh critic sub-agent**, read its report, verify every number in it, and write the
next version from what survived. Append one entry to the build log every round.

**Log rule:** say what changed, what the critic actually said, and what was rejected. *"Improved the
shape"* is a useless entry. *"Camera module was flush with the faceplate; photos show it standing
proud on a dark collar"* is a useful one. The log's whole job is that a fresh session can read it and
not re-derive anything.

### The harness, seven files

They ship with this skill in **`${CLAUDE_PLUGIN_ROOT}/skills/photo-to-3d-loop/scripts/`**, and
that folder's `README.md` carries the run order, the environment variables, and the full list
of what a new project has to change.

| file | what it does |
|---|---|
| `driver.py` | bridge, reset, studio, the fixed-view rig (az/el/**roll**/ref), render, alpha masks, contact sheet, snapshot |
| `measure.py` | silhouette W:H — alpha matte for renders, threshold + fuzz-sweep for photos, band profiles |
| `overlay.py` | red/blue silhouette difference map + IoU. **The most informative single artifact in the loop** |
| `loop.py` | scoring, verified acceptance (`judge`), deterministic oscillation monitor (`trend`) |
| `analyze_refs.py` | photogrammetry on the references: section extraction, in-plane roll, corner fits |
| `fit_camera.py` | freeze the mesh, move only the camera — the mesh-or-rig diagnostic |
| `turntable.py` | seamless orbit, EEVEE or Cycles, with a motion check |

⚠️ **`driver.py`'s `VIEWS` rig is a WORKED EXAMPLE, not a template** — seven views fitted to
one specific device. Keep it as the reference for what a fitted rig looks like, replace the
tuples for your object, and note the mapping is declared in **three** places (`driver.VIEWS`,
`measure.VIEWS`, `overlay.PAIRS`) with nothing keeping them in sync. A mapping that disagrees
between files judges a render against the wrong photograph and the numbers stay plausible.

**Prerequisites, both hard:** Blender running with the **community** MCP bridge on
`127.0.0.1:9876` (port 9877 is the official addon and has no `execute_code`), and `magick` +
`ffmpeg` on PATH. Host side is pure Python stdlib. `python3 $P23D/driver.py check` tests all
of it in one call.

**Smoke-test the whole path on a plain box before modelling anything.** Doing that found two real
harness defects on day one — every view clipping to featureless white, and the object overflowing the
frame at every angle — either of which would have burned critic rounds on lighting notes instead of
geometry. **After the smoke test, a bad render can only be the model's fault.**

### 🔴 One bridge, one scene — and the headless way out

The persistent bridge is the documented default and should stay it: twenty rounds ran on it. But it
means **one Blender, one bridge, one mutable scene**, and `driver.py iterate` opens every round by
**resetting that scene** and rebuilding it from the model script.

**Two concurrent workers therefore destroy each other's work, and the failure does not look like a
crash. It looks like plausible, wrong numbers**, because each worker measures renders of whichever
model happened to be in the scene when its render fired. That is the single most dangerous failure
mode in this whole method — every guard rail in this file exists to catch exactly that class of
silent-plausible error, and a shared scene manufactures it wholesale.

⚠️ **Do not solve it with a second bridged instance.** Both ends of the socket are pinned to 9876:
`driver.py:40` holds `PORT = 9876` as a module constant with no override, and the community addon
auto-starts on the same number (`blender_mcp_community.py:2834`, `port = 9876`; its `blendermcp_port`
scene property defaults to 9876 too, and the `BlenderMCPServer.__init__` at line 47 takes a `port`
argument nobody varies). A second bridge means editing the addon *and* the harness before you have
modelled anything.

**The way out is no bridge at all.** `blender --background --factory-startup --python <script>` —
full process launch, scene build, 512 px EEVEE render, exit — measured on this machine at
**1.45 s wall clock and 370 MB peak RSS.** No bridge, no persistent scene, **no shared mutable
state**: each worker is its own OS process and they physically cannot corrupt one another. This is
also what VIGA itself did, a fresh `--background` subprocess per iteration. The persistent bridge
here was a convenience, never a requirement.

**The ceiling is RAM, not cores.** At ~370 MB per instance, 6-8 concurrent is realistic on a 16 GB
machine and fewer with anything else running. **Check free memory before fanning out**; thrashing is
slower than running serially.

🔴 **Do not half-migrate.** The harness talks to the bridge over a socket. Headless is a *different
execution path* — a script handed to `blender --background --python`, not a socket call. **A worker
that believes it is headless while still calling the socket will silently operate on the shared GUI
scene**, which is precisely the bug headless exists to remove. Migrate fully or not at all.

⭐ **And know what you are buying, because it is less than it looks: Blender is not the bottleneck.**
A render is 1.45 s. The loop is slow because the model and the critic reason slowly. Parallel
headless Blender removes a *collision risk* and buys some wall clock; the real throughput win is
parallelising the reasoning. **Do not re-plumb infrastructure to speed up the fastest part of the
pipeline.**

### 🔴 Parallel component decomposition — the multi-agent pattern

Proven 2026-08-17 on the Guardian Pro (7 workers) and the reason this section exists. **Splitting an
object into components and giving each to its own agent with its own headless Blender is a real
technique, but almost everything intuitive about *why* it helps is wrong.** Read all four parts
before running it.

#### Pick the decomposition mode from the object, not from habit

| Object shape | Mode | Ownership unit | Conflict risk |
|---|---|---|---|
| **Genuinely separate parts** (furniture, assemblies, scenes: a crib's rails / base / legs / mattress) | **One module per part**, each exporting `build(ctx) -> objects`; an `assemble.py` imports and calls them | a whole FILE | **Structurally impossible** — no two workers touch one file |
| **One continuous body** (a moulded device shell) | Marker-block splicing inside a single script | named BLOCKS, `mark.py` inserts boundaries, `assemble.py` splices | real, must be enforced |

⭐ **Prefer whole-file ownership whenever the part boundaries are physically real.** The Guardian Pro
needed block-splicing only because it is one moulded shell — seven workers editing one 1018-line
script, where the bezel's constant sat four lines from the fins'. If your object is an *assembly*,
the file boundary does the safety work for free and you can skip that machinery entirely.

#### 🔴 The acceptance rule MUST change, or the whole run returns a guaranteed null

This is the finding that matters most and it is deeply counter-intuitive.

**Six consecutive verified, obviously-correct changes moved the mean IoU by 0.0pp** — a ×2.3 bezel
radius fix, four tabs becoming real apertures, a restored spine, measured apertures, a corner radius,
a proud lens barrel. Every one is right beside the photograph. Every one is **interior to every
silhouette**.

Six of seven components were interior in four to seven of the seven views. **A gate of the form
"commit only if the global score improves" would have refused nearly every correct edit those workers
could make.** That is not discipline, it is a pre-guaranteed null result.

So split the gate and require **both**:

1. **GLOBAL GUARD (mechanical, do-no-harm).** The mean may not fall more than 0.05pp, and no view
   already at or above 90% may fall more than 1.0pp. **Necessary, never sufficient — print that in
   the tool's own output**, because "the number didn't move" is not evidence of being right.
2. **COMPONENT EVIDENCE (the actual proof), with its method named.** Either a **ruler** — a value off
   the PHOTOGRAPH against the same value queried off the **MESH**, never off a render — or a **fresh
   critic** judging a crop of that component beside the same crop of the photo.

#### Enforce ownership; do not merely instruct it

A read-only instruction is not an enforcement mechanism. **Plant a deliberate trespasser and confirm
it is blocked** before trusting the assembly: on the Guardian Pro a fake `bezel` worker that edited
`FINS_PER_GROUP` was correctly named, diffed and refused. Also verify both safety properties
mechanically, not by inspection:

- **Structural** — stripping the markers back out reproduces the pre-split file **byte for byte**.
- **Behavioural** — the marked file renders and scores **identically** to the pre-split file.

Freeze everything shared: imports, global dimension constants, geometry helpers, materials, and
🔴 **any call ORDER that is load-bearing** (on the Guardian Pro the pocket cut had to run before the
keyholes, because the keyholes are aimed at the pocket floor).

#### Know what you are actually buying — it is NOT throughput

**Measured: 7 workers moved the score +0.033pp, and serial would have finished sooner.** Blender is
not the bottleneck; a 512 px render is 1.45 s. The loop is slow because agents and critics *reason*
slowly.

⭐ **What parallelism genuinely bought was orthogonal questions.** Every defect it surfaced had sat in
plain sight for nine to twenty rounds, and each was found by the one worker whose narrow remit
pointed straight at it — a materials worker nearly cut as out-of-scope discovered that
`paint(body, WHITE)` was a **no-op**. **Decompose to get many narrow questions asked at once, not to
go faster.** Scope the workers so their questions genuinely differ; seven agents asking the same
broad question is seven times the cost for one answer.

#### Capacity: RAM is the constraint, and check it at run time

Each headless instance is **~370 MB peak RSS** (megabytes — a 16 GB machine holds a few, not
hundreds). **6-8 concurrent is the ceiling on an idle 16 GB box, and far fewer in practice**: measured
on 2026-08-18 with 3.3 GB free, the honest cap was **4**. Query free memory immediately before
fanning out and size the pool from the answer — thrashing is slower than running serially.

```bash
vm_stat | awk '/page size/{ps=$8} /Pages free/{f=$3} /Pages inactive/{i=$3} \
  END{printf "free+inactive: %.1f GB -> cap %d blenders\n", (f+i)*ps/1073741824, int((f+i)*ps/1073741824/0.6)}'
```

### The contact sheet is the feedback signal

Each render sits **directly above the photograph taken from the same angle**. That column alignment
is the entire signal. Misalign it and every note the critic writes is judged against the wrong
picture — and it will not look like an error, because the critic is correctly reporting that the
render does not match the photo beneath it.

🔴 **This cost four rounds.** One reference was mapped to a top-down render. It was not a top view;
it was the device **lying on its side**, i.e. a second profile. The column produced a **phantom −56%
error every single round**, an elevation sweep from 25° to 85° was burned looking for a camera angle
that could match it (none can — no elevation of a top-down camera reproduces a profile), and a
"depth conflict" was logged that never existed. With the image stood upright the two profiles agreed
to 2.6%.

**Before round one:** md5 the reference set (two of seven photos arrived byte-identical), and confirm
each image is the view you think it is by looking at it, not by its filename. **Do not invent a
column for a view you have no photograph of** — that is judging a render against nothing.

---

## 🔴 The rules, all earned

### 1. A fresh critic sub-agent every round. Never self-judgement.

> *"AI is not very good at judging its own work, so we don't want the same model creating it that's
> also judging it."*

New agent, no memory of prior rounds, so it cannot defend its earlier verdicts. **No v(N+1) until the
critic on vN lands.** This rule exists because it was broken once, on round two, when the critic was
slow and someone was waiting: the measured ratios that went into that version were real, but the
judgement behind it was the builder marking its own homework.

### 2. Launch the critic WITHOUT write tools, not merely told to be read-only.

A critic once wrote a whole new scoring file into the working tree despite an explicit *"you are
read-only: you write criticism, not code"* in its prompt. **A read-only instruction is not an
enforcement mechanism.** Use an agent type that has no Edit/Write at all (`Explore` works). Then
**audit the working tree at the end of every session** and confirm every changed file was changed by
someone who meant to change it — that audit is what caught it.

### 3. Critic for form, ruler for ratios.

Across twenty rounds, critics were excellent at **everything only eyes catch** and repeatedly wrong
on numbers.

**Only a critic found these** — no measurement would have: a phantom backplate wing · a seam across
the front face · the call to rebuild as one monolithic body · two separately invented flanges · a
mount plate breaking the outline · keyholes modelled as proud spheres when they should be recesses ·
apertures modelled as applied tabs when they should be voids · a lens reading as a glossy ball, then
overshooting to a flat decal · fins buried inside their own backing plate ("the rear has no fins at
all") · a port standing out of the top of the device · the missing port cluster.

**Confidently wrong, every one of them a quantity a ruler settles:** uniform-depth profile · taper
direction · plate W:H · rear fin-field width · spine width · fin pitch (five readings on record
spanning 29%) · heatsink pocket rim height · lens protrusion.

### 4. Make the critic state its METHOD, and cap its findings.

Every report on the project whose numbers survived re-measurement **said how it measured** (circle
fit over 103 sample rows per corner; scanline analysis of the rear silhouette). Every report that
failed verification made **bare assertions**. Asking for the method appears to buy the accuracy, and
it costs one line in the prompt.

The `design-loop` critic disciplines apply unchanged: blind it to authorship, cap the findings so it
has to rank, require a citation for every claim, and never hand it the build transcript.

### 5. 🔴 A critic's number FOR THE MODEL is measured off a RENDER. Yours can be queried exactly.

**Two critics in a row were wrong in this precise way.** One measured the rendered spine at 0.096 W
when the model *builds* it at 0.110 W and the photograph says 0.112 W — the render reads narrow
because neighbouring parts overhang it. The other reported the model's fin pitch from a render at
0.0203 W against a designed 0.0177 W.

**The PHOTOGRAPH half of a critic's ratio is the half worth having.** Check every *"the model is X"*
claim against the mesh before believing it.

### 6. Never build an unverified critic number. Verify first, then build.

Applied consistently this produced three *confirmations* (a bezel corner radius that turned out to be
a ×2.3 model error, two aperture dimensions, a cube corner radius) and one **refutation by an order
of magnitude** — a claimed 0.047 H lens protrusion against a measured 0.004 H, which would have
pushed the lens through a module depth four independent measurements agree on.

⚠️ **Not reproducing a number is not the same as disproving it.** One critic's aperture figures were
logged unbuilt for three rounds because the measurement could not be reproduced — then a better
method reproduced them to within 8% and they were built. **Record WHY the verification failed, not
just that it did**, so the next session starts from the diagnosis instead of repeating the attempt.

### 7. 🔴 A ratio is only as good as the two things it divides.

**Three headline edits were withheld after verification, and each would have damaged a correct part.**
All three are the same failure wearing different clothes — the critic divided two numbers that are
not *of the same thing*:

| what it compared | the actual mismatch |
|---|---|
| model's heatsink **pocket rim** ÷ photo's **fins** | wrong feature. Its ×0.774 edit would have shrunk a correct part 23%, below every photo reading |
| model's **rendered** spine ÷ photo's spine | right feature, wrong source. The design value was already correct to 2% |
| photo's rim at **columns 0.05/0.94** ÷ model's rim at **columns 0.30-0.65** | right feature, **wrong place on the part**. The pocket spans 0.125-0.875 — at column 0.05 there is no rim to measure |

The third is the subtlest and the one to watch for: **the mismatch was in WHERE on the part each
number was taken, not in which part.** *"Which feature is this number of, and where on it"* is
exactly what a confident report will not tell you.

### 8. Never fit a camera AZIMUTH or ELEVATION to make a score match. Roll is different.

It is circular, and it hides model errors by **rotating the defect out of view**. One sweep found an
azimuth/elevation that scored −0.8% against the rig's +13.7% — rendered beside the photograph, the
"better" pose was obviously rotated far past the photo's viewpoint. It was fixing the number by
hiding the defect.

**Fit to the photograph's apparent VIEWPOINT**, chosen by rendering a grid of candidates beside the
photograph and *looking*. A ratio match is a necessary condition, never a sufficient one.

🔴 **ROLL may be fitted.** Roll is presentation, not viewpoint: it cannot change which faces are
visible, so it cannot conceal geometry. Product styling shots are routinely tilted in the image
plane, and that tilt inflates their axis-aligned bounding box; the render should carry it.

⚠️ **Carry the roll on the RENDER and use the photograph exactly as shot.** A camera fitter that
rolled the camera *and* de-rolled the photo left every pair misaligned by twice the roll. It reported
one view's baseline as 74.1% against a true 82.0%, then "recovered" the missing 8 points by swinging
elevation 36°. ⭐ **When a new instrument reports a baseline, check it against the instrument you
already trust before believing anything downstream of it.**

**The mesh-or-rig diagnostic:** freeze the mesh, move only the camera, score full-silhouette IoU
(never a scalar ratio — a great many wrong viewpoints satisfy a scalar). Fit focal length **only on
the views whose pose is not in dispute**; if one focal improves all of those simultaneously, that is
evidence about the *lens*, because their poses were never free parameters. If a bad view snaps into
place with the mesh frozen, the mesh was never the problem. **Its error is then not evidence about
the mesh and must not be spent on the mesh.**

### 9. A reject path is mandatory, and a rejection must be traced to a CAUSE.

A loop that commits every round cannot converge: it trades a solved view for an unsolved one, then
trades back, and the next critic argues about the damage. **Verified acceptance** — commit only if
the global score improves **AND** no view already at or above a "solved" threshold degrades by more
than a tolerance. Rule two is the important half.

**But a gate that fires without a diagnosis is a coin toss with a number attached.** Three overrides
are on the record across twenty rounds and every one carries a falsifiable test:

- The model to copy: the gate rejected on the rear view. The cause was traced to a **perspective
  crossover** (from behind, the near rear face stops being the widest thing subtended and the far
  front face takes over). The arithmetic predicted −4.15% in the linear regime and saturation below a
  computable threshold. **A parameter sweep was actually run** and measured −4.2%, then measured
  identical values on both sides of the predicted saturation point. Four rounds later the crossover
  reversed exactly as the model of it predicts, confirming the diagnosis a second time.
- Twice more, the same species: **a single global IoU number was the wrong instrument for the change
  being judged** — once for a change interior to every silhouette, once for a projection correction
  whose apparent cost was two reference photographs disagreeing with each other.

**An override must ship with the test that explains the regression. An override that is logged
silently is not a reject path.**

**Oscillation monitor:** deterministic, no model call. If a view's error has changed sign twice
across the recorded history, that view is OSCILLATING and more rounds of the same edit will not fix
it.

### 10. 🔴 A human who has physically handled the object outranks every critic and every metric.

**The decisive example, and it is the most important paragraph in this file.** After fifteen rounds
the user said the sides curve inward and the model looked too thick. Both claims were right.

The body had been built as the **intersection of two straight extrusions** — an excellent
construction that got everything else right, because the front silhouette is then exactly the
photographed outline and the profile exactly the photographed section, by construction rather than by
tuning. But a straight extrusion makes half-width **independent of depth**, so every flank was an
*exactly flat plane, by construction*.

**Four rounds of critics missed it. Here is why it matters: from the front, the rear and both
profiles, a flat flank and a convex one cast the identical silhouette.** The metric was structurally
blind to it. An earlier critic had explicitly asked for *"a flat side plane"*, and that half of its
instruction was superseded by a person who had held the part.

His second claim held too. Once the flanks curved, depth was re-measured band by band against both
profile photographs and came out **correct with no change at all** — the model splits the two
photographs in every band of the main body. **The "too thick" read was the flat sides**, exactly as
he had guessed.

Every critic has only ever seen photographs. **Do not require the metric to confirm him before
acting, and do not let a fresh critic talk you out of it.**

⚠️ **The corollary, learned four rounds later.** A later critic said the corrected flank had gone
too far and had no flat interval. It was right about **where** the curvature sits (the rear ~30%, not
the whole flank) and wrong to imply the *amount* should shrink. **Refine the shape on measurement; do
not let it erode the amount he reported.**

### 11. Know what your metric cannot see.

**Six consecutive verified, correct changes moved the mean IoU by 0.0pp** — a ×2.3 bezel-radius
correction, four applied tabs becoming real apertures, a heatsink spine that made the mounts visible
for the first time, measured aperture dimensions, a cube corner radius, a lens barrel. Every one is
visible beside the photograph. Every one is **interior to every silhouette**, and a silhouette
objective cannot arbitrate an interior feature.

**A loop that listens only to that number will refuse correct work.**

So the documented stop condition — three consecutive rounds without the mean improving — has to be
read with a diagnosis attached. Twice on this project the honest reading was not *"the model stopped
improving"* but **"the instrument stopped being able to measure it."** When the remaining error is
(a) two references that disagree with each other and (b) photographs at orientations your rig cannot
reproduce, both sources are **outside the mesh** and no mesh work will move them.

⚠️ **And a metric that does not move is not the same as a metric that is right.** One correction
grew a visible tab off the bottom silhouette and **the rear IoU went UP.** The render is what caught
it.

---

## 🔴 Measurement — where most of the pain was

### Renders: measure the ALPHA matte. Never brightness.

Render with `film_transparent = True` and measure the alpha channel. It is exact and immune to how
dark a material happens to be.

**Brightness thresholding cannot work.** The ground renders at **21% grey** and dark materials are
*darker than the background*, so no cutoff separates them. A brightness threshold returned *"the
object fills every row"* for all ten bands, which is a plausible-looking number describing nothing.

### Photos: threshold against the sweep, and SWEEP THE THRESHOLD.

A white product on a white background is the trap the whole section exists for.

- **A cutoff tuned once on a photo where it worked will eat the object elsewhere.** A 93%
  white-threshold sits **above the white plate's own pixel value**, so the "mask" was a crescent of
  shaded right and bottom edges plus the dark bezel outline. It had been quietly under-measuring for
  ten rounds without ever producing an obviously silly result. **Caught by a PCA on the mask
  reporting +23.3° of in-plane roll on a dead-straight-on elevation photograph.** A number that
  absurd is a gift.
- Swept against an independent low-fuzz trim: 93% was off by 13-25 px on every photo, 97% within
  8 px on five of six, **99% within 4 px on all six, and 99.5% identical to 99% — a real plateau, not
  a lucky cutoff.**
- **At a naive fuzz value the trim eats the device's own body** and silently understates it by ~40%.
  **Four versions were built to that phantom.**

🔴 **On a fuzz sweep, take the LOW-fuzz plateau, not the longest run.** The obvious idea is wrong: the
longest flat run is where the trim has *already* eaten the flanks and settled into a stable lie. Walk
fuzz upward from the conservative end and stop at the **first step that loses more than ~3% of width
or height in one increment** — that step is the trim biting into the subject. Take the median of the
window before it.

🔴 **No plateau means the measurement is not measuring the object.** Report the plateau flag beside
every number so a suspect reading announces itself.

### 🔴 No plateau means no silhouette. Measure INTERNAL features instead.

The sweep above is not just a way to choose a threshold — **it is a go/no-go test on whether the
photograph can support silhouette work at all.** A plateau means there is a real boundary. A smooth
monotonic climb means the threshold is slicing a continuous tonal gradient and **there is no
silhouette to recover**, at any threshold.

Verified on a white crib against a white wall, 2026-08-18. Sampled tones: wall `210,209,205` · back
rail `195,195,185` · slats `179,175,166`. **The object is DARKER than its background and separated by
~15 levels**, the same shape of trap as the white-device-on-white-sweep failure that cost six rounds.
The sweep confirmed it in about two minutes:

```
thresh   60%    64%    68%    72%    76%    80%    84%
fg %    33.7   41.8   48.4   56.6   66.6   82.5   97.7      <- no plateau anywhere
```

⭐ **The pivot, and it rescues the project rather than ending it: the outer boundary is unavailable
but INTERNAL features usually are not.** On the same photograph, a scanline across the slats showed a
local contrast range of **83-115 levels** — five to seven times the object-vs-background separation —
because each slat is bounded by a shadowed gap. Slat pitch, rail heights, post widths and panel
divisions are all recoverable to a few pixels.

**So when the sweep shows no plateau, change instrument rather than pushing harder:**

- ❌ Do NOT build a silhouette IoU loop. It will return confident, meaningless numbers, and every
  guard rail in this file exists to catch exactly that.
- ✅ Measure **feature-to-feature pixel distances** at high-contrast interior edges and drive the
  model from RATIOS (slat pitch ÷ panel width, rail height ÷ total height).
- ✅ Judge form with a **fresh visual critic** comparing render and photo at a matched viewpoint —
  see the critic rules below.
- ✅ Say plainly, in the deliverable, that the model is proportioned rather than measured. **Never
  state a real-world dimension the photographs cannot support.**

### Write the mask out as an image and LOOK at it.

The first bezel measurement returned 314×456 — nearly the size of the whole device, and entirely
plausible. The mask had also caught a **pinhole near the top**, stretching the bounding box
vertically. Re-measured on a crop excluding it: **314×313, square, as expected.**

⚠️ **A photo mask can come back HOLLOW**, because thresholding a white object on a white sweep
catches only its shaded edges and the interior reads as background. An IoU against a hollow outline
is meaningless — it scores a wireframe as a perfect match for a solid. Two fixes, and they are not
alternatives: **raise the threshold until the mask is solid** (this is what the live harness does,
and solidity — filled area ÷ bbox area — is the number that tells you, jumping 0.536 → 0.940 across
the correct cutoff), and if it still leaks, **flood the background in from the border and treat
whatever the flood cannot reach as interior.**

### A single bounding box collapses a wedge and a slab to the same number.

Two views once disagreed by 1.5× on depth and both readings were correct — because the body is not a
uniform slab. **Measure band by band down the height** and the contradiction dissolves into a
profile: thin at the top, deep where the module protrudes, tapering again at the bottom. A third view
that "disagreed with both" turned out to be seeing a blend of the two.

**Report every comparison band by band from then on.** A single ratio is one scalar summarising an
entire outline, so a model can move closer to the photograph *everywhere* and still score worse.

### Extract the real section. Do not describe it.

Threshold the profile photograph and record the **leftmost and rightmost object pixels per row**.
That is the actual outline as a curve, in units of the object's own height, and it beats any prose
description of a section. It is also what makes the strongest construction available:

> **Build the body as the INTERSECTION of two measured extrusions** — the front outline extruded
> along depth, intersected with the side section extruded along width. The front silhouette is then
> exactly the photographed outline and the profile exactly the photographed section, **by
> construction rather than by tuning**, and the corner radii, steps and sweeps all arrive for free.
> Every version before that stacked primitives and tuned parameters, which produced a front outline
> that was the *union* of two boxes with different widths and different corner radii — visible
> "wings" standing proud at the top corners, broken in four of six columns.
>
> ⚠️ **And read rule 10 before you ship it.** This construction's one blind spot is that it makes
> half-width independent of depth, so every flank is exactly flat and no silhouette can see it.

### To isolate a long thin feature, scan the axis it RUNS ALONG and take the MEDIAN down the band.

Two separate sessions failed to measure a set of slot apertures using horizontal scanlines through
the centre — that line reads plate / frame / cube / lens / cube / frame / plate and **never crosses a
flank slot at all**, and the frame, the slot interiors and the lens all sit in the same dark value
band, so luminance alone cannot separate them.

Scanning **along** the slot and taking the median across the band turns a noisy line into a **step
function**: a smooth frame ramp, then a dead-flat plateau (the opening), then a lit inner wall. Two
sharp steps bounding a flat plateau is a distinct surface, not a shading gradient. Third attempt,
first success, and it agreed with an unrelated method to within 8%.

### Calibrate a solver on a KNOWN quantity before trusting it on an unknown one.

One corner radius produced three answers from three methods: **0.033** (dropped an r² term — bad
algebra), **0.185** (a least-squares circle fit whose window held 136 boundary points for a ~25 px
arc, so it was mostly fitting the two *straight* edges — given straight lines a circle fit returns a
large radius and no error), and **0.109**.

⭐ **When instruments disagree, do not arbitrate between them — run all of them against a quantity
whose answer is already known and keep the one that reproduces it.** Run on a radius already settled
at 0.305 by three methods, the corrected solver returned **0.301**. Calibrated to 1.3%, and only then
pointed at the unknown. This was the **third** time on the project that the broken thing turned out
to be the verifier.

### Build a control INTO the measurement.

The scan that moved a keyhole by 0.19 H also crossed **three screws whose positions were already
known to 1.3%**. Same scan, same coordinate frame, same procedure — so the frame is right and the
procedure reproduces known-good features. **Without that control it would have been one more
unverified critic number and would not have been built.**

Two other measurement routes were **thrown away on their own controls**, which is the only reason the
third could be trusted: a centroid-offset method returned 0.221 on a dead-on view where the answer
*must* be zero, and an ellipse-eccentricity fit returned a silhouette **more compressed than a flat
disc**, which is geometrically impossible.

### 🔴 An instrument that works on the PHOTO does not automatically work on the RENDER.

A flank's planarity was verified photometrically on the photographs — a dead-flat luminance run over
tens of pixels can only be a plane — with the saturation objection checked against a surface known to
be planar in the same image. **The identical scan on the render ramps monotonically across a region
the mesh proves is exactly flat.**

The cause is the studio: three area lamps within about one object-radius put a strong gradient across
every flat surface, where the photographs' softbox is large and far. **The rig is a measurement
hazard, not just an aesthetic one.**

⭐ **Verify model-side claims against the MESH, never against a render of it.**

### To find a small protrusion: look for a local bulge in the PROFILE silhouette.

At the feature's own height, on a profile view. **No unknowns, no azimuth to solve.** A 3 px bulge is
0.004 H; a claimed 0.047 H would have been a 34 px bulge and there was not one. That is what refuted
the number by an order of magnitude.

### Never state a real-world dimension the photographs cannot support.

If nothing in the set carries a scale reference, the model is built to **proportion, and proportion
only**. A millimetre figure in a deliverable has to come from the hardware team, not from here.

---

## Blender 5.x and MCP-bridge traps

Every one of these produced a plausible result while being wrong.

**Bridge and scene**

- 🔴 `read_factory_settings()` through the bridge **kills the bridge.** Delete datablocks instead.
- 🔴 **A reset must delete CAMERA and LIGHT datablocks, not just objects, meshes and materials.**
  Left behind, the next `bpy.data.cameras.new("cam")` becomes `cam.001` while `bpy.data.cameras["cam"]`
  still resolves to the stale original. **What that cost:** a focal sweep wrote 450 mm into the stale
  datablock, the framing code computed its distance from 450 mm while the render used the live 160 mm
  camera, and every mask came out at 160/450 = **0.356× scale**. Silhouettes normalise, so the IoU
  scores looked entirely reasonable — they were quietly measured on 138×194 px renders instead of
  390×543 px ones. Caught only by an impossible anomaly: a **rear-only** edit moved the **front**
  view's score.
- ⭐ **Treat "why did that change?" as a stop-and-investigate signal even when the change is in the
  direction you wanted.**
- `bpy.context.object` is always `None` in bridge context. Use `bpy.data.objects`, and set
  `bpy.context.view_layer.objects.active` before `modifier_apply`.
- Engine key is `BLENDER_EEVEE`, **not** `BLENDER_EEVEE_NEXT`.
- `Action.fcurves` no longer exists in 5.x (slotted Actions). Set default interpolation *before*
  inserting keyframes.
- Scene state persists between calls — that is the point, since each iteration edits what the last
  one left. It also means a failed iteration leaves junk behind, so **reset is not politeness, it is
  how iterations stay comparable.**

**Geometry and coordinates**

- 🔴 **Vertex coords in a model script are LOCAL**, and `matrix_world` is **stale** for objects
  created earlier in the same script until `bpy.context.view_layer.update()`. **What that cost:** an
  envelope assert reported the frontmost point as −0.068 H — which is nothing but a ring's own radius
  — against a true −0.112 H. **The safety check could not have failed on a real violation.**
- 🔴 **Sample where the geometry actually IS.** A rounded-rectangle helper emits **no intermediate
  vertices along the long straight flank run**, so a verification band near the centreline contains
  no flank geometry at all — only boolean debris. The check reported `max|x| = 0.016`, a number with
  nothing to do with the thing being verified. Sample at the flank's own vertices.
- **Boolean cutters must not self-intersect.** One merged cutter operand deleted the entire body and
  surfaced 200 lines later as a divide-by-zero on a bounding box. **One boolean per non-overlapping
  group**, asserting the body survived each.
- **Assert that a boolean actually CUT something.** A pass that removes nothing returns the same face
  count and renders perfectly plausibly (162 faces in, 162 out — the cutters were sitting in open air
  behind a pocket floor an earlier pass had already carved).
- 🔴 **But a face-count assert is not sufficient in EITHER direction.** A later pass reported
  `3046 → 3046`, the exact signature of a no-op — and it had cut correctly, because extending a
  circular hole into a slot adds and removes faces in equal number. **Query the mesh**: the recessed
  vertices spanned 0.8918-0.9390 against a designed 0.892-0.939. False positives *and* false
  negatives.
- **Aim a cutter at the LOCAL surface, at the SHALLOWEST point of the feature's own span** — not at a
  flat nominal plane and not at the feature's centre. Where a body sweeps forward, a centre-aimed
  cutter starts *behind* the surface over the lower half of the feature and removes nothing there.
- **A loft that will be intersected must OVERSHOOT the cutting surface**, and the margin is not
  cosmetic. Where the section steps, a ring interpolates linearly across the step and can dip in
  *front* of the true surface, carving a notch out of a body that is correct. Put one ring well
  behind the deepest point.
- **Both end rings of a loft must be at constant depth** so the cap n-gons are planar. A non-planar
  n-gon is exactly the operand shape that makes the EXACT solver return nothing.
- 🔴 **A bevel parameter is not what reaches the outline.** A 0.25 W corner radius rendered as
  0.13 W, because a second bevel pass shaves every remaining edge and takes the delivered radius with
  it. **Build, then re-measure the DELIVERED value off the mesh, and print it every run.**
- 🔴 **Address the object you are USING, never a name that might resolve to something else.** **Five
  separate failures on the project were one identifier pointing at the wrong thing** — a mislabelled
  reference, a mirrored view, a local-vs-world assert, the stale camera datablock, and the flank
  sampling band. Every one produced numbers that were plausible at every step.

**Studio**

- Keep the studio **identical across every iteration.** If the lighting moves, a render that merely
  looks different reads as a model that changed, and the critic chases ghosts.
- **Set exposure and lamp energies low enough that nothing clips.** A first pass at key = 220 W on a
  white subject blew every view to a flat silhouette. Verify numerically, not by eye: per-view mean
  luminance 49-58% at 19-26% standard deviation, where clipped white reads ~100% mean and ~0
  deviation.
- `view_transform = 'Standard'`. **AgX desaturates white plastic to grey.**
- **Derive the framing half-FOV from the real lens and sensor.** A hardcoded 14° against an 85 mm
  lens's true **11.96°** pushed the subject past the frame edges at every angle.
- **Product shots are long-lens.** An unchecked 85 mm inflated every depth:height reading by 1.7-3.8%
  on a subject with heavily rounded top and bottom corners: in profile the vertical extremes sit near
  the centre line and are materially farther from the camera than the flanks, so perspective shortens
  the apparent height. Sweeping 40-450 mm against IoU with the mesh frozen put the plateau at
  160-220 mm. **The proof that this removes a distortion rather than adding one:** at 85 mm the mesh
  rendered 3.2% above its own design value; at 160 mm it renders its true value to within 0.1%.

---

### 🔴 Frame the SUBJECT, not the set

Earned 2026-08-18, and the visible symptom was the least of it.

An auto-framing camera that bounds *every mesh in the scene* breaks the moment the scene gains
anything that is not the subject. Adding an 8×8 floor plane made the camera frame a 16-unit box and
the model rendered **about 30 px wide** — a speck on a grey plane. The same happens with scene
dressing, a backdrop, a light gizmo with geometry, or a measurement proxy left in the file.

⭐ **The ugly picture is the cheap failure. The expensive one is silent:** if framing depends on scene
CONTENT, then two rounds' renders are **not comparable**, because the camera moved for a reason that
has nothing to do with the model. Every before/after judgement the loop runs on is quietly corrupted,
and nothing crashes. A round that "looks closer" may only be framed tighter.

**The rule: framing must be a function of the subject alone, never of the scene.** Tag subject
geometry at creation and frame only tagged objects:

```python
def box(...):
    ...
    ob["subject"] = 1          # every subject primitive is tagged where it is BUILT
    return ob

# in aim():
DRESSING = ("floor", "toy", "backdrop", "proxy")
pts = [ob.matrix_world @ Vector(c)
       for ob in scene.objects if ob.type == 'MESH'
       and ob.get("subject", 0) and not ob.name.lower().startswith(DRESSING)
       for c in ob.bound_box]
if not pts: raise RuntimeError("aim(): no SUBJECT geometry (is anything tagged?)")
```

Tag at construction rather than filtering by name at render time — a name list is a guess about the
future, a tag is a fact recorded by whoever built the object. Keep the name prefixes only as a
fallback for geometry that arrives through some other path. **And raise rather than silently framing
an empty set**: a camera that quietly frames nothing renders a blank image, which reads as a broken
model rather than a broken camera.

⚠️ **Give scene dressing an off switch** (`CRIB_NO_TOYS=1`-style env flag). The reference photographs
almost never contain your dressing, so every comparison render wants it gone while every beauty
render wants it there.

## Environment traps

- **ImageMagick `montage` exits 1 with no font config.** Build tiles with `-resize` / `-extent` /
  `+append` and pass `-font /System/Library/Fonts/Supplemental/Arial.ttf` explicitly.
- 🔴 **`magick ... -combine` consumes exactly THREE images**, one per channel. Feeding it two
  silently yields a greyscale composite that looks like a result and encodes nothing.
- **The shell is zsh:** there is no `timeout`, and `set -- $var` inside a `for` loop misbehaves (it
  bit twice, rounds apart). **Do multi-step measurement in Python**, not in shell.
- **Apple Silicon Cycles is METAL, not CUDA.** Every reference implementation hardcodes CUDA. Set
  `compute_device_type = 'METAL'`, call `get_devices()`, and fall back to CPU on exception rather than
  dying mid-sequence.
- The community Blender MCP bridge is on **127.0.0.1:9876**. Port 9877 is the *official* addon and
  has **no `execute_code`**.
- A "rendered" log line is a claim. **A file on disk above a minimum byte size is the evidence** —
  check it, because Blender will report success and write nothing.

---

## Deliverable discipline — the turntable

- 🔴 **Frame *i* sits at azimuth `360*i/N`, never `i/(N-1)`.** The second form makes frame N a
  duplicate of frame 0 and produces a visible hitch. Verify **loop closure numerically**: the RMSE
  from the last frame back to the first should sit inside the range of ordinary adjacent-frame steps.
- 🔴 **Verify motion numerically.** A silent failure renders N identical frames and encodes a video
  that looks like a still. Compare frame 0 against frame N/4 and require a large RMSE.
- 🔴 **Verify the turntable was rendered from the CURRENT mesh.** One was rendered from a mesh that
  no longer existed after a late correction, and **nothing in the harness flagged it.** Check scene
  identity (face count is enough) immediately before encoding. **If you change the model after
  rendering the turntable, the turntable is stale.**
- **Delete stale frames before a re-run.** Leftovers from a longer previous run silently pad the loop.
- **Assert the frame count before encoding.** Never encode a short loop.
- **Frame the orbit on the bounding SPHERE**, which is rotation-invariant, not on the current
  azimuth's bounding box — otherwise the model breathes in and out of frame as it turns.
- Keep the deliverable render **separate from the loop renders.** Loop renders are throwaway 900 px
  EEVEE frames whose only job is to be judged; this is the thing a person watches.

---

## Phasing: geometry first, materials second

**Forbid all tonal commentary in the geometry critic's rubric, on purpose.** Mixing the two means
lighting notes crowd out geometry notes in exactly the rounds where geometry is what is wrong. Write
a separate materials-and-lighting rubric when geometry closes, and do not blur them.

The corollary is that a clipping or material problem found during phase 1 gets **logged, quantified
and deferred**, not fixed. Measure it so the number is on the record (percentage of pixels at pure
white, per azimuth) and prove it is the material rather than the exposure setting before handing it
over — dropping exposure 1.3 stops moved the worst frame from 16.3% to 6.8%, which is what
established that it is the white material and the light energies.

---

## Ask for the photographs you are missing

At the end of twenty rounds, the largest remaining gaps were **not model defects** — they were views
nobody had:

- **No underside photograph.** Nothing was built there, and nothing should be. **It is unverifiable.**
- **No true top-down.**
- **No square-on rear.** The one rear photo is keystoned (you can see into an upward-facing port
  shelf, which a dead-on shot could not show), and that single fact left three separate questions
  permanently unresolvable.

**Say this out loud early.** Three more photographs would have been worth more than three more
rounds. And when two references genuinely disagree with each other — here, two profile shots
differing by 2.4% on depth — **a single geometry sitting between them is the best any model can do**,
and "fixing" it toward either one is a regression against the other.

---

## Related

- `design-loop` — the 2D sibling: builder plus fresh-context critics, binary verdicts, no scores
- `design-audit` — the same thesis on rendered pages: compute anything expressed as a number
- `art-department` — the visual-deliverable playbook, the Blender/ImageMagick/Inkscape toolchain, and
  the licence gate
