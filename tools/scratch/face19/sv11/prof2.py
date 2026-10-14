"""prof2.py: her right shoulder line at rest: per across bin (cm from her midline), the top of her body, of each outfit,
and of the chain's balls (ball3 = spine_03 top, stretched 6 cm across; shoulder ball r 8 at upperarm_r), in a slice
around z (front-back) of ZC +- 3 cm. Heights in cm above the neck centre (1.599)."""
from pads import load, bones, verts
import numpy as np, sys, math
ZC = float(sys.argv[1]) if len(sys.argv) > 1 else -0.03
gb, ab = load("heroine.glb"); B = bones(gb, ab); J = B["upperarm_r"][:3, 3]
body = np.vstack([V for n, V in verts(gb, ab, ("hair", "lash", "brow", "eye", "teeth", "tongue", "head"))])
outs = {o: np.vstack([V for n, V in verts(*load("heroine_outfit_%s.gltf" % o))]) for o in ("warden", "arcanist")}
NY = 1.599
def top(V, x0, x1):
    s = (-V[:, 0] >= x0) & (-V[:, 0] < x1) & (np.abs(V[:, 2] - ZC) < 0.03) & (V[:, 1] > 1.35) & (V[:, 1] < 1.75)
    return (V[s, 1].max() - NY) * 100 if s.any() else float("nan")
def balls(x):
    best = -1e9
    for at, r, w in (((0, 1.524, -0.027), 0.099, 0.06), ((0, 1.474, -0.010), 0.1188, 0.06), (tuple(J), 0.08, 0), ((0, 1.574, -0.0434), 0.0636, 0), ((0, 1.624, -0.0467), 0.0457, 0)):
        cx = max(-w, min(w, -x)) if w else at[0]; dx = -x - cx if w else -x - at[0]; dz = ZC - at[2]
        h = r * r - dx * dx - dz * dz
        if h > 0: best = max(best, at[1] + math.sqrt(h))
    return (best - NY) * 100
print("ZC %.3f  joint x %.1f y %.1f (above neck centre) z %.1f" % (ZC, -J[0] * 100, (J[1] - NY) * 100, J[2] * 100))
print("across  body  warden  arcanist  balls")
for x in range(2, 30, 2):
    x0 = x / 100
    print("%5d  %5.1f  %5.1f  %5.1f  %5.1f" % (x, top(body, x0, x0 + 0.02), top(outs["warden"], x0, x0 + 0.02), top(outs["arcanist"], x0, x0 + 0.02), balls(x0 + 0.01)))
