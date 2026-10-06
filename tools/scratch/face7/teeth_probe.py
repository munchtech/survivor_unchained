"""Her teeth against her lips in the built blend: from in front along her middle, what is seen first (head or teeth),
and the teeth's foremost point against her lips' surface there."""
import bpy
import numpy as np
from mathutils.bvhtree import BVHTree

head = bpy.data.objects["HeroineHead"]
teeth = bpy.data.objects["HeroineTeeth"]


def world(o, key=None):
    me = o.data
    co = np.array([v.co[:] for v in me.vertices])
    if key and me.shape_keys and key in me.shape_keys.key_blocks:
        b = np.array([d.co[:] for d in me.shape_keys.key_blocks[0].data])
        k = np.array([d.co[:] for d in me.shape_keys.key_blocks[key].data])
        co = co + (k - b)
    M = np.array(o.matrix_world)
    return co @ M[:3, :3].T + M[:3, 3]


for key in (None, "face_vixen", "face_saffron"):
    V, T = world(head, key), world(teeth, key)
    nh = len(head.data.polygons)
    bvh = BVHTree.FromPolygons([tuple(v) for v in V] + [tuple(v) for v in T],
                               [tuple(p.vertices) for p in head.data.polygons] + [tuple(i + len(V) for i in p.vertices) for p in teeth.data.polygons])
    mid = T[np.abs(T[:, 0]) < 0.01]
    zs = np.arange(mid[:, 2].min() - 0.01, mid[:, 2].max() + 0.01, 0.00025)
    seen = []
    for x in (-0.006, 0.0, 0.006):
        for z in zs:
            h = bvh.ray_cast((x, -0.5, z), (0, 1, 0), 1.0)
            if h[0] is not None and h[2] >= nh:
                seen.append((x, z))
    print("KEY", key or "her own", "teeth seen from in front at %d of %d rays along her middle" % (len(seen), 3 * len(zs)),
          "z %.4f..%.4f" % (min(s[1] for s in seen), max(s[1] for s in seen)) if seen else "")
