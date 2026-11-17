"""Her hip hinges (tools/anim/helpers.py SPEC "hinges"): extend() adds them at their pivot with no global rest turn,
drive_hinges turns `amount` of the thigh's swing and none of its roll, pin_shipped.with_hinges binds them in a piece as
the skeleton has them, and the game's rig_helpers.json carries the spec."""
import json
import math
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


def test_pauldron_hinge_turns_its_amount_of_the_arms_swing_none_of_its_roll(sk):
    """pauldron_hinge_{s} (armor-D 16 Nov): at rest it equals its rest; a pure 90 deg arm raise turns it 90 x its
    amount (.8 since pauldron-2 r4); a pure roll leaves it unturned; the sides mirror."""
    hg = next(h for h in hp.SPEC["hinges"] if h["name"].startswith("pauldron_hinge"))
    assert hg["parent"] == "clavicle_{s}" and hg["bone"] == "upperarm_{s}" and 0 < hg["amount"] <= 1
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
        assert abs(turns[s] - 90 * hg["amount"]) < 1e-4
        assert _deg(qmul(qinv(sk.rest_rot[j]), posed(qaxis(line, 60)))) < 1e-4
    assert abs(turns["l"] - turns["r"]) < 1e-4


def _tasset(name, **extra):
    return {**next(t for t in hp.SPEC["tassets"] if t["name"] == name), **extra}


def _driven(sk, tg, **deg):
    """The tasset bone `tg` driven with thighs turned: forward `l=`/`r=` degrees, spread `al=`/`ar=` (global, her rest
    axes: forward about -X, spread about her forward axis); returns its turn from rest."""
    grot, _ = sk.rest_globals()
    rot = sk.rest_rot.copy()
    for s in "lr":
        f, a = deg.get(s, 0), deg.get("a" + s, 0)
        if not f and not a:
            continue
        t = sk.index["thigh_" + s]
        g = qmul(qaxis([0, 0, 1.0 if s == "l" else -1.0], a), qaxis([-1.0, 0, 0], f))
        rot[t] = qmul(qinv(grot[0, sk.parent[t]]), qmul(g, grot[0, t]))
    j = sk.index[tg["name"]]
    sw, sp = hp.tasset_angles(sk, rot, tg)
    rot[j] = hp.qnorm(qmul(sk.rest_rot[j], hp.tasset_q(*hp.tasset_pose(tg, sw, sp))))
    return qmul(qinv(sk.rest_rot[j]), rot[j])


def test_hip_tassets_are_one_thigh_hinges_at_their_pivots(sk):
    grot, gpos = sk.rest_globals()
    for s in "lr":
        tg = _tasset("hiptasset_hinge_" + s)
        assert tg["thighs"] == ["thigh_" + s] and tg["amount"] == 1.4 and tg["soft"] == 16.0
        assert tg["roll"] == 0.95 and tg["roll_max"] == 25.0
        j = sk.index[tg["name"]]
        assert sk.names[sk.parent[j]] == "pelvis" and _deg(grot[0, j]) < 1e-6
        assert np.abs(gpos[0, j] - np.asarray(tg["pivot"], float)).max() < 1e-9
        # its pivot is on the belt (17 Nov), 0.115 out, 1.115 up, 0.067 forward; "at_rest" is thigh_{s}'s rest head
        assert np.abs(gpos[0, j] - np.array([0.115 if s == "l" else -0.115, 1.115, 0.067])).max() < 1e-9
        assert np.abs(np.asarray(tg["at_rest"]) - gpos[0, sk.index["thigh_" + s]]).max() < 1e-5
        assert _deg(_driven(sk, tg)) < 1e-6


def test_hip_tasset_turns_with_its_own_forward_swing_and_spread(sk):
    for s in "lr":
        tg = _tasset("hiptasset_hinge_" + s)
        o = "r" if s == "l" else "l"
        want = 1.4 * (45 - 4 - 8)
        assert abs(_deg(_driven(sk, tg, **{s: 45})) - want) < 1e-3
        assert _deg(_driven(sk, tg, **{o: 45})) < 1e-6  # the other thigh leaves it be
        assert _deg(_driven(sk, tg, **{o: 45, "a" + o: 25})) < 1e-6
        sg = 1 if s == "l" else -1
        tip = lambda q: qrot(q, [0, -1.0, 0])
        for a in (25, -25):  # spread out / crossing: the bottom goes with the thigh, 25 tanh(0.95 a / 25)
            q = _driven(sk, tg, **{"a" + s: a})
            assert abs(_deg(q) - 25 * math.tanh(0.95 * abs(a) / 25)) < 1e-3
            assert tip(q)[0] * sg * a > 0.1 * abs(a) / 25
        assert _deg(_driven(sk, {**tg, "roll": 0.0}, **{"a" + s: 25})) < 1e-6  # roll 0: pitch only, as before
        rot = sk.rest_rot.copy()  # a twist about the thigh's own line
        t, grot = sk.index["thigh_" + s], sk.rest_globals()[0]
        line = qrot(grot[0, t], [0, 1.0, 0])
        rot[t] = qmul(qinv(grot[0, sk.parent[t]]), qmul(qaxis(line, 60), grot[0, t]))
        sw, sp = hp.tasset_angles(sk, rot, tg)
        assert abs(sw[0]) < 1e-6 and hp.tasset_turn(tg, *sw) == 0
    a = _driven(sk, _tasset("hiptasset_hinge_l"), l=45)
    b = _driven(sk, _tasset("hiptasset_hinge_r"), r=45)
    assert abs(_deg(a) - _deg(b)) < 1e-4 and np.abs(a[:3] - b[:3]).max() < 1e-6  # mirrored: the same turn about x


def test_tasset_roll_zero_is_the_old_v_and_roll_turns_it_away_from_the_crossing_thigh(sk):
    tg0 = {**_tasset("tasset_hinge"), "roll": 0.0}  # (the SPEC ships roll 1.3 since hipv-2 r3: 0 here is the old V)
    base = {k: v for k, v in tg0.items() if k != "roll"}  # the spec before the field existed
    for kw in ({"l": 40, "r": 10, "al": -12, "ar": 3}, {"l": 5, "al": -15}, {"r": 30, "ar": -9}):
        assert np.abs(_driven(sk, tg0, **kw) - _driven(sk, base, **kw)).max() == 0
    assert _deg(_driven(sk, tg0, al=-20)) < 1e-4
    on = {**tg0, "roll": 1.3}
    tip = lambda q: qrot(q, [0, -1.0, 0])
    # her left thigh 13 deg across: the V's tip goes to her right (-x), the right thigh across: to her left
    assert tip(_driven(sk, on, al=-13))[0] < -0.1
    assert tip(_driven(sk, on, ar=-13))[0] > 0.1
    assert abs(tip(_driven(sk, on, al=-13))[0] + tip(_driven(sk, on, ar=-13))[0]) < 1e-6
    assert abs(_deg(_driven(sk, on, al=-13)) - hp.tasset_roll(on, -13, 0)) < 1e-3
    assert _deg(_driven(sk, on, al=1.0)) < 1e-6  # spread out: none
    assert 9 < hp.tasset_roll(on, -13.1, 1.0) < 10  # sword_heavy f8
    assert hp.tasset_roll({**on, "roll_max": 8.0, "roll": 3.0, "roll_from": 0.0}, -90, 0) <= 8.0
