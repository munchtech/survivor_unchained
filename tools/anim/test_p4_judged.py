"""p4.clip_hash and the judged flag (the pack gate): the hash covers what plays only; judged_state / judged_note
stamp, strip or flag stale.

    python -m pytest -q tools/anim/test_p4_judged.py
"""
import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import p4  # noqa: E402


def clip():
    return {"name": "x", "fps": 30.0, "loop": True, "frames": 2, "bones": ["a"], "rot": {"a": [[0, 0, 0, 1], [0, 0, 0.1, 0.99]]},
            "pos": {"root": [[0, 0, 0], [0, 0, 0.1]]}, "speed_mps": None, "notes": "n"}


def test_hash_ignores_key_order_judged_and_notes():
    a = clip()
    b = dict(reversed(list(copy.deepcopy(a).items())))
    b["judged"] = {"build": "zz"}
    b["notes"] = "other"
    b["source"] = {"crop": 1}
    assert p4.clip_hash(a) == p4.clip_hash(b)


def test_hash_changes_with_one_rot_value():
    a, b = clip(), clip()
    b["rot"]["a"][1][2] = 0.11
    assert p4.clip_hash(a) != p4.clip_hash(b)


def test_hash_covers_beats_and_speed():
    a, b = clip(), clip()
    b["speed_mps"] = 1.2
    c = clip()
    c["beats"] = {"hold": [0, 1]}
    assert len({p4.clip_hash(a), p4.clip_hash(b), p4.clip_hash(c)}) == 3


def test_state_not_judged_judged_stale():
    c = clip()
    assert p4.judged_state({}, c) == "not judged"
    spec = {"judged": {"by": "j", "on": "2026-11-09", "verdict": "PASS", "build": p4.clip_hash(c)}}
    assert p4.judged_state(spec, c) == "judged"
    c["rot"]["a"][0][3] = 0.5
    assert p4.judged_state(spec, c) == "stale"


def test_note_stamps_or_strips():
    c = clip()
    spec = {"judged": {"by": "j", "on": "2026-11-09", "verdict": "PASS", "build": p4.clip_hash(c)}}
    line = p4.judged_note("x", spec, c)
    assert c["judged"] == spec["judged"] and "build matches" in line
    c["rot"]["a"][0][3] = 0.5
    line = p4.judged_note("x", spec, c)
    assert "judged" not in c and "JUDGED FLAG STALE" in line
    c2 = clip()
    c2["judged"] = {"build": "old"}
    assert "not judged" in p4.judged_note("x", {}, c2) and "judged" not in c2
