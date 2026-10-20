"""The armed townsfolk's stands (animation 45): the folk's own weight shift (folk.py "idle", Mixamo) with the arms
re-solved to hold what they carry, at ease, as her town stands do (clips/idle.py free_arms): the owner, 19 Oct, "a lot
of the looks are rigid even when safe". Each hand rides the chest (keyed in its frame from the shoulder) and keeps half
of the capture's own arm swing about its rest, so it moves against the hips' shift as the unarmed folk's arms do.

- idle_armed: a one-handed piece in the right fist, the left arm free: the gate Watch's sword (they leave their
  shields in the barracks in town) and Wenna's short staff. The sword arm hangs easy, the elbow soft, the piece down and
  a little forward and out, its point well clear of the leg and off the ground; the left arm hangs free and easy as her
  town stands' (clips/idle.py free_arms). (Planted as a cane the short staff cannot be: the folk's plain mount runs the
  shaft out of the thumb side, so with the head up its foot is only 0.44 m below the wrist.)
- idle_2h: a two-handed blade (Keegan's zweihander) at rest on the right shoulder, the right fist on the grip before
  the chest, the left arm hanging free. (The knight's rest, the point planted ahead with the hands on the grip, cannot be:
  the plain mount runs the blade out of the thumb side, so a blade pointing down from the fist needs the thumb turned
  down, past the forearm's range.)

Built for the women and the men (folk.py), each on its own skeleton; scaled by each body's arm.
"""
from __future__ import annotations

import math

import numpy as np

from gait import arc_of
from rig import Clip, qinv, qmul, qrot, qslerp


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


def _chest(rig, base: Clip):
    """The base's chest turn (spine_03, from its rest), each frame, and the loop's mean."""
    sk = rig.sk
    g, _ = sk.fk(base.rot, base.pos)
    grest = sk.rest_globals()[0][0]
    ch = sk.i("spine_03")
    q = np.array([qmul(g[f, ch], qinv(grest[ch])) for f in range(base.frames)])
    q *= np.sign(q @ q[0])[:, None]
    m = q.mean(axis=0)
    return q, m / np.linalg.norm(m)


def _arm(rig):
    sk = rig.sk
    pr = sk.rest_globals()[1][0]
    return float(np.linalg.norm(pr[sk.i("lowerarm_r")] - pr[sk.i("upperarm_r")]) + np.linalg.norm(pr[sk.i("hand_r")] - pr[sk.i("lowerarm_r")]))


# Each stand: the hands' rests (chest frame, from the shoulder, for her arm: scaled to the body's), poles, and aims.
# The sword hand: out by the thigh, a little forward; the piece (character space) down, forward and out (out enough
# that Wenna's staff, whose mount turns it in toward the leg, clears her thigh too).
SWORD_R = dict(at=(-0.14, -0.45, 0.10), pole=(-0.4, -0.2, -1.0), blade=_n((-0.30, -0.74, 0.60)))
# The free hand: free_arms' (her town stands), the thumb forward.
FREE_L = dict(at=(0.16, -0.46, 0.08), pole=(0.3, -0.2, -1.0))
# The two-handed blade on the right shoulder: the fist before the chest, a little out, the elbow down at the side; the
# blade up, back and out over the shoulder, resting a few mm above it, well clear of the head. It rides the chest
# (the blade stays on the shoulder through the weight shift) and keeps none of the capture's arm swing. (The knuckles
# turn the guard so its quillons clear the upper arm.) Found by search on folkhold.py's quick model of
# Keegan (a woman) as the town builds her (animation 45); the men's is the same stand, unmeasured (no man carries one).
SHOULDER_R = dict(at=(-0.016, -0.204, 0.199), pole=_n((-0.828, -0.469, -0.307)), blade=_n((-0.188, 0.845, -0.5)),
                  knuckles=_n((0.15, -0.3, 0.94)), ride="chest", swing=0.0)

