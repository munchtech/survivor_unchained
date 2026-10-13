"""e6.py: throw braid, taper settings: worst seen turn (deg) at points 1-3 per cell c3-c10."""
from hs9 import *
fr = lg("hair17d", "throw_braid"); st = "braid"
for o in eval(sys.argv[1]):
    xs, _ = sim9(fr, st, **per4(dict(H7, **o), st))
    T = np.array([np.abs(turns2(x)[0][:3]).max() for x in xs]); A = np.array([angles(x)[:3].max() for x in xs])
    print("%-32s seen %s | 3D %s" % (o, " ".join("%3.0f" % T[2 * c] for c in range(3, 11)), " ".join("%3.0f" % A[2 * c] for c in range(3, 11))))
