"""The small things: what she does when nothing is asking anything of her.

- sit_log: the title's stranger by the fire. Forearms on her knees, hands
  loose between them, breathing slow; now and then she looks off down the
  road, and back to the fire, and warms her hands.
- <calling>_show: the flourish when a calling is chosen at creation.
- idle_<calling>_break: every so often, standing: the warden rolls her
  sword shoulder and checks her buckler; the arcanist tucks her hair and
  glances at the sky, turning the staff in her fingers; the reaver rolls
  her neck and spins the axe off her shoulder and back; the stalker looks
  left and right and crouches to read the ground.
- catch_breath: hands on her knees after a hard run.

Breaks and flourishes are laid over the calling's own captured standing
(clips/idle.py), so her weight keeps shifting under them and they leave
and return to the idle's own arms.
"""
from __future__ import annotations

import math
import os

import numpy as np

from clips import idle
from clips.actions import KNEE_Y, TUCK_Y, arm, body, stance
from clips.sword import _n
from gait import arc_of
from keyed import FINGER_PRESETS, build
from rig import qeuler, qinv, qmatrix, qmul, qrot


def feet_of(rig, base, f=0, turn=False):
    """Where the base clip's feet are at a frame, as foot controls (so a
    crouch laid over it keeps them planted). turn: with their turn too (a
    keyed foot is otherwise squared to rest: the stalker's base stands with
    her right toe out 16 deg, and her break's feet snapped 11 deg at its ends)."""
    g, p = rig.sk.fk(base.rot[f][None], base.pos[f][None])
    out = {}
    for side in "lr":
        j = rig.I[f"foot_{side}"]
        a = p[0, j]
        fwd = g[0, j]
        # (Less the body's own widening, which the solver adds back: they already stand where they stand.)
        s = 1 if side == "l" else -1
        out[f"foot_{side}"] = {"pos": (float(a[0]) - s * rig.feet_out, float(a[1] - rig.prest[j][1]), float(a[2]))}
        if turn:
            out[f"foot_{side}"]["rot"] = _euler(qmul(fwd, qinv(rig.grest[j])))
    return out


def _euler(qt):
    """qeuler's (yaw, pitch, roll) for a turn."""
    m = qmatrix(qt)
    pitch = math.asin(max(-1.0, min(1.0, -m[1][2])))
    return (math.degrees(math.atan2(m[0][2], m[2][2])), math.degrees(pitch), math.degrees(math.atan2(m[1][0], m[1][1])))


def arms_of(calling):
    return getattr(idle, calling)(0, 0)


def over(calling, **c):
    """The calling's idle arms with some controls replaced."""
    p = dict(arms_of(calling))
    p.update(c)
    return p


# ------------------------------------------------------------- the fire --
def sit_log(rig):
    """Eight seconds by the fire, looping: two slow breaths, a look off down
    the road and back, the hands rubbed warm."""
    def seat(breath=0.0, look=(0, 0, 0), rub=0.0, lean=26):
        return {
            "hips": {"pos": (0.0, -0.53, -0.33), "rot": (0, -6, 0)},
            "spine": (0, lean + 3 * breath, 0), "neck": (0, -8, 0), "head": look,
            "clav_l": (3 * breath, 3), "clav_r": (3 * breath, 3),
            "foot_l": {"pos": (0.17, 0.0, 0.20), "rot": (12, 0, 0), "pole": (0.3, 0, 1)},
            "foot_r": {"pos": (-0.12, 0.03, 0.08), "rot": (-8, 10, 0), "toe": 15, "pole": (-0.2, 0, 1)},
            # Forearms on the thighs, the hands between the knees.
            "hand_l": {"pos": (0.05 + 0.02 * rub, 0.47, 0.36 + 0.03 * abs(rub)), "pole": (0.6, -0.6, -0.4),
                       "knuckles": (-0.4, -0.3, 0.85)},
            "hand_r": {"pos": (-0.04 - 0.02 * rub, 0.46, 0.35 + 0.03 * abs(rub)), "pole": (-0.6, -0.6, -0.4),
                       "knuckles": (0.4, -0.3, 0.85)},
            "fingers_l": "relaxed", "fingers_r": "relaxed",
        }
    keys = [
        (0, seat(0), "auto"),
        (45, seat(1), "auto"),
        (90, seat(0, look=(6, -4, 0)), "auto"),
        # Off down the road, over her left shoulder.
        (120, seat(0.5, look=(48, 4, 6), lean=22), "ease"),
        (150, seat(0.6, look=(50, 6, 6), lean=22), "ease"),
        (175, seat(0.2, look=(0, -2, 0)), "auto"),
        # Warming her hands.
        (190, seat(0.4, rub=1.0, lean=30), "auto"),
        (196, seat(0.4, rub=-1.0, lean=30), "auto"),
        (202, seat(0.5, rub=1.0, lean=30), "auto"),
        (208, seat(0.5, rub=-1.0, lean=30), "auto"),
        (240, seat(0), "auto"),
    ]
    return build("sit_log", rig, keys, loop=True, meta={"layer": "full"})


# ------------------------------------------------------------ flourishes --
def SHOW_L(at=(-0.07, -0.08, 0.425), pole=(1.0, -0.3, -0.3)):
    """warden_show's shield hand in the guard (chest frame, from the shoulder):
    out ahead with the elbow open (139 deg), so the rim clears her pauldron
    (18 mm) and sits just under and before her chin (60 mm from her head) for the glare
    over it. (Close in and high, at
    (-0.14, -0.13, 0.30), the elbow closed to 99 deg and the rim cut her
    upper arm and pauldron 8/23 mm and came within 16 mm of her face.)"""
    return {"arc": arc_of(at), "pole": pole, "frame": "chest", "blade": _n(-0.2, 0.9, 0.4), "twist": 0.3}


SHOW_R_MID = (-0.24, -0.12, 0.08)


def warden_show(rig):
    """She steps in behind the buckler and levels the sword over its rim at
    you, glaring over it; holds; settles back."""
    base = idle.base_of(rig, "warden")
    f = feet_of(rig, base)
    lf = f["foot_l"]["pos"]
    step = {"foot_l": {"pos": (lf[0], 0.0, lf[2] + 0.22), "rot": (8, 0, 0)}, "foot_r": f["foot_r"],
            "hips": {"pos": (0, -0.08, 0.10), "rot": (-10, 8, 0)}}
    # The sword cocked high over her right shoulder, ready to come over the
    # rim: the fist above the shoulder, the elbow out to the side, the blade
    # back over her shoulder at a slant, its line clear against the sky
    # from the front; her chin up, eyes over the rim. The forearm rises
    # beside her head, never across her face. (Kept low and close in, the
    # arm folded and the forearm came up across her face; pointed at the
    # camera, the blade crossed her face and read as nothing.)
    guard = {**step, "spine": (-8, 8, 0), "head": (12, -10, 0),
             "hand_l": SHOW_L(),
             "hand_r": {"arc": arc_of((-0.14, 0.29, -0.04)), "pole": (-1.0, -0.2, -0.2), "frame": "chest",
                        "blade": _n(0.28, 0.02, 0.96), "twist": 0.5},
             "fingers_l": "fist", "fingers_r": "grip"}
    keys = [
        (0, over("warden"), "auto"),
        (8, over("warden", hips={"pos": (0, -0.05, -0.02)}, foot_l=f["foot_l"], foot_r=f["foot_r"]), "fast"),
        (16, guard, "ease"),
        (50, {**guard, "spine": (-8, 9, 0)}, "ease"),
        # Settling back, the sword comes down close past her side (left to
        # the arc alone, the hand swung 39 cm out at shoulder height and the
        # arm read as locked straight); the body halfway home.
        (60, {"hips": {"pos": (0, -0.04, 0.05), "rot": (-5, 4, 0)}, "spine": (-4, 4.5, 0), "head": (6, -5, 0),
              "hand_r": {"arc": arc_of(SHOW_R_MID), "pole": (-1.0, -0.3, -0.2), "frame": "chest",
                         "blade": _n(0.10, -0.30, 0.95), "twist": 0.5}}, "auto"),
        (70, over("warden"), "ease"),
    ]
    return build("warden_show", rig, keys, base=base, meta={"layer": "full", "weapon": "sword+shield"})


