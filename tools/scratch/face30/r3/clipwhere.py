"""Face 30 r3: where a style's hair strands sit >1 mm inside her head (bind pose), by clipmeasure's own maths.  run from tools/scratch/face29: python ../face30/r3/clipwhere.py pixie"""
import sys, os, numpy as np
sys.path.insert(0, os.getcwd())
sys.argv, s = sys.argv[:1], sys.argv[1]
import clipmeasure as cm
g = cm.G(cm.A + rf"\heroine_hair_{s}.gltf"); names = g.joint_names(0)
mats = np.array([cm.HJ[n] if n in cm.HJ else g.W(g.j["skins"][0]["joints"][q]) for q, n in enumerate(names)]) @ g.ibm(0)
for (node, mesh, k, mat, P, J, Wt, sk, I, ni) in g.meshes():
    if mat != "hair": continue
    at = g.j["meshes"][g.j["nodes"][ni]["mesh"]]["primitives"][k]["attributes"]
    uv = g.acc(at["TEXCOORD_0"]).astype(float); now = cm.skinned(P, J, Wt, mats)
    d = cm.headS.sd(now); bad = (d < -0.001) & (uv[:, 1] >= 0.1)
    print(mat, bad.sum()); c = now[bad]
    print("  y (up) %.3f-%.3f  z (front) %.3f-%.3f  x %.3f-%.3f" % (c[:, 1].min(), c[:, 1].max(), c[:, 2].min(), c[:, 2].max(), c[:, 0].min(), c[:, 0].max()))
    back = c[:, 2] < np.median(now[:, 2]); print("  behind her middle:", back.sum(), " v (tip near 1):", np.round(np.percentile(uv[bad, 1], [10, 50, 90]), 2))
    w = np.argsort(d[bad])[:8]; print("  worst:", [(round(float(d[bad][i]) * 1000, 1), tuple(np.round(c[i], 3))) for i in w])
