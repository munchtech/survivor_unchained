"""a8.py STYLE CLIP f0 f1 [log]: per point turn angle (deg), contact (b ball, f floor) and free, from the C# chain."""
import sys; sys.path[:0] = ["../sv4", "../sv3"]
from hs4 import *
from turn import *
st, clip, f0, f1 = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]); h = sys.argv[5] if len(sys.argv) > 5 else "hair12"
class M(M4):
    def collide(s, d, p, i=None, sc=1.0):
        if i is not None:
            for b in range(len(d["r"])):
                w = d["across"][b]; ww = w @ w; at = d["at"][b]
                c = at + w * np.clip((p - at) @ w / ww, -1, 1) if ww > 0 else at
                if np.linalg.norm(p - c) < d["r"][b] * sc: s.hit[i] = b
        return M4.collide(s, d, p, i, sc)
fr = lg(h, clip + "_" + st); m = M(fr, st, **per4(H7, st))
for j, d in enumerate(fr):
    m.hit = [None] * 8; m.gr = m.grounded.copy()
    x = m.frame(d).copy()
    if f0 <= j <= f1:
        q, seg = turns(d["target"], x)
        print("f%2d c%4.1f" % (j, j / 3), " ".join("%3.0f%s" % (angle(q[i]), ("f" if m.grounded[i] else "-" if m.hit[i] is None else "b%d" % m.hit[i]).ljust(3)) for i in range(1, 8)),
              "| ang", " ".join("%3.0f" % v for v in angles(x)), "| free", " ".join("%.1f" % (1 - m.hold[i] / m.stiff) for i in range(1, 8)))
