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
