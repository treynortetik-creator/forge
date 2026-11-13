"""Measure the planted-foot ground speed of a run/walk clip.
  blender -b --factory-startup -P stride.py -- --model char.glb --action Run --f0 0 --f1 30 \
      --feet L_Foot,R_Foot --hip Hip --fit 0.6287 [--period 15]
While a foot is planted (its height within 0.02 BU of the cycle minimum) its position, seen from the hip, slides back at the ground speed.
Prints per-foot stance frames, hip-relative backward travel per frame (BU), the mean ground speed, and the stride in world px for one
`--period` source frames: stride = speed x cycle x 64 x fit  (1 render BU = 64 world px; fit = bake_sprites.py's model scale, fit.json `s`)."""
import bpy, sys, json, math
argv = sys.argv[sys.argv.index('--') + 1:]
def a(n, d=None): return argv[argv.index(n) + 1] if n in argv else d
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a('--model'))
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
act = next(x for x in bpy.data.actions if x.name.endswith(a('--action')))
arm.animation_data_create(); arm.animation_data.action = act
try: arm.animation_data.action_slot = act.slots[0]
except Exception: pass
f0, f1 = int(a('--f0')), int(a('--f1')); cycle = float(a('--period', 15)); fit = float(a('--fit', 1.0))
feet = a('--feet', 'L_Foot,R_Foot').split(','); hip = a('--hip', 'Hip')
P = {f: [] for f in feet}; Z = {f: [] for f in feet}
for fr in range(f0, f1 + 1):
    bpy.context.scene.frame_set(fr); bpy.context.view_layer.update()
    h = arm.matrix_world @ arm.pose.bones[hip].head
    for f in feet:
        p = arm.matrix_world @ arm.pose.bones[f].head
        P[f].append((p.x - h.x, p.y - h.y)); Z[f].append(p.z)
res = {}
speeds = []
for f in feet:
    zmin = min(Z[f]); zs = Z[f]
    stance = [i for i in range(1, len(zs)) if zs[i] < zmin + 0.02 and zs[i - 1] < zmin + 0.02]
    # forward axis = +X of the model (the clip faces +X); backward travel per frame while planted
    v = [-(P[f][i][0] - P[f][i - 1][0]) for i in stance]
    sp = sum(v) / len(v) if v else 0.0
    res[f] = {'stance_frames': [f0 + i for i in stance], 'back_travel_per_frame_BU': round(sp, 5), 'zmin': round(zmin, 4)}
    if sp > 0: speeds.append(sp)
mean = sum(speeds) / len(speeds) if speeds else 0
res['mean_speed_BU_per_frame'] = round(mean, 5)
res['stride_world_px_per_cycle'] = round(mean * cycle * 64 * fit, 1)
print('STRIDE', json.dumps(res))
