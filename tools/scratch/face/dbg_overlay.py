import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abfa9bb430ec2391e\tools\assets")
import face_fit as ff

an = dict(np.load(sys.argv[1]))
part = sys.argv[3] if len(sys.argv) > 3 else "whole"
img, x0 = ff.load(sys.argv[2], part)
Q = ff.detect(img)
P0, hit = an["P0"], an["hit"]
P0 = P0 - P0[hit].mean(0)
imp = ff.importance(len(P0)) * hit
q = ff.to_3d(Q)
n = min(len(q), len(P0))
s, R, t = ff.pose(P0[:n], q[:n], imp[:n] + 1e-9)
X = s * (R @ P0[:n].T).T + t
im = Image.fromarray(img).convert("RGB")
d = ImageDraw.Draw(im)
for k in range(n):
    if not hit[k]:
        continue
    a, b = Q[k, :2], (X[k, 0], -X[k, 1])
    d.line([tuple(a), tuple(b)], fill=(255, 255, 0))
    d.ellipse([a[0] - 2, a[1] - 2, a[0] + 2, a[1] + 2], fill=(0, 255, 0))
    d.ellipse([b[0] - 2, b[1] - 2, b[0] + 2, b[1] + 2], fill=(255, 0, 0))
im.save(sys.argv[4] if len(sys.argv) > 4 else "overlay.png")
