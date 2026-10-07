"""Blender: her mouth in clay, close (front, side, three-quarter below), and her lips' profile down her middle (the
head's edges crossing x = 0 near her mouth, as y,z in mm) to JSON.
    blender -b X.blend --python mouth_probe.py -- OUT_PREFIX [shape_key]"""
import json
import math
import sys

import bpy
import numpy as np
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
out = argv[0]
key = argv[1] if len(argv) > 1 and argv[1] else None
sc = bpy.context.scene
for o in sc.objects:
    if o.type == "MESH" and o.data.shape_keys:
        for kb in o.data.shape_keys.key_blocks:
            if key and kb.name == key:
                kb.value = 1.0
bpy.context.view_layer.update()
head = bpy.data.objects["HeroineHead"]
teeth = bpy.data.objects.get("HeroineTeeth")
dg = bpy.context.evaluated_depsgraph_get()
me = head.evaluated_get(dg).to_mesh()
V = np.array([head.matrix_world @ v.co for v in me.vertices])
E = np.array([e.vertices[:] for e in me.edges])
# The mouth: in front of her teeth, or else her face's lowest third's front
if teeth is not None:
    tb = [teeth.matrix_world @ Vector(c) for c in teeth.bound_box]
    m = Vector((0.0, min(v.y for v in tb) - 0.012, max(v.z for v in tb) - 0.004))
else:
    m = Vector((0.0, V[:, 1].min() + 0.01, 1.62))
# profile: edges crossing x=0 within 3 cm of the mouth
a, b = V[E[:, 0]], V[E[:, 1]]
cross = (a[:, 0] * b[:, 0] < 0)
t = a[cross, 0] / (a[cross, 0] - b[cross, 0])
P = a[cross] + (b[cross] - a[cross]) * t[:, None]
near = (np.abs(P[:, 2] - m.z) < 0.03) & (P[:, 1] < m.y + 0.02)
prof = (P[near][:, 1:] * 1000).round(2).tolist()
json.dump({"mouth": [m.y * 1000, m.z * 1000], "profile_yz_mm": prof}, open(out + "_profile.json", "w"))
head.to_mesh_clear()
# Clay renders
sc.render.engine = "BLENDER_WORKBENCH"
sc.display.shading.light = "STUDIO"
sc.display.shading.color_type = "SINGLE"
sc.display.shading.single_color = (0.8, 0.72, 0.66)
sc.display.shading.show_cavity = True
sc.render.resolution_x = sc.render.resolution_y = 800
for o in sc.objects:
    if o.type == "MESH":
        o.hide_render = o.name not in ("HeroineHead", "Heroine", "HeroineEyes", "HeroineTeeth")
cam = bpy.data.objects.new("MouthCam", bpy.data.cameras.new("MouthCam"))
sc.collection.objects.link(cam)
sc.camera = cam
cam.data.type = "ORTHO"
cam.data.ortho_scale = 0.07
for name, d in (("front", Vector((0, -1, 0))), ("side", Vector((1, -0.02, 0))), ("below", Vector((0.5, -0.8, -0.45)))):
    d.normalize()
    cam.location = m + d * 0.5
    cam.rotation_euler = (m - cam.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = out + "_" + name + ".png"
    bpy.ops.render.render(write_still=True)
print("MOUTH", out, "at", tuple(round(c * 1000, 1) for c in m), "profile points", len(prof))
