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
from keyed import STRIKE, build
from clips.run import _swivel


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


# The buckler's hand in the guard (chest frame, from the shoulder) and its elbow's way: out
# ahead, the elbow open at 122 degrees (at (-0.12, -0.26, 0.22) it closed to 101 and the rim
# cut her upper arm 14/25 mm and sat on her pauldron).
GUARD_L_AT = (-0.07, -0.22, 0.34)
GUARD_L_POLE = (1.0, -0.5, -0.4)


def shield_l(at, pole):
    """The buckler's hand at `at` (chest frame, from the shoulder), the elbow `pole`'s way."""
    return {"arc": arc_of(at), "pole": pole, "frame": "chest", "blade": _n(-0.3, 0.75, 0.6), "twist": 0.3}


def guard_l(lift=0.0):
    """The buckler held up before her, a little to the left."""
    x, y, z = GUARD_L_AT
    return shield_l((x, y + lift, z), GUARD_L_POLE)


def with_shield(keys, track):
    """The buckler keyed on its own [(frame, hand, elbow's way, ease)]: set in the body's key of the
    same frame, or a key of its own between them."""
    keys = [(t, dict(p), e) for t, p, e in keys]
    at_t = {t: k for k, (t, _, _) in enumerate(keys)}
    for t, at, pole, e in track:
        if t in at_t:
            keys[at_t[t]][1]["hand_l"] = shield_l(at, pole)
        else:
            keys.append((t, {"hand_l": shield_l(at, pole)}, e))
    return sorted(keys, key=lambda k: k[0])


def pose(hips_yaw, spine_yaw, hand, blade, pole=(-0.7, -0.5, -0.3), left=None, pitch=6, roll=0, head=None,
         weight=0.0, pivot=0.0, fingers="grip"):
    p = feet(weight, pivot)
    p["hips"]["rot"] = (hips_yaw, 4, 0)
    p["spine"] = (spine_yaw, pitch, roll)
    # The head keeps on the foe: it turns against the back.
    p["head"] = head if head is not None else (-(hips_yaw + spine_yaw) * 0.6, -4, 0)
    p["hand_r"] = {"arc": arc_of(hand), "blade": blade, "pole": pole, "frame": "chest", "twist": 0.5}
    if left is not False:
        p["hand_l"] = left or guard_l()
    p["fingers_r"] = fingers
    p["fingers_l"] = "fist"
    return p


GUARD = pose(0, 0, (-0.05, -0.30, 0.20), _n(-0.25, 0.65, 0.7), pole=(-0.6, -0.4, -0.6))


# The buckler through each cut: its own keys (frame, hand, elbow's way, ease), chest frame
# from the shoulder.
BACK_L = [
    (0, (0.12, -0.24, 0.33), (1.0, -0.6, -0.3), "fast"),
    (2.5, (0.10, -0.26, 0.34), (1.0, -0.6, -0.3), "linear"),
    (5, (0.16, -0.16, 0.34), (1.0, -0.6, -0.3), "ease"),
    (8, (0.16, -0.16, 0.34), (1.0, -0.6, -0.3), "ease"),
    (15, GUARD_L_AT, GUARD_L_POLE, "auto"),
    (24, GUARD_L_AT, GUARD_L_POLE, "ease"),
]
FORE_L = [
    (0, (-0.04, -0.20, 0.36), (1.0, -0.5, -0.4), "fast"),
    (2.5, (0.04, -0.18, 0.37), (1.0, -0.5, -0.3), "linear"),
    (5, (0.17, -0.04, 0.36), (1.0, -0.6, -0.5), "ease"),
    (13, (0.17, -0.04, 0.36), (1.0, -0.6, -0.5), "ease"),
    (19, (0.0, -0.20, 0.36), (1.0, -0.5, -0.4), "auto"),
    (24, GUARD_L_AT, GUARD_L_POLE, "ease"),
]
HEAVY_L = [
    (0, (-0.02, -0.18, 0.37), (1.0, -0.5, -0.4), "fast"),
    (3, (0.04, -0.18, 0.37), (1.0, -0.5, -0.3), "linear"),
    (6, (0.19, 0.0, 0.35), (1.0, -0.6, -0.5), "ease"),
    (15, (0.19, 0.0, 0.35), (1.0, -0.6, -0.5), "ease"),
    (22, (0.02, -0.18, 0.37), (1.0, -0.5, -0.4), "auto"),
    (30, GUARD_L_AT, GUARD_L_POLE, "ease"),
]
# A1 L23: the buckler stays at her SIDE through every blow (the run's own shield_guard spec: hand (0.14, -0.32, 0.26) from the
# shoulder in the chest frame, swivel -90, no blade key), riding the cut a little (forward on the wind, back on the follow-
# through); the last key is the run's exactly so the blend has no pop. (BACK_L/FORE_L/HEAVY_L/shield_l stay: arts.py uses them.)
SIDE_AT = (0.14, -0.32, 0.26)
SIDE_SWIVEL = -90


