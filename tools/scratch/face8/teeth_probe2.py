"""Her teeth against her lips, the whole mouth across and from the sides too: rays toward her mouth from the front
and turned 15, 30 and 45 degrees each way, over her lips' height and width; which meet a tooth first (or her
tongue). Per key: her own, and every face_<id>. TEETH_BACK=metres: her teeth tried that much further back first."""
import os
import bpy
import numpy as np
from mathutils.bvhtree import BVHTree

head = bpy.data.objects["HeroineHead"]
inside = [bpy.data.objects[n] for n in ("HeroineTeeth", "HeroineTongue") if n in bpy.data.objects]
back = float(os.environ.get("TEETH_BACK", "0"))


def world(o, key=None):
    me = o.data
    co = np.array([v.co[:] for v in me.vertices])
    if key and me.shape_keys and key in me.shape_keys.key_blocks:
        b = np.array([d.co[:] for d in me.shape_keys.key_blocks[0].data])
        k = np.array([d.co[:] for d in me.shape_keys.key_blocks[key].data])
        co = co + (k - b)
    M = np.array(o.matrix_world)
    return co @ M[:3, :3].T + M[:3, 3]


keys = [None] + sorted(k.name for k in head.data.shape_keys.key_blocks if k.name.startswith("face_") and k.name[-1] not in "+-") if head.data.shape_keys else [None]
for key in keys:
    V = world(head, key)
    parts = [(V, [tuple(p.vertices) for p in head.data.polygons])]
    for o in inside:
        W = world(o, key)
        W[:, 1] += back
        parts.append((W, [tuple(p.vertices) for p in o.data.polygons]))
    allv, allf, owner = [], [], []
    for k, (P, F) in enumerate(parts):
        b = len(allv)
        allv += [tuple(p) for p in P]
        allf += [tuple(i + b for i in f) for f in F]
        owner += [k] * len(F)
    owner = np.array(owner)
    bvh = BVHTree.FromPolygons(allv, allf)
    T = parts[1][0]
    front = T[:, 1].min()
    zc = np.median(T[T[:, 1] < front + 0.004][:, 2])           # (her teeth's front: about where her lips meet)
    out = []
    for yaw, pitch in [(y, p) for p in (-20, 0, 20) for y in (-30, -15, 0, 15, 30)]:
        a, b_ = np.radians(yaw), np.radians(pitch)
        d = np.array([np.sin(a) * np.cos(b_), np.cos(a) * np.cos(b_), np.sin(b_)])   # (toward her: +y, turned; + up from below)
        hits = 0
        n = 0
        for x in np.arange(-0.028, 0.0281, 0.001):
            for z in np.arange(zc - 0.008, zc + 0.008, 0.00025):
                o = np.array([x, front, z]) - d * 0.3
                h = bvh.ray_cast(o, d, 1.0)
                n += 1
                if h[0] is not None and owner[h[2]] > 0:
                    hits += 1
        out.append("%+d/%+d:%d" % (yaw, pitch, hits))
    print("KEY %-14s teeth seen (of %d rays a view): %s" % (key or "her own", n, "  ".join(out)))
