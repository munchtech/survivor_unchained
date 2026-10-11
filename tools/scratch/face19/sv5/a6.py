"""a6.py: hair12 C#: per clip, max angle at each joint (p1..p6) for the braid, and capdev per joint."""
import sys; sys.path[:0] = ["../sv4", "../sv3"]
from hs4 import *
from ev import capdev
for st in sys.argv[1:] or ["braid"]:
    for cl in ("run", "stop", "throw", "getup", "getupback", "death"):
        fr = lg("hair12", cl + "_" + st); x = today(fr); n = len(x) - 1
        A = np.array([angles(x[j]) for j in range(n)]); C = np.array([capdev(fr[j]["target"], x[j]) for j in range(n)])
        print("%-6s %-9s joint" % (st, cl), " ".join("%3.0f" % v for v in A.max(0)), "| capdev", " ".join("%3.0f" % v for v in C.max(0)))