def side_l(at):
    """The run's side-shield spec with the hand at `at` (chest frame, from the shoulder)."""
    return {"arc": arc_of(at), "pole": _swivel(at, SIDE_SWIVEL), "frame": "chest"}


def _ride(dx, dz, y=0.0):
    x, yy, z = SIDE_AT
    return (x + dx, yy + y, z + dz)


def with_side_shield(keys, track):
    """with_shield's sibling: the buckler's own [(frame, hand, ease)] in the run's side format."""
    keys = [(t, dict(p), e) for t, p, e in keys]
    at_t = {t: k for k, (t, _, _) in enumerate(keys)}
    for t, at, e in track:
        if t in at_t:
            keys[at_t[t]][1]["hand_l"] = side_l(at)
        else:
            keys.append((t, {"hand_l": side_l(at)}, e))
    return sorted(keys, key=lambda k: k[0])


RIDE_WIND = (-0.03, 0.03)    # (dx, dz): in and forward on the wind
RIDE_FOLLOW = (0.0, -0.05, 0.0)   # (dx, dz, y): back on the follow-through
SIDE_BACK_L = [(0, _ride(*RIDE_WIND), "fast"), (2.5, _ride(-0.015, 0.02), "linear"), (5, _ride(*RIDE_FOLLOW), "ease"),
               (8, _ride(*RIDE_FOLLOW), "ease"), (15, _ride(0.0, -0.02), "auto"), (24, SIDE_AT, "ease")]
# The left-going cuts (fore, heavy) sweep the blade across where the buckler rides: it draws back behind the blade.
RIDE_DODGE = (0.0, -0.05, 0.0)   # (dx, dz, y) (tried z -0.10 clear of the sweep, and y -0.06: the disc rose over her head, or the arm straightened, and still met the blade)
SIDE_FORE_L = [(0, _ride(*RIDE_WIND), "fast"), (2.5, _ride(-0.015, 0.02), "linear"), (5, _ride(0.0, -0.05), "ease"),
               (8, _ride(*RIDE_DODGE), "ease"), (13, _ride(*RIDE_DODGE), "ease"), (19, _ride(0.0, -0.02), "auto"), (24, SIDE_AT, "ease")]
SIDE_HEAVY_L = [(0, _ride(*RIDE_WIND), "fast"), (3, _ride(-0.015, 0.02), "linear"), (6, _ride(*RIDE_DODGE), "ease"),
                (15, _ride(*RIDE_DODGE), "ease"), (22, _ride(0.0, -0.02), "auto"), (30, SIDE_AT, "ease")]

# A1 L23: the sword's last key = the run's trailing carry (run_warden frame 0, the right fist from the right shoulder, the blade
# line and the elbow's way, all in the chest frame; measured by L23/carry.py), the body as GUARD's.
CARRY_AT = (-0.096, -0.452, 0.191)
CARRY_BLADE = (-0.304, -0.868, -0.392)
CARRY_POLE = (-0.579, 0.419, 0.7)
CARRY = pose(0, 0, CARRY_AT, CARRY_BLADE, pole=CARRY_POLE, left=False, pitch=12)
# The way home: the blade comes from forward to the carry (back and down) out by her RIGHT side, not down through her legs
# (the plain blend swung it through her calves at 1-8 mm).
CARRY_VIA = pose(0, 0, (-0.26, -0.38, 0.20), _n(-0.9, -0.35, 0.1), pole=CARRY_POLE, left=False)
BACK_COCK = (0.30, 0.04, 0.17)   # the cocked fist off her chest (at (0.30, 0.02, 0.10) the hilt was 11 mm into it)


def _body(p):
    return {k: v for k, v in p.items() if k != "hand_l"}


