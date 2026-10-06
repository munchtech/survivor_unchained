import sys

import numpy as np

sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abfa9bb430ec2391e\tools\assets")
import face_fit as ff

an = dict(np.load(sys.argv[1]))
views = []
for p in sys.argv[2:]:
    path, part = (p.split("@") + ["whole"])[:2]
    img, _ = ff.load(path, part)
    views.append(ff.detect(img))
P0, hit = an["P0"], an["hit"]
imp = ff.importance(len(P0)) * hit
R0 = np.array([[1.0, 0, 0], [0, 0, 1], [0, -1, 0]])
for Q in views:
    q = ff.to_3d(Q)
    n = min(len(q), len(P0))
    s, R, t = ff.umeyama(P0[:n], q[:n], imp[:n] + 1e-9)
    print("scale", s, "\nR", np.round(R, 3), "\nR@R0.T", np.round(R @ R0.T, 3))
    e = np.linalg.norm(((s * (R @ P0[:n].T).T + t) - q[:n]), axis=1) / s * 1000
    print("err mm 3d", (e * imp[:n]).sum() / imp[:n].sum())
    # z spread versus x spread
    print("x range", np.ptp(q[:, 0]), "z range", np.ptp(q[:, 2]), "model x", np.ptp(P0[:, 0]) * s, "model y", np.ptp(P0[:, 1]) * s)
