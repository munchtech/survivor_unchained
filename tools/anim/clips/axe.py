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
         head=None, left_blade=None, left_pole=(0.7, -0.5, -0.3), hinge=8, clav_r=(4, 6), crouch=0.03, free="fist", knuckles=None, hroll=0, hpitch=-8, hips_off=(0, 0, 0)):
    p = feet(weight, pivot, crouch)
    p["hips"]["pos"] = tuple(a + b for a, b in zip(p["hips"]["pos"], hips_off))
    p["hips"]["rot"] = (hips_yaw, hinge, 0)
    p["spine"] = (spine_yaw, pitch, roll)
    p["head"] = head if head is not None else (-(hips_yaw + spine_yaw) * 0.55, hpitch, hroll)
    p["clav_l"] = (4, 6)
    p["clav_r"] = clav_r
    p["hand_r"] = {"arc": arc_of(hand), "blade": blade, "pole": pole, "frame": "chest", "twist": 0.5}
    if knuckles is not None:
        p["hand_r"]["knuckles"] = knuckles
    off = off or (-0.04, -0.30, 0.18)
    p["hand_l"] = {"arc": arc_of(off), "pole": left_pole, "frame": "chest", "twist": 0.4}
    if left_blade is not None:
        p["hand_l"]["blade"] = left_blade
    p["fingers_r"] = "grip"
    p["fingers_l"] = "grip" if left_blade is not None else free
    return p


# The head at the finish (solver 7a, judge r3 call 2): the spine's roll to her left and the head's counter-turn on
# a pitched neck rolled her head ~25 deg (heavy ~30) onto her shoulder; rolled back level, and the heavy's chin up.
HR5, HR7 = 22, 24
HH6, HH10, HP6, HP10 = 26, 28, -24, -24
# The run variants (axe_fore_run, axe_heavy_run): the free hand at the wind-up and its elbow's pole; the finish's
# fist moved (chest frame) and the blade's direction.
# The idle axe through the finish (solver 7a, judge r3 call 3): held in its f3 shape, not stood upright behind her
# shoulder: the fist out from her left shoulder at chest height, the haft leaning out to her left.
HV_YAW, HV_PITCH, HV_OFF = (-16, -28), -16, (-0.20, -0.10, -0.12)
AX_IH, AX_IB = (0.15, 0.06, 0.25), (0.25, 0.97, -0.06)
RUN_OFF0, RUN_LP0 = (0.22, -0.05, 0.20), (0.35, -0.9, -0.1)
RUN_DH, RUN_BL = (0.0, 0.0, 0.0), (0.62, -0.45, 0.64)
RUN_SY = 16
RUN_T11, RUN_H11 = 0, (0.10, -0.30, 0.50)
RUN_HSY = 16
RUN_HDH, RUN_HBL = (0.0, 0.04, 0.0), (0.5, -0.8, 0.35)

GUARD = pose(0, 0, (-0.06, -0.26, 0.22), _n(-0.3, 0.75, 0.55), pole=(-0.7, -0.5, -0.4), off=(-0.02, -0.28, 0.20))


def _knuckled(p, k):
    """A pose with her right hand's roll keyed (knuckles, chest frame)."""
    q = dict(p); q["hand_r"] = dict(p["hand_r"], knuckles=k)
    return q


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


