import bpy, sys
argv = sys.argv[sys.argv.index("--")+1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=argv[0])
for o in bpy.data.objects:
    if o.type == 'MESH':
        me = o.data
        tris = sum(len(p.vertices)-2 for p in me.polygons)
        print("MESH", o.name, "verts", len(me.vertices), "tris", tris, "mats", [m.name for m in me.materials], "dims", tuple(round(d,3) for d in o.dimensions), "groups", len(o.vertex_groups))
    elif o.type == 'ARMATURE':
        print("ARM", o.name, "bones", len(o.data.bones), "dims", tuple(round(d,3) for d in o.dimensions), "scale", tuple(o.matrix_world.to_scale()))
        for b in o.data.bones:
            print("  ", b.name, "parent", b.parent.name if b.parent else None, "head", tuple(round(x,3) for x in b.head_local), "tail", tuple(round(x,3) for x in b.tail_local))
for a in bpy.data.actions:
    print("ACTION", a.name, a.frame_range[:], len(a.fcurves))
for i in bpy.data.images:
    print("IMG", i.name, i.size[:], i.file_format)
for m in bpy.data.materials:
    if m.node_tree:
        print("MAT", m.name, [n.type for n in m.node_tree.nodes])
