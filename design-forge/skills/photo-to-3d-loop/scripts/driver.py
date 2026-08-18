#!/usr/bin/env python3
"""Harness for the photo-to-3D modelling loop.

This is the un-opinionated half: talk to Blender, render the model from fixed angles,
and lay those renders out next to the reference photos so a vision model can compare
them in one look. The opinionated half — what the critic is asked and how the loop
decides to stop — lives in loop.py.

Blender runs as a GUI app with the community MCP bridge listening on 127.0.0.1:9876.
Code is executed with `bpy` inside that live instance, so state persists between calls;
that is the whole point (each iteration edits the scene the last one left behind), but
it also means a failed iteration can leave junk behind. reset_scene() is therefore not
optional politeness, it is how we keep iterations comparable.

Run these from your PROJECT root — the directory holding refs/ and renders/ — not from
the plugin directory they are installed in. See the ROOT note below.

    python3 driver.py check                 # bridge up? which port? which project?
    python3 driver.py exec model_v1.py      # run a model script into the live scene
    python3 driver.py render v1             # render every view in the VIEWS rig
    python3 driver.py masks v1              # alpha-matte pass, what loop.py scores
    python3 driver.py sheet v1              # contact sheet, renders vs references
    python3 driver.py iterate v1 model_v1.py    # reset, run, render, sheet, snapshot
"""
import base64, json, os, pathlib, socket, subprocess, sys

# 🔴 PROJECT ROOT — the one thing that had to change when this harness was packaged into
# a plugin. These scripts were written to live INSIDE the project they served
# (<project>/code/), so the anchor was `__file__.resolve().parent.parent` and everything
# downstream came for free. Installed as part of a plugin that anchor resolves to the
# PLUGIN's own directory, which means refs/ would be looked for inside the plugin and
# every render and .blend snapshot would be written into it. Same class of defect as the
# stale-camera-datablock bug below: an identifier that still resolves, to the wrong thing.
#
# So the anchor is the current working directory. Run from the project root, or set
# P23D_ROOT to point at it. Every other script in this folder uses the same rule.
ROOT    = pathlib.Path(os.environ.get("P23D_ROOT") or pathlib.Path.cwd()).resolve()
REFS    = ROOT / "refs"
RENDERS = ROOT / "renders"
PORT    = 9876          # community addon. 9877 is the OFFICIAL addon and has no execute_code.

