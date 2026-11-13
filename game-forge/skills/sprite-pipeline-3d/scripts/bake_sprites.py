"""
bake_sprites.py: 3D character -> 2D sprite frames, N directions, headless Blender, ONE process.

A generalised, trimmed port of the renderer we used for a Phaser roguelite (render.py, ~1,500 lines). Kept: the fixed orthographic camera,
the "only the model turns" rig, the screen-angle -> model-yaw rule, fit-to-height, per-direction height equalisation, the feet pivot, the
centre-bone shift for root-motion clips, the penetration-free toon look, the hatched "ink" look, the inverted-hull outline and the defining-line
sidecar. Dropped (game-specific, not reproduced here): texture re-painting by region masks, skin/electrode/region mask passes, the sketch
(graphite) look, rig bulking, procedural clip hooks, the in-process penetration/face gates (see penetration_check.py for a standalone gate).

    blender -b --factory-startup -P bake_sprites.py -- --model char.glb --clips char.clips.json --out render_dir \
        [--look toon|hatch|flat] [--dirs e,ne,n,nw,w,sw,s,se] [--clip idle,run] [--elev 25] [--yaw plain|corrected|blend] \
        [--facing auto|x|y] [--yaw-offset DEG] [--pivot feet|bbox|sockets] [--cell 256x256] [--scale 1.6] [--fit-height 176] [--super 4] [--samples 4] \
        [--dir-fit] [--line-pass] [--gate] [--refit] [--skip-existing]

Input
  --model   .glb/.gltf/.fbx. Armature optional: a rig-less mesh is a static prop (give its clip frameList [0]).
  --clips   JSON: {"name": "char", "centerBone": "<bone>" (optional), "sockets": {"foot_l": {"bone": b, "local": [x,y,z], "ground": true}, ...} (optional),
              "clips": {"idle": {"action": "<action name>", "n": 8, "fps": 8, "loop": true,
                                 "range": [f0, f1] (optional), "frameList": [..] (optional explicit source frames), "cell": [w, h] (optional per-clip)}}}
            Loops sample n frames over [f0, f1) so the duplicate end frame is dropped; non-loops include both ends. standin.py writes a working example.
Output
  <out>/raw/<name>-<clip>-<dir>-<i>.png   RGBA at SUPER x cell (area-average down with finish-frames.mjs)
  <out>/raw/<...>.ln.png                  with --line-pass: coverage of the DEFINING lines (hull rim + inner contours), alpha = 0..1
  <out>/meta.json                         per-frame 2D sockets, timing per clip
  <out>/fit.json                          cached fit scale (invalidated by changing elev / fit-height / cell / scale)
Looks
  toon   albedo x 3-band diffuse (constant ColorRamp) -> emission, plus inverted-hull outline.
  hatch  engraving-style: key-light tone x albedo luminance -> one anti-aliased stripe family whose WIDTH grows with darkness, a crossing family in the
         darkest core, solid ink below a threshold, long shadow strokes. Stripes are REST-POSE surface coordinates re-aimed per direction, so the lines ride
         the body through a clip. Outline = hull rim only (hull drawn alone, body drawn alone, composited), plus inner contour lines from a camera-space normal
         pass. Requires ONE mesh object (stripe coordinates are the first mesh's bounding box): join meshes before baking.
  flat   albedo emission only, no outline (for debugging silhouettes and registration).
Needs: Blender 5.x with numpy (bundled). Tested here on Blender 5.2.0 LTS with the standin.py character. NOT tested: .fbx input, multi-mesh hatch.
"""
import bpy, sys, os, json, math, time
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

# ---------------------------------------------------------------- args
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def arg(name, default=None, flag=False):
    if name in argv:
        return True if flag else argv[argv.index(name) + 1]
    return False if flag else default

