"""q3.py STYLE CFG f0 f1: which ball each point last touched each frame (b:n.back), and the surface's receding speed (m/s)."""
import sys; sys.path.insert(0, "../sv3")
from cfg3 import *
class M(Model):
    def collide(s, d, p, i=None, sc=1.0):
        q = Model.collide(s, d, p, i, sc)
        if i is not None:
            for b in range(len(d["r"])):
                w = d["across"][b]; ww = w @ w; at = d["at"][b]
                c = at + w * np.clip((p - at) @ w / ww, -1, 1) if ww > 0 else at
                if np.linalg.norm(p - c) < d["r"][b] * sc: s.hit[i] = (b, bool(d["behind"][b]) and (p - c) @ d["back"][b] < 0)
        return q
st = sys.argv[1]; o = per(eval(sys.argv[2]), st); f0, f1 = int(sys.argv[3]), int(sys.argv[4])
fr = lg("hair9", "death_" + st); m = M(fr, st, **o)
for j, d in enumerate(fr):
    m.hit = [None] * 8
    x = m.frame(d).copy()
    if f0 <= j <= f1:
        print("f%2d" % j, " ".join("%s%s" % ("-" if h is None else h[0], "M" if h and h[1] else " ") for h in m.hit[1:]),
              "| y", " ".join("%4.0f" % ((x[k][1] - d["ground"]) * 100) for k in range(8)))
