"""blender -b heroine_built.blend --python hair_views.py -- <style> <out dir>: her head and one hairstyle in clay-ish colours from
several angles round her neck (to find stray cards)."""
import math
import os
import sys

import bpy
from mathutils import Vector

style, out = sys.argv[sys.argv.index("--") + 1:][:2]
os.makedirs(out, exist_ok=True)
sc = bpy.context.scene
names = [o.name for o in bpy.data.objects]
print("OBJECTS", [n for n in names if "air" in n or "Hero" in n][:40])
for o in bpy.data.objects:
    if o.type == "MESH":
        keep = o.name in ("HeroineHead", "Heroine", "HeroineEyes") or (style in o.name.lower() and "hair" in o.name.lower())
        o.hide_render = not keep
for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
    try:
        sc.render.engine = eng
        break
    except TypeError:
        pass
sc.render.resolution_x, sc.render.resolution_y = 900, 900
sc.render.resolution_percentage = 100
sc.world = bpy.data.worlds.new("w")
sc.world.use_nodes = True
sc.world.node_tree.nodes["Background"].inputs[0].default_value = (0.6, 0.62, 0.65, 1)
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
sun.data.energy = 3.0
sun.rotation_euler = (math.radians(40), 0, math.radians(20))
sc.collection.objects.link(sun)
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
sc.collection.objects.link(cam)
sc.camera = cam
cam.data.lens = float(os.environ.get("HV_LENS", "85"))
eyes = [o for o in bpy.data.objects if o.name == "HeroineEyes"]
ez = sum((eyes[0].matrix_world @ v.co).z for v in eyes[0].data.vertices) / len(eyes[0].data.vertices)
centre = Vector((0, 0.0, ez + float(os.environ.get("HV_UP", "-0.08"))))
for ang in (0, 35, 70, 110, 150, 180, -70, -35):
    a = math.radians(ang)
    el = math.radians(float(os.environ.get("HV_EL", "-3")))
    cam.location = centre + Vector((math.sin(a) * math.cos(el), -math.cos(a) * math.cos(el), math.sin(el)))
    cam.rotation_euler = (centre - cam.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = os.path.join(out, "v%+04d.png" % ang)
    bpy.ops.render.render(write_still=True)
