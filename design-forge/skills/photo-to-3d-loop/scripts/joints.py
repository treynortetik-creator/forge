#!/usr/bin/env python3
"""Assembled-model joint assertions — TEMPLATE. Adapt the checks, keep the shape.

🔴 WHY THIS FILE EXISTS. Component decomposition gives every worker a check that its
own part is right IN ISOLATION. No such check can ever catch two workers holding
different numbers for the SAME shared edge, because each part is individually correct.
That defect only exists in the assembly, and on this project the thing that caught it
was the owner looking at a render and saying it "looks all janky." That is not a test
strategy.

Run:  blender --background --factory-startup --python joints.py
Exit 0 = all joints agree. Exit 1 = at least one interface has drifted.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
import scene, ctx, assemble

TOL = 0.004          # ~0.4% of crib length; tighter than the eye, looser than float noise
FAILS, CHECKS = [], []

def world_z(pred):
    """Max/min world Z over objects whose name matches pred."""
    zs = []
    bpy.context.view_layer.update()
    for ob in bpy.context.scene.objects:
        if ob.type != 'MESH' or not pred(ob.name): continue
        for c in ob.bound_box:
            zs.append((ob.matrix_world @ Vector(c)).z)
    return (min(zs), max(zs)) if zs else (None, None)

def check(name, got, want, tol=TOL):
    ok = got is not None and want is not None and abs(got - want) <= tol
    CHECKS.append((name, got, want, ok))
    if not ok: FAILS.append(name)

scene.reset(); scene.studio()
assemble.build()

# ---------------------------------------------------------------------------
# The checks below are the CRIB's joints, kept as worked examples rather than
# genericised into uselessness. Replace them with your own object's mating
# surfaces. The SHAPE is what transfers:
#   - name the physical edge, not the code
#   - query BOTH sides off the assembled mesh, never off a constant
#   - state the tolerance and why it is that number
#   - CALIBRATE on a known-bad model before trusting a pass (see README)
# ---------------------------------------------------------------------------

# 1. THE JOINT THE OWNER REPORTED BY EYE: end-panel top at the BACK edge must be level with
#    the rear panel's top rail. Two files, one physical edge.
_, back_top = world_z(lambda n: n.startswith("back_toprail"))
_, end_top  = world_z(lambda n: n.startswith(("endL_post_b", "endR_post_b")))
check("end-panel back post top == rear top rail", end_top, back_top)

# 2. Only the FEET touch the floor. The photographs show the end panels stopping at
#    the deck frame; posts running to z=0 swallow the feet and render them square.
foot_lo, _  = world_z(lambda n: n.startswith("foot"))
post_lo, _  = world_z(lambda n: n.startswith(("endL_post", "endR_post")))
check("feet reach the floor", foot_lo, 0.0, 0.01)
CHECKS.append(("end posts stop ABOVE the floor", post_lo, ">= 0.02", post_lo is not None and post_lo >= 0.02))
if post_lo is not None and post_lo < 0.02: FAILS.append("end posts stop ABOVE the floor")

# 3. Slat bottoms agree between the rear panel and the end panels (same deck datum).
back_slat_lo, _ = world_z(lambda n: n.startswith("back_slat"))
end_slat_lo, _  = world_z(lambda n: n.startswith(("endL_slat", "endR_slat")))
check("rear and end slat bottoms share a datum", end_slat_lo, back_slat_lo, 0.012)

# 4. The mattress rests ON the deck, neither floating nor sunk.
_, deck_top = world_z(lambda n: n.startswith("deck_"))
mat_lo, _   = world_z(lambda n: n.startswith("mattress"))
check("mattress sits on the deck", mat_lo, deck_top, 0.02)

w = max(len(c[0]) for c in CHECKS)
print("\n" + "=" * (w + 34))
for n, got, want, ok in CHECKS:
    g = f"{got:.4f}" if isinstance(got, float) else str(got)
    t = f"{want:.4f}" if isinstance(want, float) else str(want)
    print(f"{'PASS' if ok else '🔴 FAIL'}  {n:<{w}}  got {g:>8}  want {t:>8}")
print("=" * (w + 34))
print(f"{len(CHECKS)-len(FAILS)}/{len(CHECKS)} joints agree")
sys.exit(1 if FAILS else 0)
