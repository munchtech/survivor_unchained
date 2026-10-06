import sys

import numpy as np

sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abfa9bb430ec2391e\tools\assets")
import face_fit as ff

an = dict(np.load(sys.argv[1]))
img, _ = ff.load(sys.argv[2], "whole")
Q = ff.detect(img)
P0, hit = an["P0"], an["hit"]
P0 = P0 - P0[hit].mean(0)
imp = ff.importance(len(P0)) * hit
q = ff.to_3d(Q)
R0 = np.array([[1.0, 0, 0], [0, 0, 1], [0, -1, 0]])
W = imp / imp.sum()
groups = {"oval": ff.OVAL, "lips": ff.LIPS, "eyes": ff.EYES, "brows": ff.BROWS, "nose": ff.NOSE}
for deg in range(-40, 41, 8):
    a = np.radians(deg)
    Ry = np.array([[np.cos(a), 0, np.sin(a)], [0, 1, 0], [-np.sin(a), 0, np.cos(a)]])
    R = Ry @ R0
    X = (R @ P0.T).T
    mx, mq = (W[:, None] * X[:, :2]).sum(0), (W[:, None] * q[:, :2]).sum(0)
    A, B = X[:, :2] - mx, q[:, :2] - mq
    s = (W * (A * B).sum(1)).sum() / (W * (A * A).sum(1)).sum()
    e = np.linalg.norm(s * A - B, axis=1) / s * 1000
    print(deg, "err %.2f" % ((e * imp).sum() / imp.sum()), " ".join("%s %.1f" % (g, e[ix].mean()) for g, ix in groups.items()))
