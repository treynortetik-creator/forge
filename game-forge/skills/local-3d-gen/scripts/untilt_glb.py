"""
Stand a single-view image-to-3D mesh upright. Run inside Blender:

  blender -b --factory-startup -P untilt_glb.py -- <in.glb> <out.glb> [deg=-17.5] [yaw=0|auto|<deg>]

Single-view Pixal3D meshes come out in the SOURCE CAMERA's frame, so a vertical prop leans by
the camera pitch (17.5 deg measured by PCA of the vertices on one urn; 22 deg on most others).
This rotates every mesh about X by <deg>, then optionally about Z (`yaw`: a number, or `auto` =
turn the footprint's long axis onto X, for slabs, biers and boxes whose reconstruction comes out
yawed ~30 deg), applies the transform, and writes a GLB.
Measure the pitch per mesh (PCA of the vertices) rather than assuming it: a TRELLIS.2 mesh of the
same kind of prop came out nearly upright (+6.8 deg), so a blanket value over-corrects.
"""
import bpy, sys, math
import numpy as np

a = sys.argv[sys.argv.index('--') + 1:]
src, dst = a[0], a[1]
deg = float(a[2]) if len(a) > 2 else -17.5
yaw = a[3] if len(a) > 3 else '0'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
bpy.ops.object.select_all(action='DESELECT')
for o in bpy.context.scene.objects:
    if o.type != 'MESH':
        continue
    o.select_set(True); bpy.context.view_layer.objects.active = o
    yw = 0.0
    if yaw == 'auto':
        n = len(o.data.vertices); co = np.empty(n * 3); o.data.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
        t = math.radians(deg); y2 = co[:, 1] * math.cos(t) - co[:, 2] * math.sin(t); x2 = co[:, 0]   # footprint after the tilt
        c = np.cov(np.vstack([x2[::20], y2[::20]])); w, v = np.linalg.eigh(c); ax = v[:, 1]
        ang = math.degrees(math.atan2(ax[1], ax[0]))
        while ang > 90: ang -= 180
        while ang < -90: ang += 180
        yw = -ang
        print('AUTOYAW footprint axis', round(ang, 1), '->', round(yw, 1))
    elif yaw != '0':
        yw = float(yaw)
    o.rotation_mode = 'XYZ'   # the glTF importer leaves QUATERNION, which silently ignores rotation_euler
    o.rotation_euler = (math.radians(deg), 0, math.radians(yw))
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
bpy.ops.export_scene.gltf(filepath=dst, export_format='GLB')
print('UNTILT', deg)
