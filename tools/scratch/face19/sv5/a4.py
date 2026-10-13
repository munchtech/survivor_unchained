"""a4.py: hair12 C# per clip/style: worst joint angle and worst deviation from the carried rest bend (capdev), and their frames."""
import sys; sys.path[:0] = ["../sv4", "../sv3"]
from hs4 import *
from ev import capdev
for st in ("braid", "ponytail", "long"):
    for cl in ("run", "stop", "throw", "getup", "getupback", "death"):
        fr = lg("hair12", cl + "_" + st); x = today(fr); n = len(x) - 1
        ja = [angles(x[j]).max() for j in range(n)]; cd = [capdev(fr[j]["target"], x[j]).max() for j in range(n)]
        print("%-6s %-9s joint %3.0f@f%-3d capdev %3.0f@f%-3d frames %d" % (st, cl, max(ja), int(np.argmax(ja)), max(cd), int(np.argmax(cd)), n))
