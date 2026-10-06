import bpy
import numpy as np
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=r"C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-ae2de192cce8298ca/godot/art/people/heroine.glb")
for o in bpy.data.objects:
    if o.type == "MESH":
        me = o.data
        sk = me.shape_keys
        co = np.array([(o.matrix_world @ v.co)[:] for v in me.vertices])
        print("MESH", o.name, len(me.vertices), "v", len(me.polygons), "f", "keys", len(sk.key_blocks) if sk else 0, "mats", [m.name for m in me.materials],
              "z", co[:, 2].min().round(3), co[:, 2].max().round(3), "cols", [a.name for a in me.color_attributes])
    if o.type == "ARMATURE":
        print("ARM", o.name, len(o.data.bones))
        for b in o.data.bones:
            print("  B", b.name, b.parent.name if b.parent else None, tuple(round(x, 3) for x in (o.matrix_world @ b.head_local)))
for im in bpy.data.images:
    print("IMG", im.name, im.size[:])
