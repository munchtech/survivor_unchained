"""ev12.py OPTS [K0 K1] [v]: get_up ponytail/braid, the replica at HEAD vs with OPTS: offline HAIRCLEAR (segments 4-7, worst
per frame, cm) against the warden (mw) and the reaver (mr) posed meshes, frames K0-K1; v: all 7 segments per frame."""
from hs12 import *
if __name__ == "__main__": o = eval(sys.argv[1]); K0, K1 = (int(sys.argv[2]), int(sys.argv[3])) if len(sys.argv) > 3 else (40, 52); V = "v" in sys.argv[4:]
else: K0, K1 = 40, 52
DUMP = dict(ponytail="hc/s11_ponytail_review", braid="hc/s11_braid_review")
def evals(st, oo):
    fr = lg(*DUMP[st].split("/")); xs, m = run12(fr, st, **oo); res = {}
    for md in ("mw", "mr"):
        res[md] = {k: clear(xs[k], "s12/" + md, k) for k in range(K0, K1 + 1)}
    return xs, m, res
if __name__ == "__main__":
    for st in ("ponytail", "braid"):
        for name, oo in (("HEAD", {}), ("NEW", o)):
            if name == "NEW" and not o: continue
            xs, m, res = evals(st, oo)
            for md in ("mw", "mr"):
                w = [min(res[md][k][3:]) for k in range(K0, K1 + 1)]
                print("%-8s %-4s %s worst %.1f |" % (st, name, md, min(w)), " ".join("%d:%.1f" % (k, v) for k, v in zip(range(K0, K1 + 1), w)))
                if V:
                    for k in range(K0, K1 + 1): print("    k%d %s %s" % (k, "".join("1" if r else "." for r in m.rlog[k]), " ".join("%.1f" % v for v in res[md][k])))
