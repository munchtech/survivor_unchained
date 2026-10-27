# Body 2 A: mesh sanity of a shape vs a reference (same topology): flipped/turned triangles, edge stretch, L/R mismatch.
#   python qual.py <work> <ref P.npy> <new P.npy>
import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import load, fan, edges
WK, A_, B_ = sys.argv[1:4]; a = load(os.path.join(WK, "ar.npz")); P0 = np.load(A_); P1 = np.load(B_)
T, _, _ = fan(a["ls"], a["lt"], a["lv"]); E = edges(a["ls"], a["lt"], a["lv"])
n = lambda P: np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
n0, n1 = n(P0), n(P1); c = (n0 * n1).sum(1) / np.maximum(np.linalg.norm(n0, axis=1) * np.linalg.norm(n1, axis=1), 1e-20)
mv = np.linalg.norm(P1 - P0, axis=1) > 1e-5; tm = mv[T].any(1)
ang = np.degrees(np.arccos(np.clip(c[tm], -1, 1)))
l0 = np.linalg.norm(P0[E[:, 0]] - P0[E[:, 1]], axis=1); l1 = np.linalg.norm(P1[E[:, 0]] - P1[E[:, 1]], axis=1); em = mv[E].any(1); r = l1[em] / l0[em]
print("moved verts %d; triangles turned deg p50 %.1f p99 %.1f max %.1f, flipped %d; edge ratio p1 %.2f p50 %.2f p99 %.2f" % (
    mv.sum(), np.median(ang), np.percentile(ang, 99), ang.max(), int((ang > 90).sum()), np.percentile(r, 1), np.median(r), np.percentile(r, 99)))
# dihedral roughness on moved skin: angle between neighbouring triangle normals (p99), ref vs new
from collections import defaultdict
def dih(P):
    nn = n(P); nn /= np.maximum(np.linalg.norm(nn, axis=1, keepdims=True), 1e-20)
    e = np.sort(np.r_[T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]], 1); t = np.tile(np.arange(len(T)), 3)
    o = np.lexsort(e.T[::-1]); e = e[o]; t = t[o]; same = (e[1:] == e[:-1]).all(1)
    i, j = t[:-1][same], t[1:][same]; k = tm[i] | tm[j]
    return np.degrees(np.arccos(np.clip((nn[i[k]] * nn[j[k]]).sum(1), -1, 1)))
d0, d1 = dih(P0), dih(P1); print("dihedral on moved skin deg p50/p95/p99/max: ref %.1f/%.1f/%.1f/%.1f new %.1f/%.1f/%.1f/%.1f" % (
    *np.percentile(d0, [50, 95, 99]), d0.max(), *np.percentile(d1, [50, 95, 99]), d1.max()))
