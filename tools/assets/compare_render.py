"""A survivor rendered as the reference sheets show a figure: orthographic,
front, left profile and back, in a matte black suit on light grey, so the
two can be set side by side.

    blender -b <hero.blend> --python tools/assets/compare_render.py -- <out prefix> [--skin]
"""
import math
import os
import sys

import bpy
from mathutils import Vector

ARGS = sys.argv[sys.argv.index("--") + 1:]
PREFIX = ARGS[0]
SKIN = "--skin" in ARGS
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x, scene.render.resolution_y = 800, 1100
scene.render.film_transparent = False
w = bpy.data.worlds.new("w")
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.57, 0.62, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 1.0
scene.world = w

body = next(o for o in bpy.data.objects if o.type == "MESH" and o.name.startswith("hero_") and "." not in o.name)
if not SKIN:
    suit = bpy.data.materials.new("suit")
    suit.use_nodes = True
    b = suit.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.03, 0.03, 0.035, 1)
    b.inputs["Roughness"].default_value = 0.45
    # MPFB links materials to the object as well as the mesh: set every slot.
    for slot in body.material_slots:
        slot.link = "OBJECT"
        slot.material = suit

for name, loc, energy in (("key", (2.5, -3, 3.5), 700), ("fill", (-3, -2, 2), 250), ("rim", (0, 3, 3), 500), ("rimside", (-3, 2, 2.5), 400)):
    light = bpy.data.lights.new(name, "AREA")
    light.energy, light.size = energy, 2
    obj = bpy.data.objects.new(name, light)
    obj.location = loc
    scene.collection.objects.link(obj)
    obj.rotation_euler = (-Vector(loc) + Vector((0, 0, 1))).to_track_quat("-Z", "Y").to_euler()

cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
scene.collection.objects.link(cam)
scene.camera = cam
cam.data.type = "ORTHO"
cam.data.ortho_scale = 2.15
for tag, ang in (("front", 0), ("side", 90), ("back", 180)):
    a = math.radians(ang)
    cam.location = (math.sin(a) * 8, -math.cos(a) * 8, 0.92)
    cam.rotation_euler = (math.radians(90), 0, a)
    scene.render.filepath = f"{PREFIX}_{tag}.png"
    bpy.ops.render.render(write_still=True)
print("RENDERED")
