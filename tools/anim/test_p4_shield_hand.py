"""p4 fit_of: the shield layer's `hand` option (the shield hand's local turn held at the start / end pose's)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import p4  # noqa: E402


def _poses(monkeypatch):
    poses = {"a": [0.0, 0.0, 0.0, 1.0], "b": [0.0, 0.7071, 0.0, 0.7071]}
    monkeypatch.setattr(p4, "end_pose", lambda clip, frame=0: {"rot": {"hand_l": poses[clip]}})
    monkeypatch.setattr(p4, "pieces", lambda: {"blade": {}, "shieldp": {}})
    return poses


def _spec(hand):
    return {"fit": {"start": {"clip": "a"}, "end": {"clip": "b"}, "shield": {"solve": True, "hand": hand, "keys": []}}}


def test_hand_start_takes_the_start_pose(monkeypatch):
    poses = _poses(monkeypatch)
    assert p4.fit_of(_spec("start"))["shield"]["hand_rot"] == poses["a"]


def test_hand_end_takes_the_end_pose(monkeypatch):
    poses = _poses(monkeypatch)
    assert p4.fit_of(_spec("end"))["shield"]["hand_rot"] == poses["b"]


def test_no_hand_no_hold(monkeypatch):
    _poses(monkeypatch)
    assert "hand_rot" not in p4.fit_of(_spec(None))["shield"]