# The staff lifted (f12) and struck down (f18-55), on the idle's frame and aim (idle.ARC_HAND_R, ARC_BLADE_R).
# (Animation 46: in the chest's frame, at 5-8 deg out, the crescent hung before her face from facing 45 the whole time
# it was down.)
SHOW_LIFT = {"arc": arc_of((-0.24, -0.02, 0.23)), "pole": (0.0, -1.0, -0.2), "frame": "char", "blade": _n(-0.28, 1.0, 0.0), "twist": 0.5}
SHOW_STRUCK = {"arc": arc_of((-0.26, -0.28, 0.23)), "pole": (0.0, -1.0, -0.2), "frame": "char", "blade": _n(-0.30, 1.0, -0.06), "twist": 0.5}


def arcanist_show(rig):
    """The staff lifted and struck down on the ground; the free hand rises
    open as if the light came to it; her chin lifts."""
    base = idle.base_of(rig, "arcanist")
    keys = [
        (0, over("arcanist"), "auto"),
        (12, over("arcanist", head=(0, -8, 0),
                  hand_r=SHOW_LIFT,
                  hand_l={"arc": arc_of((0.20, -0.30, 0.14)), "pole": (0.8, -0.4, -0.4), "frame": "chest",
                          "knuckles": _n(0.3, 0.2, 0.9)}, fingers_l="relaxed"), "fast"),
        (18, over("arcanist", spine=(0, 4, 0), head=(-10, -16, 0),
                  hand_r=SHOW_STRUCK,
                  hand_l={"arc": arc_of((0.30, -0.16, 0.22)), "pole": (0.8, -0.6, -0.2), "frame": "chest",
                          "knuckles": _n(0.6, 0.3, 0.75)}, fingers_l="spread"), "ease"),
        (55, over("arcanist", spine=(0, 3, 0), head=(-12, -18, 0),
                  hand_r=SHOW_STRUCK,
                  hand_l={"arc": arc_of((0.32, -0.12, 0.22)), "pole": (0.8, -0.6, -0.2), "frame": "chest",
                          "knuckles": _n(0.6, 0.35, 0.7)}, fingers_l="spread"), "ease"),
        (78, over("arcanist"), "ease"),
    ]
    clip = build("arcanist_show", rig, keys, base=base, meta={"layer": "full", "weapon": "staff", **idle.arc_grip()})
    return idle.hip_layer(rig, clip, lambda f: 1 - idle._smooth(f / 12) if f < 12 else idle._smooth((f - 55) / 23),
                          phase=lambda f: f / (clip.frames - 1))


# (reaver_show keeps the shoulder carry it was judged with, idle.reaver_shoulder; her idle now hangs the axe.)
def _reaver_over():
    """reaver_show's overhead swing as the owner saw it on 21 Oct (soul.py before d2eb0c5c): the wheel up with the
    fist over her brow. Built with REAVER_SHOW_OVER=1 (same clip name) while the owner picks overhead or lowered."""
    return [
        (16, over("reaver_shoulder", spine=(-14, -4, 0),
                  hand_r={"arc": arc_of((-0.26, 0.06, 0.22)), "pole": (-0.9, -0.2, -0.2), "frame": "chest",
                          "blade": _n(-0.5, 0.2, 0.85), "twist": 0.5}), "auto"),
        (24, over("reaver_shoulder", spine=(-6, -10, 0), head=(0, -10, 0),
                  hand_r={"arc": arc_of((-0.10, 0.36, 0.04)), "pole": (-0.8, 0.4, -0.2), "frame": "chest",
                          "blade": _n(-0.1, 0.4, -0.9), "twist": 0.5}), "auto"),
    ]


def reaver_show(rig):
    """The axe swung down off her shoulder, round in a wheel overhead and
    slammed back onto it; her chin up and a grin's worth of swagger."""
    base = idle.base_of(rig, "reaver")
    keys = [
        (0, over("reaver_shoulder"), "auto"),
        (8, over("reaver_shoulder", spine=(-10, 6, 0),
                 hand_r={"arc": arc_of((-0.30, -0.32, 0.10)), "pole": (-0.5, -0.8, 0.0), "frame": "chest",
                         "blade": _n(-0.6, -0.7, 0.3), "twist": 0.5}), "fast"),
    ] + (_reaver_over() if os.environ.get("REAVER_SHOW_OVER") == "1" else [
        # Up before her chest, the haft through upright with the fist still low (armor 18 r2: upright with the fist
        # at her brow put the head out of the close view's top at the peak), then laid back over her shoulder.
        (13, over("reaver_shoulder", spine=(-12, 0, 0),
                  hand_r={"arc": arc_of((-0.26, -0.22, 0.26)), "pole": (-0.8, -0.5, -0.2), "frame": "chest",
                          "blade": _n(-0.42, 0.62, 0.66), "twist": 0.5}), "auto"),
        (17, over("reaver_shoulder", spine=(-14, -4, 0),
                  hand_r={"arc": arc_of((-0.22, -0.15, 0.24)), "pole": (-0.9, -0.3, -0.2), "frame": "chest",
                          "blade": _n(-0.2, 0.92, -0.3), "twist": 0.5}), "auto"),
        (21, over("reaver_shoulder", spine=(-10, -8, 0), head=(0, -6, 0),
                  hand_r={"arc": arc_of((-0.17, 0.08, 0.18)), "pole": (-0.9, -0.15, 0.3), "frame": "chest",
                          "blade": _n(-0.08, 0.4, -0.91), "twist": 0.5}), "auto"),
        (24, over("reaver_shoulder", spine=(-6, -10, 0), head=(0, -10, 0),
                  hand_r={"arc": arc_of((-0.13, 0.23, 0.12)), "pole": (-0.85, -0.05, 0.5), "frame": "chest",
                          "blade": _n(-0.1, 0.45, -0.88), "twist": 0.5}), "auto"),
    ]) + [
        (30, over("reaver_shoulder", hips={"rot": (8, 0, 4)}, spine=(4, -4, 0), head=(-6, -16, -4)), "ease"),
        (60, over("reaver_shoulder", hips={"rot": (8, 0, 4)}, spine=(4, -4, 0), head=(-6, -14, -4)), "ease"),
        (72, over("reaver_shoulder"), "ease"),
    ]
    return build("reaver_show", rig, keys, base=base, meta={"layer": "full", "weapon": "axe"})


