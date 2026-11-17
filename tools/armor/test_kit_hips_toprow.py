"""kit_hips.hug_col's top row (armor-D hipv-2 r5, 17 Nov): a hugging lame's top row stands at the room there too,
never under it (it stayed at the belt radius, so the front hip plate's tucked top swung into the brief's waistband
in run_warden), and at the radius it hangs from where the room is lower."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import kit_hips  # noqa: E402


def flat(v):
    return lambda y, th: np.full(np.broadcast(np.asarray(y, float), np.asarray(th, float)).shape, v)


def test_top_row_rises_to_the_room():
    S, r = kit_hips.hug_col(flat(0.20), flat(0.18), 50.0, 1.13, 0.0, 0.17, 0.06, 6.0, 0.05)
    assert r[0] >= 0.20 - 1e-12
    assert (r >= 0.20 - 1e-12).all()


def test_top_row_keeps_its_radius_over_a_lower_room():
    S, r = kit_hips.hug_col(flat(0.15), flat(0.14), 50.0, 1.13, 0.0, 0.17, 0.06, 6.0, 0.05)
    assert abs(r[0] - 0.17) < 1e-12
