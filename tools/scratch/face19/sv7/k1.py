"""k1.py: throw braid kink: per frame f12-24 the joint angles, holds, and which balls each rest target is inside (depth cm)."""
import sys; sys.path[:0] = ["../sv6", "../sv5", "../sv4", "../sv3"]
from hs6 import *
fr = lg("hair14", "throw_braid")
m = M6(fr, "braid", **per4(H7, "braid"))
for j, d in enumerate(fr):
    x = m.frame(d).copy()
    if j < 12 or j > 24: continue
    tg = d["target"]; ins = []
    for i in range(1, 8):
        for b in range(len(d["r"])):
            w = d["across"][b]; ww = w @ w; at = d["at"][b]
            c = at + w * np.clip((tg[i] - at) @ w / ww, -1, 1) if ww > 0 else at
            dep = d["r"][b] * 1.04 - np.linalg.norm(tg[i] - c)
            if dep > 0: ins.append("p%d:b%d %.1f" % (i, b, dep * 100))
    print("f%d c%.1f ang %s hold %s | %s" % (j, j / 2, " ".join("%.0f" % a for a in angles(x)), " ".join("%.2f" % h for h in m.hold[1:]), " ".join(ins)))
