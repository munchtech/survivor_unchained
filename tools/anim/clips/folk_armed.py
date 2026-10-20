"""The armed townsfolk's stands (animation 45): the folk's own weight shift (folk.py "idle", Mixamo) with the arms
re-solved to hold what they carry, at ease, as her town stands do (clips/idle.py free_arms): the owner, 19 Oct, "a lot
of the looks are rigid even when safe". Each hand rides the chest (keyed in its frame from the shoulder) and keeps half
of the capture's own arm swing about its rest, so it moves against the hips' shift as the unarmed folk's arms do.

- idle_watch: a gate Watchman (sword in the right fist, shield on the left forearm). The sword arm hangs easy, the
  elbow soft, the blade down and a little forward and out, its point well clear of the leg and off the ground; the
  shield arm hangs too, the shield at the left side clear of the thigh and hip.
- idle_armed: any one-handed piece in the right fist, the left free (Wenna's short staff): the right arm as the
  Watchman's, the left hanging free. (Planted as a cane the short staff cannot be: the folk's plain mount runs the
  shaft out of the thumb side, so with the head up its foot is only 0.44 m below the wrist.)
- idle_2h: a two-handed blade (Keegan's zweihander) at rest on the right shoulder, the right fist on the grip at the
  chest, the left arm hanging free. (The knight's rest, the point planted ahead with the hands on the grip, cannot be:
  the plain mount runs the blade out of the thumb side, so a blade pointing down from the fist needs the thumb turned
  down, past the forearm's range.)

Built for the women and the men (folk.py), each on its own skeleton; scaled by each body's arm.
"""
from __future__ import annotations

import math

import numpy as np

from gait import arc_of
from rig import Clip, qinv, qrot


def _n(v):
    v = np.array(v, float)
    return tuple(v / np.linalg.norm(v))


# The heroine's arm (shoulder to wrist at rest, m), which free_arms' hands were placed for.
HER_ARM = 0.517
# Of the capture's own arm swing about its mean (chest frame), how much each hand keeps.
SWING = 0.5


def _captured(rig, base: Clip, side):
    """The base's own hand, shoulder-relative in its chest's frame, each frame, less its mean."""
    sk = rig.sk
    g, p = sk.fk(base.rot, base.pos)
    grest = sk.rest_globals()[0][0]
    ch, ua, ha = sk.i("spine_03"), sk.i(f"upperarm_{side}"), sk.i(f"hand_{side}")
    from rig import qmul
    rel = np.array([qrot(qinv(qmul(g[f, ch], qinv(grest[ch]))), p[f, ha] - p[f, ua]) for f in range(base.frames)])
    return rel - rel.mean(axis=0)


def _arm(rig):
    sk = rig.sk
    pr = sk.rest_globals()[1][0]
    return float(np.linalg.norm(pr[sk.i("lowerarm_r")] - pr[sk.i("upperarm_r")]) + np.linalg.norm(pr[sk.i("hand_r")] - pr[sk.i("lowerarm_r")]))


# Each stand: the hands' rests (chest frame, from the shoulder, for her arm: scaled to the body's), poles, and aims.
# The sword hand: out by the thigh, a little forward; the blade (character space) down 52 deg, forward and out.
SWORD_R = dict(at=(-0.12, -0.45, 0.10), pole=(-0.4, -0.2, -1.0), blade=_n((-0.18, -0.78, 0.60)))
# The free hand: free_arms' (her town stands), the thumb forward.
FREE_L = dict(at=(0.16, -0.46, 0.08), pole=(0.3, -0.2, -1.0))
# The shield hand: hanging out from the hip, the forearm a little forward so the shield's face looks out to the
# left-front.
SHIELD_L = dict(at=(0.20, -0.44, 0.10), pole=(0.5, -0.2, -1.0), thumb=_n((-0.1, -0.1, 1.0)))
# The two-handed blade on the right shoulder: the fist before the chest, the blade up and back over the shoulder.
SHOULDER_R = dict(at=(0.05, -0.24, 0.22), pole=(-0.6, -0.5, -0.6), blade=_n((-0.06, 0.62, -0.78)))

STANDS = {
    "idle_watch": dict(r=SWORD_R, l=SHIELD_L, weapon="sword+shield"),
    "idle_armed": dict(r=SWORD_R, l=FREE_L, weapon="staff"),
    "idle_2h": dict(r=SHOULDER_R, l=FREE_L, weapon=""),
}


def make_stand(name, rig, base: Clip, stand=None) -> Clip:
    from clips.idle import layered
    st = stand or STANDS[name.split("_", 1)[1]]
    k = _arm(rig) / HER_ARM
    swing = {s: _captured(rig, base, s) * SWING for s in "lr"}

    def hand(side, spec, f):
        at = np.array(spec["at"], float) * k + swing[side][f]
        h = {"arc": arc_of(at), "pole": spec["pole"], "frame": "chest", "twist": 1.0 if side == "l" else 0.5}
        if "blade" in spec:
            # (The arc rides the chest whatever the frame; the pole and the blade are kept in character space, so the
            # blade's line holds as the chest rolls.)
            h["blade"] = spec["blade"]
            h["frame"] = "char"
        else:
            h["thumb"] = spec.get("thumb", _n((0.15 if side == "r" else -0.15, -0.1, 1.0)))
        return h

    def over(t, f):
        d = {"hand_r": hand("r", st["r"], f), "hand_l": hand("l", st["l"], f), "fingers_r": "grip",
             "fingers_l": "grip" if st["weapon"].endswith("shield") else "relaxed"}
        return d

    clip = layered(name, rig, base, over, {"weapon": st["weapon"]})
    clip.meta["note"] = f"townsfolk, armed, at ease ({name.split('_', 1)[1]})"
    clip.meta["changes"] = clip.meta.get("changes", "") + "; the arms re-solved to hold what they carry, at ease (clips/folk_armed.py)"
    return clip
