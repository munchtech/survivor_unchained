"""Every layer of her skin along one ray of the review's frame (400 px): its
depth, whether it faces the camera (drawn) or not (culled), whether it is
turned over, its points' blend toward the calf and where they lay at rest.

    python tickray.py <variant> <deg> <x> <y> [view]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import math  # noqa: E402
import numpy as np  # noqa: E402
import tick  # noqa: E402
from sweep import pose, knee  # noqa: E402

v, deg, px, py = sys.argv[1], int(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4])
view = sys.argv[5] if len(sys.argv) > 5 else "side"
b = tick.variant_body(v)
G = pose(b, [knee("l", deg), knee("r", deg)])
I = b.sk.index
j = I["calf_l"]
target = G[j][:3, 3]
P = b.pose(G)
E, f, r, u = tick.camera(target, view, 4.5)
t = math.tan(math.radians(16))
dx = (px - 200) / 200 * t
dy = -(py - 200) / 200 * t
ray = f + dx * r + dy * u
ray /= np.linalg.norm(ray)
near = np.linalg.norm(P - target, axis=1) < 0.17
T = b.T[near[b.T].all(1)]
# Moller-Trumbore against every face
v0, v1, v2 = P[T[:, 0]], P[T[:, 1]], P[T[:, 2]]
e1, e2 = v1 - v0, v2 - v0
pv = np.cross(ray, e2)
det = np.einsum("ij,ij->i", e1, pv)
ok = np.abs(det) > 1e-14
inv = np.where(ok, 1 / np.where(ok, det, 1), 0)
tv = E - v0
uu = np.einsum("ij,ij->i", tv, pv) * inv
qv = np.cross(tv, e1)
vv = (qv @ ray) * inv
tt = np.einsum("ij,ij->i", e2, qv) * inv
hit = ok & (uu >= 0) & (vv >= 0) & (uu + vv <= 1) & (tt > 0)
Sm = b.skin_mats(G)
Nn = np.zeros_like(b.N)
for k in range(4):
    Nn += b.W[:, k:k + 1] * np.einsum("nij,nj->ni", Sm[b.J[:, k], :3, :3], b.N)
w = np.zeros((len(b.P), 3))
for k in range(4):
    for col, n in enumerate(("thigh_l", "calf_l", "calf_share_l")):
        if n in I:
            w[:, col] += np.where(b.J[:, k] == I[n], b.W[:, k], 0)
xb = (w[:, 1] + w[:, 2] / 2) / np.maximum(w.sum(1), 1e-9)
rk = b.rest[j][:3, 3]
print(f"{v} knee {deg} ray ({px},{py}) {view}: {hit.sum()} layers")
for k in np.argsort(tt[hit]):
    fi = np.nonzero(hit)[0][k]
    gn = np.cross(e1[fi], e2[fi])
    facing = gn @ (-ray) > 0
    turned = gn @ Nn[T[fi]].sum(0) < 0
    c = T[fi]
    rp = (b.P[c].mean(0) - rk) * 100
    print(f"  depth {tt[fi]*100:6.2f} cm  {'drawn ' if facing else 'culled'} {'TURNED' if turned else '      '} blend {xb[c].mean():.2f}"
          f"  rest x {rp[0]:+5.1f} y {rp[1]:+5.1f} z {rp[2]:+5.1f} cm  face {fi}")
