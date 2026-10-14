"""tb10n.py OPTS EXTRA [SET]: tb10 with extra neck balls (addball)."""
from hs10 import *
import addball
o = eval(sys.argv[1]); extra = eval(sys.argv[2]); SET = sys.argv[3] if len(sys.argv) > 3 else "hair17d"; quiet = len(sys.argv) > 4
fr = addball.add(lg(SET, "throw_braid"), extra)
W = []; out = []
xs, m = sim10(fr, "braid", **o)
for k in range(6, len(fr) - 1):
    x = xs[k]; d = fr[k]
    t, L = turns2(x); j = int(np.argmax(np.abs(t[:5]))); a = angles(x)
    P = np.array([F(d, x[i]) for i in range(8)])
    W.append(abs(t[j]))
    out.append("  k%2d c%4.1f seen %4.0f@p%d  3d %3.0f  right %5.1f  minback %5.1f | %s" % (k, k / 2, t[j], j + 1, a.max(), -P[1:, 0].min(), P[2:, 2].min(), " ".join("p%d(%+5.1f,%+5.1f,%+5.1f)" % ((i,) + tuple(P[i])) for i in (1, 2, 3))))
print("%s %s: worst seen turn c3+ %.0f, frames >60: %d of %d" % (o, extra, max(W), sum(w > 60 for w in W), len(W)))
if not quiet: print("\n".join(out))
