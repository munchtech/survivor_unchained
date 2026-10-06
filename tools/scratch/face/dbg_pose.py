import sys

import numpy as np

sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abfa9bb430ec2391e\tools\assets")
import face_fit as ff

an = dict(np.load(sys.argv[1]))
img, _ = ff.load(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "whole")
Q = ff.detect(img)
P0, hit = an["P0"], an["hit"]
P0 = P0 - P0[hit].mean(0)
imp = ff.importance(len(P0)) * hit
if "core" in sys.argv:
    core = np.zeros(len(P0))
    core[ff.EYES + ff.NOSE + ff.LIPS + ff.BROWS] = 1
    imp = imp * core
q = ff.to_3d(Q)
n = min(len(q), len(P0))
R0 = np.array([[1.0, 0, 0], [0, 0, 1], [0, -1, 0]])


def yawR(deg):
    a = np.radians(deg)
    # turn about the image's up (y)
    return np.array([[np.cos(a), 0, np.sin(a)], [0, 1, 0], [-np.sin(a), 0, np.cos(a)]]) @ R0


for y0 in (None, -40, -20, 0, 20, 40):
    s, R, t = ff.pose(P0[:n], q[:n], imp[:n] + 1e-9, None if y0 is None else yawR(y0))
    e = np.linalg.norm(((s * (R @ P0[:n].T).T + t) - q[:n])[:, :2], axis=1) / s * 1000
    Rr = R @ R0.T
    print(y0, "-> yaw %.1f pitch %.1f roll %.1f" % (np.degrees(np.arctan2(Rr[0, 2], Rr[2, 2])), np.degrees(np.arcsin(-Rr[1, 2])),
                                                     np.degrees(np.arctan2(Rr[1, 0], Rr[1, 1]))),
          "s %.0f err %.2f mm" % (s, (e * imp[:n]).sum() / imp[:n].sum()))
