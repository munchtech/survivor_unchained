"""chk.py: hs4's M4 with C2 against hs3's G2 (must match), on a few clips."""
from hs4 import *
for st, cl in (("braid", "death"), ("long", "throw"), ("ponytail", "run")):
    fr = lg("hair9", cl + "_" + st)
    a = sim(fr, st, **per(G2, st)); b = sim4(fr, st, **per4(C2, st))
    c = sim(fr, st, **per(G3, st)); e = sim4(fr, st, **per4(C3, st))
    print(st, cl, "G2-C2 %.2e  G3-C3 %.2e" % (max(np.abs(p - q).max() for p, q in zip(a, b)), max(np.abs(p - q).max() for p, q in zip(c, e))))
