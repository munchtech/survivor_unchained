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

