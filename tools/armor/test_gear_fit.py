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


if __name__ == "__main__":
    for k, f in list(globals().items()):
        if k.startswith("test_"):
            f()
            print(k, "ok")
