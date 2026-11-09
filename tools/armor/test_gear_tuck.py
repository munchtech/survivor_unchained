"""THE PLATE HIDES HER (gear_tuck + gear_seal): synthetic shapes, no build needed.

    python -m pytest tools/armor/test_gear_tuck.py -q
"""
import os
import sys

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
trimesh = pytest.importorskip("trimesh")
pytest.importorskip("trimesh.ray.ray_pyembree")
import gear_tuck as gt  # noqa: E402
import gear_seal as gs  # noqa: E402


def skin_of(m):
    """A gear_tuck.Skin over a trimesh (her stand-in): points, normals, welded graph."""
    from scipy.spatial import cKDTree
    sk = gt.Skin.__new__(gt.Skin)
    sk.P, sk.T = np.asarray(m.vertices, float), np.asarray(m.faces, np.int64)
    sk.N = np.asarray(m.vertex_normals, float)
    sk.gid, sk.ng = np.arange(len(sk.P)), len(sk.P)
    e = m.edges_unique
    sk.a, sk.b = np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]]
    sk.l = np.linalg.norm(sk.P[sk.a] - sk.P[sk.b], axis=1)
    sk.kd = cKDTree(sk.P)
    return sk


def shoulder():
    """Her: a ball of 0.1 m. The plate: a cap of 0.106 m over it, open below y = -0.03 (a pauldron's lower edge)."""
    body = trimesh.creation.icosphere(subdivisions=4, radius=0.1)
    cap = trimesh.creation.icosphere(subdivisions=4, radius=0.106)
    keep = cap.vertices[cap.faces].mean(1)[:, 1] > -0.03
    cap = trimesh.Trimesh(cap.vertices, cap.faces[keep], process=False)
    return skin_of(body), np.asarray(cap.vertices, float), np.asarray(cap.faces, np.int64)


def seen(sk, PB, TB, P=None):
    P = sk.P if P is None else P
    under = gt.under_rigid_of(sk, PB, TB, np.ones(len(TB), bool))
    idx = np.nonzero(under)[0]
    n = len(PB)
    Pall = np.vstack([PB, P])
    ts = sk.T
    tf = ts[~under[ts].any(1)]
    best, _ = gs.seen_of(P, sk.N, idx, gs.view_dirs(), Pall, np.vstack([TB, tf + n]), Pall,
                         np.vstack([TB, ts + n]), np.r_[np.ones(len(TB), bool), np.zeros(len(ts), bool)])
    return under, idx, best


def test_under_rigid_is_the_cap():
    sk, PB, TB = shoulder()
    under = gt.under_rigid_of(sk, PB, TB, np.ones(len(TB), bool))
    assert under[sk.P[:, 1] > 0.0].all() and not under[sk.P[:, 1] < -0.04].any()
    assert not gt.under_rigid_of(sk, PB, TB, np.zeros(len(TB), bool)).any()   # (a bending part hides nothing)


def test_hidden_under_the_cap_seen_at_its_edge():
    sk, PB, TB = shoulder()
    under, idx, best = seen(sk, PB, TB)
    y = sk.P[idx, 1]
    assert (best[y > 0.05] <= gs.VIEW_COS).all()          # (the crown: no camera reaches it)
    assert (best[y < -0.02] > gs.VIEW_COS).any()          # (by the lower edge: a low camera looks up under it)
    assert (best[best > gs.VIEW_COS] > 0).all() and y[best > gs.VIEW_COS].max() < 0.0


def test_through_the_plate_shows_the_plate():
    """Her skin standing past the plate is hidden: not drawn, the camera sees the plate where it was."""
    sk, PB, TB = shoulder()
    P = sk.P.copy()
    P *= 1 + 0.15 * np.clip((sk.P[:, 1] - 0.07) / 0.025, 0, 1)[:, None]   # (her crown swelling 9 mm out through the cap)
    top = np.nonzero(np.linalg.norm(P, axis=1) > 0.1065)[0]
    assert len(top) > 20
    _, idx, best = seen(sk, PB, TB, P)
    assert (best[np.isin(idx, top)] <= gs.VIEW_COS).all()


def test_plate_gone_keeps_a_rim_and_fills_no_hole():
    sk, PB, TB = shoulder()
    inside = sk.P[:, 1] > 0.0
    hole = np.linalg.norm(sk.P - [0, 0.1, 0], axis=1) < 0.012   # (a gap between lames: skin seen, ringed by hidden)
    inside &= ~hole
    g_fill = gt.gone_of(sk, inside)
    g = gt.gone_of(sk, inside, fill=False)
    assert g_fill[hole].all() and not g[hole].any()
    from scipy.sparse import csr_matrix
    from scipy.sparse.csgraph import dijkstra
    G = csr_matrix((sk.l, (sk.a, sk.b)), shape=(sk.ng, sk.ng))
    d = dijkstra(G, directed=False, indices=np.nonzero(~inside)[0], min_only=True)
    assert (d[g] >= gt.GONE_IN - 1e-9).all() and g[d > gt.GONE_IN + 0.01].all()


def test_hidden_set_stale_when_the_piece_moves(tmp_path):
    sk, PB, TB = shoulder()
    keys = np.round(sk.P[:5] * 1e5).astype(np.int64)
    gs.write_hidden(str(tmp_path), "p", keys, {"piece_hash": gs.piece_hash(PB), "_keys": keys, "_best": np.zeros(5)})
    h = gt.hidden_of(str(tmp_path), "p", sk, PB)
    assert h is not None and h.sum() == 5
    assert gt.hidden_of(str(tmp_path), "p", sk, PB + 0.001) is None
