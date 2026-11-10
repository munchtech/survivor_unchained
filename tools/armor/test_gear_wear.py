"""gear_wear's measuring core on a tiny synthetic: a two-bone cylinder (her skin) in a sleeve (a closed 2 mm shell),
one skin point poked out through the sleeve, posed through a bend (pytest, or python this file)."""
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gear_wear as gw  # noqa: E402

R, RI, RO, L = 0.050, 0.054, 0.056, 0.30
POKE_R = 0.0615          # the poked point's radius: 5.5 mm past the sleeve's outer face, 7.5 mm past its inner


def tube(r, n=48, m=31, inward=False):
    a = np.linspace(0, 2 * math.pi, n, endpoint=False)
    y = np.linspace(0, L, m)
    P = np.array([[r * math.cos(t), yy, r * math.sin(t)] for yy in y for t in a])
    T = []
    for i in range(m - 1):
        for k in range(n):
            p, q = i * n + k, i * n + (k + 1) % n
            T += [[p, p + n, q], [q, p + n, q + n]]      # (outward-facing)
    T = np.array(T)
    return P, (T[:, ::-1] if inward else T)


def weights(P):
    n = len(P)
    J = np.zeros((n, 8), np.int64)
    J[:, 1] = 1
    W = np.zeros((n, 8))
    w1 = np.clip((P[:, 1] - 0.12) / 0.06, 0, 1)
    W[:, 0], W[:, 1] = 1 - w1, w1
    return J, W


def scene():
    Ps, Ts = tube(R)
    poke = int(np.argmin(np.linalg.norm(Ps - [R, 0.06, 0], axis=1)))
    Ps[poke, [0, 2]] *= POKE_R / R
    Pi, Ti = tube(RI, inward=True)
    Po, To = tube(RO)
    Pp = np.vstack([Pi, Po])
    Tp = np.vstack([Ti, To + len(Pi)])
    P = np.vstack([Ps, Pp])
    T = np.vstack([Ts, Tp + len(Ps)])
    kind = np.r_[np.full(len(Ps), "skin"), np.full(len(Pp), "piece")]
    owner = np.r_[np.full(len(Ps), ""), np.full(len(Pp), "sleeve")]
    J, W = weights(P)
    sc = gw.Scene(P, T, kind, owner, J, W, {})
    sc.keys = gw.keys_of(Ps)
    return sc, poke


def frames():
    rest = np.stack([np.eye(4), np.eye(4)])
    rest[1, :3, 3] = [0, 0.15, 0]
    ibm = np.linalg.inv(rest)
    for f, deg in enumerate((0.0, 30.0, 60.0)):
        G = rest.copy()
        c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
        Rz = np.eye(4)
        Rz[:2, :2] = [[c, -s], [s, c]]
        G[1] = rest[1] @ Rz
        yield f, G @ ibm, {}


def run(confirm=True):
    sc, poke = scene()
    rows = [{"id": "sleeve", "slot": "top", "layer": 1, "covers": ["top"], "source": "sleeve", "tuck_path": "",
             "cover_path": ""}]
    ck = gw.Check(sc, rows, ["top"], grid=0.0025, confirm=confirm)
    ck.add_skin(["sleeve"])
    ck.run([("bend", frames)], log=lambda *_: None)
    out, worst = ck.report(["bend"], lambda pt: str(pt))
    return out, worst, poke


import pytest  # noqa: E402


@pytest.mark.parametrize("confirm", [True, False])
def test_one_known_poke(confirm):
    out, worst, poke = run(confirm)
    assert len(out) == 1
    e = out[0]
    assert e["kind"] == "skin" and e["B"] == "sleeve"
    assert e["out2_n"] == 1, e                                   # the poke alone shows
    assert abs(e["out_worst_mm"] - (POKE_R - RO) * 1000) < 0.3, e
    assert abs(e["worst_in_mm"] - (POKE_R - RI) * 1000) < 0.3, e
    assert e["per_clip"]["bend"]["region"] == str(poke)          # found at the poke
    assert len(worst) == 1 and worst[0]["clip"] == "bend"
    assert e["lost_share"] < 0.05                                # the bend kept the sleeve tracked


def test_blend_weights():
    J, W = gw.blend_weights(np.array([[3, 5]]), np.array([[0.5, 0.5]]), np.array([[5, 7]]), np.array([[1.0, 0.0]]),
                            np.array([0.5]), keep=8)
    d = {int(j): float(w) for j, w in zip(J[0], W[0]) if w > 0}
    assert d == {5: 0.75, 3: 0.25}


