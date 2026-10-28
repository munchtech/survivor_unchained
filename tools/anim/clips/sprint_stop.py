"""Faster than her run, and stopping out of it.

- sprint_<calling>[_<weapon>]: each run's own carriage pushed: a longer, lower stride,
  more lean, the arms driving harder. The same number of frames as her run,
  in step with it (the left foot lands at the start of both), so the game
  can blend the two by speed without the legs fighting.
- stop_<calling>_l / _r: out of the run onto the front foot (the left or
  the right, whichever was coming down), the body carried on over it and
  braking back, the back foot brought through beside it, a rebound, and the
  weight settling, the arms in the calling's hold throughout.
"""
from __future__ import annotations

from dataclasses import replace

import math

import numpy as np

from clips import idle
from clips.run import POST, REAVER_CARRY, RUN_GRIPS, RUNS, SPRINT_ARMS, WARDEN_CARRY
from gait import arc_of, run_cycle
from keyed import build

CALLINGS = {"warden": "run_warden", "arcanist": "run_arcanist", "reaver": "run_reaver", "stalker": "run_stalker",
            "warden_town": "run_warden_town"}


# The sprint's swing from the run's: forward +th, forward elbow +deg, the back upper arm x, back elbow +deg.
SPRINT_SWING = (5, -3, 1.25, -3)
# Per run where it differs: the town sprint's back swing a little short of the run's (x0.9), or the elbow comes through the
# shield slung on her back (judge r3: 3-5 mm through at ph0 and ph50 at x1.25).
# A fifth number: the free (left) upper arm's out, both ends, +deg. The axes sprint's hung second axe 5 in: at the run's 14 (+1 back)
# the sprint's elbow swung round 25 deg further out, the forearm turned in, and the head came in onto her knee (anim 44
# solver 7c). Animation 56 (the low point): the left arm swings its second axe like the first, so it takes the
# default swing and 3 out (at the old 5 in its upper arm met her side, 3 mm, in the sprint).
SPRINT_SWING_RUN = {"run_warden_town": (5, -3, 0.9, -3), "run_reaver_axes": (-8, -3, 1.25, -3, -5), "run_reaver_town": (5, -3, 1.25, -3, 3), "run_stalker_town": (5, -3, 1.25, -3, 8)}
# Animation 57: the warden's high carry (run.WARDEN_CARRY) takes its sword arm 3 further out in the sprint (at the run's 29
# its upper arm went 5 mm into her plate at the forward drive, motion --outfits); the low and belt carries keep the default.
if REAVER_CARRY == "low":  # Animation 56/57's low point (REAVER_CARRY; "trail" keeps Animation 55's entries above)
    SPRINT_SWING_RUN["run_reaver"] = (5, -3, 1.0, -3, 0, 9)
    SPRINT_SWING_RUN["run_reaver_axes"] = (5, -3, 1.0, -3, 10, 9)
if REAVER_CARRY == "high":  # Animation 58: the back elbow 7 closer (at the default 3 the back swing dropped her
    # forearm to 29-32 below level, and the high carry's wrist bent 15-19 to the thumb); the axe arms 6 further out, the
    # free one 5 (at 3 the upper arms went 5-7 mm into her side, at 3/5 the free one 1; motion --outfits).
    SPRINT_SWING_RUN["run_reaver"] = (5, -3, 1.25, -7, 5, 6)
    SPRINT_SWING_RUN["run_reaver_axes"] = (5, -3, 1.25, -7, 6, 6)
if WARDEN_CARRY == "high57":
    SPRINT_SWING_RUN["run_warden"] = (5, -3, 1.25, -3, 0, 3)
if WARDEN_CARRY == "high":  # Animation 58: 4 (at 3 its upper arm went 7 mm into her plate)
    SPRINT_SWING_RUN["run_warden"] = (5, -3, 1.25, -3, 0, 4)


# The Stalker's left elbow in the stops (chest frame; the idle's is (0, -0.5, -1)).
STALKER_STOP_POLE_L = (0.6, -0.5, -0.8)

