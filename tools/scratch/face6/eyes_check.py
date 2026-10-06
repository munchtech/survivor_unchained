"""blender -b heroine_built.blend --python eyes_check.py : her own face and each face_<id> key seen square on
from in front: each eye's opening (the eyeball seen between her lids, its height through the pupil against
hers) and any of her eyeball seen anywhere else (through her skin: mm2)."""
import bpy
import numpy as np
from mathutils.bvhtree import BVHTree
from scipy import ndimage

head = bpy.data.objects["HeroineHead"]
eyes = bpy.data.objects["HeroineEyes"]
STEP = 0.00025


def shaped(o, key):
    kb = o.data.shape_keys.key_blocks if o.data.shape_keys else None
    co = np.zeros(len(o.data.vertices) * 3)
    o.data.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    if kb and key and key in kb:
        b = np.zeros(len(co) * 3)
        kb[0].data.foreach_get("co", b)
        k = np.zeros(len(co) * 3)
        kb[key].data.foreach_get("co", k)
        co = co + (k - b).reshape(-1, 3)
    M = np.array(o.matrix_world)
    return co @ M[:3, :3].T + M[:3, 3]


keys = [None] + sorted(k.name for k in head.data.shape_keys.key_blocks if k.name.startswith("face_") and not k.name.endswith(("+", "-")))
ekeys = {k.name for k in eyes.data.shape_keys.key_blocks} if eyes.data.shape_keys else set()
base = None
print("EYES_CHECK")
for key in keys:
    V = shaped(head, key)
    E = shaped(eyes, key if key in ekeys else None)
    nh = len(head.data.polygons)
    verts = [tuple(v) for v in V] + [tuple(v) for v in E]
    polys = [tuple(p.vertices) for p in head.data.polygons] + [tuple(i + len(V) for i in p.vertices) for p in eyes.data.polygons]
    bvh = BVHTree.FromPolygons(verts, polys)
    res = []
    for sx in (-1, 1):
        ev = E[np.sign(E[:, 0]) == sx]
        c = ev.mean(0)
        xs = c[0] + np.arange(-0.016, 0.016, STEP)
        zs = c[2] + np.arange(-0.016, 0.016, STEP)
        vis = np.zeros((len(zs), len(xs)), bool)
        for i, z in enumerate(zs):
            for j, x in enumerate(xs):
                hit = bvh.ray_cast((x, -0.5, z), (0, 1, 0), 1.0)
                vis[i, j] = hit[0] is not None and hit[2] >= nh
        lab, n = ndimage.label(vis)
        # (the opening: the eyeball seen nearest the eye's middle)
        jc = np.argmin(np.abs(xs - c[0]))
        col = lab[:, jc]
        main = np.bincount(col[col > 0]).argmax() if (col > 0).any() else 0
        gap = (col == main).sum() * STEP if main else 0.0
        area = (vis & (lab != main)).sum() * STEP * STEP * 1e6
        res.append((gap, area, ((lab == main).sum(0) > 0).sum() * STEP))
    if key is None:
        base = res
    print("%-14s R: open %.1f mm (%.2f of hers), %.1f mm wide, %.2f mm2 seen through skin | L: open %.1f mm (%.2f), %.1f mm wide, %.2f mm2" % (
        key or "her own", 1000 * res[0][0], res[0][0] / base[0][0], 1000 * res[0][2], res[0][1],
        1000 * res[1][0], res[1][0] / base[1][0], 1000 * res[1][2], res[1][1]))
