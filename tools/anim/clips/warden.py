"""The Ford-Warden's clips for the cinematics (C02, C03), on the kit's man
(folk.py packs them as "m_<name>"; the cinematic plays "folk/m_<name>" on
its boss cast, at the Warden's size). Each is made from the owner's
Kimodo run (C:/Users/munch/Tools/mocap/kimodo, NVIDIA Open Model License),
judged as whole takes first: the take that fits the shot is kept, and
what it cannot do (hold a lamp up to a face, carry a greatsword) is keyed
over it rather than bent out of it.

- rise_stiff (C02 shot 5): on his back under the river, the knees drawn
  up; he sits up slowly, rests a beat on his knees, then gets his feet
  under him and rises straight up, standing by 3.8 s of the shot's 5.
  Take 1: the others twist off their line or jack-knife like a sit-up.
  The lamp never touches the water: his left forearm is held up from
  the elbow as he lies, the lamp kept high and wide as he sits, and at
  his side as he stands (keyed over the take, whose left hand pushes on
  the ground).
- bend_lift (C02 shots 7 to 9): from standing, a long bend down to her
  face, the knees going with it; the lamp in his left fist lifted out to
  her face as he comes down; halfway the lamp-arm shakes, once, badly,
  and he steadies it; the head tilts at the end, looking. Held there.
  The body is take 1's bend; the arms are keyed over it (in the take the
  right hand reaches for the ground).
"""
from __future__ import annotations

import math

import numpy as np

from clips.generated import make
from keyed import Rig, build
from rig import Clip, qinv, qrot

# His fists: the lamp's ring and the sword's grip held with the thumb closed
# over (keyed.py "oppose"), not thumbing a lift.
LAMP_FIST = {"curl": 1.0, "thumb": 0.7, "cascade": 0.05, "oppose": 1.0}
SWORD_GRIP = {"curl": 0.9, "thumb": 0.6, "cascade": 0.08, "oppose": 0.8}


def _grounded(sk, clip: Clip, smooth=4):
    """The body lifted so nothing it lies or sits on goes through the
    ground: each frame raised by however far its lowest part is under it
    (the back and the seat taken as the flesh round the joints), smoothed."""
    g, p = sk.fk(clip.rot, clip.pos)
    I = sk.index
    flesh = {"pelvis": 0.11, "spine_01": 0.11, "spine_02": 0.12, "spine_03": 0.12, "Head": 0.10,
             "calf_l": 0.05, "calf_r": 0.05, "ball_l": 0.015, "ball_r": 0.015, "foot_l": 0.07, "foot_r": 0.07,
             "hand_l": 0.03, "hand_r": 0.03, "lowerarm_l": 0.04, "lowerarm_r": 0.04}
    under = np.max([r - p[:, I[n], 1] for n, r in flesh.items()], axis=0)
    lift = np.maximum(under, 0.0)
    k = np.exp(-0.5 * (np.arange(-3 * smooth, 3 * smooth + 1) / smooth) ** 2)
    k /= k.sum()
    lift = np.maximum(lift, np.convolve(np.pad(lift, 3 * smooth, mode="edge"), k, mode="valid"))
    pel, root = I["pelvis"], I["root"]
    w = qrot(sk.rest_rot[root], clip.pos[:, pel])
    w[:, 1] += lift
    clip.pos[:, pel] = qrot(qinv(sk.rest_rot[root]), w)
    return clip


def _ease(keys, fr):
    """Smoothstep between (frame, value) keys."""
    if fr <= keys[0][0]:
        return np.array(keys[0][1], float)
    for (f0, a), (f1, b) in zip(keys, keys[1:]):
        if fr <= f1:
            u = (fr - f0) / (f1 - f0)
            u = u * u * (3 - 2 * u)
            return np.array(a, float) + (np.array(b, float) - np.array(a, float)) * u
    return np.array(keys[-1][1], float)