def sprint(rig, run):
    """The sprint for one of her runs (run_<calling>[_<weapon>])."""
    g, arms, weapon = RUNS[run]
    arms = {**arms, **SPRINT_ARMS.get(run, {})}
    # The arms drive further, but the elbow stays bent, as a sprinter's does:
    # an arm flung out straight behind her has no hinge to read, and the
    # forearm rolled over as it bent again.
    I = rig.I
    reach = 0.85 * sum(float(np.linalg.norm(rig.prest[I[b]] - rig.prest[I[a]]))
                       for a, b in (("upperarm_r", "lowerarm_r"), ("lowerarm_r", "hand_r")))

    def held(v):
        v = np.array(v, float)
        n = float(np.linalg.norm(v))
        return tuple(v * min(1.0, reach / n))

    s = replace(g, arms=arms, speed=g.speed * 1.45, duty=g.duty - 0.05, lean=g.lean + 8, kick=g.kick + 0.06,
                knee=g.knee + 0.06, reach=g.reach + 0.08, bob=g.bob + 0.01,
                arm_fwd=held(np.array(g.arm_fwd) * [1, 0.8, 1.2]), arm_back=held(np.array(g.arm_back) * [1, 1.1, 1.25]))
    if g.swing is not None:
        # The sprint's arms by their joints: the upper arm further forward and back, the elbow a little closer.
        k = SPRINT_SWING_RUN.get(run, SPRINT_SWING)

        def sped(sw, o=0):  # (o: the upper arm's extra out, +deg; k[4] for the left, k[5] for the right)
            (ft, fo, fe, fr), (bt, bo, be, br) = sw
            return ((ft + k[0], fo + o, fe + k[1], fr), (bt * k[2], bo + 1 + o, be + k[3], br))
        s = replace(s, swing=sped(g.swing, k[4] if len(k) > 4 else 0), swing_r=None if g.swing_r is None else sped(g.swing_r, k[5] if len(k) > 5 else 0))
    clip = run_cycle("sprint" + run[3:], rig, s, {"weapon": weapon, **RUN_GRIPS.get(run, {})})
    # (The run's post-pass too: the warden's town hand on her sword's hilt, run.hilt_carry.)
    return POST[run](rig, clip) if run in POST else clip


# The stops' left fingers closed onto her hip frame by frame (deg; idle.hip_layer's `curl`): with the hand kept on her
# pelvis they stood 4-10 mm off as her legs braked under them, the little finger 2.9 mm in at stop_l f4 (judge
# l31-hip). Fitted from the gaps (atan((gap - 1.8 mm) / finger length), 3-frame smoothed, neighbours within 3 deg).
ARC_STOP_CURL = {
    "l": {
        "index": [4.0, 4.2, 4.5, 4.8, 4.7, 4.7, 4.5, 4.3, 4.2, 3.9, 3.7, 3.5, 3.3, 2.9, 2.6, 2.2, 2.0, 1.9, 1.8, 1.7, 1.7, 1.7, 1.7, 1.7, 1.7],
        "middle": [4.7, 5.0, 5.5, 5.7, 6.0, 5.9, 5.5, 5.2, 5.0, 4.8, 4.5, 4.3, 4.0, 3.7, 3.4, 3.2, 3.0, 2.8, 2.7, 2.6, 2.6, 2.6, 2.6, 2.6, 2.6],
        "ring": [5.4, 6.0, 6.6, 6.5, 6.6, 6.6, 6.2, 5.7, 5.6, 5.2, 4.8, 4.5, 4.1, 3.5, 3.1, 2.6, 2.4, 2.1, 2.0, 2.0, 2.0, 1.9, 1.9, 1.9, 1.9],
        "pinky": [3.4, 5.0, 7.1, 7.0, 7.1, 7.1, 5.2, 4.7, 2.7, 0.7, 2.6, 4.9, 7.4, 8.0, 8.0, 8.0, 7.4, 7.1, 6.8, 6.7, 6.6, 6.5, 6.6, 6.6, 6.6],
    },
    "r": {
        "index": [-1.4, -1.1, -0.5, 0.2, 0.8, 1.7, 2.3, 2.8, 2.7, 2.6, 2.3, 2.1, 2.0, 1.8, 1.6, 1.4, 1.2, 1.1, 1.0, 0.9, 0.9, 0.8, 0.8, 0.8, 0.8],
        "middle": [-0.7, -0.4, 0.1, 0.8, 1.6, 2.4, 2.9, 3.3, 3.4, 3.4, 3.3, 3.1, 2.9, 2.7, 2.4, 2.2, 2.0, 1.9, 1.7, 1.6, 1.6, 1.5, 1.5, 1.5, 1.5],
        "ring": [-1.1, -1.0, -0.7, -0.2, 0.5, 1.6, 2.5, 3.1, 3.1, 3.0, 2.8, 2.7, 2.5, 2.3, 2.1, 1.8, 1.5, 1.2, 1.0, 0.8, 0.7, 0.6, 0.6, 0.6, 0.6],
        "pinky": [-0.7, -0.7, 0.2, 1.5, 3.7, 5.8, 8.0, 8.0, 8.0, 8.0, 8.0, 8.0, 7.5, 7.1, 6.4, 5.8, 5.3, 4.9, 4.6, 4.2, 3.9, 3.6, 3.6, 3.6, 3.6],
    },
}


