"""Blender: her head shaped as a face, a face paint laid over her head's own skin by its alpha, lit (a soft key from
above and to one side, a fill), seen from several angles round her (perspective, a portrait lens): whether a painted
brow sits on her brow's bone, and a lip on her lip.

    blender -b heroine_unpainted.blend --python preview_lit.py -- OUT_PREFIX FACE_PAINT.png [SHAPE.json] [angles]
"""
import json
import math
import sys

import bpy
import numpy as np
from mathutils import Vector

a = sys.argv[sys.argv.index("--") + 1:]
out, paint = a[0], a[1]
shape = json.load(open(a[2], encoding="utf-8-sig")) if len(a) > 2 and a[2] else {}
angles = [float(v) for v in a[3].split(",")] if len(a) > 3 else [0.0, 35.0, 90.0]
CENTRE = Vector((0.0, -0.02, 1.70))
for o in bpy.data.objects:
    if o.type == "MESH" and o.data.shape_keys:
        kb = o.data.shape_keys.key_blocks
        for s, v in shape.items():
            if s in kb:
                kb[s].value = v
bpy.context.view_layer.update()
sc = bpy.context.scene
for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
    try:
        sc.render.engine = eng
        break
    except TypeError:
        pass
sc.render.resolution_x, sc.render.resolution_y = 1024, 1024
sc.view_settings.view_transform = "Standard"
sc.world = sc.world or bpy.data.worlds.new("W")
sc.world.use_nodes = True
sc.world.node_tree.nodes["Background"].inputs[0].default_value = (0.05, 0.05, 0.055, 1)
sc.world.node_tree.nodes["Background"].inputs[1].default_value = 1.0
head = bpy.data.objects["HeroineHead"]
for o in bpy.data.objects:
    if o.type == "MESH":
        o.hide_render = o.name not in ("HeroineHead", "HeroineEyes", "Heroine", "HeroineLashes")
        for m in o.modifiers:
            m.show_render = False
tex = next(n.image for n in head.data.materials[0].node_tree.nodes if n.type == "TEX_IMAGE" and n.image)
w, h = tex.size
base = np.array(tex.pixels[:], np.float32).reshape(h, w, 4)
from PIL import Image  # noqa: E402
fp = np.asarray(Image.open(paint).convert("RGBA"), np.float32)[::-1] / 255
if fp.shape[0] != h:
    fp = np.asarray(Image.open(paint).convert("RGBA").resize((w, h), Image.LANCZOS), np.float32)[::-1] / 255
al = fp[..., 3:4]
base[..., :3] = base[..., :3] * (1 - al) + fp[..., :3] * al
img = bpy.data.images.new("preview_paint", w, h, alpha=True)
img.pixels.foreach_set(base.ravel())
img.update()
skin = head.data.materials[0]
nt = skin.node_tree
t = next(n for n in nt.nodes if n.type == "TEX_IMAGE")
t.image = img
bsdf = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
if bsdf is not None:
    nt.links.new(t.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.55
for k, v in (("Subsurface Weight", 0.0),):
    if bsdf is not None and k in bsdf.inputs:
        bsdf.inputs[k].default_value = v
key = bpy.data.objects.new("Key", bpy.data.lights.new("Key", "AREA"))
key.data.energy = 9.0
key.data.size = 0.6
key.location = CENTRE + Vector((-0.5, -0.9, 0.55))
key.rotation_euler = (CENTRE - key.location).to_track_quat("-Z", "Y").to_euler()
sc.collection.objects.link(key)
fill = bpy.data.objects.new("Fill", bpy.data.lights.new("Fill", "AREA"))
fill.data.energy = 3.0
fill.data.size = 1.0
fill.location = CENTRE + Vector((0.7, -0.8, 0.1))
fill.rotation_euler = (CENTRE - fill.location).to_track_quat("-Z", "Y").to_euler()
sc.collection.objects.link(fill)
cam = bpy.data.objects.new("LitCam", bpy.data.cameras.new("LitCam"))
sc.collection.objects.link(cam)
sc.camera = cam
cam.data.lens = 85
look = CENTRE + Vector((0, 0, 0.035))
for ang in angles:
    r = math.radians(ang)
    cam.location = look + Vector((math.sin(r), -math.cos(r), 0.02)) * 0.62
    cam.rotation_euler = (look - cam.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = f"{out}_{int(ang):+03d}.png"
    bpy.ops.render.render(write_still=True)
    print("LIT", sc.render.filepath)
