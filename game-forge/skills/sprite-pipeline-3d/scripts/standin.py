"""
Free stand-in character for the 3D-to-sprite pipeline: a procedural skinned mannequin
with a real armature, scripted idle / run / attack / dash clips, exported as a GLB the way an auto-rigged character would arrive. Use it to build and test the camera, the bake, the packer and the runtime picker
before any generated model exists (and as the smoke-test input for bake_sprites.py).
No downloads, no accounts, no credits.

  blender -b --factory-startup -P standin.py -- <out_dir>
Writes <out_dir>/standin.glb and <out_dir>/standin.clips.json (clip -> action, frames, fps, loop, hitFrames, segments).

Bone local axes (checked by hand, then by render): trunk bones point up, so +X leans FORWARD (toward -Y, the way the model
faces) and local Y is the twist (yaw) axis. Limb bones point DOWN, so +X swings the tip BACKWARD (+Y), -X swings it forward,
and +Z swings the tip toward -X.
"""
import bpy, sys, json, math, os
from mathutils import Vector, Matrix

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = argv[0] if argv else '/tmp/standin'
os.makedirs(OUT, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ---------------------------------------------------------------- skeleton
# name: (parent, head, tail)
S = 0.12
BONES = {
    'hips':      (None,       (0, 0, 0.95), (0, 0, 1.05)),
    'spine':     ('hips',     (0, 0, 1.05), (0, 0, 1.30)),
    'chest':     ('spine',    (0, 0, 1.30), (0, 0, 1.60)),
    'neck':      ('chest',    (0, 0, 1.60), (0, 0, 1.70)),
    'head':      ('neck',     (0, 0, 1.70), (0, 0, 1.98)),
}
for side, sx in (('L', 1), ('R', -1)):
    BONES[f'upper_arm.{side}'] = ('chest', (sx * 0.27, 0, 1.55), (sx * 0.31, 0, 1.27))
    BONES[f'forearm.{side}'] = (f'upper_arm.{side}', (sx * 0.31, 0, 1.27), (sx * 0.33, 0, 1.00))
    BONES[f'hand.{side}'] = (f'forearm.{side}', (sx * 0.33, 0, 1.00), (sx * 0.34, 0, 0.88))
    BONES[f'thigh.{side}'] = ('hips', (sx * S, 0, 0.95), (sx * S, 0, 0.53))
    BONES[f'shin.{side}'] = (f'thigh.{side}', (sx * S, 0, 0.53), (sx * S, 0, 0.10))
    BONES[f'foot.{side}'] = (f'shin.{side}', (sx * S, 0, 0.10), (sx * S, 0, 0.0))

arm_data = bpy.data.armatures.new('standin_rig')
arm = bpy.data.objects.new('standin_rig', arm_data)
scene.collection.objects.link(arm)
bpy.context.view_layer.objects.active = arm
arm.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
for name, (par, h, t) in BONES.items():
    b = arm_data.edit_bones.new(name)
    b.head, b.tail = Vector(h), Vector(t)
    b.roll = 0.0
for name, (par, h, t) in BONES.items():
    if par:
        arm_data.edit_bones[name].parent = arm_data.edit_bones[par]
bpy.ops.object.mode_set(mode='OBJECT')

# ---------------------------------------------------------------- body parts (rigid, one bone each, via vertex groups)
def mat(name, rgb):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*rgb, 1)
    bsdf.inputs['Roughness'].default_value = 0.8
    return m

SKIN, CLOTH, DARK, TRIM, STEEL, HAIR = (mat('skin', (0.78, 0.60, 0.46)), mat('cloth', (0.20, 0.30, 0.52)),
    mat('dark', (0.16, 0.12, 0.10)), mat('trim', (0.62, 0.42, 0.16)), mat('steel', (0.70, 0.72, 0.76)), mat('hair', (0.22, 0.12, 0.07)))

parts = []
def limb(bone, a, b, r, m, r2=None):
    """cylinder from a to b (radius r -> r2) plus sphere caps"""
    a, b = Vector(a), Vector(b)
    d = b - a
    bpy.ops.mesh.primitive_cone_add(vertices=14, radius1=r, radius2=(r2 if r2 is not None else r), depth=d.length, location=(a + b) / 2)
    o = bpy.context.active_object
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d.normalized())
    parts.append((o, bone, m))
def ball(bone, c, r, m, sc=(1, 1, 1)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=10, radius=r, location=c)
    o = bpy.context.active_object
    o.scale = sc
    parts.append((o, bone, m))
def box(bone, c, sz, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=c, rotation=rot)
    o = bpy.context.active_object
    o.scale = sz
    parts.append((o, bone, m))

