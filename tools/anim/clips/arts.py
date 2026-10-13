"""Her arts: the vault, the bull rush and the chain haul, timed to the game
(godot/logic/Sim/Arts.cs) and played whole by PlayerView.

- vault: moving, she springs 6 m on the way she runs, 0.32 s in the air
  (the game lifts her 2.2 m at the top): a split leap, legs flung wide,
  landing on the lead foot into her run.
- vault_back: standing, she springs 6 m back from where she faces, eyes on
  what she escapes: a tucked back spring into a low three-point landing,
  one hand on the ground, the blade hand swept out behind.
- bull_rush: 9 m in 0.4 s behind her shield: one driving stride cycle,
  pitched hard over it, the left shoulder and the shield leading, the
  sword cocked low behind; then the lead foot planted, the shield punched
  out, and the rebound into her guard.
- chain_haul and chain_strike: the chain bites and hauls her to it at
  28 m/s (from 0.08 s to some 0.4 s, by the gap): yanked off her feet by
  the chain arm, flown in nearly flat with the axe cocked high behind her
  head, held until she arrives; then (PlayerView, as the haul ends) the
  feet swing down under her and the axe comes over and down two-handed,
  the blow landing in the second frame, as the game's does on arrival.

The clips start at the moment the game moves her (no wind-up the game has
no time for) and land when it lands her; what comes after is the weight,
cut short by PlayerView as soon as she moves on.
"""
from __future__ import annotations

import math

import numpy as np

from dataclasses import replace

from clips.actions import arm, body
from clips.run import WARDEN
from clips.axe import GUARD as AXE_GUARD
from clips.sword import GUARD, _n, guard_l
from gait import arc_of, pose_at
from rig import qmatrix
from keyed import build


def _feet(l, r, lrot=(6, 0, 0), rrot=(-6, 0, 0), ltoe=0, rtoe=0, lpole=None, rpole=None):
    fl = {"pos": l, "rot": lrot, "toe": ltoe}
    fr = {"pos": r, "rot": rrot, "toe": rtoe}
    if lpole:
        fl["pole"] = lpole
    if rpole:
        fr["pole"] = rpole
    return {"foot_l": fl, "foot_r": fr}


def _hips(x, y, z):
    return {"hips": {"pos": (x, y, z)}}


# ----------------------------------------------------------------- vault --
def vault(rig):
    """Moving: a split leap on the run, then the landing stride."""
    # In the air: the right arm reaching on with the leap, the left trailing
    # low and out with its blade.
    fly_r = arm((-0.16, 0.06, 0.44), (-0.7, -0.3, -0.4))
    fly_l = arm((0.30, -0.24, -0.30), (0.7, 0.3, 0.2))
    keys = [
        # Off the right toe, the left knee driven up and through, the right
        # arm thrown forward against it.
        (0, body({**_hips(0, 0.0, 0.06), **_feet((0.08, 0.40, 0.34), (-0.08, 0.06, -0.30), (4, 10, 0), (-4, 55, 0), rtoe=30),
                  "hand_r": arm((-0.10, 0.00, 0.42), (-0.6, -0.4, -0.6)), "hand_l": arm((0.16, -0.20, -0.36), (0.6, 0.4, 0.2)),
                  "fingers_l": "open", "fingers_r": "grip"},
                 hips=(0, 14, 0), spine=(0, 8, 0), neck=(0, -6, 0), head=(0, -10, 0)), "auto"),
        # The split, held a breath at the top: the front leg straight out,
        # the back one stretched long behind, toes pointed.
        (4, body({**_hips(0, 0.06, 0.0), **_feet((0.05, 0.86, 0.90), (-0.05, 0.62, -0.78), (4, 25, 0), (-4, 155, 0),
                                                  lpole=(0.1, 1, 0.2), rpole=(-0.1, -1, 0.1)),
                  "hand_r": fly_r, "hand_l": fly_l, "fingers_l": "spread", "fingers_r": "grip"},
                 hips=(8, 2, 0), spine=(-10, 4, 0), neck=(0, -6, 0), head=(6, -12, 0), clav_l=(4, -6), clav_r=(6, 8)), "ease"),
        (6, body({**_hips(0, 0.06, 0.0), **_feet((0.05, 0.80, 0.90), (-0.05, 0.64, -0.78), (4, 22, 0), (-4, 155, 0),
                                                  lpole=(0.1, 1, 0.2), rpole=(-0.1, -1, 0.1)),
                  "hand_r": arm((-0.18, 0.04, 0.44), (-0.7, -0.3, -0.4)), "hand_l": arm((0.32, -0.26, -0.28), (0.7, 0.3, 0.2)),
                  "fingers_l": "spread", "fingers_r": "grip"},
                 hips=(8, 4, 0), spine=(-10, 4, 0), neck=(0, -6, 0), head=(6, -12, 0), clav_l=(4, -6), clav_r=(6, 8)), "ease"),
        # The front leg drops to meet the ground; the back one stays up.
        (8, body({**_hips(0, 0.0, 0.04), **_feet((0.07, 0.30, 0.56), (-0.06, 0.56, -0.66), (4, 15, 0), (-4, 130, 0),
                                                   lpole=(0.1, 0.4, 1), rpole=(-0.1, -1, 0.1)),
                  "hand_r": arm((-0.14, -0.02, 0.42), (-0.6, -0.4, -0.6)), "hand_l": arm((0.26, -0.26, -0.30), (0.7, 0.3, 0.2)),
                  "fingers_l": "spread", "fingers_r": "grip"},
                 hips=(4, 10, 0), spine=(-6, 6, 0), neck=(0, -6, 0), head=(2, -10, 0)), "auto"),
        # Down on the left foot, the weight taken through the knee.
        (10, body({**_hips(0.02, -0.16, 0.08), **_feet((0.07, 0.0, 0.30), (-0.07, 0.40, -0.46), (4, 0, 0), (-4, 95, 0), rtoe=10,
                                                       rpole=(-0.1, -0.6, 0.4)),
                   "hand_r": arm((-0.10, -0.10, 0.36), (-0.5, -0.4, -0.6)), "hand_l": arm((0.16, -0.20, -0.30), (0.6, 0.4, 0.2)),
                   "fingers_l": "relaxed", "fingers_r": "grip"},
                  hips=(-4, 16, -3), spine=(4, 10, 2), neck=(0, -8, 0), head=(0, -10, 0)), "auto"),
        # The right leg comes through as the planted foot runs back under her.
        (13, body({**_hips(0.0, -0.08, 0.05), **_feet((0.07, 0.02, -0.18), (-0.07, 0.32, 0.12), (4, 25, 0), (-4, 10, 0)),
                   "hand_r": arm((-0.02, -0.24, 0.10), (-0.5, -0.4, -0.6)), "hand_l": arm((0.08, -0.20, 0.10), (0.6, -0.4, -0.6)),
                   "fingers_l": "relaxed", "fingers_r": "grip"},
                  hips=(0, 16, 0), spine=(0, 10, 0), neck=(0, -8, 0), head=(0, -10, 0)), "auto"),
        (16, body({**_hips(0.0, -0.10, 0.04), **_feet((0.07, 0.18, -0.34), (-0.07, 0.0, 0.34), (4, 45, 0), (-4, 0, 0), ltoe=20),
                   "hand_r": arm((0.02, -0.28, -0.20), (-0.5, 0.4, 0.2)), "hand_l": arm((0.0, -0.18, 0.26), (0.6, -0.4, -0.6)),
                   "fingers_l": "relaxed", "fingers_r": "grip"},
                  hips=(6, 16, 0), spine=(-8, 10, 0), neck=(0, -8, 0), head=(0, -10, 0)), "ease"),
    ]
    return build("vault", rig, keys, meta={"layer": "full", "note": "keyed: split leap on the run, 0.32 s flight"})


