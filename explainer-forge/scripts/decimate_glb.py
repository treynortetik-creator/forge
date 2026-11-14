# Shrink a static 3D prop for the web: decimate to a triangle target, downsize textures, export a small GLB (JPEG textures).
#   blender -b --factory-startup -P decimate_glb.py -- <in.glb> <out.glb> [tris=20000] [tex=1024]
# Typical result: 300-700 KB per prop at 22000 triangles (8000 for small props) with 1024 px textures.
# Image-to-3D services often export models facing +X: rotate -90 degrees on Y in the page so they face the camera.
import sys

import bpy

a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
if len(a) < 2:
    print(__doc__ if __doc__ else 'usage: blender -b --factory-startup -P decimate_glb.py -- in.glb out.glb [tris] [tex]')
    sys.exit(2)
src, dst = a[0], a[1]; target = int(a[2]) if len(a) > 2 else 20000; tex = int(a[3]) if len(a) > 3 else 1024
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']


def tris():
    return sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in meshes)


t0 = tris()
for o in meshes:
    bpy.ops.object.select_all(action='DESELECT'); bpy.context.view_layer.objects.active = o; o.select_set(True)
    d = o.modifiers.new('dec', 'DECIMATE'); d.decimate_type = 'COLLAPSE'; d.ratio = min(1.0, target / max(1, t0))
    d.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier='dec')
for im in bpy.data.images:
    if im.size[0] > tex:
        im.scale(tex, int(im.size[1] * tex / im.size[0]))
print('DECIMATE', t0, '->', tris(), [(i.name, tuple(i.size)) for i in bpy.data.images])
bpy.ops.export_scene.gltf(filepath=dst, export_format='GLB', export_image_format='JPEG', export_jpeg_quality=82,
                          export_apply=True, export_animations=False)
