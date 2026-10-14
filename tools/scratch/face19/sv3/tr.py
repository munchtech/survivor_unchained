"""tr.py STYLE CFG f0 f1: per-frame trace of hold, link elevation, angle from rest."""
import sys
from cfg3 import *
st = sys.argv[1]; o = per(eval(sys.argv[2]), st); f0, f1 = int(sys.argv[3]), int(sys.argv[4]); clip = sys.argv[5] if len(sys.argv) > 5 else "death"
fr = lg("hair9", clip + "_" + st)
m = Model(fr, st, **o)
for j, d in enumerate(fr):
    x = m.frame(d).copy()
    if f0 <= j <= f1:
        tg = d["target"]
        el = [math.degrees(math.asin(np.clip(nz(x[i] - x[i - 1])[1], -1, 1))) for i in range(1, 8)]
        tel = [math.degrees(math.asin(np.clip(nz(tg[i] - tg[i - 1])[1], -1, 1))) for i in range(1, 8)]
        fromrest = [math.degrees(math.acos(np.clip(nz(x[i] - x[i - 1]) @ nz(tg[i] - tg[i - 1]), -1, 1))) for i in range(1, 8)]
        rv = (d["target"][0] - fr[j - 1]["target"][0]) / d["dt"] if j else np.zeros(3)
        print("f%2d c%4.1f hold %s | el %s | tel %s | fromrest %s | rootv %+.2f,%+.2f" % (j, j / 3, " ".join("%.2f" % (m.hold[i] / m.stiff) for i in range(1, 8)),
              " ".join("%+4.0f" % e for e in el), " ".join("%+4.0f" % e for e in tel), " ".join("%3.0f" % e for e in fromrest), rv[1], -rv[2]))