MODEL = arg('--model'); CLIPS = arg('--clips'); OUT = arg('--out', '/tmp/bake_sprites')
LOOK = arg('--look', 'toon')
ELEV = float(arg('--elev', 25)); SAMPLES = int(arg('--samples', 2)); SUP = int(arg('--super', 2))
CELL = [int(v) for v in str(arg('--cell', '256x256')).split('x')]
SCALE = float(arg('--scale', 1.6)); FIT_H = float(arg('--fit-height', 176))
ALL_DIRS = ['e', 'ne', 'n', 'nw', 'w', 'sw', 's', 'se']
DIRS = [d for d in str(arg('--dirs', ','.join(ALL_DIRS))).split(',') if d]
YAW_RULE = str(arg('--yaw', 'plain'))          # plain: true 45 degree steps | corrected: faces the on-screen ground direction (foreshortened) | blend: halfway
FACING = str(arg('--facing', 'auto'))          # auto: glTF default (faces -Y) | x: rest pose faces +X | y: faces +Y
YAW_OFFSET = math.radians(float(arg('--yaw-offset', 0)))   # extra turn for a rig whose rest facing differs from its mesh by an arbitrary angle (we needed 45 deg on one generator's rigs, 0 on another's)
PIVOT = str(arg('--pivot', 'feet'))            # feet: lowest 4% of the mesh at idle frame 0 | bbox | sockets (midpoint of spec sockets foot_l / foot_r bones)
DIR_FIT = arg('--dir-fit', flag=True)          # equalise standing height across directions (a slouching model is up to ~6% shorter on screen from the front)
REFIT = arg('--refit', flag=True); GATE = arg('--gate', flag=True); SKIP = arg('--skip-existing', flag=True)
LINE_PASS = arg('--line-pass', flag=True)
CLIP_SEL = [c for c in str(arg('--clip', '')).split(',') if c]
HATCH = (LOOK == 'hatch')
KEY_DIR = [float(v) for v in str(arg('--key-dir', '-0.55,-0.30,0.78' if HATCH else '-0.55,0.15,0.8')).split(',')]   # direction the key light COMES FROM (x east, y north, z up)
SCREEN_PX = float(arg('--screen-px', 1.27))    # hatch: screen px per cell px at the shipped runtime scale; render px per screen px = SUP / this
OUTLINE_T = float(arg('--outline', 0.025 if HATCH else 0.012))   # inverted-hull thickness in model units (hatch default ~3 px at 1x)
TONE = [float(v) for v in str(arg('--tone', '0.20,0.11,0.035')).split(',')]   # hatch: tone below which the cross set starts | long strokes start | solid ink
TONE_LIT = float(arg('--tone-lit', 0.60)); TONE_ALB = float(arg('--tone-alb', 0.4)); TONE_GAIN = float(arg('--tone-gain', 5.0))
HATCH_PERIOD = float(arg('--hatch-period', 1.9 * SUP / SCREEN_PX))
HATCH_WMAX = float(arg('--hatch-wmax', 0.70)); HATCH_GAMMA = float(arg('--hatch-gamma', 0.8))
HATCH_ANGLES = [float(v) for v in str(arg('--hatch-angles', '-45,55')).split(',')]
STROKE_PERIOD = float(arg('--stroke-period', 4.7 * SUP / SCREEN_PX)); STROKE_ANGLE = float(arg('--stroke-angle', 20.0)); STROKE_W = float(arg('--stroke-w', 0.26))
CONTOUR = HATCH and not arg('--no-contour', flag=True)
CT_THICK = float(arg('--ct-thick', 1.2)); CT_THR = float(arg('--ct-thr', 0.45)); CT_BLUR = float(arg('--ct-blur', 1.0))
BANDS = [(0.0, 0.50), (0.28, 0.78), (0.62, 1.0)]    # toon: constant ColorRamp (position, brightness)
INK = (0x12 / 255, 0x0A / 255, 0x10 / 255); PAPER = (0xE8 / 255, 0xDC / 255, 0xC4 / 255)
OUTLINE_RGB = INK if HATCH else (0x1c / 255, 0x13 / 255, 0x0d / 255)
if not MODEL or not CLIPS:
    raise SystemExit('need --model and --clips (see the header of this file)')
