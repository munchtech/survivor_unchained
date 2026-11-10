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
    assert leg_skin.any() and d[leg_skin].max() < 1e-9


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
