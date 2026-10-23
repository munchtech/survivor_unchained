# Body 2 variant A (shape round, 23 Oct 2026): shared helpers on blend dumps (Z up, her front -Y, metres).
import os, numpy as np
from scipy.spatial import cKDTree, ConvexHull
import scipy.sparse as sp

HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))


def load(path):
    d = dict(np.load(path, allow_pickle=False))
    for k in ("names", "bn", "mats"):
        if k in d: d[k] = [str(x) for x in d[k]]
    return d


def fan(ls, lt, lv):
    """triangles (vertex ids), their face ids and loop ids (fan from each face's first corner)."""
    ls = np.asarray(ls); lt = np.asarray(lt)
    nt = lt - 2; f = np.repeat(np.arange(len(ls)), nt)
    k = np.arange(nt.sum()) - np.repeat(np.cumsum(nt) - nt, nt)
    L = np.c_[ls[f], ls[f] + k + 1, ls[f] + k + 2]
    return lv[L], f, L


def edges(ls, lt, lv):
    nxt = np.arange(len(lv)) + 1
    last = ls + lt - 1; nxt[last] = ls
    E = np.sort(np.c_[lv, lv[nxt]], 1)
    return np.unique(E, axis=0)


def adjacency(n, E):
    A = sp.coo_matrix((np.ones(2 * len(E)), (np.r_[E[:, 0], E[:, 1]], np.r_[E[:, 1], E[:, 0]])), shape=(n, n)).tocsr()
    A.data[:] = 1
    return A


def vnormals(P, T):
    n = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]]); N = np.zeros_like(P)
    for k in range(3): np.add.at(N, T[:, k], n)
    return N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-15)


def ss(x):
    x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)


def bump(x, c, w):
    """smooth compact bump: 1 at c, 0 beyond |x-c| >= w (cosine)."""
    u = np.clip(np.abs(x - c) / w, 0, 1); return 0.5 * (1 + np.cos(np.pi * u))


def joints(d, s):
    bn = d["bn"]; g = lambda n: np.asarray(d["bh"][bn.index(n + "_" + s)], float)
    return dict(C=g("clavicle"), A=g("upperarm"), E=g("lowerarm"), H=g("hand"))


def armframe(d, s, P=None):
    """per point: tu (fraction shoulder->elbow along the upper-arm bone), tf (elbow->wrist), radial unit vectors and
    angles about each bone. phi 0 = up (world Z made normal to the bone), 90 = front (-Y), sign so +90 is front on both sides."""
    P = d["P"] if P is None else P; j = joints(d, s); out = dict(j=j)
    for nm, o, e in (("u", j["A"], j["E"]), ("f", j["E"], j["H"])):
        ax = e - o; L = np.linalg.norm(ax); n = ax / L
        up = np.array([0, 0, 1.]); top = up - (up @ n) * n; top /= np.linalg.norm(top)
        fr = np.array([0, -1., 0]); fr = fr - (fr @ n) * n - (fr @ top) * top; fr /= np.linalg.norm(fr)
        dd = P - o; t = dd @ n / L; rv = dd - np.outer(dd @ n, n); r = np.linalg.norm(rv, axis=1)
        e_ = rv / np.maximum(r, 1e-12)[:, None]
        phi = np.degrees(np.arctan2(e_ @ fr, e_ @ top))
        out[nm] = dict(o=o, n=n, L=L, top=top, fr=fr, t=t, r=r, e=e_, phi=phi)
    out["side"] = (P[:, 0] < 0) if s == "r" else (P[:, 0] > 0)
    return out


def section(P, T, o, n, top, fr, rmax=0.075, keep=None):
    """cut of the mesh by the plane through o normal n: points (2D in top/fr) of the piece round the axis."""
    s = (P - o) @ n
    tt = T if keep is None else T[keep[T].all(1)]
    st = s[tt]; pts = []
    for k in range(3):
        i, j = tt[:, k], tt[:, (k + 1) % 3]; si, sj = st[:, k], st[:, (k + 1) % 3]; x = si * sj < 0
        w = si[x] / (si[x] - sj[x]); pts.append(P[i[x]] + (P[j[x]] - P[i[x]]) * w[:, None])
    p = np.concatenate(pts)
    if len(p) < 8: return None
    dd = p - o; dd -= np.outer(dd @ n, n); rr = np.linalg.norm(dd, axis=1); m = rr < rmax
    if m.sum() < 8: return None
    return np.c_[dd[m] @ top, dd[m] @ fr]


def girth(q):
    h = ConvexHull(q); v = q[h.vertices]; return float(np.linalg.norm(np.roll(v, -1, 0) - v, axis=1).sum())


def cross2(a, b): return a[..., 0] * b[..., 1] - a[..., 1] * b[..., 0]


def uv_islands(ls, lt, lv, uv, mi, faces):
    """UV-connected components of `faces` (corners joined where vertex, UV and material agree): label per face."""
    from scipy.sparse.csgraph import connected_components
    faces = np.asarray(faces); L = np.concatenate([np.arange(ls[i], ls[i] + lt[i]) for i in faces]); fl = np.repeat(faces, lt[faces])
    key = np.c_[lv[L], np.round(uv[L] * 1e6).astype(np.int64), mi[fl]]
    _, uid = np.unique(key, axis=0, return_inverse=True); uid = uid.ravel()
    off = np.r_[0, np.cumsum(lt[faces])[:-1]]; r = []; c = []
    for k in range(1, int(lt[faces].max())):
        m = lt[faces] > k; r.append(uid[off[m]]); c.append(uid[off[m] + k])
    A = sp.coo_matrix((np.ones(sum(len(x) for x in r)), (np.concatenate(r), np.concatenate(c))), shape=(uid.max() + 1,) * 2)
    n, lab = connected_components(A, directed=False)
    return lab[uid[off]], n