def test_look_rules():
    byid = {"a.top": {"id": "a.top", "slot": "top", "covers": ["top"], "source": "a"},
            "a.belt": {"id": "a.belt", "slot": "belt", "covers": ["belt"], "source": "a"},
            "a.skirt": {"id": "a.skirt", "slot": "skirt", "covers": ["skirt"], "source": "a"},
            "g": {"id": "g", "slot": "bottom", "covers": ["bottom", "belt", "skirt"], "source": "g"},
            "b.belt": {"id": "b.belt", "slot": "belt", "covers": ["belt"], "source": "b"}}
    look, dropped = gw.look_of(["a.top", "a.belt", "a.skirt"], "g", byid)
    assert look == {"bottom": "g", "top": "a.top"} and len(dropped) == 2
    look, dropped = gw.look_of(["a.top", "a.belt", "a.skirt"], "b.belt", byid)
    assert look == {"belt": "b.belt", "top": "a.top"}
    assert any("hangs" in why for _, why in dropped)


if __name__ == "__main__":
    test_one_known_poke(True)
    test_one_known_poke(False)
    test_blend_weights()
    test_look_rules()
    print("ok")


def test_signed_gap_forward_hit_past_reach():
    reach = 0.1
    t = np.array([[0.12, -0.005, np.nan]])
    facing = np.array([[-1.0, -1.0, 0.0]])
    g, _, _ = gw.wc.signed_gap(t, facing, reach)
    assert not (g < 0).any()
    g, _, _ = gw.wc.signed_gap(np.array([[np.nan, -0.005, np.nan]]), facing, reach)
    assert g[0] == -0.005                                        # no forward hit at all: unchanged


def _box(x0, x1, h, inward=False):
    c = np.array([[x, y, z] for x in (x0, x1) for y in (-h, h) for z in (-h, h)], float)
    q = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    tri = []
    for a, b, c_, d in q:
        tri += [[a, b, c_], [a, c_, d]]
    tri = np.array(tri)
    # outward winding: flip any face whose normal points at the centre
    ctr = c.mean(0)
    out = []
    for t in tri:
        n = np.cross(c[t[1]] - c[t[0]], c[t[2]] - c[t[0]])
        out.append(t[::-1] if (n * (c[t].mean(0) - ctr)).sum() < 0 else t)
    tri = np.array(out)
    if inward:
        tri = tri[:, ::-1]
    return c[tri]


def test_full_cast_toe_box():
    # a boot as a 2 mm shell: outer box, inner (cavity) box facing in. The toe box inner face is 30 mm ahead (past REACH).
    outer, inner = _box(-0.012, 0.032, 0.022), _box(-0.010, 0.030, 0.020, inward=True)
    V = np.concatenate([outer, inner])
    reach = gw.wc.REACH
    O, D = np.array([[0.0, 0.0, 0.0]]), np.array([[1.0, 0.0, 0.0]])
    back = np.concatenate([outer[(outer[:, :, 0] < 0).all(1)], inner[(inner[:, :, 0] < 0).all(1)]])   # K0 misses the far wall
    t, fa, _, _ = gw.wc.cast(O, D, back[None])
    g0, _, go0 = gw.wc.signed_gap(t, fa, reach)
    g, _, go, _, _ = gw.full_cast(O, D, V, reach)
    assert g0[0] < 0 or go0[0] < 0                                # the premise: the nearest-set cast alone reads through
    assert not (g[0] < 0) and not (go[0] < 0)                     # enclosed: inside, not through
    # truly past the outer face (outside the shell, 8 mm beyond its toe): reads through
    O2 = np.array([[0.040, 0.0, 0.0]])
    D2 = np.array([[1.0, 0.0, 0.0]])
    g2, _, go2, _, _ = gw.full_cast(O2, D2, V, reach)
    assert go2[0] < 0 or g2[0] < 0