def vault_back(rig):
    """Standing: a tucked back spring, eyes on the enemy, into a low
    three-point landing; then up into her guard."""
    # The landing: the right knee all but on the ground, the left foot
    # planted before her, the left hand down beside it, the right arm and
    # its blade swept out behind; her head up, watching.
    land = {**_hips(0.02, -0.58, -0.04),
            **_feet((0.20, 0.0, 0.30), (-0.13, 0.05, -0.40), (18, 0, 0), (-14, 62, 0), rtoe=60,
                    lpole=(0.5, 0.1, 1), rpole=(-0.2, -0.4, 1)),
            "fingers_l": "spread", "fingers_r": "grip"}
    hand_down = {"pos": (0.26, 0.20, 0.44), "pole": (0.8, 0.4, -0.2), "knuckles": (0.1, -0.95, 0.3)}
    keys = [
        # Off both feet, already tipping back, the arms coming up before her.
        (0, body({**_hips(0, -0.04, 0.06), **_feet((0.11, 0.06, 0.14), (-0.11, 0.03, 0.06), (6, 45, 0), (-6, 50, 0)),
                  "hand_l": arm((0.22, -0.02, 0.34), (0.7, -0.3, -0.5)), "hand_r": arm((-0.24, -0.04, 0.32), (-0.7, -0.3, -0.5)),
                  "fingers_l": "open", "fingers_r": "grip"},
                 hips=(0, -16, 0), spine=(0, -14, 0), neck=(0, 6, 0), head=(0, 14, 0)), "auto"),
        # Tucked: the knees pulled up to her chest, the body laid back, the
        # chin down to keep her eyes on it, the blades out before her.
        (3, body({**_hips(0, 0.04, 0.0), **_feet((0.12, 0.52, 0.30), (-0.11, 0.44, 0.22), (6, 50, 0), (-6, 55, 0),
                                                  lpole=(0.3, 0.6, 1), rpole=(-0.3, 0.6, 1)),
                  "hand_l": arm((0.30, -0.22, 0.28), (0.8, -0.2, -0.4)), "hand_r": arm((-0.30, -0.26, 0.26), (-0.8, -0.2, -0.4)),
                  "fingers_l": "spread", "fingers_r": "grip"},
                 hips=(0, -38, 0), spine=(0, -10, 0), neck=(0, 14, 0), head=(0, 30, 0)), "ease"),
        (5, body({**_hips(0, 0.05, -0.02), **_feet((0.13, 0.62, 0.30), (-0.12, 0.56, 0.24), (8, 45, 0), (-6, 50, 0),
                                                  lpole=(0.3, 0.6, 1), rpole=(-0.3, 0.6, 1)),
                  "hand_l": arm((0.32, -0.26, 0.24), (0.8, -0.2, -0.4)), "hand_r": arm((-0.32, -0.22, 0.26), (-0.8, -0.2, -0.4)),
                  "fingers_l": "spread", "fingers_r": "grip"},
                 hips=(0, -44, 4), spine=(0, -8, -3), neck=(0, 16, 0), head=(0, 30, 0)), "auto"),
        # Out of the tuck, legs reaching down for the ground, the body coming
        # forward over them.
        (8, body({**_hips(0, -0.10, 0.0), **_feet((0.17, 0.16, 0.24), (-0.13, 0.22, -0.20), (12, 15, 0), (-10, 40, 0)),
                  "hand_l": arm((0.30, -0.22, 0.26), (0.7, -0.2, -0.5)), "hand_r": arm((-0.42, -0.06, 0.04), (-0.7, -0.1, -0.5)),
                  "fingers_l": "spread", "fingers_r": "grip"},
                 hips=(0, -4, 0), spine=(2, 8, -2), neck=(0, 0, 0), head=(0, 0, 0)), "auto"),
        # Down, hard.
        (10, body({**land, **_hips(0.02, -0.50, -0.02), "hand_l": {**hand_down, "pos": (0.26, 0.32, 0.46)},
                   "hand_r": arm((-0.30, -0.22, -0.30), (-0.7, 0.3, -0.4))},
                  hips=(-10, 28, 0), spine=(8, 30, -6), neck=(0, -18, 0), head=(6, -36, 0)), "fast"),
        (13, body({**land, "hand_l": hand_down, "hand_r": arm((-0.26, -0.32, -0.26), (-0.7, 0.3, -0.4))},
                  hips=(-10, 40, 0), spine=(8, 40, -6), neck=(0, -28, 0), head=(6, -56, 0)), "ease"),
        # Held: still, low, breathing; the head turns a touch as she reads it.
        (26, body({**land, **_hips(0.02, -0.56, -0.04), "hand_l": {**hand_down, "pos": (0.26, 0.21, 0.44)},
                   "hand_r": arm((-0.27, -0.30, -0.27), (-0.7, 0.3, -0.4))},
                  hips=(-8, 39, 0), spine=(10, 38, -6), neck=(0, -28, 0), head=(-10, -54, 0)), "ease"),
        # Up into her guard.
        (38, body({**_hips(0.0, -0.08, 0.0), **_feet((0.16, 0.0, 0.14), (-0.15, 0.0, -0.12), (14, 0, 0), (-16, 0, 0)),
                   "hand_l": arm((0.10, -0.26, 0.20), (0.6, -0.4, -0.5)), "hand_r": arm((-0.10, -0.24, 0.18), (-0.6, -0.4, -0.5)),
                   "fingers_l": "relaxed", "fingers_r": "grip"},
                  hips=(-6, 8, 0), spine=(6, 6, 0), neck=(0, -2, 0), head=(0, -4, 0)), "ease"),
    ]
    return build("vault_back", rig, keys, meta={"layer": "full", "note": "keyed: back spring, 0.32 s flight, three-point landing"})


