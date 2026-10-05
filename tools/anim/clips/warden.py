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
- kneel_lamp, lamp_down, fold_forward (C03 shots 2 to 5): keyed, below
  (Kimodo's kneel_fall takes were rejected).
"""
from __future__ import annotations

import math

import numpy as np

from clips.generated import make
from crowd import _in_char, _kit, _on_face
from keyed import Rig, build, merge
from rig import Clip, qinv, qrot

# His fists: the lamp's ring and the sword's grip held with the thumb closed
# over (keyed.py "oppose"), not thumbing a lift.
LAMP_FIST = {"curl": 1.0, "thumb": 0.7, "cascade": 0.05, "oppose": 1.0}
SWORD_GRIP = {"curl": 0.9, "thumb": 0.6, "cascade": 0.08, "oppose": 0.8}
OPEN = {"curl": 0.06, "thumb": 0.05, "cascade": 0.0, "oppose": 0.0}
RELAX = {"curl": 0.3, "thumb": 0.15, "cascade": 0.25, "oppose": 0.1}


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


def lie_arm_up(name, rig: Rig):
    """C02 shots 3 and 4 (and under 2): on his back on the river bed, dead
    still, the left forearm stood up off the elbow so the lamp's fist is
    out of the water; only the current moves it, a slow sway of the forearm
    about the elbow. Exactly rise_stiff's first frame, so the rise follows
    on without a seam. 14 s, held."""
    rise = rise_stiff(name, rig)
    if rise is None:
        return None
    sk = rig.sk
    n = 420
    rot = np.repeat(rise.rot[:1], n, axis=0)
    pos = np.repeat(rise.pos[:1], n, axis=0)
    base = Clip(name, 30, rot, pos, loop=False, meta=dict(rise.meta))
    g, p = sk.fk(base.rot, base.pos)
    I = sk.index
    keys = []
    for fr in range(n):
        t = fr / 30.0
        # The current: a slow lean of the forearm downstream and back, never
        # the same twice (two slow periods), easing in from the cut.
        k = min(1.0, t / 2.0)
        sway = k * np.array([0.020 * math.sin(2 * math.pi * t / 5.3) + 0.008 * math.sin(2 * math.pi * t / 2.1 + 1.0),
                             0.0, 0.012 * math.sin(2 * math.pi * t / 3.7 + 0.4)])
        hand_l = {"pos": tuple(p[0, I["hand_l"]] + sway), "pole": (0.4, -1.0, 0.0), "frame": "char", "knuckles": (0.0, 1.0, 0.15)}
        keys.append((fr, {"hand_l": hand_l, "fingers_l": LAMP_FIST, "fingers_r": SWORD_GRIP}, "linear"))
    return build(name, rig, keys, base=base, meta=dict(base.meta, hold=True, source="keyed over rise_stiff's first frame",
                                                          note="the Warden (C02): lying under the river, the lamp held up out of it"))


def wade_drag(name, rig: Rig):
    """C02 shot 6: out of the river toward her, a stride on a loop (the
    cinematic carries him; at his size 2.5 his own speed is 2.5 times the
    clip's). A heavy man's walk (100STYLE Heavyset, CC BY 4.0) leaning into
    the water, each foot lifted clear of it; the lamp held up before him at
    his left, lighting the way, steady; the greatsword trailing from his
    right fist, its point back and down in the water behind him (Kimodo's
    wade_drag takes hunch and paddle with both arms: rejected)."""
    from clips.walks import _over, walk_loop
    base = walk_loop(name, rig, "Heavyset")
    sk = rig.sk
    I = sk.index
    n = base.frames
    lean = {"hips": {"rot": (0, 7, 0)}, "spine": (0, 6, 0), "neck": (0, -4, 0), "head": (0, -3, 0)}
    # The body first (leaning, wading), to hang the arms from where its shoulders go.
    body = _over(name, rig, base, lambda fr: dict(lean), lift=0.09)
    g, p = sk.fk(body.rot, body.pos)

    def carriage(fr):
        ph = 2 * math.pi * fr / (n - 1)
        # The lamp-arm held out from the shoulder, the fist riding the walk a
        # little (the body's bob), never swinging with it.
        sl, sr = p[fr, I["upperarm_l"]], p[fr, I["upperarm_r"]]
        lamp = sl + np.array([0.06, -0.12, 0.30]) + np.array([0.0, 0.006 * math.sin(2 * ph), 0.0])
        # The sword arm hangs back with the drag, a small sway with the stride.
        drag = sr + np.array([-0.08, -0.44, -0.14 + 0.02 * math.sin(ph)])
        return {**lean,
                "hand_l": {"pos": tuple(lamp), "pole": (0.8, -0.6, -0.2), "frame": "char", "knuckles": (0.0, 1.0, 0.15)},
                "hand_r": {"pos": tuple(drag), "pole": (-0.5, 0.0, 1.0), "frame": "char",
                           "blade": (0.0, -0.55, -0.83), "knuckles": (-0.1, -0.83, 0.55)},
                "fingers_l": LAMP_FIST, "fingers_r": SWORD_GRIP}

    clip = _over(name, rig, base, carriage, lift=0.09,
                 meta={"note": "the Warden (C02): wading out of the river toward her, the lamp up, the greatsword dragging"})
    return clip


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


# --------------------------------------------------------------------- C03 --
# The Warden's end, keyed: Kimodo's kneel_fall takes drop him to his knees in
# a second and dive him onto his face with the arms flung out ahead, all in
# three seconds. C03 wants a slow, heavy kneel with the lamp held up and
# steady, a long look at it while the arm begins to shake, the fist lowered
# until the lamp goes into the river, and then a fold forward into the water,
# still. So three clips, each starting where the last ends, so the cinematic
# can cut them to its shots:
# - kneel_lamp (shots 2, 3, 3b): down on the right knee, then the left, the
#   back giving a little under the weight; the greatsword let go at 1.4 s;
#   the lamp brought up before his face and held there, the eyes on it;
#   breathing; from 6 s the arm begins to shake, and by 10 s it shakes
#   badly. Held shaking.
# - lamp_down (shot 4): the fist sinks; the lamp meets the water at 1.1 s
#   and goes under; the arm comes to rest on his thigh, the head bowed.
# - fold_forward (shot 5): over onto his face in the water without a hand put
#   out, the legs sliding out behind; face down and still by 2.4 s.
# Water in C03 stands about 0.34 of his metres (0.85 m) over the bed he kneels
# on, so the lamp's flame, 0.25 under his fist, meets it with the fist at 0.6.

WATER = 0.34


def _knelt(P, H, breath=0.0, sag=0.0):
    """Upright on both knees, the shins back along the bed, the toes behind."""
    return {"hips": {"pos": H(0, 0.50 - 0.02 * sag, -0.02), "rot": (0, 4 + 4 * sag, 0)},
            "spine": (0, 2 + 1.5 * breath + 8 * sag, 0), "clav_l": (2 * breath, 4), "clav_r": (2 * breath - 3 * sag, 6),
            "foot_l": {"pos": P(0.14, 0.02, -0.36), "rot": (8, -70, 0), "pole": (0.2, -1, 0.5)},
            "foot_r": {"pos": P(-0.15, 0.02, -0.38), "rot": (-8, -70, 0), "pole": (-0.2, -1, 0.5)}}


def _hand(P, at, pole, knuckles=None):
    h = {"frame": "char", "pos": P(*at), "pole": pole}
    if knuckles is not None:
        h["knuckles"] = knuckles
    return h


def kneel_lamp(name, rig: Rig):
    P, H = _kit(rig)
    lamp_up = (0.12, 1.12, 0.34)
    look = dict(neck=(4, 6, 0), head=(10, 10, 4))
    sword = _hand(P, (-0.30, 0.86, 0.06), (-0.4, 0.0, -1.0))
    sword["blade"], sword["knuckles"] = (0.0, -0.95, 0.3), (0.0, -0.3, -0.95)
    hang_r = _hand(P, (-0.26, 0.38, 0.02), (-0.5, 0.0, -1.0))
    keys = [
        # Reeling from the blow, the lamp still before him.
        (0, {"hips": {"pos": H(0, 0.92, 0.0), "rot": (0, 8, 0)}, "spine": (0, 10, 0), "neck": (0, 8, 0), "head": (0, 10, 0),
             "foot_l": {"pos": P(0.14, 0, 0.12), "rot": (10, 0, 0)}, "foot_r": {"pos": P(-0.15, 0, -0.08), "rot": (-12, 0, 0)},
             "hand_l": _hand(P, (0.24, 1.10, 0.22), (0.8, -0.5, -0.4), (0.0, 1.0, 0.15)), "hand_r": sword,
             "fingers_l": LAMP_FIST, "fingers_r": SWORD_GRIP}, "ease"),
        # The knees go; the lamp is held up out of instinct.
        (14, {"hips": {"pos": H(0, 0.74, 0.02), "rot": (0, 10, 0)}, "spine": (0, 8, 0), "neck": (0, 6, 0), "head": (0, 6, 0),
              "foot_l": {"pos": P(0.14, 0, 0.12), "rot": (10, 0, 0), "pole": (0.2, 0, 1)},
              "foot_r": {"pos": P(-0.15, 0.02, -0.10), "rot": (-12, -10, 0), "pole": (-0.2, 0, 1)},
              "hand_l": _hand(P, (0.22, 1.12, 0.28), (0.8, -0.5, -0.4), (0.0, 1.0, 0.15)), "hand_r": sword,
              "fingers_l": LAMP_FIST, "fingers_r": SWORD_GRIP}, "auto"),
        # The right knee down on the bed, the left foot still before him.
        (28, {"hips": {"pos": H(0, 0.58, 0.0), "rot": (-6, 8, 4)}, "spine": (4, 10, 0), "neck": (0, 8, 0), "head": (2, 8, 0),
              "foot_l": {"pos": P(0.14, 0, 0.16), "rot": (10, 0, 0), "pole": (0.2, 0.3, 1)},
              "foot_r": {"pos": P(-0.15, 0.02, -0.38), "rot": (-8, -70, 0), "pole": (-0.2, -1, 0.5)},
              "hand_l": _hand(P, (0.18, 1.06, 0.30), (0.8, -0.5, -0.4), (0.0, 1.0, 0.15)), "hand_r": sword,
              "fingers_l": LAMP_FIST, "fingers_r": SWORD_GRIP}, "auto"),
        # The greatsword let go (C03: at 1.4 s it leaves his hand and sinks).
        (40, {"hips": {"pos": H(0, 0.57, 0.0), "rot": (-6, 9, 4)}, "spine": (4, 11, 0), "neck": (0, 8, 0), "head": (2, 8, 0),
              "foot_l": {"pos": P(0.14, 0, 0.16), "rot": (10, 0, 0), "pole": (0.2, 0.3, 1)},
              "foot_r": {"pos": P(-0.15, 0.02, -0.38), "rot": (-8, -70, 0), "pole": (-0.2, -1, 0.5)},
              "hand_l": _hand(P, (0.17, 1.06, 0.31), (0.8, -0.5, -0.4), (0.0, 1.0, 0.15)),
              "hand_r": _hand(P, (-0.30, 0.66, 0.10), (-0.5, 0.0, -1.0)), "fingers_l": LAMP_FIST, "fingers_r": SWORD_GRIP}, "auto"),
        (44, {"hips": {"pos": H(0, 0.56, 0.0), "rot": (-5, 9, 4)}, "spine": (4, 11, 0), "neck": (0, 8, 0), "head": (2, 8, 0),
              "foot_l": {"pos": P(0.14, 0, 0.16), "rot": (10, 0, 0), "pole": (0.2, 0.3, 1)},
              "foot_r": {"pos": P(-0.15, 0.02, -0.38), "rot": (-8, -70, 0), "pole": (-0.2, -1, 0.5)},
              "hand_l": _hand(P, (0.16, 1.07, 0.31), (0.8, -0.5, -0.4), (0.0, 1.0, 0.15)),
              "hand_r": _hand(P, (-0.29, 0.60, 0.08), (-0.5, 0.0, -1.0)), "fingers_l": LAMP_FIST, "fingers_r": OPEN}, "auto"),
        # The left knee down too: on both knees in the river.
        (56, {**_knelt(P, H, sag=1.0), "neck": (0, 10, 0), "head": (4, 8, 0),
              "hand_l": _hand(P, (0.15, 1.05, 0.32), (0.8, -0.5, -0.4), (0.0, 1.0, 0.15)), "hand_r": hang_r,
              "fingers_l": LAMP_FIST, "fingers_r": RELAX}, "auto"),
        # Up straight, and the lamp brought up before his face; he looks at it.
        (74, {**_knelt(P, H, breath=0.5, sag=0.3), **look, "hand_l": _hand(P, lamp_up, (0.8, -0.5, -0.4), (0.0, 1.0, 0.15)),
              "hand_r": hang_r, "fingers_l": LAMP_FIST, "fingers_r": RELAX}, "ease"),
    ]
    # Breathing while he looks; the arm sagging a little once it shakes.
    for i, fr in enumerate(range(104, 316, 30)):
        breath = 1.0 if i % 2 == 0 else 0.0
        sag = min(1.0, max(0.0, (fr - 180) / 135))
        at = (lamp_up[0], lamp_up[1] - 0.04 * sag, lamp_up[2] - 0.02 * sag)
        keys.append((fr, {**_knelt(P, H, breath=breath, sag=0.35), **look, "hand_l": _hand(P, at, (0.8, -0.5, -0.4), (0.0, 1.0, 0.15)),
                          "hand_r": hang_r, "fingers_l": LAMP_FIST, "fingers_r": RELAX}, "ease"))

    def shake(fr, pose):
        """From 6 s the lamp-arm shakes, the tremor growing for four seconds."""
        grow = min(1.0, max(0.0, (fr - 180) / 120)) ** 1.5
        if grow <= 0:
            return pose
        t = fr / 30
        d = 0.012 * grow * np.array([math.sin(2 * math.pi * 6.3 * t) + 0.4 * math.sin(2 * math.pi * 9.1 * t + 1),
                                     0.8 * math.sin(2 * math.pi * 7.7 * t + 0.6), 0.5 * math.sin(2 * math.pi * 5.2 * t + 2)])
        h = dict(pose["hand_l"])
        h["pos"] = tuple(np.array(h["pos"]) + d)
        return {**pose, "hand_l": h}

    return build(name, rig, keys, post=shake, meta={"layer": "full", "hold": True, "source": "keyed (tools/anim/clips/warden.py)",
                                                     "note": "the Warden (C03): down on his knees, the lamp held up and looked at; the arm begins to shake"})


def lamp_down(name, rig: Rig):
    P, H = _kit(rig)
    hang_r = _hand(P, (-0.26, 0.38, 0.02), (-0.5, 0.0, -1.0))
    up = (0.12, 1.08, 0.32)
    keys = [
        (0, {**_knelt(P, H, sag=0.35), "neck": (4, 6, 0), "head": (10, 10, 4), "hand_l": _hand(P, up, (0.8, -0.5, -0.4), (0.0, 1.0, 0.15)),
             "hand_r": hang_r, "fingers_l": LAMP_FIST, "fingers_r": RELAX}, "ease"),
        # The shoulders give; the fist starts down.
        (15, {**_knelt(P, H, sag=0.4), "neck": (4, 10, 0), "head": (8, 14, 4),
              "hand_l": _hand(P, (0.14, 0.92, 0.33), (0.8, -0.5, -0.4), (0.0, 1.0, 0.15)), "hand_r": hang_r,
              "fingers_l": LAMP_FIST, "fingers_r": RELAX}, "auto"),
        # The lamp meets the river (its flame goes out here, 1.1 s).
        (33, {**_knelt(P, H, sag=0.8), "neck": (2, 14, 0), "head": (4, 18, 2),
              "hand_l": _hand(P, (0.17, WATER + 0.26, 0.33), (0.8, -0.3, -0.5), (0.0, 1.0, 0.2)), "hand_r": hang_r,
              "fingers_l": LAMP_FIST, "fingers_r": RELAX}, "auto"),
        # Under, and the arm comes to rest on his thigh; the head bowed.
        (52, {**_knelt(P, H, sag=1.0), "neck": (0, 18, 0), "head": (0, 22, 0),
              "hand_l": _hand(P, (0.18, 0.46, 0.30), (0.6, 0.0, -0.8), (0.0, 0.6, 0.8)), "hand_r": hang_r,
              "fingers_l": LAMP_FIST, "fingers_r": RELAX}, "ease"),
        (75, {**_knelt(P, H, breath=-0.5, sag=1.0), "neck": (0, 19, 0), "head": (0, 23, 0),
              "hand_l": _hand(P, (0.18, 0.45, 0.30), (0.6, 0.0, -0.8), (0.0, 0.6, 0.8)), "hand_r": hang_r,
              "fingers_l": LAMP_FIST, "fingers_r": RELAX}, "ease"),
    ]
    return build(name, rig, keys, meta={"layer": "full", "hold": True, "source": "keyed (tools/anim/clips/warden.py)",
                                        "note": "the Warden (C03): the fist lowered, the lamp into the river"})


def fold_forward(name, rig: Rig):
    P, H = _kit(rig)
    knelt = _knelt(P, H, breath=-0.5, sag=1.0)
    rest_l = _hand(P, (0.18, 0.45, 0.30), (0.6, 0.0, -0.8), (0.0, 0.6, 0.8))
    hang_r = _hand(P, (-0.26, 0.38, 0.02), (-0.5, 0.0, -1.0))
    keys = [
        (0, {**knelt, "neck": (0, 19, 0), "head": (0, 23, 0), "hand_l": rest_l, "hand_r": hang_r,
             "fingers_l": LAMP_FIST, "fingers_r": RELAX}, "ease"),
        # The last of him goes: the head drops, the shoulders roll in.
        (12, {**knelt, "spine": (0, 14, 0), "neck": (0, 24, 0), "head": (4, 26, 6), "clav_l": (-4, 10), "clav_r": (-4, 10),
              "hand_l": rest_l, "hand_r": hang_r, "fingers_l": LAMP_FIST, "fingers_r": RELAX}, "ease"),
        # Tipping over the knees, slow, then faster.
        (32, {**knelt, "hips": {"pos": H(0, 0.47, 0.06), "rot": (4, 30, 4)}, "spine": (4, 20, 4), "neck": (0, 18, 0), "head": (8, 20, 10),
              "hand_l": _hand(P, (0.20, 0.42, 0.24), (0.7, 0.0, -0.7)), "hand_r": _hand(P, (-0.22, 0.36, 0.10), (-0.7, 0.0, -0.7)),
              "fingers_l": LAMP_FIST, "fingers_r": RELAX}, "auto"),
        (46, {**knelt, "hips": {"pos": H(0, 0.40, 0.14), "rot": (8, 58, 8)}, "spine": (6, 14, 6), "neck": (6, -2, 0), "head": (20, 4, 14),
              "foot_l": {"pos": P(0.16, 0.02, -0.50), "rot": (8, -80, 0), "pole": (0.2, -0.2, 1)},
              "foot_r": {"pos": P(-0.15, 0.03, -0.54), "rot": (-8, -80, 0), "pole": (-0.2, -0.2, 1)},
              # The arms hang from him as he goes, trailing a little.
              "hand_l": _hand(P, (0.22, 0.22, 0.38), (0.7, 0.3, -0.6)), "hand_r": _hand(P, (-0.22, 0.20, 0.36), (-0.7, 0.3, -0.6)),
              "fingers_l": LAMP_FIST, "fingers_r": OPEN}, "linear"),
        # Into the water face first, no hand put out; the legs slide out behind.
        (54, merge(_on_face(P, H), hips={"pos": H(0.0, 0.13, 0.34), "rot": (6, 90, 4)}, neck=(10, -6, 0), head=(24, -2, 0),
                   foot_l={"pos": P(0.30, 0.10, -0.34), "rot": (20, 120, -30), "pole": (1, 0.1, 0.4)},
                   foot_r={"pos": P(-0.16, 0.08, -0.58), "rot": (-15, 120, 0), "pole": (-0.2, -1, 0)},
                   hand_l={"frame": "char", "pos": P(0.30, 0.08, 0.80), "pole": (1, 0.3, -0.2), "knuckles": (0.2, 0, 1)},
                   fingers_l=LAMP_FIST, fingers_r=OPEN), "auto"),
        (60, merge(_on_face(P, H), hips={"pos": H(0.0, 0.15, 0.36), "rot": (8, 87, 6)}, neck=(16, -12, 0), head=(36, -8, 0),
                   fingers_l=LAMP_FIST, fingers_r=OPEN), "auto"),
        (72, merge(_on_face(P, H, 1.0), fingers_l=LAMP_FIST, fingers_r=OPEN), "ease"),
        (120, merge(_on_face(P, H, 1.0), fingers_l=LAMP_FIST, fingers_r=OPEN), "ease"),
    ]
    keys = _in_char(rig, keys)
    return build(name, rig, keys, meta={"layer": "full", "hold": True, "source": "keyed (tools/anim/clips/warden.py)",
                                        "note": "the Warden (C03): folded forward into the river, face down, still"})


# name: function(name, rig) -> Clip or None (the take not on this machine).
CLIPS = {"lie_arm_up": lie_arm_up, "rise_stiff": rise_stiff, "wade_drag": wade_drag, "bend_lift": bend_lift, "kneel_lamp": kneel_lamp, "lamp_down": lamp_down,
         "fold_forward": fold_forward}