def test_views_where_it_shows():
    """A clip's view by the words of its name; a view counts its own clips at its own depth; merge unions the parts."""
    assert gw.clip_view("idle_stalker") == "close" and gw.clip_view("run_stalker") == "play"   # not "talk" in stalker
    assert gw.clip_view("run_warden_town.json") == "close" and gw.clip_view("Jog_Fwd") == "play"
    assert gw.clip_view("sword_heavy") == "play" and gw.clip_view("talk_sella") == "close"
    pc = {"idle_warden": np.array([-0.003, -0.001, 0.0, 0.0]), "sword_fore": np.array([-0.003, 0.0, -0.007, 0.0]),
          "Jog_Fwd": np.array([0.0, 0.0, 0.0, -0.02])}
    vs = gw.view_sets(pc, 4)
    assert vs == {"close": [0], "close_ex": [0], "play": [2, 3], "play_ex": [2]}
    base = {"A": "skin", "B": "p", "kind": "skin", "_area": [1.0, 2.0, 4.0, 8.0], "_o2": [], "_i2": [], "lost_share": 0.0,
            "out2_mm2": 0.0, "out_worst_mm": None}
    a = dict(base, per_clip={"idle_warden": {}}, _vw=gw.view_sets({"idle_warden": pc["idle_warden"]}, 4), _od=[0])
    b = dict(base, per_clip={"sword_fore": {}, "Jog_Fwd": {}}, _od=[3],
             _vw=gw.view_sets({k: pc[k] for k in ("sword_fore", "Jog_Fwd")}, 4))
    m = gw.merge([{"pairs": [a]}, {"pairs": [b]}])[0]
    assert m["views"] == {"close": 1.0, "close_ex": 1.0, "play": 12.0, "play_ex": 4.0} and m["outd_mm2"] == 9.0


def test_frame_views_worst_single_frame():
    """frames: per view the worst single frame's area at each depth, with its clip; the broken clip left out of _ex;
    the merge of two parts' clips gives the same answer as one run."""
    row = lambda a2, a3, a6, f: {"frame_mm2": {"2": a2, "3": a3, "6": a6}, "frame_at": {"2": f, "3": f, "6": f}}
    pc = {"idle_warden": row(40.0, 10.0, 0.0, 4), "run_warden_town": row(55.0, 0.0, 0.0, 8),
          "sword_fore": row(300.0, 200.0, 90.0, 12), "Jog_Fwd": row(900.0, 800.0, 700.0, 2), "old_clip": {}}
    fv = gw.frame_views(pc)
    assert fv["close"]["2"] == {"mm2": 55.0, "clip": "run_warden_town", "frame": 8} and fv["close"]["6"]["mm2"] == 0.0
    assert fv["play"]["6"] == {"mm2": 700.0, "clip": "Jog_Fwd", "frame": 2}
    assert fv["play_ex"]["6"] == {"mm2": 90.0, "clip": "sword_fore", "frame": 12} and fv["play_ex"]["3"]["mm2"] == 200.0
    base = {"A": "skin", "B": "p", "kind": "skin", "_area": [1.0], "_o2": [], "_i2": [], "lost_share": 0.0,
            "out2_mm2": 0.0, "out_worst_mm": None}
    a = dict(base, per_clip={k: pc[k] for k in ("idle_warden", "sword_fore")},
             _samples={"pos": [[0, 0, 0]], "clips": {"idle_warden": [1.0], "sword_fore": [-7.0]}})
    b = dict(base, per_clip={k: pc[k] for k in ("run_warden_town", "Jog_Fwd")},
             _samples={"pos": [[0, 0, 0]], "clips": {"run_warden_town": [999.0], "Jog_Fwd": [-20.0]}})
    m = gw.merge([{"pairs": [a]}, {"pairs": [b]}])[0]
    assert m["frames"] == fv and sorted(m["_samples"]["clips"]) == ["Jog_Fwd", "idle_warden", "run_warden_town", "sword_fore"]