# ------------------------------------------------------------- bull rush --
def _shield_charge(ph, k, hand):
    """The shield square before her face and chest, riding the stride."""
    bounce = 0.02 * math.cos(4 * math.pi * ph)
    return {"arc": arc_of((-0.16, -0.04 + bounce, 0.32)), "pole": (1.0, -0.2, -0.2), "frame": "chest",
            "blade": _n(-0.15, 0.8, 0.55), "twist": 0.3}


def _sword_cocked(ph, k, hand):
    """The sword low behind her, edge trailing, ready to come through."""
    sway = 0.03 * math.cos(2 * math.pi * ph)
    return {"arc": arc_of((-0.10, -0.32, -0.16 + sway)), "pole": (-0.6, 0.3, 0.4), "frame": "chest",
            "blade": _n(-0.2, -0.45, -0.85), "twist": 0.5}


def _shield_rush(ph, k, hand):
    """The shield out before her left shoulder, its face to the front: the
    upper arm down, out and forward, the forearm up across before the
    shoulder. The shield rides the forearm's back on its hinge (the game
    hands the forearm's roll to the hand), so its face is set by the plane
    of shoulder, elbow and wrist, never by a twist: that plane faces up and
    out from her chest, which her lean and the turned shoulder make the
    front, and keeps the disc off her breasts, neck and head."""
    bounce = 0.012 * math.cos(4 * math.pi * ph)
    return {"arc": arc_of(RUSH_HAND + (0.0, bounce, 0.0)), "pole": RUSH_POLE, "frame": "chest",
            "thumb": (-0.3, 0.6, 0.75)}


# The shield out before her (chest frame, from the shoulder): chosen from a grid of real builds
# (round 6), the hand x -0.07..0, y -0.08..0.03, z 0.34..0.42 and two elbow poles. This one keeps
# it 0 mm off her skin, outfit and holding arm for f0-11, the rim 30+ mm off the pauldron.
RUSH_HAND = np.array((0.0, 0.03, 0.42))
RUSH_POLE = (1.0, -0.3, -0.3)
CHARGE = replace(WARDEN, frames=12, speed=4.4, duty=0.3, drop=0.13, bob=0.06, lean=50, spine_lean=8, hip_yaw=8,
                 hip_roll=3, chest_yaw=4, reach=0.44, kick=0.46, knee=0.40, shoulders=(8, 8),
                 arms={"l": _shield_rush, "r": _sword_cocked})
RUSH_TURN = (-8, -22, 26)   # hips, spine yaw (the left shoulder leading), head yaw back to the front
SWORD_BACK = (-0.24, -0.05, -0.08)            # f12: the sword hand flung out and back at her right side, chest high (chest frame, from the shoulder)
SWORD_BACK_POLE = (-0.2, -1.0, -0.3)          # the elbow down by her ribs, the forearm up and out
PLANT_L = (0.15, 0.0, 0.17)                    # f12: the lead foot stamps down where her guard keeps it
BLEND_IN = 8                                   # the charge eases toward the plant from this frame
SWORD_BACK_BLADE = (-0.2, 0.15, -0.97)       # f12: the blade drawn back behind her, a little up (chest frame)
# The sword hand's way from the plant into her guard (SWING): out round her
# right side, the elbow dropping to her ribs and the forearm coming up level
# and out, so the blade rises on her right and goes over into the guard
# (frame, the hand from the shoulder in the chest frame, the elbow's way).
SWORD_WAY = ((12, SWORD_BACK, SWORD_BACK_POLE),
             (16, (-0.25, -0.15, 0.08), (-0.25, -1.0, -0.1)),
             (22, None, None))                 # (None: her guard's)
