"""geo13.py STYLE OPTS [K0 K1] [MD]: per frame, carried flags, capsule on, HAIRCLEAR all 7 segments, and the chain in her
neck frame (a right, h up, b behind; cm)."""
from ev13 import *
st = sys.argv[1]; o = eval(sys.argv[2]); K0, K1 = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (40, 52)
md = sys.argv[5] if len(sys.argv) > 5 else "mw"
fr, xs, m, res = evalc(st, o, K0, K1)
for k in range(K0, K1 + 1):
    d = fr[k]; n, R = neckf(d); P = (xs[k] - n) @ R * 100; P[:, 0] *= -1  # (a: to her right)
    print("k%d %s c%d w%.2f | %s | %s" % (k, "".join("1" if r else "." for r in m.rlog[k]), m.caplog[k], m.wlog[k],
          " ".join("%5.1f" % v for v in res[md][k]), " ".join("(%.0f,%.0f,%.0f)" % tuple(P[i]) for i in range(1, 8))))
