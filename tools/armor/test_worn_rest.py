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
        rg = ((o["comp"] >= 0) & ~np.isin(o["lead"][np.maximum(o["comp"], 0)], o["bridges"]))[o["inv"]]   # (a bridge: the tuck's)
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


def test_joins_keep_the_piece_joined(bodies, tmp_path, monkeypatch):
    """The join law (slots.top.joins) on the plate top, as the engine poses the stored points in her worn rest: the
    stored points land on the fit, a strap's end stays on its cup, a buckle on its strap, and the gore (a bridge) stays
    between its cups and is not pushed proud of them. eval_unit's "Xbind" stays the authored points (on the bind body it
    was the stored array itself, which made an as-worn check read the cups' 42 mm move as 16)."""
    import copy
    import json
    from scipy.spatial import cKDTree
    roles = copy.deepcopy(gf.rigid_roles())
    roles["slots"]["top"]["joins"] = True
    path = tmp_path / "roles.json"
    path.write_text(json.dumps(roles), encoding="utf-8")
    monkeypatch.setenv("GEAR_ROLES", str(path))
    body = bodies["close"]
    bd = next(iter(gf.bindings(["plate_top_plain"])))
    wr = worn_rest.worn(body, bd.meta["row"], gf.rigid_roles())
    ev = gf.eval_unit(bd, bodies, None)
    ms = [m for m in bd.meta["meshes"] if m["tier"] == "close"]
    Xa = np.vstack([gf.eval_points(body, bd.z[f"tri{m['i']}"], bd.z[f"bw{m['i']}"], bd.z[f"off{m['i']}"])[0] for m in ms])
    assert np.abs(np.vstack([ev[m["node"]]["Xbind"] for m in ms]) - Xa).max() == 0
    Pw, comp = [], []
    for m in ms:
        o = ev[m["node"]]
        first = np.zeros(len(o["Xu"]), np.int64)
        first[o["inv"]] = np.arange(len(o["inv"]))
        Pw.append(worn_rest.pose(wr.S, wr.weights, o["Xu"], o["J"][first], o["W"][first], {k: v[first] for k, v in o["shapes"].items()}))
        comp.append(o["comp"])
        lead, bridges = o["lead"], o["bridges"]
    Pw, comp = np.vstack(Pw), np.concatenate(comp)
    rg = comp >= 0
    grp = np.where(rg, lead[np.maximum(comp, 0)], -1)
    assert len(bridges) == 1
    sizes = np.bincount(grp[rg])
    cups = [c for c in np.argsort(-sizes)[:2]]
    for c in cups:      # the cups moved to her worn breasts (about 42 mm at most), their rims with them
        assert 0.035 < np.linalg.norm(Pw[grp == c] - Xa[grp == c], axis=1).max() < 0.05
    # seams: a bendy point that touched a rigid one still does
    d0, j0 = cKDTree(Xa[rg]).query(Xa[~rg])
    seam = d0 < 0.002
    gap = np.linalg.norm(Pw[~rg][seam] - Pw[rg][j0[seam]], axis=1)
    at_cup = np.isin(grp[rg][j0[seam]], cups)
    assert at_cup.sum() > 30 and gap[at_cup].max() < 0.0025 and gap.max() < 0.006
    # the bridge: with its plates (its close pairs keep their distance), and resting ON her worn skin (hinge + lift:
    # what is left under is the tuck's, under 2 mm on a few points; unhinged it was 8 mm on 389 of 967)
    b = grp == bridges[0]
    for c in cups:
        d, j = cKDTree(Xa[grp == c]).query(Xa[b])
        k = d < 0.010
        dw = np.linalg.norm(Pw[b][k] - Pw[grp == c][j[k]], axis=1)
        assert k.sum() > 20 and np.abs(dw - d[k]).max() < 0.006
    cb_ = gf.signed_clear(wr.body, Pw[b])[0]
    assert cb_.min() > -0.002 and (cb_ < 0).mean() < 0.05


def test_bridge_lift_is_none_at_the_plate_and_bounded_by_strain():
    """The bridge rule's bound (worn_rest "THE JOINS"): a bridge point may lift JOIN "strain" of its distance to the
    plate it is joined to, nothing at the plate, and a bridge's own row never counts as the plate it reaches for."""
    import numpy as np
    import worn_rest as wr
    d = np.linspace(0.0, 0.05, 51)
    cap = wr._lift_cap(d)
    assert cap[0] == 0.0 and np.all(np.diff(cap) >= 0)
    assert np.all(np.diff(cap) / np.diff(d) <= wr.JOIN["strain"] + 1e-9)
    assert np.all(wr._lift_cap(np.array([-0.001])) == 0.0)
    plate = np.c_[np.linspace(0, 0.02, 30), np.zeros(30), np.zeros(30)]
    span = plate + np.array([0.0, 0.004, 0.0])
    jn = wr.Joins(np.zeros((0, 3)), np.zeros((0, 3)))
    jn.add(1, plate, np.eye(3), np.zeros(3), np.zeros(3))
    jn.add(2, span, np.eye(3), np.zeros(3), np.zeros(3))
    assert np.allclose(jn.reach(span, skip=2), 0.004, atol=1e-9)      # (its plate, not itself)
    assert np.allclose(jn.reach(span), 0.0, atol=1e-12)
    far = span + np.array([0.0, 0.5, 0.0])
    assert jn.reach(far, skip=2) is None                              # (linked to no plate: no bridge)


