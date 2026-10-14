"""e4.py K [N]: freeze her at frame K (same pose every frame) from the chain as C# had it, and let the model run N frames:
is the fold where it settles (a rest of the model) or only on its way?"""
from g9 import *
fr = lg("hair17d", "throw_braid"); st = "braid"
K = int(sys.argv[1]); N = int(sys.argv[2]) if len(sys.argv) > 2 else 60
m = M8(fr, st, **per4(H7, st))
for k in range(K): m.frame(fr[k])
d = fr[K]
for j in range(N):
    x = m.frame(d).copy()
    if j in (0, 1, 2, 4, 8, 15, 30, 59):
        a = angles(x)
        print("t+%2d ang %3.0f %3.0f %3.0f %3.0f  p1 %s p2 %s p3 %s p7 %s" % (j, a[0], a[1], a[2], a[3], np.round(F(d, x[1]), 1), np.round(F(d, x[2]), 1), np.round(F(d, x[3]), 1), np.round(F(d, x[7]), 1)))
