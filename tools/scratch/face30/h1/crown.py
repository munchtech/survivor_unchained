"""H8: where the pixie's cards leave its cap bare on top of her head (nearest card point, alpha-weighted)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from headlib import *  # noqa
from scipy.spatial import cKDTree
A = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] else ART
g = G(os.path.join(A, "heroine_hair_pixie.gltf")); M = mats_for(g)
cap, card = [], []
for (node, mesh, k, mat, P, J, Wt, sk, I, ni) in g.meshes():
    at = g.j["meshes"][g.j["nodes"][ni]["mesh"]]["primitives"][k]["attributes"]
    V = skinned(P, J, Wt, M); col = g.acc(at["COLOR_0"]).astype(float)
    if col.max() > 1.5: col /= 65535.0
    uv = g.acc(at["TEXCOORD_0"]).astype(float)
    (cap if mat == "hair_cap" else card if mat == "hair" else []).append((V, col, uv))
CV = np.vstack([c[0] for c in cap])
KV = np.vstack([c[0] for c in card]); KA = np.concatenate([c[1][:, 3] for c in card])
top = CV[:, 1] > EYE_Y + 0.07
ctr = CV[top].mean(0)
# cover over each cap point: card points within 2.5 mm whose alpha > 0.5
t = cKDTree(KV[KA > 0.5])
n = np.array([len(x) for x in t.query_ball_point(CV[top], 0.0025)])
d, _ = t.query(CV[top])
print("top cap points %d; bare (no card point with alpha > 0.5 within 2.5 mm): %d; nearest > 4 mm: %d" % (top.sum(), (n == 0).sum(), (d > 0.004).sum()))
b = CV[top][n == 0]
if len(b):
    print("bare at (x, height over eye, z) mm: mean", ((b.mean(0) - [0, EYE_Y, 0]) * 1e3).round(0), "spread", (b.std(0) * 1e3).round(0))
    H, xe, ze = np.histogram2d(b[:, 0] * 1e3, b[:, 2] * 1e3, bins=[np.arange(-60, 61, 10), np.arange(-80, 81, 10)])
    print(" bare by x (rows) and z (cols, back to front)", ze.astype(int)); [print("  %+4d" % x0, r) for r, x0 in zip(H.astype(int), xe)]
