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

import numpy as np

from clips import idle
from clips.actions import arm, body, stance
from clips.sword import _n
from gait import arc_of
from keyed import build


def feet_of(rig, base, f=0):
    """Where the base clip's feet are at a frame, as foot controls (so a
    crouch laid over it keeps them planted)."""
    g, p = rig.sk.fk(base.rot[f][None], base.pos[f][None])
    out = {}
    for side in "lr":
        j = rig.I[f"foot_{side}"]
        a = p[0, j]
        fwd = g[0, j]
        # (Less the body's own widening, which the solver adds back: they already stand where they stand.)
        s = 1 if side == "l" else -1
        out[f"foot_{side}"] = {"pos": (float(a[0]) - s * rig.feet_out, float(a[1] - rig.prest[j][1]), float(a[2]))}
    return out


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
             "hand_l": {"arc": arc_of((-0.14, -0.13, 0.30)), "pole": (1.0, -0.3, -0.3), "frame": "chest",
                        "blade": _n(-0.2, 0.9, 0.4), "twist": 0.3},
             "hand_r": {"arc": arc_of((-0.14, 0.29, -0.04)), "pole": (-1.0, -0.2, -0.2), "frame": "chest",
                        "blade": _n(0.28, 0.02, 0.96), "twist": 0.5},
             "fingers_l": "fist", "fingers_r": "grip"}
    keys = [
        (0, over("warden"), "auto"),
        (8, over("warden", hips={"pos": (0, -0.05, -0.02)}, foot_l=f["foot_l"], foot_r=f["foot_r"]), "fast"),
        (16, guard, "ease"),
        (50, {**guard, "spine": (-8, 9, 0)}, "ease"),
        (70, over("warden"), "ease"),
    ]
    return build("warden_show", rig, keys, base=base, meta={"layer": "full", "weapon": "sword+shield"})


def arcanist_show(rig):
    """The staff lifted and struck down on the ground; the free hand rises
    open as if the light came to it; her chin lifts."""
    base = idle.base_of(rig, "arcanist")
    keys = [
        (0, over("arcanist"), "auto"),
        (12, over("arcanist", head=(0, -8, 0),
                  hand_r={"arc": arc_of((-0.16, -0.02, 0.14)), "pole": (-0.8, -0.3, -0.6), "frame": "chest",
                          "blade": _n(-0.1, 1.0, 0.1), "twist": 0.5},
                  hand_l={"arc": arc_of((0.20, -0.30, 0.14)), "pole": (0.8, -0.4, -0.4), "frame": "chest",
                          "knuckles": _n(0.3, 0.2, 0.9)}, fingers_l="relaxed"), "fast"),
        (18, over("arcanist", spine=(0, 4, 0), head=(-10, -16, 0),
                  hand_r={"arc": arc_of((-0.16, -0.30, 0.14)), "pole": (-0.8, -0.3, -0.6), "frame": "chest",
                          "blade": _n(-0.1, 1.0, 0.12), "twist": 0.5},
                  hand_l={"arc": arc_of((0.30, -0.16, 0.22)), "pole": (0.8, -0.6, -0.2), "frame": "chest",
                          "knuckles": _n(0.6, 0.3, 0.75)}, fingers_l="spread"), "ease"),
        (55, over("arcanist", spine=(0, 3, 0), head=(-12, -18, 0),
                  hand_r={"arc": arc_of((-0.16, -0.30, 0.14)), "pole": (-0.8, -0.3, -0.6), "frame": "chest",
                          "blade": _n(-0.1, 1.0, 0.12), "twist": 0.5},
                  hand_l={"arc": arc_of((0.32, -0.12, 0.22)), "pole": (0.8, -0.6, -0.2), "frame": "chest",
                          "knuckles": _n(0.6, 0.35, 0.7)}, fingers_l="spread"), "ease"),
        (78, over("arcanist"), "ease"),
    ]
    return build("arcanist_show", rig, keys, base=base, meta={"layer": "full", "weapon": "staff"})


def reaver_show(rig):
    """The axe swung down off her shoulder, round in a wheel overhead and
    slammed back onto it; her chin up and a grin's worth of swagger."""
    base = idle.base_of(rig, "reaver")
    keys = [
        (0, over("reaver"), "auto"),
        (8, over("reaver", spine=(-10, 6, 0),
                 hand_r={"arc": arc_of((-0.30, -0.32, 0.10)), "pole": (-0.5, -0.8, 0.0), "frame": "chest",
                         "blade": _n(-0.6, -0.7, 0.3), "twist": 0.5}), "fast"),
        (16, over("reaver", spine=(-14, -4, 0),
                  hand_r={"arc": arc_of((-0.26, 0.06, 0.22)), "pole": (-0.9, -0.2, -0.2), "frame": "chest",
                          "blade": _n(-0.5, 0.2, 0.85), "twist": 0.5}), "auto"),
        (24, over("reaver", spine=(-6, -10, 0), head=(0, -10, 0),
                  hand_r={"arc": arc_of((-0.10, 0.36, 0.04)), "pole": (-0.8, 0.4, -0.2), "frame": "chest",
                          "blade": _n(-0.1, 0.4, -0.9), "twist": 0.5}), "auto"),
        (30, over("reaver", hips={"rot": (8, 0, 4)}, spine=(4, -4, 0), head=(-6, -16, -4)), "ease"),
        (60, over("reaver", hips={"rot": (8, 0, 4)}, spine=(4, -4, 0), head=(-6, -14, -4)), "ease"),
        (72, over("reaver"), "ease"),
    ]
    return build("reaver_show", rig, keys, base=base, meta={"layer": "full", "weapon": "axe"})


