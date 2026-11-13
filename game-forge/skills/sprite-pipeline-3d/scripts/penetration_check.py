"""
penetration_check.py: does a limb sink into the body (or into another limb) on any pose of any clip? A pre-bake gate, headless Blender.

    blender -b --factory-startup -P penetration_check.py -- --model char.glb \
        --seg RFA=Forearm_R --seg RHD=Hand_R --seg LFA=Forearm_L --seg LHD=Hand_L [--pair RFA:LFA] [--pair RFA:RHD] \
        [--actions a,b] [--step 2] [--pen-mm 20] [--height-mm 1850] [--vote 0.8] [--out report.json]

A generalisation of the gate we ran on a game character (there it was hard-wired to one rig's arm bones; here YOU name the segments).
  --seg NAME=substr[,substr]   a segment = the vertices whose weight is >= 90% in vertex groups whose name contains one of the substrings
  body                         every face with NO vertex belonging to any --seg (torso, head, coat, legs ...), always a target.
                               So NAME EVERY LIMB SEGMENT (upper arm too): an unnamed upper arm counts as body, and the forearm's elbow overlap
                               with it then shows as a constant 'hit' (we saw exactly that on the stand-in: 13 mm on every frame of a run).
  --pair A:B                   also test segment A's vertices against segment B's faces (other arm, own upper arm, a weapon)
Per pose (every --step-th frame of every action, or --actions to restrict): a segment vertex penetrates when it is BEHIND the nearest face of the target
AND a 14-ray parity vote says it is enclosed by the target (--vote 0.8 = 80% of rays; an open mesh, e.g. the shoulder cuts of a jacket, gives false hits
from the normal-sign test alone). Depth = distance to the nearest face. A segment's depth on a pose = the THIRD deepest vertex (one stray fingertip or one
vote does not fail a bake), MINUS the same number at the rest pose (skinning at the shoulder and elbow overlaps the neighbour on purpose and is not a hit).
Units: the model has no real size, so depth is scaled to --height-mm for a figure of that height (default 1850: an ASSUMPTION, state it in your report).
Exit 1 + a table of the worst poses when any depth exceeds --pen-mm (default 20); writes <out> JSON. No constraints are added to the rig: it tells you which key to move.
Run BEFORE the renders: ~2 minutes for ~100k triangles over six clips in our case. Needs Blender 5.x + numpy. Tested here on the standin.py mannequin (3k tris);
NOT tested on a high-poly auto-rigged mesh (the nearest-face and ray casts are per vertex, so decimate first: see decimate-glb.py).
"""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def args(name): return [argv[i + 1] for i, a in enumerate(argv) if a == name]
def arg(name, default=None): return (args(name) or [default])[0]
MODEL = arg('--model'); PEN_MM = float(arg('--pen-mm', 20.0)); STEP = int(arg('--step', 2)); PEN_H = float(arg('--height-mm', 1850.0)); VOTE = float(arg('--vote', 0.8))
OUTJ = arg('--out', os.path.splitext(MODEL or 'model')[0] + '.penetration.json'); ONLY = [a for a in str(arg('--actions', '')).split(',') if a]
SEGS = {}
for s in args('--seg'):
    k, v = s.split('=', 1); SEGS[k] = [x for x in v.split(',') if x]
PAIRS = [tuple(p.split(':')) for p in args('--pair')]
if not MODEL or not SEGS:
    raise SystemExit('need --model and at least one --seg NAME=groupSubstring')

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=MODEL)
scene = bpy.context.scene
arm = next((o for o in scene.objects if o.type == 'ARMATURE'), None)
shapes = {pb.custom_shape for pb in (arm.pose.bones if arm else []) if pb.custom_shape}
meshes = [o for o in scene.objects if o.type == 'MESH' and o not in shapes and o.vertex_groups]
if not arm or not meshes:
    raise SystemExit('need a rigged mesh with vertex groups')
o = max(meshes, key=lambda m: len(m.data.vertices))
me = o.data; nv = len(me.vertices); gi = {g.index: g.name for g in o.vertex_groups}
polys = [tuple(p.vertices) for p in me.polygons]

def seg_of(group):
    for k, subs in SEGS.items():
        if any(s in group for s in subs): return k
    return 'BODY'
part = np.empty(nv, dtype=object); pure = np.zeros(nv, dtype=bool)
for v in me.vertices:
    w = {}
    for g in v.groups:
        p = seg_of(gi[g.group]); w[p] = w.get(p, 0.0) + g.weight
    if not w: part[v.index] = 'BODY'; continue
    tot = sum(w.values()) or 1.0; best = max(w, key=w.get)
    part[v.index] = best; pure[v.index] = (w[best] / tot) >= 0.9
