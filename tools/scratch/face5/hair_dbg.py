"""blender -b <built.blend> --python hair_dbg.py -- <art> <outdir> [style]: her scalp (where hair grows: red), the cap
fade band, and a style if given, rendered from several sides (workbench)."""
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Vector

sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a6007bf07fd45ab0d\tools\assets")
args = sys.argv[sys.argv.index("--") + 1:]
OUTD = args[1]
STYLE = args[2] if len(args) > 2 else None
sys.argv = sys.argv[:sys.argv.index("--") + 1] + [args[0]]
import heroine_hair as hh  # noqa: E402

os.makedirs(OUTD, exist_ok=True)
T = hh.scalp()
me = bpy.data.meshes.new("scalpdbg")
me.from_pydata([tuple(p + n * 0.0015) for p, n in zip(hh.HP, hh.HN)], [], [tuple(t) for t in T])
o = bpy.data.objects.new("scalpdbg", me)
bpy.context.scene.collection.objects.link(o)
m = bpy.data.materials.new("red")
m.diffuse_color = (0.9, 0.1, 0.1, 1)
me.materials.append(m)
show = [o, hh.head, bpy.data.objects["HeroineEyes"], hh.body]
if STYLE:
    h = hh.build(STYLE)
    mh = bpy.data.materials.new("hairdbg")
    mh.diffuse_color = (0.2, 0.5, 0.9, 1)
    h.data.materials.clear()
    h.data.materials.append(mh)
    for mo in h.modifiers:
        mo.show_render = mo.show_viewport = False
    show.append(h)
    o.hide_render = True
for ob in bpy.data.objects:
    if ob.type == "MESH":
        ob.hide_render = ob not in show or (ob is o and STYLE is not None)
        for mo in ob.modifiers:
            mo.show_render = False
sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"
sc.display.shading.light = "STUDIO"
sc.display.shading.color_type = "MATERIAL"
sc.render.resolution_x, sc.render.resolution_y = 900, 900
cam = bpy.data.objects.new("dbgcam", bpy.data.cameras.new("dbgcam"))
sc.collection.objects.link(cam)
sc.camera = cam
cam.data.lens = 85
tgt = Vector((0, 0.0, hh.EYE_Z - 0.02))
for ang in (0, 45, 90, 135, 180, -90):
    a = math.radians(ang)
    cam.location = tgt + Vector((math.sin(a) * 0.75, -math.cos(a) * 0.75, 0.05))
    cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = os.path.join(OUTD, f"{STYLE or 'scalp'}_{ang}.png")
    bpy.ops.render.render(write_still=True)
