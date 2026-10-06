"""blender -b --python hairlook.py -- <art dir> <out dir> : each hairstyle on her, at rest, round her neck."""
import math
import os
import sys

import bpy
from mathutils import Vector

art, out = sys.argv[sys.argv.index("--") + 1:][:2]
os.makedirs(out, exist_ok=True)
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o)
bpy.ops.import_scene.gltf(filepath=os.path.join(art, "heroine.glb"))
body = [o for o in bpy.data.objects if o.type == "MESH"]
sc = bpy.context.scene
sc.render.engine = "BLENDER_EEVEE_NEXT"
sc.render.resolution_x = sc.render.resolution_y = 900
sc.world = bpy.data.worlds.new("w")
sc.world.use_nodes = True
sc.world.node_tree.nodes["Background"].inputs[0].default_value = (0.3, 0.3, 0.3, 1)
for rot, e in (((math.radians(50), 0, math.radians(-30)), 3.0), ((math.radians(60), 0, math.radians(160)), 2.0)):
    ld = bpy.data.lights.new("s", "SUN")
    ld.energy = e
    lo = bpy.data.objects.new("s", ld)
    lo.rotation_euler = rot
    sc.collection.objects.link(lo)
cam = bpy.data.objects.new("c", bpy.data.cameras.new("c"))
sc.collection.objects.link(cam)
sc.camera = cam
cam.data.lens = 60
for style in ("long", "ponytail", "braid", "bob", "pixie"):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(art, f"heroine_hair_{style}.gltf"))
    new = [o for o in bpy.data.objects if o not in before]
    for name, ang, z in (("back", 180, 1.58), ("side", 75, 1.62), ("front", 15, 1.66)):
        a = math.radians(ang)
        c = Vector((0, 0.0, z))
        cam.location = c + Vector((math.sin(a), -math.cos(a), 0.05)) * 0.75
        cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = os.path.join(out, f"{style}_{name}.png")
        bpy.ops.render.render(write_still=True)
    for o in new:
        bpy.data.objects.remove(o)
