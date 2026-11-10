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
