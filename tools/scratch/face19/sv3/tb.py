"""tb.py STYLE CFG f0 f1 [clip]: chain in her back's frame (cm): lat (her right +), out (off her back +), along (toward hips +)."""
import sys
from cfg3 import *
st = sys.argv[1]; o = per(eval(sys.argv[2]), st); f0, f1 = int(sys.argv[3]), int(sys.argv[4]); clip = sys.argv[5] if len(sys.argv) > 5 else "death"
src = sys.argv[6] if len(sys.argv) > 6 else None
fr = lg("hair9", clip + "_" + st)
m = Model(fr, st, **o)
t = today(lg(src, clip + "_" + st)) if src else None
for j, d in enumerate(fr):
    x = m.frame(d).copy() if not src else t[j]
    if f0 <= j <= f1:
        b = 5; out = nz(d["back"][b]); lat = nz(d["across"][b]); along = nz(np.cross(out, lat))
        # along should point toward her hips: down her spine at rest (-y). check sign with spine_01 ball
        if (d["at"][10] - d["at"][3]) @ along < 0: along = -along
        def bf(p): q = p - x[0]; return (q @ lat * 100, q @ out * 100, q @ along * 100)
        tg = d["target"]
        print("f%2d c%4.1f up(body along) %+.2f |" % (j, j / 3, along[1]), " ".join("(%+4.0f %+4.0f %+4.0f)" % bf(x[i]) for i in range(1, 8)), "| tgt7 (%+4.0f %+4.0f %+4.0f)" % bf(tg[7]))
