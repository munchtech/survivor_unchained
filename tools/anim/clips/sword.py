"""The warden's sword (and buckler).

How the game swings (BattleFx, Hits.Arc): the damage, the arc and the clip
start in the same frame; the arc's head crosses in 0.12 s and alternate
swings are mirrored, the first sweeping from her left to her right. The
clips play at 1.6 times, so the blade must cross in the first five or six
frames here. So each swing starts already cocked (its anticipation is the
blend in), cuts through frames 0-5, holds the end of the cut a beat (where
hit-stop lands), then follows through and recovers into the guard; the
next swing may cut that short.

- sword_back: backhand, her left to her right (the game's first swing).
- sword_fore: forehand, her right to her left.
- sword_heavy: a full turn from the hips, low and wide, for the wide arcs.

The buckler never drops: through every cut it stays up before her, riding
the turn of her body.

Hands are placed on arcs about the shoulder in the chest's frame, so the
blade travels round her, not through her; the blade points out along the
cut, edge leading.
"""
from __future__ import annotations

import numpy as np

from gait import arc_of
from keyed import build


def _n(*v):
    v = np.array(v, float)
    return tuple(v / np.linalg.norm(v))


def feet(weight=0.0, pivot=0.0):
    """A fighting stance, left foot forward (the buckler's side); weight
    -1 back on the right, +1 onto the left; pivot: the back heel turning
    out as the hips come round."""
    return {
        "foot_l": {"pos": (0.15, 0, 0.17), "rot": (12, 0, 0)},
        "foot_r": {"pos": (-0.17, 0.0 + 0.03 * max(pivot, 0), -0.13), "rot": (-25 - 20 * pivot, 0, 0), "toe": 25 * max(pivot, 0)},
        "hips": {"pos": (0.03 * weight, -0.07 - 0.02 * abs(weight), 0.02 * weight)},
    }


def guard_l(lift=0.0):
    """The buckler held up before her, a little to the left."""
    return {"arc": arc_of((-0.12, -0.26 + lift, 0.22)), "pole": (1.0, -0.4, -0.3), "frame": "chest",
            "blade": _n(-0.3, 0.75, 0.6), "twist": 0.3}


def pose(hips_yaw, spine_yaw, hand, blade, pole=(-0.7, -0.5, -0.3), left=None, pitch=6, roll=0, head=None,
         weight=0.0, pivot=0.0, fingers="grip"):
    p = feet(weight, pivot)
    p["hips"]["rot"] = (hips_yaw, 4, 0)
    p["spine"] = (spine_yaw, pitch, roll)
    # The head keeps on the foe: it turns against the back.
    p["head"] = head if head is not None else (-(hips_yaw + spine_yaw) * 0.6, -4, 0)
    p["hand_r"] = {"arc": arc_of(hand), "blade": blade, "pole": pole, "frame": "chest", "twist": 0.5}
    p["hand_l"] = left or guard_l()
    p["fingers_r"] = fingers
    p["fingers_l"] = "fist"
    return p


GUARD = pose(0, 0, (-0.05, -0.30, 0.20), _n(-0.25, 0.65, 0.7), pole=(-0.6, -0.4, -0.6))


def sword_back(rig):
    keys = [
        # Cocked: the blade drawn back across her to the left, high; hips and
        # back wound to the left.
        (0, pose(18, 30, (0.30, 0.02, 0.10), _n(0.55, 0.6, -0.55), pole=(0.2, -0.3, -1.0),
                 left=guard_l(-0.08), weight=0.4, pitch=4), "fast"),
        # Through the middle at full reach, the blade level and leading.
        (2.5, pose(4, 4, (-0.05, -0.08, 0.46), _n(-0.15, 0.05, 1.0), pole=(-0.3, -0.8, -0.4),
                   left=guard_l(-0.04), weight=0.0), "linear"),
        # Out to her right: the cut ends.
        (5, pose(-16, -32, (-0.36, -0.14, 0.30), _n(-0.95, -0.05, 0.25), pole=(-0.2, -1.0, 0.2),
                 left={"arc": arc_of((0.10, -0.18, 0.30)), "pole": (1.0, -0.5, 0.0), "frame": "chest",
                       "blade": _n(0.2, 0.7, 0.7)}, weight=-0.5, pivot=0.0), "ease"),
        # Held, the blade carrying on a hair (the weight of it).
        (8, pose(-19, -38, (-0.38, -0.18, 0.24), _n(-0.9, -0.15, -0.3), pole=(-0.1, -1.0, 0.3),
                 left={"arc": arc_of((0.12, -0.18, 0.30)), "pole": (1.0, -0.5, 0.0), "frame": "chest",
                       "blade": _n(0.2, 0.7, 0.7)}, weight=-0.6), "ease"),
        # Recovering: the blade comes round and up into the guard.
        (15, pose(-6, -10, (-0.15, -0.26, 0.24), _n(-0.5, 0.5, 0.7), pole=(-0.6, -0.5, -0.4), weight=-0.2), "auto"),
        (24, GUARD, "ease"),
    ]
    return build("sword_back", rig, keys, meta={"layer": "upper", "contact": 2.5 / 30, "weapon": "sword+shield"})


