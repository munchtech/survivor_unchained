"""Checks of the solver's conventions (not shipped)."""
from keyed import build, merge, stance


def clips(rig, want):
    if not any("test" in w for w in want):
        return []
    base = stance()
    out = []
    # Hips: up/down, yaw left, pitch forward, roll right; spine likewise.
    out.append(build("test_axes", rig, [
        (0, base, "ease"),
        (10, merge(base, hips={"pos": (0, -0.15, 0)}), "ease"),
        (20, merge(base, spine=(40, 0, 0)), "ease"),
        (30, merge(base, spine=(0, 30, 0)), "ease"),
        (40, merge(base, spine=(0, 0, 25)), "ease"),
        (50, merge(base, head=(40, 0, 0)), "ease"),
        (60, merge(base, clav_l=(20, 0), clav_r=(0, 20)), "ease"),
        (70, merge(base, hand_r={"arc": (0, 0, 0.42), "blade": (0, 1, 0), "knuckles": (0, 0, 1)}, fingers_r="grip"), "ease"),
        (80, merge(base, hand_l={"arc": (60, 30, 0.42)}, fingers_l="spread"), "ease"),
        (90, merge(base, foot_l={"pos": (0.2, 0.3, 0.3), "toe": 30}, fingers_l="fist", fingers_r="claw"), "ease"),
    ]))
    return out
