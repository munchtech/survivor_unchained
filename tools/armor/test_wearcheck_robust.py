"""wearcheck confirm_gap on a thin open rim: the depth is the nearest real face's, not a far wall's (lane D, 17 Nov)."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import wearcheck as wc  # noqa: E402

Z = 0.0005  # half of a 1 mm shell


def _rim():
    """Two antiparallel 1 mm-apart walls (inner normal -z, outer +z) open at x = 0, and a far wall 30 mm below."""
    inner = [[0, 0, -Z], [0, .05, -Z], [.05, 0, -Z]]
    outer = [[0, 0, Z], [.05, 0, Z], [0, .05, Z]]
    far = [[0, 0, -.03], [0, .05, -.03], [.05, 0, -.03]]
    return np.array([inner, outer, far], float)


def test_point_past_a_rim_end_reads_clear_new_and_through_legacy():
    F = _rim()[None]
    O = np.array([[-.003, .001, 0.0]])
    inner = np.array([[True, False, True]])
    try:
        wc.LEGACY = True
        g_old, _ = wc.confirm_gap(O, F, inner, 0.001)
        wc.LEGACY = False
        g_new, _ = wc.confirm_gap(O, F, inner, 0.001)
    finally:
        wc.LEGACY = False
    assert g_old[0] < -0.002          # legacy: one face's normal, 3 mm "through"
    assert abs(min(g_new[0], 0)) <= 0.0015


def test_point_inside_the_rim_wall_stays_through():
    F = _rim()[None]
    O = np.array([[.02, .01, -Z * 0.2]])   # between the walls, 0.4 mm from the inner one
    inner = np.array([[True, False, True]])
    g, _ = wc.confirm_gap(O, F, inner, 0.001)
    assert g[0] < 0 and abs(g[0]) <= 0.0015
