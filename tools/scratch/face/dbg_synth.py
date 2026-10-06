import sys

import numpy as np

sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abfa9bb430ec2391e\tools\assets")
import face_fit as ff

an = dict(np.load(sys.argv[1]))
P0, hit = an["P0"], an["hit"]
P0 = P0 - P0[hit].mean(0)
imp = ff.importance(len(P0)) * hit
R0 = np.array([[1.0, 0, 0], [0, 0, 1], [0, -1, 0]])
for deg in (0, 15, 32, -32):
    a = np.radians(deg)
    Ry = np.array([[np.cos(a), 0, np.sin(a)], [0, 1, 0], [-np.sin(a), 0, np.cos(a)]])
    Rt = Ry @ R0
    q = 3400 * (Rt @ P0.T).T + [500, -500, 0]
    q[:, 2] *= 0.7                                   # (MediaPipe's depth on another scale)
    for init in (None, "R0"):
        s, R, t = ff.pose(P0, q, imp + 1e-9, None if init is None else R0)
        Rr = R @ R0.T
        print(deg, init, "-> yaw %.1f" % np.degrees(np.arctan2(Rr[0, 2], Rr[2, 2])), "s %.0f" % s)
