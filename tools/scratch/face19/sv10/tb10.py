"""tb10.py OPTS [SET]: throw braid under hs10(OPTS): per frame from k6 (c3) the worst seen-from-behind turn at p1-p5 (deg,
and where), the worst 3D joint angle, how far right any point is (cm, b3's frame) and the least 'back' of p2-p7 (cm), and
the tip's offset from its rest (across, up, back). Then the C# at HEAD (orig) the same, for comparison."""
from hs10 import *
o = eval(sys.argv[1]); SET = sys.argv[2] if len(sys.argv) > 2 else "hair17d"; quiet = len(sys.argv) > 3
fr = lg(SET, "throw_braid")
def rows(xs, tag):
    W = []; out = []
    for k in range(6, len(fr) - 1):
        x = xs[k]; d = fr[k]
        t, L = turns2(x); j = int(np.argmax(np.abs(t[:5]))); a = angles(x)
        P = np.array([F(d, x[i]) for i in range(8)]); tip = P[7] - F(d, d["target"][7])
        W.append(abs(t[j]))
        out.append("  k%2d c%4.1f seen %4.0f@p%d  3d %3.0f  right %5.1f  minback %5.1f  tip(%+5.1f,%+5.1f,%+5.1f)" % (k, k / 2, t[j], j + 1, a.max(), -P[1:, 0].min(), P[2:, 2].min(), *tip))
    print("%s: worst seen turn c3+ %.0f, cells >60: %d of %d frames" % (tag, max(W), sum(w > 60 for w in W), len(W)))
    if not quiet: print("\n".join(out))
xs, m = sim10(fr, "braid", **o); rows(xs, "NEW " + str(o))
xs0, _ = sim10(fr, "braid", orig=1); rows(xs0, "HEAD")
