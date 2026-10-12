"""h19.py OPTS1 [OPTS2..]: the hair19 get_up ponytail capture (another run of the clip, no meshes): carry flags per frame
k26.., when the carry ends, the largest move k26-end (Godot-like, neck frame), HEAD first."""
import sys; sys.path[:0] = ["../sv14"]
from ev14 import *
runs = [("HEAD", {})] + [("O%d" % i, eval(a)) for i, a in enumerate(sys.argv[1:])]
fr = lg("hair19", "getup_ponytail"); out = []
for n, o in runs:
    xs, m = run12(fr, "ponytail", **o); g = gx(xs, m); best, mv = gmove(fr, g, 26, len(fr) - 1)
    end = max((k for k in range(len(m.rlog)) if m.rlog[k].any()), default=-2) + 1
    out.append((n, m, mv, end, best))
    print("%s ends k%d move %.1f k%d p%d (of %d frames)" % (n, end, best[0], best[1], best[2], len(fr)))
for k in range(26, len(fr)):
    print("k%d " % k + " | ".join("%s %4.1f" % ("".join("1" if q else "." for q in m.rlog[k][3:]), mv.get(k, 0)) for n, m, mv, end, best in out))
