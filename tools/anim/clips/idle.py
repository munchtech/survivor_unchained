"""Her signature idles: a captured way of standing (100STYLE, CC BY 4.0) for
each calling's body, the arms re-solved to hold what that calling holds,
its way. The capture brings the weight shifts and the breath; the arms
ride the chest as it moves.

- Warden: Heavyset (tensed, square, settled). The shield at rest at her
  left side, its face turned a little to the front, off her body; the
  sword low at her right, point toward the ground ahead.
- Arcanist: Strutting (chin up, a little back, at ease). The staff upright
  at her side, the free hand on her hip.
- Reaver: Angry (tense, restless). The axe on her shoulder, its head
  behind her, the left hand a fist.
- Stalker: Crouched (low, ready). The crossbow low across her, the left
  hand under its stock.
"""
from __future__ import annotations

import math

import numpy as np

from clips.mocap import idle_loop
from gait import arc_of
from rig import Clip


def layered(name, rig, base: Clip, over, meta=None) -> Clip:
    """A clip with every frame of `base` under the controls `over(t, frame)`
    gives (hands, fingers, any extra turns)."""
    from keyed import solve_frames
    n = base.frames
    rot, pos = solve_frames(rig, [over(f / max(n - 1, 1), f) for f in range(n)], [(base.rot[f], base.pos[f]) for f in range(n)],
                            loop=base.loop, weapon=(meta or {}).get("weapon", ""))
    m = dict(base.meta)
    m.update(meta or {})
    return Clip(name, base.fps, rot, pos, loop=base.loop, meta=m)


def _n(v):
    v = np.array(v, float)
    return tuple(v / np.linalg.norm(v))


# Her sword hand at rest (chest frame), shared with the stops (sprint_stop.py).
WARDEN_HAND_R = (-0.09, -0.45, 0.04)


def warden(t, f):
    breath = 0.008 * math.sin(2 * math.pi * t * 2)
    return {
        # The shield at rest at her left side, off her body: the elbow out
        # about 19 degrees, the upper arm back about 14 and bent about 58, the
        # forearm forward and about 50 degrees down, turned in about 10, so
        # the shield's face (the back of the forearm) looks out to her
        # left-front about 15 degrees, its plane near upright. The shield is
        # strapped low on the forearm, its boss over her wrist, so its top rim
        # sits about 145 cm up, level with her armpit and the top of her cup,
        # with air under the shoulder armour, and its bottom is 8 cm or more
        # clear of her hip and thigh. The wrist straight, the fist on the
        # strap; the forearm turned palm-up a little (the whole roll in the
        # forearm, which carries the shield), not wrung at the wrist.
        # (Carried across her body, the 66 cm shield sank 5 cm into her
        # breast and trunk.) The upper arm turned 8 degrees out about its
        # length (judges 46-47): the rim clear of her cup's outline from the
        # front by 2-5 cm. In the game the forearm bone keeps to its hinge
        # (HerJoints hands its roll to the hand), so the shield on it does not
        # take the forearm's roll: measure with the helpers driven.
        "hand_l": {"arc": arc_of((0.0817, -0.3796 + breath, 0.1299)), "pole": (0.3281, -0.4168, -0.8477), "frame": "chest",
                   "thumb": (-0.1498, 0.7455, 0.6495), "twist": 1.0},
        # The sword low at her right, its point 45 degrees down ahead and a
        # little out: the hand in line with the forearm, its thumb forward,
        # dropped 16 degrees toward the little finger under the blade's
        # weight, the turn shared by the forearm and the wrist; no bend
        # back. (Keyed by the blade alone, the
        # wrist cocked back 42 degrees and 34 to the side.)
        "hand_r": {"arc": arc_of(WARDEN_HAND_R), "pole": (-0.4, -0.2, -1.0), "frame": "chest",
                   "blade": _n((-0.131, -0.630, 0.765)), "knuckles": _n((0.135, -0.776, -0.617)), "twist": 0.5},
        # The left thumb closed round the grip, swung in across the palm
        # (judge 47: held straight, it showed between the rim and her skirt).
        "fingers_l": {"curl": 0.95, "cascade": 0.05, "thumb": 1.6, "oppose": 0.9}, "fingers_r": "grip",
    }


