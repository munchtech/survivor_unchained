"""bodies.clip_source: body p1 makes skin's clip loader read tools/anim/data/body_p1/clips; A leaves skin.OUT alone."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "anim"))
sys.path.insert(0, HERE)

import bodies  # noqa: E402
import skin  # noqa: E402


def test_p1_reads_b_clips(monkeypatch):
    monkeypatch.setattr(skin, "OUT", skin.Path("A_CLIPS_STAND_IN"))
    monkeypatch.setenv("SU_ARMOR_BODY", "p1")
    monkeypatch.setenv("ANIM_OUT", "A_CLIPS_STAND_IN")
    out = bodies.clip_source(skin)
    assert str(out / "clips") == bodies.cur("p1").clips
    assert os.environ["ANIM_OUT"] == str(out)


def test_a_leaves_skin_out(monkeypatch):
    monkeypatch.setattr(skin, "OUT", skin.Path("A_CLIPS_STAND_IN"))
    monkeypatch.setenv("SU_ARMOR_BODY", "a")
    assert str(bodies.clip_source(skin)) == "A_CLIPS_STAND_IN"