def stalker_show(rig):
    """The crossbow up to her eye, sighting across the dark to the left,
    then the right, then down."""
    base = idle.base_of(rig, "stalker")
    # The shoot's sighting (actions.crossbow_shoot): a shooter's stance, the body bladed to her right and the
    # crossbow turned back, upright, the left hand cradling the fore-stock palm up (idle.ride_stock with
    # actions.aim_cradle; on its own keyed arc the upper arm went 3 mm into her chest and the crossbow 10 mm into
    # her left hand). Turned whole to the left and the right by the spine.
    from clips import actions as A
    B = A.AIM_BLADE

    def aim(yaw):
        return over("stalker", spine=(yaw * 0.6 - B, -4, 0), head=(yaw * 0.4 + B, 6, -6),
                    clav_l=A.AIM_CLAV_L, clav_r=A.AIM_CLAV_R,
                    hand_r=arm(A._yawed(A.AIM_R, B), A._yawed(A.AIM_POLE_R, B),
                               knuckles=_n(*A._yawed((0.06, 0.03, 1.0), B)), blade=A.AIM_TOP),
                    hand_l=arm(A._yawed((-0.10, -0.08, 0.40), B), A.AIM_POLE_L_SHOW, knuckles=_n(0.1, -0.2, 1.0)))
    rest = over("stalker", hand_r={**idle.STALKER_HAND_R["hand_r"], "blade": idle.stalker_top(rig)})
    keys = [
        (0, rest, "auto"),
        (12, aim(0), "ease"),
        (26, aim(34), "ease"),
        (38, aim(34), "auto"),
        (54, aim(-34), "ease"),
        (64, aim(-34), "auto"),
        (74, aim(0), "ease"),
        (90, rest, "ease"),
    ]
    return idle.ride_stock(rig, lambda post: build("stalker_show", rig, keys, base=base, post=post,
                                                   meta={"layer": "full", "weapon": "crossbow"}),
                           rel=A.aim_cradle(76, 86, t_in=(2, 12)))


# ----------------------------------------------------------------- breaks --
def _swing_l(abd, flex, reach=0.0):
    """The side-carry left arm swung whole about the shoulder (abduction out,
    flexion forward, degrees), the elbow's bend and the hand on the forearm
    kept: the reach, pole and thumb turn with it (judge 51: lifting by the
    elbow swings the shield's top rim into the pauldron). `reach` (m) opens
    the elbow a little (about 2.5 mm a degree) for its follow-through."""
    h = dict(arms_of("warden")["hand_l"])
    az, el, r = h["arc"]
    a, b = math.radians(abd), math.radians(flex)
    Rz = np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])
    Rx = np.array([[1, 0, 0], [0, math.cos(b), math.sin(b)], [0, -math.sin(b), math.cos(b)]])
    R = Rx @ Rz
    v = np.array([r * math.cos(math.radians(el)) * math.sin(math.radians(az)), r * math.sin(math.radians(el)),
                  r * math.cos(math.radians(el)) * math.cos(math.radians(az))])
    h["arc"] = arc_of(R @ v * (r + reach) / r)
    for k in ("pole", "thumb"):
        if k in h:
            h[k] = tuple(R @ np.array(h[k], float))
    return h


def warden_break(rig):
    base = idle.base_of(rig, "warden")
    # The fist up and forward of the shoulder, so the guard stands in front of
    # it and the flat rests on the pauldron (armscheck, 13 October: at 6 cm
    # down and 18 forward the quillon sank 20 mm into her shoulder).
    shoulder = {"arc": arc_of((0.02, -0.025, 0.215)), "pole": (-0.8, -0.6, 0.0), "frame": "chest",
                "blade": _n(-0.15, 0.5, -0.85), "twist": 0.5}
    # (With the shoulder rolled up under it the blade rides a little lower on
    # the shoulder, so it stays on the pauldron instead of lifting off.)
    rolled = dict(shoulder, arc=arc_of((0.02, -0.03, 0.21)))
    # Halfway up and halfway down, the fist where it passed before the rest
    # moved (keyed, so the lift and the return keep their paths and the wrist
    # does not flip as the target moved), the elbow's way halfway between the
    # carry's and the shoulder's as it was then (the shoulder's, this early,
    # swung the elbow out and rolled the upper arm 11 degrees in a frame).
    passing = dict(shoulder, arc=arc_of((-0.108, -0.242, 0.189)), pole=(-0.6, -0.4, -0.5))
    keys = [
        (0, over("warden"), "auto"),
        # The flat of the blade laid on her shoulder, the shoulder rolled under it.
        (8, over("warden", hand_r=dict(passing, blade=_n(-0.42, 0.78, 0.46))), "auto"),
        (16, over("warden", hand_r=shoulder), "ease"),
        (24, over("warden", hand_r=rolled, clav_r=(10, 6), head=(-8, 0, 6)), "auto"),
        (32, over("warden", hand_r=shoulder, clav_r=(2, -6), head=(-6, 0, 3)), "auto"),
        (40, over("warden", hand_r=rolled, clav_r=(10, 6), head=(-8, 0, 6)), "auto"),
        (48, over("warden", hand_r=shoulder, clav_r=(0, 0)), "ease"),
        # The shield hefted and the shoulder rolled under it, echoing the
        # sword's roll on the other shoulder (judge 50: a "look over the
        # buckler" cannot read with the shield on a hinge-only forearm, its
        # face always away from her). The shoulder shrugs and comes forward,
        # the shield rises off her hip and drops back with its weight, the
        # shoulder rolls back, the fist regrips; then all of it settles into
        # the side carry by f80. The forearm keeps the carry's roll.
        # The clavicle leads (its peak at f54), the arm swung whole about the
        # shoulder trails it to f57; the elbow keeps the carry's bend.
        (54, over("warden", hand_r=shoulder, clav_l=(10, 0), hand_l=_swing_l(6, 3.5, 0.005),
                  head=(8, 6, 0)), "auto"),
        (57, over("warden", hand_r=shoulder, clav_l=(10, 0), hand_l=_swing_l(10, 6, 0.0025),
                  head=(10, 8, 0)), "ease"),
        (64, over("warden", hand_r=shoulder, clav_l=(6, -10), hand_l=_swing_l(2.5, 0, 0.0075),
                  spine=(0, -3, 0), head=(4, -3, 0)), "auto"),
        (72, over("warden", hand_r=shoulder, clav_l=(-2, -2), hand_l=_swing_l(0, 0, 0.006),
                  fingers_l={"curl": 1.05, "cascade": 0.05, "thumb": 1.6, "oppose": 0.9}), "ease"),
        (80, over("warden", hand_r=shoulder), "ease"),
        # (Unkeyed, the fist came down 3 cm higher and further forward than
        # before and the wrist held at its sideways limit, then let go: the
        # hand turned 17 degrees a frame faster in one frame, at f91.)
        (90, over("warden", hand_r=dict(passing, blade=_n(-0.66, 0.59, 0.46))), "auto"),
        (100, over("warden"), "ease"),
    ]
    # The right elbow eases out of the carry's own place (it takes over from
    # the idle): settled with the frames after, the carry's straight arm
    # rolled 8-11 degrees into the lift's in the first frame.
    return build("idle_warden_break", rig, keys, base=base, meta={"layer": "full", "weapon": "sword+shield"}, pin_first={"r": 4})


# The idle's right hand (her character's frame, idle_arcanist's first frame, the grip's blade and knuckles as
# keyed._whole_aims fills them) and the staff's line in it: idle.arc_aim, per ARC_CAND (R1: 10 deg forward, 16 out).
# At the staff's roll peak (brk_c, f60-70, the head up and the brim tipped back) the fist ARC_BRK_OUT further out
# (metres, her right) and the staff ARC_BRK_TIP deg more out, easing back after (the max judge, animation 46, Fix B:
# the blade edge-on, gem and tuft 1-3 cm off her hair from facing 45). A delta on whichever arm ARC_CAND picks.
ARC_BRK_OUT = 0.04
ARC_BRK_TIP = 3.0


