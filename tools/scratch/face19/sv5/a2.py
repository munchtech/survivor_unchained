"""a2.py: throw braid hair9 vs hair11: per-frame worst point distance (cm), hold/free, joint angles per joint at f14-21."""
import sys; sys.path[:0] = ["../sv4", "../sv3"]
from hs4 import *
a = lg("hair9", "throw_braid"); b = lg("hair11", "throw_braid")
xa, xb = today(a), today(b)
print("dist", " ".join("%d:%.1f" % (j, np.linalg.norm(xa[j] - xb[j], axis=1).max() * 100) for j in range(len(xa))))
for j in range(12, 22):
    print(j, "h9", " ".join("%3.0f" % v for v in angles(xa[j])), "| h11", " ".join("%3.0f" % v for v in angles(xb[j])))
# replicate with the model: today's (C5 = solver 4) on hair9 inputs vs hair9's x
m = sim4(a, "braid", **per4(H7, "braid"))
print("model H7 on hair9 inputs vs h11 C#:", " ".join("%.1f" % (np.linalg.norm(m[j] - xb[j], axis=1).max() * 100) for j in range(len(xb))))
