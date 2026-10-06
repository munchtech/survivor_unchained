"""Paint colour at 3D probe points on each mesh (nearest surface, by its UVs and image)."""
import bpy, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
probes = {"neck front": (0, -0.08, 1.62), "neck side": (0.07, -0.0, 1.66), "nape": (0, 0.06, 1.70), "traps": (0.17, 0.02, 1.6),
          "chest": (0.1, -0.15, 1.42), "back": (0.1, 0.12, 1.42), "upper arm": (0.45, 0.0, 1.58), "forearm": (0.75, 0, 1.58),
          "belly": (0.05, -0.13, 1.15), "thigh": (0.12, -0.08, 0.8), "cheek": (0.05, -0.1, 1.79), "scalp": (0, 0.0, 1.97),
          "head back": (0, 0.1, 1.82), "graft": (0.0, -0.06, 1.69)}
imgs = {}
for o in bpy.data.objects:
    if o.type != "MESH" or o.name not in ("Hero", "HeroHead"):
        continue
    me = o.data
    me.calc_loop_triangles()
    V = [o.matrix_world @ v.co for v in me.vertices]
    tris = [t for t in me.loop_triangles]
    bvh = BVHTree.FromPolygons(V, [t.vertices[:] for t in tris])
    uvd = me.uv_layers.active.data
    for name, p in probes.items():
        loc, nor, idx, d = bvh.find_nearest(Vector(p), 0.08)
        if loc is None:
            continue
        t = tris[idx]
        mat = me.materials[t.material_index]
        img = next(n.image for n in mat.node_tree.nodes if n.type == "TEX_IMAGE" and n.image)
        if img.name not in imgs:
            imgs[img.name] = np.array(img.pixels[:], np.float32).reshape(img.size[1], img.size[0], 4)
        a = imgs[img.name]
        from mathutils.geometry import barycentric_transform
        uvs = [Vector((*uvd[l].uv, 0)) for l in t.loops]
        q = barycentric_transform(loc, V[t.vertices[0]], V[t.vertices[1]], V[t.vertices[2]], *uvs)
        x, y = int(q[0] * a.shape[1]), int(q[1] * a.shape[0])
        c = a[max(y - 6, 0):y + 6, max(x - 6, 0):x + 6, :3].reshape(-1, 3).mean(0)
        print("PROBE %-10s %-9s %-24s d=%.3f %s" % (name, o.name, mat.name, d, np.round(c, 3)))
