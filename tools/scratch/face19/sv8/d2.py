"""d2.py CLIP STYLE F0 F1 [opts]: M8 per frame: w, flags, side, and each point in her body frame (cm: across,up,back)."""
from ev8 import *
cl, st, f0, f1 = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
o = eval(sys.argv[5]) if len(sys.argv) > 5 else {}
fr = lg("hair15", cl + "_" + st)
m = M8(fr, st, **per4(dict(H7, **o), st))
for j, d in enumerate(fr):
    out = m.frame(d).copy()
    if j < f0 or j > f1: continue
    o0, B = body(d)
    pts = " ".join("%3.0f,%3.0f,%3.0f" % tuple(B @ (out[i] - o0) * 100) for i in range(1, 8))
    print("f%2d c%5.2f w%.2f s%+d r%s | %s" % (j, j / STEP[cl], m.w, m.side, "".join("1" if r else "." for r in m.rnd[1:]), pts))
