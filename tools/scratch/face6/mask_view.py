"""Her head coloured by the scalp mask (green over her paint), with Tail's hair, from in front: does the mask reach under the cards' edge?"""
import math
import os
import sys

import bpy
from mathutils import Vector

W = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2f7b0f1283f6144a"
out = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
head = bpy.data.objects["HeroineHead"]
m = head.data.materials[0]
nt = m.node_tree
tex = nt.nodes.new("ShaderNodeTexImage")
tex.image = bpy.data.images.load(W + r"\godot\art\people\head_tex\heroine_shadow.png")
tex.image.colorspace_settings.name = "Non-Color"
paint = next(n for n in nt.nodes if n.type == "TEX_IMAGE" and n != tex)
sep = nt.nodes.new("ShaderNodeSeparateColor")
nt.links.new(tex.outputs["Color"], sep.inputs[0])
mix = nt.nodes.new("ShaderNodeMix")
mix.data_type = "RGBA"
mix.inputs["B"].default_value = (0.0, 1.0, 0.0, 1)
nt.links.new(sep.outputs["Green"], mix.inputs["Factor"])
nt.links.new(paint.outputs["Color"], mix.inputs["A"])
em = nt.nodes.new("ShaderNodeEmission")
nt.links.new(mix.outputs["Result"], em.inputs["Color"])
nt.links.new(em.outputs[0], next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL").inputs["Surface"])
for o in bpy.data.objects:
    if o.type == "MESH":
        o.hide_render = o.name not in ("HeroineHead", "HeroineEyes", "hair_ponytail")
for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
    try:
        sc.render.engine = eng
        break
    except TypeError:
        pass
sc.render.resolution_x = sc.render.resolution_y = 900
sc.world = bpy.data.worlds.new("w")
sc.world.use_nodes = True
sc.world.node_tree.nodes["Background"].inputs[1].default_value = 1.0
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
sc.collection.objects.link(cam)
sc.camera = cam
cam.data.lens = 85
eyes = bpy.data.objects["HeroineEyes"]
ez = sum((eyes.matrix_world @ v.co).z for v in eyes.data.vertices) / len(eyes.data.vertices)
c = Vector((0, 0, ez + 0.04))
for ang in (0, 40):
    a = math.radians(ang)
    cam.location = c + Vector((math.sin(a), -math.cos(a), 0.1)) * 0.8
    cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y").to_euler()
    for show_hair in (True, False):
        bpy.data.objects["hair_ponytail"].hide_render = not show_hair
        sc.render.filepath = os.path.join(out, "mask_%02d_%s.png" % (ang, "hair" if show_hair else "bare"))
        bpy.ops.render.render(write_still=True)
