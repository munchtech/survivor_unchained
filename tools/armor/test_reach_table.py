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


def test_a_bent_plate_reads_per_vertex():
    """A plate whose part bends: its blend varies (rows lerp from the ride {3: 1} toward bone 4), so the rigid reading
    drops it; with bent it stays, its rule is the mode row (the ride), and it is posed per vertex from its own weights
    on its formed rest (X + F). Rigid plates read the same either way."""
    import gear_wear as gw
    x = np.arange(0.0, 0.1001, 0.02)
    strip = np.array([[a, b, 0.0] for a in x for b in (0.0, 0.1)])          # 12 points, 10 triangles, 100 cm2
    T = np.array([[2 * i, 2 * i + 2, 2 * i + 3] for i in range(5)] + [[2 * i, 2 * i + 3, 2 * i + 1] for i in range(5)])
    alpha = np.clip((strip[:, 0] - 0.05) / 0.05, 0, 1) * 0.5                 # 0 on the first half, to 0.5 at the end
    J = np.tile([3, 4], (len(strip), 1))
    W = np.c_[1 - alpha, alpha]
    F = np.tile([0.0, 0.0, 0.001], (len(strip), 1))                          # its carried shapes at the form: +1 mm z
    sq = np.array([[0, 0, 0], [0.1, 0, 0], [0.1, 0.1, 0], [0, 0.1, 0]], float) + [0.5, 0, 0]
    rigid = (sq, np.array([[0, 1, 2], [0, 2, 3]]), np.tile([3, 0], (4, 1)), np.tile([1.0, 0.0], (4, 1)))
    bent = (strip, T, J, W, F)
    assert [q["rule"] for q in rt.plates([rigid, bent[:4]])] == [{3: 1.0}]
    pl = rt.plates([rigid + (np.zeros((4, 3)),), bent], bent=True)
    b = [q for q in pl if q["bent"]]
    r = [q for q in pl if not q["bent"]]
    old = rt.plates([rigid, bent[:4]])[0]
    assert len(b) == 1 and len(r) == 1 and r[0]["rule"] == old["rule"] and np.array_equal(r[0]["X"], old["X"]) and np.array_equal(r[0]["T"], old["T"])
    q = b[0]
    assert q["rule"] == {3: 1.0} and np.allclose(q["Xf"], q["X"] + [0, 0, 0.001]) and q["J"].shape == (12, 5)
    S = np.broadcast_to(np.eye(4), (5, 4, 4)).copy()
    S[4, :3, 3] = [0, 0, -0.01]                                             # bone 4 sinks 10 mm, bone 3 stays
    P = gw.Scene.lbs(S, q["Xf"], q["J"], q["W"])
    a = np.clip((q["X"][:, 0] - 0.05) / 0.05, 0, 1) * 0.5
    assert np.allclose(P[:, 2], 0.001 - 0.01 * a)                            # each vertex by its own share
    assert rt.role_of({"b3": 1.0}, {"cop_l_rigid": {"b3": 1.0}}, tol=0.01) == "cop_l_rigid"


def test_spaulder_row_is_lead_11s():
    """Lead 11 (room.py, the four fight clips, 91 frames) read the cop 18.3 mm past on the left (sword_heavy f13), 15.0
    on the right (daggers_heavy f0); this table reads 20.6 / 16.2. Traced (10 Nov) on the same frames: ride (mesh
    weights = room.py's mean_ride, to 1e-4), skin (stored vs vertex normals, the tuck) and leather (2.4 both) add 0.0;
    it is all WHICH POINTS. Lead 11 sampled the cop's design inner face on a 4 mm x 27-column grid; this reads the built
    mesh's vertices. Left: the worst vertex (th 87, 2.6 mm in from the neck edge) is on the rolled rim's wall, 3.8 mm
    nearer her than the design face there: +3.2 (17.4 on the design face at that vertex -> 20.6 built); the grid's own
    peak sits elsewhere on the design face: -0.9 (18.3 -> 17.4); sum +2.3. Right: the worst is on the front lower edge (th 23, no
    rim, built within 0.1 mm of design), a peak between lead 11's grid points: +1.1 (15.0 -> 16.1 on the design face at
    that vertex), the built face there +0.1; sum +1.2 (the rim wall puts the right neck edge at 16.0, cast_flick f6,
    against lead 11's 13.8). Lead 11's grid under-reads; this table is the built plate's reading, held to 1 mm."""
    import gear_wear as gw
    if not os.path.isfile(os.path.join(gw.GEAR, "plate_spaulders_plain.gltf")):
        pytest.skip("no built spaulders")
    rows, _ = rt.run(gw.GEAR, ["plate_spaulders_plain"], "four", log=lambda *_: None, shapes=False)   # (plain LBS: lead 11's reading)
    cop = {s["plate"].split()[3]: s for s in rows if s["plate"].split()[2] == "cop"}
    # (10 Nov: the split cop was built and scrapped; the plain spaulders are round 4's one cop again, rigid: 20.6 / 16.2)
    assert abs(cop["l"]["past"] - 20.6) < 1.0 and cop["l"]["at"].startswith("sword_heavy") and cop["l"]["part"] == "cop_l_rigid"
    assert abs(cop["r"]["past"] - 16.2) < 1.0 and cop["r"]["at"].startswith("daggers_heavy") and cop["r"]["part"] == "cop_r_rigid"
