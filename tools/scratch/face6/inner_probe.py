"""Her head's skin facing inward behind her cheeks (an inner layer): which faces, how far behind the outer skin,
and whether any of it comes through, for her own face and each face_<id>."""
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

head = bpy.data.objects["HeroineHead"]
me = head.data
kb = me.shape_keys.key_blocks
B = np.zeros(len(me.vertices) * 3)
kb[0].data.foreach_get("co", B)
B = B.reshape(-1, 3)
mw = np.array(head.matrix_world)
F = [list(p.vertices) for p in me.polygons]


def shaped(key):
    V = B.copy()
    if key:
        k = np.zeros(len(V) * 3)
        kb[key].data.foreach_get("co", k)
        V = k.reshape(-1, 3)
    return V @ mw[:3, :3].T + mw[:3, 3]


def normals(V):
    N = np.zeros_like(V)
    for f in F:
        N[f] += np.cross(V[f[1]] - V[f[0]], V[f[-1]] - V[f[0]])
    N /= np.linalg.norm(N, axis=1)[:, None] + 1e-12
    own = np.array([v.normal[:] for v in me.vertices]) @ mw[:3, :3].T
    return N if (N * own).sum(1).mean() > 0 else -N


V = shaped(None)
N = normals(V)
# faces of the front of her face (y < -0.06, between chin and brow) whose normal points back into her
fc = np.array([V[f].mean(0) for f in F])
fn = np.array([N[f].mean(0) for f in F])
inner = np.where((fc[:, 1] < -0.06) & (fc[:, 2] > 1.66) & (fc[:, 2] < 1.76) & (fn[:, 1] > 0.3))[0]
mats = {}
for i in inner:
    m = me.polygons[i].material_index
    mats[m] = mats.get(m, 0) + 1
print("INNER faces facing back, in front of her face:", len(inner), "materials", mats)
iv = sorted({v for i in inner for v in F[i]})
print("  their points: x %.3f..%.3f  y %.3f..%.3f  z %.3f..%.3f" % (V[iv, 0].min(), V[iv, 0].max(), V[iv, 1].min(), V[iv, 1].max(), V[iv, 2].min(), V[iv, 2].max()))
# connected pieces of them
adj = {}
for i in inner:
    for v in F[i]:
        adj.setdefault(v, []).append(i)
seen = set()
pieces = []
for i in inner:
    if i in seen:
        continue
    st, piece = [i], []
    seen.add(i)
    while st:
        j = st.pop()
        piece.append(j)
        for v in F[j]:
            for k in adj[v]:
                if k not in seen:
                    seen.add(k)
                    st.append(k)
    pieces.append(piece)
pieces.sort(key=len, reverse=True)
for p in pieces[:6]:
    c = fc[p].mean(0)
    print("  piece of %d faces about (%.3f %.3f %.3f)" % (len(p), *c))
keys = [None] + sorted(k.name for k in kb if k.name.startswith("face_") and not k.name.endswith(("+", "-")))
outer = [i for i in range(len(F)) if i not in set(inner)]
for key in keys:
    V = shaped(key)
    bvh = BVHTree.FromPolygons([tuple(v) for v in V], [tuple(F[i]) for i in outer])
    gaps = []
    for v in iv:
        hit = bvh.ray_cast(Vector(V[v]), Vector((0, -1, 0)), 0.01)
        if hit[0] is not None:
            gaps.append(hit[3])                          # (+: the inner layer behind the outer skin)
            continue
        hit = bvh.ray_cast(Vector(V[v]), Vector((0, 1, 0)), 0.01)
        if hit[0] is not None:
            gaps.append(-hit[3])                         # (-: in front of it, seen through it)
    g = np.array(gaps)
    print("%-14s inner layer behind her skin: min %.2f mm, 5%% %.2f mm, median %.2f mm; %d points within 0.3 mm or through" % (
        key or "her own", 1000 * g.min(), 1000 * np.percentile(g, 5), 1000 * np.median(g), (g < 0.0003).sum()))
