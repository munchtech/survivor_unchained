"""Blender: her head in clay with her eyes, lit from in front, as heroine_face.py draws clay_front.png (orthographic,
0.25 m across, 1536 px, the same centre and light), for each face key given ("" her own), from the blend opened.
    blender -b X.blend --python clay_now.py -- OUTDIR TAG key1 key2 ..."""
import math
import os
import sys

import bpy
from mathutils import Vector

a = sys.argv[sys.argv.index("--") + 1:]
outdir, tag, keys = a[0], a[1], a[2:] or [""]
DRAW, SCALE = 1536, 0.25
CENTRE = Vector((0.0, -0.02, 1.735))
sc = bpy.context.scene
for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
    try:
        sc.render.engine = eng
        break
    except TypeError:
        pass
sc.render.resolution_x = sc.render.resolution_y = DRAW
sc.view_settings.view_transform = "Standard"
sc.world = sc.world or bpy.data.worlds.new("W")
sc.world.use_nodes = True
sc.world.node_tree.nodes["Background"].inputs[0].default_value = (0.45, 0.45, 0.47, 1)
for o in bpy.data.objects:
    if o.type == "MESH":
        o.hide_render = o.name not in ("HeroineHead", "Heroine", "HeroineEyes")
        for m in o.modifiers:
            if m.type != "ARMATURE":
                m.show_render = False
clay = bpy.data.materials.new("clay")
clay.use_nodes = True
clay.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.62, 0.52, 0.47, 1)
clay.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.55
for n in ("HeroineHead", "Heroine", "HeroineEyes"):
    o = bpy.data.objects.get(n)
    if o:
        for s in o.material_slots:
            s.material = clay
sun = bpy.data.objects.new("ClaySun", bpy.data.lights.new("ClaySun", "SUN"))
sun.data.energy = 2.0
sun.data.angle = math.radians(20)
sun.rotation_euler = Vector((0.2, 1.0, -0.5)).normalized().to_track_quat("-Z", "Y").to_euler()
sc.collection.objects.link(sun)
cam = bpy.data.objects.new("FaceCam", bpy.data.cameras.new("FaceCam"))
sc.collection.objects.link(cam)
sc.camera = cam
cam.data.type = "ORTHO"
cam.data.ortho_scale = SCALE
cam.location = CENTRE + Vector((0, -1, 0))
cam.rotation_euler = (CENTRE - cam.location).to_track_quat("-Z", "Y").to_euler()
for key in keys:
    for o in bpy.data.objects:
        if o.type == "MESH" and o.data.shape_keys:
            for kb in o.data.shape_keys.key_blocks:
                if kb.name.startswith("face_") and not kb.name.endswith(("+", "-")):
                    kb.value = 1.0 if kb.name == key else 0.0
    bpy.context.view_layer.update()
    sc.render.filepath = os.path.join(outdir, "clay_%s_%s.png" % (tag, key or "own"))
    bpy.ops.render.render(write_still=True)
    print("CLAY", sc.render.filepath)
