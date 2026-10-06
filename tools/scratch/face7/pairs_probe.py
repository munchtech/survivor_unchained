# Points of her body that nearly meet but are not joined by smooth_normals' rounding (1e-5 m): how many, how far
# apart, where. And her surface's folds: corners whose joined smooth normal turns from their own face.
import bpy
import numpy as np
from scipy.spatial import cKDTree

me = bpy.data.objects["Heroine"].data
V = np.array([v.co[:] for v in me.vertices])
key = np.unique(np.round(V / 1e-5).astype(np.int64), axis=0, return_inverse=True)[1].ravel()
pairs = np.array(sorted(cKDTree(V).query_pairs(0.0005)))
d = np.linalg.norm(V[pairs[:, 0]] - V[pairs[:, 1]], axis=1)
split = key[pairs[:, 0]] != key[pairs[:, 1]]
print("PAIRS within 0.5 mm: %d; joined by rounding %d; not joined %d" % (len(pairs), (~split).sum(), split.sum()))
for lo, hi in ((0, 1e-6), (1e-6, 1e-5), (1e-5, 5e-5), (5e-5, 1e-4), (1e-4, 2e-4), (2e-4, 5e-4)):
    m = split & (d >= lo) & (d < hi)
    if m.any():
        c = V[pairs[m, 0]]
        print("  unjoined %.0e..%.0e m: %d pairs; |x|<5mm: %d; z %.2f..%.2f" % (lo, hi, m.sum(), (np.abs(c[:, 0]) < 0.005).sum(), c[:, 2].min(), c[:, 2].max()))
# folds
acc = np.zeros((key.max() + 1, 3))
FN = np.zeros((len(me.polygons), 3))
for p in me.polygons:
    vs = list(p.vertices)
    for i in range(1, len(vs) - 1):
        a, b, c = V[vs[0]], V[vs[i]], V[vs[i + 1]]
        fn = np.cross(b - a, c - a)
        FN[p.index] += fn
        for k in (vs[0], vs[i], vs[i + 1]):
            acc[key[k]] += fn
acc /= np.linalg.norm(acc, axis=1)[:, None] + 1e-12
FN /= np.linalg.norm(FN, axis=1)[:, None] + 1e-12
LV = np.array([l.vertex_index for l in me.loops])
LP = np.zeros(len(me.loops), int)
for p in me.polygons:
    LP[p.loop_start:p.loop_start + p.loop_total] = p.index
dot = (acc[key[LV]] * FN[LP]).sum(1)
CN = np.array([n.vector[:] for n in me.corner_normals])
hd = (CN * FN[LP]).sum(1)
for t in (0.0, 0.2, 0.5):
    m = dot < t
    print("FOLD corners whose joined normal is under %.1f to their face: %d (theirs under it: %d)" % (t, m.sum(), (m & (hd < t)).sum()))
m = dot < 0.2
P = V[LV[m]]
for nm, r in (("z<0.2 feet", P[:, 2] < 0.2), ("hands |x|>0.55", np.abs(P[:, 0]) > 0.55), ("underbust z1.28-1.38 y<-0.05", (P[:, 2] > 1.28) & (P[:, 2] < 1.38) & (P[:, 1] < -0.05)),
              ("head z>1.5", P[:, 2] > 1.5), ("groin z0.8-0.95 |x|<0.1", (P[:, 2] > 0.8) & (P[:, 2] < 0.95) & (np.abs(P[:, 0]) < 0.1)),
              ("armpit z1.25-1.45 |x|0.12-0.22", (P[:, 2] > 1.25) & (P[:, 2] < 1.45) & (np.abs(P[:, 0]) > 0.12) & (np.abs(P[:, 0]) < 0.22))):
    print("  folds at %s: %d" % (nm, r.sum()))
