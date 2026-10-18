"""Cards on her forehead (bind pose): vertices with |angle| < TH deg, between her brows (eye+15 mm) and her hairline
(at that angle), within NEAR of the skin. Each card's middle path printed (x, height over eye, gap) every few points."""
import sys, os, numpy as np
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\tools\scratch\face29")
from gl import G, skinned
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
import clipmeasure as cm
A = sys.argv[1] or cm.A
S = cm.Surf(cm.surf(cm.her, lambda n, m: n == "HeroineHead"))
eye = 1.748; TH = float(os.environ.get("TH", "40")); NEAR = float(os.environ.get("NEAR", "0.02"))
def hl(th):
    return np.interp(np.abs(th), [0, 20, 40, 55, 65, 75, 84, 100, 120, 145, 180], [0.064, 0.064, 0.053, 0.036, 0.026, 0.006, -0.010, -0.035, -0.048, -0.062, -0.074])
for s in sys.argv[2:]:
    g = G(A + rf"\heroine_hair_{s}.gltf")
    M = np.array([cm.HJ[n] if n in cm.HJ else g.W(g.j["skins"][0]["joints"][q]) for q, n in enumerate(g.joint_names(0))]) @ g.ibm(0)
    for (node, mesh, k, mat, P, J, Wt, sk, I, ni) in g.meshes():
        if mat in ("hair_cap", "hair_tie"): continue
        at = g.j["meshes"][g.j["nodes"][ni]["mesh"]]["primitives"][k]["attributes"]
        uv = g.acc(at["TEXCOORD_0"]).astype(float); col = g.acc(at["COLOR_0"]).astype(float)
        if col.max() > 1.5: col /= 65535.0
        V = skinned(P, J, Wt, M); n = len(V)
        E = np.r_[I[:, [0, 1]], I[:, [1, 2]]]
        nc, lab = connected_components(coo_matrix((np.ones(len(E)), (E[:, 0], E[:, 1])), shape=(n, n)), directed=False)
        th = np.degrees(np.arctan2(V[:, 0], V[:, 2]))
        rise = V[:, 1] - eye - hl(th)
        cand = (np.abs(th) < TH) & (V[:, 1] > eye + 0.012) & (rise < -0.002) & (V[:, 2] > 0.0)
        sd = np.full(n, np.inf); sd[cand] = S.sd(V[cand], k=12, reach=0.06)
        cand &= sd < NEAR
        bad = np.unique(lab[cand])
        print(f"== {s} [{mat}] {len(bad)} cards on her forehead (within {NEAR*1000:.0f} mm)")
        for b in bad:
            m = np.nonzero(lab == b)[0]
            K = len(m) // 3
            order = m[np.argsort(uv[m, 1])]          # root (v small) to tip
            # middle column: the vertices at u = middle (the 3 columns share v): take every 3rd after sorting by v then u
            vv = np.round(uv[m, 1], 5); us = np.unique(np.round(uv[m, 0], 5))
            mid = m[np.isclose(uv[m, 0], np.sort(us)[len(us) // 2], atol=1e-4)] if len(us) >= 3 else m
            mid = mid[np.argsort(-uv[mid, 1])]       # v runs 1 at root to 0 at tip in the atlas (1 - f)
            ss = S.sd(V[mid], k=12, reach=0.08) * 1000
            pts = " ".join("(%+.0f,%+.0f,%.0f)" % (V[i, 0] * 1000, (V[i, 1] - eye) * 1000, s_) for i, s_ in zip(mid[::max(1, len(mid) // 8)], ss[::max(1, len(mid) // 8)]))
            print(f"  card {b:5d}: {len(m)} v, {cand[m].sum()} on forehead, alpha {col[m,3].max():.2f} width~{np.linalg.norm(V[m][0]-V[m][-1])*0:.0f}: " + pts)
