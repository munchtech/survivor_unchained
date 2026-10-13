"""a4.py SET [SET...]: throw braid as seen from behind, per cell: turn at points 1-5 (deg) and seen link lengths (cm)."""
from g9 import *
for SET in sys.argv[1:]:
    fr = lg(SET, "throw_braid"); cs = today(fr)
    print(SET)
    for k in range(0, len(fr) - 1, 2):
        t, L = turns2(cs[k])
        print("  c%-2d turn %s | seen %s" % (k // 2, " ".join("%+4.0f" % v for v in t[:5]), " ".join("%4.1f" % v for v in L[:5])))
