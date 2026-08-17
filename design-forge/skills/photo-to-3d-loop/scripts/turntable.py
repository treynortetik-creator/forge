#!/usr/bin/env python3
"""Render the finished model as a seamless looping turntable.

Deliberately separate from driver.py: the loop renders are throwaway 900px EEVEE frames whose
only job is to be judged, and this is the thing a person actually watches. Different
resolution, different sample count, optional Cycles.

Needs `ffmpeg` on PATH to encode, and `magick` for the motion check.

    python3 turntable.py v4                 # 72 frames, EEVEE, 1080px
    python3 turntable.py v4 --cycles        # Cycles, slower, for the final
    python3 turntable.py v4 --frames 120
    python3 turntable.py v4 --name widget    # widget-turntable-v4.mp4

Seamlessness: frame i sits at azimuth 360*i/N, so frame N would equal frame 0 and is never
rendered. Getting this off by one is the classic way to end up with a visible hitch.
"""
import argparse, math, pathlib, subprocess, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import driver

ORBIT = """
import bpy, math, mathutils
sc = bpy.context.scene
cam = bpy.data.objects["cam"]
targets = [o for o in bpy.data.objects if o.type == 'MESH']
mn = mathutils.Vector(( 1e9,  1e9,  1e9))
mx = mathutils.Vector((-1e9, -1e9, -1e9))
for o in targets:
    for c in o.bound_box:
        w = o.matrix_world @ mathutils.Vector(c)
        mn = mathutils.Vector((min(mn[i], w[i]) for i in range(3)))
        mx = mathutils.Vector((max(mx[i], w[i]) for i in range(3)))
ctr = (mn + mx) / 2
radius = (mx - mn).length / 2

sc.render.engine = ENGINE
if ENGINE == 'CYCLES':
    sc.cycles.samples = 128
    # Apple Silicon: the GPU backend is METAL, not CUDA. Falling back to CPU rather than
    # guessing wrong and dying mid-sequence.
    try:
        prefs = bpy.context.preferences.addons['cycles'].preferences
        prefs.compute_device_type = 'METAL'
        prefs.get_devices()
        sc.cycles.device = 'GPU'
    except Exception as e:
        print("cycles GPU unavailable, using CPU: %s" % e)
        sc.cycles.device = 'CPU'
sc.render.resolution_x = RES
sc.render.resolution_y = RES
sc.render.film_transparent = False

cd = cam.data          # this camera's OWN data, never by datablock name
half_fov = math.atan((cd.sensor_width / 2) / cd.lens)
# The orbit must frame the WIDEST azimuth, not the current one, or the model breathes in and
# out of frame as it turns. Use the bounding sphere, which is rotation-invariant.
dist = radius / math.tan(half_fov * 0.72)

el = math.radians(ELEV)
for i in range(FRAMES):
    az = math.radians(360.0 * i / FRAMES)      # i/FRAMES, never i/(FRAMES-1) — that duplicates frame 0
    off = mathutils.Vector((math.sin(az) * math.cos(el),
                            -math.cos(az) * math.cos(el),
                            math.sin(el))) * dist
    cam.location = ctr + off
    cam.rotation_mode = 'QUATERNION'
    cam.rotation_quaternion = (cam.location - ctr).to_track_quat('Z', 'Y')
    sc.render.filepath = OUTDIR + "/f_%04d.png" % i
    bpy.ops.render.render(write_still=True)
print("ORBIT_DONE %d frames" % FRAMES)
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tag")
    ap.add_argument("--frames", type=int, default=72)
    ap.add_argument("--res", type=int, default=1080)
    ap.add_argument("--elev", type=float, default=12.0)
    ap.add_argument("--cycles", action="store_true")
    ap.add_argument("--name", default="model",
                    help="filename stem for the mp4, e.g. --name widget-mk2")
    a = ap.parse_args()

    outdir = driver.RENDERS / a.tag / "turntable"
    outdir.mkdir(parents=True, exist_ok=True)
    for old in outdir.glob("f_*.png"):
        old.unlink()          # stale frames from a shorter run would silently pad the loop

    engine = "CYCLES" if a.cycles else "BLENDER_EEVEE"
    print(f"  {a.frames} frames, {a.res}px, {engine}, elevation {a.elev}deg")
    code = (f"ENGINE = {engine!r}\nRES = {a.res}\nFRAMES = {a.frames}\n"
            f"ELEV = {a.elev}\nOUTDIR = {str(outdir)!r}\n") + ORBIT
    ok, out = driver.run_code(code)
    if not ok:
        sys.exit(f"orbit failed:\n{out}")
    print(" ", out.strip())

    got = sorted(outdir.glob("f_*.png"))
    if len(got) != a.frames:
        sys.exit(f"expected {a.frames} frames, found {len(got)} — not encoding a short loop")

    mp4 = driver.RENDERS / a.tag / f"{a.name}-turntable-{a.tag}.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-framerate", "24",
                    "-i", str(outdir / "f_%04d.png"),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
                    "-movflags", "+faststart", str(mp4)], check=True)
    print(f"  {mp4.name}  {mp4.stat().st_size // 1024} KB")

    # Prove it actually moves. A silent failure here renders 72 identical frames and encodes
    # a video that looks like a still, which is exactly the trap paid for on 2026-08-06.
    a0, a1 = got[0], got[len(got) // 4]
    rmse = subprocess.run(["magick", "compare", "-metric", "RMSE", str(a0), str(a1), "null:"],
                          capture_output=True, text=True).stderr.strip()
    print(f"  motion check, frame 0 vs frame {len(got)//4}: RMSE {rmse}")
    return mp4


if __name__ == "__main__":
    main()
