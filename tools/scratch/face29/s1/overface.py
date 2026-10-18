"""Cards over her face (bind pose): each card (connected strip) with any strand vertex in front of her face below her
hairline: material, vertices, root, how far down, gap to skin, alpha. usage: overface.py ART style [style...]"""
import sys, numpy as np
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\tools\scratch\face29")
from gl import G, skinned
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
import clipmeasure as cm
A = sys.argv[1] or cm.A
S = cm.Surf(cm.surf(cm.her, lambda n, m: n == "HeroineHead"))
eye = 1.748
def hl(th):  # her hairline over her eyes (face_shapes.HAIRLINE), th degrees from front
    return np.interp(np.abs(th), [0, 20, 40, 55, 65, 75, 84, 100, 120, 145, 180], [0.064, 0.064, 0.053, 0.036, 0.026, 0.006, -0.010, -0.035, -0.048, -0.062, -0.074])
for s in sys.argv[2:]:
    g = G(A + rf"\heroine_hair_{s}.gltf")
    M = np.array([cm.HJ[n] if n in cm.HJ else g.W(g.j["skins"][0]["joints"][q]) for q, n in enumerate(g.joint_names(0))]) @ g.ibm(0)
    for (node, mesh, k, mat, P, J, Wt, sk, I, ni) in g.meshes():
        if mat in ("hair_cap", "hair_tie"): continue
        at = g.j["meshes"][g.j["nodes"][ni]["mesh"]]["primitives"][k]["attributes"]
        uv = g.acc(at["TEXCOORD_0"]).astype(float); col = g.acc(at["COLOR_0"]).astype(float)
        if col.max() > 1.5: col /= 65535.0
        V = skinned(P, J, Wt, M)
        n = len(V)
        E = np.r_[I[:, [0, 1]], I[:, [1, 2]]]
        nc, lab = connected_components(coo_matrix((np.ones(len(E)), (E[:, 0], E[:, 1])), shape=(n, n)), directed=False)
        th = np.degrees(np.arctan2(V[:, 0], V[:, 2]))
        rise = V[:, 1] - eye - hl(th)
        # over her face: in front (z > 0.04), below her hairline, within the head's width
        over = (V[:, 2] > 0.03) & (rise < -0.003) & (V[:, 1] > eye - 0.13) & (np.abs(th) < float(__import__("os").environ.get("TH", "80")))
        sd = np.full(n, np.inf); sd[over] = S.sd(V[over], k=12, reach=0.05)
        near = np.isfinite(sd) & (sd < float(__import__("os").environ.get("NEAR", "1")))
        over &= near
        bad = np.unique(lab[over])
        print(f"== {s} [{mat}] {nc} cards, {len(bad)} reach over her face")
        rows = []
        for b in bad:
            m = lab == b; o = m & over
            root = V[m][np.argmin(uv[m, 1])] if True else None
            g_ = sd[o][np.isfinite(sd[o])] * 1000
            vmin = uv[m, 1].min(); vmax = uv[m, 1].max()
            rows.append((o.sum(), b, m.sum(), th[m][np.argmax(uv[m,1])], (root[1]-eye)*1000, rise[o].min()*1000, np.median(g_) if len(g_) else np.nan, g_.min() if len(g_) else np.nan, col[m, 3].max(), col[m, 0].mean(), col[m, 2].mean(), np.ptp(V[m], 0).max() * 1000))
        rows.sort(reverse=True)
        for r in rows[:14]:
            print("  card %5d: %3d of %4d v over face; root %+5.0f mm vs eye, tip angle %+4.0f; deepest %5.0f mm below hairline; gap med %4.1f min %4.1f mm; alpha %.2f depth %.2f blue %.2f; extent %3.0f mm" % (r[1], r[0], r[2], r[4], r[3], r[5], r[6], r[7], r[8], r[9], r[10], r[11]))
