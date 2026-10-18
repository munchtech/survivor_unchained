"""Face 30 H1b: each of her head's vertices' thickness inward (a ray along -normal to the first surface it meets):
her ear's flap is a few millimetres thick both sides, her scalp a head across.
    blender -b heroine_built.blend --python thick.py -- <out.npz>"""
import sys
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

head = bpy.data.objects["HeroineHead"]
me = head.data
mw = np.array(head.matrix_world)
V = np.array([v.co[:] for v in me.vertices]) @ mw[:3, :3].T + mw[:3, 3]
me.calc_normals_split() if hasattr(me, "calc_normals_split") else None
N = np.array([v.normal[:] for v in me.vertices]) @ np.linalg.inv(mw[:3, :3])
N /= np.linalg.norm(N, axis=1)[:, None]
polys = [p.vertices[:] for p in me.polygons]
bvh = BVHTree.FromPolygons([Vector(v) for v in V], polys)
th = np.full(len(V), 1.0)
for i in range(len(V)):
    o = Vector(V[i] - N[i] * 1e-4)
    hit = bvh.ray_cast(o, Vector(-N[i]), 1.0)
    if hit[0] is not None:
        th[i] = hit[3] + 1e-4
np.savez_compressed(sys.argv[sys.argv.index("--") + 1], th=th, V=V, N=N)
print("THICK", (th < 0.012).sum(), "vertices under 12 mm")
# (and each ear key's movement of each vertex, for the ear's own extent)
kb = me.shape_keys.key_blocks if me.shape_keys else {}
base = np.array([d.co[:] for d in kb[0].data]) if kb else None
mv = {k.name: np.linalg.norm(np.array([d.co[:] for d in k.data]) - base, axis=1) for k in kb if "ear" in k.name.lower()}
np.savez_compressed(sys.argv[sys.argv.index("--") + 1].replace(".npz", "_keys.npz"), **mv)
print("KEYS", {k: round(float(v.max()), 4) for k, v in mv.items()})
