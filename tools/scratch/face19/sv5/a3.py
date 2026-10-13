"""a3.py STYLE CLIP f0 f1 [log]: per frame, per point: hold/stiff, ball touched (b; '*' target inside a ball), joint angle; root speed and accel."""
import sys; sys.path[:0] = ["../sv4", "../sv3"]
from hs4 import *
st, clip, f0, f1 = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]); h = sys.argv[5] if len(sys.argv) > 5 else "hair12"
class M(M4):
    def collide(s, d, p, i=None, sc=1.0):
        if i is not None:
            for b in range(len(d["r"])):
                w = d["across"][b]; ww = w @ w; at = d["at"][b]
                c = at + w * np.clip((p - at) @ w / ww, -1, 1) if ww > 0 else at
                if np.linalg.norm(p - c) < d["r"][b] * sc: s.hit[i] = b
        return M4.collide(s, d, p, i, sc)
fr = lg(h, clip + "_" + st); m = M(fr, st, **per4(H7, st)); pv = None; ppv = None
def inside(d, p, sc=1.04):
    for b in range(len(d["r"])):
        w = d["across"][b]; ww = w @ w; at = d["at"][b]
        c = at + w * np.clip((p - at) @ w / ww, -1, 1) if ww > 0 else at
        if np.linalg.norm(p - c) < d["r"][b] * sc: return b
    return None
for j, d in enumerate(fr):
    m.hit = [None] * 8
    x = m.frame(d).copy()
    r = d["target"][0]; v = (r - pv) / d["dt"] if pv is not None else np.zeros(3); a = (v - ppv) / d["dt"] if ppv is not None else np.zeros(3)
    ppv = v; pv = r.copy()
    if f0 <= j <= f1:
        tin = [inside(d, d["target"][i]) for i in range(1, 8)]
        print("f%2d" % j, " ".join("%.1f%s%s" % (m.hold[i] / m.stiff, "-" if m.hit[i] is None else str(m.hit[i]), "*" if tin[i - 1] is not None else " ") for i in range(1, 8)),
              "| ang", " ".join("%3.0f" % a_ for a_ in angles(x)), "| root v %.1f a %.0f m/s2" % (np.linalg.norm(v), np.linalg.norm(a)))
