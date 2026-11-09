"""Unit tests for the gear fit engine's bind/evaluate core on a tiny synthetic body (pytest, or python this file)."""
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gear_fit as gf  # noqa: E402


def cylinder(r=0.05, L=0.3, n=32, m=24):
    a = np.linspace(0, 2 * math.pi, n, endpoint=False)
    y = np.linspace(0, L, m)
    P = np.array([[r * math.cos(t), yy, r * math.sin(t)] for yy in y for t in a])
    T = []
    for i in range(m - 1):
        for k in range(n):
            p, q = i * n + k, i * n + (k + 1) % n
            T += [[p, p + n, q], [q, p + n, q + n]]
    return P, np.array(T)


def body(P, T):
    n = len(P)
    J = np.zeros((n, 8), np.int64)
    J[:, 1] = 1
    W = np.zeros((n, 8))
    W[:, 0] = 1 - P[:, 1] / P[:, 1].max()
    W[:, 1] = 1 - W[:, 0]
    head = np.array([[0, 5.0, 0], [0.01, 5.0, 0], [0, 5.0, 0.01]])
    return gf.Body(P, T, J, W, {"s": np.tile([0, 0.001, 0], (n, 1))}, head, np.array([[0, 1, 2]]),
                   np.zeros((3, 4), np.int64), np.c_[np.ones(3), np.zeros((3, 3))], ["a", "b"])


def sleeve(r=0.058, n=24, m=10):
    P, T = cylinder(r, 0.2, n, m)
    return P + [0, 0.05, 0], T


def test_bind_eval_identity():
    P, T = cylinder()
    b = body(P, T)
    X, _ = sleeve()
    tri, bq, off, _ = gf.bind_points(b, X)
    Xe, _ = gf.eval_points(b, tri, bq, off)
    assert np.abs(Xe - X).max() < 1e-8          # 0.01 micron: the bind body gives back the bind geometry


def test_follows_and_rigid_preserved():
    P, T = cylinder()
    b = body(P, T)
    X, Ts = sleeve()
    tri, bq, off, _ = gf.bind_points(b, X)
    # a second body: +8% girth fading along y, the sleeve follows it
    s = 1 + 0.08 * np.clip(P[:, 1] / 0.3, 0, 1)
    b2 = b.with_points(np.vstack([P * np.c_[s, np.ones(len(P)), s], b.V[b.nt:]]), "fat")
    X2, _ = gf.eval_points(b2, tri, bq, off)
    assert not np.isnan(X2).any()
    r1 = np.hypot(X[:, 0], X[:, 2])
    r2 = np.hypot(X2[:, 0], X2[:, 2])
    assert (r2 > r1 + 1e-4).mean() > 0.9          # grew with the body
    # rigid: Procrustes of the bendy evaluation onto the bind points, every pairwise distance kept
    R, ca, cb = gf.kabsch(X, X2)
    Xr = (X - ca) @ R.T + cb
    d0 = np.linalg.norm(X[:, None] - X[None], axis=2)
    d1 = np.linalg.norm(Xr[:, None] - Xr[None], axis=2)
    assert np.abs(d1 - d0).max() < 5e-8
    # smoothing a zero displacement is the identity
    E = gf.edges_of(Ts)
    D = gf.smooth_field(np.zeros_like(X), E, len(X), np.ones(len(X)), 8)
    assert np.abs(D).max() == 0


def test_weights_at_bound_point():
    P, T = cylinder()
    b = body(P, T)
    X, _ = sleeve()
    tri, bq, off, _ = gf.bind_points(b, X)
    J, W = gf.body_weights(b, tri.astype(np.int64), gf.unq(bq))
    assert np.allclose(W.sum(1), 1, atol=1e-6)
    wb = np.where(J == 1, W, 0).sum(1)
    yb = (X[:, 1]) / 0.3
    assert np.abs(wb - np.clip(yb, 0, 1)).max() < 0.05


def test_field_two_cylinders():
    """The follow field: a sleeve bound across two cylinders (2 cm stand-off) follows one cylinder's +10% girth as one
    smooth surface (the per-triangle evaluation tears it where the binding switches cylinders), clear of the new skin,
    and the bind body gives back the bind geometry exactly."""
    import gear_field as gfl
    P, T = cylinder(0.05, 0.3, 48, 30)
    n = len(P)
    P2 = np.vstack([P + [-0.055, 0, 0], P + [0.055, 0, 0]])
    T2 = np.vstack([T, T + n])
    b = body(P2, T2)
    a = np.linspace(0, 2 * math.pi, 96, endpoint=False)
    X = np.array([[0.125 * math.cos(t), y, 0.07 * math.sin(t)] for y in np.linspace(0.05, 0.25, 21) for t in a])
    Ts = []
    for i in range(20):
        for k in range(96):
            p_, q = i * 96 + k, i * 96 + (k + 1) % 96
            Ts += [[p_, p_ + 96, q], [q, p_ + 96, q + 96]]
    E = gf.edges_of(np.array(Ts))
    tri, bq, off = gf.bind_points(b, X)[:3]
    c0 = np.linalg.norm(off.astype(np.float64), axis=1)
    V = b.V.copy()
    r = V[n:2 * n] - [0.055, 0, 0]
    V[n:2 * n] += 0.10 * r * [1, 0, 1]                     # the right cylinder grows 10% in girth
    b2 = b.with_points(V, "grown")
    Xb, Fb = gf.eval_points(b, tri, bq, off)
    X2, F2 = gf.eval_points(b2, tri, bq, off)
    Xe, _ = gfl.exact_follow(X2, F2, Xb, Fb, off)
    Xf, G = gfl.field_for(b2, b)(Xb)
    bt = gfl.beta(c0)
    Xn, _ = gfl.clear_push(b2, Xe + bt[:, None] * (Xf - Xe), c0, np.ones(len(X), bool))
    l0 = np.linalg.norm(Xb[E[:, 0]] - Xb[E[:, 1]], axis=1)
    st = lambda Y: np.abs(np.linalg.norm(Y[E[:, 0]] - Y[E[:, 1]], axis=1) / l0 - 1)  # noqa: E731
    assert not np.isnan(Xn).any()
    assert st(Xe).max() > 0.18                              # bound triangle by triangle: torn where the binding switches
    assert st(Xn).max() < 0.16                              # the field: one surface (the cylinder itself grew 10%)
    assert st(Xn).max() < 0.8 * st(Xe).max()
    c, _ = gfl.signed_clear(b2, Xn, k=16)
    assert (c > c0 - 5e-4).all()                            # kept its clearance on the grown body
    grew = Xn[:, 0] > 0.08
    assert (np.hypot(Xn[grew, 0] - 0.055, Xn[grew, 2]) > np.hypot(Xb[grew, 0] - 0.055, Xb[grew, 2]) + 2e-3).all()
    gfl._CACHE.clear()
    Xi, _ = gfl.field_for(b.with_points(b.V.copy(), "same"), b)(Xb)
    assert np.abs(Xi - Xb).max() < 1e-12                    # no move: the bind geometry


if __name__ == "__main__":
    for k, f in list(globals().items()):
        if k.startswith("test_"):
            f()
            print(k, "ok")
