"""flex_check on synthetic parts: a rigid ride reads 0 flex, a blend of two bones that differ reads its bend; two
bands round a limb read their overlap, and an opening when the lower one slides off."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import flex_check as fc  # noqa: E402


def _rot(deg):
    c, s = np.cos(np.radians(deg)), np.sin(np.radians(deg))
    M = np.eye(4)
    M[:3, :3] = [[c, -s, 0], [s, c, 0], [0, 0, 1]]
    return M


def _band(y0, y1, r=0.05):
    th = np.linspace(-np.pi, np.pi, 48, endpoint=False)
    return np.array([[r * np.sin(t), y, r * np.cos(t)] for y in np.linspace(y0, y1, 5) for t in th])


def test_rigid_reads_zero_and_a_blend_bends():
    X = _band(0.0, -0.1)
    S = np.stack([np.stack([_rot(a), _rot(-a)]) for a in (0, 30, 60)])
    J = np.zeros((len(X), 8), int)
    W = np.zeros((len(X), 8))
    W[:, 0] = 1
    mx, _ = fc.flex(X, J, W, S)
    assert mx.max() < 1e-6                                           # one bone: rigid
    J[:, 1], W[:, :2] = 1, np.c_[np.linspace(0, 1, len(X)), 1 - np.linspace(0, 1, len(X))]
    mx, _ = fc.flex(X, J, W, S)
    assert mx[0] < 1e-6 and mx[2] > mx[1] > 1.0                      # a per-vertex blend bends with the angle


def test_lap_reads_overlap_and_opening():
    heads = np.array([[0, 0, 0], [0, -0.3, 0]], float)               # a limb down -y: bone 0 -> bone 1
    up, low = _band(0.0, -0.10), _band(-0.08, -0.18, 0.052)           # 20 mm of lap at rest
    J = lambda X, b: np.pad(np.full((len(X), 1), b), ((0, 0), (0, 7)))  # noqa: E731
    W = lambda X: np.pad(np.ones((len(X), 1)), ((0, 0), (0, 7)))      # noqa: E731
    S = np.broadcast_to(np.eye(4), (2, 2, 4, 4)).copy()
    S[1, 1, :3, 3] = [0, -0.03, 0]                                    # frame 1: the lower band slides 30 mm down
    o, sgn = fc.lap((up, J(up, 0), W(up)), (low, J(low, 1), W(low)), S, heads, 0, 1)
    assert sgn == 1.0
    assert np.allclose(np.nanmin(o[0]), 20.0, atol=0.01) and np.allclose(np.nanmin(o[1]), -10.0, atol=0.01)
    assert np.isfinite(o[0]).sum() >= 20
