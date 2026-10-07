"""Blender: her head shaped as a face, a face paint laid over her head's own skin by its alpha, drawn flat (no light)
from in front as heroine_face.py's front drawing is (orthographic, 0.25 m across, 1536 px), with her eyes.

    blender -b heroine_unpainted.blend --python preview_front.py -- OUT.png FACE_PAINT.png [SHAPE.json]
"""
import json
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Vector

a = sys.argv[sys.argv.index("--") + 1:]
out, paint = a[0], a[1]
shape = json.load(open(a[2], encoding="utf-8-sig")) if len(a) > 2 and a[2] else {}
DRAW, SCALE = 1536, 0.25
CENTRE = Vector((0.0, -0.02, 1.735))
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
sc.render.resolution_x = sc.render.resolution_y = DRAW
sc.view_settings.view_transform = "Standard"
sc.world = sc.world or bpy.data.worlds.new("W")
sc.world.use_nodes = True
sc.world.node_tree.nodes["Background"].inputs[0].default_value = (0.45, 0.45, 0.47, 1)
head = bpy.data.objects["HeroineHead"]
for o in bpy.data.objects:
    if o.type == "MESH":
        o.hide_render = o.name not in ("HeroineHead", "HeroineEyes", "Heroine")
        for m in o.modifiers:
            m.show_render = False
# The paint over her head's own skin, by its alpha (as heroine_head.py's head_paint lays it, less its neck easing).
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
for o in bpy.data.objects:
    if o.type != "MESH" or o.hide_render:
        continue
    for m in o.data.materials:
        nt = m.node_tree
        t = next((n for n in nt.nodes if n.type == "TEX_IMAGE"), None)
        outn = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
        em = nt.nodes.new("ShaderNodeEmission")
        if t and o.name == "HeroineHead" and m == head.data.materials[0]:
            t.image = img
        if t:
            nt.links.new(t.outputs["Color"], em.inputs["Color"])
        if t and m.name.startswith("eyes"):
            tr = nt.nodes.new("ShaderNodeBsdfTransparent")
            mix = nt.nodes.new("ShaderNodeMixShader")
            nt.links.new(t.outputs["Alpha"], mix.inputs[0])
            nt.links.new(tr.outputs[0], mix.inputs[1])
            nt.links.new(em.outputs[0], mix.inputs[2])
            nt.links.new(mix.outputs[0], outn.inputs["Surface"])
            m.surface_render_method = "DITHERED"
        else:
            nt.links.new(em.outputs[0], outn.inputs["Surface"])
cam = bpy.data.objects.new("PreviewCam", bpy.data.cameras.new("PreviewCam"))
sc.collection.objects.link(cam)
sc.camera = cam
cam.data.type = "ORTHO"
cam.data.ortho_scale = SCALE
cam.location = CENTRE + Vector((0, -1, 0))
cam.rotation_euler = (CENTRE - cam.location).to_track_quat("-Z", "Y").to_euler()
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
print("PREVIEW", out)
