"""The crowd's own motion, keyed on the kit's bodies (folk.py packs it with
the townsfolk's clips, "f_<name>" and "m_<name>", and the crowd bakes it:
Vat.cs, FolkClips.Crowd).

- lurch, lurch_armed: the walking dead's gait. The crowd closes at a jog
  (Risen 2.7 m/s), far faster than any captured shamble (Kimodo's are 0.6
  to 1 m/s: at the crowd's pace their feet would skate). So the lurch is
  solved from the stride (gait.py) at the crowd's own speed and made dead
  on top of it: pitched forward from the ankles, always about to fall into
  the next step; the left leg dragged through on its toes, the body
  dipping onto it; the head hung and lolling late on the bounce; one arm
  dead weight, swinging on its own; the other half raised, reaching for
  the living.
- rally, rally_armed: a caster's cast (a call, a horn, a drum, "To me!"):
  a dip, then the weapon or the fist thrust up overhead and shaken, the
  chest thrown open, the free hand flung out to call them on. Held up for
  as long as the cast lasts (the longest is 1.5 s).
"""
from __future__ import annotations

import math
from dataclasses import replace

import numpy as np

from clips.actions import arm, body, stance
from gait import Gait, arc_of, pose_at
from keyed import Rig, build
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


def rally(name, rig: Rig, armed=False) -> Clip:
    hold = "grip" if armed else "fist"

    def up(lift, out=0.0):
        """The right hand high over the head (lift 0..1: to full reach), the
        weapon held upright."""
        h = arm((-0.12 - 0.04 * out, 0.26 + 0.30 * lift, 0.10 + 0.08 * (1 - lift)), (-0.9, 0.1, 0.3))
        if armed:
            # Brandished: the shaft tipped forward over the head.
            h["blade"] = (0.0, 0.55, 0.85)
            h["frame"] = "char"
        return h

    def calling(k):
        """The left hand flung out ahead, pointing them on at her (k 0..1: out)."""
        return arm((0.14 + 0.06 * k, -0.30 + 0.30 * k, 0.12 + 0.36 * k), (0.8, -0.4, -0.4), knuckles=(0.1, -0.1, 1.0))

    base = stance(0.04, l=(0.14, 0.10), r=(-0.15, -0.10))
    wide = stance(0.08, l=(0.16, 0.16), r=(-0.17, -0.14))
    keys = [
        (0, body(base, hand_l=arm((0.06, -0.44, 0.06), (0.6, -0.4, -0.5)), hand_r=arm((-0.06, -0.44, 0.06), (-0.6, -0.4, -0.5)),
                 fingers_l="relaxed", fingers_r=hold), "ease"),
        # The gather: down and turned to the right, the arm drawn in low (it
        # rises in front of the body from here, never out to the side).
        (5, body(wide, hips=(-8, 6, 0), spine=(-10, 10, 0), neck=(0, 4, 0), head=(4, 6, 0), clav_r=(-4, -10),
                 hand_l=arm((0.10, -0.40, 0.14), (0.6, -0.4, -0.5)), hand_r=arm((-0.16, -0.36, 0.08), (-0.8, -0.2, -0.4)),
                 fingers_l="relaxed", fingers_r=hold), "auto"),
        # Up: thrust high, the chest thrown open, head back on the shout,
        # the free hand flung out ahead.
        (10, body(wide, hips=(6, -4, 0), spine=(8, -12, 0), neck=(0, -6, 0), head=(0, -14, 0), clav_r=(16, 6), clav_l=(6, 8),
                  hand_l=calling(1.0), hand_r=up(1.0), fingers_l="point", fingers_r=hold), "fast"),
    ]
    # Shaken: pumped on each beat, the body bobbing with it, the head nodding the beat.
    beats = [(15, 0.4), (20, 1.0), (25, 0.4), (30, 1.0), (35, 0.4), (40, 1.0), (47, 0.9)]
    for i, (f, lift) in enumerate(beats):
        k = 1.0 - 0.35 * min(1.0, i / 3)
        bob = 0.035 * (1 - lift)
        keys.append((f, body(stance(0.08 + bob, l=(0.16, 0.16), r=(-0.17, -0.14)), hips=(6, -4 + 6 * (1 - lift), 0),
                             spine=(8, -10 + 8 * (1 - lift), 0), neck=(0, -4, 0), head=(0, -10 + 10 * (1 - lift), 0),
                             clav_r=(10 + 6 * lift, 6), clav_l=(4, 6), hand_l=calling(k), hand_r=up(lift),
                             fingers_l="point" if i < 3 else "open", fingers_r=hold), "auto"))
    meta = {"layer": "full", "note": "a caster's rally" + (", armed" if armed else ""), "source": "keyed (tools/anim/crowd.py)"}
    return build(name, rig, keys, meta=meta)


# name: function(name, rig) -> Clip, for each body.
KEYED = {"lurch": lurch, "lurch_armed": lambda name, rig: lurch(name, rig, armed=True),
         "rally": rally, "rally_armed": lambda name, rig: rally(name, rig, armed=True)}