SHOVE_AT = np.array((-0.08, 0.0, 0.40))                     # f12: the shield cocked in on the plant (chest frame, from the shoulder)
# The punch, the impact and the recoil (chest frame, from the shoulder): solved from the build so the shield's hand
# goes 17 cm forward over the ground at f13, 18 at f14 (a near-hold), back to 12 at f15 (round 7: keyed as a
# reach beyond the plant's, the chest's yaw and pitch sent the punch to her right and down).
SHOVE_13 = np.array((0.045, 0.166, 0.389))
SHOVE_14 = np.array((0.044, 0.170, 0.386))
SHOVE_15 = np.array((-0.021, 0.099, 0.387))
SHOVE_POLE = (1.0, -0.4, -0.4)
SHOVE_THUMB = (-0.3, 0.6, 0.75)                           # the shield hand rides its forearm (the shield is on the forearm): no blade aim, no wrist bend
REBOUND_HAND = (-0.051, -0.028, 0.426)                           # f16: the shield's place on its way home (None: between the shove and the guard)
REBOUND_POLE = (1.0, -0.5, -0.4)
# The sword hand's pace from the plant into the guard (SWING): cm a frame at the tip, as the judge keyed it
# (slow out of the plant, the peak at f17-18, braking into the guard), one entry per frame f12->f13 ... f21->f22.
SWORD_PACE = (3, 5, 8, 13, 18, 20, 15, 10, 5, 2)
OVERSHOOT, OVER_END = 0.035, 25               # the blade runs this far past the guard's turn at f22 (of SWING's turn), back by OVER_END
HEAD_NOD = {14: 1.0, 15: 5.0, 16: 5.0, 17: 2.0}   # the recoil's nod (degrees, chin down), a frame behind the chest
HOME_LIFT = 0.0                                # f22: the shield on her guard (a lift off it brought the rim to her pauldron)
HEAD_FROM, HEAD_SETTLE = 11, 24


def _shield_home(lift=0.0):
    """The rebound's shield on her guard: sword.py's guard_l (GUARD_L_AT (-0.07, -0.22, 0.34), the pole
    GUARD_L_POLE, solved 0/0 against skin, outfit and her holding arm) with the hand 2 cm further left
    and 3 cm further out, so the sword hand's guard keeps 200 mm off the rim (at guard_l's own place
    it came to 178). `lift` raises it; the shield's face is set by the thumb's plane."""
    from clips.sword import GUARD_L_POLE
    x, y, z = HOME_AT
    return {"arc": arc_of((x, y + lift, z)), "pole": GUARD_L_POLE, "frame": "chest",
            "thumb": (-0.3, 0.75, 0.6)}


HOME_AT = (-0.05, -0.22, 0.37)


def _head_held(start, settle, guard):
    """The head kept on its way while the body slams and unwinds under it:
    from frame `start` its turn in her space goes round to the guard's
    (smoothly, one way, done by `settle`), whatever her back does. (Turned
    with the trunk, it whipped 15 degrees in a frame and flung a lock of her
    hair out level.)"""
    from rig import qeuler, qinv, qmul, qslerp
    from keyed import SPINE

    def chain(pose):
        q = qeuler(*pose["hips"].get("rot", (0, 0, 0)))
        sp = pose.get("spine", (0, 0, 0))
        for _, w in SPINE:
            q = qmul(q, qeuler(sp[0] * w, sp[1] * w, sp[2] * w))
        return qmul(q, qeuler(*pose.get("neck", (0, 0, 0))))

    ends = {}

    def post(fr, pose):
        if fr < start:
            return pose
        if fr == start:
            ends["a"] = qmul(chain(pose), qeuler(*pose.get("head", (0, 0, 0))))
            return pose
        u = min(1.0, (fr - start) / (settle - start))
        u = u * u * (3 - 2 * u)
        want = qslerp(ends["a"], qmul(chain(guard), qeuler(*guard["head"])), u)
        if HEAD_NOD.get(fr):
            want = qmul(want, qeuler(0, HEAD_NOD[fr], 0))
        m = qmatrix(qmul(qinv(chain(pose)), want))
        pose = dict(pose)
        pose["head"] = (math.degrees(math.atan2(m[0, 2], m[2, 2])), math.degrees(math.asin(max(-1.0, min(1.0, -m[1, 2])))),
                        math.degrees(math.atan2(m[1, 0], m[1, 1])))
        return pose
    return post


