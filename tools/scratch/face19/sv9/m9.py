"""m9.py SET: C# (dump) vs the M9 replica (braid fold 45) on throw braid, worst cm over the clip."""
from hs9 import *
fr = lg(sys.argv[1], "throw_braid"); xs, _ = sim9(fr, "braid", **per4(dict(H7, taper=False, kink=45), "braid")); cs = today(fr)
print("C# vs M9 throw braid: worst %.3f cm" % max(np.linalg.norm(p - q, axis=1).max() * 100 for p, q in list(zip(xs, cs))[:-1]))
A = [angles(x)[1] for x in cs]; T = [np.abs(turns2(x)[0][:3]).max() for x in cs]
print("C# p2 angle c5-c10:", " ".join("%.0f" % A[2 * c] for c in range(5, 11)), "| seen worst turn p1-3:", " ".join("%.0f" % T[2 * c] for c in range(5, 11)))
