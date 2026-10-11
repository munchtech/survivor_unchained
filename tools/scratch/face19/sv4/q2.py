"""q2.py: per clip/style, the range of each point's rest direction from the root against straight down (dot)."""
import sys; sys.path.insert(0, "../sv3")
from cfg3 import *
for st in ("braid", "ponytail", "long"):
    for cl in ("run", "stop", "throw", "getup", "getupback", "death"):
        fr = lg("hair9", cl + "_" + st)
        D = np.array([[nz(d["target"][i] - d["target"][0]) @ [0, -1, 0] for i in range(1, 8)] for d in fr])
        u = smooth(0.35, 0.85, D)
        print("%-9s %-9s dot min %.2f p5 %.2f | u<1 in %d/%d frames (min u %.2f)" % (st, cl, D.min(), np.percentile(D, 5), (u.min(1) < 0.999).sum(), len(fr), u.min()))