def faces(pred): return [i for i, p in enumerate(polys) if all(pred(part[v]) for v in p)]
body_f = faces(lambda x: x == 'BODY')
seg_f = {k: faces(lambda x, k=k: x == k) for k in SEGS}
seg_v = {k: np.where((part == k) & pure)[0] for k in SEGS}
print('SEGS', {k: {'verts': int(len(seg_v[k])), 'faces': len(seg_f[k])} for k in SEGS}, 'body faces', len(body_f))

def world_verts():
    dg = bpy.context.evaluated_depsgraph_get()
    oe = o.evaluated_get(dg); m = oe.to_mesh()
    a = np.empty(len(m.vertices) * 3, dtype=np.float32); m.vertices.foreach_get('co', a); a = a.reshape(-1, 3)
    mw = np.array(oe.matrix_world); oe.to_mesh_clear()
    return (a @ mw[:3, :3].T) + mw[:3, 3]
def bvh(P, fl): return BVHTree.FromPolygons([tuple(map(float, p)) for p in P], [polys[i] for i in fl], epsilon=0.0) if fl else None
DIRS = [Vector(v).normalized() for v in [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1), (1, 1, 1), (1, 1, -1), (1, -1, 1), (1, -1, -1), (-1, 1, 1), (-1, 1, -1), (-1, -1, 1), (-1, -1, -1)]]
def vote(tree, co):
    odd = 0
    for d in DIRS:
        n = 0; p = co.copy()
        for _ in range(12):
            r = tree.ray_cast(p, d)
            if r[0] is None: break
            n += 1; p = r[0] + d * 1e-5
        odd += n & 1
    return odd / len(DIRS)
def depths(P, idx, tree):
    out = np.zeros(len(idx))
    if tree is None: return out
    for k, i in enumerate(idx):
        co = Vector(P[i]); r = tree.find_nearest(co)
        if r[0] is None or (co - r[0]).dot(r[1]) >= 0: continue
        if vote(tree, co) >= VOTE: out[k] = r[3]
    return out
def measure(P):
    res = {}
    body = bvh(P, body_f); segt = {k: bvh(P, seg_f[k]) for k in SEGS}
    for k, idx in seg_v.items():
        res[k + '>body'] = depths(P, idx, body)
    for a, b in PAIRS:
        res[a + '>' + b] = depths(P, seg_v[a], segt[b])
    return res

def set_action(act):
    arm.animation_data_create()
    for tr in list(arm.animation_data.nla_tracks): arm.animation_data.nla_tracks.remove(tr)   # an importer's NLA tracks would override the assigned action
    arm.animation_data.action = act
    try:
        if act.slots: arm.animation_data.action_slot = act.slots[0]
    except Exception: pass
    return act

# rest pose baseline (shoulder / elbow skinning overlap at rest must not count)
arm.animation_data.action = None
for pb in arm.pose.bones:
    pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0); pb.scale = (1, 1, 1)
bpy.context.view_layer.update()
P0 = world_verts(); hgt = float(P0[:, 2].max() - P0[:, 2].min())
base = measure(P0)

rows = []
acts = [a for a in bpy.data.actions if (not ONLY or a.name in ONLY or a.name.split('|')[-1] in ONLY)]
for act in acts:
    set_action(act)
    f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
    for fr in range(f0, f1 + 1, STEP):
        scene.frame_set(fr); bpy.context.view_layer.update()
        for key, d in measure(world_verts()).items():
            ex = np.maximum(0.0, d - base[key])
            deep = float(np.sort(ex)[-3]) if len(ex) >= 3 else float(ex.max()) if len(ex) else 0.0
            rows.append({'action': act.name.split('|')[-1], 'frame': fr, 'pair': key, 'mm': round(deep / hgt * PEN_H, 1)})
worst = {}
for r in rows:
    k = (r['action'], r['pair'])
    if k not in worst or r['mm'] > worst[k]['mm']: worst[k] = r
bad = [r for r in worst.values() if r['mm'] > PEN_MM]
print('FRAMES', sorted({(r['action'], r['frame']) for r in rows})[:6], '... total poses', len({(r['action'], r['frame']) for r in rows}))
print('PEN_TABLE (worst pose per action x pair, mm at an assumed %.0f mm figure; limit %.0f)' % (PEN_H, PEN_MM))
for r in sorted(worst.values(), key=lambda r: -r['mm'])[:25]:
    print('  %-14s %-12s frame %-4d %6.1f mm %s' % (r['action'], r['pair'], r['frame'], r['mm'], 'FAIL' if r['mm'] > PEN_MM else ''))
json.dump({'rows': rows, 'model': os.path.basename(MODEL), 'limit_mm': PEN_MM, 'assumed_height_mm': PEN_H, 'step': STEP, 'worst': list(worst.values()), 'fail': bool(bad)}, open(OUTJ, 'w'), indent=1)
print('PEN_VERDICT', 'FAIL' if bad else 'PASS', len(bad), 'over limit; report', OUTJ)
sys.exit(1 if bad else 0)