def arcanist(t, f):
    return {
        "hand_l": {"arc": arc_of((-0.02, -0.40, -0.05)), "pole": (1.0, 0.0, -0.7), "frame": "chest",
                   "knuckles": _n((0.2, -0.6, 0.6)), "twist": 0.3},
        # The staff upright at her side, its head leaning in a little and its foot out past her right leg
        # (13 Oct: on the seated bound staff, blade (-0.12, 1.0, 0.18) crossed its lower half behind her right
        # thigh and calf every frame; now >= 10 mm off her legs and her hat).
        "hand_r": {"arc": arc_of((-0.16, -0.28, 0.12)), "pole": (-0.8, -0.3, -0.6), "frame": "chest",
                   "blade": _n((0.03, 1.0, 0.06)), "twist": 0.5},
        "fingers_l": "relaxed", "fingers_r": "grip",
    }


def reaver(t, f):
    return {
        # The axe on her shoulder, its head behind her.
        "hand_r": {"arc": arc_of((-0.03, -0.13, 0.11)), "pole": (-0.6, -1.0, 0.0), "frame": "chest",
                   "blade": _n((-0.15, 0.35, -0.95)), "twist": 0.5},
        "hand_l": {"arc": arc_of((-0.02, -0.42, 0.06)), "pole": (0.4, 0.0, -1.0), "frame": "chest"},
        "fingers_r": "grip", "fingers_l": "fist",
    }


def stalker(t, f):
    return {
        # The crossbow low across her, pointing ahead and to her left, the
        # left hand under its stock.
        "hand_r": {"arc": arc_of((0.12, -0.38, 0.20)), "pole": (-0.7, -0.4, -0.5), "frame": "chest",
                   "knuckles": _n((0.5, -0.15, 0.85)), "twist": 0.5},
        "hand_l": {"arc": arc_of((-0.16, -0.42, 0.30)), "pole": (0.7, -0.4, -0.5), "frame": "chest",
                   "knuckles": _n((0.2, -0.2, 0.95)), "twist": 0.4},
        "fingers_r": "grip", "fingers_l": "relaxed",
    }


def warden_town(t, f):
    """In town, her weapons sheathed (the sword at her left hip, the shield
    on her back): the arms hang free and easy at her sides, the elbows soft,
    the wrists straight (the thumb forward, the palm to the thigh), clear of
    her hips and skirt; a small counter-swing to the hips' sway."""
    sw = 0.012 * math.sin(2 * math.pi * t * 2)
    return {
        "hand_l": {"arc": arc_of((0.16, -0.46, 0.08 + sw)), "pole": (0.3, -0.2, -1.0), "frame": "chest",
                   "thumb": _n((-0.15, -0.1, 1.0)), "twist": 1.0},
        "hand_r": {"arc": arc_of((-0.14, -0.46, 0.08 - sw)), "pole": (-0.3, -0.2, -1.0), "frame": "chest",
                   "thumb": _n((0.15, -0.1, 1.0)), "twist": 1.0},
        "fingers_l": "relaxed", "fingers_r": "relaxed",
    }


IDLES = {
    "idle_warden": ("Heavyset", warden, "sword+shield"),
    "idle_arcanist": ("Strutting", arcanist, "staff"),
    "idle_reaver": ("Angry", reaver, "axe"),
    "idle_stalker": ("Crouched", stalker, "crossbow"),
    # In town, weapons sheathed (the game asks for idle_<calling>_town).
    "idle_warden_town": ("WiggleHips", warden_town, ""),
}


_bases = {}


def base_of(rig, calling):
    """A calling's captured standing (made once a run, shared by its idle,
    its breaks and its flourish)."""
    if calling not in _bases:
        style = IDLES[f"idle_{calling}"][0]
        _bases[calling] = idle_loop(f"idle_{calling}_base", rig, style, seconds=(5.0, 8.0))
    return _bases[calling]


def clips(rig, want):
    out = []
    for name, (style, arms, weapon) in IDLES.items():
        if want and not any(w in name for w in want):
            continue
        out.append(layered(name, rig, base_of(rig, name[5:]), arms, {"weapon": weapon}))
    return out