os.makedirs(os.path.join(OUT, 'raw'), exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
t_start = time.time()

def srgb_to_lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

# ---------------------------------------------------------------- screen angle -> model yaw
SCREEN_ANGLE = {'e': 0, 'ne': 45, 'n': 90, 'nw': 135, 'w': 180, 'sw': 225, 's': 270, 'se': 315}
def model_yaw(d):
    s = math.radians(SCREEN_ANGLE[d])
    w = math.atan2(math.sin(s) / math.sin(math.radians(ELEV)), math.cos(s))
    if YAW_RULE == 'plain':
        w = s
    elif YAW_RULE == 'blend':
        dw = math.atan2(math.sin(w - s), math.cos(w - s)); w = s + dw / 2
    return YAW_OFFSET + w + (0 if FACING == 'x' else -math.pi / 2 if FACING == 'y' else math.pi / 2)   # glTF faces -Y (screen S)

# ---------------------------------------------------------------- render settings, camera, lights
def setup_render(cw, ch):
    r = scene.render
    r.engine = 'BLENDER_EEVEE'                  # the only valid EEVEE key in Blender 5.x ('BLENDER_EEVEE_NEXT' is gone)
    r.resolution_x, r.resolution_y, r.resolution_percentage = cw * SUP, ch * SUP, 100
    r.film_transparent = True
    r.image_settings.file_format = 'PNG'; r.image_settings.color_mode = 'RGBA'; r.image_settings.color_depth = '8'
    r.image_settings.compression = 15
    scene.view_settings.view_transform = 'Standard'; scene.view_settings.look = 'None'
    scene.display_settings.display_device = 'sRGB'
    e = scene.eevee
    e.taa_render_samples = SAMPLES
    for attr, val in (('use_shadows', False), ('use_raytracing', False), ('use_gtao', False), ('use_volumetric_shadows', False)):
        if hasattr(e, attr):
            setattr(e, attr, val)
    scene.render.use_motion_blur = False

def setup_camera(cw, ch):
    cam_d = bpy.data.cameras.new('cam'); cam_d.type = 'ORTHO'
    cam_d.ortho_scale = max(cw, ch) / (64.0 * SCALE)       # 1 model unit = 64 world px; SCALE render px per world px
    cam_d.shift_y = 0.35 * ch / max(cw, ch)                # feet (origin) land at y = 0.85 of the cell
    cam_d.clip_start, cam_d.clip_end = 0.1, 100
    cam = bpy.data.objects.new('cam', cam_d); scene.collection.objects.link(cam)
    th = math.radians(ELEV)
    cam.location = Vector((0, -math.cos(th), math.sin(th))) * 20
    cam.rotation_euler = (math.radians(90 - ELEV), 0, 0)
    scene.camera = cam
    return cam

def sun(name, frm, energy, color, angle=0.2):
    ld = bpy.data.lights.new(name, 'SUN'); ld.energy = energy; ld.color = color; ld.angle = angle
    ld.use_shadow = False
    o = bpy.data.objects.new(name, ld); scene.collection.objects.link(o)
    v = Vector(frm).normalized()
    o.rotation_euler = Vector((0, 0, -1)).rotation_difference(-v).to_euler()   # a sun shines along its local -Z
    return o

def setup_lights():
    w = bpy.data.worlds.new('w'); w.use_nodes = True
    bg = w.node_tree.nodes['Background']
    if HATCH:
        # key only, white; a tiny fill so the camera-facing side is not a flat void; no world light
        sun('key', KEY_DIR, 1.0, (1, 1, 1)); sun('fill', (0.45, -0.85, 0.35), 0.06, (1, 1, 1))
        bg.inputs['Color'].default_value = (0, 0, 0, 1); bg.inputs['Strength'].default_value = 0.0
    else:
        sun('key', KEY_DIR, 2.6, (1.0, 0.90, 0.74))                 # warm key, upper left
        sun('fill', (0.45, -0.85, 0.35), 0.9, (0.70, 0.78, 1.0))    # cool fill from the camera side
        sun('rim', (0.7, 0.55, 0.35), 0.8, (1.0, 0.85, 0.62))       # thin warm rim, upper right
        bg.inputs['Color'].default_value = (0.42, 0.44, 0.52, 1); bg.inputs['Strength'].default_value = 0.35
    scene.world = w

# ---------------------------------------------------------------- looks
STRIPES = []    # hatch: [(vector-math dot node, theta degrees, period render px)], re-aimed per direction by aim_stripes()

def _albedo(m):
    """Return (albedo socket or None, constant albedo value) and strip every non-texture node so the material can be rebuilt."""
    if not m.use_nodes:
        m.use_nodes = True
    N = m.node_tree.nodes
    bsdf = next((n for n in N if n.type == 'BSDF_PRINCIPLED'), None)
    sock = None; val = (0.8, 0.8, 0.8, 1)
    if bsdf:
        bc = bsdf.inputs['Base Color']
        if bc.is_linked:
            sock = bc.links[0].from_socket
        else:
            val = tuple(bc.default_value)
    for n in list(N):
        if n.type != 'TEX_IMAGE' and not (sock and n == sock.node) and n.type not in ('TEX_COORD', 'UVMAP', 'MAPPING', 'ATTRIBUTE', 'VERTEX_COLOR'):
            N.remove(n)
    return sock, val

def toon_material(m):
    sock, val = _albedo(m); nt = m.node_tree; N = nt.nodes; L = nt.links
    out = N.new('ShaderNodeOutputMaterial'); out.is_active_output = True
    emi = N.new('ShaderNodeEmission')
    if LOOK == 'flat':
        if sock: L.new(sock, emi.inputs['Color'])
        else: emi.inputs['Color'].default_value = val
        L.new(emi.outputs['Emission'], out.inputs['Surface']); return
    diff = N.new('ShaderNodeBsdfDiffuse'); diff.inputs['Color'].default_value = (1, 1, 1, 1)
    s2r = N.new('ShaderNodeShaderToRGB')
    ramp = N.new('ShaderNodeValToRGB'); ramp.color_ramp.interpolation = 'CONSTANT'
    ramp.color_ramp.elements[0].position = BANDS[0][0]; ramp.color_ramp.elements[0].color = (BANDS[0][1],) * 3 + (1,)
    ramp.color_ramp.elements[1].position = BANDS[1][0]; ramp.color_ramp.elements[1].color = (BANDS[1][1],) * 3 + (1,)
    e = ramp.color_ramp.elements.new(BANDS[2][0]); e.color = (BANDS[2][1],) * 3 + (1,)
    bw = N.new('ShaderNodeRGBToBW')
    mix = N.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'; mix.inputs[0].default_value = 1.0
    L.new(diff.outputs['BSDF'], s2r.inputs['Shader']); L.new(s2r.outputs['Color'], bw.inputs['Color'])
    L.new(bw.outputs['Val'], ramp.inputs['Fac']); L.new(ramp.outputs['Color'], mix.inputs[6])
    if sock: L.new(sock, mix.inputs[7])
    else: mix.inputs[7].default_value = val
    L.new(mix.outputs[2], emi.inputs['Color']); L.new(emi.outputs['Emission'], out.inputs['Surface'])

def hatch_material(m):
    sock, val = _albedo(m); nt = m.node_tree; N = nt.nodes; L = nt.links
    out = N.new('ShaderNodeOutputMaterial'); out.is_active_output = True
    def math_(op, a=None, b=None, clamp=False):
        n = N.new('ShaderNodeMath'); n.operation = op; n.use_clamp = clamp
        for i, v in enumerate((a, b)):
            if v is None: continue
            if isinstance(v, (int, float)): n.inputs[i].default_value = v
            else: L.new(v, n.inputs[i])
        return n.outputs['Value']
    clamp01 = lambda v: math_('MINIMUM', math_('MAXIMUM', v, 0.0), 1.0)
    diff = N.new('ShaderNodeBsdfDiffuse'); diff.inputs['Color'].default_value = (1, 1, 1, 1)
    s2r = N.new('ShaderNodeShaderToRGB'); L.new(diff.outputs['BSDF'], s2r.inputs['Shader'])
    lit = N.new('ShaderNodeRGBToBW'); L.new(s2r.outputs['Color'], lit.inputs['Color'])
    if sock:
        al = N.new('ShaderNodeRGBToBW'); L.new(sock, al.inputs['Color']); alv = al.outputs['Val']
    else:
        alv = math_('ADD', sum(val[:3]) / 3, 0.0)
    tone = math_('MULTIPLY', math_('MULTIPLY', lit.outputs['Val'], math_('POWER', math_('MAXIMUM', alv, 0.0005), TONE_ALB)), TONE_GAIN)
    gen = N.new('ShaderNodeTexCoord')
    def coord(th, period):
        dot = N.new('ShaderNodeVectorMath'); dot.operation = 'DOT_PRODUCT'
        L.new(gen.outputs['Generated'], dot.inputs[0])
        STRIPES.append((dot, th, period)); return dot.outputs['Value']
    def stripe(c, w, period):
        """Anti-aliased stripe coverage 0..1: distance to the nearest line centre (in periods) against half the line width, one render px of ramp."""
        dist = math_('ABSOLUTE', math_('SUBTRACT', math_('FRACT', c), 0.5))
        return clamp01(math_('ADD', math_('DIVIDE', math_('SUBTRACT', math_('DIVIDE', w, 2.0), dist), 1.0 / period), 0.5))
    t_cross, t_stroke, t_solid = TONE
    d1 = clamp01(math_('DIVIDE', math_('SUBTRACT', TONE_LIT, tone), TONE_LIT - t_cross))               # fine set: width 0 at TONE_LIT, HATCH_WMAX at t_cross
    w1 = math_('MULTIPLY', HATCH_WMAX, math_('POWER', d1, HATCH_GAMMA))
    set1 = math_('MULTIPLY', stripe(coord(HATCH_ANGLES[0], HATCH_PERIOD), w1, HATCH_PERIOD), math_('GREATER_THAN', d1, 0.02))
    d2 = clamp01(math_('DIVIDE', math_('SUBTRACT', t_cross, tone), t_cross - t_solid))                  # cross set: darkest core only
    set2 = math_('MULTIPLY', stripe(coord(HATCH_ANGLES[1], HATCH_PERIOD), math_('MULTIPLY', 0.55, d2), HATCH_PERIOD), math_('GREATER_THAN', d2, 0.02))
    set3 = math_('MULTIPLY', stripe(coord(STROKE_ANGLE, STROKE_PERIOD), STROKE_W, STROKE_PERIOD), math_('LESS_THAN', tone, t_stroke))   # long shadow strokes
    solid = math_('LESS_THAN', tone, t_solid)
    ink = math_('MAXIMUM', math_('MAXIMUM', math_('MAXIMUM', set1, set2), set3), solid)
    mix = N.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'MIX'
    L.new(ink, mix.inputs[0])
    mix.inputs[6].default_value = tuple(srgb_to_lin(c) for c in PAPER) + (1,)
    mix.inputs[7].default_value = tuple(srgb_to_lin(c) for c in INK) + (1,)
    emi = N.new('ShaderNodeEmission'); L.new(mix.outputs[2], emi.inputs['Color']); L.new(emi.outputs['Emission'], out.inputs['Surface'])

def aim_stripes(meshes):
    """Per direction (rest pose, once): stripe planes whose normal is perpendicular to the view, at the given screen angles, expressed in the mesh's local
    rest coordinates. Planes containing the view ray project to exact straight screen lines whatever the surface shape; fixed in local space they ride the
    body through the clip (no swim). Generated coords are bbox-normalised, so the vector is scaled by the bbox size."""
    import numpy as np
    el = math.radians(ELEV)
    right = Vector((1, 0, 0)); up = Vector((0, math.sin(el), math.cos(el)))
    px_per_bu = SUP * 64.0 * SCALE
    mo = meshes[0]
    bpy.context.view_layer.update()
    mw = mo.matrix_world; sc = mw.to_scale().x; rot = mw.to_3x3().normalized()
    co = np.empty(len(mo.data.vertices) * 3, dtype=np.float32); mo.data.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    size = np.maximum(co.max(0) - co.min(0), 1e-6)
    for dot, th, period_px in STRIPES:
        t = math.radians(th)
        nw = right * math.cos(t) + up * math.sin(t)
        nl = rot.inverted() @ nw
        v = Vector((nl.x * size[0], nl.y * size[1], nl.z * size[2])) * (sc / (period_px / px_per_bu))
        dot.inputs[1].default_value = (v.x, v.y, v.z)

def outline_material():
    m = bpy.data.materials.new('outline'); m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputMaterial'); em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = tuple(srgb_to_lin(c) for c in OUTLINE_RGB) + (1,)
    nt.links.new(em.outputs['Emission'], out.inputs['Surface'])
    m.use_backface_culling = True
    return m

def normal_material():
    """Camera-space normal as emission (for the inner contour lines)."""
    m = bpy.data.materials.new('nrm'); m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputMaterial'); em = nt.nodes.new('ShaderNodeEmission')
    g = nt.nodes.new('ShaderNodeNewGeometry'); vt = nt.nodes.new('ShaderNodeVectorTransform'); vt.vector_type = 'NORMAL'; vt.convert_from = 'WORLD'; vt.convert_to = 'CAMERA'
    mm = nt.nodes.new('ShaderNodeVectorMath'); mm.operation = 'MULTIPLY_ADD'; mm.inputs[1].default_value = (0.5, 0.5, 0.5); mm.inputs[2].default_value = (0.5, 0.5, 0.5)
    nt.links.new(g.outputs['Normal'], vt.inputs['Vector']); nt.links.new(vt.outputs['Vector'], mm.inputs[0]); nt.links.new(mm.outputs['Vector'], em.inputs['Color'])
    nt.links.new(em.outputs['Emission'], out.inputs['Surface'])
    return m
NRM_MAT = None

def apply_look(meshes):
    done = set()
    for o in meshes:
        for slot in o.material_slots:
            if slot.material and slot.material.name not in done:
                (hatch_material if HATCH else toon_material)(slot.material); done.add(slot.material.name)
        if not o.material_slots:
            m = bpy.data.materials.new('auto'); m.use_nodes = True; o.data.materials.append(m); (hatch_material if HATCH else toon_material)(m)
    om = outline_material(); mods = []
    for o in ([] if LOOK == 'flat' else meshes):
        # inverted hull: a linked copy (same deformation, same vertex groups) with every slot = outline, plus a flipped Solidify
        o2 = o.copy(); o2.name = o.name + '_ol'
        scene.collection.objects.link(o2)
        o2.parent = o.parent; o2.matrix_parent_inverse = o.matrix_parent_inverse.copy()
        for slot in o2.material_slots:
            slot.link = 'OBJECT'; slot.material = om
        sm = o2.modifiers.new('outline', 'SOLIDIFY')
        sm.thickness = OUTLINE_T; sm.offset = 1.0; sm.use_flip_normals = True; sm.use_quality_normals = True
        mods.append((o2, sm))
    return om, mods

# ---------------------------------------------------------------- numpy image helpers (run inside Blender)
def _load(f):
    import numpy as np
    im = bpy.data.images.load(f); im.colorspace_settings.name = 'Non-Color'; im.alpha_mode = 'CHANNEL_PACKED'
    w, h = im.size; a = np.empty(w * h * 4, dtype=np.float32); im.pixels.foreach_get(a); return im, a.reshape(h, w, 4)

def read_alpha(path):
    import numpy as np
    img = bpy.data.images.load(path); w, h = img.size
    a = np.empty(w * h * 4, dtype=np.float32); img.pixels.foreach_get(a)
    a = a.reshape(h, w, 4)[::-1]    # top row first
    bpy.data.images.remove(img)
    return a

def alpha_bbox(a, thr=0.5):
    import numpy as np
    ys, xs = np.where(a[..., 3] > thr)
    return (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())) if len(ys) else None