# ---- the sweep's domain (P2 lead 7): cloth is read for the skin under it, a plate for every point near it ----
def _press_scene(plate):
    """Her torso (the two-bone cylinder), an arm (a tube on bone 2) and the piece: the skinned sleeve (the arm 2 cm thick,
    44 mm beside it at rest), or a rigid plate (two open 5 mm grids 2 mm apart on bone 0, y 0.05..0.25, z -0.03..0.03,
    facing +x; the arm 1 cm thick, 50 mm off its z border at rest, its near side 2 mm above the plate's plane)."""
    Ps, Ts = tube(R)
    Pa, Ta = tube(0.01 if plate else 0.02, n=24)
    Pa += [0.068, 0, 0.09] if plate else [0.12, 0, 0]
    if plate:
        y, z = np.arange(0.05, 0.2501, 0.005), np.arange(-0.03, 0.0301, 0.005)
        G = np.array([[0.0, a, b] for a in y for b in z])
        nz = len(z)
        Tg = np.array([t for i in range(len(y) - 1) for k in range(nz - 1) for p in [i * nz + k]
                       for t in ([p, p + nz, p + 1], [p + 1, p + nz, p + nz + 1])])
        Pp = np.vstack([G + [RI, 0, 0], G + [RO, 0, 0]])
        Tp = np.vstack([Tg[:, ::-1], Tg + len(G)])
    else:
        Pi, Ti = tube(RI, inward=True)
        Po, To = tube(RO)
        Pp, Tp = np.vstack([Pi, Po]), np.vstack([Ti, To + len(Pi)])
    P = np.vstack([Ps, Pa, Pp])
    T = np.vstack([Ts, Ta + len(Ps), Tp + len(Ps) + len(Pa)])
    ns = len(Ps) + len(Pa)
    kind = np.r_[np.full(ns, "skin"), np.full(len(Pp), "piece")]
    owner = np.r_[np.full(ns, ""), np.full(len(Pp), "piece")]
    J, W = weights(P)
    arm = np.arange(len(Ps), ns)
    J[arm], W[arm] = 0, 0.0
    J[arm, 0], W[arm, 0] = 2, 1.0
    if plate:
        J[ns:], W[ns:] = 0, 0.0
        W[ns:, 0] = 1.0
    sc = gw.Scene(P, T, kind, owner, J, W, {})
    sc.keys = gw.keys_of(P[:ns])
    rows = [{"id": "piece", "slot": "top", "layer": 1, "covers": ["top"], "source": "piece", "tuck_path": "", "cover_path": ""}]
    ck = gw.Check(sc, rows, ["top"], grid=0.0025, confirm=True)
    ck.add_skin(["piece"])
    return sc, ck, arm


def _press(ck, slide=False):
    """The arm pressed 60 mm into the sleeve, or slid 90 mm over the plate from beside it: its far side stands 24 / 22 mm
    in front of the piece's outer face, normals running with it."""
    def frames():
        S = np.stack([np.eye(4)] * 3)
        S[2, 2 if slide else 0, 3] = -0.09 if slide else -0.06
        yield 0, S, {}
    ck.run([("press", frames)], log=lambda *_: None)
    return ck.report(["press"], lambda pt: str(pt))[0][0]


def test_bare_arm_beside_cloth_reads_zero():
    sc, ck, arm = _press_scene(plate=False)
    x = ck.tests[0]
    assert x["swSkin"].all() and len(x["pts"]) > x["nfp"]         # cloth; the arm's points are in the sweep's set
    assert not x["cover"][x["nfp"]:].any() and x["cover"][:x["nfp"]].all()
    assert _press(ck)["out2_mm2"] == 0.0                          # an arm on the garment is not skin through it
    sc, ck, arm = _press_scene(plate=False)
    ck.tests[0]["cover"][:] = True                                # (the premise: read against cloth, the arm counts)
    assert _press(ck)["out2_mm2"] > 100.0


def test_skin_through_cloth_in_its_cover_counts():
    sc, poke = scene()
    rows = [{"id": "sleeve", "slot": "top", "layer": 1, "covers": ["top"], "source": "sleeve", "tuck_path": "", "cover_path": ""}]
    ck = gw.Check(sc, rows, ["top"], grid=0.0025, confirm=True)
    ck.add_skin(["sleeve"])
    x = ck.tests[0]
    row = int(np.nonzero(x["pts"] == poke)[0][0])
    assert row < x["nfp"] and x["cover"][row] and x["swSkin"].all()
    sw = ck._sweep(x, sc.P0[x["pts"]], ck.N0[x["pts"]], sc.P0, np.arange(len(sc.P0)))    # (the sweep alone, at rest)
    assert abs(-sw[row] - (POKE_R - RO)) < 0.0005 and np.isfinite(sw).sum() == 1
    ck.run([("bend", frames)], log=lambda *_: None)
    e = ck.report(["bend"], lambda pt: str(pt))[0][0]
    assert e["split"]["out2"]["under_mm2"] == e["out2_mm2"] > 0 and e["split"]["out2"]["beside_mm2"] == 0.0
    assert e["per_clip"]["bend"]["under_mm2"] == e["per_clip"]["bend"]["out2_mm2"]


