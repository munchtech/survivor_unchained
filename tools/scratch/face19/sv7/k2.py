"""k2.py: throw braid at F: each point's x - target (cm), the balls x touches (gap cm), link directions."""
import sys; sys.path[:0] = ["../sv6", "../sv5", "../sv4", "../sv3"]
from hs6 import *
fr = lg("hair14", "throw_braid"); xs = sim5(fr, "braid", **per4(H7, "braid"))
d0 = fr[0]; print("balls:", " ".join("b%d r%.3f bh%d w%.2f" % (b, d0["r"][b], d0["behind"][b], np.linalg.norm(d0["across"][b])) for b in range(len(d0["r"]))))
for j in map(int, sys.argv[1:]):
    d = fr[j]; x = xs[j]; tg = d["target"]
    print("f%d angles %s" % (j, " ".join("%.0f" % a for a in angles(x))))
    for i in range(8):
        tch = []
        for b in range(len(d["r"])):
            w = d["across"][b]; ww = w @ w; at = d["at"][b]
            c = at + w * np.clip((x[i] - at) @ w / ww, -1, 1) if ww > 0 else at
            gp = np.linalg.norm(x[i] - c) - d["r"][b] * 1.04
            if gp < 0.01: tch.append("b%d %.1f" % (b, gp * 100))
        dl = (x[i] - tg[i]) * 100
        ln = nz(x[i] - x[i - 1]) if i else np.zeros(3)
        print("  p%d off %5.1f %5.1f %5.1f | dir %5.2f %5.2f %5.2f | %s" % (i, *dl, *ln, " ".join(tch)))
