"""ev11.py OPTS: get_up ponytail/braid (hc every-frame dumps): HEAD vs OPTS per 5 photographed frames (dump index = k)."""
from hs11 import *
o = eval(sys.argv[1])
for st in ("ponytail", "braid"):
    fr = lg("hc", "g0_%s_review" % st)
    for name, oo in (("HEAD", {}), ("NEW", o)):
        xs, m = run(fr, st, **oo); M = metrics(fr, xs, m)
        print(st, name, "k: stretch/neck/shoulder rnd w")
        print("  " + " | ".join("k%d %.1f/%.1f/%.1f %s %.2f" % ((k,) + M[k]) for k in range(24, 61, 4)))
        print("  worst k27-60: stretch %.1f neck %.1f shoulder %.1f" % tuple(max(M[k][j] for k in range(27, 61)) for j in range(3)))