# Her staff's line through the stops (her character's frame, as idle_arcanist's): 3 deg nearer upright than the
# idle's, so the shaft's foot clears her right leg as it comes through (101 mm or more; at the idle's own aim 46 mm at f9
# of the left stop), the crescent still 148 mm or more outside her brim as she pitches over the fist. (13 Oct it was
# (-0.10, 1.0, 0.04) in the chest's frame, leant out past the brim; animation 46.)
# (Animation 47: per idle.ARC_CAND, its "stop_blade"; R1's (-0.30, 1.0, -0.07).)
STOP_ARC_BLADE = idle._ARC["stop_blade"]
# (Animation 48, the tilted grip: on the first key only, the staff arm 6 deg further out, its elbow pole 0.3 toward her
# right and the staff 0.05 further forward (the face stays clear), so the upper arm clears the warden's and the reaver's trunk as she pitches over at the landing; 0 mm, was 6 and 5.)
ARC_DX0 = 6.0
BX0 = 0.0
BZ0 = 0.05
POLE_DX0 = -0.3
# (Animation 49: from the second key on, the staff arm's arc turned against the chest's pitch (1.0: wholly, the arm
# hung from the shoulder as the idle's whatever the lean), so the thrown-back lean no longer lifts the fist to a shelf.)
STOP_HOLD = 1.0
# (And the staff's head eased back (its aim's z, keys 9 and 15) per side: with the fist held back the shaft's foot met
# her right leg as it came through on the left stop; its head back also clears her cheek from 45. With the back foot's
# key restored (animation 49) the staff passes 24 mm from that leg at 0.30 s, never touching; right stop 112 mm.)
STOP_BACK = {"l": (0.08, 0.05), "r": (0.0, 0.0)}


def _warden_town_stop(t, f):
    """The town warden's stop lands with her arms free and easy at her sides (the warden town stand's arms before
    Animation 50-52 restaged it round her pelvis: its arms are now a make(rig, base) riding the stand's own sway, and
    its left fist is closed on the sword by a post pass, neither of which a stop's single key can carry). Kept as it
    was so the stops build unchanged."""
    sw = 0.012 * math.sin(2 * math.pi * t * 2)
    return {
        "hand_l": {"arc": arc_of((0.16, -0.46, 0.08 + sw)), "pole": (0.3, -0.2, -1.0), "frame": "chest",
                   "thumb": idle._n((-0.15, -0.1, 1.0)), "twist": 1.0},
        "hand_r": {"arc": arc_of((-0.14, -0.46, 0.08 - sw)), "pole": (-0.3, -0.2, -1.0), "frame": "chest",
                   "thumb": idle._n((0.15, -0.1, 1.0)), "twist": 1.0},
        "fingers_l": "relaxed", "fingers_r": "relaxed",
    }


# A stop's arms (one key, over(t, f)) where its calling's idle arms aren't one (Animation 52).
STOP_ARMS = {"warden_town": _warden_town_stop}


