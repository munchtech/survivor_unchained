"""P1 R1c: the armpit fill (designed/armpit.json, rule "py:armpit_form.fill"; numbers and their measurements there).

Rule "field"'s moves (sliders.OurSliders.field_delta: C2 masks on the reference surface; "translate", "normal" with an
optional "smooth": normals umbrella-averaged that many steps) plus "fair": a masked umbrella fairing of the body itself.
The armpit's top is a crease (trunk wall and inner arm meet at the vault's apex, 0 mm apart at rest): a move along the
normals, raw or smoothed (10 / 30 steps), pushes its two sides into each other and folds it (her close tier: quad folds
over 60 deg 60 -> 68 at 3 mm, 74-76 at 6 mm, to 95 deg); the fairing moves the apex as one piece into the hollow and
rounds it (no new fold). v scales the move (the fairing's on the body it is laid on)."""
import numpy as np
import scipy.sparse as sp

_CACHE = {}


def smooth_normals(sl, k):
    key = (sl.path, int(k))
    if key not in _CACHE:
        t = sl.topo()
        N = t["N"].copy()
        if k:
            Q = t["Q"]
            e = np.concatenate([Q[:, [0, 1]], Q[:, [1, 2]], Q[:, [2, 3]], Q[:, [3, 0]]])
            n = len(N)
            A = sp.coo_matrix((np.ones(2 * len(e)), (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])), (n, n)).tocsr()
            A.data[:] = 1.0
            Dg = np.asarray(A.sum(1)).ravel()
            M = sp.diags(1.0 / np.maximum(Dg, 1)) @ A
            for _ in range(int(k)):
                N = 0.5 * N + 0.5 * (M @ N)
                N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
        _CACHE[key] = N
    return _CACHE[key]


def _adj(sl):
    key = ("A", sl.path)
    if key not in _CACHE:
        Q = sl.topo()["Q"]
        e = np.concatenate([Q[:, [0, 1]], Q[:, [1, 2]], Q[:, [2, 3]], Q[:, [3, 0]]])
        n = len(sl.V0)
        A = sp.coo_matrix((np.ones(2 * len(e)), (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])), (n, n)).tocsr()
        A.data[:] = 1.0
        _CACHE[key] = (A, np.asarray(A.sum(1)).ravel())
    return _CACHE[key]


def fair(sl, w, V, iters, lam):
    """The masked umbrella fairing's move on body V: each step every point goes lam * w of the way to its neighbours'
    mean (the uniform graph Laplacian; no Taubin mu: in a crease the mean lies inside the hollow, so the fairing
    fills and rounds it, and a mask easing to 0 holds the rim)."""
    A, deg = _adj(sl)
    W = V.copy()
    for _ in range(int(iters)):
        W = W + (lam * w)[:, None] * ((A @ W) / deg[:, None] - W)
    return W - V


def delta(sl, c, V=None):
    P = sl.V0
    sx = np.where(P[:, 0] >= 0, 1.0, -1.0)
    D = np.zeros_like(P)
    for mv in c["moves"]:
        w = sl.mask(mv["mask"], P)
        d = np.zeros_like(P)
        if "translate" in mv:
            d += np.asarray(mv["translate"], float)[None, :] * np.stack([sx, np.ones_like(sx), np.ones_like(sx)], 1)
        if "fair" in mv:
            f = mv["fair"]
            D += fair(sl, w, sl.V0 if V is None else V, f.get("iters", 20), f.get("lam", 0.5)) * float(f.get("k", 1.0))
            continue
        if "normal" in mv:
            d += smooth_normals(sl, mv.get("smooth", 0)) * float(mv["normal"])
        D += w[:, None] * d
    return D


def fill(sl, c, v, V, values):
    return V + v * delta(sl, c, V)
