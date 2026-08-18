#!/usr/bin/env python3
"""Freeze the mesh, move only the camera, and see what the silhouette error was really made of.

The `threeq` and `upperq` columns have disagreed with their photographs for ten rounds and
every round the question has been the same: is that a MESH defect or a CAMERA-RIG defect?
Arguing about it from renders is how the project already burned an elevation sweep and
nearly baked a fitted camera angle into the record.

This settles it the cheap way. The mesh is not touched at all. Only camera pose and focal
length move, and the score is IoU of the normalised silhouettes — the whole outline, not a
single bounding-box ratio.

🔴 Why this is NOT the circular camera-fitting the hand-off forbids.

The rule earned in rounds 5-7 is "never fit a camera angle to make a RATIO match", because
a ratio is one scalar that a great many wrong viewpoints satisfy, so the search finds an
angle that hides a real model defect. Two things make this different:

  1. The objective is full-silhouette IoU, not a scalar ratio. It constrains the entire
     outline, so a wrong viewpoint cannot satisfy it by coincidence.
  2. The focal length is fitted on the FOUR views whose pose is already known and not in
     dispute (front 0/0, rear 180/0, and the two profiles at +/-90/0). If one focal
     improves all four of those simultaneously, that is evidence about the LENS, because
     the poses were never free parameters. Only after focal is pinned that way is pose
     searched on the two disputed views.

And the result still has to survive being looked at: a fitted pose that scores well but
plainly is not the photograph's viewpoint gets rejected. The verdict here is diagnostic —
if the bad views snap into place with the mesh frozen, the mesh was never the problem.

    python3 fit_camera.py focal          # step 1, on the four known-pose views
    python3 fit_camera.py pose <lens>    # step 2, az/el on threeq and upperq
"""
import math, os, pathlib, subprocess, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import driver

# Project root: the cwd, or P23D_ROOT. Full note in driver.py — this was
# __file__.parent.parent back when the scripts lived inside the project they served.
ROOT = pathlib.Path(os.environ.get("P23D_ROOT") or pathlib.Path.cwd()).resolve()
REFS = ROOT / "refs"
TMP  = pathlib.Path(os.environ.get("P23D_TMP") or "/tmp/p23d/fit")
TMP.mkdir(parents=True, exist_ok=True)
SIZE = 400          # smaller canvas than the overlay tool: this runs hundreds of scores

# ⚠️ WORKED EXAMPLE — all three tables below describe one device and must be rewritten for
# yours. The METHOD is the part that transfers: pin focal length on the views whose pose is
# not in dispute, and only then search pose on the ones that are.
#
# measured in-plane roll of each photograph (analyze_refs.py roll, on 99% masks)
PHOTO_ROLL = {"ref-01.jpg": 0.17, "ref-02.jpg": 1.49, "ref-04.jpg": -25.35,
              "ref-05.jpg": 7.21, "ref-06.jpg": 3.97, "ref-03-upright.jpg": -2.28}

# KNOWN_POSE is not a free choice: it is the views whose azimuth and elevation are fixed by
# what the photograph plainly is — dead-on front, dead-on rear, the two profiles. That is
# what makes a focal fitted across them evidence about the LENS rather than a pose fudge.
# DISPUTED is everything else. If you have no straight-on views, you have no focal fit.
KNOWN_POSE = [                 # view, az, el, reference — poses that are NOT in dispute
    ("front",  0.0,   0.0, "ref-01.jpg"),
    ("rear",   180.0, 0.0, "ref-02.jpg"),
    ("side",   90.0,  0.0, "ref-06.jpg"),
    ("side2",  -90.0, 0.0, "ref-03-upright.jpg"),
]
DISPUTED = [("threeq", -35.0, -20.0, "ref-04.jpg"),
            ("upperq",  40.0,  25.0, "ref-05.jpg")]

# Same framing maths as driver.AIM, plus a ROLL about the view axis and a settable LENS.
AIM_RL = """
import bpy, math, mathutils
sc = bpy.context.scene
cam = bpy.data.objects["cam"]
cd = cam.data          # this camera's OWN data, never by datablock name
cd.lens = LENS
targets = [o for o in bpy.data.objects if o.type == 'MESH']
mn = mathutils.Vector(( 1e9,  1e9,  1e9))
mx = mathutils.Vector((-1e9, -1e9, -1e9))
for o in targets:
    for c in o.bound_box:
        w = o.matrix_world @ mathutils.Vector(c)
        mn = mathutils.Vector((min(mn[i], w[i]) for i in range(3)))
        mx = mathutils.Vector((max(mx[i], w[i]) for i in range(3)))
ctr = (mn + mx) / 2
radius = max((mx - mn).length / 2, 1e-4)
half_fov = math.atan((cd.sensor_width / 2) / cd.lens)
dist = radius / math.tan(half_fov * 0.78)
az = math.radians(AZ); el = math.radians(EL)
off = mathutils.Vector((math.sin(az)*math.cos(el), -math.cos(az)*math.cos(el), math.sin(el))) * dist
cam.location = ctr + off
cam.rotation_mode = 'QUATERNION'
q = (cam.location - ctr).to_track_quat('Z', 'Y')
# roll about the camera's own view axis, applied AFTER aiming
q = q @ mathutils.Quaternion((0.0, 0.0, 1.0), math.radians(ROLL))
cam.rotation_quaternion = q
sc.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print("OK")
"""


