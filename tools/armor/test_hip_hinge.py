"""Her hip hinges (tools/anim/helpers.py SPEC "hinges"): extend() adds them at their pivot with no global rest turn,
drive_hinges turns `amount` of the thigh's swing and none of its roll, pin_shipped.with_hinges binds them in a piece as
the skeleton has them, and the game's rig_helpers.json carries the spec."""
import json
import os
import sys

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "anim"))
sys.path.insert(0, HERE)

import helpers as hp  # noqa: E402
from rig import Skeleton, qaxis, qinv, qmul, qrot  # noqa: E402


def _deg(q):
    q = np.asarray(q, float)
    return float(np.degrees(2 * np.arctan2(np.linalg.norm(q[:3]), abs(q[3]))))


@pytest.fixture(scope="module")
def sk():
    return hp.extend(Skeleton.load())


def test_extend_adds_the_hinges_at_their_pivots(sk):
    grot, gpos = sk.rest_globals()
    hg = hp.SPEC["hinges"][0]
    for s in "lr":
        j = sk.index[hg["name"].replace("{s}", s)]
        assert sk.names[sk.parent[j]] == hg["parent"]
        assert _deg(grot[0, j]) < 1e-6
        assert np.abs(gpos[0, j] - hp.hinge_pivot(hg, s)).max() < 1e-9


def _posed(sk, s, turn_global):
    """The rest pose with the thigh turned `turn_global` (her rest axes), driven."""
    rot = sk.rest_rot.copy()
    t = sk.index["thigh_" + s]
    grot, _ = sk.rest_globals()
    gpar = grot[0, sk.parent[t]]
    rot[t] = qmul(qinv(gpar), qmul(turn_global, grot[0, t]))
    hp.drive_hinges(sk, rot)
    return rot


def test_half_the_swing_none_of_the_roll(sk):
    hg = hp.SPEC["hinges"][0]
    grot, _ = sk.rest_globals()
    for s in "lr":
        j = sk.index[hg["name"].replace("{s}", s)]
        assert _deg(qmul(qinv(sk.rest_rot[j]), _posed(sk, s, np.array([0, 0, 0, 1.0]))[j])) < 1e-6
        line = qrot(grot[0, sk.index["thigh_" + s]], [0, 1.0, 0])
        rot = _posed(sk, s, qaxis(np.cross(line, [0, 0, 1.0]), -70))
        assert abs(_deg(qmul(qinv(sk.rest_rot[j]), rot[j])) - 70 * hg["amount"]) < 1e-6
        rot = _posed(sk, s, qaxis(line, 50))
        assert _deg(qmul(qinv(sk.rest_rot[j]), rot[j])) < 1e-6


def test_the_piece_bind_carries_the_hinges_as_the_skeleton_has_them(sk):
    import pin_shipped as pn
    import body_follow_post as bf
    B = pn.with_hinges(bf.Body(os.path.join(ROOT, "godot", "art", "people", "heroine.glb")))
    n = len(B.names)
    assert pn.with_hinges(B) is B and len(B.names) == n and B.W.shape[1] == n and len(B.ibm) == n
    par = {c: i for i, x in enumerate(B.nodes) for c in x.get("children", [])}

    def world(i):
        return (world(par[i]) if i in par else np.eye(4)) @ pn._trs(B.nodes[i])

    _, gpos = sk.rest_globals()
    for s in "lr":
        nm = "thigh_hinge_" + s
        k = B.names.index(nm)
        W = world(B.joint_nodes[k])
        assert np.abs(W[:3, :3] - np.eye(3)).max() < 1e-5
        assert np.abs(W[:3, 3] - gpos[0, sk.index[nm]]).max() < 1e-5
        assert np.abs(B.ibm[k].reshape(4, 4).T @ W - np.eye(4)).max() < 1e-5
        assert not B.W[:, k].any()


def test_the_games_spec_carries_the_hinges():
    game = json.loads(open(hp.SPEC_FILE, encoding="utf-8").read())
    assert game["hinges"] == hp.SPEC["hinges"]


