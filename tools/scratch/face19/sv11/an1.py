"""an1.py LOG STYLE [K0 K1]: the C# replica (hs10, HEAD) on an every-frame dump: per photographed frame k (dump k+3), the
down weight, carried points, and each point's place against her right shoulder ball (b13) and upper-arm ball (b14):
in the neck frame (cm: across +her near side, up, back) and how deep inside b13/b14 (cm, + inside; r*1.04)."""
import sys; sys.path[:0] = ["../sv10", "../sv9", "../sv8", "../sv6", "../sv5", "../sv4", "../sv3"]
from h11 import *
LOG, st = sys.argv[1], sys.argv[2]; K0, K1 = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (0, 60)
fr = lg("hc", LOG); xs, m = run(fr, st); cs = today(fr)
def dep(d, p, b, sc=1.04): return (d["r"][b] * sc - np.linalg.norm(p - d["at"][b])) * 100
for k in range(K0, min(K1, len(fr) - 4) + 1):
    i = k + 3; d = fr[i]; x = xs[i]
    at = d["at"]; neck = (at[1] + at[2]) / 2; up = nz(neck - at[10]); bk = d["back"][1]; bk = nz(bk - (bk @ up) * up); ac = np.cross(up, bk)
    sh = at[13]; S = lambda p: ((p - neck) @ ac * 100, (p - neck) @ up * 100, (p - neck) @ bk * 100)
    e = np.linalg.norm(x - cs[i], axis=1).max() * 100
    print("k%d w=%.2f rnd=%s replica-C#x %.1f | shR %s shL %s" % (k, m.wlog[i], "".join("1" if r else "." for r in m.rlog[i]), e,
          "%.0f,%.0f,%.0f" % S(sh), "%.0f,%.0f,%.0f" % S(at[11])))
    print("   " + " ".join("p%d(%.0f,%.0f,%.0f|%.1f,%.1f)" % ((j,) + S(x[j]) + (dep(d, x[j], 13), dep(d, x[j], 14))) for j in range(2, 8)))
