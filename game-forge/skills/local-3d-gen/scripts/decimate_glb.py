"""
Decimate a generated GLB for use in a game or a sprite renderer. Run inside Blender:

  blender -b --factory-startup -P decimate_glb.py -- <in.glb> <out.glb> [target_tris=100000] [tex=2048] [extra.glb ...]

Raw Pixal3D output is ~950k tris and 36-41 MB; this collapses it to a target (the roguelite used
30,000 for static props and ~100,000 for rigged characters) and downsizes the albedo to `tex` px.
Keeps the armature, vertex groups (Decimate collapse interpolates them), UVs and every action.
extra.glb: further animated GLBs of the SAME rig; their actions are carried over onto the first
armature so one GLB holds every clip. A mesh with no armature (a static prop) works too.
Only meshes over 1000 faces are decimated. The armature modifier is removed during the collapse
and re-added after (applying Decimate with an Armature modifier present misbehaves).
"""
import bpy, sys
a = sys.argv[sys.argv.index('--') + 1:]
src, dst = a[0], a[1]
target = int(a[2]) if len(a) > 2 else 100000
tex = int(a[3]) if len(a) > 3 else 2048
extras = a[4:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
arm0 = next((o for o in bpy.context.scene.objects if o.type == 'ARMATURE'), None)
for ex in extras:
    before = set(bpy.data.objects)
    have = {x.name for x in bpy.data.actions}
    bpy.ops.import_scene.gltf(filepath=ex)
    new_acts = [x for x in bpy.data.actions if x.name not in have]
    for o in list(set(bpy.data.objects) - before):
        bpy.data.objects.remove(o, do_unlink=True)
    for x in new_acts:
        x.use_fake_user = True
    print('EXTRA', ex, [x.name for x in new_acts])
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH' and len(o.data.polygons) > 1000]
tris0 = sum(len(o.data.polygons) for o in meshes)
for o in meshes:
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    arm_mods = [(m.name, m.object) for m in o.modifiers if m.type == 'ARMATURE']
    for m in list(o.modifiers):
        if m.type == 'ARMATURE':
            o.modifiers.remove(m)
    d = o.modifiers.new('dec', 'DECIMATE'); d.decimate_type = 'COLLAPSE'
    d.ratio = min(1.0, target / max(1, len(o.data.polygons))); d.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier='dec')
    for n, ob in arm_mods:
        m = o.modifiers.new(n, 'ARMATURE'); m.object = ob
for im in bpy.data.images:
    if im.size[0] > tex:
        im.scale(tex, tex)
print('DECIMATE', tris0, '->', sum(len(o.data.polygons) for o in meshes))
# one NLA track per action so the exporter writes every clip
if arm0 is not None:
    arm0.animation_data_create()
    for x in list(arm0.animation_data.nla_tracks):
        arm0.animation_data.nla_tracks.remove(x)
    for act in bpy.data.actions:
        tr = arm0.animation_data.nla_tracks.new(); tr.name = act.name
        try:
            st = tr.strips.new(act.name, int(act.frame_range[0]), act); st.name = act.name
        except Exception as e:
            print('NLA fail', act.name, e)
    arm0.animation_data.action = None
bpy.ops.export_scene.gltf(filepath=dst, export_format='GLB', export_animations=arm0 is not None,
                          export_animation_mode='NLA_TRACKS', export_image_format='AUTO', export_apply=False)
print('EXPORTED', dst)