def sword_fore(rig):
    keys = [
        # Cocked over the right shoulder, the back wound to the right.
        (0, pose(-18, -32, (-0.20, 0.10, 0.14), _n(-0.45, 0.65, -0.6), pole=(-0.8, -0.2, -0.5),
                 left={"arc": arc_of((0.06, -0.16, 0.30)), "pole": (1.0, -0.5, 0.0), "frame": "chest",
                       "blade": _n(0.2, 0.7, 0.7)}, weight=-0.4), "fast"),
        (2.5, pose(-3, -4, (-0.02, -0.06, 0.46), _n(0.1, 0.05, 1.0), pole=(-0.6, -0.7, -0.3),
                   left=guard_l(-0.06), weight=0.0), "linear"),
        # Out to her left, across her: the cut ends low.
        (5, pose(16, 30, (0.26, -0.22, 0.30), _n(0.9, -0.15, 0.35), pole=(-0.9, -0.2, 0.2),
                 left=guard_l(0.02), weight=0.6, pivot=0.6), "ease"),
        (8, pose(19, 36, (0.28, -0.27, 0.24), _n(0.85, -0.3, -0.2), pole=(-0.9, -0.1, 0.3),
                 left=guard_l(0.02), weight=0.7, pivot=0.7), "ease"),
        (15, pose(6, 10, (0.02, -0.28, 0.24), _n(0.2, 0.5, 0.8), pole=(-0.6, -0.5, -0.4), weight=0.2, pivot=0.2),
         "auto"),
        (24, GUARD, "ease"),
    ]
    return build("sword_fore", rig, keys, meta={"layer": "upper", "contact": 2.5 / 30, "weapon": "sword+shield"})


def sword_heavy(rig):
    keys = [
        # Wound far round to the right and low, the buckler thrown out
        # behind her the other way.
        (0, pose(-30, -40, (-0.30, -0.20, 0.06), _n(-0.6, 0.1, -0.8), pole=(-0.6, -0.8, 0.0),
                 left={"arc": arc_of((0.10, -0.10, 0.36)), "pole": (1.0, -0.3, 0.2), "frame": "chest",
                       "blade": _n(0.2, 0.8, 0.6)}, weight=-0.7, pitch=14), "fast"),
        (3, pose(-6, -8, (-0.10, -0.14, 0.47), _n(-0.3, -0.05, 1.0), pole=(-0.4, -0.9, -0.1),
                 left=guard_l(-0.1), weight=0.0, pitch=12), "linear"),
        # All the way round to her left, the whole back behind it.
        (6, pose(26, 44, (0.30, -0.16, 0.34), _n(0.95, -0.05, 0.2), pole=(-0.8, -0.6, 0.2),
                 left=guard_l(0.02), weight=0.8, pivot=1.0, pitch=10), "ease"),
        (10, pose(30, 50, (0.30, -0.22, 0.26), _n(0.8, -0.3, -0.3), pole=(-0.8, -0.4, 0.4),
                  left=guard_l(0.02), weight=0.9, pivot=1.0, pitch=10), "ease"),
        (19, pose(10, 14, (0.04, -0.28, 0.24), _n(0.2, 0.5, 0.8), pole=(-0.6, -0.5, -0.4), weight=0.3, pivot=0.3),
         "auto"),
        (30, GUARD, "ease"),
    ]
    return build("sword_heavy", rig, keys, meta={"layer": "upper", "contact": 3 / 30, "weapon": "sword+shield"})


def clips(rig, want):
    out = []
    for name, fn in (("sword_back", sword_back), ("sword_fore", sword_fore), ("sword_heavy", sword_heavy),
                     ("sword_guard", None)):
        if want and not any(w in name for w in want):
            continue
        if fn:
            out.append(fn(rig))
    return out
