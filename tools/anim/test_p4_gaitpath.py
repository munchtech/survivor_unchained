"""p4 gen's root path for a directional gait (A1 lead 19, the 2D move node's back and side walks): root2d straight along
`deg` in her frame with `face_deg`, a constant heading track (her facing held toward the aim while the root goes back or
sideways); without face_deg no heading is sent (the forward walk's jobs unchanged).

    python -m pytest -q tools/anim/test_p4_gaitpath.py
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import p4  # noqa: E402


def test_back_path_keeps_her_facing():
    g = {"seconds": 4.0, "root2d": {"kind": "straight", "speed": 1.3, "ramp": 0.5, "deg": 180, "face_deg": 0, "every": 1}}
    out = p4.path_of(g, 1.0)
    xz = np.array(out["xz"])
    assert len(out["heading"]) == len(xz) and set(out["heading"]) == {0.0}
    v = (xz[-1] - xz[-2]) * p4.KFPS
    assert abs(v[0]) < 1e-3 and abs(v[1] + 1.3) < 1e-3


def test_side_path_and_forward_unchanged():
    g = {"seconds": 4.0, "root2d": {"kind": "straight", "speed": 1.3, "ramp": 0.5, "deg": 90, "face_deg": 0}}
    xz = np.array(p4.path_of(g, 1.0)["xz"])
    assert abs((xz[-1, 0] - xz[-2, 0]) * p4.KFPS - 1.3) < 1e-3 and abs(xz[-1, 1]) < 1e-6
    f = p4.path_of({"seconds": 4.0, "root2d": {"kind": "straight", "speed": 1.2, "ramp": 0.8, "every": 1}}, 1.0)
    assert "heading" not in f
