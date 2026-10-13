"""e5.py [opts]: throw braid: M8 vs M9 (opts), per cell: 3D angles at points 1-3, seen turns at 1-3, C# match of M9 off."""
from hs9 import *
o = eval(sys.argv[1]) if len(sys.argv) > 1 else {}
fr = lg(sys.argv[2] if len(sys.argv) > 2 else "hair17d", "throw_braid"); st = "braid"
a8, _ = sim8(fr, st, **per4(H7, st)); a9, _ = sim9(fr, st, **per4(dict(H7, **o), st)); z9, _ = sim9(fr, st, **per4(dict(H7, taper=False), st))
print("M9 taper off vs M8: %.4f cm" % max(np.abs(p - q).max() * 100 for p, q in zip(a8, z9)))
for name, xs in (("M8", a8), ("M9", a9)):
    A = np.array([angles(x) for x in xs]); T = np.array([turns2(x)[0] for x in xs])
    print(name, "3D p1-3 :", " ".join("%3.0f/%3.0f/%3.0f" % tuple(A[k, :3]) for k in range(0, 22, 2)))
    print(name, "seen p1-3:", " ".join("%+4.0f/%+4.0f/%+4.0f" % tuple(T[k, :3]) for k in range(0, 22, 2)))
print("chg per cell (cm):", " ".join("%.1f" % (np.linalg.norm(p - q, axis=1).max() * 100) for p, q in list(zip(a8, a9))[::2]))
