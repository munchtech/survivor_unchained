"""deform_audit's zero points: the rest pose and a rigid whole-body move score 0 on every metric, on B and on A (the
game poser), slide_bone reads a known offset, and the layers leave the rest pose alone.

    python -m pytest tools/body/test_deform_audit.py
"""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import deform_audit as da  # noqa: E402
from bends import rot  # noqa: E402

TOL = 1e-3      # the rows are rounded to 3 places: % / deg / mm


@pytest.fixture(scope="module", params=["B", "A"])
def bd(request):
    b = da.body(request.param)
    b.set_layer("full")
    return b


def worst(out):
    return max((abs(x), r, da.MET[i]) for r, row in out.items() for i, x in enumerate(row))


def test_loads_with_every_joint(bd):
    for joint, regs in da.JOINTS.items():
        for rg in regs:
            for s in "lr":
                name = rg.replace("{s}", s)
                assert name in bd.reg and len(bd.reg[name]["tris"]) > 20, name
    for s in "lr":
        assert "ref" in bd.reg[f"shoulder_{s}.deltoid"] and "ref" in bd.reg[f"clav_{s}"]


def test_rest_scores_zero(bd):
    V, G = bd.pose_turns([])
    out, _ = bd.measure(V, G)
    assert all(len(row) == len(da.MET) for row in out.values())
    assert worst(out)[0] <= TOL, worst(out)


def test_layers_agree_at_rest(bd):
    try:
        for layer in bd.layers:
            bd.set_layer(layer)
            V, G = bd.pose_turns([])
            assert np.abs(V - bd.V0).max() < 1e-6, layer
            assert worst(bd.measure(V, G)[0])[0] <= TOL, layer
    finally:
        bd.set_layer("full")


def test_rigid_turn_scores_zero(bd):
    M = np.eye(4)
    M[:3, :3] = rot(np.array([0.3, 0.9, -0.2]) / np.linalg.norm([0.3, 0.9, -0.2]), 71.0) @ rot(np.array([1.0, 0, 0]), -33.0)
    M[:3, 3] = [0.4, -0.25, 1.3]
    V = bd.V0 @ M[:3, :3].T + M[:3, 3]
    out, _ = bd.measure(V, M @ bd.G0)
    assert worst(out)[0] <= TOL, worst(out)


def test_slide_bone_reads_an_offset(bd):
    r = bd.reg["shoulder_l.deltoid"]
    V = bd.V0.copy()
    V[r["v"]] += np.array([0.0, 0.005, 0.0])
    out, _ = bd.measure(V, bd.G0, inside=False)
    i = da.MET.index("sb50")
    assert out["shoulder_l.deltoid"][i:i + 3] == pytest.approx([5.0, 5.0, 5.0], abs=1e-2)
    assert out["knee_l"][i:i + 3] == [0, 0, 0]


def test_a_bend_is_seen(bd):
    """The other way round: a real bend must not score 0 (the knee at 90 on either body stretches its skin)."""
    row = next(r for r in da.rom_list(bd) if r[0] == "knee90" and r[2] == "l")
    V, G = da.rom_pose(bd, row)
    out, _ = bd.measure(V, G, inside=False)
    assert out["knee_l"][da.MET.index("st99")] > 10
    assert out["knee_r"][da.MET.index("st99")] < 1


def test_clavicle_law_and_frozen():
    """A p4-style clip whose clavicle track sits at rest is posed with a moving clavicle under "law" (the game) and a
    still one under "frozen"; a clip that really keys the clavicle stays as keyed under both; a ROM pose keys nothing."""
    from scipy.spatial.transform import Rotation
    b = da.body("B")
    b.set_layer("full")
    p, gd = b.p, b.rig["girdle"]
    cl, ua = (p.index[gd[k].replace("{s}", "l")] for k in ("clavicle", "arm"))
    quat = lambda R: Rotation.from_matrix(R).as_quat().tolist()
    Rp = p.rest[p.parent[ua]][:3, :3]
    up = [quat(Rp.T @ rot(b.frame.front, a) @ p.rest[ua][:3, :3]) for a in (100.0, -100.0)]   # one of the two lifts the arm
    still = [quat(b.rl[cl][:3, :3])] * 2
    keyed = [quat(b.rl[cl][:3, :3] @ rot(np.array([0.0, 0, 1]), 5.0))] * 2
    deg = lambda G: float(da._turn_deg(G[None, cl, :3, :3], p.rest[cl][:3, :3])[0])
    turn = lambda d: max(deg(G) for _, _, G in b.clip_frames(d, 1))
    clip = lambda c: {"bones": [p.names[cl], p.names[ua]], "frames": 2, "rot": {p.names[cl]: c, p.names[ua]: up}}
    row = next(r for r in da.rom_list(b) if r[0] == "sh_abd135" and r[2] == "l")
    try:
        b.clavicle = "law"
        assert turn(clip(still)) > 3.0
        assert turn(clip(keyed)) == pytest.approx(5.0, abs=1e-3)
        assert deg(da.rom_pose(b, row)[1]) > 3.0
        b.clavicle = "frozen"
        assert turn(clip(still)) < 1e-3
        assert turn(clip(keyed)) == pytest.approx(5.0, abs=1e-3)
        assert deg(da.rom_pose(b, row)[1]) < 1e-3
    finally:
        b.clavicle = "frozen"
