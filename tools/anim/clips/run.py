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
    arm barely swinging. The hand 80 mm out to her right of where it was (x 0.02): with
    the fist closed on the shaft (WRAP["staff"], 17 October) its fingers went 80 mm into
    her right thigh as it came through (motion.py; 50 with the hand open), now 0.3."""
    def f(ph, k, hand):
        sway = 0.03 * (k - 0.5)
        return {"arc": arc_of((-0.08, -0.40, 0.10 + sway)), "pole": (-0.3, -0.1, -1.0),
                "blade": (0.05, 0.94, 0.33), "knuckles": (0.0, -0.33, 0.94), "frame": "chest", "twist": 0.5}
    return f


def crossbow_low():
    """The crossbow low in the right hand, pointing at the ground ahead, carried out beside her right
    thigh (9 cm out, 2 cm higher; under her it sat 76 mm in the thigh as it drove up), the elbow by her ribs."""
    def f(ph, k, hand):
        sway = 0.06 * (k - 0.5)
        return {"arc": arc_of((-0.09, -0.34, 0.15 + sway)), "pole": (-0.2, -0.3, -1.0),
                "knuckles": (0.0, -0.55, 0.83), "blade": (0.0, 0.83, 0.55), "frame": "chest", "twist": 0.5}
    return f


def open_hand():
    def f(ph, k, hand):
        return hand
    return f


# Each calling's arm swing by its joints (gait.Gait.swing: forward, back = upper arm forward of hanging,
# out from her side, the elbow's inside angle, the upper arm turned in; chest frame): a natural run's arms,
# the elbows near square and close to her ribs, the fist ahead of the shoulder through the swing, in toward
# her middle and under her bust in front, by her hip behind. (Their old keys flared the elbows 35-55 degrees
# out and swung the fist 0.8-1.3 arm-lengths fore and aft: "chicken wing", "weird exaggerated arm movements".)
# (Round 2, animation 37: behind her the elbow closes to 65-75 and the forearm turns out (turn -25/-30), so the
# fist rides up and out past her hip; at 85-90 and turned in it went 45-80 mm into the thigh driving through.
# The Reaver leans 14+3, not 32+12: bent that far her own thigh came up into her hand, and from the play camera's
# 53-degree look down 24+8 still read as a stoop (judge r2).)
# The town run carries the shield slung on her back (Arms.cs Back socket, 66 cm across): the elbow no further than
# about 12 cm behind the shoulder, or it comes out through the shield's face (judge r2: at -36 it did, 27 mm; the
# sprint 56). The swing a touch further forward instead.
SWING = ((8, 12, 80, 20), (-20, 14, 70, -22))
# A heavy axe's arm (judge r2: the axe elbow winged out 30-35 degrees at the close-up): in by her side, half the
# free arm's swing, the forearm barely turned out.
AXE_ARM = ((6, 10, 80, 10), (-20, 11, 70, -10))
WARDEN = Gait(frames=21, speed=SPEED, duty=0.33, drop=0.09, bob=0.05, lean=19, spine_lean=4, hip_yaw=6, hip_roll=3,
              hip_shift=0.02, chest_yaw=6, width=0.08, reach=0.38, kick=0.36, knee=0.28, shoulders=(4, 4),
              fingers="fist", swing=((6, 14, 85, 20), (-32, 15, 75, -25)))
ARCANIST = Gait(frames=20, speed=SPEED, duty=0.30, drop=0.05, bob=0.06, lean=13, spine_lean=2, hip_yaw=8, hip_roll=5.5,
                hip_shift=0.03, chest_yaw=7, width=0.03, reach=0.34, kick=0.40, knee=0.30, head_up=4,
                arm_fwd=(0.0, -0.20, 0.25), arm_back=(0.0, -0.32, -0.22), elbow_out=0.25, fingers="open",
                swing=((6, 10, 80, 25), (-30, 12, 70, -25)))
REAVER = Gait(frames=19, speed=SPEED, duty=0.30, drop=0.10, bob=0.08, lean=14, spine_lean=3, hip_yaw=11, hip_roll=4,
              hip_shift=0.025, chest_yaw=8, width=0.07, reach=0.36, kick=0.48, knee=0.36, shoulders=(8, 10),
              arm_fwd=(0.0, -0.06, 0.34), arm_back=(0.04, -0.24, -0.32), elbow_out=0.5, fingers="fist",
              swing=((10, 14, 75, 20), (-36, 15, 65, -30)))
STALKER = Gait(frames=20, speed=SPEED, duty=0.34, drop=0.14, bob=0.035, lean=26, spine_lean=8, hip_yaw=8,
               hip_roll=4.5, hip_shift=0.025, chest_yaw=8, width=0.045, reach=0.40, kick=0.38, knee=0.26,
               head_up=6, arm_fwd=(0.0, -0.18, 0.26), arm_back=(0.03, -0.30, -0.24), elbow_out=0.2,
               swing=((6, 10, 80, 20), (-32, 12, 70, -25)))

# The runs the game asks for: calling and what is in hand.
RUNS = {
    "run_warden": (WARDEN, {"r": blade_carry(swing=SWORD_SWING, tuck=SWORD_TUCK), "l": shield_guard(lift=0.04, fwd=-0.005)}, "sword+shield"),
    "run_reaver": (replace(REAVER, swing_r=AXE_ARM), {"r": blade_carry(up_fwd=0.75)}, "axe"),
    "run_reaver_axes": (replace(REAVER, swing=AXE_ARM), {"r": blade_carry(up_fwd=0.75), "l": blade_carry(1.0, up_fwd=0.75)}, "axes"),
    "run_arcanist": (replace(ARCANIST, fingers_r="grip"), {"r": staff_hold()}, "staff"),
    # The wand fist turned further out behind her (judge r2: it brushed her buttock's outline at the close-up).
    "run_arcanist_wand": (replace(ARCANIST, swing_r=((6, 10, 80, 25), (-30, 13, 70, -35))), {"r": blade_carry()}, "wand"),
    # The free left hand a fist and closer behind (its open fingers met her thigh, 7 mm; 31 in the sprint).
    "run_stalker": (replace(STALKER, fingers="fist", fingers_r="relaxed", swing=((6, 10, 80, 20), (-30, 12, 62, -35))),
                    {"r": crossbow_low()}, "crossbow"),
    # Both fists closed on the daggers ("grip": each the fitted dagger fist, keyed.wrap_of: WRAP["daggers"] right,
    # WRAP["daggers_l"] left; with the gait's relaxed hands the fingers stood 10-73 mm off the hilts).
    "run_stalker_daggers": (replace(STALKER, fingers="grip"), {"r": blade_carry(), "l": blade_carry(1.0)}, "daggers"),
    # In town, weapons sheathed: her calling's carriage, the arms swinging free.
    "run_warden_town": (replace(WARDEN, fingers="relaxed", swing=SWING), {}, ""),
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
