"""k4.py DEG: try: the held braid's joint cap (DEG) only where the point's rest target is inside a ball (kin). As k3."""
import sys; sys.path[:0] = ["../sv6", "../sv5", "../sv4", "../sv3"]
import hs6, hs7, hs5
from hs6 import *
base5 = hs5.M5; deg = float(sys.argv[1])
for cl in ("throw", "run", "stop", "death", "getup", "getupback"):
    st = "braid"
    fr = lg("hair14", cl + "_" + st)
    hs6.M5 = base5; a = sim6(fr, st, **per4(H7, st))[0]
    hs6.M5 = hs7.M5; b = sim6(fr, st, **per4(dict(H7, kink=deg, kin=1), st))[0]
    ch = max(np.linalg.norm(p - q, axis=1).max() for p, q in zip(a, b)) * 100
    k = " joint f15-21 %.0f -> %.0f" % (max(angles(a[j]).max() for j in range(15, 21)), max(angles(b[j]).max() for j in range(15, 21))) if cl == "throw" else ""
    print("%s %s change %.1f cm%s" % (cl, st, ch, k))