def arcanist_break(rig):
    base = idle.base_of(rig, "arcanist")
    tuck = {"pos": (0.13, 1.62, 0.04), "pole": (1.0, 0.2, -0.3), "knuckles": (0.0, 0.5, -0.85)}
    # The staff turning in her fingers: the idle's hand (idle.ARC_HAND_R, in her character's frame) turned about the
    # staff's own line (idle.arc_aim's), so the staff turns in place. (Animation 46: these keys kept the chest-frame aim
    # of 13 Oct, blade (-0.12, 1.0, 0.18), the grip 7 cm back, and swung the crescent back over her face as the idle's
    # was re-aimed off it; turned about the blade instead, the line swung 7 deg in at the peak, over her face from
    # facing 45, and its foot to 73 mm of her leg. `roll`: the turn from the idle's hand; turned the other way past
    # about 10 deg, the staff, on the fist's diagonal, comes round toward her right leg and the crescent before her
    # face from facing 45.)
    from rig import qaxis, qmul
    blade0, knuckles0, line = idle.arc_aim(rig)
    def staff(roll, peak=0.0):
        # (`peak` 0..1: Fix B's share, the fist out along her right and the whole hand turned about her forward.)
        q = qmul(qaxis((0.0, 0.0, 1.0), ARC_BRK_TIP * peak), qaxis(line, roll))
        return {"arc": arc_of(np.array(idle.ARC_HAND_R) + (-ARC_BRK_OUT * peak, 0.0, 0.0)), "pole": idle.ARC_POLE_R,
                "frame": "char", "blade": tuple(qrot(q, np.array(blade0))), "knuckles": tuple(qrot(q, np.array(knuckles0))),
                "twist": 0.6}
    if rig.body == "him":
        # His: a hand to the back of his neck, kneading it, the head rolled
        # forward and aside into it.
        neck = rig.prest[rig.I["neck_01"]]
        rub = {"pos": (0.05, float(neck[1]) + 0.02, float(neck[2]) - 0.10), "pole": (1.0, 0.4, 0.2), "knuckles": (-0.3, 0.3, 0.9)}
        first = (18, over("arcanist", hand_l=rub, head=(-4, 12, -6), fingers_l="relaxed"), "ease")
        second = (28, over("arcanist", hand_l={**rub, "pos": (0.02, float(neck[1]) + 0.04, float(neck[2]) - 0.11)}, head=(-6, 14, -10)), "ease")
    else:
        # A strand tucked behind her ear: the hand comes up before her
        # shoulder, fingers up, palm to her, then back over the ear (it turns
        # on the way, not at the top).
        # The elbow low and forward of the shoulder (not out level with the hand), so the forearm rises to the ear and
        # the wrist stays near straight (it bent 55-65 deg back with the elbow out: the owner, 14 October, "her hands
        # ... going at a very weird angle at the wrists"); the fingers soft and graded, the index leading.
        tuck = {"pos": (0.1109, 1.6728, -0.0495), "pole": (0.3, -0.75, 0.6), "knuckles": (-0.1005, 0.6249, -0.7742),
                "blade": (0.0391, -0.7750, -0.6307)}
        tuck2 = {**tuck, "pos": (0.1201, 1.6613, -0.0747), "knuckles": (-0.0781, 0.6320, -0.7710), "blade": (0.0314, -0.7714, -0.6356)}
        # (Thumb drawn in 22, not 28: at 28 her glove's thumb sleeve sank up to 9.8 mm into her hand at the index's
        # base, 13 points, f15-34; at 22 none within 4 mm. Animation 33, outfits s27's thumb-hole flap.)
        soft = {"thumb": 0.1, "oppose": 0.05, "thumb_in": 22, "thumb_roll": -23.6,
                "bends": {"index": [10, 22, 11], "middle": [15, 25, 12.5], "ring": [20, 27, 13.5], "pinky": [24, 27, 13.5],
                          "thumb": [0.5, 12, 20]},
                "spreads": {"index": -13.35, "middle": 0.0, "ring": 10, "pinky": 30}}
        first = (18, over("arcanist", hand_l=tuck, head=(-6, 4, 8), fingers_l=soft), "ease")
        second = (28, over("arcanist", hand_l=tuck2, head=(-6, 4, 8), fingers_l=soft), "ease")
        # Out of her hair before it drops (eased down from behind the ear, the fingertips went 9 mm into her head).
        lift = (31, over("arcanist", hand_l={**tuck2, "pos": (0.1519, 1.6416, -0.0674)}, fingers_l=soft), "auto")
    # Up beside her face, not before it (the fingers stay 6 cm or more out from her mouth), the wrist easing
    # straight on the way (extension 55 -> 27 deg, no flick back; tools: scratch tuck/wrist.py, facecheck.py), and
    # down the same way to the hip.
    h9 = {"pos": (0.2100, 1.4001, 0.1100), "pole": (0.6, -0.7, 0.4), "knuckles": (-0.2910, 0.4774, 0.8289), "blade": (-0.1065, 0.8448, -0.5233)}
    rising = (9, over("arcanist", hand_l=h9, fingers_l="relaxed"), "auto")
    h41 = {"pos": (0.2100, 1.3601, 0.0800), "pole": (0.6, -0.7, 0.4), "knuckles": (-0.3434, 0.4529, 0.8226), "blade": (-0.0956, 0.8544, -0.5096)}
    # The drop from her head to her chest over 10 frames, not 5 (it ran 30 cm in 5, 8.7 cm a frame: lead 31's tuck
    # judge), so the staff's turn and the hand's landing on her hip come 5 frames later for her.
    lowering = (41, over("arcanist", hand_l=h41, fingers_l="relaxed"), "auto")
    # Wrist keys on the way up and down, and h9/h41 aimed in full: between the keys the hand bent 21-22 deg sideways
    # (lead 31's tuck judge); now 11-12 at most from f9 to the chest key (tools: scratch anim/l32/try.sh, speed.py).
    w12 = (12, {"hand_l": {"pos": (0.1843, 1.4708, 0.0686), "pole": (0.5, -0.72, 0.47), "knuckles": (-0.2388, 0.8157, 0.5267), "blade": (-0.0682, 0.5268, -0.8464)}}, "auto")
    w15 = (15, {"hand_l": {"pos": (0.1516, 1.6022, -0.0232), "pole": (0.42, -0.73, 0.53), "knuckles": (-0.1495, 0.8269, -0.5420), "blade": (0.0529, -0.5406, -0.8388)}}, "auto")
    w36 = (36, {"hand_l": {"pos": (0.1912, 1.4792, 0.0170), "pole": (0.45, -0.72, 0.5), "knuckles": (-0.2001, 0.9279, 0.3144), "blade": (-0.0365, 0.3134, -0.9481)}}, "auto")
    w39 = (39, {"hand_l": {"pos": (0.2066, 1.3838, 0.0674), "pole": (0.55, -0.71, 0.43), "knuckles": (-0.2865, 0.5744, 0.7666), "blade": (-0.0990, 0.7780, -0.6193)}}, "auto")
    d = 0 if rig.body == "him" else 5
    if idle.ARC_ST and rig.body != "him":
        # (Animation 48, the restaged stand: her head stands 9-12 cm further forward than on R1's Strutting take and
        # her shoulders 8-10, so these keys, made in her character's frame on R1, sat the hand behind her ear 10 cm
        # back in her hair and collar (the reaver's outfit 30 mm into the forearm, f11-38) and took it through her
        # breast on the way down (9 mm, f39-42). Each carried rigidly from R1's base to this one at its own frame:
        # by her head where it is up at her ear, by her chest below.)
        r1 = idle.base_r1(rig)
        g1, p1 = rig.sk.fk(r1.rot, r1.pos)
        g2, p2 = rig.sk.fk(base.rot, base.pos)

        def carried(key):
            fr, spec, ease = key
            h = dict(spec["hand_l"])
            j = rig.I["Head" if h["pos"][1] > 1.55 else "spine_03"]
            dq = qmul(g2[fr, j], qinv(g1[fr, j]))
            h["pos"] = tuple(float(x) for x in p2[fr, j] + qrot(dq, np.array(h["pos"]) - p1[fr, j]))
            for k in ("pole", "knuckles", "blade"):
                if k in h:
                    h[k] = tuple(float(x) for x in qrot(dq, np.array(h[k], float)))
            return (fr, dict(spec, hand_l=h), ease)
        rising, w12, w15, first, second, lift, w36, w39, lowering = (
            carried(k) for k in (rising, w12, w15, first, second, lift, w36, w39, lowering))
    keys = [
        (0, over("arcanist"), "auto"),
        *([rising, w12, w15] if rig.body != "him" else []),
        first,
        second,
        *([lift, w36, w39, lowering] if rig.body != "him" else []),
        # Up at the sky, the staff turning in her fingers.
        (44 + d, over("arcanist", head=(10, -24, 0), hand_r=staff(-40)), "ease"),
        (60 + d, over("arcanist", head=(14, -26, 0), hand_r=staff(5, peak=1.0)), "auto"),
        (74 + d, over("arcanist", head=(8, -20, 0), hand_r=staff(-25)), "ease"),
        (100, over("arcanist"), "ease"),
    ]
    clip = build("idle_arcanist_break", rig, keys, base=base, meta={"layer": "full", "weapon": "staff", **idle.arc_grip()})
    # The hand on her hip as it leaves and from where it is back (f44 on it floated 3-10 mm in the chest's frame).
    # (On a restaged stand, idle.ARC_ST, the idle's free hand instead, its fingers' slow life one round over the clip,
    # so both ends meet the idle's first frame.)
    return idle.hip_layer(rig, clip, lambda f: 1 - idle._smooth(f / 9) if f < 9 else idle._smooth((f - 36 - d) / 8),
                          phase=lambda f: f / (clip.frames - 1))


