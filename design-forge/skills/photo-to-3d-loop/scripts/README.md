# The photo-to-3D harness

Seven scripts that drive a Blender modelling loop from reference photographs: render fixed
views, measure the silhouettes against the photos, and gate each round on whether the
numbers actually improved. The method they serve is in `../SKILL.md` — read that first.
This file is how to run them.

They are the working harness from a real twenty-round build, moved here largely unchanged.
**The comments are load-bearing.** Nearly every non-obvious line carries a note recording
what it cost to learn, and several of them are the only reason a plausible-looking wrong
number was ever caught. Don't tidy them away.

---

## Two hard prerequisites

**1. Blender, running, with the COMMUNITY MCP bridge on `127.0.0.1:9876`.**
The scripts do not launch Blender and cannot. They open a socket to a live GUI instance and
execute `bpy` inside it, which is what makes scene state persist between iterations.
🔴 Port **9877 is the OFFICIAL addon and has no `execute_code`** — it will connect and then
fail to do anything. Verified against Blender 5.2.0 LTS.

⚠️ **One bridge, one scene, one worker.** `driver.py iterate` resets that shared scene every
round, so two of these running at once overwrite each other and produce plausible wrong
numbers rather than an error. Both ends of the socket are pinned to 9876 (`driver.py:40`, and
the addon's own default), so a second bridged instance is not a supported path. `../SKILL.md`
documents the headless alternative — `blender --background`, 1.45 s and 370 MB per render —
which removes the shared state entirely.

**2. `magick` (ImageMagick 7) and `ffmpeg` on PATH.**
All measurement is ImageMagick shelling out; `ffmpeg` encodes the turntable only. Note
ImageMagick 7 has no bare `convert`. Verified against ImageMagick 7.1.2 and ffmpeg 8.1.

Beyond those, the host side is **pure Python standard library** — no numpy, no Pillow.
Developed on macOS with Python 3.13.

Check all of it in one call, before anything else:

```bash
cd /path/to/your/project
python3 "${CLAUDE_PLUGIN_ROOT}"/skills/photo-to-3d-loop/scripts/driver.py check
```

That prints both ports, the Blender version across the bridge, the project root it resolved,
and whether `refs/`, `renders/` and the label font are where it expects.

---

## 🔴 Run from your project root

Paths are anchored to the **current working directory**, not to the scripts. `refs/` and
`renders/` are resolved as `./refs` and `./renders`.

This changed when the harness was packaged. Originally these lived inside the project they
served (`<project>/code/`) and anchored to `__file__.parent.parent`; installed in a plugin,
that anchor resolves to the plugin's own directory, which would hunt for `refs/` inside your
Claude plugin folder and write every render and `.blend` snapshot in there. So: `cd` to the
project first, or set `P23D_ROOT`.

Expected project layout:

```
your-project/
  refs/            # the reference photographs — you supply these
  renders/         # created for you; one subdirectory per version tag
  model_v1.py      # your Blender build script — you write this
```

### Environment variables

| var | default | when you need it |
|---|---|---|
| `P23D_ROOT` | the cwd | running from somewhere other than the project root |
| `P23D_FONT` | macOS system Arial | **any non-macOS host** — an absent font makes the contact sheet and overlay labels exit 1 having written nothing |
| `P23D_TMP` | `/tmp/p23d` | two projects scoring at the same time, which would otherwise share scratch |

---

## The seven scripts

| script | what it does |
|---|---|
| `driver.py` | The bridge. Reset, studio, the fixed-view camera rig, render, alpha masks, contact sheet, `.blend` snapshot. Everything else imports it or depends on its output. |
| `measure.py` | Silhouette W:H. Alpha matte for renders, threshold + fuzz-sweep for photos, band-by-band profiles. |
| `overlay.py` | Red/blue silhouette difference map plus IoU. The most informative single artifact in the loop. |
| `loop.py` | Scoring, the verified acceptance gate (`judge`), and a deterministic oscillation monitor (`trend`). |
| `analyze_refs.py` | Photogrammetry on the photographs themselves: section extraction, in-plane roll by PCA, corner circle fits. |
| `fit_camera.py` | Freeze the mesh, move only the camera. The mesh-or-rig diagnostic. |
| `turntable.py` | Seamless orbit render, EEVEE or Cycles, with a numeric motion check. Deliverable only. |

`score.py` from the original project is deliberately **not** here. It was a superseded first
attempt at scoring; `loop.py` is the live gate.

## The order you use them in

**Once, at the start of a project:**

```bash
python3 .../driver.py check                  # prerequisites + which project
python3 .../analyze_refs.py roll             # in-plane roll of each photograph
python3 .../analyze_refs.py section          # the real profile section, as a curve
```

Then **smoke-test the whole path on a plain box before modelling anything.** Doing that on
the original project found two real harness defects on day one. After it passes, a bad
render can only be the model's fault.

**Every round after that:**

```bash
cp model_v20.py model_v21.py                       # ALWAYS fork; never edit a shipped version
#   ... one coherent set of changes to ONE named component ...
python3 .../driver.py iterate v21 model_v21.py     # reset, run, render, contact sheet, snapshot
python3 .../driver.py masks v21                    # alpha-matte pass — what gets scored
python3 .../loop.py score v21                      # per-view IoU + W:H error
python3 .../loop.py judge v21 v20                  # ACCEPT or REJECT, with reasons
python3 .../overlay.py v21                         # red/blue silhouette difference map
python3 .../loop.py trend                          # per-view history + oscillation flags
```

**Occasionally, when a view will not converge and you need to know whether the mesh or the
rig is at fault:**

```bash
python3 .../fit_camera.py focal        # pin focal on the views whose pose is NOT in dispute
python3 .../fit_camera.py pose 160     # only then search pose on the disputed ones
```

**At the end:**

```bash
python3 .../turntable.py v21 --cycles --name widget
```

---

## What a new project must change

Three things, and only the first is subtle.

**1. The view rig — `VIEWS` in `driver.py`.** Seven named views with a fitted
azimuth / elevation / roll and the reference photo each is judged against. What ships is the
rig for one specific device, kept concrete because a worked example is more use than a blank
template. The header comment above it documents every field and the order that actually works
for fitting a new one.

🔴 **The mapping is declared in THREE places and nothing keeps them in sync:**
`driver.VIEWS`, `measure.VIEWS`, and `overlay.PAIRS`. `loop.py` iterates `overlay.PAIRS` to
decide what to score, so a view missing there is a view that never gets judged. A mapping
that disagrees between files scores a render against the wrong photograph and the numbers
stay entirely plausible — which is precisely the failure this whole harness exists to catch.

**2. The reference photographs — `refs/`.** Before round one: md5 the set (two of the seven
on the original project arrived byte-identical), and confirm each image is the view you think
it is **by looking at it, not by its filename**. A single mislabelled reference cost four
rounds and generated a phantom −56% error that a critic dutifully reported as a model defect
every time. Don't invent a column for a view you have no photograph of.

**3. The model script — `model_vN.py`.** Yours entirely; the harness only ever reads it and
executes it into a clean scene. `driver.py iterate` takes its path.

Also project-specific, and less subtle: `fit_camera.PHOTO_ROLL` / `KNOWN_POSE` / `DISPUTED`
(all three describe one device), and the `corners` / `bezel` readers at the bottom of
`analyze_refs.py`, which look for a rounded rectangular faceplate with one dark inset panel.
`gray_mask`, `rowspans`, `colspans`, `section`, `roll` and `fit_circle` in that file are
general and transfer as-is.

---

## Verified and unverified

**Verified here:** all seven import cleanly from an arbitrary working directory; `ROOT` and
its `refs/` and `renders/` resolve to the cwd; the three view-name lists agree; and
`driver.py check` runs against a live Blender 5.2.0 LTS bridge and correctly reports a
missing `refs/`.

**Not verified here:** no end-to-end round was run. That needs reference photographs, a model
script and a rendering Blender session. The rendering, scoring, camera-fitting and turntable
paths are carried over from a project where they ran for twenty rounds, but they have not
been re-run since being moved, and the acceptance-gate thresholds (`GOOD = 0.90`,
`TOL = 0.010` in `loop.py`) were tuned for that object and are a starting point, not a law.
