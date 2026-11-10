"""The worn rest (tools/armor/worn_rest.py, rigid_roles.json slots.<slot>.worn_rest): a slot's rigid plates are made to
measure for her body as her support rests it under the piece, not for the bare bind."""
import os
import sys

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gear_fit as gf  # noqa: E402
import worn_rest  # noqa: E402

ROW = {"slot": "top", "hold": {"amount": 0.55, "squash": 0}}


@pytest.fixture(scope="module")
def bodies():
    return gf.load_bodies(gf.BIND_BODY)


def test_off_without_a_switch_a_hold_or_support(bodies):
    roles, body = gf.rigid_roles(), bodies["close"]
    assert worn_rest.worn(body, {"slot": "top"}, roles) is None                        # no hold
    assert worn_rest.worn(body, {"slot": "top", "hold": {"amount": 1}}, roles) is None   # support 0
    assert worn_rest.worn(body, dict(ROW, slot="pauldrons"), roles) is None             # a slot not switched
    off = {k: v for k, v in roles.items() if k != "worn_rest"}
    assert worn_rest.worn(body, ROW, off) is None                                       # no springs file named
    assert worn_rest.support_of(ROW)[0] == pytest.approx(1.0)                           # plate: push-up
    assert worn_rest.support_of({"hold": {"amount": 0.55, "support": 0.4, "fill": 0.1}}) == (0.4, (0.4, 0.4, 0.1))


def test_a_push_up_rests_her_breasts_higher_and_nothing_else(bodies):
    body = bodies["close"]
    wr = worn_rest.worn(body, ROW, gf.rigid_roles())
    for s in "lr":      # springs.json: sag 16 mm x her size, -0.25 of it at support 1 against the bind's full sag
        assert 0.018 < wr.eqs[f"breast_{s}"][1] < 0.023
    d = np.linalg.norm(wr.body.V - body.V, axis=1)
    assert d.max() > 0.012
    names = list(body.joint_names)
    legs = np.array([n.startswith(("thigh", "calf", "foot", "ball")) for n in names])
    leg_skin = (body.W * legs[body.J]).sum(1) > 0.99
    assert leg_skin.any() and d[leg_skin].max() < 1e-6      # (float32 binds)


def test_unpose_inverts_the_engines_pose(bodies):
    body = bodies["close"]
    wr = worn_rest.worn(body, ROW, gf.rigid_roles())
    names = list(body.joint_names)
    J = np.array([names.index("breast_l"), names.index("spine_04")] + [0] * 6)
    W = np.array([0.6, 0.4] + [0.0] * 6)
    rng = np.random.default_rng(3)
    X, d = rng.normal(size=(40, 3)) * 0.05 + [0.1, 1.38, 0.12], np.array([0.001, 0.004, -0.002])
    X0, _ = wr.unpose(X, np.tile([0.0, 0, 1], (40, 1)), J, W, {"form_support_lift": d})
    M = np.einsum("k,kij->ij", W, wr.S[J][:, :3, :])
    back = (X0 + wr.weights["form_support_lift"] * d) @ M[:, :3].T + M[:, 3]
    assert np.abs(back - X).max() < 1e-9


def test_plate_top_cups_clear_her_worn_skin_at_rest(bodies):
    """The built plate top: no rigid point under her skin as the engine rests her under it (the bare-bind fit left
    3,821 points under, 20.4 mm deep), and the plates keep their shape (a similarity inside the rigid fit's clamp)."""
    wr = worn_rest.worn(bodies["close"], ROW, gf.rigid_roles())
    bd = next(iter(gf.bindings(["plate_top_plain"])))
    assert worn_rest.worn(bodies["close"], bd.meta["row"], gf.rigid_roles()) is not None    # its row carries the hold
    ev = gf.eval_unit(bd, bodies, None)
    seen = 0
    for m in bd.meta["meshes"]:
        if m["tier"] != "close":
            continue
        o = ev[m["node"]]
        rg = (o["comp"] >= 0)[o["inv"]]
        if not rg.any():
            continue
        X = o["Xu"][o["inv"]].copy()
        for nm, k in wr.weights.items():
            if nm in o["shapes"]:
                X += k * o["shapes"][nm]
        c = gf.signed_clear(wr.body, X[rg])[0]      # (a top's plates ride the spine: stored = worn but for the shapes)
        assert c.min() > -0.0005, f"{m['node']}: {(c < 0).sum()} rigid points under her worn skin, deepest {-c.min() * 1000:.1f} mm"
        seen += int(rg.sum())
    assert seen > 5000


def _grid(x0, n=6, step=0.001):
    g = np.arange(n) * step
    return np.array([[x0 + a, b, 0.0] for a in g for b in g])


def test_join_clusters_weld_by_touch():
    """Components that touch are one group named by its largest member; a group with a bind-time leader is a plate,
    a group without one is a fitting."""
    import worn_rest as wr_
    X = np.vstack([_grid(0.0, 8), _grid(0.0085, 3), _grid(0.05, 3)])      # plate 0, a rivet touching it, a buckle apart
    comp = np.r_[np.zeros(64, int), np.ones(9, int), np.full(9, 2)]
    lead, plate = wr_.clusters(X, comp, np.array([0, 0, 0]))
    assert list(lead) == [0, 0, 2] and list(plate) == [True, True, False]


def test_join_field_and_bridge():
    """At a fitted plate a point takes the plate's move, far from it her skin's; a bridge between two plates takes
    each one's move at its own end."""
    import worn_rest as wr_
    A, B = _grid(0.0), _grid(0.1)
    jn = wr_.Joins(np.zeros((0, 3)), np.zeros((0, 3)))
    I = np.eye(3)
    jn.add(0, A, I, np.zeros(3), np.array([0.0, 0.02, 0.0]))            # plate 0 moves up 20 mm
    jn.add(1, B, I, np.zeros(3), np.array([0.0, -0.01, 0.0]))           # plate 1 moves down 10 mm
    P = np.array([[0.0, -0.001, 0.0], [0.05, 0.3, 0.0]])
    Y, G, near = jn.field(P, P.copy())
    assert G[0] == 1.0 and near[0] == 0 and abs(Y[0, 1] - (P[0, 1] + 0.02)) < 1e-9
    assert G[1] == 0.0 and near[1] == -1 and np.allclose(Y[1], P[1])
    mid = np.array([[0.007, 0.0, 0.0], [0.098, 0.0, 0.0]])
    Yb = jn.bridge(mid)
    assert Yb[0, 1] > 0.019 and Yb[1, 1] < -0.009
    assert jn.bridge(np.array([[0.05, 0.3, 0.0]])) is None


def test_unpose_each_lands():
    """A point stored by unpose_each under a blend lands on its target when posed (the engine's order)."""
    import worn_rest as wr_
    rng = np.random.default_rng(0)
    S = np.tile(np.eye(4), (3, 1, 1))
    S[1, :3, 3] = [0.0, 0.02, 0.01]
    w = wr_.Worn.__new__(wr_.Worn)
    w.S, w.weights = S, {"s": 0.5}
    Y = rng.normal(size=(5, 3))
    J = np.tile(np.array([0, 1, 0, 0, 0, 0, 0, 0]), (5, 1))
    Wt = np.tile(np.array([0.3, 0.7, 0, 0, 0, 0, 0, 0.0]), (5, 1))
    d = rng.normal(size=(5, 3)) * 0.01
    X0, _ = w.unpose_each(Y, J, Wt, {"s": d})
    assert np.allclose(wr_.pose(S, {"s": 0.5}, X0, J, Wt, {"s": d}), Y, atol=1e-12)
