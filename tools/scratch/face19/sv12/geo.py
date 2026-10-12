"""geo.py STYLE LOG [K0 K1]: the replica at HEAD on a dump; per frame k, each chain point in her neck frame (a: to her
right, h: up her spine, b: behind; cm from the neck balls' middle), carried flags, and the right shoulder ball's centre."""
from h12 import *
st, log = sys.argv[1], sys.argv[2]; K0, K1 = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (40, 52)
fr = lg(*log.split("/")); xs, m = run12(fr, st)
for k in range(K0, K1 + 1):
    d = fr[k]; at = d["at"]; neck = (at[1] + at[2]) / 2; up = nz(neck - at[10]); bk = d["back"][1]; bk = nz(bk - (bk @ up) * up); ac = np.cross(up, bk)
    P = lambda p: np.array([(p - neck) @ ac, (p - neck) @ up, (p - neck) @ bk]) * 100
    x = xs[k]
    print("k%d w%.2f rnd %s sh %s" % (k, m.wlog[k], "".join("1" if r else "." for r in m.rlog[k]), np.round(P(at[13]), 1)),
          " ".join("p%d(%.0f,%.0f,%.0f)" % ((i,) + tuple(P(x[i]))) for i in range(1, 8)))