# The free hand's fingers at ease on the folk's hands (judge, animation 45: the rig's "relaxed" reads straight and
# spread on a townsperson at the game camera): each finger curled more, toward the little one (index 20 at the knuckle,
# little 44), the thumb as "relaxed" has it (drawn in further, or opposed more, its tip only moved off the forefinger
# on the folk hand: 5.5 cm as relaxed, 6.0-9.4 tried; its draw-in is still to find).
FOLK_RELAXED = {"bends": {"index": [20, 22, 12], "middle": [27, 30, 15], "ring": [35, 37, 18], "pinky": [44, 42, 20],
                          "thumb": [12, 12, 16]},
                "oppose": 0.16, "thumb_in": 18, "thumb_roll": -8,
                "spreads": {"index": -7.0, "middle": 0.0, "ring": 8.0, "pinky": 22.0}}

STANDS = {
    # (A woman's free arm and hand are the capture's own, unlayered: on Wenna's narrow corset waist the free_arms rest
    # held the arm out in an A-frame and the fingers read straight (judge folk 2); the unarmed folk's, which pass.)
    "idle_armed": dict(r=SWORD_R, l=FREE_L, weapon="sword", f=dict(l=None)),
    "idle_2h": dict(r=SHOULDER_R, l=FREE_L, weapon=""),
}


def make_stand(name, rig, base: Clip, stand=None) -> Clip:
    from clips.idle import layered
    st = stand or STANDS[name.split("_", 1)[1]]
    sex = name.split("_", 1)[0]
    if sex in st:
        # The stand's own for this body (its "f" or "m": hands, fingers), over the shared.
        st = {k: (dict(v, **st[sex][k]) if isinstance(v, dict) and isinstance(st[sex].get(k), dict) else st[sex].get(k, v))
              for k, v in st.items()}
        st.update({k: v for k, v in st[sex].items() if k not in st})
    k = _arm(rig) / HER_ARM
    swing = {s: _captured(rig, base, s) * SWING for s in "lr"}
    chest, chest_mean = _chest(rig, base)

    def hand(side, spec, f):
        at = np.array(spec["at"], float) * k + swing[side][f] * spec.get("swing", 1.0)
        h = {"arc": arc_of(at), "pole": spec["pole"], "frame": "chest", "twist": 1.0 if side == "l" else 0.5}
        if "steady" in spec:
            # A blade resting on the shoulder ("ride": "chest") whose line holds steadier than the chest turns: the
            # fist, blade and pole turned as one about the resting point ("pivot", chest frame from the shoulder) by
            # `steady` of the way from this frame's chest turn back to the loop's mean, so the blade stays on the
            # shoulder and the fist takes up the difference (the long blade would swing a chest's every roll).
            d = qmul(qinv(chest[f]), qslerp(chest[f], chest_mean, spec["steady"]))
            pv = np.array(spec["pivot"], float) * k
            at = pv + qrot(d, at - pv)
            h["arc"] = arc_of(at)
            h["pole"] = tuple(qrot(d, spec["pole"]))
            spec = dict(spec, blade=tuple(qrot(d, spec["blade"])), knuckles=tuple(qrot(d, spec["knuckles"])))
        if "blade" in spec:
            # (The arc rides the chest whatever the frame; the pole and the blade are kept in character space, so a
            # hanging blade's line holds as the chest rolls; a blade resting on the shoulder rides the chest with it,
            # "ride": "chest".)
            h["blade"] = spec["blade"]
            if "knuckles" in spec:
                h["knuckles"] = spec["knuckles"]
            h["frame"] = spec.get("ride", "char")
        else:
            h["thumb"] = spec.get("thumb", _n((0.15 if side == "r" else -0.15, -0.1, 1.0)))
        return h

    def over(t, f):
        d = {"hand_r": hand("r", st["r"], f), "fingers_r": "grip"}
        if st["l"] is None:
            # (None: the capture's own free arm and fingers.)
            d["fingers_l"] = "base"
        else:
            d["hand_l"] = hand("l", st["l"], f)
            d["fingers_l"] = "grip" if st["weapon"].endswith("shield") else st.get("fingers_l", "relaxed")
        return d

    clip = layered(name, rig, base, over, {"weapon": st["weapon"]})
    clip.meta["note"] = f"townsfolk, armed, at ease ({name.split('_', 1)[1]})"
    clip.meta["changes"] = clip.meta.get("changes", "") + "; the arms re-solved to hold what they carry, at ease (clips/folk_armed.py)"
    return clip
