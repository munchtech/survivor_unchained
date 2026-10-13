"""a1.py: throw braid in hair9/11/12: inputs the same? joint angles per frame (C# x)."""
import sys; sys.path[:0] = ["../sv4", "../sv3"]
from hs4 import *
for st in ("braid",):
    F = {h: lg(h, "throw_" + st) for h in ("hair9", "hair11", "hair12")}
    n = min(len(f) for f in F.values())
    print("frames", {h: len(f) for h, f in F.items()})
    print("target diff 9-11 %.4f  11-12 %.4f" % (max(np.abs(F["hair9"][j]["target"] - F["hair11"][j]["target"]).max() for j in range(n)),
          max(np.abs(F["hair11"][j]["target"] - F["hair12"][j]["target"]).max() for j in range(n))))
    for h in F:
        x = today(F[h])
        print(h, " ".join("%d:%3.0f" % (j, angles(x[j]).max()) for j in range(12, n)))
