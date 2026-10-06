"""Render his chest in Blender with the relief, to see if the blotches are in the map."""
import math, os, sys
import bpy
from mathutils import Vector
S = r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\r"
him = bpy.data.objects["Hero"]
for o in bpy.data.objects:
    if o.type == "MESH":
        o.hide_render = o.name not in ("Hero", "HeroHead")
mat = him.data.materials[0]
nt = mat.node_tree
bsdf = nt.nodes["Principled BSDF"]
bsdf.inputs["Roughness"].default_value = 0.6
for n in nt.nodes:
    if n.type == "TEX_IMAGE" and n.image.colorspace_settings.name == "sRGB":
        if os.environ.get("FLAT"):
            nt.links.remove(n.outputs["Color"].links[0])
            bsdf.inputs["Base Color"].default_value = (0.5, 0.4, 0.33, 1)
if os.environ.get("NONRM"):
    for l in list(bsdf.inputs["Normal"].links):
        nt.links.remove(l)
sc = bpy.context.scene
sc.render.engine = "BLENDER_EEVEE_NEXT"
sc.render.resolution_x, sc.render.resolution_y = 900, 1000
cam = bpy.data.objects.new("c", bpy.data.cameras.new("c"))
sc.collection.objects.link(cam)
a = math.radians(-30)
d = 0.7
# lookdev: ORBIT deg,height,dist,target -> pos (sin a * d, height, cos a * d) in y-up, front +z (godot) => blender front -y
pos = Vector((math.sin(a) * d, -math.cos(a) * d, 1.6))
cam.location = pos
tgt = Vector((0, 0, 1.72))
cam.rotation_euler = (tgt - pos).to_track_quat("-Z", "Y").to_euler()
cam.data.angle = math.radians(35 * 900 / 1000)
sc.camera = cam
sun = bpy.data.objects.new("s", bpy.data.lights.new("s", "SUN"))
sun.data.energy = 3
sun.rotation_euler = (math.radians(55), 0, math.radians(30))
sc.collection.objects.link(sun)
sc.world = bpy.data.worlds.new("w")
sc.world.color = (0.3, 0.3, 0.32)
sc.render.filepath = os.path.join(S, os.environ.get("OUT", "bl_chest.png"))
bpy.ops.render.render(write_still=True)