def test_skin_over_a_rigid_plate_from_beside_counts():
    sc, ck, arm = _press_scene(plate=True)
    x = ck.tests[0]
    assert not x["swSkin"].any() and x["swBE"].any()              # one bone blend: a plate; two open sheets
    e = _press(ck, slide=True)
    s = e["split"]["out2"]
    assert s["beside_mm2"] > 100.0 and s["under_mm2"] == 0.0 and e["out2_mm2"] == s["beside_mm2"]
    assert set(np.nonzero(x["min_out"] < -0.002)[0]) <= set(np.nonzero(np.isin(x["pts"], arm))[0])   # the arm's skin
    fv = e["frames"]["play_ex"]["2"]
    assert fv["beside_mm2"] == fv["mm2"] > 100.0 and fv["under_mm2"] == 0.0
    m = gw.merge([{"pairs": [e]}, {"pairs": [dict(e, per_clip={})]}])[0]          # (the split survives the merge)
    assert abs(m["split"]["out2"]["beside_mm2"] - s["beside_mm2"]) < 1.0 and m["split"]["out2"]["under_mm2"] == 0.0
    assert m["frames"]["play_ex"]["2"] == fv


def test_point_off_an_open_sheets_border_is_not_counted():
    sc, ck, arm = _press_scene(plate=True)
    x = ck.tests[0]
    # 21 mm in front of the outer sheet: one point 12 mm off its z border, its normal tilted back over the sheet (the
    # back cast lands on it), one over its middle
    O = np.array([[0.0773, 0.15, 0.042], [0.0773, 0.15, 0.0]])
    D = np.array([[0.866, 0.0, 0.5], [1.0, 0.0, 0.0]])
    at = np.arange(len(sc.P0))
    sw = ck._sweep(x, O, D, sc.P0, at)
    assert not np.isfinite(sw[0]) and abs(-sw[1] - 0.0213) < 0.0005
    x["swBE"][:], x["swBV"][:] = False, False                     # (the premise: without the border rule it counts)
    assert np.isfinite(ck._sweep(x, O, D, sc.P0, at)[0])


# ---- as worn: her springs under a top with a hold (gear_wear docstring AS WORN; the built body, skipped without it) --
def _worn_scene(piece="plate_top_plain"):
    import os
    import pytest
    if not os.path.isfile(os.path.join(gw.GEAR, "gear_index.json")):
        pytest.skip("no built gear folder")
    ix, rows = gw.load_rows(gw.GEAR)
    if piece not in {r["id"] for r in rows}:
        pytest.skip(f"{piece} is not built")
    body = os.path.join(gw.REPO, "godot", "art", "people", ix["body"])
    sc = gw.build_scene(body, rows, {piece, "ranger.belt"})
    order = __import__("json").load(open(os.path.join(gw.HERE, "slot_map.json"), encoding="utf-8"))["order"]
    return sc, gw.Check(sc, rows, order), body


def test_worn_top_rest_is_worn_rests_body_and_piece():
    """The rest a held top's skin test reads is gear_tuck's worn path (worn_rest.state / pose) to under 0.01 mm: her
    skin and the piece; and the worn rest is not the bind (the springs moved her)."""
    import os
    import gear_tuck as gt
    from scipy.spatial import cKDTree
    sc, ck, body = _worn_scene()
    row = ck.byid["plate_top_plain"]
    wn = ck.worn_of("plate_top_plain")
    assert wn is not None and wn.support > 0
    R = ck.rest_of(wn, gw.support_of(row))
    sk = gt.Skin(os.path.join(body, "body.glb"))
    st = gt.worn_state(sk, row)
    assert st is not None
    ref = sk.as_worn(st).P
    assert len(ref) == len(sc.isk)
    assert np.abs(R["P0"][sc.isk] - ref).max() < 1e-5
    assert np.abs(ref - sc.P0[sc.isk]).max() > 0.010                      # (a push-up: the breasts rest elsewhere)
    Pw = gt.piece_of(gw.GEAR, row, worn=st)[0]
    mine = R["P0"][sc.owner == "plate_top_plain"]
    assert len(Pw) == len(mine)
    assert cKDTree(Pw).query(mine)[0].max() < 1e-5 and cKDTree(mine).query(Pw)[0].max() < 1e-5
    ck.add_skin(["plate_top_plain"])
    assert ck.tests[0]["worn"] is wn


