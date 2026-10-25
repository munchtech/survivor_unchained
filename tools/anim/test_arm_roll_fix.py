"""arm_roll_fix: the wrist brought in range by the hand's slack, the hand kept where it was; a straight arm's roll
traded into the forearm with the hand's turn kept; idempotent.  python tools/anim/test_arm_roll_fix.py  (or pytest)"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import arm_roll_fix as F  # noqa: E402
from rig import Skeleton, qaxis, qinv, qmul  # noqa: E402

SK = Skeleton.load()
I = SK.index


def _pose(T=12, bend=80.0, roll=0.0, dev=0.0):
    rot = np.tile(SK.rest_rot, (T, 1, 1)).astype(float)
    pos = np.tile(SK.rest_pos, (T, 1, 1)).astype(float)
    arm = F.Arm(SK, "r")
    for t in range(T):
        rot[t, arm.u] = qmul(arm.ru, qaxis([0, 1.0, 0], roll * (0.9 + 0.1 * t / T)))
        rot[t, arm.l] = qaxis(arm.hinge, bend)
        rot[t, arm.h] = qmul(arm.rh, qaxis([1.0, 0, 0], dev))
    return rot, pos


def _deg(a, b):
    return np.degrees(2 * np.arccos(np.clip(np.abs(np.sum(a * b, axis=-1)), 0, 1)))


def test_wrist_slack_keeps_the_hand_where_it_was():
    rot, pos = _pose(dev=-45.0)
    rep = {}
    new = F.fix_rot(SK, rot, pos, sides="r", report=rep, slack=30.0)
    b, a = rep["r"]["before"], rep["r"]["after"]
    assert min(x["ulnar"] for x in b) > 35
    assert max(x["ulnar"] for x in a) < F.LIMITS["ulnar"] + 1.5
    g0, p0 = SK.fk(rot, pos)
    g1, p1 = SK.fk(new, pos)
    h = I["hand_r"]
    assert np.max(np.linalg.norm(p1[:, h] - p0[:, h], axis=-1)) < 1e-4


def test_no_slack_keeps_the_hands_turn():
    rot, pos = _pose(dev=-45.0)
    new = F.fix_rot(SK, rot, pos, sides="r", slack=0.0)
    g0, p0 = SK.fk(rot, pos)
    g1, p1 = SK.fk(new, pos)
    h = I["hand_r"]
    assert np.max(_deg(g0[:, h], g1[:, h])) < 0.1
    assert np.max(np.linalg.norm(p1[:, h] - p0[:, h], axis=-1)) < 1e-4


def test_straight_arm_roll_into_the_forearm():
    rot, pos = _pose(bend=4.0, roll=150.0)
    rep = {}
    new = F.fix_rot(SK, rot, pos, sides="r", report=rep)
    a = rep["r"]["after"]
    assert max(abs(x["roll"]) for x in a) < F.LIMITS["roll_ext"] + 5
    assert max(abs(x["pron"]) for x in a) < F.LIMITS["pron"] + 5
    g0, p0 = SK.fk(rot, pos)
    g1, p1 = SK.fk(new, pos)
    h = I["hand_r"]
    assert np.max(_deg(g0[:, h], g1[:, h])) < 0.1
    assert np.max(np.linalg.norm(p1[:, h] - p0[:, h], axis=-1)) < 1e-4
    # continuous: no frame-to-frame jump in the upper arm
    assert np.max(_deg(new[1:, I["upperarm_r"]], new[:-1, I["upperarm_r"]])) < 10


def test_in_range_is_left_alone_and_idempotent():
    rot, pos = _pose(bend=60.0, roll=20.0, dev=-5.0)
    new = F.fix_rot(SK, rot, pos, slack=30.0)
    assert np.max(np.abs(new - rot)) < 1e-6 or np.max(_deg(new, rot)) < 0.05
    d = {"name": "x", "fps": 30, "loop": False, "length": 1.0, "path": SK.path, "meta": {"arm_roll_fix": F.VERSION},
         "tracks": [{"bone": "hand_r", "type": "rot", "keys": rot[:, I["hand_r"]].tolist()}]}
    assert F.fix_json(SK, d) is d


if __name__ == "__main__":
    for k, f in list(globals().items()):
        if k.startswith("test_"):
            f()
            print("ok", k)