def stalker_show(rig):
    """The crossbow up to her eye, sighting across the dark to the left,
    then the right, then down."""
    base = idle.base_of(rig, "stalker")
    def aim(yaw):
        return over("stalker", spine=(yaw * 0.6, -4, 0), head=(yaw * 0.4, 6, -6),
                    hand_r={"arc": arc_of((0.06, -0.02, 0.40)), "pole": (-0.8, -0.5, -0.2), "frame": "chest",
                            "knuckles": _n(0.06, 0.03, 1.0), "twist": 0.5},
                    hand_l={"arc": arc_of((-0.10, -0.08, 0.40)), "pole": (0.8, -0.5, -0.2), "frame": "chest",
                            "knuckles": _n(0.1, -0.2, 1.0), "twist": 0.4})
    keys = [
        (0, over("stalker"), "auto"),
        (12, aim(0), "ease"),
        (26, aim(34), "ease"),
        (38, aim(34), "auto"),
        (54, aim(-34), "ease"),
        (64, aim(-34), "auto"),
        (74, aim(0), "ease"),
        (90, over("stalker"), "ease"),
    ]
    return build("stalker_show", rig, keys, base=base, meta={"layer": "full", "weapon": "crossbow"})


# ----------------------------------------------------------------- breaks --
def warden_break(rig):
    base = idle.base_of(rig, "warden")
    shoulder = {"arc": arc_of((0.02, -0.06, 0.18)), "pole": (-0.8, -0.6, 0.0), "frame": "chest",
                "blade": _n(-0.15, 0.5, -0.85), "twist": 0.5}
    keys = [
        (0, over("warden"), "auto"),
        # The flat of the blade laid on her shoulder, the shoulder rolled under it.
        (16, over("warden", hand_r=shoulder), "ease"),
        (24, over("warden", hand_r=shoulder, clav_r=(10, 6), head=(-8, 0, 6)), "auto"),
        (32, over("warden", hand_r=shoulder, clav_r=(2, -6), head=(-6, 0, 3)), "auto"),
        (40, over("warden", hand_r=shoulder, clav_r=(10, 6), head=(-8, 0, 6)), "auto"),
        (48, over("warden", hand_r=shoulder, clav_r=(0, 0)), "ease"),
        # The buckler turned to her and looked over, its strap tugged.
        (64, over("warden", hand_r=shoulder, head=(24, 22, 0), spine=(8, 4, 0),
                  hand_l={"arc": arc_of((-0.10, -0.22, 0.26)), "pole": (1.0, -0.6, 0.2), "frame": "chest",
                          "blade": _n(-0.6, 0.3, 0.75), "twist": 0.6}), "ease"),
        (76, over("warden", hand_r=shoulder, head=(26, 24, 0), spine=(8, 4, 0),
                  hand_l={"arc": arc_of((-0.10, -0.20, 0.28)), "pole": (1.0, -0.6, 0.2), "frame": "chest",
                          "blade": _n(-0.55, 0.35, 0.75), "twist": 0.6}), "ease"),
        (100, over("warden"), "ease"),
    ]
    return build("idle_warden_break", rig, keys, base=base, meta={"layer": "full", "weapon": "sword+shield"})


