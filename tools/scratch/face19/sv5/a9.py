"""a9.py: hair12 C#: per clip/style, max point turn angle (deg) per point 1..7, and the cell where the max is."""
import sys; sys.path[:0] = ["../sv4", "../sv3"]
from hs4 import *
from turn import *
STEP = dict(run=2, stop=2, throw=2, getup=4, getupback=4, death=3)
for st in ("braid", "ponytail", "long"):
    for cl in ("run", "stop", "throw", "getup", "getupback", "death"):
        fr = lg("hair12", cl + "_" + st); x = today(fr); n = len(x) - 1
        A = np.array([[angle(q) for q in turns(fr[j]["target"], x[j])[0]] for j in range(n)])
        j = int(A.max(1).argmax())
        print("%-8s %-9s max turn" % (st, cl), " ".join("%3.0f" % v for v in A[:, 1:].max(0)), " worst f%d c%.1f" % (j, j / STEP[cl]))
