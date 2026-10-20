"""The reaver's axes: hacking, feral, from the hips.

One axe (the butcher's cleaver): diagonal hacks that start high and finish
low, the whole back thrown behind them, the free fist flung back for the
counterweight; the heavy is a two-step overhead brought down and through.

Two axes (the gyre axes): each hand cuts in turn, the left from her left to
her right (the game's first arc), the right back the other way, the idle
hand winding up for its turn as the other cuts; the heavy crosses both.

Timing as the sword's (clips/sword.py): cocked at frame 0, through by 5,
a beat held, then the weight. The reaver holds less and recovers later:
she carries the swing further.
"""
from __future__ import annotations

import math

import numpy as np

from clips.sword import _n
from gait import arc_of
from keyed import STRIKE, build, merge


def feet(weight=0.0, pivot=0.0, crouch=0.03):
    """Set for the blow (anim 42, the judge's stance): feet about 1.3x her
    shoulders apart, the left about 20 cm ahead, knees soft (15-20 deg) and
    over the toes, never knocked in. The back heel peels up on the ball as
    the hips drive through (no turn of the foot, so nothing slides)."""
    def pole(yaw, s):
        a = math.radians(yaw)
        return (math.sin(a) + s * 0.25, 0, math.cos(a))
    return {
        "foot_l": {"pos": (0.25, 0, 0.09), "rot": (12, 0, 0), "pole": pole(12, 1)},
        "foot_r": {"pos": (-0.25, 0.02 * max(pivot, 0), -0.11), "rot": (-24, 0, 0), "toe": 16 * max(pivot, 0),
                   "pole": pole(-24, -1)},
        "hips": {"pos": (0.035 * weight, -crouch - 0.008 * abs(weight), 0.0 + 0.025 * weight)},
    }


def pose(hips_yaw, spine_yaw, hand, blade, pole=(-0.7, -0.5, -0.3), off=None, pitch=12, roll=0, weight=0.0, pivot=0.0,
         head=None, left_blade=None, left_pole=(0.7, -0.5, -0.3), hinge=8, clav_r=(4, 6)):
    p = feet(weight, pivot)
    p["hips"]["rot"] = (hips_yaw, hinge, 0)
    p["spine"] = (spine_yaw, pitch, roll)
    p["head"] = head if head is not None else (-(hips_yaw + spine_yaw) * 0.55, -8, 0)
    p["clav_l"] = (4, 6)
    p["clav_r"] = clav_r
    p["hand_r"] = {"arc": arc_of(hand), "blade": blade, "pole": pole, "frame": "chest", "twist": 0.5}
    off = off or (-0.04, -0.30, 0.18)
    p["hand_l"] = {"arc": arc_of(off), "pole": left_pole, "frame": "chest", "twist": 0.4}
    if left_blade is not None:
        p["hand_l"]["blade"] = left_blade
    p["fingers_r"] = "grip"
    p["fingers_l"] = "grip" if left_blade is not None else "fist"
    return p


GUARD = pose(0, 0, (-0.06, -0.26, 0.22), _n(-0.3, 0.75, 0.55), pole=(-0.7, -0.5, -0.4), off=(-0.02, -0.28, 0.20))


