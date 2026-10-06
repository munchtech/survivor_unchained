"""Render him unlit (each material's colour only) from given angles, to judge paint apart from light.
env: VIEWS=deg,deg,...  TGT=z  DIST=m  OUT=prefix"""
import math, os
import bpy
from mathutils import Vector
S = r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\r"
for o in bpy.data.objects:
    if o.type != "MESH":
        continue
    for m in o.data.materials:
        if not m or not m.use_nodes:
            continue
        nt = m.node_tree
        tex = next((n for n in nt.nodes if n.type == "TEX_IMAGE" and n.image and n.image.colorspace_settings.name == "sRGB"), None)
        out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
        em = nt.nodes.new("ShaderNodeEmission")
        if tex:
            nt.links.new(tex.outputs["Color"], em.inputs["Color"])
        nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
sc = bpy.context.scene
sc.render.engine = "BLENDER_EEVEE_NEXT"
sc.view_settings.view_transform = "Standard"
sc.render.resolution_x, sc.render.resolution_y = 700, 900
cam = bpy.data.objects.new("c", bpy.data.cameras.new("c"))
sc.collection.objects.link(cam)
sc.camera = cam
sc.world = bpy.data.worlds.new("w")
sc.world.color = (0.2, 0.2, 0.22)
tz = float(os.environ.get("TGT", "1.75"))
d = float(os.environ.get("DIST", "0.75"))
cam.data.angle = math.radians(30)
for deg in os.environ.get("VIEWS", "0,90,180").split(","):
    a = math.radians(float(deg))
    pos = Vector((math.sin(a) * d, -math.cos(a) * d, tz + 0.02))
    cam.location = pos
    cam.rotation_euler = (Vector((0, 0, tz)) - pos).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = os.path.join(S, "%s_%s.png" % (os.environ.get("OUT", "alb"), deg))
    bpy.ops.render.render(write_still=True)