def reaver_break(rig):
    base = idle.base_of(rig, "reaver")
    def spin(a):
        # The axe rocked over and back in the fist by the forearm's roll, the
        # wrist straight, its head sweeping round her fist and back: a twirl.
        # (Keyed as a wheel spun twice round, it asked the hand to turn a
        # full turn about the haft, which no wrist can; the hand rolled over
        # in a frame.)
        r = math.radians(a)
        return {"arc": arc_of((-0.16, -0.24, 0.30)), "pole": (-0.8, -0.4, -0.2), "frame": "chest",
                "thumb": (-math.sin(r), math.cos(r), 0.2), "twist": 0.7}
    keys = [
        (0, over("reaver"), "auto"),
        # Her neck rolled, slow, a crack at the end of it.
        (10, over("reaver", head=(0, 16, 14)), "auto"),
        (18, over("reaver", head=(14, 4, 0)), "auto"),
        (26, over("reaver", head=(0, -14, -14)), "auto"),
        (32, over("reaver", head=(-10, 0, 0)), "ease"),
        # The axe off her shoulder and twirled in the fist, over and back, twice. (27 Oct: +-64-68, not +-70-75: with the
        # fist higher on the haft the wrist turned 30-32 deg in a frame at the turns, past the audit's 30.)
        (40, over("reaver", hand_r=spin(-68)), "auto"),
        (45, over("reaver", hand_r=spin(64)), "auto"),
        (50, over("reaver", hand_r=spin(-64)), "auto"),
        (55, over("reaver", hand_r=spin(64)), "auto"),
        (60, over("reaver", hand_r=spin(-40)), "auto"),
        (64, over("reaver", hand_r=spin(10)), "auto"),
        (70, over("reaver", hips={"rot": (6, 0, 3)}), "ease"),
        # Shaking out the left hand.
        (78, over("reaver", hand_l={"arc": arc_of((-0.04, -0.40, 0.10)), "pole": (0.4, 0, -1), "frame": "chest"},
                  fingers_l="relaxed"), "auto"),
        (82, over("reaver", hand_l={"arc": arc_of((-0.04, -0.36, 0.12)), "pole": (0.4, 0, -1), "frame": "chest"},
                  fingers_l="spread"), "auto"),
        (100, over("reaver"), "ease"),
    ]
    return build("idle_reaver_break", rig, keys, base=base, meta={"layer": "full", "weapon": "axe", **idle.axe_grip()})


def _vpath(pts, fr):
    """A shoulder-relative vector along keyed points [(frame, vector)], eased between each pair (smoothstep), the
    direction turned on the sphere and the length drawn straight."""
    if fr <= pts[0][0]:
        return np.array(pts[0][1], float)
    for (f0, a), (f1, b) in zip(pts, pts[1:]):
        if fr <= f1:
            u = idle._smooth((fr - f0) / (f1 - f0))
            a, b = np.array(a, float), np.array(b, float)
            na, nb = np.linalg.norm(a), np.linalg.norm(b)
            ua, ub = a / na, b / nb
            om = math.acos(max(-1.0, min(1.0, float(ua @ ub))))
            d = ua if om < 1e-6 else (math.sin((1 - u) * om) * ua + math.sin(u * om) * ub) / math.sin(om)
            return d * (na + (nb - na) * u)
    return np.array(pts[-1][1], float)


def _arc_vec(spec):
    az, el, r = (math.radians(spec["arc"][0]), math.radians(spec["arc"][1]), spec["arc"][2])
    return np.array([math.sin(az) * math.cos(el), math.sin(el), math.cos(az) * math.cos(el)]) * r


def _pchip(pts, fr):
    """A place along (frame, vector) points, monotone between them (no overshoot past a point, so a held place
    stays held)."""
    xs = np.array([p[0] for p in pts], float)
    ys = np.array([np.asarray(p[1], float) for p in pts])
    if fr <= xs[0]:
        return ys[0]
    if fr >= xs[-1]:
        return ys[-1]
    h = np.diff(xs)
    d = np.diff(ys, axis=0) / h[:, None]
    m = np.zeros_like(ys)
    for k in range(1, len(xs) - 1):
        a, b = d[k - 1], d[k]
        w1, w2 = 2 * h[k] + h[k - 1], h[k] + 2 * h[k - 1]
        with np.errstate(divide="ignore", invalid="ignore"):
            m[k] = np.where(a * b > 0, (w1 + w2) / (w1 / a + w2 / b), 0.0)
    k = int(np.searchsorted(xs, fr) - 1)
    t = (fr - xs[k]) / h[k]
    h00, h10, h01, h11 = 2 * t ** 3 - 3 * t ** 2 + 1, t ** 3 - 2 * t ** 2 + t, -2 * t ** 3 + 3 * t ** 2, t ** 3 - t ** 2
    return h00 * ys[k] + h10 * h[k] * m[k] + h01 * ys[k + 1] + h11 * h[k] * m[k + 1]