def test_worn_top_carries_the_springs_into_a_posed_frame():
    """A frame's springs sit at their worn equilibrium IN that pose: the rest carried is the worn rest; her whole
    skeleton turned about the up axis carries the worn rest turned with it; only the sprung bones' rows change."""
    sc, ck, _ = _worn_scene()
    wn = ck.worn_of("plate_top_plain")
    n = len(sc.ibm)
    eye = np.broadcast_to(np.eye(4), (n, 4, 4)).copy()
    assert np.abs(wn.carry(eye) - wn.S).max() < 1e-9
    moved = np.abs(wn.S - eye).reshape(n, -1).max(1) > 1e-9
    names = np.array(sc.poser.names)
    assert moved.any() and all("breast" in b for b in names[moved])
    a = math.radians(40)
    Y = np.array([[math.cos(a), 0, math.sin(a), 0.1], [0, 1, 0, 0.02], [-math.sin(a), 0, math.cos(a), -0.3], [0, 0, 0, 1]])
    S = np.broadcast_to(Y, (n, 4, 4)).copy()
    out = wn.carry(S)
    assert np.abs(out - Y @ wn.S).max() < 1e-9
    assert (out[~moved] == S[~moved]).all()
    # (a dump's frames take the WornTop; a caller's own frames are taken as they are)
    src = gw.dump_sources(sc, gw.clip_files("Jog_Fwd"), 1000)[0][1]
    f0, S0, _ = next(src())
    f1, S1, _ = next(src(wn))
    assert f0 == f1 and np.abs(S1[moved] - S0[moved]).max() > 1e-3 and (S1[~moved] == S0[~moved]).all()


def test_no_hold_rows_are_posed_as_before():
    """A row with no hold (and a scene with no poser) has no worn state: the bind's own rest, the frames untouched."""
    sc, ck, _ = _worn_scene()
    assert ck.worn_of("ranger.belt") is None
    assert ck.rest_of(None, (0.0, 0.0, 0.0)) is ck.bind and ck.bind["P0"] is sc.P0
    ck.add_skin(["ranger.belt"])
    assert ck.tests[0]["worn"] is None and not ck.rests
    assert gw.worn_top(scene()[0] if isinstance(scene(), tuple) else scene(), {"slot": "top", "hold": {"support": 1}}) is None


def _pair_scene(top):
    import os
    import pytest
    if not os.path.isfile(os.path.join(gw.GEAR, "gear_index.json")):
        pytest.skip("no built gear folder")
    ix, rows = gw.load_rows(gw.GEAR)
    have = {r["id"] for r in rows}
    ids = {top, "warden.greaves", "warden.boots"}
    if not ids <= have:
        pytest.skip("pieces not built")
    body = os.path.join(gw.REPO, "godot", "art", "people", ix["body"])
    sc = gw.build_scene(body, rows, ids)
    order = __import__("json").load(open(os.path.join(gw.HERE, "slot_map.json"), encoding="utf-8"))["order"]
    return sc, gw.Check(sc, rows, order)


def test_pair_without_the_top_is_posed_on_the_looks_worn_frames():
    """A look with a held top: a pair with no top in it takes the top's worn frames (the ones its skin test uses), and its
    row says so; the same pair in a look with no held top is posed bare."""
    sc, ck = _pair_scene("plate_top_plain")
    wn = ck.worn_of("plate_top_plain")
    assert wn is not None
    look = ["plate_top_plain", "warden.greaves", "warden.boots"]
    ck.add_pair("warden.greaves", "warden.boots", "control", look=look)
    assert len(ck.tests) == 1 and ck.tests[0]["worn"] is wn
    ck.tests.clear()
    ck.add_skin(["plate_top_plain"])
    skin_wn = ck.tests[0]["worn"]
    src = gw.dump_sources(sc, gw.clip_files("Jog_Fwd"), 1000)[0][1]
    _, Sa, _ = next(src(wn))
    _, Sb, _ = next(src(skin_wn))
    assert np.abs(Sa - Sb).max() < 1e-5            # (metres: 0.01 mm)
    # (the row's "worn_rest": True is written from the test's "worn", as the skin row's)


def test_pair_in_a_look_without_a_held_top_is_posed_as_before():
    """No held top in the look (or no look given): the pair's worn is None and its frames are the bare ones, bit-equal."""
    sc, ck = _pair_scene("plate_top_plain")
    ck.add_pair("warden.greaves", "warden.boots", "control", look=["warden.greaves", "warden.boots"])
    ck.add_pair("warden.greaves", "warden.boots", "control")
    assert len(ck.tests) == 1 and ck.tests[0]["worn"] is None
    assert ck.look_worn(["warden.greaves", "warden.boots"]) is None and ck.look_worn(None) is None
    src = gw.dump_sources(sc, gw.clip_files("Jog_Fwd"), 1000)[0][1]
    f0, S0, _ = next(src())
    f1, S1, _ = next(src(ck.look_worn(None)))
    assert f0 == f1 and np.array_equal(S0, S1)
