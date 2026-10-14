"""gap.py STYLE CFG f0 f1 [clip] [src]: each point's gap to her body (cm, + off it) and height over the floor (cm)."""
import sys
from cfg3 import *
def gaps(d, x, sc=1.04):
    g = []
    for p in x:
        best = 1e9
        for b in range(len(d["r"])):
            w = d["across"][b]; ww = w @ w; at = d["at"][b]
            c = at + w * np.clip((p - at) @ w / ww, -1, 1) if ww > 0 else at
            best = min(best, np.linalg.norm(p - c) - d["r"][b] * sc)
        g.append(best)
    return np.array(g)
if __name__ == "__main__":
    st = sys.argv[1]; o = per(eval(sys.argv[2]), st); f0, f1 = int(sys.argv[3]), int(sys.argv[4]); clip = sys.argv[5] if len(sys.argv) > 5 else "death"
    src = sys.argv[6] if len(sys.argv) > 6 else None
    fr = lg("hair9", clip + "_" + st); m = Model(fr, st, **o)
    t = today(lg(src, clip + "_" + st)) if src else None
    for j, d in enumerate(fr):
        x = m.frame(d).copy() if not src else t[j]
        if f0 <= j <= f1:
            g = gaps(d, x) * 100; fl = (x[:, 1] - d["ground"]) * 100
            print("f%2d c%4.1f gap %s | floor %s" % (j, j / 3, " ".join("%4.0f" % v for v in g[1:]), " ".join("%4.0f" % v for v in fl[1:])))