def stalker_break(rig):
    base = idle.base_of(rig, "stalker")
    f = feet_of(rig, base, turn=True)
    sk, I = rig.sk, rig.I
    # Down on one knee to read the ground (animation 39: the heel-squat she had, hips behind her heels and the back
    # near flat, read from the play camera in a thong cut as crouching to relieve herself, the head hunched down).
    # The right foot steps back onto its tucked toes and the right knee goes down; the left foot stays planted ahead,
    # its shin near upright; the pelvis under her shoulders, the back near upright, the head up and scanning. The
    # pelvis is placed in her space (the base's own sway taken out, so the knee holds still on the ground), the knee
    # a thigh's length below the solved hip, the foot a shin's length behind it.
    def base_pelvis(fr):
        fr = min(fr, base.frames - 1)
        g, p = sk.fk(base.rot[fr][None], base.pos[fr][None])
        return p[0, I["pelvis"]]

    kneel = {"hips": {"rot": BREAK_HIPS_ROT}, "spine": BREAK_SPINE, "neck": BREAK_NECK, "head": BREAK_HEAD,
             "foot_l": f["foot_l"], "foot_r": f["foot_r"]}
    BOT = 81
    bot = dict(kneel, hips={"pos": tuple(np.subtract(BREAK_PELVIS, base_pelvis(BOT))), "rot": BREAK_HIPS_ROT})
    local, pos = rig.solve(bot, base=(base.rot[BOT], base.pos[BOT]))
    gq, gp = sk.fk(local[None], pos[None])
    gq, gp = gq[0], gp[0]
    hip = gp[I["thigh_r"]]
    L = float(np.linalg.norm(rig.prest[I["calf_r"]] - rig.prest[I["thigh_r"]]))
    S = float(np.linalg.norm(rig.prest[I["foot_r"]] - rig.prest[I["calf_r"]]))
    kx = BREAK_KNEE_X
    knee = np.array([kx, KNEE_Y, hip[2] - math.sqrt(max(L * L - (hip[1] - KNEE_Y) ** 2 - (hip[0] - kx) ** 2, 1e-6))])
    ankle_b = np.array([kx, TUCK_Y, knee[2] - math.sqrt(max(S * S - (TUCK_Y - KNEE_Y) ** 2, 1e-6))])

    # The right foot's way (its ball's place, the foot's pitch and the toes' bend): heel up, swung back and set down
    # on the ball, the toes tucked under; and back the same way. The ball never moves while it carries her.
    rest_a = rig.prest[I["foot_r"]]
    ball_off = rig.prest[I["ball_r"]] - rest_a
    yaw, p0, roll = f["foot_r"]["rot"]
    home_a = np.array([f["foot_r"]["pos"][0] - rig.feet_out, rest_a[1] + f["foot_r"]["pos"][1], f["foot_r"]["pos"][2]])

    def ball_of(a, pitch):
        return a + qrot(qeuler(yaw, pitch, roll), ball_off)
    home_b, bot_b = ball_of(home_a, p0), ball_of(ankle_b, TUCK_PITCH)

    def swing(t):
        # (Lifted straight up first and set straight down last: a foot that arrived along the ground slid 3 cm.)
        return idle._smooth((t - 0.15) / 0.7)

    def right(fr):
        """(ball, pitch, toe) of the right foot at a frame."""
        (h0, h1), (s0, s1), (r0, r1) = R_HEEL, R_BACK, R_HOME
        if fr <= h0 or fr >= r1:
            return home_b, p0, 0.0
        if fr <= h1:
            u = idle._smooth((fr - h0) / (h1 - h0))
            return home_b, p0 + 25 * u, 25 * u
        if fr <= s1:
            t = (fr - s0) / (s1 - s0)
            u = swing(t)
            b = home_b + (bot_b - home_b) * u + np.array([0, 0.07 * math.sin(math.pi * t), 0])
            return b, p0 + 25 + (TUCK_PITCH - p0 - 25) * u, 25 + (TUCK_TOE - 25) * u
        if fr <= r0:
            return bot_b, TUCK_PITCH, TUCK_TOE
        t = (fr - r0) / (r1 - r0)
        u = swing(t)
        b = bot_b + (home_b - bot_b) * u + np.array([0, 0.05 * math.sin(math.pi * t), 0])
        return b, TUCK_PITCH + (p0 - TUCK_PITCH) * u, TUCK_TOE * (1 - u) ** 2

    # The pelvis's way (her space): the weight onto the left foot, down and back onto the right knee, held; forward
    # over the left foot, the knee up, and up as the right foot comes home.
    pel = [(R_HEEL[0], base_pelvis(R_HEEL[0])), (R_HEEL[1], base_pelvis(R_HEEL[1]) + np.array((0.02, -0.03, 0.0))), (R_BACK[1], BREAK_DOWN),
           (R_DOWN, BREAK_PELVIS), (90, BREAK_PELVIS), (R_HOME[0], BREAK_OFF), (R_HOME[1], BREAK_UP),
           (R_STAND, base_pelvis(R_STAND))]

    # (The left hand: laid on her left thigh in post, knee_hand.)
    crouch = {**kneel,
              # The crossbow held low ahead of her, off the ground and clear of her thighs and left shin.
              "hand_r": {"arc": arc_of(BREAK_HAND_R), "pole": (-0.7, -0.4, -0.5), "frame": "chest",
                         "knuckles": idle._n(BREAK_AIM_R), "twist": 0.5}}
    keys = [
        (0, over("stalker", **f), "auto"),
        (14, over("stalker", **f, spine=(22, 0, 0), head=(40, 2, 0)), "ease"),
        (28, over("stalker", **f, spine=(24, 0, 0), head=(44, 4, 0)), "ease"),
        (44, over("stalker", **f, spine=(-22, 0, 0), head=(-40, 2, 0)), "ease"),
        (56, over("stalker", **f, spine=(-24, 0, 0), head=(-44, 4, 0)), "ease"),
        # Down on her right knee, reading the ground ahead, the head turning across it.
        (R_BACK[1], over("stalker", **{**crouch, **BREAK_LEAN}), "ease"),
        (R_DOWN, over("stalker", **crouch), "ease"),
        (90, over("stalker", **{**crouch, "head": BREAK_HEAD_TO}), "ease"),
        (R_HOME[0], over("stalker", **{**crouch, **BREAK_LEAN, "head": BREAK_HEAD_TO}), "ease"),
        (R_STAND, over("stalker", foot_l=f["foot_l"], foot_r=f["foot_r"]), "ease"),
        (120, over("stalker", **f), "ease"),
    ]
    # The hands' own timing through the fold (animation 38): the left hand comes up and off the fore-stock (out to
    # her left) before the crossbow moves, is laid along her left thigh as she sinks, and is laid back on the stock
    # only once the crossbow is home again (the crossbow had swung up through the resting hand, 17 mm into her thumb).
    hl, hr = idle.STALKER_HAND_L["hand_l"], idle.STALKER_HAND_R["hand_r"]
    V0 = _arc_vec(hl)
    V1 = V0 + np.array(STALKER_LIFT_L)
    R0, RC = _arc_vec(hr), _arc_vec(crouch["hand_r"])
    # (Off the stock and back onto it along the idle's own lift; between, laid on her left thigh: see knee_hand.)
    left = [(55, V0), (59, V1), (108, V1), (114, V0)]
    # (The crossbow brought forward first, off her right thigh as it comes up.)
    RW = R0 + np.array(BREAK_FWD_R)
    right_h = [(56, R0), (61, RW), (72, RC), (90, RC), (101, RW), (110, R0)]

    def mixv(a, b, w):
        v = np.array(a, float) * (1 - w) + np.array(b, float) * w
        return tuple(float(x) for x in v / np.linalg.norm(v))

    def ramp(pts, fr):
        if fr <= pts[0][0]:
            return pts[0][1]
        for (f0, a), (f1, b) in zip(pts, pts[1:]):
            if fr <= f1:
                return a + (b - a) * idle._smooth((fr - f0) / (f1 - f0))
        return pts[-1][1]

    aim_r = (knee - (hip + ankle_b) / 2) * 10
    up, out_x = np.array((0.0, 1.0, 0.0)), np.array((1.0, 0.0, 0.0))

    def unit(v):
        return v / np.linalg.norm(v)

    def knee_hand(fr, pose):
        """The left hand laid along the top-outer left thigh at a frame (animation 39, judge r2: the hand that hung
        beside the knee swung 30 cm out round it and did nothing at the bottom): the wrist's place in her space and
        the hand's knuckles and blade in the chest's frame, from her legs as solved at that frame. The palm rides
        forward along the thigh as the knee rises and lies on the kneecap at the bottom, on the thickest outfit's
        surface (PALM_R: the thigh's bone line to it), and slides back the same way."""
        b = min(fr, base.frames - 1)
        loc, ps = rig.solve(pose, base=(base.rot[b], base.pos[b]))
        q, p = sk.fk(loc[None], ps[None])
        q, p = q[0], p[0]
        th, kn = p[I["thigh_l"]], p[I["calf_l"]]
        u = unit(kn - th)
        t, lift = ramp(KNEE_T, fr), ramp(KNEE_LIFT, fr)
        n = up + out_x * (KNEE_OUT[0] + (KNEE_OUT[1] - KNEE_OUT[0]) * t)
        n = unit(n - u * (n @ u))
        c = th + (kn - th) * t + n * (float(np.interp(t, *zip(*PALM_R))) + lift)
        a = math.radians(float(np.interp(t, *zip(*PALM_TILT))))
        y = unit(u * math.cos(a) - n * math.sin(a))
        z = np.cross(-n, y)
        wrist = c - y * PALM_FWD + n * PALM_UP
        ch = qmul(q[I["spine_03"]], qinv(rig.grest[I["spine_03"]]))
        return wrist, qrot(qinv(ch), y), qrot(qinv(ch), z)

    def post(fr, pose):
        if not R_HEEL[0] <= fr <= 114:
            return pose
        pose = dict(pose)
        if R_HEEL[0] <= fr <= R_STAND:
            hips = dict(pose.get("hips", {}))
            hips["pos"] = tuple(float(x) for x in np.subtract(_pchip(pel, fr), base_pelvis(fr)))
            pose["hips"] = hips
            b, pitch, toe = right(fr)
            a = b - qrot(qeuler(yaw, pitch, roll), ball_off)
            k = ramp(KNEE_AIM, fr)
            pose["foot_r"] = {"pos": (float(a[0]) + rig.feet_out, float(a[1] - rest_a[1]), float(a[2])),
                              "rot": (yaw, float(pitch), roll), "toe": float(toe),
                              # The knee's way turned onto its place on the ground as she goes down (and back).
                              "pole": tuple(float(x) for x in np.array((-0.15, 0, 1.0)) * (1 - k) + aim_r * k)}
        w, wt = ramp(KNEE_MIX, fr), ramp(KNEE_TURN, fr)
        hand_l = {"arc": arc_of(_vpath(left, fr)), "frame": "chest", "pole": hl["pole"], "knuckles": hl["knuckles"],
                  "blade": hl["blade"], "twist": 0.4}
        if w > 0 or wt > 0:
            wrist, yk, zb = knee_hand(fr, pose)
            hand_l.update(pos=tuple(float(x) for x in wrist), mix=float(w), pole=mixv(hl["pole"], KNEE_POLE, wt),
                          knuckles=mixv(hl["knuckles"], yk, wt), blade=mixv(hl["blade"], zb, wt))
        pose["hand_l"] = hand_l
        # (The fingers soft throughout, curled a little further over the kneecap.)
        pose["fingers_l"] = dict(FINGER_PRESETS["relaxed"], curl=float(ramp(KNEE_CURL, fr)))
        pose["hand_r"] = dict(hr, arc=arc_of(_vpath(right_h, fr)),
                              knuckles=mixv(hr["knuckles"], crouch["hand_r"]["knuckles"], ramp([(58, 0.0), (72, 1.0), (90, 1.0), (110, 0.0)], fr)))
        return pose
    return build("idle_stalker_break", rig, keys, base=base, post=post, meta={"layer": "full", "weapon": "crossbow"})


