"""c15.py A B: the chain C# ran (HAIRDUMP x) in sheet set A vs B, per clip: worst difference (cm)."""
import sys; sys.path[:0] = ["../sv5", "../sv4", "../sv3"]
from hs5 import *
for cl in ("run", "stop", "throw", "death", "getup", "getupback"):
    row = []
    for st in ("ponytail", "braid", "long"):
        a, b = lg(sys.argv[1], cl + "_" + st), lg(sys.argv[2], cl + "_" + st); n = min(len(a), len(b))
        row.append("%s %.2f" % (st, max(np.linalg.norm(a[j]["x"] - b[j]["x"], axis=1).max() for j in range(n)) * 100))
    print(cl, " ".join(row))