def _box_blur(a, r):
    import numpy as np
    r = int(r)
    if r < 1: return a
    for ax in (0, 1):
        pad = [(0, 0)] * a.ndim; pad[ax] = (r + 1, r)
        c = np.cumsum(np.pad(a, pad, mode='edge'), axis=ax, dtype=np.float64)
        n = a.shape[ax]
        hi = np.take(c, np.arange(2 * r + 1, 2 * r + 1 + n), axis=ax); lo = np.take(c, np.arange(0, n), axis=ax)
        a = ((hi - lo) / (2 * r + 1)).astype(np.float32)
    return a

def contour_mask(nrm, alpha):
    """Inner contour mask from a camera-space normal image (H, W, 3 in 0..1) and the body alpha: smooth the normals, take the normal-change magnitude over a
    +-k px step, threshold, thicken to CT_THICK screen px. Only inside the body and not within ~1 screen px of the silhouette (the hull is there)."""
    import numpy as np
    px = SUP / SCREEN_PX
    n = (nrm * 2.0 - 1.0) * (alpha[..., None] > 0.5)
    n = _box_blur(n, round(CT_BLUR * px / 2))
    n = n / np.maximum(np.linalg.norm(n, axis=2, keepdims=True), 1e-4)
    k = max(1, round(px * 0.6))
    mag = np.maximum(np.linalg.norm(np.roll(n, -k, axis=1) - np.roll(n, k, axis=1), axis=2), np.linalg.norm(np.roll(n, -k, axis=0) - np.roll(n, k, axis=0), axis=2))
    m = (mag > CT_THR) & (alpha > 0.5)
    grow = int(max(0, round((CT_THICK * px - 2 * k) / 2)))
    if grow:
        m = (_box_blur(m.astype(np.float32), grow) > (0.5 / (2 * grow + 1))) & (alpha > 0.5)
    inner = _box_blur((alpha > 0.5).astype(np.float32), int(round(px * 0.8))) > 0.999
    return m & inner

