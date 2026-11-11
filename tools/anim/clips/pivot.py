"""A1 L23: the 180's held plant, pivot_warden_l / pivot_warden_r.

Two static full-body poses (two identical keys, looping) the game blends in under the pivot's foot pin (PlayerView
pivotMix). Each is run_warden's own pose at the planted foot's mid-stance (_l: ph 0.145, left foot down; _r: 0.645,
the right) with only the lower body changed: the hips 8 cm lower and pitched 6 deg more forward at the hip, the
planted foot exactly where the run has it but flat, the free foot swung wide (out to its own side, behind the planted
foot, up, toed out, heel up) with the knee out and forward. Spine, neck, head, arms, shield and sword are the run's.
"""
from __future__ import annotations

import math
from dataclasses import replace

from clips.run import RUN_GRIPS, RUNS
from gait import pose_at
from keyed import solve_frames
from rig import Clip

PH = {"l": 0.145, "r": 0.645}
# Values (A1 L23): hips drop and pitch, free foot out (past its line), back (behind the planted foot), up, yaw, heel up.
HIPS_DROP, HIPS_PITCH = 0.075, 6.0
FREE_OUT, FREE_BACK, FREE_UP, FREE_YAW, FREE_HEEL = 0.32, 0.22, 0.10, 30.0, 15.0


def pose(rig, side):
    g, arms, weapon = RUNS["run_warden"]
    g = replace(g, arms=arms)
    p = pose_at(g, rig, PH[side])
    hx, hy, hz = p["hips"]["pos"]
    yaw, pitch, roll = p["hips"]["rot"]
    p["hips"] = {"pos": (hx, hy - HIPS_DROP, hz), "rot": (yaw, pitch + HIPS_PITCH, roll)}
    pl = dict(p[f"foot_{side}"])
    pl["rot"] = (pl["rot"][0], 0.0, pl["rot"][2])
    pl["toe"] = 0.0
    p[f"foot_{side}"] = pl
    fs = "r" if side == "l" else "l"
    sf = 1 if fs == "l" else -1
    rest_x = g.width
    p[f"foot_{fs}"] = {"pos": (sf * (rest_x + FREE_OUT), FREE_UP, pl["pos"][2] - FREE_BACK),
                       "rot": (sf * FREE_YAW, FREE_HEEL, 0), "toe": 0.0, "pole": (sf * 0.6, 0, 1)}
    return p, weapon


def clips(rig, want):
    out = []
    for side in "lr":
        name = f"pivot_warden_{side}"
        if want and not any(w in name for w in want):
            continue
        p, weapon = pose(rig, side)
        mt = {"weapon": weapon, **RUN_GRIPS.get("run_warden", {})}
        rot, pos = solve_frames(rig, [p, p], loop=True, weapon=weapon, tilt=float(mt.get("grip_tilt", 0.0)))
        m = {"layer": "full", "speed": 0.0, "cycle": 1 / 30.0, "steps": 0, "source": "keyed (tools/anim/clips/pivot.py)",
             "licence": "own work"}
        m.update(mt)
        out.append(Clip(name, 30, rot, pos, loop=True, meta=m))
    return out
