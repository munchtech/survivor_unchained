"""env14.py MD K0 K1: her right shoulder's upper envelope in spine_03's rest space (cm; x out to her right, z to her front,
y above 1.50 m), the highest over frames K0..K1 of the posed body (mesh 0) / of everything (outfit)."""
import sys; sys.path[:0] = ["../sv12"]
from h12 import *
md, K0, K1 = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
fr = lg("hc", "s11_braid_review")
A3 = np.array([0, 1.5240698, -0.0268065])
def rest_of(d):
    ex = nz(d["across"][3]); ez = -nz(d["back"][3]); ey = np.cross(ez, ex); R = np.c_[ex, ey, ez]; a3 = d["at"][3]
    return lambda p: (p - a3) @ R / 1.04 + A3
XS = list(range(4, 25, 2)); ZS = list(range(-16, 15, 2))
top = np.full((len(XS), len(ZS)), -99.0); topa = top.copy()
for k in range(K0, K1 + 1):
    d = fr[k]; f = rest_of(d); v, _ = mesh(md, k); P = f(v[:, :3]); body = v[:, 6] == 0; head = v[:, 6] == 1
    for i, x in enumerate(XS):
        for j, z in enumerate(ZS):
            s = (np.abs(-P[:, 0] * 100 - x) < 1) & (np.abs(P[:, 2] * 100 - z) < 1) & ~head & (P[:, 1] > 1.30)
            if (s & body).any(): top[i, j] = max(top[i, j], (P[s & body, 1].max() - 1.50) * 100)
            if s.any(): topa[i, j] = max(topa[i, j], (P[s, 1].max() - 1.50) * 100)
print("x-z " + " ".join("%5d" % z for z in ZS))
for i, x in enumerate(XS):
    print("%3d " % x + " ".join(("%5.1f" % top[i, j]) if top[i, j] > -90 else "    ." for j in range(len(ZS))))
if "outfit" in sys.argv:
    print("outfit/all:")
    for i, x in enumerate(XS):
        print("%3d " % x + " ".join(("%5.1f" % topa[i, j]) if topa[i, j] > -90 else "    ." for j in range(len(ZS))))