def _settled(sk, clip: Clip):
    """The take carried so it ends standing where it is placed: every frame's
    hips moved by the last frame's distance from the origin (along the
    ground), so the cinematic's mark is where he stands at the end."""
    pel, root = sk.index["pelvis"], sk.index["root"]
    w = qrot(sk.rest_rot[root], clip.pos[:, pel])
    end = w[-1].copy()
    w[:, 0] -= end[0]
    w[:, 2] -= end[2] - float(sk.rest_globals()[1][0, pel][2])
    clip.pos[:, pel] = qrot(qinv(sk.rest_rot[root]), w)
    return clip


def _bare_hands(sk, clip: Clip):
    """The take's fingers put back to rest, so the keyed grip and fist close
    from there (a take's hands are loose, the thumbs out)."""
    for j, n in enumerate(sk.names):
        if any(n.startswith(f) for f in ("thumb_", "index_", "middle_", "ring_", "pinky_")):
            clip.rot[:, j] = sk.rest_rot[j]
    return clip


def _pole(p, I, side, fr):
    """The way the elbow points in a take's frame (from the arm's middle out to it)."""
    s, e, h = p[fr, I[f"upperarm_{side}"]], p[fr, I[f"lowerarm_{side}"]], p[fr, I[f"hand_{side}"]]
    v = e - (s + h) / 2
    n = np.linalg.norm(v)
    return tuple(v / n) if n > 1e-4 else (0.0, -1.0, 0.0)


def rise_stiff(name, rig: Rig):
    # From 0.9 s, as the knees come up (the take lies still before then):
    # the sit-up in 1.9 s, the rest on his knees 0.8 s, up in 1.5 s.
    base = make(rig, name, "kimodo", "rise_stiff_1.bvh", warp_=[(0.9, 3.5, 1.9), (3.5, 4.5, 0.8), (4.5, 6.6, 1.5)],
                place="keep", note="the Warden (C02): up from his back under the river, slow and stiff, the lamp kept up")
    if base is None:
        return None
    sk = rig.sk
    base = _bare_hands(sk, _settled(sk, _grounded(sk, base)))
    I = sk.index
    g, p = sk.fk(base.rot, base.pos)
    n = base.frames
    # The lamp hand from the left shoulder, in his space: the forearm stood
    # up off the elbow as he lies; out wide and high as he sits; kept up as
    # he rises; at his side, a little forward, once he stands.
    lamp = [(0, (0.10, 0.27, 0.16)), (12, (0.12, 0.28, 0.16)), (57, (0.30, 0.10, 0.22)), (81, (0.30, 0.08, 0.24)),
            (104, (0.26, -0.10, 0.32)), (n - 1, (0.12, -0.26, 0.30))]
    pole = [(0, (0.4, -1.0, 0.0)), (57, (0.8, -0.6, -0.2)), (104, (0.8, -0.4, -0.4)), (n - 1, (0.6, -0.5, -0.6))]
    # The greatsword: laid along him, flat, as he lies and sits (the blade
    # toward his feet); point down at his side once he is up.
    blade = [(0, (0.0, 0.0, 1.0)), (81, (0.15, 0.0, 1.0)), (104, (0.0, -0.6, 0.8)), (n - 1, (0.0, -0.95, 0.3))]
    knuckles = [(0, (-1.0, 0.0, 0.0)), (81, (-1.0, 0.0, 0.0)), (104, (-0.3, -0.5, -0.8)), (n - 1, (0.0, -0.3, -0.95))]
    keys = []
    for fr in range(n):
        hand_l = {"pos": tuple(p[fr, I["upperarm_l"]] + _ease(lamp, fr)), "pole": tuple(_ease(pole, fr)), "frame": "char",
                  "knuckles": (0.0, 1.0, 0.15)}
        hand_r = {"pole": _pole(p, I, "r", fr), "blade": tuple(_ease(blade, fr)), "knuckles": tuple(_ease(knuckles, fr)), "frame": "char"}
        keys.append((fr, {"hand_l": hand_l, "hand_r": hand_r, "fingers_l": LAMP_FIST, "fingers_r": SWORD_GRIP}, "linear"))
    return build(name, rig, keys, base=base, meta=dict(base.meta, hold=True))


