"""kit_hips.unweld_rigid (armor-D hipv-2, 16 Nov): two rigid nodes never share a point, so pin_shipped's welded
components stay one weight set each (a shared corner made both hip plates bend with her skin)."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import kit_hips  # noqa: E402
from native_build import Part  # noqa: E402

TRI = np.array([[0, 1, 2]])


def _part(name, P):
    return Part(name, "steel", np.array(P, float), TRI)


def test_shared_corner_is_split_between_two_rigid_nodes():
    a = _part("hipf_l_rigid", [[0, 0, 0], [1, 0, 0], [0, 1, 0]])
    b = _part("hip_l_rigid", [[0, 0, 0], [0, 0, 1], [1, 1, 0]])
    kit_hips.unweld_rigid([a, b])
    d = np.linalg.norm(a.P[:, None] - b.P[None], axis=-1).min()
    assert d > 2e-6
    assert np.allclose(a.P[0], 0) and np.linalg.norm(b.P[0]) < 1e-4  # (only the later node moves, by 0.05 mm)


def test_a_nodes_own_parts_stay_welded():
    a = _part("hip_l_rigid", [[0, 0, 0], [1, 0, 0], [0, 1, 0]])
    b = _part("hip_l_rigid", [[0, 0, 0], [0, 0, 1], [1, 1, 0]])
    kit_hips.unweld_rigid([a, b])
    assert np.allclose(b.P[0], 0)
