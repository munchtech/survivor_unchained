"""ev6.py: per clip: w per cell, pops at the blend (|dw|*|drape-swing|, cm), change from C# (cm), and shapes."""
from hs6 import *
STEP = dict(death=3, getup=4, getupback=4, throw=2, run=2, stop=2)
CLIPS = [(c, s) for c in ("run", "stop", "throw", "death", "getup", "getupback") for s in ("ponytail", "braid", "long")]
def shape(x):
    r, t = x[0], x[7]; u = nz(t - r); ang = math.degrees(math.acos(np.clip(u @ [0, -1, 0], -1, 1)))
    sag = max(np.linalg.norm((x[i] - r) - ((x[i] - r) @ u) * u) for i in range(1, 7)) * 100
    return ang, sag
def run(o, clips=CLIPS, verbose=False):
    for cl, st in clips:
        fr = lg("hair13", cl + "_" + st)
        xs, m = sim6(fr, st, **per4(dict(H7, **o), st))
        base = sim5(fr, st, **per4(H7, st))
        ch = max(np.linalg.norm(p - q, axis=1).max() for p, q in zip(xs, base)) * 100
        w = np.array(m.wlog) if m.wlog else np.zeros(len(fr))
        pop = 0
        for j in range(1, len(fr)):
            if len(m.swing) > j: pop = max(pop, abs(w[j] - w[j - 1]) * np.linalg.norm(m.drape[j - 1] - m.swing[j - 1], axis=1).max() * 100)
        ws = " ".join("%.1f" % w[j] for j in range(0, len(fr), STEP[cl])) if len(w) else ""
        print("%-9s %-8s chg %5.1f pop %4.1f w %s" % (cl, st, ch, pop, ws))
        if verbose and cl in ("getupback",):
            print("   shape c3-c6 (ang/sag): " + " ".join("c%.1f %.0f/%.0f" % (j / 4, *shape(xs[j])) for j in range(12, 26, 2)))
if __name__ == "__main__":
    run(eval(sys.argv[1]) if len(sys.argv) > 1 else {}, verbose=True)