def bull_rush(rig):
    plant = {"foot_l": {"pos": PLANT_L, "rot": (12, 0, 0), "pole": (0.2, 0, 1)},
             "foot_r": {"pos": (-0.14, 0.06, -0.46), "rot": (-16, 40, 0), "toe": 40},
             "fingers_l": "fist", "fingers_r": "grip"}
    shove_l = {"arc": arc_of(SHOVE_AT), "pole": SHOVE_POLE, "frame": "chest", "thumb": SHOVE_THUMB}
    sword_up = {"arc": arc_of(SWORD_BACK), "pole": SWORD_BACK_POLE, "frame": "chest", "twist": 0.5,
                **({"blade": _n(*SWORD_BACK_BLADE)} if SWORD_BACK_BLADE is not None else {})}
    slam = body({**plant, "hips": {"pos": (0.02, -0.22, 0.10)}, "hand_l": shove_l, "hand_r": sword_up,
                 "clav_l": (6, 16), "clav_r": (6, -4)},
                hips=(-12, 22, 0), spine=(-22, 16, 0), neck=(0, -10, 0), head=(18, -18, 0))
    keys = []
    for f in range(12):
        pose = pose_at(CHARGE, rig, (f / 12) % 1.0)
        # The left shoulder driving: the chest turned to lead with it, the
        # head down behind the shield's rim.
        hr = pose["hips"]["rot"]
        pose["hips"]["rot"] = (hr[0] + RUSH_TURN[0], hr[1], hr[2])
        sp = pose["spine"]
        pose["spine"] = (sp[0] + RUSH_TURN[1], sp[1], sp[2])
        pose["head"] = (pose["head"][0] + RUSH_TURN[2], pose["head"][1] + 2, 0)
        pose["fingers_r"] = "grip"
        if f > BLEND_IN:
            # The last strides ease into the plant (the body, the arms' places,
            # the feet: the lead foot comes down under her, the back leg reaches
            # out behind), so nothing jumps as the plant lands.
            u = (f - BLEND_IN) / (12 - BLEND_IN)
            pose = _toward(pose, slam, u * u * (3 - 2 * u))
        keys.append((f, pose, "linear"))
    # The sword drawn back behind her as the shield goes in; from the plant
    # it goes its way (SWORD_WAY, _sword_way) round her right side and up
    # into the guard, the blade rising over the top, never across her or the
    # shield. (Keyed by its blade at each key, the hand rolled over in a
    # frame: from behind her to the front the forearm swings the other way
    # than the blade turns, and the turn about the forearm, taken the nearest
    # way frame to frame, went round the far side.)
    keys += [
        # The lead foot slams down; the shield punches out, the body behind it.
        (12, slam, "fast"),
        # The punch: the body drives through the shield, chest fastest f12-13, the left shoulder
        # forward, the arm straight.
        (13, body({**plant, "hips": {"pos": (0.02, -0.23, 0.14)}, "hand_l": {**shove_l, "arc": arc_of(SHOVE_13)},
                   "clav_l": (6, 24), "clav_r": (6, -6)},
                  hips=(-14, 25, 0), spine=(-25, 22, 0), neck=(0, -10, 0), head=(20, -18, 0)), "auto"),
        # The impact: a near-hold.
        (14, body({**plant, "hips": {"pos": (0.02, -0.235, 0.15)}, "hand_l": {**shove_l, "arc": arc_of(SHOVE_14)},
                   "clav_l": (6, 24), "clav_r": (6, -6)},
                  hips=(-14, 25, 0), spine=(-25, 22, 0), neck=(0, -10, 0), head=(20, -18, 0)), "ease"),
        # The recoil: knocked back off the hit, the shield 5 cm back, the hips back, the chest pitching up.
        (15, body({**plant, "hips": {"pos": (0.02, -0.228, 0.14)},
                   "hand_l": {**shove_l, "arc": arc_of(SHOVE_15)},
                   "clav_l": (5, 18), "clav_r": (5, -5)},
                  hips=(-13, 23.5, 0), spine=(-22, 20, 0), neck=(0, -8.6, 0), head=(17.6, -15.2, 0)), "auto"),
        # The rebound: back up over her feet, the back foot stepping up into
        # her guard (the lead foot stays planted), shield home.
        (16, body({"foot_l": plant["foot_l"], "foot_r": {"pos": (-0.16, 0.10, -0.30), "rot": (-20, 12, 0), "toe": 10},
                   "hips": {"pos": (0.01, -0.205, 0.10)}, "clav_l": (4, 12), "clav_r": (4, -4),
                   **({"hand_l": {"arc": arc_of(REBOUND_HAND), "pole": REBOUND_POLE, "frame": "chest", "thumb": (-0.3, 0.75, 0.6)}}
                      if REBOUND_HAND is not None else {})},
                  hips=(-11.0, 17.2, 0), spine=(-17.9, 15.0, 0), neck=(0, -6, 0), head=(15, -12, 0)), "auto"),
        (19, body({"foot_l": {"pos": PLANT_L, "rot": (12, 0, 0)},
                   "foot_r": {"pos": (-0.17, 0.0, -0.13), "rot": (-25, 0, 0)},
                   "hips": {"pos": (0.0, -0.155, 0.065)}, "hand_l": _shield_home(-0.03),
                   "fingers_l": "fist", "fingers_r": "grip"},
                  hips=(-8.6, 6, 0), spine=(-11.6, 3, 0), neck=(0, -2, 0), head=(8, -4, 0)), "auto"),
        (22, body({**GUARD, "hips": {"pos": (0.0, -0.10, 0.035)}, "hand_l": _shield_home(HOME_LIFT)},
                  hips=(-3, 5, 0), spine=(-4, 4, 0), head=(4, -4, 0)), "auto"),
        # Her guard, the shield held a hand further out before her than the
        # sword clips' (their guard_l rests its rim on her breastplate).
        (30, {**GUARD, "hand_l": _shield_home()}, "ease"),
    ]
    guard = {**GUARD, "hand_l": _shield_home()}
    meta = {"layer": "full", "weapon": "sword+shield", "note": "keyed: 0.4 s shield charge, then the plant and shove"}
    # The sword hand's turn from the plant into the guard (SWING), spread
    # evenly on its forearm as it goes its way: solved once with the hand
    # riding the forearm between the two ends, then again with the hand's
    # whole turn on the forearm (its roll about it and the wrist's bend)
    # carried evenly from the one end's to the other's.
    way = _sword_way(*SWING)
    first = build("bull_rush", rig, keys, post=_then(_head_held(HEAD_FROM, HEAD_SETTLE, guard), way), meta=meta)
    return build("bull_rush", rig, keys, post=_then(_head_held(HEAD_FROM, HEAD_SETTLE, guard), way,
                                                     _turn_world(rig, first, *SWING, lead=TURN_LEAD)), meta=meta)