def test_the_tasset_hinge_turns_its_bottom_forward_with_the_leading_thigh(sk):
    tg = hp.SPEC["tassets"][0]
    j = sk.index[tg["name"]]
    grot, gpos = sk.rest_globals()
    assert sk.names[sk.parent[j]] == tg["parent"] and _deg(grot[0, j]) < 1e-6
    assert np.abs(gpos[0, j] - np.asarray(tg["pivot"])).max() < 1e-9

    def turned(**deg):
        rot = sk.rest_rot.copy()
        for s, d in deg.items():
            t = sk.index["thigh_" + s]
            # (a forward swing, global: about the axis taking her -Y toward +Z)
            rot[t] = qmul(qinv(grot[0, sk.parent[t]]), qmul(qaxis([-1.0, 0, 0], d), grot[0, t]))
        hp.drive_tassets(sk, rot)
        return qmul(qinv(sk.rest_rot[j]), rot[j])

    assert _deg(turned()) < 1e-6
    k, a = tg["soft"], tg["amount"]
    # the leading thigh alone (the other at rest, more than `soft` behind it), less soft/4, past the softrelu's knee
    assert abs(_deg(turned(l=60)) - a * (60 - k / 4 - k / 2)) < 1e-3
    assert abs(_deg(turned(l=60, r=-30)) - a * (60 - k / 4 - k / 2)) < 1e-3
    assert abs(_deg(turned(r=60)) - _deg(turned(l=60))) < 1e-3
    assert _deg(turned(l=-25, r=-25)) < 1e-6
    # the bottom forward and up
    tip = qrot(turned(l=60), [0, -1.0, 0])
    assert tip[2] > 0.3 and tip[1] < 0


def test_the_piece_bind_carries_the_tasset_hinge(sk):
    import pin_shipped as pn
    import body_follow_post as bf
    B = pn.with_hinges(bf.Body(os.path.join(ROOT, "godot", "art", "people", "heroine.glb")))
    n = len(B.names)
    assert pn.with_hinges(B) is B and len(B.names) == n and B.W.shape[1] == n and len(B.ibm) == n
    par = {c: i for i, x in enumerate(B.nodes) for c in x.get("children", [])}

    def world(i):
        return (world(par[i]) if i in par else np.eye(4)) @ pn._trs(B.nodes[i])

    _, gpos = sk.rest_globals()
    nm = hp.SPEC["tassets"][0]["name"]
    k = B.names.index(nm)
    W = world(B.joint_nodes[k])
    assert np.abs(W[:3, :3] - np.eye(3)).max() < 1e-5
    assert np.abs(W[:3, 3] - gpos[0, sk.index[nm]]).max() < 1e-5
    assert np.abs(B.ibm[k].reshape(4, 4).T @ W - np.eye(4)).max() < 1e-5
    assert not B.W[:, k].any()


def test_the_games_spec_carries_the_tasset_hinge():
    game = json.loads(open(hp.SPEC_FILE, encoding="utf-8").read())
    assert game["tassets"] == hp.SPEC["tassets"]


def test_pauldron_hinge_turns_half_the_arms_swing_none_of_its_roll(sk):
    """pauldron_hinge_{s} (armor-D 16 Nov): at rest it equals its rest; a pure 90 deg arm raise turns it 45; a pure
    roll leaves it unturned; the sides mirror."""
    hg = next(h for h in hp.SPEC["hinges"] if h["name"].startswith("pauldron_hinge"))
    assert hg["parent"] == "clavicle_{s}" and hg["bone"] == "upperarm_{s}" and hg["amount"] == 0.5
    grot, gpos = sk.rest_globals()
    turns = {}
    for s in "lr":
        j = sk.index[hg["name"].replace("{s}", s)]
        assert sk.names[sk.parent[j]] == "clavicle_" + s
        assert _deg(grot[0, j]) < 1e-4
        assert np.abs(gpos[0, j] - hp.hinge_pivot(hg, s)).max() < 1e-4
        u = sk.index["upperarm_" + s]

        def posed(turn):
            rot = sk.rest_rot.copy()
            gpar = grot[0, sk.parent[u]]
            rot[u] = qmul(qinv(gpar), qmul(turn, grot[0, u]))
            hp.drive_hinges(sk, rot)
            return rot[j]
        assert _deg(qmul(qinv(sk.rest_rot[j]), posed(np.array([0, 0, 0, 1.0])))) < 1e-4
        line = qrot(grot[0, u], [0, 1.0, 0])
        turns[s] = _deg(qmul(qinv(sk.rest_rot[j]), posed(qaxis(np.cross(line, [0, 0, 1.0]), -90))))
        assert abs(turns[s] - 45) < 1e-4
        assert _deg(qmul(qinv(sk.rest_rot[j]), posed(qaxis(line, 60)))) < 1e-4
    assert abs(turns["l"] - turns["r"]) < 1e-4
