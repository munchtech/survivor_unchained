"""Unit tests for foldcheck's measures on synthetic sheets (pytest, or python tools/body/test_foldcheck.py)."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import foldcheck as fc  # noqa: E402


def sheet(n=8, h=0.01):
    """A flat n x n grid in the xz plane (normals +y), points and triangles."""
    P = np.array([[i * h, 0.0, k * h] for k in range(n) for i in range(n)])
    T = []
    for k in range(n - 1):
        for i in range(n - 1):
            a, b, c, d = k * n + i, k * n + i + 1, (k + 1) * n + i, (k + 1) * n + i + 1
            T += [[a, c, b], [b, c, d]]
    return P, np.array(T)


def test_inverted_finds_a_turned_point():
    P, T = sheet()
    A, EP = fc.vt_adj(T, len(P)), fc.edge_pairs(T)
    nb, sh = fc.inverted(P, P, T, A, EP)
    assert not nb.any() and not sh.any()
    Q = P.copy()
    c = 3 * 8 + 3
    Q[c, 1] = 0.0
    Q[c, 0] += 0.025                     # one point dragged past its neighbours: its fan turns over
    nb, sh = fc.inverted(P, Q, T, A, EP)
    assert nb.any() and sh.any()
    assert all(c in T[t] or np.isin(T[t], T[np.any(T == c, 1)]).any() for t in np.flatnonzero(nb))


def test_crossings_two_sheets():
    P, T = sheet()
    Q = P.copy()
    Q[:, 1] = 0.005
    P2 = np.r_[P, Q]
    T2 = np.r_[T, T + len(P)]
    E = np.unique(np.sort(np.r_[T2[:, [0, 1]], T2[:, [1, 2]], T2[:, [2, 0]]], 1), axis=0)
    he, ht = fc.crossings(P2, T2, E)
    assert not he.any() and not ht.any()          # two parallel sheets 5 mm apart: no crossing
    R = P2.copy()
    R[len(P):, 1] = 0.004 - 0.008 * (R[len(P):, 0] > 0.035)    # the second sheet stepped through the first
    he, ht = fc.crossings(R, T2, E)
    assert he.any() and ht.any()
    assert not ht[:len(T)].all()


def test_crossings_skip_shared_points():
    P, T = sheet(4)
    E = np.unique(np.sort(np.r_[T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]], 1), axis=0)
    he, _ = fc.crossings(P, T, E)
    assert not he.any()                            # a flat sheet's own edges touch only their own fans


def test_min_height_finds_a_sliver():
    P = np.array([[0, 0, 0], [0.01, 0, 0], [0.00843, 0.00000003, 0], [0, 0.01, 0]], float)
    h = fc.min_height(P, np.array([[0, 1, 2], [0, 1, 3]]))
    assert h[0] < fc.DEGEN_MM and h[1] > 5          # three points on a line (mm heights), and a fair triangle


if __name__ == "__main__":
    for k, f in list(globals().items()):
        if k.startswith("test_"):
            f()
            print("ok", k)