# ============================================================================
# THE VIEW RIG — ⚠️ THIS IS A WORKED EXAMPLE. REPLACE IT FOR YOUR OWN OBJECT.
# ============================================================================
# What survives below is the rig fitted to ONE device across twenty rounds against seven
# photographs. It is kept concrete rather than blanked to a template because every field
# here was argued over, and the comments record what each mistake cost. Your object will
# have different photographs, a different number of them, and different poses. Swap the
# tuples; keep the discipline in the comments.
#
# Each tuple is (name, azimuth, elevation, roll, reference photo):
#
#   name       column label on the contact sheet, and the render's filename stem.
#   azimuth    degrees CCW around the object from straight-on. 0 = front, 180 = rear,
#              +90 / -90 = the two profiles.
#   elevation  degrees above the horizon. 0 = camera at the object's own height.
#   roll       degrees of in-plane tilt applied to the CAMERA, to reproduce a styling
#              photograph that was shot tilted. 🔴 Roll is the ONLY one of the three you
#              may fit to a score — it cannot change which faces are visible, so it cannot
#              hide a geometry defect. Azimuth and elevation must be chosen BY EYE.
#   reference  the photograph in refs/ this render is judged against. Getting this wrong
#              is the single most expensive mistake available here (see the ref-03 note).
#
# HOW TO FIT A NEW RIG, in the order that works:
#   1. md5 the reference set first — two of the seven photos here arrived byte-identical.
#   2. LOOK at each photograph and name the view it actually shows. Never trust the
#      filename, and never invent a column for a view you have no photograph of.
#   3. For each photo, render a coarse az/el grid of candidates beside it and pick the
#      cell that matches the apparent VIEWPOINT. Not the cell that scores best — see the
#      note on the IoU-optimised poses that were rejected on sight.
#   4. Only then sweep ROLL against IoU and take the peak. `analyze_refs.py roll` gives an
#      independent PCA reading of the photograph's own tilt to check that peak against.
#   5. Mirror the finished list into measure.VIEWS and overlay.PAIRS (see those files).
#
# The six angles are chosen to line up with the six reference photos we actually have,
# so every render has a real photograph to be judged against. Azimuth is degrees CCW
# from straight-on; elevation is degrees above the horizon.
#
# The 4th field is which reference photo this view must be compared against. Getting
# this mapping right is the entire value of the contact sheet — if the columns are not
# the same angle, the critic is comparing a front render to a rear photo and every
# note it writes is garbage.
# (name, azimuth, elevation, ROLL about the view axis, reference photo)
#
# 🔴 `upperq` was MIRRORED for the project's first eleven rounds. It was rigged at
# az +40, which views the device from its RIGHT; `ref-05` is shot from the LEFT — the
# photograph puts the bezel to the right of centre and shows the left flank and the
# top-face ports, and the az +40 render put the bezel left and showed the right flank.
# Verified by rendering +55 and -55 beside the photo and looking: -45 is the photo's
# hand and +55 is its mirror. Same family of defect as the ref-03 top-view mislabel and
# the profile-column mirroring the v4 critic caught, and it means every critic note ever
# written about that column's asymmetric features was judged against a mirror image.
#
# ROLL exists because the two three-quarter shots are styling photographs with the
# product tilted in the image plane. Rolling the CAMERA to match is not fitting a free
# parameter to a score — it reproduces the photograph's presentation so the contact-sheet
# columns are actually comparable. Poses here were chosen by rendering candidates beside
# the photograph and looking at them, never by optimising a ratio; an IoU-optimised pose
# search proposed az -65 for threeq and az +76 for upperq, and both were rejected on
# sight as viewpoints the photographs plainly do not show.
VIEWS = [
    ("front",   0,    0,   0.0, "ref-01.jpg"),          # straight-on elevation
    ("threeq", -32,  -8, -25.4, "ref-04.jpg"),          # lower-left three-quarter
    ("side",    90,   0,   0.0, "ref-06.jpg"),          # profile
    ("side2",  -90,   0,   0.0, "ref-03-upright.jpg"),  # the opposite-hand profile
    ("rear",   180,   0,   0.0, "ref-02.jpg"),          # heatsink fins + ports + label
    ("upperq", -45,  30, -13.2, "ref-05.jpg"),          # upper-LEFT three-quarter
    ("upperq2",-28,  24, -12.0, "ref-07.jpg"),          # upper-LEFT 3/4, shallower + higher
]

# `upperq2` / `ref-07` was added in round 16. It is the clearest view of the SIDE WALL in the
# whole set and it is the reference that settles the flank-curvature question: the left flank
# reads as a continuous convex sweep with no flat facet, which supersedes an earlier critic's
# call for "a flat side plane". Pose was chosen BY EYE from a 4x3 az/el grid rendered beside
# the photograph (/tmp/gpc/pose-sheet2.png), never by optimising a score: az -28 because the
# bezel's left wall and the front-face/flank width ratio match there, el 24 because the top of
# the bezel and its recessed IR window are visible while the BODY's top face stays a narrow
# band (the module sits low and is seen from above; the body's top is near camera height, so
# perspective compresses it — the two are consistent only in a narrow elevation window).
# ROLL was fitted, which the standing rule permits because roll cannot change which faces are
# visible: -3/-6/-9/-12/-15/-18 scored 80.8/82.3/83.0/83.6/83.2/82.2 IoU, a clean single peak
# at -12. That agrees with ref-05's fitted -13.2 and with ref-07's own PCA roll of +8.6 deg.

# 🔴 ref-03 IS NOT A TOP VIEW. Rounds 1-4 mapped it to a top-down render and it generated a
# phantom -56% error every round, which the critic dutifully reported as a model defect. It is
# the device lying on its side: its long image axis is the device HEIGHT and the thin end on
# the right is the top hook. Rotated CCW to `ref-03-upright.jpg` it stands up as the OPPOSITE
# profile to ref-06 (front faces right instead of left), and the two then agree on
# depth:height to within 2.6% — 0.460 vs 0.472. The depth "conflict" logged at iteration 1
# never existed; it was this mislabel.
#
# There is NO true top-down photograph in the set, so there is no top column. Inventing one
# would mean judging a render against nothing.

# magick has no font config here, so the path is passed explicitly — see `montage` note in
# _cell(). The default is the macOS system Arial this was developed against; on any other
# OS set P23D_FONT to a .ttf that exists, or the contact sheet will fail to build.
FONT = os.environ.get("P23D_FONT", "/System/Library/Fonts/Supplemental/Arial.ttf")


