"""wearcheck LIFT: a plate that rotates off a moving body reads lift > 10 mm; one that rides along reads ~0."""
import os
import sys

import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wearcheck as wc  # noqa: E402


def _body():
    g = np.linspace(-0.1, 0.1, 21)
    X, Z = np.meshgrid(g, g)
    return np.c_[X.ravel(), np.zeros(X.size), Z.ravel()]   # her skin: a flat patch at y = 0


def _rot(P, deg, about):
    a = np.radians(deg)
    R = np.array([[1, 0, 0], [0, np.cos(a), -np.sin(a)], [0, np.sin(a), np.cos(a)]])
    return (P - about) @ R.T + about


def test_lift_rotating_vs_riding():
    skin0 = _body()
    plate0 = skin0[::7] + [0, 0.005, 0]                       # 5 mm above her at rest
    kd0 = cKDTree(skin0)
    rest_mm = kd0.query(plate0)[0] * 1000
    seated = wc.seated_mask(rest_mm)
    assert seated.all()
    # she moves (shifts), the plate rides along: ~0
    shift = np.array([0.03, 0.02, 0.0])
    riding = wc.lift_of(plate0 + shift, cKDTree(skin0 + shift), rest_mm)
    assert np.abs(riding).max() < 1.0
    # the plate rotates 25 deg off her about its edge: lift > 10
    off = _rot(plate0, 25, np.array([0, 0.005, -0.1]))
    lift = wc.lift_of(off, kd0, rest_mm)
    assert lift.max() > 10


def test_far_points_not_seated():
    assert list(wc.seated_mask([5, 15, 16, 40])) == [True, True, False, False]
