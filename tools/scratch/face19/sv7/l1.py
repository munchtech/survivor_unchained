"""l1.py LOGDIR CLIP STEP F0 F1: the long hair drawn offline (sv6 drape replica, C#'s 20 deg card cap) at frames F0..F1: the extra lift of
its vertices off her body or the floor over no card turn (cm, of those over 2 cm off), and the chain's change from C# (cm)."""
import sys; sys.path[:0] = ["../sv6", "../sv5", "../sv4", "../sv3"]
from hs6 import *
from vlift import gaps
from skin import Hair
from turn import turns, angle
from capq import capq
dirn, clip, step, f0, f1 = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
fr = lg(dirn, clip + "_long"); xs, m = sim6(fr, "long", **per4(H7, "long")); H = Hair("long"); cs = today(fr)
for j in range(f0, f1 + 1):
    d = fr[j]; x = xs[j]; q, _ = turns(d["target"], x); qc = capq(q)
    P0, _ = H.drawn(d, x, None); P1, _ = H.drawn(d, x, qc)
    g0 = gaps(d, P0) * 100; g1 = gaps(d, P1) * 100; ex = g1 - g0; mk = g1 > 2
    print("f%d c%.2f w %.2f turn %3.0f capped extra lift %.1f cm (n>2cm %d); gap max %.1f; chain vs C# %.2f cm" % (
        j, j / step, m.wlog[j], max(angle(a) for a in q), ex[mk].max() if mk.any() else 0, (ex[mk] > 2).sum() if mk.any() else 0, g1.max(),
        np.linalg.norm(x - cs[j], axis=1).max() * 100 if m.wlog[j] <= 0 or m.wlog[j] >= 1 - 1e-4 else -1))
