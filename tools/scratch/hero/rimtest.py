"""His chest in Blender, grey, lit only from behind (as lookdev's rim), to see whether the hard lines are his shape."""
import math, os
import bpy
import numpy as np
from mathutils import Vector
R = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "r")
grey = bpy.data.materials.new("grey")
grey.use_nodes = True
b = grey.node_tree.nodes["Principled BSDF"]
b.inputs["Base Color"].default_value = (0.5, 0.4, 0.33, 1)
b.inputs["Roughness"].default_value = 0.62
for o in bpy.data.objects:
    if o.type == "MESH":
        o.hide_render = o.name not in ("Hero", "HeroHead")
        for i in range(len(o.data.materials)):
            o.data.materials[i] = grey
sc = bpy.context.scene
sc.render.engine = "BLENDER_EEVEE_NEXT"
sc.render.resolution_x, sc.render.resolution_y = 900, 800
sc.world = bpy.data.worlds.new("w")
sc.world.color = (0.05, 0.05, 0.05)
cam = bpy.data.objects.new("c", bpy.data.cameras.new("c"))
sc.collection.objects.link(cam)
sc.camera = cam
cam.location = Vector((0, -1.3, 1.5))
cam.rotation_euler = (Vector((0, 0, 1.5)) - cam.location).to_track_quat("-Z", "Y").to_euler()
cam.data.angle = math.radians(35)
# lookdev's rim: Godot rotation (-20, 200, 0), its light along -Z of that turn (y up, front +z) -> Blender
sun = bpy.data.objects.new("s", bpy.data.lights.new("s", "SUN"))
sun.data.energy = 4
sc.collection.objects.link(sun)
d = Vector((math.sin(math.radians(200)) * math.cos(math.radians(-20)), math.sin(math.radians(-20)), math.cos(math.radians(200)) * math.cos(math.radians(-20))))
# godot dir of light travel = -Z basis: (-sin(y)cos(x), sin(x), -cos(y)cos(x)); to blender (x, -z, y)
g = Vector((-math.sin(math.radians(200)) * math.cos(math.radians(-20)), math.sin(math.radians(-20)), -math.cos(math.radians(200)) * math.cos(math.radians(-20))))
travel = Vector((g.x, -g.z, g.y))
sun.rotation_euler = (-travel).to_track_quat("Z", "Y").to_euler()
sc.render.filepath = os.path.join(R, "bl_rim.png")
bpy.ops.render.render(write_still=True)
# his shape there: how sharply his surface turns at each edge on his collarbones and neck
him = bpy.data.objects["Hero"]
me = him.data
V = np.array([v.co[:] for v in me.vertices])
me.calc_loop_triangles()
import bmesh
bm = bmesh.new()
bm.from_mesh(me)
angs = []
for e in bm.edges:
    if len(e.link_faces) == 2:
        c = (e.verts[0].co + e.verts[1].co) / 2
        if 1.5 < c.z < 1.66 and abs(c.x) < 0.2 and c.y < 0:
            angs.append(math.degrees(e.calc_face_angle()))
angs = np.array(angs)
print("RIM collarbone edges", len(angs), "dihedral pct 50/90/99/max", np.round(np.percentile(angs, [50, 90, 99, 100]), 1))
