"""
Merge the actions of several animated GLBs (same rig) into one GLB. Run inside Blender:

  blender -b --factory-startup -P merge_actions.py -- <out.glb> <base.glb> [more.glb ...]

The first file is the base (its armature and mesh are kept); every later file contributes its
actions, then is discarded. Each action becomes an NLA track so the glTF exporter writes it.
Use it after retargeting one clip per GLB (the retarget step writes one animated GLB per move).
"""
import sys, bpy
a = sys.argv[sys.argv.index('--') + 1:]
out = a[0]; files = a[1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=files[0])
arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
acts = {}
base = arm.animation_data.action; acts[base.name] = base
for f in files[1:]:
    before = set(bpy.data.objects.keys()); beforea = set(bpy.data.actions.keys())
    bpy.ops.import_scene.gltf(filepath=f)
    new = [bpy.data.objects[k] for k in bpy.data.objects.keys() if k not in before]
    newa = [bpy.data.actions[k] for k in bpy.data.actions.keys() if k not in beforea]
    for x in newa:
        acts[x.name] = x; x.use_fake_user = True
    for o in new:
        bpy.data.objects.remove(o, do_unlink=True)
arm.animation_data_create()
for name, x in acts.items():
    t = arm.animation_data.nla_tracks.new(); t.name = name
    s = t.strips.new(name, int(x.frame_range[0]), x); s.name = name
arm.animation_data.action = None
print("ACTIONS", list(acts))
bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', export_animations=True, export_nla_strips=True)
