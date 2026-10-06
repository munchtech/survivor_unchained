import bpy, sys, collections
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r"C:/Users/munch/Desktop/ComfyUI_00008-reduced/autorig_actor.fbx")
for o in bpy.data.objects:
    print("OBJ", o.type, o.name, tuple(round(x, 3) for x in o.dimensions), "loc", tuple(round(x, 3) for x in o.location),
          "rot", tuple(round(x, 3) for x in o.rotation_euler), "scale", tuple(round(x, 3) for x in o.scale), "parent", o.parent.name if o.parent else None)
    if o.type == "MESH":
        me = o.data
        print("  verts", len(me.vertices), "faces", len(me.polygons), "uv layers", [u.name for u in me.uv_layers], "colour attrs", [a.name for a in me.color_attributes])
        print("  vgroups", len(o.vertex_groups))
        sk = me.shape_keys
        print("  shape keys", len(sk.key_blocks) if sk else 0, [k.name for k in sk.key_blocks][:120] if sk else [])
        print("  materials", [m.name for m in me.materials])
        print("  poly sizes", dict(collections.Counter(len(p.vertices) for p in me.polygons)))
    if o.type == "ARMATURE":
        print("  bones", len(o.data.bones))
        print("  ", [b.name for b in o.data.bones])
    if o.animation_data:
        print("  anim", o.animation_data.action.name if o.animation_data.action else None)
for a in bpy.data.actions:
    print("ACTION", a.name, a.frame_range[:], len(a.fcurves))
for im in bpy.data.images:
    print("IMAGE", im.name, im.size[:], im.filepath, im.packed_file is not None)
for m in bpy.data.materials:
    if m.node_tree:
        print("MAT", m.name, [(n.type, n.image.name if getattr(n, 'image', None) else '') for n in m.node_tree.nodes])
bpy.ops.wm.save_as_mainfile(filepath=r"C:/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-wowsurvivors/f1b9be14-0826-4f47-8004-f1d371f2c6a3/scratchpad/male/actor.blend")
