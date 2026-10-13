"""vlift.py: how far her drawn hair's vertices stand off her body and the floor (cm): per frame p99, max, and count over 3 cm."""
import sys; sys.path[:0] = ["../sv4", "../sv3"]
from hs4 import *
from skin import Hair
from turn import turns
def gaps(d, P, sc=1.04):
    g = np.full(len(P), 1e9)
    for b in range(len(d["r"])):
        w = d["across"][b]; ww = w @ w; at = d["at"][b]
        t = np.clip((P - at) @ w / ww, -1, 1) if ww > 0 else np.zeros(len(P))
        c = at + t[:, None] * w
        g = np.minimum(g, np.linalg.norm(P - c, axis=1) - d["r"][b] * sc)
    return np.minimum(g, P[:, 1] - d["ground"])
def report(style, clip, frames, h="hair12", xs=None, variants=None, step=3):
    H = Hair(style); fr = lg(h, clip + "_" + style); x = today(fr) if xs is None else xs
    for j in frames:
        d = fr[j]; q, _ = turns(d["target"], x[j]); row = []
        for name, fn in variants.items():
            P, _ = H.drawn(d, x[j], *fn(d, x[j], q))
            g = gaps(d, P) * 100
            row.append("%s p99 %4.1f max %4.1f n>3 %5d" % (name, np.percentile(g, 99), g.max(), (g > 3).sum()))
        print("f%2d c%4.1f  " % (j, j / step) + " | ".join(row))
if __name__ == "__main__":
    V = {"none": lambda d, x, q: (None,), "turn": lambda d, x, q: (q,)}
    report("long", "death", range(24, 40), variants=V)
