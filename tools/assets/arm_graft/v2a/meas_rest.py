# Body 2 A: arm sections at rest on blend dumps, perpendicular to the bone (elbow: the bisector plane).
#   python meas_rest.py <dump.npz>[:P.npy] ...      girth (convex hull, mm), width across (top), depth (front), per side
import sys, numpy as np
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
from lib import load, fan, armframe, section, girth

ST = ["u.15", "u.30", "u.46", "u.60", "elb", "f.15", "f.25", "f.50", "f.75", "f.90", "f.95"]


def sections(d, P, T, s):
    F = armframe(d, s, P); side = F["side"]; keep = side.copy(); out = {}
    for k in ST:
        if k == "elb":
            u, f = F["u"], F["f"]; n = u["n"] + f["n"]; n /= np.linalg.norm(n); o = f["o"]
            top = u["top"] + f["top"]; top -= (top @ n) * n; top /= np.linalg.norm(top); fr = np.cross(n, top)
            if fr @ np.array([0, -1, 0]) < 0: fr = -fr
        else:
            g = F[k[0]]; t = float(k[1:]); o = g["o"] + g["n"] * g["L"] * t; n, top, fr = g["n"], g["top"], g["fr"]
        q = section(P, T, o, n, top, fr, rmax=0.07 if k[0] != "f" else 0.055, keep=keep)
        if q is None: out[k] = None; continue
        # (the piece round the axis only: drop the torso where the plane still cuts it near the pit)
        out[k] = dict(g=girth(q) * 1e3, w=(q[:, 0].max() - q[:, 0].min()) * 1e3, dp=(q[:, 1].max() - q[:, 1].min()) * 1e3)
    return out


if __name__ == "__main__":
    for a in sys.argv[1:]:
        p = a.split("|"); d = load(p[0]); P = np.load(p[1]) if len(p) > 1 else d["P"]
        T, _, _ = fan(d["ls"], d["lt"], d["lv"])
        for s in "rl":
            o = sections(d, P, T, s)
            print(p[-1][-40:], s, " ".join(f"{k}:{v['g']:.0f}/{v['w']:.0f}x{v['dp']:.0f}" if v else f"{k}:-" for k, v in o.items()))
