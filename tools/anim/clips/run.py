"""Her runs: a carriage for each calling, and the way each weapon is
carried at a run (tools/anim/gait.py).

- Warden: heavy plate. Square shoulders, a wider, flatter, harder stride,
  the shield held up across the body; the weight lands.
- Arcanist: poise. Upright, chin up, feet on one line, the hips swaying,
  the staff held still in one hand and the other hand open and loose.
- Reaver: feral. Pitched forward and hunched, a short fast cadence, big
  knee drive and the arms pumping with the axes.
- Stalker: a predator's glide. Low in the knees, long and smooth with
  little bounce, the head level and forward.
"""
from __future__ import annotations

import math
from dataclasses import replace

import numpy as np

from gait import Gait, arc_of, run_cycle

SPEED = 5.1  # her skeleton's metres a second: 5.3 in the world (she stands 1.04 times her model)


def _dir(up_deg, out=0.0):
    a = math.radians(up_deg)
    v = np.array([out, math.sin(a), math.cos(a)])
    return tuple(v / np.linalg.norm(v))


def _perp(up_deg, out=0.0):
    """The knuckles' line for a blade at up_deg: square to it, below it."""
    a = math.radians(up_deg - 90)
    v = np.array([out * 0.3, math.sin(a), math.cos(a)])
    return tuple(v / np.linalg.norm(v))


def blade_carry(out=-1.0, up_back=0.35, up_fwd=0.5, swing=None, tuck=0.0):
    """A blade carried in the swinging hand as a running hand carries one:
    the wrist straight in the grip and the forearm rolled so the thumb side
    faces out and up (`out`: -1 her right, +1 her left), so the blade rides
    out and ahead of her, rising as the fist comes through and dipping as
    it goes back, never across her legs. `swing`: the fist's own path (back,
    forward: from the shoulder, in the chest's frame, as for her right hand),
    held steadier than the free arm's: a hand behind her with the wrist
    straight can only point a blade down or across her, so a long blade's
    hand stays at her side. (Keyed by direction, up over her shoulder behind
    her, it asked a wrist bent back past what one can, and the hand flapped
    from one side to the other.) `tuck`: the elbow drawn in toward her side
    as the fist goes back (the pole's sideways part, toward the middle, all
    of it with the fist back and none with it forward), so the forearm runs
    straight ahead from it, not in across her: the hilt and its cross ride
    beside her hip, not into it and her thigh."""
    def f(ph, k, hand):
        hand = dict(hand)
        hand.update({"thumb": (out, up_back + (up_fwd - up_back) * k, 0.0), "frame": "chest", "twist": 0.5})
        e = k * k * (3 - 2 * k)
        if swing is not None:
            back, fwd = np.array(swing[0], float), np.array(swing[1], float)
            v = (back + (fwd - back) * e) * [-out, 1, 1]
            v[1] += 0.03 * math.sin(math.pi * k)
            hand["arc"] = arc_of(v)
        if tuck:
            hand["pole"] = tuple(np.array(hand["pole"], float) + [-out * tuck * (1 - e), 0.0, 0.0])
        else:
            hand["pole"] = tuple(np.array(hand["pole"]))
        return hand
    return f


# The long blades' hands: the sword at her side and ahead; the reaver's axe
# pumped harder, but still never far behind her. The warden's sword fist
# rides back 4-5 cm out from her hip and 4 cm higher, its elbow tucked in
# behind it (blade_carry's tuck), so the pommel and cross pass clear of her
# side, the plates at her hip and the thigh driving up (the oath's longer
# pommel too; at the old line they went 2-5 cm into her, the fist 5); and
# forward it comes no further in than her shoulder's line, a touch lower,
# its cross clear of the shield's rim (3 cm; it touched).
SWORD_SWING = ((-0.045, -0.30, 0.0), (0.0, -0.22, 0.25))
SWORD_TUCK = 0.45
AXE_SWING = ((0.02, -0.30, -0.08), (0.0, -0.10, 0.31))


def _swivel(h, phi):
    """A pole (chest frame) that swings the elbow phi degrees about shoulder-to-hand (h, from the
    shoulder) from her left: far out, so the elbow goes exactly there."""
    d = np.array(h, float) / np.linalg.norm(h)
    ref = np.array([1.0, 0, 0]) - d * d[0]
    ref /= np.linalg.norm(ref)
    a = math.radians(phi)
    return tuple(20.0 * (math.cos(a) * ref + math.sin(a) * np.cross(d, ref)))


def shield_guard(side="l", hand_at=(-0.02, -0.20, 0.38), swivel=-20, lift=0.0, fwd=0.0):
    """The shield up across the body, riding the step a little. It rides the
    forearm's hinge (its face is the plane of shoulder, elbow and wrist), so
    the guard is set by where the hand goes and how the elbow swings, never
    by the hand's aim: the hand well out ahead and the elbow open (120-130
    degrees) and out, so the disc stays clear of her own shoulder. (With the
    elbow near square it reached over the shoulder, through the pauldron.)
    The hand rides the forearm, the wrist straight in the grip."""
    def f(ph, k, hand):
        h = (hand_at[0], hand_at[1] + lift + 0.015 * math.cos(4 * math.pi * ph), hand_at[2] + fwd)
        return {"arc": arc_of(h), "pole": _swivel(h, swivel), "frame": "chest"}
    return f