def arcanist_break(rig):
    base = idle.base_of(rig, "arcanist")
    tuck = {"pos": (0.13, 1.62, 0.04), "pole": (1.0, 0.2, -0.3), "knuckles": (0.0, 0.5, -0.85)}
    def staff(roll):
        a = math.radians(roll)
        return {"arc": arc_of((-0.16, -0.28, 0.12)), "pole": (-0.8, -0.3, -0.6), "frame": "chest",
                "blade": _n(-0.12, 1.0, 0.18), "knuckles": _n(math.sin(a), 0.0, math.cos(a)), "twist": 0.6}
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
        tuck = {"pos": (0.13, 1.62, 0.04), "pole": (1.0, 0.2, -0.3), "knuckles": (-0.25, 0.8, -0.55)}
        first = (18, over("arcanist", hand_l=tuck, head=(-6, 4, 8), fingers_l="relaxed"), "ease")
        second = (28, over("arcanist", hand_l={**tuck, "pos": (0.14, 1.60, -0.02)}, head=(-6, 4, 8)), "ease")
    rising = (9, over("arcanist", hand_l={"pos": (0.16, 1.38, 0.16), "pole": (1.0, -0.3, -0.3), "knuckles": (-0.1, 0.9, 0.3)},
                      fingers_l="relaxed"), "auto")
    keys = [
        (0, over("arcanist"), "auto"),
        *([rising] if rig.body != "him" else []),
        first,
        second,
        # Up at the sky, the staff turning in her fingers.
        (44, over("arcanist", head=(10, -24, 0), hand_r=staff(-40)), "ease"),
        (60, over("arcanist", head=(14, -26, 0), hand_r=staff(30)), "auto"),
        (74, over("arcanist", head=(8, -20, 0), hand_r=staff(-20)), "ease"),
        (100, over("arcanist"), "ease"),
    ]
    return build("idle_arcanist_break", rig, keys, base=base, meta={"layer": "full", "weapon": "staff"})


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
        # The axe off her shoulder and twirled in the fist, over and back, twice.
        (40, over("reaver", hand_r=spin(-75)), "auto"),
        (45, over("reaver", hand_r=spin(70)), "auto"),
        (50, over("reaver", hand_r=spin(-70)), "auto"),
        (55, over("reaver", hand_r=spin(70)), "auto"),
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
    return build("idle_reaver_break", rig, keys, base=base, meta={"layer": "full", "weapon": "axe"})


def stalker_break(rig):
    base = idle.base_of(rig, "stalker")
    f = feet_of(rig, base)
    crouch = {"hips": {"pos": (0, -0.26, 0.06), "rot": (0, 22, 0)}, "spine": (0, 22, 0), "head": (0, 10, 0),
              "foot_l": f["foot_l"], "foot_r": f["foot_r"],
              "hand_l": {"pos": (0.06, 0.04, 0.42), "pole": (0.8, 0.2, -0.4), "knuckles": (0.0, -0.3, 1.0)},
              "fingers_l": "open"}
    keys = [
        (0, over("stalker"), "auto"),
        (14, over("stalker", spine=(22, 0, 0), head=(40, 2, 0)), "ease"),
        (28, over("stalker", spine=(24, 0, 0), head=(44, 4, 0)), "ease"),
        (44, over("stalker", spine=(-22, 0, 0), head=(-40, 2, 0)), "ease"),
        (56, over("stalker", spine=(-24, 0, 0), head=(-44, 4, 0)), "ease"),
        # Down on her haunches, two fingers to the ground, reading it.
        (72, over("stalker", **crouch), "ease"),
        (90, over("stalker", **{**crouch, "head": (8, 14, 0)}), "ease"),
        (110, over("stalker", foot_l=f["foot_l"], foot_r=f["foot_r"]), "ease"),
        (120, over("stalker"), "ease"),
    ]
    return build("idle_stalker_break", rig, keys, base=base, meta={"layer": "full", "weapon": "crossbow"})


def catch_breath(rig):
    """Hands down onto her knees, the back heaving with three hard breaths,
    then up, a hand pushing the hair back.

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
            "fingers_l": "relaxed", "fingers_r": "grip",
        }
    upright = body(stance(0.05), spine=(0, 2, 0), head=(-6, -6, 4),
                   hand_l={"pos": (0.10, 1.66 + hy, 0.06 + hz), "pole": (1.0, 0.3, -0.2), "knuckles": (0.0, 0.4, -0.9)},
                   hand_r=arm((0.02, -0.36, 0.10), (-0.6, -0.4, -0.5)), fingers_l="relaxed", fingers_r="grip")
    keys = [
        (0, body(stance(0.06), spine=(0, 8, 0), hand_l=arm((-0.02, -0.34, 0.12), (0.6, -0.4, -0.5)),
                 hand_r=arm((0.02, -0.34, 0.12), (-0.6, -0.4, -0.5)), fingers_l="relaxed", fingers_r="grip"), "auto"),
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
                  hand_r=arm((0.02, -0.36, 0.10), (-0.6, -0.4, -0.5)), fingers_l="relaxed", fingers_r="grip"), "auto"),
        (98, upright, "ease"),
        # Down again round the front of her, not back through her shoulder.
        (110, body(stance(0.05), spine=(0, 3, 0), head=(-3, -2, 2),
                   hand_l={"pos": (0.16, 1.24 + hy, 0.20 + hz), "pole": (0.9, -0.3, -0.3), "knuckles": (0.1, 0.55, 0.8)},
                   hand_r=arm((0.02, -0.37, 0.08), (-0.6, -0.4, -0.5)), fingers_l="relaxed", fingers_r="grip"), "auto"),
        (124, body(stance(0.05), hand_l=arm((-0.02, -0.38, 0.06), (0.6, -0.4, -0.5)),
                   hand_r=arm((0.02, -0.38, 0.06), (-0.6, -0.4, -0.5)), fingers_l="relaxed", fingers_r="grip"), "ease"),
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
