"""bends._neck_ring: the open-boundary ring (her), the narrowest-slice fallback (a closed mesh), the error (python tools/body/test_bends_ring.py)."""
import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import bends  # noqa: E402

N = 48


def lathe(profile, closed_top):
    """Surface of revolution about Y from (r, y) rows; a row with r == 0 is one vertex (a pole)."""
    P, rows = [], []
    for r, y in profile:
        if r == 0:
            rows.append([len(P)])
            P.append([0.0, y, 0.0])
        else:
            rows.append(list(range(len(P), len(P) + N)))
            P.extend([r * math.cos(2 * math.pi * k / N), y, r * math.sin(2 * math.pi * k / N)] for k in range(N))
    T = []
    for a, b in zip(rows[:-1], rows[1:]):
        for k in range(N):
            k2 = (k + 1) % N
            if len(a) == 1:
                T.append([a[0], b[k], b[k2]])
            elif len(b) == 1:
                T.append([a[k], b[0], a[k2]])
            else:
                T.append([a[k], b[k], b[k2]])
                T.append([a[k], b[k2], a[k2]])
    return np.array(P), np.array(T)


class StandIn:
    """Exactly what _neck_ring reads: piece, P0, T, rest, index."""
    def __init__(self, P, T, sh=1.40):
        self.P0, self.T = P, T
        self.piece = np.array(["body"] * len(P))
        self.index = {"upperarm_l": 0, "upperarm_r": 1}
        self.rest = np.tile(np.eye(4), (2, 1, 1))
        self.rest[0][1, 3] = self.rest[1][1, 3] = sh
        self.rest[0][0, 3], self.rest[1][0, 3] = 0.18, -0.18


def torso():
    return [(0.0, 0.0), (0.20, 0.0), (0.20, 1.40), (0.05, 1.40)]


def neck(top):
    return [(0.05, y) for y in np.arange(1.405, top + 1e-9, 0.005)]


def head():
    a = np.linspace(math.pi, 0, 17)[1:-1]
    sph = [(0.10 * math.sin(t), 1.62 + 0.10 * math.cos(t)) for t in a]
    return [(r, y) for r, y in sph if r > 0.05 and y > 1.52] + [(0.0, 1.72)]


def test_closed_mesh_takes_the_narrowest_slice():
    P, T = lathe(torso() + neck(1.52) + head(), True)
    p = StandIn(P, T)
    ring = bends._neck_ring(p)
    assert len(ring) > 0 and p._neck_ring_kind == "narrowest"
    assert (P[ring, 1] > 1.40).all() and (P[ring, 1] < 1.52).all(), P[ring, 1]
    assert (np.abs(P[ring, 0]) <= 0.051).all()


def test_open_neck_takes_the_rim():
    P, T = lathe(torso() + neck(1.52), False)
    p = StandIn(P, T)
    ring = bends._neck_ring(p)
    assert p._neck_ring_kind == "boundary"
    assert len(ring) == N and np.allclose(P[ring, 1], 1.52)


def test_nothing_above_the_shoulders_raises():
    P, T = lathe(torso(), True)
    try:
        bends._neck_ring(StandIn(P, T))
    except ValueError as e:
        assert "no neck ring" in str(e)
    else:
        raise AssertionError("no ValueError")


def _old_ring(poser):
    body = np.where(poser.piece == "body")[0]
    _, inv = np.unique(np.round(poser.P0[body], 6), axis=0, return_inverse=True)
    inv = inv.ravel()
    loc = np.full(len(poser.piece), -1)
    loc[body] = np.arange(len(body))
    Tw = inv[loc[poser.T[(poser.piece[poser.T] == "body").all(1)]]]
    E = np.sort(np.concatenate([Tw[:, [0, 1]], Tw[:, [1, 2]], Tw[:, [2, 0]]]), 1)
    u, c = np.unique(E, axis=0, return_counts=True)
    idx = body[np.isin(inv, np.unique(u[c == 1].ravel()))]
    sh = 0.5 * (poser.rest[poser.index["upperarm_l"]][1, 3] + poser.rest[poser.index["upperarm_r"]][1, 3])
    return idx[poser.P0[idx, 1] > sh]


def test_her_ring_is_the_old_ring():
    glb = HERE.parents[1] / "godot" / "art" / "people" / "heroine.glb"
    if not glb.exists():
        print("skip: no heroine.glb")
        return
    from posers import make_poser
    poser = make_poser("game", str(glb), {})
    old = _old_ring(poser)
    new = bends._neck_ring(poser)
    assert len(old) > 0 and poser._neck_ring_kind == "boundary" and np.array_equal(old, new)


if __name__ == "__main__":
    for k, f in list(globals().items()):
        if k.startswith("test_"):
            f()
            print("ok", k)
