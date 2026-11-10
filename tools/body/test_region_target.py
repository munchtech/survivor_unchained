"""region_target's zero points: the rest gives the rest, a rigid turn gives the turned rest, the border ring is the
published surface, the target is deterministic, and the two sides agree under the mirror (to the rest's own asymmetry:
her body is not mirror symmetric, up to 10 mm, so the sides' displacements are compared, not their points).

    python -m pytest tools/body/test_region_target.py
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import region_target as rt  # noqa: E402
from posers import make_poser  # noqa: E402


class Lite:
    """The poser and the driver without the audit's Body (no ray scene): enough for the target."""

    def __init__(self):
        self.rig = json.loads((rt.da.P1 / "rig.json").read_text())
        self.p = make_poser("lbs", str(rt.da.P1 / "body.glb"), self.rig)
        self.rd = self.p.driver


@pytest.fixture(scope="module")
def ctx():
    bd = Lite()
    return bd, rt.Model(bd.p)


def tgt(bd, md, G, s):
    Vp = rt.published(bd, G)[md.first]
    return md.target(G, Vp, s), Vp


def test_rest_is_rest(ctx):
    bd, md = ctx
    for s in "lr":
        X, _ = tgt(bd, md, bd.p.rest, s)
        assert np.abs(X - md.V0[md.S[s]["ids"]]).max() < 1e-6


def test_rigid_turn(ctx):
    bd, md = ctx
    D = np.eye(4)
    D[:3, :3] = rt.Rot.from_rotvec([0.3, -0.7, 0.4]).as_matrix()
    D[:3, 3] = [0.2, -0.1, 0.5]
    X, _ = tgt(bd, md, D @ bd.p.rest, "l")
    assert np.abs(X - (md.V0[md.S["l"]["ids"]] @ D[:3, :3].T + D[:3, 3])).max() < 1e-6


def test_border_ring_and_determinism(ctx):
    bd, md = ctx
    G = rt.extreme_G(bd, "abd90_int60")[0]
    X, Vp = tgt(bd, md, G, "l")
    ring = md.beta == 0
    assert ring.sum() > 100 and md.depth[ring].max() >= 3
    assert np.abs(X[ring] - Vp[md.S["l"]["ids"]][ring]).max() == 0
    X2, _ = tgt(bd, md, G, "l")
    assert hashlib.sha256(X.tobytes()).hexdigest() == hashlib.sha256(X2.tobytes()).hexdigest()


def test_mirror_sides_agree(ctx):
    bd, md = ctx
    G = rt.extreme_G(bd, "abd90_int60")[0]
    Gm = md.mirror_G(G)
    assert np.abs(md.mirror_G(Gm) - G).max() < 1e-9
    Xl, _ = tgt(bd, md, G, "l")
    Xr, _ = tgt(bd, md, Gm, "r")
    dl = Xl - md.V0[md.S["l"]["ids"]]
    dr = (Xr - md.V0[md.S["r"]["ids"]]) * [-1, 1, 1]
    assert np.percentile(np.linalg.norm(dl - dr, axis=1), 95) < 0.004      # the rest's asymmetry carried by the pose
