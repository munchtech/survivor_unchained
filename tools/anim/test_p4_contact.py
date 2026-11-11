"""p4_contact: the blade's crossing, the tip's peak and the blend rule on synthetic cuts whose answers are closed form.
Every bone rests but hand_r, which turns about a fixed world axis through the hand joint with a cosine ease:
theta(t) = A * (1 - cos(pi * u)) / 2, u = (t - T0) / D. The tip's speed peaks at u = 0.5; the target sits on the blade's
0.75 point at theta = F * A (plus an offset along the axis), so the outer half is nearest it at u = acos(1 - 2F) / pi.

    python -m pytest -q tools/anim/test_p4_contact.py
"""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import p4  # noqa: E402
import p4_contact as PC  # noqa: E402
from motion import quat as Q  # noqa: E402
from motion.rig import Rig  # noqa: E402

T0, D, A, F = 0.1, 0.2, np.radians(150), 0.7
U = float(np.arccos(1 - 2 * F) / np.pi)
CROSS, PEAK = T0 + D * U, T0 + D * 0.5
RIGS = {}


def rig():
    return RIGS.setdefault("r", Rig(p4.RIG))


def rot(axis, th):
    return Q.to_mat(Q.from_axis_angle(np.array(axis, float), th))


def cut(axis, e0, fps=60.0, frames=42, hold=None):
    """(clip, world point of the blade's 0.75 at the crossing, the tip's radius about the axis). axis: the world axis
    the hand turns about; e0: the blade's direction at theta 0 (square to the axis). hold: every key at that angle."""
    r, pc = rig(), p4.pieces()["blade"]
    h = r.index["hand_r"]
    base = Q.arc(pc["dir"], e0)
    Gp = r.R0[r.parent[h]]
    th = lambda t: A * (1 - np.cos(np.pi * np.clip((t - T0) / D, 0, 1))) / 2 if hold is None else hold
    R = lambda a: rot(axis, a) @ base
    keys = [Q.from_mat((Gp.T @ R(th(i / fps)))[None])[0].tolist() for i in range(frames)]
    clip = {"name": "syn", "fps": fps, "loop": False, "frames": frames, "bones": ["hand_r"], "rot": {"hand_r": keys}, "pos": {}}
    pt = lambda a, s: r.head[h] + R(a) @ (np.array(pc["at"]) + s * np.array(pc["dir"]))
    ax = np.array(axis, float)
    tip = pt(0.0, pc["tip"]) - r.head[h]
    return clip, pt(F * A, 0.75 * pc["tip"]), float(np.linalg.norm(tip - (tip @ ax) * ax))


def spec(T, contact):
    return {"kind": "action", "held": ["sword"],
            "beats": {"contact": [contact], "target": {"bearing_deg": float(np.degrees(np.arctan2(T[0], T[2]))),
                                                        "height_cm": 100 * T[1], "dist_cm": 100 * float(np.hypot(T[0], T[2]))}}}


CASES = {"flat sweep": ([0, 1, 0], [-1, 0, 0], [0, 0.2, 0]),       # (about the vertical, her right to her left; T 20 cm under the sweep)
         "overhead chop": ([1, 0, 0], [0, 1, 0], [0.2, 0, 0])}     # (about her left-right axis, from straight up down the front; T 20 cm aside)


@pytest.mark.parametrize("case", list(CASES))
@pytest.mark.parametrize("fps", [60.0, 30.0])
def test_cross_and_peak_closed_form(case, fps):
    axis, e0, off = CASES[case]
    clip, T, _ = cut(axis, e0, fps, 42 if fps == 60 else 21)
    m = PC.measure(p4, rig(), clip, spec(T - np.array(off), CROSS))["marks"][0]
    assert abs(m["cross"] - CROSS) * 60 < 0.25
    assert abs(m["tip_peak"] - PEAK) * 60 < 0.25
    assert abs(m["pass_cm"] - 20) < 1.0 and abs(m["along"] - 0.75) < 0.03
    assert not m["miss"] and abs(m["contact_minus_cross_f60"]) < 0.25
    assert abs(m["contact_minus_peak_f60"] - (CROSS - PEAK) * 60) < 0.25


@pytest.mark.parametrize("case", list(CASES))
def test_miss_word_when_the_mark_is_two_frames_early(case):
    axis, e0, off = CASES[case]
    clip, T, _ = cut(axis, e0)
    on = PC.measure(p4, rig(), clip, spec(T - np.array(off), CROSS))
    early = PC.measure(p4, rig(), clip, spec(T - np.array(off), CROSS - 2 / 60))
    assert "MISS" not in "\n".join(PC.lines(on))
    assert "contact - cross -2.0" in PC.lines(early)[0] and " MISS" in PC.lines(early)[0]
    assert early["marks"][0]["miss"] and abs(early["marks"][0]["contact_minus_cross_f60"] + 2) < 0.25


def test_no_crossing_when_the_blade_never_reaches_the_target():
    clip, T, _ = cut(*CASES["flat sweep"][:2])
    s = spec(T, CROSS)
    s["beats"]["target"]["bearing_deg"] += 170            # (past the sweep's end: nearest at the swing's edge)
    res = PC.measure(p4, rig(), clip, s)
    assert res["marks"][0]["cross"] is None and res["marks"][0]["miss"] and "NO-CROSS" in PC.lines(res)[0]


@pytest.mark.parametrize("deg,miss", [(20.0, False), (140.0, True)])
def test_blend_ratio(deg, miss):
    axis, e0, _ = CASES["flat sweep"]
    clip, T, rad = cut(axis, e0)
    idle, _, _ = cut(axis, e0, frames=2, hold=-np.radians(deg))   # (the idle's pose: the blade deg behind the cut's start)
    B = 0.1                                                         # (the cut rests until T0 = 0.1: the fade alone moves the blade)
    res = PC.measure(p4, rig(), clip, spec(T, CROSS), frm=idle, frame=0, seconds=B)
    chord = lambda w: 2 * rad * np.sin(w / 2)                       # (the tip's chord over an angle w)
    want = chord(np.radians(deg) / B / 60) * 60 / (chord(A * np.pi / (2 * D) / 60) * 60)
    b = res["blend"]
    assert abs(b["ratio"] - want) < 0.03 * want
    assert b["miss"] == miss == (want >= 1.0) and ("MISS" in PC.lines(res)[-1]) == miss
