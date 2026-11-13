"""
Pixal3D (single-view) meshes come out in the source camera's frame: a vertical prop leans by the camera pitch (measured 17.5 deg on one urn prop by PCA of the vertices).
This stands the mesh upright: rotates every mesh about X by <deg> (default -17.5), then optionally about Z (`yaw`: a number, or `auto` = turn the footprint's long axis onto X, for slabs,
biers and boxes whose reconstruction comes out yawed ~30 deg), applies the transform, writes a GLB. Local, free.
  blender -b --factory-startup -P untilt-glb.py -- <in.glb> <out.glb> [deg=-17.5] [yaw=0|auto|<deg>]
"""
import bpy, sys, math
a = sys.argv[sys.argv.index('--') + 1:]
src, dst = a[0], a[1]
deg = float(a[2]) if len(a) > 2 else -17.5
yaw = a[3] if len(a) > 3 else '0'
import numpy as np
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
bpy.ops.object.select_all(action='DESELECT')
for o in bpy.context.scene.objects:
    if o.type == 'MESH':
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
        elif yaw != '0': yw = float(yaw)
        o.rotation_mode = 'XYZ'   # the glTF importer leaves QUATERNION, which ignores rotation_euler
        o.rotation_euler = (math.radians(deg), 0, math.radians(yw))
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
bpy.ops.export_scene.gltf(filepath=dst, export_format='GLB')
print('UNTILT', deg)