def render_mask(az, el, roll, lens, out):
    code = (f"AZ={az}\nEL={el}\nROLL={roll}\nLENS={lens}\nOUT={str(out)!r}\n" + AIM_RL)
    ok, msg = driver.run_code(code)
    if not ok:
        raise SystemExit(f"render failed: {msg[-400:]}")
    return out


def _norm_bits(src, is_render, roll=0.0):
    pre = (["-alpha", "extract", "-threshold", "50%"] if is_render else
           ["-alpha", "off", "-colorspace", "gray", "-white-threshold", "99%",
            "-negate", "-threshold", "1%"])
    cmd = ["magick", str(src), *pre]
    if abs(roll) > 0.05:
        cmd += ["-background", "black", "-rotate", f"{-roll}"]
    cmd += ["-trim", "+repage", "-resize", f"x{SIZE}",
            "-background", "black", "-gravity", "center", "-extent", f"{SIZE}x{SIZE}",
            "-depth", "8", "gray:-"]
    raw = subprocess.run(cmd, capture_output=True).stdout
    return [v > 127 for v in raw]


_PHOTO_CACHE = {}


def photo_bits(ref):
    if ref not in _PHOTO_CACHE:
        _PHOTO_CACHE[ref] = _norm_bits(REFS / ref, False, PHOTO_ROLL.get(ref, 0.0))
    return _PHOTO_CACHE[ref]


def score(az, el, roll, lens, ref, tag="s"):
    p = render_mask(az, el, roll, lens, TMP / f"{tag}.png")
    a, b = _norm_bits(p, True), photo_bits(ref)
    n = min(len(a), len(b))
    inter = sum(1 for i in range(n) if a[i] and b[i])
    union = sum(1 for i in range(n) if a[i] or b[i])
    return inter / union if union else 0.0


def enable_alpha(on=True):
    driver.run_code(f"import bpy; bpy.context.scene.render.film_transparent={on}; print('x')")


def fit_focal():
    """Sweep focal length on the four views whose pose is not in dispute."""
    enable_alpha(True)
    lenses = [40, 55, 70, 85, 105, 135, 180, 250, 400]
    print(f"  {'lens':>6} " + " ".join(f"{v:>8}" for v, _, _, _ in KNOWN_POSE) + f" {'mean':>8}")
    best = None
    try:
        for lens in lenses:
            row = []
            for view, az, el, ref in KNOWN_POSE:
                row.append(score(az, el, 0.0, lens, ref, tag=f"f{lens}_{view}"))
            m = sum(row) / len(row)
            print(f"  {lens:>6} " + " ".join(f"{v*100:>7.2f}%" for v in row) + f" {m*100:>7.2f}%")
            if best is None or m > best[1]:
                best = (lens, m)
    finally:
        enable_alpha(False)
    print(f"\n  best focal {best[0]} mm, mean IoU {best[1]*100:.2f}% "
          f"over the four known-pose views")
    return best[0]


def fit_pose(lens):
    """Coarse-to-fine az/el search on the two disputed views, mesh frozen."""
    enable_alpha(True)
    results = {}
    try:
        for view, az0, el0, ref in DISPUTED:
            # 🔴 Camera roll stays ZERO here. `photo_bits` already rotates the PHOTOGRAPH
            # upright by its measured in-plane roll, so also rolling the camera applies
            # the correction twice and leaves the pair misaligned by 2x the roll. That bug
            # reported threeq's baseline as 74.13% where the correctly-de-rolled overlay
            # says 81.9%, and the pose search then "fixed" the missing 8 points by swinging
            # elevation 36 degrees — which would have flipped a lower-three-quarter view
            # into an upper one and buried a phantom correction in the camera rig. Exactly
            # the failure mode the never-fit-a-camera-to-a-number rule exists to prevent.
            roll = 0.0
            best = (az0, el0, score(az0, el0, roll, lens, ref, tag=f"p_{view}_base"))
            print(f"\n  {view}: rig is az {az0} el {el0}, baseline IoU {best[2]*100:.2f}% "
                  f"(photo de-rolled by {PHOTO_ROLL.get(ref, 0.0):+.1f} deg)")
            step = 12.0
            for _ in range(3):
                improved = False
                for daz in (-step, 0, step):
                    for dele in (-step, 0, step):
                        if daz == 0 and dele == 0:
                            continue
                        az, el = best[0] + daz, best[1] + dele
                        s = score(az, el, roll, lens, ref, tag=f"p_{view}")
                        if s > best[2] + 1e-4:
                            best = (az, el, s)
                            improved = True
                if not improved:
                    step /= 2.0
            print(f"  {view}: best az {best[0]:.1f} el {best[1]:.1f} "
                  f"IoU {best[2]*100:.2f}%  (moved {best[0]-az0:+.1f} / {best[1]-el0:+.1f})")
            results[view] = best
    finally:
        enable_alpha(False)
    return results


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "focal"
    if what == "focal":
        fit_focal()
    elif what == "pose":
        fit_pose(float(sys.argv[2]))
