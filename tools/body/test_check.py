"""Unit tests for the body check's measures on synthetic shapes (pytest, or python tools/body/test_check.py)."""
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bends  # noqa: E402
import ray  # noqa: E402


def cylinder(r=0.04, L=0.3, n=48, m=60):
    """A closed cylinder along +Y from 0 to L (outward-wound), points and triangles."""
    a = np.linspace(0, 2 * math.pi, n, endpoint=False)
    y = np.linspace(0, L, m)
    P = np.array([[r * math.cos(t), yy, r * math.sin(t)] for yy in y for t in a])
    T = []
    for i in range(m - 1):
        for k in range(n):
            p, q = i * n + k, i * n + (k + 1) % n
            T += [[p, p + n, q], [q, p + n, q + n]]
    c0, c1 = len(P), len(P) + 1
    P = np.vstack([P, [[0, 0, 0], [0, L, 0]]])
    for k in range(n):
        T += [[c0, k, (k + 1) % n], [c1, (m - 1) * n + (k + 1) % n, (m - 1) * n + k]]
    return P, np.array(T)


def test_rigid_bend_keeps_girth():
    P, T = cylinder()
    sel = np.ones(len(P), bool)
    c, n = np.array([0, 0.15, 0]), np.array([0, 1.0, 0])
    per0, area0 = bends.section(P, T, sel, c, n)
    R = bends.rot([1, 0, 0], 90)
    per1, area1 = bends.section(P @ R.T, T, sel, R @ c, R @ n)
    assert abs(per1 / per0 - 1) < 1e-6 and abs(area1 / area0 - 1) < 1e-6
    # the hull perimeter of a 48-gon of radius 4 cm, and its area
    assert abs(per0 - 2 * 48 * 0.04 * math.sin(math.pi / 48)) < 1e-6
    assert abs(area0 - 0.5 * 48 * 0.04 ** 2 * math.sin(2 * math.pi / 48)) < 1e-6


def test_known_penetration():
    P, T = cylinder()
    sc = ray.scene(P, T)
    pts = np.array([[0.0, 0.15, 0.0], [0.03, 0.1, 0.0], [0.05, 0.15, 0.0], [0.0, 0.35, 0.0]])
    assert ray.inside(sc, pts).tolist() == [True, True, False, False]


def test_outline_deviation():
    ref = {"a": np.array([[0.0, 0.0], [0.1, 0.0]])}
    edge = np.stack([np.linspace(0, 0.1, 200), np.full(200, 0.002)], 1)
    d = bends.deviation(ref, edge)["a"]
    assert abs(d["ref_to_model_mean_mm"] - 2.0) < 0.05 and abs(d["max_px"] - 1.88) < 0.05


if __name__ == "__main__":
    for k, f in list(globals().items()):
        if k.startswith("test_"):
            f()
            print("ok", k)
