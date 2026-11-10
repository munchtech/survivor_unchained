"""region_shape's own checks (python -m pytest tools/body/test_region_shape.py -x -q). Silhouette: not built yet."""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import region_shape as rs  # noqa: E402


@pytest.fixture(scope="module")
def cx():
    return rs.Ctx()


def test_bands_disjoint_and_filled(cx):
    ids = np.concatenate([cx.bands[b]["l"] for b in rs.BANDS])
    assert len(ids) == len(np.unique(ids))
    assert all(len(cx.bands[b]["l"]) > 20 for b in rs.BANDS)


def test_rest_is_zero(cx):
    for s in "lr":
        pose = next(cx.poses([f"rest:{s}"]))
        for b, v in cx.shift("pub", pose).items():
            assert np.nanmax(np.abs(v)) < 1e-6, (b, s)


def test_a_is_zero(cx):
    for nm in ("x:abd150", "cast_bolt@0:r"):
        pose = next(cx.poses([nm]))
        for b, v in cx.shift("a", pose).items():
            assert np.nanpercentile(np.abs(v), 99) < 2e-5, (nm, b, np.nanmax(np.abs(v)))


def test_edges_rest_is_one():
    import carried_target as ct
    h = ct.Her(verbose=False)
    for s in "lr":
        pr = rs.edge_probe(h, s)
        r = rs.edge_rows(h, pr, h.bd.G0, s)
        for k, tol in (("c", 1e-6), ("a", 1e-6), ("p", 1e-3), ("t", 1e-3)):    # the published surface at rest sits a few
            assert np.abs(r[k] - 1).max() < tol, (s, k, np.abs(r[k] - 1).max())    # um off the rest points (4e-4 of an edge)
        z = np.zeros(len(r["t"]), bool)
        assert (rs.classify_edges(r["t"], r["p"], r["c"], r["a"], z, z + 1.0, z + 1.0, z, 2.5) == -1).all()


def test_edge_classes_partition():
    rng = np.random.default_rng(3)
    n = 4000
    t, p, c, a = (rng.uniform(0.5, 6, n) for _ in range(4))
    inp, bridge = rng.random(n) < 0.1, rng.random(n) < 0.2
    b = rng.choice([0, 0.3, 1.0], (2, n))
    lab = rs.classify_edges(t, p, c, a, inp, b.min(0), b.max(0), bridge, 2.5)
    assert ((lab >= 0) == (t > 2.5)).all() and lab.max() < len(rs.EDGE_CLASSES)
    assert set(lab[lab >= 0]) == set(range(len(rs.EDGE_CLASSES)))          # every class is reached, each edge has one
    assert (lab[inp & (t > 2.5)] == 0).all() and (lab[~inp & (b.max(0) <= 0) & (t > 2.5)] == 1).all()


def test_offset_reads(cx):
    pose = next(cx.poses(["rest"]))
    B = cx.B
    N = B._normals(B.V0)
    for b in rs.BANDS:
        V = B.V0.copy()
        pt = np.zeros(cx.md.n, bool)
        pt[cx.bands[b]["l"]] = True
        g = np.nonzero(pt[cx.md.src])[0]
        V[g] -= 0.005 * N[g]
        out = cx.shift("pub", pose, V)
        for k, v in out.items():
            want = -0.005 if k == b else 0.0
            assert abs(np.nanmedian(v) - want) < 3e-4, (b, k, np.nanmedian(v))