def hull_visibility(show_hull):
    for o2, _sm in mods: o2.hide_render = not show_hull
    for o in meshes: o.hide_render = show_hull

def _save_cov(path, cov):
    """write the defining-line sidecar <frame>.ln.png (RGB 0, alpha = coverage 0..1)"""
    import numpy as np
    out = np.zeros(cov.shape + (4,), np.float32); out[..., 3] = cov
    im = bpy.data.images.new('lnout', cov.shape[1], cov.shape[0], alpha=True)
    im.colorspace_settings.name = 'Non-Color'; im.alpha_mode = 'CHANNEL_PACKED'
    im.pixels.foreach_set(out.ravel()); im.filepath_raw = path[:-4] + '.ln.png'; im.file_format = 'PNG'; im.save()
    bpy.data.images.remove(im)

def rim_render(path):
    """Outline = the hull's RIM only. The hull is one constant ink colour, so `body OVER hull` equals `body OVER (body + hull)`: render the hull alone, the body
    alone, and composite; the hull then shows only outside the body's own silhouette and never pokes through folds or between limbs as crease ink. With CONTOUR a
    third render (camera-space normals) gives inner contour lines drawn in ink over the body."""
    import numpy as np
    global NRM_MAT
    hp = path[:-4] + '.hull.png'
    hull_visibility(True); scene.render.filepath = hp; bpy.ops.render.render(write_still=True)
    hull_visibility(False); scene.render.filepath = path; bpy.ops.render.render(write_still=True)
    ib, b = _load(path); ih, c = _load(hp)
    cm = None
    if CONTOUR:
        if NRM_MAT is None: NRM_MAT = normal_material()
        np_ = path[:-4] + '.nrm.png'
        vl = scene.view_layers[0]; vl.material_override = NRM_MAT
        scene.render.filepath = np_; bpy.ops.render.render(write_still=True)
        vl.material_override = None
        inn, nr = _load(np_)
        nrgb = np.where(nr[..., :3] <= 0.04045, nr[..., :3] / 12.92, ((nr[..., :3] + 0.055) / 1.055) ** 2.4)   # PNG holds sRGB-encoded emission
        cm = contour_mask(nrgb, b[..., 3])
        b[..., :3][cm] = np.array(OUTLINE_RGB, dtype=np.float32)       # Non-Color load returns encoded values, so write encoded
        bpy.data.images.remove(inn); os.remove(np_)
    if LINE_PASS:
        cov = c[..., 3] * (1 - b[..., 3])
        if cm is not None: cov = np.maximum(cov, cm.astype(np.float32))
        _save_cov(path, np.clip(cov, 0, 1).astype(np.float32))
    ba = b[..., 3:4]; ca = c[..., 3:4]
    oa = ba + ca * (1 - ba)
    orgb = (b[..., :3] * ba + c[..., :3] * ca * (1 - ba)) / np.maximum(oa, 1e-6)
    out = np.concatenate([orgb, oa], axis=2).astype(np.float32)
    ib.pixels.foreach_set(out.ravel()); ib.filepath_raw = path; ib.file_format = 'PNG'; ib.save()
    bpy.data.images.remove(ib); bpy.data.images.remove(ih); os.remove(hp)