def call(cmd, params=None, timeout=900):
    """One request/response against the bridge. It answers with a single JSON object
    and then closes, so read until the buffer parses rather than until EOF."""
    s = socket.socket()
    s.settimeout(timeout)
    s.connect(("127.0.0.1", PORT))
    s.sendall(json.dumps({"type": cmd, "params": params or {}}).encode())
    buf = b""
    try:
        while True:
            chunk = s.recv(65536)
            if not chunk:
                break
            buf += chunk
            try:
                return json.loads(buf.decode())
            except json.JSONDecodeError:
                continue          # partial frame, keep reading
    finally:
        s.close()
    raise RuntimeError(f"bridge closed without a complete response ({len(buf)} bytes)")


def run_code(code):
    """Execute Python in Blender. Returns (ok, text).

    The traceback is the single most valuable thing this function produces — it is what
    gets fed back to the model on the next turn — so it is returned, never swallowed.
    """
    r = call("execute_code", {"code": code})
    if r.get("status") == "success":
        res = r.get("result", {})
        return True, (res.get("result") if isinstance(res, dict) else str(res)) or ""
    return False, r.get("message", json.dumps(r)[:2000])


RESET = """
import bpy
# Do NOT use read_factory_settings() here — through the bridge it kills the bridge.
# Deleting datablocks directly is the safe equivalent.
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
for m in list(bpy.data.meshes):
    bpy.data.meshes.remove(m, do_unlink=True)
for m in list(bpy.data.materials):
    bpy.data.materials.remove(m, do_unlink=True)
# 🔴 Cameras and lights are DATABLOCKS and deleting the objects does not remove them. Left
# behind, the next STUDIO run's bpy.data.cameras.new("cam") is named "cam.001" while
# bpy.data.cameras["cam"] still resolves to the ORIGINAL, stale one. Anything that reads or
# writes the camera by that name then talks to a datablock the scene is not rendering
# through. That is not hypothetical: a focal sweep left the stale "cam" at 450 mm, the AIM
# framing computed its distance from 450 mm while the render actually used the live 160 mm
# camera, and every mask came out 160/450 = 0.356x scale. The silhouettes still normalised,
# so the IoU scores looked entirely reasonable and were quietly measured on 138x194 px
# renders instead of 390x543 px ones.
for c in list(bpy.data.cameras):
    bpy.data.cameras.remove(c, do_unlink=True)
for l in list(bpy.data.lights):
    bpy.data.lights.remove(l, do_unlink=True)
print("SCENE_RESET")
"""

# Studio setup kept identical across every iteration: if the lighting moves, a render
# that merely looks different reads as a model that changed, and the critic chases ghosts.
STUDIO = """
import bpy, math
sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'          # 5.x reverted the 'BLENDER_EEVEE_NEXT' key
sc.render.film_transparent = False
sc.render.resolution_x = 900
sc.render.resolution_y = 900
sc.render.resolution_percentage = 100
sc.view_settings.view_transform = 'Standard'   # 'AgX' desaturates white plastic to grey

world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
sc.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.05, 0.05, 0.06, 1)
world.node_tree.nodes["Background"].inputs[1].default_value = 1.0

def lamp(name, loc, energy, size):
    d = bpy.data.lights.new(name, type='AREA'); d.energy = energy; d.size = size
    o = bpy.data.objects.new(name, d); bpy.context.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = (0, 0, 0)
    # aim it at the origin
    import mathutils
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = (mathutils.Vector(loc)).to_track_quat('Z', 'Y')
    return o

# Energies are deliberately low. The subject is a WHITE plastic device on a dark ground:
# at the first pass (key=220) every view clipped to featureless white and the silhouette
# was the only thing readable, which would have sent the critic chasing lighting notes
# instead of geometry. Keep highlights off the clip point so panel breaks stay visible.
lamp("key",  ( 0.45,  -0.55,  0.40), 45, 0.9)
lamp("fill", (-0.50,  -0.35,  0.10), 14, 1.2)
lamp("rim",  ( 0.10,   0.60,  0.45), 28, 0.8)
sc.view_settings.exposure = -0.4

# 160 mm, not 85. The 85 mm was a guess that had never been checked against the
# photographs. Product shots are long-lens, and at 85 mm this subject's rounded top and
# bottom corners put the profile's vertical extremes near x=0 — much farther from a side
# camera than the flanks at x=+/-0.5 — so perspective shortened the apparent height and
# inflated every depth:height reading by 1.7-3.8%. Swept 40-450 mm against silhouette IoU
# on all six views with the mesh frozen: 85 mm scores 91.18% mean, 160 mm scores 91.81%,
# and it improves front, rear, side and upperq together. Beyond 160 mm the gain flattens.
# ⚠️ `side` gains 2.3 points while `side2` loses 0.9 — the same geometry photographed from
# opposite sides. That asymmetry is the two profile PHOTOGRAPHS disagreeing with each other
# by about 2% on depth:height, not a lens artefact, and no focal length satisfies both.
cam_d = bpy.data.cameras.new("cam"); cam_d.lens = 160
cam_d.sensor_width = 36
cam = bpy.data.objects.new("cam", cam_d)
bpy.context.collection.objects.link(cam)
sc.camera = cam
print("STUDIO_OK")
"""