def bend_lift(name, rig: Rig):
    # Take 1's bend, from its start until his head is down about where hers
    # can be seen from it, slowing into the end; then carried on so slowly
    # that it only settles, for the shots held on the look.
    base = make(rig, name, "kimodo", "bend_lift_1.bvh",
                warp_=[(0.9, 1.7, 1.4), (1.7, 1.95, 0.8), (1.95, 2.05, 0.7), (2.05, 2.15, 6.0)], place="keep",
                note="the Warden (C02): bent down to her, the lamp lifted to her face")
    if base is None:
        return None
    sk = rig.sk
    base = _bare_hands(sk, base)
    I = sk.index
    g, p = sk.fk(base.rot, base.pos)
    n = base.frames
    # The lamp's path in his space (the kit man's metres), from his side,
    # out and up as he starts down, then on to her face, before him and a
    # touch to his left. Her eyes stand about 0.9 before him and 0.86 up in
    # C02 (his size 2.5, in the river 0.45 below her); the flame hangs 0.25
    # of his metres under the fist, so the fist is held that much higher.
    lamp = [(0, (0.27, 0.92, 0.06)), (30, (0.25, 1.06, 0.30)), (55, (0.15, 1.04, 0.56)), (80, (0.10, 1.00, 0.70)),
            (100, (0.09, 0.99, 0.72)), (160, (0.08, 0.98, 0.73)), (n - 1, (0.09, 0.98, 0.72))]

    def tremble(fr):
        """Halfway up the arm shakes, once, badly (a fast, dying shudder), at
        2.0 s with the shot's rattle, and is steadied."""
        t = (fr - 54) / 30.0
        if t < 0 or t > 0.55:
            return np.zeros(3)
        amp = 0.04 * math.sin(math.pi * t / 0.55) ** 0.5
        return np.array([0.6 * math.sin(2 * math.pi * 9 * t), math.sin(2 * math.pi * 7 * t + 1.0), 0.3 * math.sin(2 * math.pi * 11 * t)]) * amp

    keys = []
    for fr in range(n):
        s_r = p[fr, I["upperarm_r"]]
        # The greatsword hangs in the right fist at his side, the point down
        # and a little forward, whatever the back does.
        hand_r = {"pos": tuple(s_r + np.array([-0.05, -0.50, 0.06])), "pole": (-0.4, 0.0, -1.0), "frame": "char",
                  "blade": (0.0, -0.95, 0.3), "knuckles": (0.0, -0.3, -0.95)}
        # The held lamp sways a little with his breath while he looks.
        sway = np.array([0.006 * math.sin(fr / 30 * 1.3), 0.008 * math.sin(fr / 30 * 1.7 + 0.5), 0.0]) * min(1.0, max(0.0, (fr - 90) / 30))
        hand_l = {"pos": tuple(_ease(lamp, fr) + tremble(fr) + sway), "pole": (0.8, -0.6, -0.2), "frame": "char",
                  "knuckles": (-0.1, 1.0, 0.2)}
        # Looking down at her face, the head tilting as he looks, once he is down.
        look = min(1.0, max(0.0, (fr - 40) / 40.0))
        tilt = min(1.0, max(0.0, (fr - 84) / 24.0))
        look, tilt = look * look * (3 - 2 * look), tilt * tilt * (3 - 2 * tilt)
        keys.append((fr, {"hand_l": hand_l, "hand_r": hand_r, "fingers_l": LAMP_FIST, "fingers_r": SWORD_GRIP,
                          "head": (0, 10 * look + 3 * tilt, 13 * tilt)}, "linear"))
    return build(name, rig, keys, base=base, meta=dict(base.meta, hold=True))


# name: function(name, rig) -> Clip or None (the take not on this machine).
CLIPS = {"rise_stiff": rise_stiff, "bend_lift": bend_lift}
