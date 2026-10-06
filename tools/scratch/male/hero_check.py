"""Renders of the hero's blend: rest and a test pose, textured, in Eevee.
    blender -b <blend> --python hero_check.py -- <out prefix> [pose]"""
import bpy, math, os, sys
import numpy as np
from mathutils import Vector, Euler, Quaternion
ARGS = sys.argv[sys.argv.index("--") + 1:]
OUT = ARGS[0]
POSE = ARGS[1] if len(ARGS) > 1 else ""
os.makedirs(os.path.dirname(OUT), exist_ok=True)
sc = bpy.context.scene
sc.render.engine = "BLENDER_EEVEE_NEXT"
sc.render.resolution_x, sc.render.resolution_y = 1000, 1400
sc.view_settings.view_transform = "AgX"
w = bpy.data.worlds.new("w"); sc.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.3, 0.31, 0.33, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 0.5
for nm, rot, e in (("key", (55, 0, 35), 3.5), ("fill", (65, 0, -70), 1.0), ("rim", (75, 0, 180), 2.5)):
    l = bpy.data.lights.new(nm, "SUN"); l.energy = e; l.angle = math.radians(8)
    lo = bpy.data.objects.new(nm, l); sc.collection.objects.link(lo)
    lo.rotation_euler = [math.radians(a) for a in rot]
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
arm = bpy.data.objects["Armature"]
if POSE:
    arm.data.pose_position = "POSE"
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="POSE")
    P = {
        "down": {"upperarm_l": (0, 75, 0), "upperarm_r": (0, -75, 0), "lowerarm_l": (-20, 0, 0), "lowerarm_r": (-20, 0, 0)},
        "action": {"upperarm_l": (-30, 60, 0), "upperarm_r": (-80, -30, 0), "lowerarm_l": (-70, 0, 0), "lowerarm_r": (-50, 0, 0),
                   "thigh_l": (-60, 0, 0), "calf_l": (80, 0, 0), "thigh_r": (25, 0, 0), "calf_r": (30, 0, 0), "spine_02": (10, 0, 15)},
    }[POSE]
    for b, (x, y, z) in P.items():
        pb = arm.pose.bones[b]
        # world-axis rotation about the bone's head
        bpy.context.view_layer.update()
        R = Euler((math.radians(x), math.radians(y), math.radians(z))).to_matrix().to_4x4()
        m = pb.matrix.copy()
        hd = m.translation.copy()
        m.translation = (0, 0, 0)
        m = R @ m
        m.translation = hd
        pb.matrix = m
        bpy.context.view_layer.update()
    bpy.ops.object.mode_set(mode="OBJECT")
meshes = [o for o in bpy.data.objects if o.type == "MESH"]
co = np.concatenate([np.array([(o.matrix_world @ v.co)[:] for v in o.data.vertices]) for o in meshes if o.name.startswith("Hero")])
zmin, zmax = co[:, 2].min(), co[:, 2].max()
H = zmax - zmin


def shot(name, ang, tgt, dist, lens=50, el=0.0):
    a = math.radians(ang)
    t = Vector(tgt)
    cam.data.lens = lens
    cam.location = t + Vector((math.sin(a) * dist, -math.cos(a) * dist, el))
    cam.rotation_euler = (t - cam.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = OUT + "_" + name + ".png"
    bpy.ops.render.render(write_still=True)


views = os.environ.get("VIEWS", "front,side,back,torso,head,hand").split(",")
mid = (0, 0, zmin + H / 2)
wide = 4.6 if not POSE or POSE == "down" else 4.6
if "front" in views: shot("front", 0, mid, wide, 40)
if "side" in views: shot("side", 90, mid, wide, 40)
if "back" in views: shot("back", 180, mid, wide, 40)
if "q" in views: shot("q", 35, mid, wide, 40)
if "torso" in views: shot("torso", 20, (0, 0, zmin + H * 0.66), 1.6, 50)
if "head" in views: shot("head", 25, (0, -0.02, zmax - 0.15), 0.8, 60)
if "hand" in views:
    hb = arm.pose.bones["hand_l"]
    p = arm.matrix_world @ hb.head
    shot("hand", 0, (p.x + 0.08, p.y, p.z), 0.7, 50, 0.3)
if "shoulder" in views:
    hb = arm.pose.bones["upperarm_l"]
    p = arm.matrix_world @ hb.head
    shot("shoulder", 30, (p.x, p.y, p.z - 0.1), 1.0, 50)
    shot("shoulder_b", 150, (p.x, p.y, p.z - 0.1), 1.0, 50)