# Framing is computed from the model's own bounding box every time, so the object fills
# the frame identically at every angle and between iterations even as its size changes.
AIM = """
import bpy, math, mathutils
sc = bpy.context.scene
cam = bpy.data.objects["cam"]
targets = [o for o in bpy.data.objects if o.type == 'MESH']
if not targets:
    raise RuntimeError("no mesh objects in scene — nothing to frame")
mn = mathutils.Vector(( 1e9,  1e9,  1e9))
mx = mathutils.Vector((-1e9, -1e9, -1e9))
for o in targets:
    for c in o.bound_box:
        w = o.matrix_world @ mathutils.Vector(c)
        mn = mathutils.Vector((min(mn[i], w[i]) for i in range(3)))
        mx = mathutils.Vector((max(mx[i], w[i]) for i in range(3)))
ctr = (mn + mx) / 2
radius = max((mx - mn).length / 2, 1e-4)
# Derive the half-FOV from the actual lens+sensor instead of guessing an angle. The first
# pass hardcoded 14deg while an 85mm on a 36mm sensor is really 11.96deg half-FOV, so the
# object was pushed BEYOND the frame edges at every angle. 0.78 leaves a visible margin.
# read the lens off THIS camera object's own data, never by datablock name — see RESET
cd = cam.data
half_fov = math.atan((cd.sensor_width / 2) / cd.lens)
dist = radius / math.tan(half_fov * 0.78)

az = math.radians(AZ); el = math.radians(EL)
off = mathutils.Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el))) * dist
cam.location = ctr + off
cam.rotation_mode = 'QUATERNION'
q = (cam.location - ctr).to_track_quat('Z', 'Y')
# ROLL about the camera's own view axis, applied AFTER aiming, so the render reproduces
# the in-plane tilt of the styling photographs instead of leaving the columns misaligned.
q = q @ mathutils.Quaternion((0.0, 0.0, 1.0), math.radians(ROLL))
cam.rotation_quaternion = q
sc.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print("RENDERED " + OUT)
"""


def reset():
    for label, code in (("reset", RESET), ("studio", STUDIO)):
        ok, out = run_code(code)
        if not ok:
            sys.exit(f"{label} failed:\n{out}")
    return True


def render(tag, views=VIEWS):
    d = RENDERS / tag
    d.mkdir(parents=True, exist_ok=True)
    made = []
    for name, az, el, roll, _ref in views:
        out = str(d / f"{name}.png")
        code = f"AZ = {az}\nEL = {el}\nROLL = {roll}\nOUT = {out!r}\n" + AIM
        ok, msg = run_code(code)
        if not ok:
            print(f"  {name}: FAILED — {msg.splitlines()[-1][:160]}")
            continue
        p = pathlib.Path(out)
        # "rendered" is a claim; a file on disk with real bytes is the evidence
        if p.exists() and p.stat().st_size > 5000:
            made.append(p)
            print(f"  {name}: {p.stat().st_size // 1024} KB")
        else:
            print(f"  {name}: WROTE NOTHING (blender said ok) — {out}")
    return made


def _cell(src, label, tmp):
    """One labelled tile. Built with -resize/-extent rather than `montage` because
    montage insists on drawing filename labels and this box has no ImageMagick font
    config, so it exits 1 before writing anything."""
    subprocess.run(["magick", str(src), "-resize", "400x400", "-background", "#141414",
                    "-gravity", "center", "-extent", "412x412",
                    "-gravity", "north", "-font", FONT, "-pointsize", "22",
                    "-fill", "#ffcc55", "-annotate", "+0+6", label,
                    str(tmp)], check=True)
    return tmp


