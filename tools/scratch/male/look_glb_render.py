import bpy, math, os
import numpy as np
from mathutils import Vector
OUT = r"C:/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-wowsurvivors/f1b9be14-0826-4f47-8004-f1d371f2c6a3/scratchpad/male/r"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=r"C:/Users/munch/Desktop/ComfyUI_00008.glb")
body = next(o for o in bpy.data.objects if o.type == "MESH")
bpy.ops.object.select_all(action="DESELECT")
body.select_set(True)
bpy.context.view_layer.objects.active = body
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
co = np.array([v.co[:] for v in body.data.vertices])
k = 1.85 / (co[:, 2].max() - co[:, 2].min())
body.scale = (k, k, k)
body.location = (0, 0, -co[:, 2].min() * k)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
co = np.array([v.co[:] for v in body.data.vertices])
print("GLB bounds", co.min(0).round(3), co.max(0).round(3))
sc = bpy.context.scene
sc.render.engine = "BLENDER_EEVEE_NEXT"
sc.render.resolution_x, sc.render.resolution_y = 900, 1200
w = bpy.data.worlds.new("w"); sc.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.35, 0.35, 0.37, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 0.6
for nm, rot, e in (("key", (50, 0, 30), 3.0), ("fill", (60, 0, -60), 1.2), ("rim", (70, 0, 180), 2.0)):
    l = bpy.data.lights.new(nm, "SUN"); l.energy = e
    lo = bpy.data.objects.new(nm, l); sc.collection.objects.link(lo)
    lo.rotation_euler = [math.radians(a) for a in rot]
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam


def shot(name, ang, tgt, dist, lens=50, el=0.0):
    a = math.radians(ang)
    t = Vector(tgt)
    cam.data.lens = lens
    cam.location = t + Vector((math.sin(a) * dist, -math.cos(a) * dist, el))
    cam.rotation_euler = (t - cam.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = os.path.join(OUT, name + ".png")
    bpy.ops.render.render(write_still=True)


shot("glb_front", 0, (0, 0, 0.95), 3.0, 50)
shot("glb_back", 180, (0, 0, 0.95), 3.0, 50)
shot("glb_head", 0, (0, 0, 1.68), 0.7, 60)
shot("glb_head_q", 35, (0, 0, 1.68), 0.7, 60)
shot("glb_torso", 0, (0, 0, 1.25), 1.4, 50)
shot("glb_hips", 0, (0, 0, 0.9), 0.9, 50)
