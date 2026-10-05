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

from dataclasses import replace

from clips.actions import arm, body
from clips.run import WARDEN
from clips.axe import GUARD as AXE_GUARD
from clips.sword import GUARD, _n, guard_l
from gait import arc_of, pose_at
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


CHARGE = replace(WARDEN, frames=12, speed=4.4, duty=0.3, drop=0.13, bob=0.06, lean=50, spine_lean=8, hip_yaw=8,
                 hip_roll=3, chest_yaw=4, reach=0.44, kick=0.46, knee=0.40, shoulders=(8, 8),
                 arms={"l": _shield_charge, "r": _sword_cocked})


def bull_rush(rig):
    keys = []
    for f in range(12):
        pose = pose_at(CHARGE, rig, (f / 12 + 0.25) % 1.0)
        # The left shoulder driving: the chest turned to lead with it, the
        # head down behind the shield's rim.
        sp = pose["spine"]
        pose["spine"] = (sp[0] - 16, sp[1], sp[2])
        pose["head"] = (pose["head"][0] + 12, pose["head"][1] - 4, 0)
        keys.append((f, pose, "linear"))
    shove_l = {"arc": arc_of((-0.10, 0.02, 0.44)), "pole": (1.0, -0.2, -0.3), "frame": "chest",
               "blade": _n(-0.1, 0.85, 0.5), "twist": 0.3}
    # The sword drawn back behind her as the shield goes in, the wrist
    # straight and the blade trailing where the arm takes it; it comes over
    # the top into the guard as she recovers. (Held upright while the arm
    # swung from behind her to the front, the hand rolled over in a frame.)
    sword_up = {"arc": arc_of((-0.18, -0.20, -0.06)), "pole": (-0.7, 0.0, -0.3), "frame": "chest",
                "thumb": (-0.4, 0.6, -0.7), "twist": 0.5}
    plant = {"foot_l": {"pos": (0.12, 0.0, 0.56), "rot": (10, 0, 0), "pole": (0.2, 0, 1)},
             "foot_r": {"pos": (-0.14, 0.06, -0.46), "rot": (-16, 40, 0), "toe": 40},
             "fingers_l": "fist", "fingers_r": "grip"}
    keys += [
        # The lead foot slams down; the shield punches out, the body behind it.
        (12, body({**plant, "hips": {"pos": (0.02, -0.22, 0.10)}, "hand_l": shove_l, "hand_r": sword_up,
                   "clav_l": (6, 16), "clav_r": (6, -4)},
                  hips=(-12, 22, 0), spine=(-22, 16, 0), neck=(0, -10, 0), head=(18, -18, 0)), "fast"),
        (14, body({**plant, "hips": {"pos": (0.02, -0.24, 0.13)}, "hand_l": {**shove_l, "arc": arc_of((-0.08, 0.04, 0.47))},
                   "hand_r": sword_up, "clav_l": (6, 20), "clav_r": (6, -6)},
                  hips=(-14, 24, 0), spine=(-24, 16, 0), neck=(0, -10, 0), head=(20, -18, 0)), "ease"),
        # The rebound: back up over her feet, shield home, sword raised.
        (19, body({"foot_l": {"pos": (0.13, 0.0, 0.38), "rot": (12, 0, 0)},
                   "foot_r": {"pos": (-0.16, 0.0, -0.24), "rot": (-22, 0, 0)},
                   "hips": {"pos": (0.0, -0.12, 0.04)}, "hand_l": guard_l(0.06),
                   "hand_r": {"arc": arc_of((-0.08, -0.22, 0.12)), "pole": (-0.6, -0.3, -0.6), "frame": "chest",
                              "blade": _n(-0.25, 0.7, 0.65), "twist": 0.5},
                   "fingers_l": "fist", "fingers_r": "grip"},
                  hips=(-6, 6, 0), spine=(-8, 2, 0), neck=(0, -2, 0), head=(8, -4, 0)), "auto"),
        (30, GUARD, "ease"),
    ]
    return build("bull_rush", rig, keys, meta={"layer": "full", "weapon": "sword+shield", "note": "keyed: 0.4 s shield charge, then the plant and shove"})


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