SWING = (12, 22)   # the sword hand's way and whole turn between these frames (SWORD_WAY)
GLIDE_RAMP = 0.25  # the sword's way and turn: the part of SWING its pace takes to ramp up (and down)
PLANT_ROLL = 0.2   # how far the plant's sword hand is rolled about its blade toward the guard's roll
TURN_LEAD = 5      # the frames before the plant over which the sword hand eases into its roll there


def _toward(pose, goal, w):
    """pose with each number goal also has moved w of the way to goal's (aims, presets kept)."""
    from keyed import _flatten, _unflatten
    a, b = _flatten(pose), _flatten(goal)
    for k, v in list(a.items()):
        if isinstance(v, float) and isinstance(b.get(k), float):
            a[k] = v + (b[k] - v) * w
    return _unflatten(a)


def _then(*posts):
    def post(fr, pose):
        for p in posts:
            pose = p(fr, pose)
        return pose
    return post


def _ease(u):
    """0..1 eased in and out (the hand's way and turn along it)."""
    return u * u * (3 - 2 * u)


def _glide(u, ramp=None):
    """0..1 at an even pace between two soft ramps (each `ramp` of the way in
    time, the pace eased up and down on a half cosine): the least top speed
    that starts and ends at rest."""
    ramp = GLIDE_RAMP if ramp is None else ramp
    u = min(1.0, max(0.0, u))
    top = 1.0 / (1.0 - ramp)

    def up(t):  # the way covered while the pace ramps up for t (<= ramp)
        return top * (t / 2 - ramp / (2 * math.pi) * math.sin(math.pi * t / ramp))
    if u <= ramp:
        return up(u)
    if u >= 1.0 - ramp:
        return 1.0 - up(1.0 - u)
    return up(ramp) + top * (u - ramp)


def _pace(u):
    """0..1 along SWING at the judge's pace (SWORD_PACE, one entry a frame), smooth between frames."""
    c = np.concatenate([[0.0], np.cumsum(SWORD_PACE)]) / sum(SWORD_PACE)
    x = min(1.0, max(0.0, u)) * len(SWORD_PACE)
    i = min(int(x), len(SWORD_PACE) - 1)
    return float(c[i] + (c[i + 1] - c[i]) * (x - i))


def _over(fr):
    """How far past the guard's turn (of SWING's turn) the sword hand runs at frame fr >= SWING's end: the peak at
    its end, back by OVER_END."""
    b = SWING[1]
    u = (fr - b) / (OVER_END - b)
    return OVERSHOOT * (1 - _ease(min(1.0, max(0.0, u))))


def _unarc(arc):
    """The hand's place from the shoulder (chest frame) that arc_of gave as `arc`."""
    az, el, r = math.radians(arc[0]), math.radians(arc[1]), arc[2]
    return np.array([math.sin(az) * math.cos(el), math.sin(el), math.cos(az) * math.cos(el)]) * r


def _sword_way(a, b):
    """The sword hand between frames a and b on SWORD_WAY: its place and its
    elbow's way through the waypoints on one smooth curve (Catmull-Rom on
    their frames), eased along it; the hand rides the forearm (its turn is
    _turn_world's)."""
    pts = []
    for f, at, pole in SWORD_WAY:
        if at is None:
            at, pole = _unarc(GUARD["hand_r"]["arc"]), GUARD["hand_r"]["pole"]
        pts.append((f, np.array(at, float), np.array(pole, float) / np.linalg.norm(pole)))

    def at(t):
        fs = [p[0] for p in pts]
        k = max(0, min(len(pts) - 2, int(np.searchsorted(fs, t, side="right")) - 1))
        f0, f1 = fs[k], fs[k + 1]
        u = (t - f0) / (f1 - f0)
        out = []
        for i in (1, 2):
            p0, p1 = pts[k][i], pts[k + 1][i]
            m0 = (p1 - pts[k - 1][i]) / (f1 - fs[k - 1]) * (f1 - f0) if k > 0 else p1 - p0
            m1 = (pts[k + 2][i] - p0) / (fs[k + 2] - f0) * (f1 - f0) if k + 2 < len(pts) else p1 - p0
            h = ((2 * u ** 3 - 3 * u ** 2 + 1) * p0 + (u ** 3 - 2 * u ** 2 + u) * m0 + (-2 * u ** 3 + 3 * u ** 2) * p1
                 + (u ** 3 - u ** 2) * m1)
            out.append(h)
        return out

    def post(fr, pose):
        if not a < fr < b:
            return pose
        t = a + (b - a) * _pace((fr - a) / (b - a))
        h, pole = at(t)
        pose = dict(pose)
        pose["hand_r"] = {"arc": arc_of(h), "pole": tuple(float(x) for x in pole), "frame": "chest", "twist": 0.5}
        return pose
    return post


