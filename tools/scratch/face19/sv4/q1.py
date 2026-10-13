"""q1.py STYLE CFG...: per death frame: max joint angle, highest point over the root (cm), lift off her back (cm)."""
import sys; sys.path.insert(0, "../sv3")
from cfg3 import *
from lift import lifts
st = sys.argv[1]; clip = "death"
fr = lg("hair9", clip + "_" + st)
for n in sys.argv[2:]:
    xs = sim(fr, st, **per(eval(n), st))
    print(n)
    for j in range(len(fr)):
        x = xs[j]; a = angles(x); up = max(x[k][1] - x[0][1] for k in range(1, 8)) * 100
        L = lifts(fr[j], x)[2:].max() * 100
        print("f%2d c%4.1f ang %s | up %+5.1f lift %4.1f" % (j, j / 3, " ".join("%3.0f" % v for v in a), up, L))
