"""reach_table: the reach rule's reading (limit = rest standoff - leather) on synthetic plates, and the spaulder row
against P2 lead 11's measure (room.py: the four fight clips)."""
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reach_table as rt  # noqa: E402

MM = 0.001


def _flat(push_mm, standoff_mm=5.0):
    g = np.arange(-0.05, 0.0501, 0.002)
    V0 = np.array([[x, y, 0.0] for x in g for y in g])
    N0 = np.tile([0.0, 0.0, 1.0], (len(V0), 1))
    p = np.arange(-0.02, 0.0201, 0.004)
    X0 = np.array([[x, y, standoff_mm * MM] for x in p for y in p])
    frames = [(X0, 0), (X0 - [0, 0, push_mm * MM], 1), (X0 + [0, 0, 0.003], 2)]
    return rt.summary(rt.measure(X0, frames, V0, N0, lambda k: (V0, N0)))


def test_inside_its_room_reads_inside():
    s = _flat(2.0)                                   # limit 5 - 2.4 = 2.6: a 2 mm travel stays inside
    assert s["mark"] == "INSIDE" and s["points_past"] == 0 and s["samples_past"] == 0
    assert abs(s["limit_med"] - 2.6) < 1e-6 and abs(s["standoff_min"] - 5.0) < 1e-6


@pytest.mark.parametrize("push, want, mk", [(4.0, 1.4, "PAST <3"), (9.0, 6.4, "PAST >=3")])
def test_pushed_past_reads_the_amount(push, want, mk):
    s = _flat(push)
    assert abs(s["past"] - want) < 0.1 and s["mark"] == mk and s["at"] == 1 and s["frames_past"] == 1
    assert s["points_past"] == s["points"] and abs(s["travel"] - push) < 0.1


def test_a_stray_is_a_note_not_the_worst():
    g = np.arange(-0.05, 0.0501, 0.002)
    V0 = np.array([[x, y, 0.0] for x in g for y in g])
    N0 = np.tile([0.0, 0.0, 1.0], (len(V0), 1))
    p = np.arange(-0.02, 0.0201, 0.004)
    X0 = np.array([[x, y, 0.005] for x in p for y in p])
    X1 = X0 - [0, 0, 0.003]
    X1[0, 2] -= 0.010                                # one point 10 mm deeper than the plate
    s = rt.summary(rt.measure(X0, [(X1, 0)], V0, N0, lambda k: (V0, N0)))
    assert abs(s["past"] - 0.4) < 0.1 and s["mark"] == "PAST <3"
    assert abs(s["stray"]["past"] - 10.4) < 0.1 and s["stray"]["points"] == 1


def test_plates_are_the_one_blend_components():
    sq = np.array([[0, 0, 0], [0.1, 0, 0], [0.1, 0.1, 0], [0, 0.1, 0]], float)
    T = np.array([[0, 1, 2], [0, 2, 3]])
    J = np.zeros((4, 2), int)
    rigid = (sq, T, J + [3, 0], np.tile([1.0, 0.0], (4, 1)))
    cloth = (sq + [0.5, 0, 0], T, J + [3, 4], np.array([[1, 0], [0.5, 0.5], [0, 1], [0.5, 0.5]], float))
    pl = rt.plates([rigid, cloth], min_cm2=10)
    assert len(pl) == 1 and pl[0]["rule"] == {3: 1.0} and abs(pl[0]["cm2"] - 100) < 1e-6


def test_spaulder_row_is_lead_11s():
    """Lead 11 (room.py, four fight clips): the left cop 18.3 mm past (sword_heavy f13); the right 15.0 on the whole
    cop (daggers_heavy f0), 13.8 on its neck edge (cast_flick f6). Here 20.6 and 16.2, same frames and places: the built mesh with its rolled rim, not the design sheet on a grid (2.5 mm allowed)."""
    import gear_wear as gw
    if not os.path.isfile(os.path.join(gw.GEAR, "plate_spaulders_plain.gltf")):
        pytest.skip("no built spaulders")
    rows, _ = rt.run(gw.GEAR, ["plate_spaulders_plain"], "four", log=lambda *_: None)
    cop = {s["plate"].split()[3]: s for s in rows[::-1] if s["cm2"] == max(x["cm2"] for x in rows if x["plate"].split()[3] == s["plate"].split()[3])}
    assert abs(cop["l"]["past"] - 18.3) < 2.5 and cop["l"]["at"].startswith("sword_heavy")
    assert abs(cop["r"]["past"] - 15.0) < 2.5
