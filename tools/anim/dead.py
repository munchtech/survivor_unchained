"""The walking dead's own gait: the Risen's lurch, keyed on the kit's bodies
(folk.py packs it with the townsfolk's clips as "f_lurch" and "m_lurch").

The crowd closes at a jog (Risen 2.7 m/s), far faster than any captured
shamble (Kimodo's are 0.6 to 1 m/s: at the crowd's pace their feet would
skate). So the lurch is solved from the stride (gait.py) at the crowd's own
speed and made dead on top of it: pitched forward from the ankles, always
about to fall into the next step; the left leg dragged through on its toes,
the body dipping onto it; the head hung and lolling late on the bounce; the
left arm dead weight, swinging on its own; the right half raised, reaching
for the living.
"""
from __future__ import annotations

import math
from dataclasses import replace

import numpy as np

from gait import Gait, arc_of, pose_at
from keyed import Rig
from rig import Clip

LURCH = Gait(frames=22, speed=2.6, duty=0.52, drop=0.11, bob=0.05, lean=19.0, spine_lean=13.0, hip_yaw=11.0,
             hip_roll=7.0, hip_shift=0.05, chest_yaw=5.0, width=0.10, reach=0.42, kick=0.18, knee=0.22, toe_off=16.0,
             arm_fwd=(0.02, -0.46, 0.10), arm_back=(0.04, -0.46, -0.06), elbow_out=0.1, fingers="relaxed", head_up=-16.0,
             shoulders=(-4, 10))


def _lurch_pose(g: Gait, rig: Rig, ph, armed=False):
    p = pose_at(g, rig, ph)
    ph = ph % 1.0
    # The dragged left leg: swung through stiff, out round the side with the
    # hip hitched to clear it, toes down and scraping, turned out; set down
    # flat at the end.
    hike = 0.0
    if ph >= g.duty:
        s = (ph - g.duty) / (1 - g.duty)
        f = p["foot_l"]
        x, y, z = f["pos"]
        drag = math.sin(math.pi * min(1.0, s / 0.85))
        hike = drag
        lift = 0.25 + 0.75 * max(0.0, (s - 0.75) / 0.25)
        p["foot_l"] = {**f, "pos": (x + 0.11 * drag, y * lift + 0.02 * drag, z), "toe": 0, "pole": (0.7, 0.0, 1.0),
                       "rot": (4 + 16 * drag, 22 * drag + f["rot"][1] * (1 - drag), 0)}
    # The body drops onto the weak leg as it takes the weight, and hitches
    # up over the good one to swing it through.
    on_left = 1.0 if ph < g.duty else 0.0
    dip = 0.035 * on_left * math.sin(math.pi * min(1.0, ph / g.duty))
    hx, hy, hz = p["hips"]["pos"]
    yaw, pitch, roll = p["hips"]["rot"]
    p["hips"] = {"pos": (hx + 0.015 * on_left - 0.03 * hike, hy - dip + 0.025 * hike, hz + 0.02),
                 "rot": (yaw, pitch, roll + 5 * dip / 0.035 + 11 * hike)}
    # The head hung and tipped to one side, bouncing late.
    ny, npitch, nroll = p["neck"]
    p["neck"] = (ny, npitch + 6, nroll + 6)
    hy_, hp, hr = p["head"]
    p["head"] = (hy_ * 0.4 + 6, hp + 8 + 5 * math.sin(4 * math.pi * (ph - 0.14)), hr + 12 + 4 * math.sin(2 * math.pi * (ph - 0.2)))
    # One arm swings as dead weight, late on the body; the other is half
    # raised and reaching, the fingers hooked. Unarmed, the right reaches;
    # armed, the left does, and the weapon hangs in the right, trailing.
    k = 0.5 - 0.5 * math.cos(2 * math.pi * (ph - 0.62))
    reach = 0.5 - 0.5 * math.cos(2 * math.pi * (ph - 0.1))
    # (The chest is pitched some 30 degrees forward: hanging straight down
    # is down and forward in its frame.)
    if not armed:
        p["hand_l"] = {"arc": arc_of((0.07, -0.44, 0.14 + 0.14 * k)), "pole": (0.2, -0.3, -1.0)}
        p["hand_r"] = {"arc": arc_of((0.03, 0.02 + 0.04 * reach, 0.40 + 0.04 * reach)), "pole": (-0.7, -0.6, -0.3),
                       "knuckles": (0.0, -0.3, 1.0)}
        p["clav_r"], p["clav_l"] = (2, 14), (-6, 6)
        p["fingers_l"], p["fingers_r"] = "relaxed", "claw"
    else:
        k = 1 - k
        p["hand_r"] = {"arc": arc_of((-0.08, -0.42, 0.12 + 0.12 * k)), "pole": (-0.2, -0.3, -1.0), "frame": "char",
                       "blade": (0.0, -0.55, -0.85)}
        p["hand_l"] = {"arc": arc_of((-0.03, 0.02 + 0.04 * reach, 0.40 + 0.04 * reach)), "pole": (0.7, -0.6, -0.3),
                       "knuckles": (0.0, -0.3, 1.0)}
        p["clav_l"], p["clav_r"] = (2, 14), (-8, 4)
        p["fingers_r"], p["fingers_l"] = "grip", "claw"
    return p


def lurch(name, rig: Rig, g: Gait = LURCH, armed=False) -> Clip:
    n = g.frames
    rot = np.empty((n + 1, len(rig.sk), 4))
    pos = np.empty((n + 1, len(rig.sk), 3))
    for f in range(n + 1):
        rot[f], pos[f] = rig.solve(_lurch_pose(g, rig, f / n, armed))
    meta = {"layer": "full", "speed": g.speed, "cycle": n / 30.0, "steps": 2, "source": "keyed (tools/anim/dead.py)",
            "licence": "own work", "changes": "", "note": "the Risen's lurch, at the crowd's pace" + (", armed" if armed else "")}
    return Clip(name, 30, rot, pos, loop=True, meta=meta)


# name: function(name, rig) -> Clip, for each body.
KEYED = {"lurch": lurch, "lurch_armed": lambda name, rig: lurch(name, rig, armed=True)}