def eval_points(meshes):
    import numpy as np
    dg = bpy.context.evaluated_depsgraph_get()
    pts = []
    for o in meshes:
        oe = o.evaluated_get(dg); me = oe.to_mesh()
        a = np.empty(len(me.vertices) * 3, dtype=np.float32); me.vertices.foreach_get('co', a)
        mw = np.array(oe.matrix_world)
        pts.append((a.reshape(-1, 3) @ mw[:3, :3].T) + mw[:3, 3])
        oe.to_mesh_clear()
    return np.concatenate(pts) if pts else np.zeros((1, 3))

# ---------------------------------------------------------------- main
CW, CH = CELL
setup_render(CW, CH)
cam = setup_camera(CW, CH)
setup_lights()
KEEP = ('cam', 'key', 'fill', 'rim')

if GATE:
    # G0: a 0.5 BU cube centred on the origin must land at (cell_w/2, 0.85 cell_h) +-1 px (a 1 BU cube would clip the cell bottom)
    bpy.ops.mesh.primitive_cube_add(size=0.5, location=(0, 0, 0))
    scene.render.filepath = os.path.join(OUT, 'gate.png')
    t0 = time.time(); bpy.ops.render.render(write_still=True); dt = time.time() - t0
    import numpy as np
    a = read_alpha(scene.render.filepath)
    ys, xs = np.where(a[..., 3] > 0.5)
    cx = ((xs.min() + xs.max() + 1) / 2) / SUP; cy = ((ys.min() + ys.max() + 1) / 2) / SUP
    exp = (CW / 2, 0.85 * CH); ok = abs(cx - exp[0]) <= 1 and abs(cy - exp[1]) <= 1
    print('GATE_G0', json.dumps({'centre': [round(cx, 2), round(cy, 2)], 'expected': [exp[0], round(exp[1], 2)], 'pass': bool(ok), 'render_s': round(dt, 2)}))
    sys.exit(0 if ok else 1)

ext = os.path.splitext(MODEL)[1].lower()
if ext in ('.glb', '.gltf'): bpy.ops.import_scene.gltf(filepath=MODEL)
elif ext == '.fbx': bpy.ops.import_scene.fbx(filepath=MODEL)
else: raise SystemExit(f'unsupported model {ext}')
spec = json.load(open(CLIPS))
char = spec['name']
objs = list(scene.objects)
meshes = [o for o in objs if o.type == 'MESH']
arms = [o for o in objs if o.type == 'ARMATURE']
arm = arms[0] if arms else None
# the glTF importer adds an 'Icosphere' bone-display shape per armature: not part of the model
shapes = {pb.custom_shape for a in arms for pb in a.pose.bones if pb.custom_shape}
for o in list(shapes):
    if o in meshes: meshes.remove(o)
    bpy.data.objects.remove(o)
for a in arms:
    for pb in a.pose.bones: pb.custom_shape = None
objs = list(scene.objects)
for o in objs:
    if o.type in ('CAMERA', 'LIGHT') and o.name not in KEEP:
        bpy.data.objects.remove(o)
