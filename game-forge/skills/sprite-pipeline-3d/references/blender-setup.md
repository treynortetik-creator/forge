# Blender: headless bakes, the live MCP bridge, and their gotchas

## Rule of thumb

| Job | Use |
|---|---|
| Any bake, gate or mesh prep that must be reproducible | headless: `blender -b --factory-startup -P script.py -- args` (rationale: factory settings mean no add-on or preference drift between runs, and exit codes work for gates; all our scripts used it) |
| Inspect a scene, look at the viewport, iterate on a rig or a pose, search the Python API and manual | the live MCP bridge |
| Anything for a gate or CI | never the bridge |

**One Blender process at a time** (our heavy lock, a mkdir lock on a 16 GB laptop, waited on with a sleep loop; the
same rule covered headless browsers and production builds). RAM binds first on such a machine: one incident had
load 22 and swap at 14.4 of 15.4 GB with six headless browsers from overlapping agents. A full 8-direction bake ran 6-8 minutes at super 4. Never `pkill` Blender by name: close only
the process you started, by PID.

## The live MCP bridge

- We ran two servers on different ports: the Blender Lab official one (port 9877; scene inspection, full Python API
  and manual search, viewport screenshots, `execute_blender_code`) and the community `ahujasid/blender-mcp` (port
  9876; builds scenes, renders, pulls free CC0 assets). Both add-ons default to 9876, so one must be moved or they
  fight. We later removed the community one: its launcher had drifted to expose the same tool set as the official
  one, a pure duplicate costing context every session. Today the official one alone is the setup.
- An autostart shim in the Blender startup scripts folder brings the bridge up ~2 s after launch; nothing to click.
- **The bridge runs LLM-written Python inside Blender with no sandbox (`bpy` can `import os`).** Only live while
  Blender is open; keep it off machines or sessions where that is not acceptable.

## Gotchas learned the hard way (Blender 5.x, all hit)

1. **Never call `bpy.ops.wm.read_factory_settings()` through the bridge.** It tears down the add-on and kills the
   socket server mid-request; the call returns nothing. Clear a scene by removing objects:
   `for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)`. (Headless scripts DO call it, at
   the top, fine: there is no bridge to kill. `bake_sprites.py` does.)
2. **`bpy.context.object` is `None`** inside the bridge's execution context, so `primitive_x_add()` followed by
   `bpy.context.object` throws. Capture new objects by set difference of `bpy.data.objects` before and after.
   `bpy.ops.object.shade_smooth()` fails for the same reason: set `poly.use_smooth = True` directly.
3. `Action.fcurves` no longer exists (slotted actions); see `rigging-and-clips.md`.
4. `BLENDER_EEVEE_NEXT` is not a valid render engine key in 5.x; the enum is `BLENDER_EEVEE`, `BLENDER_WORKBENCH`,
   `CYCLES`. EEVEE for animation and bakes (fast), Cycles for hero stills.
5. Emission strength is a rim glow, not a light: `2.4` washed every colour to pastel; `0.25-0.35` with metallic ~0.55
   and roughness ~0.28 read as saturated metal. With a transparent film you still need a dark world or metal reflects nothing and goes flat grey.
6. Seamless turntable loop: key frame 1 at 0 degrees and frame 73 at 360, render frames 1-72 (73 duplicates 1 and stutters);
   parent everything to an empty and rotate the empty.
7. Crop an animation without jitter: never trim each frame (the box moves, the subject wobbles). Compute the UNION
   bbox over the sampled frames and apply one crop. `finish-frames.mjs` does this per cell size.
8. Eevee attribute names change between releases: `hasattr()` before setting (`bake_sprites.py` does for its four shadow/AO/volumetric toggles).

## Quick checklist before a bake

1. `df -h /` has several GB free (an agent-worktree explosion once filled a disk to 0).
2. No other Blender process (`pgrep -fl Blender` shows only your own).
3. `--gate` passes for this cell and scale.
4. A 1-direction, 1-clip trial (`--dirs s --clip idle --super 2`) looks right at 1x before the full run.
5. Penetration gate green on the clip spec you are about to bake.
