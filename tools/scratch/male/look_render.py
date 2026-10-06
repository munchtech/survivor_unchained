"""Render the AccuRIG actor with the TRELLIS paint through its own UVs, to judge
whether the reduction kept them, and how good the sculpt is."""
import bpy, math, os
import numpy as np
from mathutils import Vector
OUT = r"C:/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-wowsurvivors/f1b9be14-0826-4f47-8004-f1d371f2c6a3/scratchpad/male/r"
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r"C:/Users/munch/Desktop/ComfyUI_00008-reduced/autorig_actor.fbx")
arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
body = next(o for o in bpy.data.objects if o.type == "MESH")
for o in (arm, body):
    o.animation_data_clear()
bpy.ops.object.select_all(action="DESELECT")
body.select_set(True); arm.select_set(True)
bpy.context.view_layer.objects.active = body
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
co = np.array([(body.matrix_world @ v.co)[:] for v in body.data.vertices])
k = 1.85 / (co[:, 2].max() - co[:, 2].min())
arm.scale = (k, k, k)
bpy.context.view_layer.update()
bpy.ops.object.select_all(action="DESELECT")
arm.select_set(True); body.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
co = np.array([(body.matrix_world @ v.co)[:] for v in body.data.vertices])
print("FBX bounds", co.min(0).round(3), co.max(0).round(3))
for b in ("CC_Base_Hip", "CC_Base_Head", "CC_Base_L_Hand", "CC_Base_L_Foot", "CC_Base_L_Eye"):
    bb = arm.data.bones[b]
    print("BONE", b, (arm.matrix_world @ bb.head_local)[:])
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=r"C:/Users/munch/Desktop/ComfyUI_00008.glb")
src = next(o for o in bpy.data.objects if o not in before and o.type == "MESH")
mat = src.data.materials[0]
body.data.materials.clear()
body.data.materials.append(mat)
for p in body.data.polygons:
    p.use_smooth = True
bpy.data.objects.remove(src)
body.modifiers.clear()
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
zmin, zmax = co[:, 2].min(), co[:, 2].max()
H = zmax - zmin


def shot(name, ang, tgt, dist, lens=50, el=0.0):
    a = math.radians(ang)
    t = Vector(tgt)
    cam.data.lens = lens
    cam.location = t + Vector((math.sin(a) * dist, -math.cos(a) * dist, el))
    cam.rotation_euler = (t - cam.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = os.path.join(OUT, name + ".png")
    bpy.ops.render.render(write_still=True)


mid = (0, 0, zmin + H / 2)
shot("full_front", 0, mid, 4.2, 35)
shot("full_side", 90, mid, 4.2, 35)
shot("full_back", 180, mid, 4.2, 35)
hz = (arm.matrix_world @ arm.data.bones["CC_Base_Head"].head_local).z
shot("head_front", 0, (0, 0, hz + 0.08), 0.75, 60)
shot("head_q", 35, (0, 0, hz + 0.08), 0.75, 60)
shot("head_side", 90, (0, 0, hz + 0.08), 0.75, 60)
shot("torso", 0, (0, 0, zmin + H * 0.65), 1.5, 50)
shot("hips", 0, (0, 0, zmin + H * 0.48), 1.0, 50)
shot("hand", 0, ((arm.matrix_world @ arm.data.bones["CC_Base_L_Hand"].head_local).x + 0.08, 0, (arm.matrix_world @ arm.data.bones["CC_Base_L_Hand"].head_local).z), 0.6, 50)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "..", "actor_tex.blend"))