if HATCH and len(meshes) > 1:
    print('WARNING: hatch look aims stripes from the first mesh only; join meshes first for consistent lines (%d meshes)' % len(meshes))

# hierarchy: YAW (turns) > FIT (scale + ground offset) > model roots
yaw = bpy.data.objects.new('YAW', None); scene.collection.objects.link(yaw)
fit = bpy.data.objects.new('FIT', None); scene.collection.objects.link(fit); fit.parent = yaw
for o in objs:
    if o.parent is None and o.name not in KEEP and o.type in ('MESH', 'ARMATURE', 'EMPTY'):
        o.parent = fit

def find_action(name):
    for a in bpy.data.actions:
        if a.name == name or a.name.endswith('|' + name) or a.name.split('.')[0] == name:
            return a
    return None

if arm:
    arm.animation_data_create()
    for tr in list(arm.animation_data.nla_tracks): arm.animation_data.nla_tracks.remove(tr)

def set_action(act):
    if arm is None: return      # static prop: nothing to pose
    arm.animation_data.action = act
    try:
        if act.slots: arm.animation_data.action_slot = act.slots[0]     # Blender 5 slotted actions
    except Exception:
        pass

def clip_frames(act, c):
    if c.get('frameList'):
        return [float(v) for v in c['frameList']]
    f0, f1 = c.get('range') or act.frame_range
    n = c['n']
    if c.get('loop'):
        return [f0 + (f1 - f0) * i / n for i in range(n)]       # drop the duplicate end frame
    return [f0 + (f1 - f0) * i / max(1, n - 1) for i in range(n)]

def goto(frame):
    fi = int(math.floor(frame))
    scene.frame_set(fi, subframe=frame - fi)
    bpy.context.view_layer.update()

# ground + centre the model on its idle frame 0
idle = spec['clips'].get('idle') or next(iter(spec['clips'].values()))
idle_act = find_action(idle['action']) if arm else None
if arm:
    set_action(idle_act); goto(clip_frames(idle_act, idle)[0])
pts = eval_points(meshes)
z0 = float(pts[:, 2].min()); height = float(pts[:, 2].max() - z0)
# PIVOT: the model turns about its FEET, not its bounding box, so a big asymmetric weapon cannot drag the pivot off the body and slide the feet between directions.
if PIVOT == 'sockets' and arm and spec.get('sockets', {}).get('foot_l') and spec['sockets'].get('foot_r'):
    fl = arm.matrix_world @ arm.pose.bones[spec['sockets']['foot_l']['bone']].head; fr = arm.matrix_world @ arm.pose.bones[spec['sockets']['foot_r']['bone']].head
    cx0 = float((fl.x + fr.x) / 2); cy0 = float((fl.y + fr.y) / 2)
elif PIVOT == 'bbox':
    cx0 = float((pts[:, 0].min() + pts[:, 0].max()) / 2); cy0 = float((pts[:, 1].min() + pts[:, 1].max()) / 2)
