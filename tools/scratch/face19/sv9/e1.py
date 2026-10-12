"""e1.py: is the fold an attractor? Run M8 on throw braid; at frame K put the chain at its targets (pushed out of her, still)
and carry on; print the joint angles and p2-p3 in b3's frame after."""
from g9 import *
fr = lg("hair17d", "throw_braid"); st = "braid"
for K in (6, 10, 14):
    m = M8(fr, st, **per4(H7, st)); out = []
    for k, d in enumerate(fr):
        if k == K:
            for i in range(1, 8):
                q = m.collide(d, d["target"][i].copy(), None, 1.04); m.x[i] = q; m.xp[i] = q.copy()
        out.append(m.frame(d).copy())
    print("reset at k%d" % K)
    for k in range(K, len(fr)):
        a = angles(out[k]); d = fr[k]
        print("  k%2d ang %s  p1 %s p2 %s p3 %s" % (k, " ".join("%3.0f" % v for v in a), np.round(F(d, out[k][1]), 1), np.round(F(d, out[k][2]), 1), np.round(F(d, out[k][3]), 1)))
