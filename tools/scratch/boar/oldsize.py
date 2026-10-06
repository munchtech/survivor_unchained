import bpy
from mathutils import Vector
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-af551cacc6292152f\godot\art\beasts\boar.glb")
arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
act = bpy.data.actions["Armature|observing"]
arm.animation_data.action = act
bpy.context.scene.frame_set(int(2.5 * 30))
dg = bpy.context.evaluated_depsgraph_get()
heads = [(arm.matrix_world @ pb.head) for pb in arm.pose.bones]
zs = [h.z for h in heads]
mz, mx, my = [], [], []
for o in bpy.data.objects:
    if o.type == "MESH" and o.find_armature():
        e = o.evaluated_get(dg)
        for v in e.data.vertices:
            w = o.matrix_world @ v.co
            mz.append(w.z); mx.append(w.x); my.append(w.y)
ext = max(zs) - min(zs)
s = 0.9 / ext
print("OLD bone extent", round(ext, 3), "mesh z", round(min(mz), 3), round(max(mz), 3), "x", round(max(mx) - min(mx), 3), "y", round(max(my) - min(my), 3))
print("OLD in game: height", round((max(mz) - min(mz)) * s, 3), "length", round(max(max(mx) - min(mx), max(my) - min(my)) * s, 3), "width", round(min(max(mx) - min(mx), max(my) - min(my)) * s, 3))
