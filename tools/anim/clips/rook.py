"""Mother Rook's cinematic clips (C04 B), on the kit's woman (folk.py packs
them as "f_<name>"; the cinematic plays "folk/f_<name>" on its own Rook).

- unfold_arms (B4b): at her door with her arms folded (her standing,
  folk/f_arms_crossed: the same take, so the cut in is seamless); she looks
  back at the survivor and unfolds her arms the way you put down a tool when
  work arrives: a breath in, the arms drop, the hands come together low
  before her, the weight settles. Held.
"""
from __future__ import annotations

import math

import numpy as np

from clips.generated import make
from held import slerp_dir, solved
from keyed import Rig, smoothstep_
from rig import qrot


def _crossed(rig: Rig, frames):
    """Her arms-crossed standing (folk.py's "arms_crossed": Kimodo arms_crossed_0),
    run on to `frames` (it loops)."""
    base = make(rig, "f_arms_crossed", "kimodo", "arms_crossed_0.bvh", loop=True, place="pin",
                note="townsfolk (women)")
    if base is None:
        return None
    idx = np.arange(frames) % (base.frames - 1)
    base.rot, base.pos = base.rot[idx], base.pos[idx]
    return base


def unfold_arms(name, rig: Rig):
    n = 90
    base = _crossed(rig, n)
    if base is None:
        return None
    sk = rig.sk
    g, p = sk.fk(base.rot, base.pos)
    I = sk.index
    # The hands' places low before her, lightly together (her space, the kit
    # woman's metres: her pelvis stands at 0.93).
    # (From each shoulder, so they sit at her waist however low the stance.)
    rest_l, rest_r = np.array([-0.10, -0.35, 0.29]), np.array([0.095, -0.36, 0.285])
    poses = []
    for fr in range(n):
        # A breath in (0.5 s), then down (0.8 to 1.3 s), settling.
        w = smoothstep_((fr - 22) / 16.0)
        breath = math.sin(math.pi * min(1.0, max(0.0, (fr - 8) / 26.0)))
        settle = smoothstep_((fr - 36) / 20.0)
        pose = {"spine": (0, -2.0 * breath + 1.5 * settle, 0), "clav_l": (3 * breath - 2 * settle, 0), "clav_r": (3 * breath - 2 * settle, 0),
                "head": (0, 2 * settle, 0)}
        fing = {"curl": 0.28 + 0.07 * w, "thumb": 0.15 + 0.1 * w, "cascade": 0.25 - 0.05 * w, "spread": 0.0}
        pose["fingers_l"] = pose["fingers_r"] = fing
        if w > 0:
            for s, rest, pole in (("l", rest_l, (0.6, -0.4, -0.7)), ("r", rest_r, (-0.6, -0.4, -0.7))):
                at = p[fr, I[f"hand_{s}"]]
                # The arm swings out of the fold and down, not straight through her.
                arc = np.array([0.08 if s == "l" else -0.08, 0.0, 0.10]) * math.sin(math.pi * w)
                pos = at * (1 - w) + (p[fr, I[f"upperarm_{s}"]] + rest) * w + arc
                # The hand turns from how it lay in the fold (its fingers' way, +Y).
                lay = qrot(g[fr, I[f"hand_{s}"]], np.array([0.0, 1.0, 0.0]))
                knuck = slerp_dir(lay, (-0.75 if s == "l" else 0.75, -0.45, 0.35), w)
                pose[f"hand_{s}"] = {"pos": tuple(pos), "pole": pole, "frame": "char", "knuckles": tuple(knuck)}
        poses.append(pose)
    meta = dict(base.meta, layer="full", hold=True,
                note="Mother Rook (C04 B4b): her folded arms unfolded, the hands together low before her")
    meta["source"] = "keyed over " + base.meta["source"]
    return solved(name, rig, poses, base=base, meta=meta)


CLIPS = {"unfold_arms": unfold_arms}
