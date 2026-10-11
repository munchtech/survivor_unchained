"""tb4.py STYLE CFG f0 f1 [clip]: chain in her back's frame (cm): (lat, out, along) per point, its lift and hold/stiff."""
import sys
from hs4 import *
sys.path.insert(0, "../sv3")
from lift import lifts
st = sys.argv[1]; o = per4(eval(sys.argv[2]), st); f0, f1 = int(sys.argv[3]), int(sys.argv[4]); clip = sys.argv[5] if len(sys.argv) > 5 else "death"
fr = lg("hair9", clip + "_" + st); m = M4(fr, st, **o)
for j, d in enumerate(fr):
    x = m.frame(d).copy()
    if f0 <= j <= f1:
        b = 5; out = nz(d["back"][b]); lat = nz(d["across"][b]); along = nz(np.cross(out, lat))
        if (d["at"][10] - d["at"][3]) @ along < 0: along = -along
        def bf(p): q = p - x[0]; return (q @ lat * 100, q @ out * 100, q @ along * 100)
        print("f%2d c%4.1f" % (j, j / 3), " ".join("(%+3.0f %+3.0f %+3.0f)" % bf(x[i]) for i in range(1, 8)), "| tgt7 (%+3.0f %+3.0f %+3.0f)" % bf(d["target"][7]),
              "| lift %s | hold %s" % (" ".join("%2.0f" % v for v in lifts(d, x)[1:] * 100), " ".join("%.1f" % (m.hold[i] / m.stiff) for i in range(1, 8))))