def _strap_on_a_plate():
    """A plate (a small grid at the origin) and a strap of bendy points running 0.2 m up from it; the plate moves
    25 mm up, her skin carries the strap's first 20 mm with it and nothing further along (a cup under a shoulder strap)."""
    g = np.linspace(-0.01, 0.01, 5)
    plate = np.array([[x, y, 0.0] for x in g for y in g])
    s = np.arange(0.0, 0.2, 0.002)
    strap = np.c_[np.zeros(len(s)), 0.01 + s, np.zeros(len(s))]
    up = np.array([0.0, 0.025, 0.0])
    skin = strap + np.clip(1 - s / 0.02, 0, 1)[:, None] * up * 0.6
    jn = worn_rest.Joins(strap, skin)
    jn.add(0, plate, np.eye(3), np.zeros(3), up)
    return jn, plate, strap, skin, s, up


def test_join_fade_is_measured_along_the_strap_and_its_ramp_is_straight():
    jn, plate, strap, skin, s, up = _strap_on_a_plate()
    J = worn_rest.JOIN
    # the mismatch is the whole 25 mm (past where her skin stops going with the plate), not the seam's 10 mm
    assert jn.rows[0]["gap"] == pytest.approx(0.025, abs=1e-4)
    assert jn.rows[0]["fade"] == pytest.approx(0.025 / J["strain"], abs=1e-3)
    Y, G, near = jn.field(strap, skin)
    assert G[0] == 1.0 and np.allclose(Y[0], strap[0] + up)             # (its end is on the plate)
    far = s > J["weld_m"] + jn.rows[0]["fade"]
    assert np.allclose(Y[far], skin[far]) and (G[far] == 0).all()        # (past the fade it is her skin's own)
    # taut: the strap's stretch is even along it (no step squeezed more than JOIN strain, no fold, no zigzag)
    step = np.diff(Y[:, 1]) / np.diff(strap[:, 1])
    free = (s[:-1] > 0.03) & (s[1:] < jn.rows[0]["fade"])               # (her skin's own move is over by 20 mm)
    assert np.ptp(step[free]) < 1e-6 and step[free].min() == pytest.approx(1 - J["strain"], abs=1e-6)
    assert step.min() > 0.5 and step.max() < 1 + 1e-6                    # (no fold anywhere, her skin's own squeeze included)


def test_join_fields_that_overlap_leave_a_seam_on_its_own_plate():
    jn, plate, strap, skin, s, up = _strap_on_a_plate()
    other = plate + [0.05, 0.0, 0.0]                                       # (a second plate 50 mm off, moving sideways)
    jn.add(1, other, np.eye(3), np.zeros(3), np.array([0.02, 0.0, 0.0]))
    Y, G, near = jn.field(strap, skin)
    assert near[0] == 0 and np.linalg.norm(Y[0] - (strap[0] + up)) < 1e-6
    assert np.abs(np.diff(Y - strap, axis=0)).max() < 0.002              # (and the blend between them has no jump)


def test_two_plate_link_is_a_bridge_one_plate_a_fitting():
    """THE JOINS: a small group linked to 2 fitted plates is a bridge whatever its size; linked to one, a fitting."""
    jn = worn_rest.Joins(np.zeros((0, 3)), np.zeros((0, 3)))
    g = np.stack(np.meshgrid(np.linspace(0, 0.05, 11), np.linspace(0, 0.05, 11), [0.0]), -1).reshape(-1, 3)
    I = (np.eye(3), np.zeros(3), np.zeros(3))
    jn.add(1, g - [0.08, 0, 0], *I)                    # (left plate: x -0.08..-0.03)
    jn.add(2, g + [0.03, 0, 0], *I)                    # (right plate: x 0.03..0.08)
    jn.add(3, g + [0.0, 0.2, 0], *I)                   # (a bridge fitted before: not a plate, never counted)
    bar = np.c_[np.linspace(-0.025, 0.025, 11), np.full(11, 0.02), np.zeros(11)]   # (5 mm off both plates)
    rivet = np.array([[-0.025, 0.01, 0.0], [-0.024, 0.01, 0.0], [-0.025, 0.011, 0.0]])
    assert jn.links(bar, only={1, 2}) == [1, 2]
    assert jn.is_bridge(bar, [1, 2])
    assert not jn.is_bridge(rivet, [1, 2])
    assert not jn.is_bridge(bar, [1])                  # (one plate only: a fitting)
    assert not jn.is_bridge(bar[:1] - [0, 0, 0.05], [1, 2])   # (linked to none)