def axe_back(rig):
    """Backhand hack, her left to her right, falling as it goes."""
    keys = [
        (0, pose(28, 30, (0.30, 0.10, 0.12), _n(0.5, 0.75, -0.45), pole=(0.2, -0.2, -1.0),
                 off=(0.0, -0.32, -0.10), weight=0.5, pitch=8), "fast"),
        (2.5, pose(4, 6, (-0.04, -0.10, 0.46), _n(-0.2, -0.15, 1.0), pole=(-0.3, -0.8, -0.4),
                   off=(0.04, -0.30, 0.0), weight=0.0, pitch=16), "linear"),
        (5, pose(-20, -36, (-0.36, -0.30, 0.28), _n(-0.95, -0.3, 0.1), pole=(-0.2, -1.0, 0.2),
                 off=(0.14, -0.20, 0.26), weight=-0.6, pitch=8, hinge=13), "ease"),
        (7, pose(-23, -42, (-0.38, -0.36, 0.20), _n(-0.85, -0.45, -0.25), pole=(-0.1, -1.0, 0.3),
                 off=(0.14, -0.22, 0.26), weight=-0.7, pitch=9, hinge=14), "ease"),
        (16, pose(-8, -12, (-0.18, -0.26, 0.24), _n(-0.5, 0.55, 0.65), pole=(-0.6, -0.5, -0.4), weight=-0.2), "auto"),
        (26, GUARD, "ease"),
    ]
    return build("axe_back", rig, keys, lead=STRIKE, meta={"layer": "upper", "stance": True, "contact": 2.5 / 30, "weapon": "axe"})


def axe_fore(rig):
    """Forehand hack, her right to her left, over the top and down across."""
    keys = [
        # Cocked as the heavy is (anim 42: it read as a torch raised): the fist by her right ear, the elbow up and
        # back, the head back over her shoulder; the shoulders wound about 25 deg behind the hips.
        (0, pose(-28, -26, (-0.12, 0.24, -0.02), _n(-0.3, 0.6, -0.75), pole=(-0.6, 0.6, -0.4),
                 off=(0.10, -0.16, 0.32), weight=-0.5, pitch=2, hinge=4), "fast"),
        (2.5, pose(-6, -4, (0.0, -0.06, 0.46), _n(0.15, -0.1, 1.0), pole=(-0.6, -0.7, -0.3),
                   off=(0.04, -0.28, 0.16), weight=0.1, pitch=6), "linear"),
        # The follow-through (anim 42): the right fist carried across before her left hip, the arm long and the
        # shoulder rolled after it; the head out past her left leg, the haft 30 deg down; a hinge from the hips
        # (the back long); the free arm long and swung back behind her for the counterweight.
        (5, pose(22, 28, (0.25, -0.40, 0.31), _n(0.8, -0.5, 0.3), pole=(-0.9, -0.3, 0.1),
                 off=(0.10, -0.47, -0.05), left_pole=(0.4, -0.2, -0.9), weight=0.7, pivot=0.7, pitch=6, hinge=14,
                 clav_r=(4, 22)), "ease"),
        (7, pose(24, 30, (0.27, -0.42, 0.30), _n(0.8, -0.5, 0.3), pole=(-0.9, -0.3, 0.2),
                 off=(0.10, -0.47, -0.06), left_pole=(0.4, -0.2, -0.9), weight=0.8, pivot=0.8, pitch=6, hinge=15,
                 clav_r=(4, 24)), "ease"),
        (16, pose(7, 12, (0.02, -0.26, 0.24), _n(0.2, 0.6, 0.75), pole=(-0.6, -0.5, -0.4), weight=0.2, pivot=0.2),
         "auto"),
        (26, GUARD, "ease"),
    ]
    return build("axe_fore", rig, keys, lead=STRIKE, meta={"layer": "upper", "stance": True, "contact": 2.5 / 30,
                                                           "weapon": "axe"})


