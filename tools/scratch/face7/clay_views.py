"""Her head in clay (Workbench, studio light): front, three-quarter, below the jaw, and her mouth close, side by side.
Usage: blender -b X.blend --python clay_views.py -- out.png [shape_key]"""
import bpy, sys, math
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
out = argv[0]
key = argv[1] if len(argv) > 1 else None
sc = bpy.context.scene
for o in sc.objects:
    if o.type == "MESH" and o.data.shape_keys and key:
        for kb in o.data.shape_keys.key_blocks:
            if kb.name == key:
                kb.value = 1.0
    if o.type == "MESH" and not o.name.startswith(("Heroine", "Body", "heroine")):
        pass
sc.render.engine = "BLENDER_WORKBENCH"
sc.display.shading.light = "STUDIO"
sc.display.shading.color_type = "SINGLE"
sc.display.shading.single_color = (0.8, 0.72, 0.66)
sc.display.shading.show_cavity = True
sc.display.shading.cavity_type = "WORLD"
sc.render.resolution_x = 900
sc.render.resolution_y = 900
sc.render.film_transparent = False
head = bpy.data.objects["HeroineHead"]
teeth = bpy.data.objects["HeroineTeeth"]
tb = [teeth.matrix_world @ Vector(c) for c in teeth.bound_box]
m = Vector((0.0, min(v.y for v in tb) - 0.012, max(v.z for v in tb) - 0.004))   # (her mouth, in front of her teeth)
c = m + Vector((0, 0, 0.068))
cam_d = bpy.data.cameras.new("cv")
cam = bpy.data.objects.new("cv", cam_d)
sc.collection.objects.link(cam)
sc.camera = cam
views = [("front", (0, -0.6, 0.0), 0.30, c),
         ("three", (-0.42, -0.42, 0.02), 0.30, c),
         ("below", (0.0, -0.45, -0.38), 0.26, c + Vector((0, 0.0, -0.05))),
         ("mouth", (0, -0.6, 0.0), 0.075, m)]
import os
tmp = []
for name, d, ortho, tgt in views:
    cam_d.type = "ORTHO"
    cam_d.ortho_scale = ortho
    cam.location = tgt + Vector(d)
    dirv = tgt - cam.location
    cam.rotation_euler = dirv.to_track_quat("-Z", "Y").to_euler()
    p = out.replace(".png", "_%s.png" % name)
    sc.render.filepath = p
    bpy.ops.render.render(write_still=True)
    tmp.append(p)
print("CLAY", tmp)