def sheet(tag):
    """Renders on top, the matching reference photo directly underneath each one.
    Same column = same angle, so the critic compares down a column."""
    d = RENDERS / tag
    missing = [n for n, _, _, _, _ in VIEWS if not (d / f"{n}.png").exists()]
    if missing:
        sys.exit(f"missing renders for {tag}: {missing}")

    tmp, cells_r, cells_p = d / "_t", [], []
    tmp.mkdir(exist_ok=True)
    for name, az, el, roll, ref in VIEWS:
        cells_r.append(_cell(d / f"{name}.png", f"MODEL {name}", tmp / f"r-{name}.png"))
        rp = REFS / ref
        if not rp.exists():
            sys.exit(f"reference {ref} missing — the column mapping in VIEWS is stale")
        cells_p.append(_cell(rp, f"PHOTO {name}", tmp / f"p-{name}.png"))

    row1, row2 = tmp / "row1.png", tmp / "row2.png"
    subprocess.run(["magick", *map(str, cells_r), "+append", str(row1)], check=True)
    subprocess.run(["magick", *map(str, cells_p), "+append", str(row2)], check=True)
    out = d / "_compare.png"
    subprocess.run(["magick", str(row1), str(row2), "-append", str(out)], check=True)
    for f in tmp.iterdir():
        f.unlink()
    tmp.rmdir()

    dims = subprocess.run(["magick", "identify", "-format", "%wx%h", str(out)],
                          capture_output=True, text=True).stdout
    print(f"  {out}  ({dims})")
    return out


def silhouette(path, light_bg):
    """Binary object mask as (rows, top, bottom).

    🔴 Two silent failures already paid for here, both of which produced plausible numbers:
      1. `-fuzz 8% -trim` on a WHITE device against a WHITE sweep eats the device's own body.
         It reported the upper body at 0.178 of height where a threshold mask, a 41-row
         extraction and the critic all independently say 0.300-0.305. Every band number
         between iterations 3 and 7 was understated by that.
      2. Thresholding a RENDER by brightness cannot work at all: the background renders at
         21% grey and the bezel material is DARKER than the background, so no cutoff separates
         them. A brightness threshold returned "the object fills every row" for all ten bands.
    So: photos are thresholded against their white sweep, and renders are measured on the
    ALPHA channel of a transparent-film render, which is exact and immune to material colour.
    """
    if light_bg:
        ops = ["magick", str(path), "-alpha", "off", "-colorspace", "gray",
               "-white-threshold", "93%", "-negate", "-threshold", "1%"]
    else:
        ops = ["magick", str(path), "-alpha", "extract", "-threshold", "50%"]
    ops += ["-depth", "8", "gray:-"]
    raw = subprocess.run(ops, capture_output=True).stdout
    w, h = [int(v) for v in subprocess.run(
        ["magick", "identify", "-format", "%w %h", str(path)],
        capture_output=True, text=True).stdout.split()]
    rows = []
    for y in range(h):
        line = raw[y * w:(y + 1) * w]
        xs = [x for x, v in enumerate(line) if v > 127]
        rows.append((min(xs), max(xs)) if xs else None)
    live = [i for i, r in enumerate(rows) if r]
    if not live:
        raise SystemExit(f"silhouette: nothing found in {path} — threshold is wrong for it")
    return rows, live[0], live[-1]


def band_profile(path, light_bg, bands=10):
    """Object width in each horizontal band, as a fraction of the object's own height."""
    rows, top, bot = silhouette(path, light_bg)
    height = bot - top + 1
    out = []
    for i in range(bands):
        a = top + int(i * height / bands)
        b = top + int((i + 1) * height / bands)
        widths = [r[1] - r[0] + 1 for r in rows[a:b] if r]
        out.append((sum(widths) / len(widths) / height) if widths else 0.0)
    return out


def render_masks(tag, views=VIEWS):
    """Alpha-matte pass. Same camera rig, transparent film, so the alpha channel IS the
    silhouette — no thresholding, no dependence on how dark a material happens to be."""
    d = RENDERS / tag / "mask"
    d.mkdir(parents=True, exist_ok=True)
    ok, _ = run_code("import bpy; bpy.context.scene.render.film_transparent = True; print('on')")
    if not ok:
        sys.exit("could not enable transparent film")
    try:
        for name, az, el, roll, _ref in views:
            out = str(d / f"{name}.png")
            ok, msg = run_code(f"AZ = {az}\nEL = {el}\nROLL = {roll}\nOUT = {out!r}\n" + AIM)
            if not ok:
                print(f"  mask {name}: FAILED — {msg.splitlines()[-1][:120]}")
    finally:
        run_code("import bpy; bpy.context.scene.render.film_transparent = False; print('off')")
    return d


