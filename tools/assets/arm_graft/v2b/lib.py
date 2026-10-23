# Body 2 variant B (her original arm densified and resculpted): shared helpers. Blend coords (Z up, -Y front).
import numpy as np
from scipy.spatial import cKDTree, ConvexHull
import scipy.sparse as sp


def ss(x):
    x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)


def win(t, a0, a1, b0, b1):
    return ss((t - a0) / (a1 - a0)) * ss((b1 - t) / (b1 - b0))


def load(path):
    d = dict(np.load(path)); ls, lt, lv = d["ls"], d["lt"], d["lv"]
    d["polys"] = [lv[s:s + n] for s, n in zip(ls, lt)]
    d["names"] = [str(x) for x in d["names"]]; d["bn"] = [str(x) for x in d["bn"]]
    return d


def bone(d, name):
    i = d["bn"].index(name); return d["bh"][i], d["bt"][i]


class Frame:
    """Arm frame for side s ('r'/'l'): t along the upper arm (0 shoulder joint, 1 elbow), then tf along the forearm
    (0 elbow, 1 wrist); u = 1 + tf past the elbow's bisecting plane. phi about the active bone: 0 = top (blend +Z
    projected), +90 = front (-Y)."""
    def __init__(s, d, side):
        s.A, s.E = bone(d, "upperarm_" + side); s.Wr = bone(d, "hand_" + side)[0]
        s.nu = (s.E - s.A) / np.linalg.norm(s.E - s.A); s.Lu = np.linalg.norm(s.E - s.A)
        s.nf = (s.Wr - s.E) / np.linalg.norm(s.Wr - s.E); s.Lf = np.linalg.norm(s.Wr - s.E)
        s.side = side; s.sx = -1.0 if side == "r" else 1.0
        bis = s.nu + s.nf; s.bis = bis / np.linalg.norm(bis)

    def axes(s, n):
        up = np.array([0, 0, 1.0]); top = up - (up @ n) * n; top /= np.linalg.norm(top)
        fr = np.cross(n, top)
        if fr[1] > 0: fr = -fr
        return top, fr

    def coords(s, P):
        P = np.atleast_2d(P)
        fore = (P - s.E) @ s.bis > 0
        t = (P - s.A) @ s.nu / s.Lu; tf = (P - s.E) @ s.nf / s.Lf
        u = np.where(fore, 1 + tf, t)
        O = np.where(fore[:, None], s.E, s.A); N = np.where(fore[:, None], s.nf, s.nu)
        dd = P - O; ax = (dd * N).sum(1); rv = dd - ax[:, None] * N; r = np.linalg.norm(rv, axis=1)
        tu, fu = s.axes(s.nu); tF, fF = s.axes(s.nf)
        TOP = np.where(fore[:, None], tF, tu); FR = np.where(fore[:, None], fF, fu)
        phi = np.degrees(np.arctan2((rv * FR).sum(1), (rv * TOP).sum(1)))
        side = np.sign(P[:, 0]) == np.sign(s.sx)
        return dict(t=t, tf=tf, u=u, fore=fore, r=r, phi=phi, e=rv / np.maximum(r, 1e-9)[:, None], side=side, N=N)


def tri_split(polys, uvc=None):
    """polys (list of index arrays) -> triangles (fan) + source poly id + corner index map."""
    T = []; src = []; cidx = []; c0 = 0
    for k, p in enumerate(polys):
        n = len(p)
        for j in range(1, n - 1):
            T.append((p[0], p[j], p[j + 1])); src.append(k); cidx.append((c0, c0 + j, c0 + j + 1))
        c0 += n
    return np.array(T), np.array(src), np.array(cidx)


def vnormals(V, T):
    fn = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    N = np.zeros_like(V)
    for k in range(3): np.add.at(N, T[:, k], fn)
    return N / np.maximum(np.linalg.norm(N, axis=1), 1e-12)[:, None]


def section(P, T, o, n, top, fr, keep=None):
    """Plane (o, n) cut of triangles T over P: returns the 2D points (along top, fr) of edge crossings."""
    s = (P - o) @ n
    Tk = T if keep is None else T[keep[T].all(1)]
    pts = []
    for a, b in ((0, 1), (1, 2), (2, 0)):
        ia, ib = Tk[:, a], Tk[:, b]; sa, sb = s[ia], s[ib]
        m = (sa * sb) < 0
        w = (sa[m] / (sa[m] - sb[m]))[:, None]
        q = P[ia[m]] + w * (P[ib[m]] - P[ia[m]])
        pts.append(q)
    q = np.concatenate(pts) - o
    return np.c_[q @ top, q @ fr]


def girth(q2):
    if len(q2) < 5: return np.nan
    h = ConvexHull(q2); v = q2[h.vertices]; return np.linalg.norm(np.roll(v, -1, 0) - v, axis=1).sum()


STATIONS = [("up", t) for t in (0.15, 0.30, 0.46, 0.50, 0.60, 0.75, 0.90, 1.0)] + [("fo", t) for t in (0.1, 0.2, 0.3, 0.5, 0.7, 0.85, 0.9, 0.95)]


def profile(P, T, F, keep, stations=STATIONS, rad=0.08):
    """per station: girth, lateral (+top), medial (-top), front (+fr), back (-fr) extents from the bone axis, in mm."""
    out = []
    for seg, t in stations:
        if seg == "up": o = F.A + t * F.Lu * F.nu; n = F.nu
        else: o = F.E + t * F.Lf * F.nf; n = F.nf
        top, fr = F.axes(n)
        q = section(P, T, o, n, top, fr, keep)
        q = q[np.linalg.norm(q, axis=1) < rad] if len(q) else q
        if len(q) < 5: out.append((seg, t) + (np.nan,) * 5); continue
        out.append((seg, t, girth(q) * 1e3, q[:, 0].max() * 1e3, -q[:, 0].min() * 1e3, q[:, 1].max() * 1e3, -q[:, 1].min() * 1e3))
    return out


def show_profile(rows, label=""):
    print("%s seg    t  girth  /S     lat   med  front  back | frontW depth  w:d" % label)
    for seg, t, g, la, me, fr, bk in rows:
        print("   %s %5.2f %6.0f %.3f %5.1f %5.1f %5.1f %5.1f | %5.0f %5.0f %5.2f" % (seg, t, g, g / 1654, la, me, fr, bk, la + me, fr + bk, (la + me) / (fr + bk)))
