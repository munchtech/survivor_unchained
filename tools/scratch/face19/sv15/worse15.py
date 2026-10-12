"""worse15.py OPTS: frames k28-60 where any segment (1-7) of OPTS is more than 0.5 cm deeper than HEAD's same segment, per
outfit; and the worst segs 1-3 of each."""
from ev15 import *
o = eval(sys.argv[1]); h = full("ponytail", {}); r = full("ponytail", o)
for md in ("mw", "mr"):
    bad = []
    for k in range(28, 61):
        for s in range(7):
            a, b = h["res"][md][k][s], r["res"][md][k][s]
            if b < a - 0.5 and b < 0: bad.append("k%d s%d %.1f (was %.1f)" % (k, s + 1, b, a))
    print(md, "segs1-3 HEAD %.1f NEW %.1f" % (min(min(h["res"][md][k][:3]) for k in range(28, 61)), min(min(r["res"][md][k][:3]) for k in range(28, 61))),
          "| deeper:", "; ".join(bad) if bad else "none")
