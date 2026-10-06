"""blender -b built.blend --python glossy.py -- out.png: her head alone, shiny grey, lit from her right, to show creases in its normals."""
import math
import sys

import bpy
from mathutils import Vector

out = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
for o in bpy.data.objects:
    if o.type == "MESH":
        o.hide_render = o.name not in ("HeroineHead", "Heroine")
        for m in o.modifiers:
            m.show_render = m.type == "ARMATURE" and False
mat = bpy.data.materials.new("gloss")
mat.use_nodes = True
b = mat.node_tree.nodes["Principled BSDF"]
b.inputs["Base Color"].default_value = (0.6, 0.6, 0.6, 1)
b.inputs["Roughness"].default_value = 0.25
for name in ("HeroineHead", "Heroine"):
    o = bpy.data.objects[name]
    o.data.materials.clear()
    o.data.materials.append(mat)
for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
    try:
        sc.render.engine = eng
        break
    except TypeError:
        pass
sc.render.resolution_x, sc.render.resolution_y = 1000, 1000
sc.world = bpy.data.worlds.new("w")
sc.world.use_nodes = True
sc.world.node_tree.nodes["Background"].inputs[0].default_value = (0.05, 0.05, 0.05, 1)
ld = bpy.data.lights.new("key", "SUN")
ld.energy = 4
lo = bpy.data.objects.new("key", ld)
lo.rotation_euler = (math.radians(60), 0, math.radians(-35))
sc.collection.objects.link(lo)
cam = bpy.data.objects.new("c", bpy.data.cameras.new("c"))
sc.collection.objects.link(cam)
sc.camera = cam
cam.data.lens = 85
t = Vector((0, -0.02, 1.70))
cam.location = t + Vector((0, -0.9, 0.0))
cam.rotation_euler = (t - cam.location).to_track_quat("-Z", "Y").to_euler()
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