def stop(rig, calling, side):
    """Planting the `side` foot out of the run."""
    if calling == "arcanist":
        idle.base_of(rig, "arcanist")  # (on a restaged stand, idle.ARC_ST, its free hand is read off the base)
    arms = (STOP_ARMS.get(calling) or idle.IDLES[f"idle_{calling}"][1])(0, 0)
    if calling == "arcanist":
        arms["hand_r"] = {**arms["hand_r"], "blade": idle._n(idle._ARC.get(f"stop_blade_{side}", STOP_ARC_BLADE))}
    s = 1 if side == "l" else -1
    front, back = f"foot_{side}", f"foot_{'r' if side == 'l' else 'l'}"
    w = 0.09 if calling == "warden" else 0.05

    if calling == "arcanist":
        g0, _ = rig.sk.fk(idle.base_of(rig, "arcanist").rot[:1], idle.base_of(rig, "arcanist").pos[:1])
        stand = idle.chest_pitch(rig, g0, 0)   # (the idle's chest pitch, 4.4 deg forward on S2H2)

    def p(fz, bz, by, btoe, hy, hz, lean, roll=0.0, brot=-25, out=0.0, pole_dx=0.0, head_back=0.0):
        a = arms
        if not pole_dx and calling == "arcanist" and "tilt" in idle._ARC:
            # After the landing the staff arm held against the trunk's lean, as the idle's (its arc is in the chest's
            # frame): thrown back -7 at 0.30 s, the arm swung forward with the chest, the forearm near level and the
            # fist up at her under-bust, "holding the staff out to someone" (max judge, animation 49). Now the shoulder
            # extends with the lean, the elbow back at her side, the fist down and back toward her hip.
            hr = arms["hand_r"]
            a = {**arms, "hand_r": {**hr, "arc": idle.pitched(hr["arc"], stand - lean * STOP_HOLD),
                                    "blade": (hr["blade"][0], hr["blade"][1], hr["blade"][2] - head_back)}}
        if pole_dx and calling == "arcanist" and "tilt" in idle._ARC:
            hr = arms["hand_r"]
            ax = ARC_DX0
            a = {**arms, "hand_r": {**hr, "pole": (hr["pole"][0] + pole_dx, hr["pole"][1], hr["pole"][2]),
                                    "arc": (hr["arc"][0] - ax, hr["arc"][1], hr["arc"][2]),
                                    "blade": (hr["blade"][0] + BX0, hr["blade"][1], hr["blade"][2] + BZ0)}}
        if calling == "stalker" and isinstance(arms.get("hand_l"), dict):
            # (The left elbow turned a little out as she brakes: by her side as in the idle, the inner upper arm
            # pressed 4.5 mm into her side as the lean was thrown back.)
            a = {**arms, "hand_l": {**arms["hand_l"], "pole": STALKER_STOP_POLE_L}}
        if out and calling == "warden":
            # The sword hand carried 15 mm out from her right thigh through the stop (14 Oct: with the hilt seated in
            # the fist's hollow, 12 mm nearer the palm, it came 7-12 mm from the thigh, inside the skirt, as she
            # landed, braked and settled with her hips forward; the game blends the stop's ends with the run and idle).
            a = {**arms, "hand_r": {**arms["hand_r"], "arc": arc_of(np.add(idle.WARDEN_HAND_R, (-out, 0.0, 0.0)))}}
        return {**a,
                front: {"pos": (s * w, 0, fz), "rot": (s * 6, 0, 0)},
                back: {"pos": (-s * (w + 0.06), by, bz), "rot": (-s * 10, brot, 0), "toe": btoe},
                "hips": {"pos": (s * 0.02, hy, hz), "rot": (s * 4, lean * 0.4, roll)},
                "spine": (0, lean * 0.6, -roll), "head": (0, -lean * 0.5, 0)}

    keys = [
        # Coming down on the front foot, the back leg still behind.
        (0, p(0.34, -0.48, 0.12, 25, -0.08, 0.04, 16, out=0.015, pole_dx=POLE_DX0), "auto"),
        # Over it and braking: the body carried on, the back foot coming through.
        (5, p(0.30, -0.12, 0.10, 10, -0.13, 0.12, 4, roll=2, out=0.015), "auto"),
        # Down beside it, the weight back on the heels, the lean thrown back.
        (9, p(0.26, 0.10, 0.0, 0, -0.12, 0.10, -7, brot=0, out=0.015, head_back=STOP_BACK[side][0]), "auto"),
        # The rebound and the settle.
        (15, p(0.20, 0.06, 0.0, 0, -0.05, 0.06, 4, brot=0, out=0.015, head_back=STOP_BACK[side][1]), "auto"),
        (24, p(0.16, 0.00, 0.0, 0, -0.04, 0.03, 1, brot=0, out=0.015), "ease"),
    ]
    meta = {"layer": "full", "weapon": idle.IDLES[f"idle_{calling}"][2]}
    if calling == "arcanist":
        meta.update(idle.arc_grip())   # (the idle's grip: the staff tilted in her fist as the idle holds it, animation 48)
    if calling == "reaver":
        meta.update(idle.axe_grip())   # (the idle's grip: the fist 13 cm up the haft, as idle_reaver holds it, animation 57)
    if calling == "stalker":
        # (Her left hand kept on the crossbow's fore-stock as she brakes: idle.ride_stock.)
        return idle.ride_stock(rig, lambda post: build(f"stop_{calling}_{side}", rig, keys, meta=meta, post=post))
    clip = build(f"stop_{calling}_{side}", rig, keys, meta=meta)
    if calling == "arcanist":
        # Her left hand kept on her hip as the hips brake and rock under her (it floated 10-17 mm off in the chest's frame).
        # (On a restaged stand, idle.ARC_ST: the idle's free hand kept on her pelvis the same way; no curl, no contact.)
        # (The free hand, chest-held on the restaged stand, held against the lean the same way from the landing on: at
        # 0.30 s it was swung out ahead of her, "thrown out", max judge, animation 49; at the landing as it passed.)
        clip = idle.hip_layer(rig, clip, lambda f: 1.0, curl=ARC_STOP_CURL[side],
                              upright=lambda f, P: P + min(1.0, f / 5.0) * (stand - P))
    return clip


def clips(rig, want):
    out = []
    for run in RUNS:
        name = "sprint" + run[3:]
        if not want or any(w in name for w in want):
            out.append(sprint(rig, run))
    for c in CALLINGS:
        for side in "lr":
            name = f"stop_{c}_{side}"
            if not want or any(w in name for w in want):
                out.append(stop(rig, c, side))
    return out