else:
    low = pts[pts[:, 2] <= z0 + 0.04 * height]
    xs = sorted(low[:, 0]); ys = sorted(low[:, 1])
    cx0 = float((xs[len(xs) // 4] + xs[3 * len(xs) // 4]) / 2); cy0 = float((ys[len(ys) // 4] + ys[3 * len(ys) // 4]) / 2)
print('MODEL', char, 'tris~', sum(len(o.data.polygons) for o in meshes), 'height BU', round(height, 3), 'ground offset', round(z0, 3))

CENTER_BONE = spec.get('centerBone')
hip_ref = (arm.matrix_world @ arm.pose.bones[CENTER_BONE].head) if (arm and CENTER_BONE) else None
CLIP_SHIFT = [0.0, 0.0]   # per clip: mean xy of the centre bone over the clip minus its idle-0 position (a retargeted run carries the root ahead of the feet)

om, mods = apply_look(meshes)

def set_fit(s):
    fit.scale = (s, s, s)
    fit.location = (-(cx0 + CLIP_SHIFT[0]) * s, -(cy0 + CLIP_SHIFT[1]) * s, -z0 * s)
    for o, sm in mods:
        sm.thickness = OUTLINE_T / max(1e-6, s)      # the outline stays the same width in pixels whatever the model's own scale

# fit: render the S idle frame 0 and scale until the alpha box = FIT_H. Cached in <out>/fit.json.
fitp = os.path.join(OUT, 'fit.json'); fit_s = None
if os.path.exists(fitp) and not REFIT:
    try:
        fj = json.load(open(fitp))
        if abs(fj.get('elev', 0) - ELEV) < 1e-6 and fj.get('fitHeight') == FIT_H and fj.get('cell') == CELL and fj.get('scale') == SCALE:
            fit_s = fj['s']
    except Exception:
        pass
yaw.rotation_euler = (0, 0, model_yaw('s'))
if fit_s is None:
    s = 1.0
    for it in range(3):
        set_fit(s)
        scene.render.filepath = os.path.join(OUT, 'fit.png'); bpy.ops.render.render(write_still=True)
        hpx = (lambda bb: (bb[3] - bb[1] + 1) / SUP)(alpha_bbox(read_alpha(scene.render.filepath)))
        print('FIT iter', it, 's', round(s, 4), 'alpha h px', hpx)
        if abs(hpx - FIT_H) <= 0.5: break
        s *= FIT_H / hpx
    fit_s = s
    json.dump({'s': fit_s, 'elev': ELEV, 'fitHeight': FIT_H, 'cell': CELL, 'scale': SCALE, 'modelHeightBU': height}, open(fitp, 'w'))
set_fit(fit_s)

DIR_SCALE = {d: 1.0 for d in DIRS}
if DIR_FIT and arm:
    set_action(idle_act); goto(clip_frames(idle_act, idle)[0])
    stand = {}
    for d in sorted(set(DIRS) | {'s'}):
        yaw.rotation_euler = (0, 0, model_yaw(d))
        scene.render.filepath = os.path.join(OUT, 'dirfit.png'); bpy.ops.render.render(write_still=True)
        bb = alpha_bbox(read_alpha(scene.render.filepath)); stand[d] = (bb[3] - bb[1] + 1) / SUP
    DIR_SCALE = {d: stand['s'] / stand[d] for d in DIRS}
    print('DIR_FIT alpha px', {d: round(v, 1) for d, v in stand.items()}, 'scale', {d: round(v, 3) for d, v in DIR_SCALE.items()})

def socket_px(sdef, cc):
    if sdef.get('bones'):
        ps = [arm.matrix_world @ arm.pose.bones[b].matrix @ Vector(sdef.get('local', (0, 0, 0))) for b in sdef['bones']]
        p = sum(ps, Vector((0, 0, 0))) / len(ps)
    else:
        p = arm.matrix_world @ arm.pose.bones[sdef['bone']].matrix @ Vector(sdef.get('local', (0, 0, 0)))
    if sdef.get('ground'):
        p = Vector((p.x, p.y, 0.0))      # the point straight below the bone, on the floor plane
    v = world_to_camera_view(scene, cam, p)
    return [round(v.x * cc[0], 1), round(cc[1] - v.y * cc[1], 1)]

meta = {'name': char, 'look': LOOK, 'elev': ELEV, 'cell': CELL, 'super': SUP, 'scale': SCALE, 'refHeight': FIT_H, 'fit': fit_s,
        'yawRule': YAW_RULE, 'pivot': PIVOT, 'samples': SAMPLES, 'clips': {}, 'timing': {}}
mp = os.path.join(OUT, 'meta.json')
if SKIP and os.path.exists(mp):
    try:
        old = json.load(open(mp)); meta['clips'] = old.get('clips', {}); meta['timing'] = old.get('timing', {})
    except Exception:
        pass
cur_cell = [CELL]
for cname, c in spec['clips'].items():
    if CLIP_SEL and cname not in CLIP_SEL:
        continue
    act = find_action(c['action']) if arm else None
    if arm and not act:
        print('MISSING ACTION', c['action']); continue
    set_action(act)
    frames = clip_frames(act, c) if arm else [float(v) for v in c.get('frameList', [0])]
    CLIP_SHIFT[0] = CLIP_SHIFT[1] = 0.0
    if hip_ref is not None:
        set_fit(fit_s); acc = []
        for fr in frames:
            goto(fr)
            hp = fit.matrix_world.inverted() @ (arm.matrix_world @ arm.pose.bones[CENTER_BONE].head)
            acc.append((hp.x, hp.y))
        CLIP_SHIFT[0] = sum(a[0] for a in acc) / len(acc) - hip_ref.x; CLIP_SHIFT[1] = sum(a[1] for a in acc) / len(acc) - hip_ref.y
        print('CENTER', cname, [round(v, 3) for v in CLIP_SHIFT])
    cc = c.get('cell') or CELL
    if cc != cur_cell[0]:
        setup_render(*cc); cam.data.ortho_scale = max(cc) / (64.0 * SCALE); cam.data.shift_y = 0.35 * cc[1] / max(cc); cur_cell[0] = cc
    t0 = time.time(); count = 0
    mc = meta['clips'].setdefault(cname, {k: v for k, v in c.items() if k != 'action'})
    mc['dirs'] = mc.get('dirs', {}); mc['cell'] = cc
    for d in DIRS:
        set_fit(fit_s * DIR_SCALE[d])
        if HATCH:
            # stripes are aimed from the REST pose at the base direction only, so the hatching rides the body
            yaw.rotation_euler = (0, 0, model_yaw(d))
            set_action(idle_act); goto(clip_frames(idle_act, idle)[0]) if arm else bpy.context.view_layer.update()
            aim_stripes(meshes)
            set_action(act)
        socks = []
        for i, fr in enumerate(frames):
            yaw.rotation_euler = (0, 0, model_yaw(d))
            path = os.path.join(OUT, 'raw', f'{char}-{cname}-{d}-{i}.png')
            goto(fr)
            socks.append({k: socket_px(v, cc) for k, v in spec.get('sockets', {}).items()} if (arm and spec.get('sockets')) else {})
            if SKIP and os.path.exists(path):
                continue
            scene.render.filepath = path
            if HATCH:
                rim_render(path)
            else:
                bpy.ops.render.render(write_still=True)
            count += 1
        mc['dirs'][d] = {'frames': len(frames), 'sockets': socks}
    dt = time.time() - t0
    meta['timing'][cname] = {'seconds': round(dt, 2), 'frames_rendered': count, 'per_frame_s': round(dt / max(1, count), 3)}
    print('CLIP', cname, json.dumps(meta['timing'][cname]), flush=True)
meta['total_seconds'] = round(time.time() - t_start, 1)
json.dump(meta, open(mp, 'w'), indent=1)
print('RENDER_DONE', char, meta['total_seconds'], 's')
