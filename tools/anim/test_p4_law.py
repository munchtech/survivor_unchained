"""p4's law bones (LAW_BONES: the clavicles, B's girdle law's): run_post's rule drops a law bone's track that never
leaves rest, and the build / check line is a MISS for one that does (synthetic clips on the game's rig).

    python -m pytest -q tools/anim/test_p4_law.py
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import p4  # noqa: E402
from motion import quat as Q  # noqa: E402
from motion.rig import Rig  # noqa: E402

RIG = Rig(p4.RIG)


def clip(bones=p4.LAW_BONES + ("spine_05",), n=6):
    rot = {b: np.round(np.repeat(Q.from_mat(RIG.Lr0[RIG.index[b]])[None], n, 0), 7).tolist() for b in bones}
    return {"name": "t", "fps": 30, "loop": False, "frames": n, "bones": list(rot), "rot": rot, "pos": {}}


def keyed(c, b, f, deg):
    R = RIG.Lr0[RIG.index[b]] @ Q.to_mat(Q.from_axis_angle(np.array([0.0, 0.0, 1.0]), np.radians(deg)))
    c["rot"][b][f] = np.round(Q.from_mat(R), 7).tolist()
    return c


def test_law_bones_are_the_rigs_clavicles():
    assert set(p4.LAW_BONES) == {"clavicle_l", "clavicle_r"}
    assert all(b in RIG.index and b not in RIG.keyed for b in p4.LAW_BONES)


def test_rest_tracks_drop_and_the_build_line_names_them():
    c = clip()
    dropped, off = p4.MC.drop_rest(c, RIG, p4.LAW_BONES, p4.LAW_TOL_DEG)
    assert dropped == ["clavicle_l", "clavicle_r"] and off == {}
    assert list(c["rot"]) == ["spine_05"] == c["bones"]
    assert p4.law_lines(c, RIG, dropped) == ["  law tracks dropped: clavicle_l, clavicle_r"]
    assert p4.law_lines(c, RIG) == []                       # (check on a clean built clip: no track, nothing to flag)


def test_a_keyed_clavicle_is_a_miss():
    c = keyed(clip(), "clavicle_l", 3, 0.2)
    dropped, off = p4.MC.drop_rest(c, RIG, p4.LAW_BONES, p4.LAW_TOL_DEG)
    assert dropped == ["clavicle_r"] and list(off) == ["clavicle_l"]
    L = p4.law_lines(c, RIG, dropped)
    assert L[0] == "  law tracks dropped: clavicle_r"
    assert len(L) == 2 and "law bone clavicle_l: keyed, 0.20 deg off rest @f3 MISS" in L[1]


def test_a_stale_built_file_is_flagged_not_missed():
    L = p4.law_lines(clip(), RIG)                           # (a file built before the drop: both tracks at rest)
    assert len(L) == 2 and all("STALE" in x and "MISS" not in x for x in L)


def test_pose_measures_read_rest_where_the_track_is_absent():
    c = clip(bones=("spine_05",))
    pm = p4.pose_measures(RIG, *p4.MC.globals_of(c, RIG), 0, held=())
    assert pm["collar"]["clavicle_l_vs_rest_deg"] == 0.0 and pm["collar"]["clavicle_r_vs_rest_deg"] == 0.0
    k = keyed(clip(), "clavicle_l", 0, 2.0)
    pm = p4.pose_measures(RIG, *p4.MC.globals_of(k, RIG), 0, held=())
    assert pm["collar"]["clavicle_l_vs_rest_deg"] == 2.0 and pm["collar"]["clavicle_r_vs_rest_deg"] == 0.0