def compare_profile(tag, view="side", ref="ref-06.jpg"):
    """Print the model's depth profile beside the photograph's, band for band."""
    mask = RENDERS / tag / "mask" / f"{view}.png"
    if not mask.exists():
        render_masks(tag)
    m = band_profile(mask, light_bg=False)
    p = band_profile(REFS / ref, light_bg=True)
    print(f"  depth/height by band, {view} vs {ref}")
    print(f"  {'band':<10} {'MODEL':>7} {'PHOTO':>7} {'err':>8}")
    for i, (a, b) in enumerate(zip(m, p)):
        err = f"{(a-b)/b*100:+.0f}%" if b > 0.01 else "  n/a"
        print(f"  {i*10:>3}-{(i+1)*10:<3}% {a:>7.3f} {b:>7.3f} {err:>8}")
    return m, p


def snapshot(tag):
    """Save the .blend after a good iteration. This is the undo rail: a later step that
    makes things worse can be rolled back to any earlier tag instead of being re-derived."""
    d = RENDERS / tag
    d.mkdir(parents=True, exist_ok=True)
    path = str(d / "state.blend")
    ok, out = run_code(f"import bpy; bpy.ops.wm.save_as_mainfile(filepath={path!r}); print('SAVED')")
    if not ok:
        print(f"  snapshot FAILED: {out.splitlines()[-1][:160]}")
        return None
    p = pathlib.Path(path)
    print(f"  snapshot: {p.stat().st_size // 1024} KB")
    return p


def iterate(tag, script):
    """One full turn: run the model script into a clean scene, render all six views,
    build the comparison sheet, snapshot. Returns the sheet path, or None if the script
    threw — in which case the traceback is what the next turn needs, not a render."""
    src = pathlib.Path(script).read_text()
    reset()
    ok, out = run_code(src)
    if not ok:
        print("SCRIPT FAILED — traceback follows, feed this back verbatim:\n")
        print(out)
        return None
    print(out.strip() or "  (script produced no stdout)")
    if not render(tag):
        return None
    snapshot(tag)
    return sheet(tag)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    if cmd == "check":
        for p in (9876, 9877):
            s = socket.socket(); s.settimeout(3)
            try:
                s.connect(("127.0.0.1", p)); print(f"port {p}: OPEN")
            except Exception as e:
                print(f"port {p}: {e}")
            finally:
                s.close()
        # Which project this will read and write, printed BEFORE the bridge call. A wrong
        # cwd looks exactly like a broken tool, and if the bridge is down the call below
        # raises — so putting this after it would hide the answer in the one case that
        # most needs it: nothing set up yet.
        print(f"project root: {ROOT}")
        print(f"  refs/     {'OK' if REFS.is_dir() else 'MISSING — wrong cwd? or set P23D_ROOT'}"
              f"  ({len(list(REFS.glob('*'))) if REFS.is_dir() else 0} files)")
        print(f"  renders/  {'OK' if RENDERS.is_dir() else 'will be created'}")
        print(f"  font      {'OK' if pathlib.Path(FONT).exists() else 'MISSING — set P23D_FONT'}")
        try:
            ok, out = run_code("import bpy; print('blender ' + bpy.app.version_string)")
            print(("bridge exec: " + out.strip()) if ok else f"bridge exec FAILED: {out}")
        except Exception as e:
            print(f"bridge exec FAILED: {e}  — is Blender running with the community "
                  f"MCP addon on 127.0.0.1:{PORT}?")
    elif cmd == "exec":
        src = pathlib.Path(sys.argv[2]).read_text()
        reset()
        ok, out = run_code(src)
        print(out if ok else f"FAILED:\n{out}")
        sys.exit(0 if ok else 1)
    elif cmd == "render":
        render(sys.argv[2])
    elif cmd == "masks":
        # The alpha-matte pass loop.py scores against. This used to be invoked as
        # `python3 -c "import driver; driver.render_masks('v21')"`, which only resolved
        # while the scripts sat in the working directory. They no longer do, so it is a
        # subcommand like everything else rather than an import that quietly stops working.
        render_masks(sys.argv[2])
    elif cmd == "sheet":
        sheet(sys.argv[2])
    elif cmd == "iterate":
        sys.exit(0 if iterate(sys.argv[2], sys.argv[3]) else 1)
    else:
        sys.exit(__doc__)
