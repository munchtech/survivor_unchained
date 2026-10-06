"""blender -b --python glossy_glb.py -- heroine.glb out.png: the exported head imported back, shiny grey, lit from her right."""
import math
import sys

import bpy
from mathutils import Vector

glb, out = sys.argv[sys.argv.index("--") + 1:][:2]
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o)
bpy.ops.import_scene.gltf(filepath=glb)
sc = bpy.context.scene
mat = bpy.data.materials.new("gloss")
mat.use_nodes = True
b = mat.node_tree.nodes["Principled BSDF"]
b.inputs["Base Color"].default_value = (0.6, 0.6, 0.6, 1)
b.inputs["Roughness"].default_value = 0.3
for o in bpy.data.objects:
    if o.type == "MESH":
        o.hide_render = o.name not in ("HeroineHead", "Heroine")
        o.data.materials.clear()
        o.data.materials.append(mat)
        print("MESH", o.name, len(o.data.vertices), "keys", len(o.data.shape_keys.key_blocks) if o.data.shape_keys else 0)
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
