"""p4.skin_gap, the body field's distance: a point off her side in a skin vertex's tangent plane reads its true gap,
not the 0-8 mm the bare normal projection gave (solver F3: the leap's raised sword 40 cm off her read 0 mm and the clear
layer moved the arm); a point just off her skin still reads along the normal.

    python -m pytest -q tools/anim/test_p4_field.py
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import p4  # noqa: E402


def gap(d, pr, inside):
    return float(p4.skin_gap(np.array([d]), np.array([pr]), np.array([inside]))[0])


def test_far_point_in_the_tangent_plane_reads_its_gap():
    assert gap(0.40, 0.002, False) > 0.38


def test_near_point_reads_along_the_normal():
    # (5 mm off a vertex sideways (inside its patch), 3 mm out: the normal's 3 mm, not the vertex's 5.8)
    assert abs(gap(np.hypot(0.005, 0.003), 0.003, False) - 0.003) < 1e-9


def test_inside_reads_negative():
    assert abs(gap(0.02, -0.02, True) + 0.02) < 1e-9
    assert gap(0.40, -0.001, True) < -0.38


def test_sign_disagreeing_with_the_normal_keeps_the_vertex_distance():
    assert abs(gap(0.03, -0.01, False) - 0.03) < 1e-9