# The break's kneel (her space, m and deg): the pelvis at the bottom (over her right knee, under her shoulders, a
# thigh's length behind her left knee), the right knee's side place, the hips', back's and head's turns there, the
# crossbow hand's at the bottom and on its way out (chest frame, from the shoulder; the way out off the idle's), its
# knuckles' aim (a crossbow aimed across her went 7-21 mm into her left shin), the tucked right foot's pitch. KNEE_AIM: how far the right knee's pole
# is turned onto its place.
BREAK_PELVIS = (0.02, 0.545, -0.38)
BREAK_KNEE_X = -0.10
BREAK_HIPS_ROT = (0, 4, 0)
BREAK_SPINE = (0, 8, 0)
BREAK_NECK = (0, 2, 0)
BREAK_HEAD = (-10, 15, 0)
BREAK_HEAD_TO = (12, 17, 0)
BREAK_FWD_R = (-0.12, 0.09, 0.06)
BREAK_HAND_R = (-0.06, -0.30, 0.32)
BREAK_AIM_R = (-0.10, 0.45, 0.88)
TUCK_PITCH = 50.0
TUCK_TOE = TUCK_PITCH + 4  # (the toes near level along the ground; get_up's 64 lifts them 14 deg)
# Her lean over the left foot going down and coming up, and the pelvis as the right foot sets down behind her, as
# the knee leaves the ground (the back leg near straight) and as the foot comes home.
BREAK_LEAN = {"hips": {"rot": (0, 12, 0)}, "spine": (0, 16, 0)}
BREAK_DOWN, BREAK_OFF, BREAK_UP = (0.01, 0.75, -0.23), (0.02, 0.76, -0.20), (0.03, 0.97, -0.04)
# The left hand on the thigh (her space, m and deg): how far it is laid there (from the idle's lift off the stock),
# where along the thigh (0 hip, 1 knee joint), the palm's height over the thickest outfit's surface, the thigh's
# top-outer side (how far the normal leans out, at the hip and at the knee), the bone line to that surface (at the
# hip and at the knee), the fingers' tilt down over the knee's front, the wrist behind and above the palm's middle,
# the elbow's way (chest frame: out and back) and the fingers' curl.
KNEE_MIX = [(59, 0.0), (64, 1.0), (101, 1.0), (108, 0.0)]
KNEE_TURN = [(58, 0.0), (62, 1.0), (101, 1.0), (107, 0.0)]
KNEE_T = [(60, 0.30), (70, 1.04), (90, 1.04), (97, 0.62), (105, 0.30)]
KNEE_LIFT = [(59, 0.06), (63, 0.032), (66, 0.032), (69, 0.025), (75, 0.013), (90, 0.013), (95, 0.038), (104, 0.04)]
KNEE_OUT = (0.6, 0.75)
PALM_R = [(0.3, 0.165), (0.4, 0.162), (0.5, 0.133), (0.6, 0.120), (0.7, 0.109), (0.8, 0.096), (0.85, 0.106), (0.9, 0.092),
          (0.95, 0.090), (1.0, 0.083), (1.05, 0.070)]
