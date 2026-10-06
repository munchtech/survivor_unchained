"""Which of her cheek's points under her eyes a front view cannot see, shaped as a preset (PROBE_KEY), and what hides them."""
import os
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

KEY = os.environ.get("PROBE_KEY", "face_saffron")


def shaped(o):
    me = o.data
    V = np.zeros(len(me.vertices) * 3)
    me.vertices.foreach_get("co", V)
    V = V.reshape(-1, 3)
    if me.shape_keys and KEY in me.shape_keys.key_blocks:
        kb = me.shape_keys.key_blocks
        b = np.zeros(len(V) * 3)
        kb[0].data.foreach_get("co", b)
        k = np.zeros(len(V) * 3)
        kb[KEY].data.foreach_get("co", k)
        V = b.reshape(-1, 3) + (k - b).reshape(-1, 3)
    mw = np.array(o.matrix_world)
    return V @ mw[:3, :3].T + mw[:3, 3]


objs = [bpy.data.objects[n] for n in ("HeroineHead", "Heroine", "HeroineEyes")]
vs, fs, owner = [], [], []
for o in objs:
    b = len(vs)
    V = shaped(o)
    vs += [tuple(p) for p in V]
    for p in o.data.polygons:
        fs.append([b + i for i in p.vertices])
        owner.append(o.name)
bvh = BVHTree.FromPolygons(vs, fs)
head = objs[0]
V = shaped(head)
N = np.zeros_like(V)
for p in head.data.polygons:
    q = list(p.vertices)
    N[q] += np.cross(V[q[1]] - V[q[0]], V[q[-1]] - V[q[0]])
N /= np.linalg.norm(N, axis=1)[:, None] + 1e-12
own = np.array([v.normal[:] for v in head.data.vertices])
if (N * own).sum(1).mean() < 0:
    N = -N
E = shaped(objs[2])
eye_z = E[:, 2].mean()
from PIL import Image
_pp = os.environ.get("PROBE_PAINT")
A = np.asarray(Image.open(_pp))[::-1, :, 3] / 255.0
uvd = head.data.uv_layers[0].data
UVV = np.zeros((len(V), 2))
cnt = np.zeros(len(V))
for p in head.data.polygons:
    for li in p.loop_indices:
        vi = head.data.loops[li].vertex_index
        UVV[vi] += uvd[li].uv[:]
        cnt[vi] += 1
UVV /= np.maximum(cnt, 1)[:, None]
S = A.shape[0]
alpha = A[np.clip((UVV[:, 1] * S).astype(int), 0, S - 1), np.clip((UVV[:, 0] * S).astype(int), 0, S - 1)]
hole_f = []
for p in head.data.polygons:
    uvc = np.mean([uvd[li].uv[:] for li in p.loop_indices], 0)
    al = A[min(int(uvc[1] * S), S - 1), min(int(uvc[0] * S), S - 1)]
    c = V[list(p.vertices)].mean(0)
    if al < 0.1 and abs(c[0]) > 0.01 and eye_z - 0.045 < c[2] < eye_z - 0.012 and c[1] < -0.07:
        hole_f.append(p.index)
sel = sorted({v for f in hole_f for v in head.data.polygons[f].vertices})
sel = np.array(sel, int)
print("HOLE faces on her cheeks:", len(hole_f), "points", len(sel))
for i in sel[:30]:
    print("  hole v%d at (%.4f %.4f %.4f) uv %s n %s alpha %.2f" % (i, *V[i], np.round(UVV[i], 4), np.round(N[i], 2), alpha[i]))
import math
from collections import Counter
for name, ang in (("front", 0.0), ("left", 55.0), ("right", -55.0)):
    a = math.radians(ang)
    d = Vector((math.sin(a), -math.cos(a), 0.0))         # (toward the viewer: -fwd)
    hidden = []
    for i in sel:
        p = Vector(V[i]) + Vector(N[i]) * 0.0008 + d * 0.0005
        hit = bvh.ray_cast(p, d, 2.0)
        if hit[0] is not None:
            hidden.append((i, owner[hit[2]], hit[3], hit[2]))
    print("VIEW", name, len(hidden), "of", len(sel), "hidden;", Counter(h[1] for h in hidden))
    for i, o, dist, f in hidden[:30]:
        fc = np.mean([vs[j] for j in fs[f]], 0)
        print("   v%d hit %s face %d at %.1f mm (its middle %s)" % (i, o, f, dist * 1000, np.round(fc, 4)))
