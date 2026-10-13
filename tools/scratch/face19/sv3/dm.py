"""Death metrics for a run of chains."""
from hs3 import *
import math
def dmet(fr, xs, lo=12, hi=None):
    hi = hi or len(xs)
    coil = 0; close = 1; ang = 0; up_end = -1; spd = 0; past = -1
    for i in range(lo, hi):
        x = xs[i]; a = angles(x); ang = max(ang, a.max())
        coil = max(coil, max(a[j:j + 4].sum() for j in range(3)))
        for p in range(8):
            for q in range(p + 3, 8): close = min(close, np.linalg.norm(x[p] - x[q]))
        hd = fr[i]["head"]
        past = max(past, max((x[j] - hd[0]) @ hd[2] for j in range(2, 8)) - (x[0] - hd[0]) @ hd[2])
        if i >= hi - 8:
            up_end = max(up_end, max(x[j][1] - x[0][1] for j in range(1, 8)))
            if i > lo:
                rel = (x - xs[i - 1]) - (fr[i]["target"][0] - fr[i - 1]["target"][0])
                spd = max(spd, np.linalg.norm(rel, axis=1).max() / fr[i]["dt"])
    return dict(ang=ang, coil=coil, close=close, past=past, up_end=up_end, spd_end=spd)
def show(name, d):
    return "%-14s ang %3.0f coil %3.0f close %.3f past %+.2f up_end %+.2f spd_end %.2f" % (name, d["ang"], d["coil"], d["close"], d["past"], d["up_end"], d["spd_end"])
