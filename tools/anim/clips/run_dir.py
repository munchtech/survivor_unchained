"""(aim-move) Her directional run set: the Warden's run keyed at a heading in her hips' frame (gait.Gait.heading).

The game (godot/logic/Play/DirLegs.cs) yaws her pelvis part of the way toward her travel and plays these for the rest:
forward (run_warden itself), forward-left and forward-right (45), the backpedal (180) and back-left and back-right (135),
all on one stride phase (0 = the left foot down) so any two blend foot for foot. The backpedal is quicker and shorter
than the run (14 frames, 4.3 steps a second; flight 2.8 frames a step): a run reversed held a 5-frame split (judge r1).
"""
from __future__ import annotations

from dataclasses import replace

from clips.run import BACK_ARM, BACK_ARMS, RUN_GRIPS, RUNS, WARDEN_CARRY
from gait import run_cycle

# The backpedal's carriage (over the run's): low and athletic, the body a touch forward, quick short steps.
BACK = dict(frames=14, duty=0.30, lean=5.0, spine_lean=2.0, drop=0.11, bob=0.035, hip_yaw=4.0, chest_yaw=4.0,
            reach_back=0.33, kick_back=0.26, width=0.09)
DIAG = dict(width=0.09)
HEADINGS = {"fl": (45, DIAG), "fr": (-45, DIAG), "b": (180, BACK), "bl": (135, BACK), "br": (-135, BACK)}
SOURCES = ("run_warden",)


def clips(rig, want):
    out = []
    for src in SOURCES:
        g, arms, weapon = RUNS[src]
        for tag, (h, over) in HEADINGS.items():
            name = f"{src}_{tag}"
            if want and not any(w in name for w in want):
                continue
            back = abs(h) > 90
            sw = {"swing_r": BACK_ARM} if back and BACK_ARM and src == "run_warden" and WARDEN_CARRY == "wrist" else {}
            gd = replace(g, arms={**arms, **BACK_ARMS.get(src, {})} if back else arms, heading=float(h), **over, **sw)
            out.append(run_cycle(name, rig, gd, {"weapon": weapon, "heading": h, **RUN_GRIPS.get(src, {})}))
    return out