def _turn_world(rig, first, a, b, lead=3, side="r"):
    """The sword hand's whole turn from the plant (frame a) into the guard
    (frame b) of `first` (solved with the hand riding its forearm between
    them) carried evenly in her space, the short way: at a the hand is
    rolled about its blade to the guard's roll, so the turn from a to b is
    the blade's swing alone, the least there is; the frames from a - lead
    ease into that from the charge's hand. Given to each frame as the blade
    and knuckles that make it, in the chest's frame. (Its turn on the forearm
    spread evenly, the forearm swinging forward from behind her sent the
    blade down and under, 250 degrees; and the blade keyed alone was turned
    the nearest way about the forearm each frame, and flipped over in one.)"""
    from rig import qaxis, qbetween, qinv, qmul, qrot, qslerp
    sk, I = rig.sk, rig.I
    g, _ = sk.fk(first.rot, first.pos)
    h, s3 = I[f"hand_{side}"], I["spine_03"]
    lq = qaxis([1.0, 0, 0], -rig.grip.get(side, 0.0))

    def blade(q):
        return qrot(qmul(q, lq), [0, 0, 1.0])

    plant = qslerp(g[a, h], qmul(qbetween(blade(g[b, h]), blade(g[a, h])), g[b, h]), PLANT_ROLL)

    def post(fr, pose):
        if not a - lead < fr <= (OVER_END if b == SWING[1] else b - 1):
            return pose
        if fr < a:
            hand = qslerp(g[a - lead, h], plant, _ease((fr - a + lead) / lead))
        elif fr < b:
            hand = qslerp(plant, g[b, h], _pace((fr - a) / (b - a)))
        else:
            # past the guard's turn and back (the blade's follow-through in the wrist): the plant-to-guard
            # turn carried on a little, applied to the hand as the keys hold it there
            r = qmul(g[b, h], qinv(plant))
            if r[3] < 0:
                r = -r
            ang = 2 * math.acos(min(1.0, r[3]))
            ax = r[:3] / max(1e-9, np.linalg.norm(r[:3]))
            hand = qmul(qaxis(ax, math.degrees(ang * _over(fr))), g[fr, h])
        q = qmul(qinv(qmul(g[fr, s3], qinv(rig.grest[s3]))), qmul(hand, lq))
        pose = dict(pose)
        pose[f"hand_{side}"] = dict(pose[f"hand_{side}"], frame="chest", blade=tuple(float(x) for x in qrot(q, [0, 0, 1.0])),
                                    knuckles=tuple(float(x) for x in qrot(q, [0, 1.0, 0])))
        return pose
    return post


# ------------------------------------------------------------ chain haul --
def _axe_cocked(lift=0.0):
    """The axe high behind her head, ready to come over."""
    return {"arc": arc_of((-0.10, 0.30 + lift, -0.06)), "pole": (-0.6, 0.7, -0.3), "frame": "chest",
            "blade": _n(-0.25, 0.55, -0.8), "twist": 0.5}


def _chain_arm(reach=0.48, up=0.02):
    """The chain arm straight out at what it bit, the fist shut on it."""
    return {"arc": arc_of((0.04, up, reach)), "pole": (0.8, -0.3, -0.4), "frame": "chest",
            "knuckles": _n(0.0, 0.2, 1.0), "twist": 0.3}


def _flight(t):
    """Hauled through the air: nearly flat, legs trailing, chin up at it."""
    sway = 0.02 * math.sin(t * 1.3)
    return body({"hips": {"pos": (0.0, -0.08 + sway, 0.10)},
                 "foot_l": {"pos": (0.10, 0.62 + sway, -0.58), "rot": (8, 120, 0), "pole": (0.1, -1, 0.2)},
                 "foot_r": {"pos": (-0.10, 0.46 - sway, -0.70), "rot": (-8, 130, 0), "pole": (-0.1, -1, 0.2)},
                 "hand_l": _chain_arm(0.50, 0.04), "hand_r": _axe_cocked(0.02),
                 "clav_l": (4, 14), "clav_r": (10, -6), "fingers_l": "fist", "fingers_r": "grip"},
                hips=(6, 46, 0), spine=(-10, 20, 0), neck=(0, -24, 0), head=(4, -36, 0))


def chain_haul(rig):
    keys = [
        # The chain has bitten: the arm that threw it still out, the axe
        # coming up, the weight thrown forward off the back foot.
        (0, body({"hips": {"pos": (0.0, -0.10, 0.08)},
                  "foot_l": {"pos": (0.14, 0.0, 0.30), "rot": (12, 0, 0)},
                  "foot_r": {"pos": (-0.15, 0.08, -0.36), "rot": (-16, 45, 0), "toe": 40},
                  "hand_l": _chain_arm(0.46, 0.0), "hand_r": _axe_cocked(-0.10),
                  "fingers_l": "fist", "fingers_r": "grip"},
                 hips=(6, 18, 0), spine=(-8, 10, 0), neck=(0, -8, 0), head=(4, -12, 0)), "fast"),
        # Yanked off her feet.
        (3, body({"hips": {"pos": (0.0, -0.06, 0.12)},
                  "foot_l": {"pos": (0.11, 0.30, -0.10), "rot": (10, 70, 0)},
                  "foot_r": {"pos": (-0.11, 0.36, -0.52), "rot": (-10, 110, 0)},
                  "hand_l": _chain_arm(0.50, 0.04), "hand_r": _axe_cocked(0.0),
                  "clav_l": (4, 12), "clav_r": (8, -4), "fingers_l": "fist", "fingers_r": "grip"},
                 hips=(6, 34, 0), spine=(-10, 16, 0), neck=(0, -18, 0), head=(4, -28, 0)), "auto"),
        (6, _flight(0.0), "auto"),
        (12, _flight(1.0), "auto"),
        (18, _flight(2.0), "auto"),
        (24, _flight(3.0), "ease"),
    ]
    return build("chain_haul", rig, keys, meta={"layer": "full", "weapon": "axe", "note": "keyed: yanked off her feet and flown in on the chain, held"})