# torso: wide chest, narrower waist, hips (the figure reads front/back by its shoulders and belt)
box('hips', (0, 0, 1.00), (0.34, 0.20, 0.14), DARK)
limb('spine', (0, 0, 1.06), (0, 0, 1.32), 0.155, CLOTH, 0.17)
box('chest', (0, 0, 1.46), (0.46, 0.24, 0.30), CLOTH)
box('chest', (0, -0.125, 1.40), (0.14, 0.02, 0.26), TRIM)       # front panel: reads the facing
box('hips', (0, -0.115, 1.06), (0.20, 0.03, 0.05), TRIM)         # belt buckle
limb('neck', (0, 0, 1.60), (0, 0, 1.72), 0.055, SKIN)
ball('head', (0, 0, 1.83), 0.115, SKIN, (0.95, 1.0, 1.1))
ball('head', (0, 0.025, 1.87), 0.12, HAIR, (1.0, 1.0, 0.95))     # hair cap, back and top
box('head', (0.045, -0.105, 1.84), (0.03, 0.02, 0.03), DARK)     # eyes
box('head', (-0.045, -0.105, 1.84), (0.03, 0.02, 0.03), DARK)
ball('chest', (0.30, 0, 1.55), 0.085, CLOTH)                      # shoulders
ball('chest', (-0.30, 0, 1.55), 0.085, CLOTH)
for side, sx in (('L', 1), ('R', -1)):
    limb(f'upper_arm.{side}', (sx * 0.27, 0, 1.55), (sx * 0.31, 0, 1.27), 0.062, SKIN, 0.052)
    limb(f'forearm.{side}', (sx * 0.31, 0, 1.27), (sx * 0.33, 0, 1.00), 0.052, TRIM, 0.045)
    ball(f'hand.{side}', (sx * 0.335, 0, 0.93), 0.06, SKIN)
    limb(f'thigh.{side}', (sx * S, 0, 0.95), (sx * S, 0, 0.53), 0.088, DARK, 0.072)
    limb(f'shin.{side}', (sx * S, 0, 0.53), (sx * S, 0, 0.12), 0.07, CLOTH, 0.055)
    ball(f'foot.{side}', (sx * S, -0.02, 0.055), 0.07, DARK, (1.0, 1.2, 0.8))   # shoe: near-spherical so the sole row barely changes with the facing
# the weapon is its own mesh on the right hand : a blade held point-up, crossguard, grip
box('hand.R', (-0.335, 0, 0.93), (0.045, 0.045, 0.2), DARK)
box('hand.R', (-0.335, 0, 1.05), (0.20, 0.05, 0.035), TRIM)
box('hand.R', (-0.335, 0, 1.35), (0.07, 0.022, 0.6), STEEL)

objs = []
for o, bone, m in parts:
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    o.data.materials.append(m)
    vg = o.vertex_groups.new(name=bone)
    vg.add(list(range(len(o.data.vertices))), 1.0, 'REPLACE')
    objs.append(o)
bpy.ops.object.select_all(action='DESELECT')
for o in objs:
    o.select_set(True)
bpy.context.view_layer.objects.active = objs[0]
bpy.ops.object.join()
body = bpy.context.active_object
body.name = 'standin_body'
bpy.ops.object.shade_smooth()
mod = body.modifiers.new('Armature', 'ARMATURE')
mod.object = arm
body.parent = arm

# ---------------------------------------------------------------- clips
D = math.radians
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='POSE')
for pb in arm.pose.bones:
    pb.rotation_mode = 'XYZ'
POSE0 = {}

def key(frame, pose, loc=None):
    """pose: {bone: (rx, ry, rz) degrees}; unlisted bones return to rest"""
    for pb in arm.pose.bones:
        r = pose.get(pb.name, (0, 0, 0))
        pb.rotation_euler = (D(r[0]), D(r[1]), D(r[2]))
        pb.location = (0, 0, 0)
        if loc and pb.name in loc:
            pb.location = loc[pb.name]
        pb.keyframe_insert('rotation_euler', frame=frame)
        pb.keyframe_insert('location', frame=frame)

def new_action(name):
    act = bpy.data.actions.new(name)
    arm.animation_data_create()
    arm.animation_data.action = act
    return act

CLIPS = {}

# idle: breathing, weight shift. 8 frames + the duplicate end frame
act = new_action('idle')
for i in range(9):
    ph = (i / 8) * 2 * math.pi
    b = math.sin(ph)
    key(1 + i, {'spine': (2 + 1.5 * b, 0, 0), 'chest': (1.5 * b, 0, 0), 'head': (-1.5 * b, 0, 0),
                'upper_arm.L': (0, 0, -4 - 1.5 * b), 'upper_arm.R': (0, 0, 4 + 1.5 * b),
                'forearm.R': (-8, 0, 0), 'thigh.L': (-2, 0, 0), 'thigh.R': (2, 0, 0)},
        loc={'hips': (0, 0, 0.012 * b)})
CLIPS['idle'] = dict(action='idle', n=8, fps=8, loop=True)