def axe_heavy(rig):
    """The axe brought from behind her shoulder, high, and hacked down and
    across in front, the back bending into it."""
    keys = [
        (0, pose(-26, -40, (-0.12, 0.26, -0.02), _n(-0.3, 0.6, -0.75), pole=(-0.6, 0.6, -0.4),
                 off=(0.08, -0.06, 0.34), weight=-0.6, pitch=-4), "fast"),
        (3, pose(-6, -8, (-0.02, 0.0, 0.42), _n(0.0, 0.2, 1.0), pole=(-0.6, -0.5, -0.4),
                 off=(0.04, -0.28, 0.16), weight=0.2, pitch=10), "linear"),
        # (As axe_fore's finish, anim 42, but heavier: 10 deg more hinge, the head lower and further out.)
        (6, pose(22, 28, (0.25, -0.50, 0.32), _n(0.8, -0.55, 0.3), pole=(-0.9, -0.3, 0.1),
                 off=(0.10, -0.47, 0.0), left_pole=(0.4, -0.2, -0.9), weight=0.8, pivot=0.8, pitch=9, hinge=22,
                 clav_r=(4, 22)), "ease"),
        (10, pose(25, 30, (0.27, -0.54, 0.30), _n(0.8, -0.58, 0.3), pole=(-0.9, -0.3, 0.2),
                  off=(0.10, -0.47, 0.0), left_pole=(0.4, -0.2, -0.9), weight=0.9, pivot=0.9, pitch=10, hinge=24,
                  clav_r=(4, 24)), "ease"),
        (20, pose(6, 10, (0.0, -0.26, 0.24), _n(0.2, 0.6, 0.75), pole=(-0.6, -0.5, -0.4), weight=0.2, pivot=0.2),
         "auto"),
        (32, GUARD, "ease"),
    ]
    return build("axe_heavy", rig, keys, lead=STRIKE, meta={"layer": "upper", "stance": True, "contact": 3 / 30,
                                                            "weapon": "axe"})


# Two axes: the left hand's forehand is the right hand's mirrored.
def mirror(p):
    """A pose mirrored left for right."""
    out = {}
    for k, v in p.items():
        k2 = k.replace("_l", "_R").replace("_r", "_l").replace("_R", "_r") if k[-2:] in ("_l", "_r") else k
        if isinstance(v, dict):
            v2 = {}
            for kk, vv in v.items():
                if kk == "arc":
                    v2[kk] = (-vv[0], vv[1], vv[2])
                elif kk in ("pos", "blade", "knuckles", "pole"):
                    v2[kk] = (-vv[0], vv[1], vv[2])
                elif kk == "rot":
                    v2[kk] = (-vv[0], vv[1], -vv[2])
                else:
                    v2[kk] = vv
            out[k2] = v2
        elif k in ("spine", "neck", "head"):
            out[k2] = (-v[0], v[1], -v[2])
        else:
            out[k2] = v
    return out


def axes_pose(hips_yaw, spine_yaw, hand, blade, pole, idle_hand, idle_blade, weight=0.0, pivot=0.0, pitch=12, hinge=8,
              clav_r=(4, 6)):
    """The right hand cutting, the left winding up for its turn."""
    return pose(hips_yaw, spine_yaw, hand, blade, pole=pole, off=idle_hand, left_blade=idle_blade,
                left_pole=(0.8, -0.3, -0.4), weight=weight, pivot=pivot, pitch=pitch, hinge=hinge, clav_r=clav_r)


AXES_GUARD = pose(0, 0, (-0.08, -0.24, 0.22), _n(-0.35, 0.75, 0.5), pole=(-0.7, -0.5, -0.4), off=(0.08, -0.24, 0.22),
                  left_blade=_n(0.35, 0.75, 0.5))


def _axes_cut():
    """The right axe's forehand, her right to her left; the left axe drawn
    back for its turn (axes_left plays it mirrored)."""
    return [
        (0, axes_pose(-28, -30, (-0.18, 0.14, 0.10), _n(-0.4, 0.8, -0.45), (-0.8, 0.1, -0.5),
                      (0.02, -0.26, 0.30), _n(0.3, 0.6, 0.75), weight=-0.4), "fast"),
        (2.5, axes_pose(-3, -4, (0.0, -0.06, 0.46), _n(0.15, -0.1, 1.0), (-0.6, -0.7, -0.3),
                        (0.10, -0.20, 0.16), _n(0.5, 0.7, 0.3), weight=0.1, pitch=8), "linear"),
        # (As axe_fore's follow-through, anim 42: the fist across before her left hip, the shoulder rolled after
        # it, the head out past her left leg, a hinge from the hips.)
        (5, axes_pose(22, 28, (0.25, -0.40, 0.31), _n(0.8, -0.5, 0.3), (-0.9, -0.3, 0.1),
                      (0.20, -0.04, 0.0), _n(0.5, 0.75, -0.4), weight=0.6, pivot=0.6, pitch=6, hinge=14,
                      clav_r=(4, 22)), "ease"),
        (7, axes_pose(24, 30, (0.27, -0.42, 0.30), _n(0.8, -0.5, 0.3), (-0.9, -0.3, 0.2),
                      (0.22, 0.0, -0.02), _n(0.5, 0.75, -0.45), weight=0.7, pivot=0.7, pitch=6, hinge=15,
                      clav_r=(4, 24)), "ease"),
        (15, axes_pose(7, 12, (0.0, -0.24, 0.24), _n(0.2, 0.6, 0.75), (-0.6, -0.5, -0.4),
                       (0.10, -0.20, 0.20), _n(0.4, 0.7, 0.55), weight=0.2, pivot=0.2), "auto"),
    ]


