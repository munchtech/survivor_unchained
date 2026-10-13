"""ev8.py [opts]: per clip vs the C# model (M6): worst change (cm, and from which cell), and for get_up the in-front check."""
from hs8 import *
STEP = dict(death=3, getup=4, getupback=4, throw=2, run=2, stop=2)
CLIPS = [(c, s) for c in ("run", "stop", "throw", "death", "getup", "getupback") for s in ("ponytail", "braid", "long")]
def body(d):
    at = d["at"]; o = (at[1] + at[2]) / 2; up = nz(at[1] - at[10]); bk = d["back"][1]; bk = nz(bk - (bk @ up) * up); ac = np.cross(up, bk)
    return o, np.array([ac, up, bk])
def run(o, clips=CLIPS, SET="hair15"):
    for cl, st in clips:
        fr = lg(SET, cl + "_" + st)
        xs, m = sim8(fr, st, **per4(dict(H7, **o), st))
        base, _ = sim6(fr, st, **per4(H7, st))
        dif = [np.linalg.norm(p - q, axis=1).max() * 100 for p, q in zip(xs, base)]
        j = int(np.argmax(dif)); first = next((k for k, v in enumerate(dif) if v > 1), -1)
        # relative motion per frame in her body frame (cm), worst, frames >= 1
        rel = 0; relj = 0
        for k in range(1, len(fr)):
            o0, B0 = body(fr[k - 1]); o1, B1 = body(fr[k])
            mv = max(np.linalg.norm(B1 @ (xs[k][i] - o1) - B0 @ (xs[k - 1][i] - o0)) for i in range(1, 8)) * 100
            if mv > rel: rel, relj = mv, k
        print("%-9s %-8s chg %5.1f (c%.2f, >1cm from c%s) relmove max %4.1f at c%.2f" % (cl, st, dif[j], j / STEP[cl], "%.2f" % (first / STEP[cl]) if first >= 0 else "-", rel, relj / STEP[cl]))
if __name__ == "__main__":
    o = eval(sys.argv[1]) if len(sys.argv) > 1 else {}
    clips = CLIPS if len(sys.argv) < 3 else [tuple(c.split("_")) for c in sys.argv[2].split(",")]
    run(o, clips)
