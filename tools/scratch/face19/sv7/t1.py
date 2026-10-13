"""t1.py: long hair in run/stop/throw (hair14 dumps): frames whose card turn passes the 20 deg cap, and how far the cap moves its vertices (cm)."""
import sys; sys.path[:0] = ["../sv5", "../sv4", "../sv3"]
from vlift import *
from capq import capq
from turn import angle
H = Hair("long")
for cl in ("run", "stop", "throw"):
    fr = lg("hair14", cl + "_long"); x = today(fr)
    for j in range(len(fr)):
        d = fr[j]; q, _ = turns(d["target"], x[j]); a = max(angle(qq) for qq in q)
        if a <= 20: continue
        P0, _ = H.drawn(d, x[j], q); P1, _ = H.drawn(d, x[j], capq(q))
        print("%s f%d turn max %.1f deg, cap moves verts max %.2f cm" % (cl, j, a, np.linalg.norm(P0 - P1, axis=1).max() * 100))