def axes_right(rig):
    """The right axe's forehand, her right to her left; the left axe drawn
    back for its turn."""
    keys = _axes_cut() + [(24, AXES_GUARD, "ease")]
    return build("axes_right", rig, keys, lead=STRIKE, meta={"layer": "upper", "stance": True, "contact": 2.5 / 30, "weapon": "axes"})


def axes_left(rig):
    """The left axe's forehand, her left to her right: the right's mirrored."""
    keys = [(t, mirror(p), e) for t, p, e in _axes_cut()] + [(24, AXES_GUARD, "ease")]
    # (The mirrored stance puts her right foot forward for this one: a step
    # through with the cut.)
    return build("axes_left", rig, keys, lead=STRIKE, meta={"layer": "upper", "stance": True, "contact": 2.5 / 30, "weapon": "axes"})


def axes_heavy(rig):
    """Both axes from wide and high, crossing in front of her and out."""
    keys = [
        (0, pose(0, 0, (-0.30, 0.16, 0.0), _n(-0.5, 0.75, -0.4), pole=(-0.7, 0.3, -0.5), off=(0.30, 0.16, 0.0),
                 left_blade=_n(0.5, 0.75, -0.4), left_pole=(0.7, 0.3, -0.5), pitch=0, weight=0.0), "fast"),
        (3, pose(0, 0, (0.02, -0.12, 0.44), _n(0.3, -0.1, 1.0), pole=(-0.7, -0.6, -0.2), off=(-0.02, -0.08, 0.44),
                 left_blade=_n(-0.3, -0.1, 1.0), left_pole=(0.7, -0.6, -0.2), pitch=18, weight=0.3), "linear"),
        (6, pose(0, 0, (0.24, -0.36, 0.22), _n(0.8, -0.5, 0.2), pole=(-0.9, -0.3, 0.2), off=(-0.24, -0.36, 0.22),
                 left_blade=_n(-0.8, -0.5, 0.2), left_pole=(0.9, -0.3, 0.2), pitch=12, hinge=17, weight=0.5), "ease"),
        (10, pose(0, 0, (0.26, -0.40, 0.18), _n(0.75, -0.6, -0.1), pole=(-0.9, -0.2, 0.3), off=(-0.26, -0.40, 0.18),
                  left_blade=_n(-0.75, -0.6, -0.1), left_pole=(0.9, -0.2, 0.3), pitch=12, hinge=19, weight=0.5), "ease"),
        (20, AXES_GUARD, "auto"),
        (30, AXES_GUARD, "ease"),
    ]
    return build("axes_heavy", rig, keys, lead=STRIKE, meta={"layer": "upper", "stance": True, "contact": 3 / 30, "weapon": "axes"})


def clips(rig, want):
    out = []
    for name, fn in (("axe_back", axe_back), ("axe_fore", axe_fore), ("axe_heavy", axe_heavy),
                     ("axes_right", axes_right), ("axes_left", axes_left), ("axes_heavy", axes_heavy)):
        if want and not any(w in name for w in want):
            continue
        out.append(fn(rig))
    return out
