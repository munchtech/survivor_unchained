import sys, numpy as np
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\tools\scratch\face29")
from gl import G, skinned
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
import clipmeasure as cm
A = sys.argv[1] or cm.A; s = sys.argv[2]; mat_want = sys.argv[3]; ids = [int(x) for x in sys.argv[4:]]
S = cm.Surf(cm.surf(cm.her, lambda n, m: n == "HeroineHead"))
g = G(A + rf"\heroine_hair_{s}.gltf")
M = np.array([cm.HJ[n] if n in cm.HJ else g.W(g.j["skins"][0]["joints"][q]) for q, n in enumerate(g.joint_names(0))]) @ g.ibm(0)
for (node, mesh, k, mat, P, J, Wt, sk, I, ni) in g.meshes():
    if mat != mat_want: continue
    at = g.j["meshes"][g.j["nodes"][ni]["mesh"]]["primitives"][k]["attributes"]
    uv = g.acc(at["TEXCOORD_0"]).astype(float)
    V = skinned(P, J, Wt, M); n = len(V)
    E = np.r_[I[:, [0, 1]], I[:, [1, 2]]]
    nc, lab = connected_components(coo_matrix((np.ones(len(E)), (E[:, 0], E[:, 1])), shape=(n, n)), directed=False)
    for b in ids:
        m = np.nonzero(lab == b)[0]
        us = np.unique(np.round(uv[m, 0], 5))
        mid = m[np.isclose(uv[m, 0], np.sort(us)[len(us) // 2], atol=1e-4)]
        mid = mid[np.argsort(uv[mid, 1])]
        ss = S.sd(V[mid], k=12, reach=0.08) * 1000
        print(f"card {b}: u {us}, {len(mid)} pts (Blender x, y, z-eye mm; gap mm)")
        for i, s_ in zip(mid, ss):
            print("   v=%.3f  (%+6.1f, %+6.1f, %+6.1f)  gap %5.1f" % (uv[i, 1], V[i, 0] * 1000, -V[i, 2] * 1000, (V[i, 1] - 1.748) * 1000, s_))