def _fore_keys(run=False):
    """axe_fore's keys; run: the variant play shows over her run (axe_fore_run)."""
    off0, lp0 = (RUN_OFF0, RUN_LP0) if run else ((0.10, -0.16, 0.32), (0.7, -0.5, -0.3))
    dh, bl = (RUN_DH, _n(*RUN_BL)) if run else ((0, 0, 0), _n(0.45, -0.45, 0.8))
    sy = RUN_SY if run else 0
    h5, h7 = (0.21 + dh[0], -0.12 + dh[1], 0.44 + dh[2]), (0.235 + dh[0], -0.10 + dh[1], 0.43 + dh[2])
    keys = [
        # Cocked as the heavy is (anim 42: it read as a torch raised): the fist by her right ear, the elbow up and
        # back, the head back over her shoulder; the shoulders wound about 25 deg behind the hips.
        # (Solver 5a, judge r2: the elbow higher and further back, the forearm back beside her head, her face clear.)
        (0, pose(-28, -26, (-0.16, 0.30, -0.14), _n(-0.3, 0.5, -0.8), pole=(-0.6, 1.0, -0.5),
                 off=off0, left_pole=lp0, weight=-0.5, pitch=2, hinge=4), "fast"),
        (2.5, pose(-6, -4, (0.0, -0.06, 0.46), _n(0.15, -0.1, 1.0), pole=(-0.6, -0.7, -0.3),
                   off=(0.04, -0.28, 0.16), weight=0.1, pitch=6), "linear"),
        # The follow-through (anim 42): the right fist carried across before her left hip, the arm long and the
        # shoulder rolled after it; the head out past her left leg, the haft 30 deg down; a hinge from the hips
        # (the back long); the free arm long and swung back behind her for the counterweight.
        # (Solver 4: the arm carried in front of her breast, not through it: the chest and hips turned further
        # into the blow and the arm aimed well forward, the shoulder drawn forward less; upper arm into her
        # breast 72 -> 38 mm. The haft turned with the arm so the wrist stays near straight.)
        # (Solver 5a, judge r2: committed, and clear of the run's knee. Play shows only the spine up, so the lean is
        # the spine's: 22 deg more pitch and a roll to her left; the fist out before her left thigh, elbow ~160,
        # up off the run's lifted knee; the free hand loose, out from her hip and a little behind it.)
        (5, pose(28, 32 + sy, h5, bl, pole=(-0.9, -0.3, 0.1),
                 off=(0.20, -0.33, 0.16), left_pole=(0.4, -0.2, -0.9), free="relaxed", weight=0.7, pivot=0.7, pitch=26,
                 roll=-14, hinge=14, clav_r=(6, 14), hroll=HR5), "ease"),
        (7, pose(30, 34 + sy, h7, bl, pole=(-0.9, -0.3, 0.2),
                 off=(0.20, -0.33, 0.16), left_pole=(0.4, -0.2, -0.9), free="relaxed", weight=0.8, pivot=0.8, pitch=28,
                 roll=-16, hinge=15, clav_r=(6, 14), hroll=HR7), "ease"),
        (16, pose(7, 12, (0.02, -0.26, 0.24), _n(0.2, 0.6, 0.75), pole=(-0.6, -0.5, -0.4), weight=0.2, pivot=0.2),
         "auto"),
        (26, GUARD, "ease"),
    ]
    if run and RUN_T11:
        # (Over the run the fist finishes higher; on its way back to the guard it would come up through her breast:
        # first it drops, the arm still long, the shoulders unwinding.)
        keys.insert(4, (RUN_T11, pose(24, 28 + sy, RUN_H11, bl, pole=(-0.9, -0.3, 0.2), off=(0.20, -0.33, 0.16),
                                      left_pole=(0.4, -0.2, -0.9), free="relaxed", weight=0.7, pivot=0.7, pitch=24,
                                      roll=-12, hinge=13, clav_r=(6, 12), hroll=HR7 * 0.8), "auto"))
    return keys


def axe_fore(rig):
    """Forehand hack, her right to her left, over the top and down across."""
    return build("axe_fore", rig, _fore_keys(), lead=STRIKE, meta={"layer": "upper", "stance": True, "contact": 2.5 / 30,
                                                                     "weapon": "axe"})


def axe_fore_run(rig):
    """axe_fore as play shows it while she runs (PlayerView.UpperHer): her hips are the run's, not turned into the
    blow, so the cut is re-aimed for them (solver 7a, judge r3 calls 4 and 5): the free fist out before her left
    ribs at the wind-up, not across her belly; the finish further out to her left and higher, beside her left hip
    from the 315 camera, the head trailing outside her thigh. Upper layer only: never her stance."""
    return build("axe_fore_run", rig, _fore_keys(True), lead=STRIKE, meta={"layer": "upper", "contact": 2.5 / 30,
                                                                           "weapon": "axe"})


def _heavy_keys(run=False):
    """axe_heavy's keys; run: the variant play shows over her run (axe_heavy_run)."""
    dh, bl = (RUN_HDH, _n(*RUN_HBL)) if run else ((0, 0, 0), _n(0.75, -0.55, 0.45))
    sy = RUN_HSY if run else 0
    h6 = (0.20 + dh[0], -0.16 + dh[1], 0.44 + dh[2])
    return [
        # (Solver 5a, judge r2: apart from fore's: wound further, arched back, the elbow high and back, the haft
        # laid back so the head drops behind her shoulders.)
        # (Solver 7a, judge r3 call 1: loaded: down onto the back leg, the pelvis over the back foot, wound further
        # and the back arched more.)
        (0, pose(-26 + HV_YAW[0], -54 + HV_YAW[1], (-0.18, 0.28, -0.18), _n(-0.25, 0.3, -0.95), pole=(-0.6, 1.0, -0.6),
                 off=(0.08, -0.06, 0.34), weight=-0.6, pitch=-14 + HV_PITCH, knuckles=(-0.782, 0.412, 0.467),
                 hips_off=HV_OFF), "fast"),
        (3, pose(-6, -8, (-0.02, 0.0, 0.42), _n(0.0, 0.2, 1.0), pole=(-0.6, -0.5, -0.4),
                 off=(0.04, -0.28, 0.16), weight=0.2, pitch=10, knuckles=(-0.211, -0.901, 0.378)), "linear"),
        # (As axe_fore's finish, anim 42, but heavier: 10 deg more hinge, the head lower and further out.)
        # (Solver 4: as fore's, the arm in front of her breast; and apart from fore: the head about 13 cm lower
        # and 15 further out, the haft steeper, the knees deeper, held two frames longer.)
        # (Solver 5a, judge r2: heavier than fore at the finish: the spine 14 deg more pitched, the head lower and
        # further forward; the haft rolled (knuckles) so the head's flat shows to the camera, edge leading, not
        # end-on; the free hand loose, out from her hip.)
        (6, pose(28, 34 + sy, h6, bl, pole=(-0.9, -0.3, 0.1),
                 off=(0.20, -0.28, 0.22), left_pole=(0.4, -0.2, -0.9), free="relaxed", weight=0.8, pivot=0.8, pitch=40,
                 roll=-14, hinge=23, clav_r=(6, 14), crouch=0.07, knuckles=(0.43,-0.15,-0.89), hroll=HH6, hpitch=HP6), "ease"),
        (10, pose(31, 36 + sy, h6, bl, pole=(-0.9, -0.3, 0.2),
                  off=(0.20, -0.28, 0.22), left_pole=(0.4, -0.2, -0.9), free="relaxed", weight=0.9, pivot=0.9,
                  pitch=42, roll=-16, hinge=25, clav_r=(6, 14), crouch=0.07, knuckles=(0.43,-0.15,-0.89),
                  hroll=HH10, hpitch=HP10), "ease"),
        (22, pose(6, 10, (0.0, -0.26, 0.24), _n(0.2, 0.6, 0.75), pole=(-0.6, -0.5, -0.4), weight=0.2, pivot=0.2, knuckles=(-0.005, -0.932, 0.362)),
         "auto"),
        (32, _knuckled(GUARD, (-0.061, -0.857, 0.511)), "ease"),
    ]