# run: 8 frames. Contact / down / pass / up for each leg, arms counter-swing, torso lean
act = new_action('run')
for i in range(9):
    ph = (i / 8) * 2 * math.pi
    s, c = math.sin(ph), math.cos(ph)
    def leg(sgn):
        sw = sgn * s
        lift = max(0.0, math.cos(ph + (0 if sgn > 0 else math.pi) + math.pi / 2))
        return (42 * sw, 0, 0), (8 + 62 * max(0.0, -math.sin(ph + (0 if sgn > 0 else math.pi) + 0.6)), 0, 0)
    tl, sl = leg(1)
    tr, sr = leg(-1)
    key(1 + i, {'thigh.L': tl, 'shin.L': sl, 'thigh.R': tr, 'shin.R': sr,
                'foot.L': (-(tl[0] + sl[0]) * 0.5, 0, 0), 'foot.R': (-(tr[0] + sr[0]) * 0.5, 0, 0),
                'upper_arm.L': (-48 * s, 0, -6), 'forearm.L': (-45, 0, 0),
                'upper_arm.R': (48 * s, 0, 6), 'forearm.R': (-45, 0, 0),
                'spine': (12, -6 * s, 0), 'chest': (4, -6 * s, 0), 'head': (-12, 5 * s, 0)},
        loc={'hips': (0, 0, -0.05 * abs(c) + 0.02)})
CLIPS['run'] = dict(action='run', n=8, fps=12, loop=True)

# attack: two cuts, 3 frames each (windup / contact / recovery); hit frames 1 and 4. Right arm swings a blade.
act = new_action('attack')
swing = [
    # (right upper arm xyz, forearm x, chest yaw, spine lean, hips yaw, front foot)
    ((-150, 0, -20), -35, 28, 4, 12),    # 0 windup 1: blade high, behind
    ((-30, 0, 35), -12, -38, 14, -18),   # 1 contact 1: cut down across the body
    ((10, 0, 55), -20, -50, 8, -26),     # 2 recovery 1
    ((-20, 0, 50), -20, -50, 8, -26),    # 3 windup 2: back-hand pull
    ((-95, 0, -15), -8, 42, 10, 22),     # 4 contact 2: backswing, wide
    ((-40, 0, 10), -25, 18, 4, 8),       # 5 recovery 2
]
for i, (ra, fa, ch, lean, hy) in enumerate(swing):
    key(1 + i, {'upper_arm.R': ra, 'forearm.R': (fa, 0, 0), 'upper_arm.L': (-25, 0, -15), 'forearm.L': (-50, 0, 0),
                'chest': (lean * 0.5, ch * 0.6, 0), 'spine': (lean, ch * 0.4, 0), 'hips': (0, hy * 0.5, 0),
                'head': (-lean, -ch * 0.3, 0),
                'thigh.L': (-28 if i % 3 else -12, 0, 0), 'shin.L': (14, 0, 0),
                'thigh.R': (30 if i % 3 else 12, 0, 0), 'shin.R': (22, 0, 0)},
        loc={'hips': (0, -0.05 if i % 3 == 1 else 0, -0.04)})
CLIPS['attack'] = dict(action='attack', n=6, fps=14, loop=False, hitFrames=[1, 4], segments=[3, 3])

# dash: 4 frames, forward lunge, arms trailing
act = new_action('dash')
for i, lean in enumerate((8, 26, 30, 18)):
    key(1 + i, {'spine': (lean, 0, 0), 'chest': (lean * 0.5, 0, 0), 'head': (-lean * 0.8, 0, 0),
                'upper_arm.L': (50, 0, -10), 'upper_arm.R': (55, 0, 10), 'forearm.R': (-25, 0, 0), 'forearm.L': (-25, 0, 0),
                'thigh.L': (-60 if i in (1, 2) else -30, 0, 0), 'shin.L': (20, 0, 0),
                'thigh.R': (40 if i in (1, 2) else 10, 0, 0), 'shin.R': (50 if i in (1, 2) else 20, 0, 0)},
        loc={'hips': (0, -0.10 * i / 3, -0.10)})
CLIPS['dash'] = dict(action='dash', n=4, fps=16, loop=False)

bpy.ops.object.mode_set(mode='OBJECT')
# rest pose + no active action so the exporter keeps all actions as separate clips
arm.animation_data.action = None
for a in bpy.data.actions:
    a.use_fake_user = True
    tr = arm.animation_data.nla_tracks.new()
    tr.name = a.name
    tr.strips.new(a.name, int(a.frame_range[0]), a)

glb = os.path.join(OUT, 'standin.glb')
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=glb, export_format='GLB', export_animations=True, export_animation_mode='NLA_TRACKS',
                          export_apply=False, export_yup=True, export_image_format='AUTO')
with open(os.path.join(OUT, 'standin.clips.json'), 'w') as f:
    json.dump({'name': 'standin', 'clips': CLIPS, 'refHeight': 176, 'scale': 1.6, 'cell': [256, 256],
               'sockets': {'hand_l': {'bone': 'hand.L', 'local': [0, 0.07, 0]}, 'hand_r': {'bone': 'hand.R', 'local': [0, 0.07, 0]},
                           'head': {'bone': 'head', 'local': [0, 0.28, 0]}, 'weapon_tip': {'bone': 'hand.R', 'local': [0, -0.65, 0]},
                           'foot_l': {'bone': 'foot.L', 'local': [0, 0.10, 0]}, 'foot_r': {'bone': 'foot.R', 'local': [0, 0.10, 0]}}}, f, indent=1)
print('STANDIN_OK', glb, os.path.getsize(glb))
