"""How far the Reaver's band (the convex hull of her chest's section, as bandeau() lays it)
stands off her skin round her chest, row by row, at rest.   python tunnel.py <heroine.glb>"""
import sys

import numpy as np
from scipy.spatial import ConvexHull

from glbread import Body

b = Body(sys.argv[1])
V = b.V
names = b.jnames
armj = [i for i, n in enumerate(names) if n.split('_')[0] in ('upperarm', 'lowerarm', 'hand', 'index', 'middle', 'ring', 'pinky', 'thumb')]
armw = np.where(np.isin(b.J, armj), b.W, 0).sum(1)
body = armw < 0.25
nz = (1.422 + 1.425) / 2          # the build's nipples (Godot y)
pig = 1.415                       # the areolas' centres from her paint
zc, width, rows = nz - 0.01, 0.07, 11
zs = np.linspace(zc - width / 2, zc + width / 2, rows)
nu = 120
a = np.linspace(0, 2 * np.pi, nu, endpoint=False)
d = np.stack([np.sin(a), np.cos(a)], 1)        # (x, z): a=0 her front (+z), a=pi/2 her left (+x)
cxy = None
print('rows from %.3f to %.3f; areola centres at %.3f' % (zs[0], zs[-1], pig))
EXACT = len(sys.argv) > 2


def section(z):
    tri = b.T[body[b.T].all(1)]
    out = []
    for i, j in ((0, 1), (1, 2), (2, 0)):
        p, q = V[tri[:, i]], V[tri[:, j]]
        s = (p[:, 1] - z) * (q[:, 1] - z) < 0
        t = (z - p[s, 1]) / (q[s, 1] - p[s, 1])
        out.append(p[s][:, [0, 2]] + t[:, None] * (q[s][:, [0, 2]] - p[s][:, [0, 2]]))
    return np.vstack(out)


for k, z in enumerate(zs):
    m = body & (np.abs(V[:, 1] - z) < 0.01)
    q = section(z) if EXACT else V[m][:, [0, 2]]
    if cxy is None:
        cxy = q.mean(0)
    h = ConvexHull(q)
    hv = q[h.vertices]
    R = np.zeros(nu)
    for i in range(len(hv)):
        p0, p1 = hv[i] - cxy, hv[(i + 1) % len(hv)] - cxy
        e = p1 - p0
        den = d[:, 0] * e[1] - d[:, 1] * e[0]
        ok = np.abs(den) > 1e-12
        t = np.where(ok, (p0[0] * e[1] - p0[1] * e[0]) / np.where(ok, den, 1), -1)
        u = np.where(ok, (p0[0] * d[:, 1] - p0[1] * d[:, 0]) / np.where(ok, den, 1), -1)
        hit = ok & (t > 0) & (u >= 0) & (u <= 1)
        R = np.where(hit, np.maximum(R, t), R)
    # her skin's own outline: the furthest point of the thin slab at each bearing (2 degrees wide)
    m2 = body & (np.abs(V[:, 1] - z) < 0.003)
    q2 = (section(z) if EXACT else V[m2][:, [0, 2]]) - cxy
    ang = np.arctan2(q2[:, 0], q2[:, 1]) % (2 * np.pi)
    rad = np.linalg.norm(q2, axis=1)
    S = np.full(nu, np.nan)
    for i, ai in enumerate(a):
        dd = np.abs((ang - ai + np.pi) % (2 * np.pi) - np.pi)
        sel = dd < np.radians(2.5)
        if sel.any():
            S[i] = rad[sel].max()
    gap = (R - S) * 1000
    idx = [int(round(x / 3)) % nu for x in (0, 15, 30, 45, 60, 75, 90, 105, 120)]
    lab = ' '.join('%3d:%5.1f' % (int(round(np.degrees(a[i]))), gap[i]) for i in idx)
    lab2 = ' '.join('%4d:%5.1f' % (-int(round(np.degrees(2 * np.pi - a[i]))), gap[i]) for i in [int(round(x / 3)) % nu for x in (360 - 15, 360 - 30, 360 - 45, 360 - 60, 360 - 75, 360 - 90, 360 - 105)])
    print('row %2d y %.3f  gap mm by bearing (her left +):  %s' % (k, z, lab))
    print('                 her right:                       %s' % lab2)
