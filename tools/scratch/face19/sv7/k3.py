"""k3.py: try: held points' rest targets pushed fully out of the balls (pushheld). Throw braid worst joint f15-21; every other clip's
worst chain change (cm) from today's model (sv6)."""
import sys; sys.path[:0] = ["../sv6", "../sv5", "../sv4", "../sv3"]
import hs6, hs7
from hs6 import *
def run6(fr, st, o):
    hs6.M5 = hs7.M5 if o.get("pushheld") else hs6.__dict__["M5"]
    return sim6(fr, st, **per4(dict(H7, **o), st))[0]
import hs5; base5 = hs5.M5
for cl in ("throw", "run", "stop", "death", "getup", "getupback"):
    for st in ("braid", "ponytail", "long"):
        fr = lg("hair14", cl + "_" + st)
        hs6.M5 = base5; a = sim6(fr, st, **per4(H7, st))[0]
        hs6.M5 = hs7.M5; b = sim6(fr, st, **per4(dict(H7, pushheld=1), st))[0]
        ch = max(np.linalg.norm(p - q, axis=1).max() for p, q in zip(a, b)) * 100
        k = " joint f15-21 %.0f -> %.0f" % (max(angles(a[j]).max() for j in range(15, 21)), max(angles(b[j]).max() for j in range(15, 21))) if cl == "throw" else ""
        print("%s %s change %.1f cm%s" % (cl, st, ch, k))