def chain_strike(rig):
    both = {"pole": (-0.6, -0.4, -0.4), "frame": "chest", "twist": 0.5}
    keys = [
        (0, _flight(3.0), "fast"),
        # Feet swung down under her as the axe comes over the top, both
        # hands on it.
        (1, body({"hips": {"pos": (0.0, -0.22, 0.10)},
                  "foot_l": {"pos": (0.20, 0.12, 0.20), "rot": (14, 10, 0)},
                  "foot_r": {"pos": (-0.20, 0.16, -0.20), "rot": (-20, 30, 0)},
                  "hand_r": {**both, "arc": arc_of((-0.04, 0.30, 0.20)), "blade": _n(-0.1, 0.9, 0.4)},
                  "hand_l": {"arc": arc_of((0.02, 0.26, 0.24)), "pole": (0.6, -0.4, -0.4), "frame": "chest", "twist": 0.3},
                  "fingers_l": "grip", "fingers_r": "grip"},
                 hips=(0, 26, 0), spine=(0, 8, 0), neck=(0, -16, 0), head=(0, -24, 0)), "linear"),
        # Coming down: the arms out before her at the height of her
        # shoulders, the haft forward, the head of the axe still above it.
        # (Over the top to buried in one frame, the hands turned over in it.)
        (2, body({"hips": {"pos": (0.0, -0.26, 0.10)},
                  "foot_l": {"pos": (0.22, 0.04, 0.22), "rot": (16, 4, 0)},
                  "foot_r": {"pos": (-0.22, 0.06, -0.23), "rot": (-23, 24, 0)},
                  "hand_r": {**both, "arc": arc_of((-0.03, 0.06, 0.44)), "blade": _n(-0.05, 0.35, 0.94)},
                  "hand_l": {"arc": arc_of((0.04, 0.02, 0.40)), "pole": (0.6, -0.4, -0.4), "frame": "chest", "twist": 0.3},
                  "fingers_l": "grip", "fingers_r": "grip"},
                 hips=(0, 30, 0), spine=(0, 18, 0), neck=(0, -17, 0), head=(0, -25, 0)), "linear"),
        # The blow: down hard into a wide crouch, the axe buried low before her.
        (3, body({"hips": {"pos": (0.0, -0.30, 0.10)},
                  "foot_l": {"pos": (0.24, 0.0, 0.24), "rot": (18, 0, 0)},
                  "foot_r": {"pos": (-0.24, 0.02, -0.26), "rot": (-26, 20, 0), "toe": 20},
                  "hand_r": {**both, "arc": arc_of((-0.02, -0.22, 0.44)), "blade": _n(0.0, -0.75, 0.65)},
                  "hand_l": {"arc": arc_of((0.06, -0.26, 0.38)), "pole": (0.6, -0.4, -0.4), "frame": "chest", "twist": 0.3},
                  "fingers_l": "grip", "fingers_r": "grip", "clav_l": (-4, 14), "clav_r": (-4, 14)},
                 hips=(0, 34, 0), spine=(0, 30, 0), neck=(0, -18, 0), head=(0, -26, 0)), "ease"),
        (6, body({"hips": {"pos": (0.0, -0.34, 0.10)},
                  "foot_l": {"pos": (0.24, 0.0, 0.24), "rot": (18, 0, 0)},
                  "foot_r": {"pos": (-0.24, 0.02, -0.26), "rot": (-26, 20, 0), "toe": 20},
                  "hand_r": {**both, "arc": arc_of((-0.02, -0.28, 0.42)), "blade": _n(0.0, -0.85, 0.5)},
                  "hand_l": {"arc": arc_of((0.06, -0.30, 0.36)), "pole": (0.6, -0.4, -0.4), "frame": "chest", "twist": 0.3},
                  "fingers_l": "grip", "fingers_r": "grip", "clav_l": (-4, 16), "clav_r": (-4, 16)},
                 hips=(0, 38, 0), spine=(0, 32, 0), neck=(0, -20, 0), head=(0, -28, 0)), "ease"),
        # Wrenched free and up, the free hand back to its fist.
        (15, body({"hips": {"pos": (0.0, -0.18, 0.04)},
                   "foot_l": {"pos": (0.20, 0.0, 0.20), "rot": (16, 0, 0)},
                   "foot_r": {"pos": (-0.21, 0.0, -0.20), "rot": (-24, 0, 0)},
                   "hand_r": {**both, "arc": arc_of((-0.10, -0.26, 0.20)), "blade": _n(-0.3, 0.6, 0.7)},
                   "hand_l": {"arc": arc_of((0.04, -0.30, 0.16)), "pole": (0.7, -0.5, -0.3), "frame": "chest", "twist": 0.4},
                   "fingers_l": "fist", "fingers_r": "grip"},
                  hips=(0, 16, 0), spine=(0, 12, 0), neck=(0, -8, 0), head=(0, -10, 0)), "auto"),
        (27, AXE_GUARD, "ease"),
    ]
    return build("chain_strike", rig, keys, meta={"layer": "full", "contact": 3 / 30, "weapon": "axe",
                                                   "note": "keyed: the haul's landing blow, two-handed"})


ALL = (("vault", vault), ("vault_back", vault_back), ("bull_rush", bull_rush), ("chain_haul", chain_haul),
       ("chain_strike", chain_strike))
# Judged on sheets and in the game. Any other clip here is work in progress:
# built only when named, so a full build (and the game, which plays anything
# in her library at once) leaves it out.
JUDGED = {"vault", "vault_back", "bull_rush", "chain_haul", "chain_strike"}


def clips(rig, want):
    return [f(rig) for name, f in ALL
            if (want and any(w in name for w in want)) or (not want and name in JUDGED)]