def staff_hold():
    """The staff upright in the right fist at her side, tipped forward, the
    arm barely swinging."""
    def f(ph, k, hand):
        sway = 0.03 * (k - 0.5)
        return {"arc": arc_of((0.02, -0.40, 0.10 + sway)), "pole": (-0.3, -0.1, -1.0),
                "blade": (0.05, 0.94, 0.33), "knuckles": (0.0, -0.33, 0.94), "frame": "chest", "twist": 0.5}
    return f


def crossbow_low():
    """The crossbow low in the right hand, pointing at the ground ahead."""
    def f(ph, k, hand):
        sway = 0.06 * (k - 0.5)
        return {"arc": arc_of((0.0, -0.36, 0.14 + sway)), "pole": (-0.4, -0.2, -1.0),
                "knuckles": (0.0, -0.55, 0.83), "blade": (0.0, 0.83, 0.55), "frame": "chest", "twist": 0.5}
    return f


def open_hand():
    def f(ph, k, hand):
        return hand
    return f


WARDEN = Gait(frames=21, speed=SPEED, duty=0.33, drop=0.09, bob=0.05, lean=19, spine_lean=4, hip_yaw=6, hip_roll=3,
              hip_shift=0.02, chest_yaw=6, width=0.08, reach=0.38, kick=0.36, knee=0.28, shoulders=(4, 4),
              fingers="fist")
ARCANIST = Gait(frames=20, speed=SPEED, duty=0.30, drop=0.05, bob=0.06, lean=13, spine_lean=2, hip_yaw=8, hip_roll=5.5,
                hip_shift=0.03, chest_yaw=7, width=0.03, reach=0.34, kick=0.40, knee=0.30, head_up=4,
                arm_fwd=(0.0, -0.20, 0.25), arm_back=(0.0, -0.32, -0.22), elbow_out=0.25, fingers="open")
REAVER = Gait(frames=19, speed=SPEED, duty=0.30, drop=0.10, bob=0.08, lean=32, spine_lean=12, hip_yaw=11, hip_roll=4,
              hip_shift=0.025, chest_yaw=14, width=0.07, reach=0.36, kick=0.48, knee=0.36, shoulders=(8, 10),
              arm_fwd=(0.0, -0.06, 0.34), arm_back=(0.04, -0.24, -0.32), elbow_out=0.5, fingers="fist")
STALKER = Gait(frames=20, speed=SPEED, duty=0.34, drop=0.14, bob=0.035, lean=26, spine_lean=8, hip_yaw=8,
               hip_roll=4.5, hip_shift=0.025, chest_yaw=8, width=0.045, reach=0.40, kick=0.38, knee=0.26,
               head_up=6, arm_fwd=(0.0, -0.18, 0.26), arm_back=(0.03, -0.30, -0.24), elbow_out=0.2)

# The runs the game asks for: calling and what is in hand.
RUNS = {
    "run_warden": (WARDEN, {"r": blade_carry(swing=SWORD_SWING, tuck=SWORD_TUCK), "l": shield_guard(lift=0.04, fwd=-0.005)}, "sword+shield"),
    "run_reaver": (REAVER, {"r": blade_carry(up_fwd=0.75, swing=AXE_SWING)}, "axe"),
    "run_reaver_axes": (REAVER, {"r": blade_carry(up_fwd=0.75, swing=AXE_SWING), "l": blade_carry(1.0, up_fwd=0.75, swing=AXE_SWING)}, "axes"),
    "run_arcanist": (ARCANIST, {"r": staff_hold()}, "staff"),
    "run_arcanist_wand": (ARCANIST, {"r": blade_carry()}, "wand"),
    "run_stalker": (STALKER, {"r": crossbow_low()}, "crossbow"),
    "run_stalker_daggers": (STALKER, {"r": blade_carry(), "l": blade_carry(1.0)}, "daggers"),
    # In town, weapons sheathed: her calling's carriage, the arms swinging free.
    "run_warden_town": (replace(WARDEN, fingers="relaxed", arm_fwd=(-0.04, -0.20, 0.27), arm_back=(0.11, -0.25, -0.21), elbow_out=0.22), {}, ""),
}

# The sprint's own arms where they differ from the run's (sprint_stop applies these over RUNS).
# The shield hand sits back toward her (run 2.5 cm, sprint 2 cm from the first pass) so the
# elbow stays bent: at most 124 degrees in the run, 119 in the sprint (a judge's bar: 125/120).
SPRINT_ARMS = {"run_warden": {"l": shield_guard(lift=0.08, fwd=0.0)}}


def clips(rig, want):
    out = []
    for name, (g, arms, weapon) in RUNS.items():
        if want and not any(w in name for w in want):
            continue
        out.append(run_cycle(name, rig, replace(g, arms=arms), {"weapon": weapon}))
    return out
