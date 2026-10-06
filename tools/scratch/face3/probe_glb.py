import bpy, sys, numpy as np
path = sys.argv[sys.argv.index("--") + 1]
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o)
bpy.ops.import_scene.gltf(filepath=path)
for o in bpy.data.objects:
    print("OBJ", o.name, o.type, [list(r) for r in o.matrix_world])
    if o.type != "MESH":
        continue
    me = o.data
    V = np.array([v.co[:] for v in me.vertices])
    print("NV", len(V), "NF", len(me.polygons), "min", V.min(0), "max", V.max(0))
    print("UV layers", [u.name for u in me.uv_layers])
    uv = np.array([d.uv[:] for d in me.uv_layers[0].data])
    print("UV min", uv.min(0), "max", uv.max(0))
    # vertex -> uv
    vu = np.zeros((len(V), 2))
    for l in me.loops:
        vu[l.vertex_index] = uv[l.index]
    for q in ((0.5, 0.5), (0.5, 0.3), (0.3, 0.5), (0.5, 0.7)):
        k = np.argmin(((vu - q) ** 2).sum(1))
        print("near uv", q, "->", vu[k], V[k])
    print("mats", [m.name for m in me.materials])
