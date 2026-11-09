"""clipcheck's spike rule after a frozen hold (A1 Stage B, solver F4): the median over the moving steps only.

    python -m pytest -q tools/anim/test_spike_rule.py
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "body"))
import clipcheck as CC  # noqa: E402


def _rx(deg):
    a = np.radians(deg)
    m = np.eye(4)
    m[1:3, 1:3] = [[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]]
    return m


def _clip(hold, steps):
    """One root bone: frozen for `hold` frames, then turning by `steps` (deg per frame)."""
    ang = np.r_[np.zeros(hold), np.cumsum(steps)]
    return np.stack([_rx(a) for a in ang])[:, None]


def test_fast_beat_after_a_hold_is_not_a_spike():
    # (a 40-frame brace, then a burst spread over 3 frames (6, 9, 6 deg) inside motion at ~2.5 deg a frame: the old
    # median over all steps was 0 and flagged it)
    steps = [2, 3, 2.5, 6, 9, 6, 2.5, 2, 3, 2.5, 2, 3]
    out, worst, _ = CC.pops(["root"], [-1], _clip(40, steps), ["root"], False)
    assert out == {}
    assert worst[0] > 8.9


def test_one_frame_spike_after_a_hold_still_fails():
    steps = [12, -12, 2.5, 2, 3, 2.5, 2, 3, 2.5, 2]      # (one frame out and straight back, right after the hold)
    out, _, _ = CC.pops(["root"], [-1], _clip(40, steps), ["root"], False)
    assert out["root"]["frame"] in (40, 41)


def test_lone_spike_after_a_hold_sets_no_bar():
    out, _, _ = CC.pops(["root"], [-1], _clip(40, [8, -8] + [0] * 5), ["root"], False)
    assert "root" in out
