"""l2.py LOGDIR FRAMES...: death long: where the vertices lifted >2 cm by the capped card turn are (height over floor, over/under her
back ball's top, chain place, card offset), grouped by chain segment, and the turn at each point."""
import sys; sys.path[:0] = ["../sv6", "../sv5", "../sv4", "../sv3"]
from hs6 import *
from vlift import gaps
from skin import Hair
from turn import turns, angle
from capq import capq
fr = lg(sys.argv[1], "death_long"); xs, m = sim6(fr, "long", **per4(H7, "long")); H = Hair("long")
for j in map(int, sys.argv[2:]):
    d = fr[j]; x = xs[j]; q, _ = turns(d["target"], x); qc = capq(q)
    P0, _ = H.drawn(d, x, None); P1, _ = H.drawn(d, x, qc); g0 = gaps(d, P0) * 100; g1 = gaps(d, P1) * 100
    k = (g1 > 2) & (g1 - g0 > 2)
    bk = d["at"][3:8]; topY = (bk[:, 1] + 0).max(); g = d["ground"]
    print("f%d c%.2f turns %s; chain y %s; back ball top y %.2f; head y %.2f" % (j, j / 3, " ".join("%.0f" % angle(a) for a in q),
          " ".join("%.2f" % (p[1] - g) for p in x), topY - g + d["r"][3:8].max(), d["head"][0][1] - g))
    s = np.clip(H.UV2[:, 0], 0, 1) * 7
    for seg in range(7):
        kk = k & (np.floor(s).astype(int).clip(0, 6) == seg)
        if not kk.any(): continue
        P = P1[kk]; print("  seg %d: n %d, y %.2f..%.2f, lift %.1f..%.1f cm, gap %.1f..%.1f, x %.2f..%.2f z %.2f..%.2f" % (seg, kk.sum(), P[:, 1].min() - g, P[:, 1].max() - g,
            (g1 - g0)[kk].min(), (g1 - g0)[kk].max(), g1[kk].min(), g1[kk].max(), P[:, 0].min(), P[:, 0].max(), P[:, 2].min(), P[:, 2].max()))
