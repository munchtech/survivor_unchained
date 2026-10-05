"""Her signature idles: a captured way of standing (100STYLE, CC BY 4.0) for
each calling's body, the arms re-solved to hold what that calling holds,
its way. The capture brings the weight shifts and the breath; the arms
ride the chest as it moves.

- Warden: Heavyset (tensed, square, settled). The buckler resting across
  her body, the sword low at her right, point toward the ground ahead.
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


def warden(t, f):
    breath = 0.008 * math.sin(2 * math.pi * t * 2)
    return {
        "hand_l": {"arc": arc_of((-0.10, -0.38 + breath, 0.16)), "pole": (1.0, -0.4, -0.3), "frame": "chest",
                   "blade": _n((-0.3, 0.75, 0.6)), "twist": 0.3},
        "hand_r": {"arc": arc_of((-0.06, -0.44, 0.10)), "pole": (-0.5, -0.1, -1.0), "frame": "chest",
                   "blade": _n((-0.25, -0.5, 0.85)), "twist": 0.5},
        "fingers_l": "fist", "fingers_r": "grip",
    }


def arcanist(t, f):
    return {
        "hand_l": {"arc": arc_of((-0.02, -0.40, -0.05)), "pole": (1.0, 0.0, -0.7), "frame": "chest",
                   "knuckles": _n((0.2, -0.6, 0.6)), "twist": 0.3},
        "hand_r": {"arc": arc_of((-0.16, -0.28, 0.12)), "pole": (-0.8, -0.3, -0.6), "frame": "chest",
                   "blade": _n((-0.12, 1.0, 0.18)), "twist": 0.5},
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


IDLES = {
    "idle_warden": ("Heavyset", warden, "sword+shield"),
    "idle_arcanist": ("Strutting", arcanist, "staff"),
    "idle_reaver": ("Angry", reaver, "axe"),
    "idle_stalker": ("Crouched", stalker, "crossbow"),
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
