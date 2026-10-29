# Body 2 A: the turn of the arm's longitudinal edges about the bone (deg per cm, by band along the forearm / upper arm)
#   python turn.py <dump.npz>[|P.npy]
import sys, numpy as np
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
from lib import load, edges, armframe


def turn(d, P, s, seg="f", bands=None, own=None):
    F = armframe(d, s, P); g = F[seg]; E = edges(d["ls"], d["lt"], d["lv"])
    m = F["side"][E].all(1) & (g["r"][E] < (0.06 if seg == "f" else 0.07)).all(1)
    if own is not None: m &= own[E].all(1)
    E = E[m]; dv = P[E[:, 1]] - P[E[:, 0]]; ln = np.linalg.norm(dv, axis=1); ca = (dv @ g["n"]) / ln
    E = E[np.abs(ca) > 0.85]
    t0, t1 = g["t"][E[:, 0]], g["t"][E[:, 1]]; p0, p1 = g["phi"][E[:, 0]], g["phi"][E[:, 1]]
    dz = (t1 - t0) * g["L"] * 100; dp = (p1 - p0 + 180) % 360 - 180
    rate = dp / dz; tm = (t0 + t1) / 2
    bands = bands or [(0.0, 0.2), (0.2, 0.4), (0.4, 0.6), (0.6, 0.8), (0.8, 0.9), (0.9, 1.0)]
    return [(a, b, float(np.median(rate[(tm >= a) & (tm < b)])) if ((tm >= a) & (tm < b)).sum() > 5 else np.nan) for a, b in bands]


if __name__ == "__main__":
    for a in sys.argv[1:]:
        p = a.split("|"); d = load(p[0]); P = np.load(p[1]) if len(p) > 1 else d["P"]
        for s in "rl":
            for seg in "uf":
                r = turn(d, P, s, seg)
                L = armframe(d, s, P)[seg]["L"] * 100
                tot = sum(x * (b - a_) * L for a_, b, x in r if x == x)
                print(p[-1][-30:], s, seg, " ".join(f"{a_:.1f}-{b:.1f}:{x:+.2f}" for a_, b, x in r), f"total {tot:+.1f} deg")
