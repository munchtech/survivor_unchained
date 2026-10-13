"""ev5.py CFG...: solver 5's numbers: getupback c4 shape (f15-17: tip angle off down, sag cm), throw braid worst joint f15-21, and each must-stay clip's worst change (cm) from H7."""
from hs5 import *
def shape(x):
    r, t = x[0], x[7]; u = nz(t - r); ang = math.degrees(math.acos(np.clip(u @ [0, -1, 0], -1, 1)))
    sag = max(np.linalg.norm((x[i] - r) - ((x[i] - r) @ u) * u) for i in range(1, 7)) * 100
    return ang, sag
KEEP = [(c, s) for s in ("ponytail", "braid", "long") for c in ("run", "stop")] + [("throw", "ponytail"), ("throw", "long")] + \
       [("getup", s) for s in ("ponytail", "braid", "long")] + [("getupback", "ponytail"), ("death", "braid"), ("death", "ponytail")]
def run(name, o):
    out = []
    for st in ("braid", "long"):
        fr = lg("hair12", "getupback_" + st); xs = sim5(fr, st, **per4(o, st))
        out.append("gub %s c4 " % st[:2] + " ".join("%.0f/%.0f" % shape(xs[j]) for j in (15, 16, 17)))
    fr = lg("hair12", "throw_braid"); xs = sim5(fr, "braid", **per4(o, "braid"))
    out.append("throw braid joint f15-21 %.0f" % max(angles(xs[j]).max() for j in range(15, 21)))
    ch = []
    for cl, st in KEEP:
        fr = lg("hair12", cl + "_" + st); a = sim5(fr, st, **per4(H7, st)); b = sim5(fr, st, **per4(o, st))
        ch.append("%s/%s %.1f" % (cl[:5], st[:2], max(np.linalg.norm(p - q, axis=1).max() for p, q in zip(a, b)) * 100))
    print("== %s: %s\n   keep: %s" % (name, " | ".join(out), " ".join(ch)))
if __name__ == "__main__":
    for n in sys.argv[1:]: run(n, eval(n, globals(), dict(H7=H7, F15=dict(H7, facc=1.5), F2=dict(H7, facc=2.0), K35=dict(H7, kink=35), K30=dict(H7, kink=30))))
