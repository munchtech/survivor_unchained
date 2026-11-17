"""wearcheck poses her skin at her worn rest when a checked piece is built on it (armor-D, 17 Nov): kit_bodice on B."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wearcheck as wc  # noqa: E402
import bodies  # noqa: E402


def test_worn_piece_sets_support_shapes_and_others_none():
    s = wc.worn_shapes_of([{"id": "kit_bodice"}])
    assert s and set(s) <= {"form_support_lift", "form_support_press", "form_support_fill"}
    assert wc.worn_shapes_of([{"id": "kit_brief"}]) == {}
    assert wc.worn_shapes_of([{"id": "no_such_piece"}]) == {}


def test_shapes_move_b_skin_and_leave_a_unchanged():
    s = wc.worn_shapes_of([{"id": "kit_bodice"}])
    b = bodies.BODIES["p1"]
    pb = b.glb
    pa = wc.skin.PEOPLE / "heroine.glb"
    if not (os.path.isfile(pb) and os.path.isfile(str(pa))):
        import pytest
        pytest.skip("body glbs not present")
    db = wc.shape_delta(pb, s, 10 ** 6)
    moved = np.abs(db).max(1) > 1e-6
    assert moved.sum() > 100 and np.abs(db).max() > 0.001   # B: her breasts move by mm
    da = wc.shape_delta(pa, s, 10 ** 6)
    assert np.abs(da).max() == 0                              # A has no support shapes: unchanged
    assert not np.abs(wc.shape_delta(pb, {}, 10 ** 6)).any()  # no shapes: nothing
