"""(aim-move solver 3b, 15 Nov) A swung sword arm's fist set by the wrist, not by the blade's line.

The owner (15 Nov): "while running its held rigid not moving at all". run.low_point keyed the blade's line in her
character's space and left the fist's roll to the solver: to lay the line back and down the wrist had to bend past
armroll's caps (ulnar 39-54, pronation past 80), and the pack turned the hand back into its range, so the blade played
out to her right as a stiff bar (run_warden -99..-63 heading, 0.6-1.1 m up, the tip 1.1-1.4 m out to the side).

Here the arm is where its joints put it (gait._swung: the fist's place and the elbow's way, untouched) and the fist is
set on its forearm by the wrist, in armroll's own reading (armroll.wrist): the forearm's pronation `pro` (+ turned
out), the wrist's flexion `flex` (+ toward the palm, - extension) and deviation `dev` (+ toward the thumb), eased
between the fist-forward and fist-back ends with the stride and read `lag` of a cycle late, so the blade trails the fist
through the swing. Because the grip leans the blade toward the fingers, the forearm turned out and the wrist extended
lay it back and down behind her hip (solver 2's reach.py: the line is reached inside the caps, nothing turned back).

The fist's turn is solved once per key on a still body (keyed.Rig.solve, the hand riding the forearm) and keyed as the
grip's blade and knuckles in the chest's frame: the arm's joints are the chest's (arc and pole), so on the running
body the solve lands the same fist on the same forearm. keyed then hands half the fist's turn about the forearm to the
forearm bone (Rig.solve, "twist"), which moves the reading a little (flexion 5-10 toward extension); the built clip is
read as played (armroll.measure) to check it stays inside the caps.
"""
from __future__ import annotations

import math

import numpy as np

_RIG = {}


def _rig():
    if "r" not in _RIG:
        from keyed import Rig, grip_of
        from rig import Skeleton
        sk = Skeleton.load()
        rig = Rig(sk, body="her")
        rig.grip = grip_of("sword+shield")
        _RIG["r"] = rig
    return _RIG["r"]


def fist_frame(spec, pro, flex, dev, side="r", tilt=0.0):
    """The grip's (blade, knuckles) in the chest's frame for an arm keyed by `spec` (arc / pos and pole, chest frame)
    with the fist at wrist reading (pro, flex, dev) (armroll.wrist's, before keyed's forearm share). `tilt`: the clip's
    "grip_tilt" (degrees; keyed.grip_of: the blade's lean in the fist 35 - tilt about hand +X, - toward her fingers), the
    same the clip's meta carries, so keyed's solve (rig.grip = grip_of(weapon, tilt)) lands the fist at this reading."""
    from keyed import grip_of
    from rig import qaxis, qinv, qmul, qrot
    import armroll
    rig = _rig()
    rig.grip = grip_of("sword+shield", tilt)
    sk, I = rig.sk, rig.I
    s2 = {k: v for k, v in spec.items() if k in ("arc", "pos", "pole", "pole_at", "frame")}
    s2["frame"] = "chest"
    rig.swivel, rig.twist_last, rig.swing_last, rig.bend_last = {}, {}, {}, {}
    r2, q2 = rig.solve({f"hand_{side}": s2})
    g, _p = sk.fk(r2[None], q2[None])
    la, h = I[f"lowerarm_{side}"], I[f"hand_{side}"]
    rl, rh = sk.rest_rot[la], sk.rest_rot[h]
    dl = qmul(qinv(rl), r2[la])
    t = np.array([0.0, dl[1], 0.0, dl[3]])
    t = t / np.linalg.norm(t)
    A = qmul(qinv(rl), qmul(t, rl))
    sgn = 1.0 if side == "r" else -1.0
    tw = np.array([0.0, math.sin(math.radians(pro) / 2), 0.0, math.cos(math.radians(pro) / 2)])
    sw = armroll._qexp(np.array([math.radians(dev), 0.0, sgn * math.radians(flex)]))
    hrot = qmul(qinv(A), qmul(rh, qmul(tw, sw)))
    gh = qmul(g[0, la], hrot)
    G = qmul(gh, qaxis([1.0, 0, 0], -rig.grip.get(side, 0.0)))
    return tuple(qrot(G, np.array([0, 0, 1.0]))), tuple(qrot(G, np.array([0, 1.0, 0])))


def wrist_carry(fwd, back, lag=0.0, side="r", tilt=0.0):
    """A carry (Gait.arms) for an arm keyed by its joints (Gait.swing / swing_r): the fist at wrist reading `fwd`
    (pro, flex, dev) with the fist forward, `back` with it back, eased between by the swing read `lag` of a cycle late
    (the blade trails the fist). `tilt`: the clip's "grip_tilt" (fist_frame; the clip's meta must carry the same)."""
    fw, bk = np.array(fwd, float), np.array(back, float)
    cache = {}

    def f(ph, k, hand):
        hand = dict(hand)
        kl = 0.5 - 0.5 * math.cos(2 * math.pi * (ph - lag - hand["_koff"])) if lag and "_koff" in hand else k
        pro, flex, dev = bk + (fw - bk) * kl
        key = (tuple(np.round(hand.get("arc", (0, 0, 0)), 6)), tuple(np.round(hand.get("pole", (0, 0, 0)), 6)),
               round(pro, 4), round(flex, 4), round(dev, 4))
        if key not in cache:
            cache[key] = fist_frame(hand, pro, flex, dev, side, tilt)
        b, kn = cache[key]
        hand.update({"blade": b, "knuckles": kn, "frame": "chest"})
        hand.pop("pole_frame", None)
        return hand
    return f