PALM_TILT = [(0.3, 8.0), (0.8, 10.0), (1.04, 16.0)]
PALM_FWD, PALM_UP = 0.045, 0.041
KNEE_POLE = (0.45, -0.3, -0.85)
KNEE_CURL = [(55, 0.1), (57, 0.0), (60, 0.0), (66, 0.1)]
# The right foot's frames: heel up, swung back to its toes, and home (from, to); the knee down, and up standing.
R_HEEL, R_BACK, R_HOME = (54, 57), (57, 67), (97, 108)
R_DOWN, R_STAND = 73, 114
KNEE_AIM = [(57, 0.0), (67, 1.0), (97, 1.0), (104, 0.0)]
# The left hand lifted off the fore-stock on the way (chest frame, m: up and out to her left of the idle's).
STALKER_LIFT_L = (0.05, 0.05, 0.0)


# The relaxed hand closing a little as it comes down off her hair.
SOFT = {**FINGER_PRESETS["relaxed"], "curl": 0.2}


def catch_breath(rig):
    """Hands down onto her knees, the back heaving with three hard breaths,
    then up, a hand pushing the hair back.

    Played with both hands empty only (logic/Play/FreeHand.cs, armor 18 r2): a shield swung across her head and
    throat, and any held piece went through her thigh on the knee, so the hands are relaxed, not gripping.

    Hands and head are placed from the body's own knees and head (hers are
    narrower and lower than the hero's)."""
    # How much further out the knees are, and the head higher and forward, than hers.
    kx = float(rig.prest[rig.I["calf_l"]][0]) + 0.6 * rig.feet_out - 0.103
    head = rig.prest[rig.I["Head"]]
    hy, hz = float(head[1]) - 1.666, float(head[2]) + 0.036

    def bent(b, up=0.0):
        return {
            "hips": {"pos": (0, -0.14 + 0.1 * up, -0.08), "rot": (0, 18 - 14 * up, 0)},
            "spine": (0, 30 - 26 * up + 5 * b, 0), "neck": (0, -18 + 10 * up, 0), "head": (0, -12 + 6 * up - 4 * b, 0),
            "clav_l": (6 * b, 2), "clav_r": (6 * b, 2),
            "foot_l": {"pos": (0.16, 0, 0.06), "rot": (10, 0, 0)}, "foot_r": {"pos": (-0.17, 0, -0.04), "rot": (-12, 0, 0)},
            "hand_l": {"pos": (0.12 + kx, 0.56, 0.24), "pole": (0.9, 0.2, -0.3), "knuckles": (0.2, -0.6, 0.75)},
            "hand_r": {"pos": (-0.13 - kx, 0.55, 0.22), "pole": (-0.9, 0.2, -0.3), "knuckles": (-0.2, -0.6, 0.75)},
            "fingers_l": "relaxed", "fingers_r": "relaxed",
        }
    # The hair pushed back along the side of her head, not over the top: the
    # wrist at her jaw, the fingers up into the hair at her brow and hairline and swept
    # back over her ear, the elbow forward and down (over the top the upper
    # arm went 27 degrees above level, the armpit opened to the camera). Armor 18 r2 (judge RJ1): the sweep starts
    # at her brow, not the corner of her eye; her head tips into the hand; the push ends with the fingers at the side
    # of her head above the ear, not behind it (the elbow 10-15 deg more open: no pinch inside it).
    hand_r = arm((0.02, -0.36, 0.10), (-0.6, -0.4, -0.5))
    temple = body(stance(0.05), spine=(0, 3, 0), neck=(0, 0, -3), head=(3, 2, -8),
                  hand_l={"pos": (0.135, 1.556 + hy, 0.11 + hz), "pole": (0.5, -0.8, 0.5), "knuckles": (0.0, 0.97, 0.25)},
                  hand_r=hand_r, fingers_l="relaxed", fingers_r="relaxed")
    upright = body(stance(0.05), spine=(0, 2, 0), neck=(0, 0, -3), head=(-2, -8, -7),
                   hand_l={"pos": (0.124, 1.582 + hy, 0.09 + hz), "pole": (0.5, -0.85, 0.4), "knuckles": (0.3, 0.75, -0.6)},
                   hand_r=hand_r, fingers_l="relaxed", fingers_r="relaxed")
    keys = [
        (0, body(stance(0.06), spine=(0, 8, 0), hand_l=arm((-0.02, -0.34, 0.12), (0.6, -0.4, -0.5)),
                 hand_r=arm((0.02, -0.34, 0.12), (-0.6, -0.4, -0.5)), fingers_l="relaxed", fingers_r="relaxed"), "auto"),
        (12, bent(1), "auto"),
        (24, bent(-0.6), "auto"),
        (36, bent(1), "auto"),
        (48, bent(-0.6), "auto"),
        (60, bent(0.9), "auto"),
        (74, bent(-0.3, up=0.4), "auto"),
        # Up off the knee, the hand rising before her chest, fingers up, palm
        # toward her, before it goes into her hair (it turns over on the way,
        # not in a flick at the top).
        (86, body(stance(0.05), spine=(0, 6, 0), head=(-4, 0, 2),
                  hand_l={"pos": (0.13, 1.30 + hy, 0.22 + hz), "pole": (0.9, -0.2, -0.3), "knuckles": (0.05, 0.9, 0.35)},
                  hand_r=hand_r, fingers_l="relaxed", fingers_r="relaxed"), "auto"),
        (93, temple, "auto"),
        (99, upright, "ease"),
        # Off her hair: the elbow drops toward her ribs first, the hand trailing by her jaw, then down round the
        # front of her (clear of her breast), the fingers softening closed.
        (103, body(stance(0.05), spine=(0, 3, 0), neck=(0, 0, -1), head=(-3, -5, -3),
                   hand_l={"pos": (0.165, 1.47 + hy, 0.14 + hz), "pole": (0.15, -1.0, 0.05), "knuckles": (-0.05, 0.85, 0.5)},
                   hand_r=hand_r, fingers_l="relaxed", fingers_r="relaxed"), "auto"),
        (108, body(stance(0.05), spine=(0, 3, 0), head=(-3, -2, 1),
                   hand_l={"pos": (0.165, 1.31 + hy, 0.22 + hz), "pole": (0.45, -0.9, -0.1), "knuckles": (0.05, 0.25, 0.97)},
                   hand_r=hand_r, fingers_l=SOFT, fingers_r="relaxed"), "auto"),
        (113, body(stance(0.05), spine=(0, 2, 0), head=(-2, -1, 1),
                   hand_l={"pos": (0.16, 1.20 + hy, 0.17 + hz), "pole": (0.6, -0.6, -0.4), "knuckles": (0.1, -0.35, 0.93)},
                   hand_r=hand_r, fingers_l=SOFT, fingers_r="relaxed"), "auto"),
        (124, body(stance(0.05), hand_l=arm((-0.02, -0.38, 0.06), (0.6, -0.4, -0.5)),
                   hand_r=arm((0.02, -0.38, 0.06), (-0.6, -0.4, -0.5)), fingers_l="relaxed", fingers_r="relaxed"), "ease"),
    ]
    return build("catch_breath", rig, keys, meta={"layer": "full"})


ALL = (("sit_log", sit_log), ("warden_show", warden_show), ("arcanist_show", arcanist_show),
       ("reaver_show", reaver_show), ("stalker_show", stalker_show), ("idle_warden_break", warden_break),
       ("idle_arcanist_break", arcanist_break), ("idle_reaver_break", reaver_break),
       ("idle_stalker_break", stalker_break), ("catch_breath", catch_breath))


def clips(rig, want):
    out = []
    for name, fn in ALL:
        if want and not any(w in name for w in want):
            continue
        out.append(fn(rig))
    return out