def axe_heavy(rig):
    """The axe brought from behind her shoulder, high, and hacked down and
    across in front, the back bending into it."""
    return build("axe_heavy", rig, _heavy_keys(), lead=STRIKE, meta={"layer": "upper", "stance": True,
                                                                     "contact": 3 / 30, "weapon": "axe"})


def axe_heavy_run(rig):
    """axe_heavy over her run (as axe_fore_run): the finish further out to her left and higher."""
    return build("axe_heavy_run", rig, _heavy_keys(True), lead=STRIKE, meta={"layer": "upper", "contact": 3 / 30,
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
              clav_r=(4, 6), roll=0, hroll=0, hpitch=-8):
    """The right hand cutting, the left winding up for its turn."""
    return pose(hips_yaw, spine_yaw, hand, blade, pole=pole, off=idle_hand, left_blade=idle_blade,
                left_pole=(0.8, -0.3, -0.4), weight=weight, pivot=pivot, pitch=pitch, hinge=hinge, clav_r=clav_r,
                roll=roll, hroll=hroll, hpitch=hpitch)


AXES_GUARD = pose(0, 0, (-0.08, -0.24, 0.22), _n(-0.35, 0.75, 0.5), pole=(-0.7, -0.5, -0.4), off=(0.08, -0.24, 0.22),
                  left_blade=_n(0.35, 0.75, 0.5))


def _axes_cut():
    """The right axe's forehand, her right to her left; the left axe drawn
    back for its turn (axes_left plays it mirrored)."""
    return [
        (0, axes_pose(-28, -30, (-0.18, 0.14, 0.10), _n(-0.4, 0.8, -0.45), (-0.8, 0.1, -0.5),
                      (0.12, -0.26, 0.30), _n(0.3, 0.6, 0.75), weight=-0.4), "fast"),
        (2.5, axes_pose(-3, -4, (0.0, -0.06, 0.46), _n(0.15, -0.1, 1.0), (-0.6, -0.7, -0.3),
                        (0.22, -0.20, 0.14), _n(0.5, 0.7, 0.3), weight=0.1, pitch=8), "linear"),
        # (As axe_fore's follow-through, anim 42: the fist across before her left hip, the shoulder rolled after
        # it, the head out past her left leg, a hinge from the hips.)
        # (Solver 4: as axe_fore's, the arm in front of her breast.)
        # (Solver 5a, judge r2: committed as axe_fore's; the idle axe tipped back, its head behind her shoulder,
        # and the guard axe out to the side so its haft clears her face.)
        (5, axes_pose(28, 32, (0.21, -0.12, 0.44), _n(0.45, -0.45, 0.8), (-0.9, -0.3, 0.1),
                      AX_IH, _n(*AX_IB), weight=0.6, pivot=0.6, pitch=26, roll=-14, hinge=14,
                      clav_r=(6, 14), hroll=HR5), "ease"),
        (7, axes_pose(30, 34, (0.235, -0.10, 0.43), _n(0.45, -0.45, 0.8), (-0.9, -0.3, 0.2),
                      AX_IH, _n(*AX_IB), weight=0.7, pivot=0.7, pitch=28, roll=-16, hinge=15,
                      clav_r=(6, 14), hroll=HR7), "ease"),
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
    # (The mirrored stance puts her right foot forward for this one: a step
    # through with the cut. The guard it ends in is mirrored too, so the feet
    # stay planted: the plain guard slid both feet 20 cm to swap them, solver 4.)
    keys = [(t, mirror(p), e) for t, p, e in _axes_cut()] + [(24, mirror(AXES_GUARD), "ease")]
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
                     ("axe_fore_run", axe_fore_run), ("axe_heavy_run", axe_heavy_run),
                     ("axes_right", axes_right), ("axes_left", axes_left), ("axes_heavy", axes_heavy)):
        if want and not any(w in name for w in want):
            continue
        out.append(fn(rig))
    return out
