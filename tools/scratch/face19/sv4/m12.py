"""m12.py: hair12 (C#) numbers: death long lift c8, death braid/ponytail rod c3-5, worst joint and cap deviation, run/stop/throw against hair11."""
import sys
from hs4 import *
from ev import capdev
from lift import lifts
fr = lg("hair12", "death_long"); x = today(fr)
print("death long lift c8 %.1f cm, c7-11 %.1f" % (max(lifts(fr[j], x[j])[2:].max() for j in (23, 24, 25)) * 100, max(lifts(fr[j], x[j])[2:].max() for j in range(21, 34)) * 100))
for st in ("braid", "ponytail", "long"):
    fr = lg("hair12", "death_" + st); x = today(fr)
    rod = max(lifts(fr[j], x[j])[2:].max() for j in range(9, 16)) * 100
    cd = [capdev(fr[j]["target"], x[j]).max() for j in range(len(x) - 1)]
    print("death %-8s rod c3-5 %4.1f joint max %3.0f cap dev max %3.0f@c%.1f up c11-14 %+5.1f" % (st, rod, max(angles(x[j]).max() for j in range(len(x) - 1)), max(cd), np.argmax(cd) / 3,
          max(max(x[j][k][1] - x[j][0][1] for k in range(1, 8)) for j in range(33, len(x) - 1)) * 100))
for st in ("braid", "ponytail", "long"):
    for cl in ("run", "stop", "throw", "getup", "getupback"):
        a = today(lg("hair11", cl + "_" + st)); b = today(lg("hair12", cl + "_" + st)); n = min(len(a), len(b)) - 1
        print("%-9s %-8s vs hair11 %.1f cm" % (cl, st, max(np.linalg.norm(a[j] - b[j], axis=1).max() for j in range(n)) * 100))