def sword_back(rig):
    keys = [
        # Cocked: the blade drawn back across her to the left, high; hips and
        # back wound to the left.
        (0, pose(18, 30, BACK_COCK, _n(0.55, 0.6, -0.55), pole=(0.2, -0.3, -1.0), left=False, weight=0.4, pitch=4), "fast"),
        # Through the middle at full reach, the blade level and leading.
        (2.5, pose(4, 4, (-0.08, -0.12, 0.46), _n(0.05, 0.5, 0.86), pole=(-0.3, -0.8, -0.4), left=False, weight=0.0), "linear"),
        # Out to her right: the cut ends.
        (5, pose(-16, -32, (-0.36, -0.14, 0.30), _n(-0.93, 0.26, 0.24), pole=(-0.2, -1.0, 0.2), left=False, weight=-0.5), "ease"),
        # Held, the blade carrying on a hair (the weight of it).
        (8, pose(-19, -38, (-0.38, -0.18, 0.24), _n(-0.99, 0.04, -0.05), pole=(-0.1, -1.0, 0.3), left=False, weight=-0.6), "ease"),
        # Recovering: the blade comes round and up into the guard.
        (13, CARRY_VIA, "ease"),
        (24, CARRY, "ease"),
    ]
    keys = with_side_shield(keys, SIDE_BACK_L)
    return build("sword_back", rig, keys, lead=STRIKE, meta={"layer": "upper", "contact": 2.5 / 30, "weapon": "sword+shield"})


def sword_fore(rig):
    keys = [
        # Cocked over the right shoulder, the back wound to the right.
        (0, pose(-18, -32, (-0.20, 0.10, 0.14), _n(-0.3, 0.79, -0.69), pole=(-0.8, -0.2, -0.5), left=False, weight=-0.4), "fast"),
        (2.5, pose(-3, -4, (-0.125, -0.0925, 0.46), _n(0.015, 0.49, 0.88), pole=(-0.6, -0.325, -0.3), left=False, weight=0.0), "linear"),
        # Out to her left, across her: the cut ends low.
        (5, pose(16, 30, (0.26, -0.22, 0.30), _n(0.9, 0.0175, 0.0), pole=(-0.9, -0.2, 0.2), left=False, weight=0.6, pivot=0.6), "ease"),
        (8, pose(19, 36, (0.28, -0.27, 0.24), _n(0.86, -0.26, -0.17), pole=(-0.9, -0.1, 0.3), left=False, weight=0.7, pivot=0.7), "ease"),
        (17, CARRY_VIA, "ease"),
        (24, CARRY, "ease"),
    ]
    keys = with_side_shield(keys, SIDE_FORE_L)
    return build("sword_fore", rig, keys, lead=STRIKE, meta={"layer": "upper", "contact": 2.5 / 30, "weapon": "sword+shield"})


def sword_heavy(rig):
    keys = [
        # Wound far round to the right and low.
        (0, pose(-30, -40, (-0.30, -0.20, 0.06), _n(-0.6, 0.1, -0.8), pole=(-0.6, -0.8, 0.0), left=False, weight=-0.7, pitch=14), "fast"),
        (3, pose(-6, -8, (-0.165, -0.14, 0.47), _n(-0.4, 0.29, 1.0), pole=(-0.4, -0.9, -0.1), left=False, weight=0.0, pitch=12), "linear"),
        # All the way round to her left, the whole back behind it.
        (6, pose(26, 44, (0.30, -0.16, 0.34), _n(0.95, 0.175, 0.075), pole=(-0.8, -0.6, 0.2), left=False, weight=0.8, pivot=1.0, pitch=10), "ease"),
        (10, pose(30, 50, (0.30, -0.22, 0.26), _n(0.8, -0.25, -0.3), pole=(-0.8, -0.4, 0.4), left=False, weight=0.9, pivot=1.0, pitch=10), "ease"),
        (16, pose(10, 14, (0.0, -0.24, 0.36), _n(-0.6, -0.4, 0.7), pole=CARRY_POLE, left=False, weight=0.3, pivot=0.3), "ease"),
        (24, CARRY_VIA, "ease"),
        (30, CARRY, "ease"),
    ]
    keys = with_side_shield(keys, SIDE_HEAVY_L)
    return build("sword_heavy", rig, keys, lead=STRIKE, meta={"layer": "upper", "contact": 3 / 30, "weapon": "sword+shield"})


def clips(rig, want):
    out = []
    for name, fn in (("sword_back", sword_back), ("sword_fore", sword_fore), ("sword_heavy", sword_heavy),
                     ("sword_guard", None)):
        if want and not any(w in name for w in want):
            continue
        if fn:
            out.append(fn(rig))
    return out
