"""Her clips for C04 A, First Light (godot/data/cinematics/c04a.json).

- flask_drink (A6, and held under A7): standing on the road in the first
  sun. She lifts the flask that hangs on its cord from her right wrist and
  looks at it; bites the cork and pulls it (the click at 1.0 s); the left
  hand takes the cork from her teeth; she brings the flask up under her
  nose and stops: the river (her head draws back and aside, 1.5 s). A beat
  looking at it. Then she drinks anyway (from 2.3 s): the head goes back,
  the flask tips higher as it empties, four swallows; off it at 4.3 s with
  a breath, and the flask comes down to her waist, the left hand to it
  with the cork. Then she stands so, only breathing, for A7's 6.5 s (the
  close-up on her eyes: she reaches for her mother's face).

  The body is a captured standing (100STYLE Neutral, CC BY 4.0), so the
  weight and the breath under it are real; the back, the neck and the head
  are keyed over it, and the hands are placed by what they hold (held.py):
  the flask's spout on her lips, the cork in her teeth, wherever the head
  has gone.
"""
from __future__ import annotations

import math

import numpy as np

from clips.mocap import take
from held import FACE, GRIP, face_point, flask_dirs, in_head, slerp_dir, solved, wrist_for
from keyed import Rig, Track
from retarget import Source, clip_from, face_forward, in_place, lean_neck, retarget


def _f(curl, thumb, cascade=0.25, spread=0.0, oppose=0.0):
    """Fingers, every key the same shape (a preset name and a dict do not blend)."""
    return {"curl": curl, "thumb": thumb, "cascade": cascade, "spread": spread, "oppose": oppose}


def standing(rig: Rig, style="Neutral", seconds=12.0):
    """A stretch of a 100STYLE idle take, unlooped, centred: a body to key over."""
    path, start, stop = take(style, "ID")
    stop = min(stop, start + int(seconds * 60) + 2)
    src = Source(path, start, stop)
    local, pos, _ = retarget(rig.sk, src, stance=0.8)
    local, pos = face_forward(rig.sk, local, pos)
    local = lean_neck(rig, local)
    pos, _, _ = in_place(rig.sk, pos)
    meta = {"source": f"100STYLE {style}_ID frames {start}-{stop} (60 fps)", "licence": "CC BY 4.0",
            "changes": "retargeted to her skeleton, feet locked, centred; back, head and arms keyed over"}
    return clip_from(f"{style}_stand", rig.sk, local, pos, meta=meta)


# ------------------------------------------------------------- flask_drink --
# The flask's points in her right hand's frame (the hand bone's): its grip
# (Arms.Hold's mount) and, 9 cm up out of the thumb side, the spout; the
# cork stands 2 cm above that.
SPOUT = GRIP + np.array([0.0, 0.0, 0.09])
CORK = GRIP + np.array([0.0, 0.0, 0.11])
# The left hand's pinch (between the thumb's and the index's tips), in its
# own frame.
PINCH_L = np.array([0.03, 0.15, 0.05])

FLASK_GRIP = {**_f(0.62, 0.4, 0.12, 0.0, 0.35), "tip": 0.5}
HANG = _f(0.3, 0.15, 0.25)
READY = _f(0.2, 0.1, 0.15, 3.0)
PINCHED = _f(0.55, 0.55, 0.35, 0.0, 0.7)


def _body_keys():
    """Back, neck and head over the captured standing (degrees: yaw + to her
    left, pitch + down), and the shoulders."""
    K = []

    def k(fr, spine=(0, 0, 0), neck=(0, 0, 0), head=(0, 0, 0), clav_l=(0, 0), clav_r=(0, 0), ease="auto"):
        K.append((fr, {"spine": spine, "neck": neck, "head": head, "clav_l": clav_l, "clav_r": clav_r}, ease))

    k(0, ease="ease")
    # She looks down at the flask as it comes up.
    k(12, spine=(0, 2, 0), neck=(0, 6, 0), head=(-2, 10, 0))
    # The head comes down to it, a little to her right, and bites the cork.
    k(24, spine=(0, 3, 0), neck=(0, 4, 0), head=(-4, 11, 2), clav_r=(3, 2))
    k(28, spine=(0, 3, 0), neck=(0, 5, 0), head=(-4, 13, 3), clav_r=(3, 2), ease="ease")
    # The pull (the click at 1.0 s): the head tugs back against the hand.
    k(30, spine=(0, 2, 0), neck=(0, 2, 0), head=(-3, 6, 1), clav_r=(2, 1), ease="ease")
    k(36, spine=(0, 2, 0), neck=(0, 3, 0), head=(-1, 7, 0))
    # The left hand takes the cork from her teeth.
    k(40, spine=(0, 1, 0), neck=(0, 3, 0), head=(0, 7, 0))
    # Under her nose: a breath in, the chest lifting, the head bowed to it.
    k(44, spine=(0, -2, 0), neck=(0, 4, 0), head=(0, 9, 0), clav_l=(2, 0), clav_r=(2, 0))
    # The river: the head draws back and turns aside, the chin in.
    k(49, spine=(0, -1, 0), neck=(0, -4, 0), head=(7, 7, -4), clav_l=(1, 0), clav_r=(1, 0), ease="ease")
    k(56, spine=(0, 0, 0), neck=(0, -3, 0), head=(6, 8, -3))
    # A beat, looking down at it.
    k(62, spine=(0, 2, 0), neck=(0, 3, 0), head=(1, 12, 0), ease="ease")
    # Anyway: a breath, and up to it.
    k(67, spine=(0, -2, 0), neck=(0, 0, 0), head=(0, 4, 0), clav_r=(2, 2))
    # Drinking: the head back, more as the flask empties; the right shoulder up with the elbow.
    k(73, spine=(0, -4, 0), neck=(0, -8, 0), head=(-2, -12, 0), clav_r=(4, 4))
    k(90, spine=(0, -5, 0), neck=(0, -10, 0), head=(-2, -15, 0), clav_r=(5, 4))
    k(108, spine=(0, -6, 0), neck=(0, -12, 0), head=(-2, -17, 0), clav_r=(6, 4))
    k(126, spine=(0, -7, 0), neck=(0, -13, 0), head=(-2, -19, 0), clav_r=(6, 4), ease="ease")
    # Off it: the head comes forward, a breath out (the shoulders drop).
    k(134, spine=(0, -2, 0), neck=(0, -2, 0), head=(-1, -3, 0), clav_r=(3, 2))
    k(143, spine=(0, 3, 0), neck=(0, 3, 0), head=(0, 3, 0), clav_l=(-2, 0), clav_r=(-2, 0))
    k(152, spine=(0, 2, 0), neck=(0, 2, 0), head=(0, 1, 0), ease="ease")
    # Held for A7: slow breaths, the shoulders with them; at its 2.6 s the
    # eyes go up and to her left, and the head follows a little; back at 4.6 s.
    t = 152
    for i, fr in enumerate(range(170, 350, 32)):
        lift = 1.0 if i % 2 == 0 else -0.4
        look = 1.0 if 230 <= fr <= 290 else 0.0
        k(fr, spine=(0, 2 - 1.2 * lift, 0), neck=(0, 2, 0), head=(2.5 * look, 1 - 2.0 * look, 1.0 * look),
          clav_l=(1.2 * lift, 0), clav_r=(1.2 * lift, 0), ease="ease")
    return K


def _swallows(fr):
    """The head's small lift with each swallow (no throat to bob), degrees of pitch."""
    out = 0.0
    for s in (81, 97, 112, 124):
        u = (fr - s) / 8.0
        if 0 <= u <= 1:
            out -= 2.2 * math.sin(math.pi * u) ** 2
    return out


def _flask(fr):
    """The flask on her face (head space): which of its points goes where
    (a FACE point and an offset from it in her head's frame), its neck's
    angle (flask_dirs), and how much the face has it (0: the hand is keyed
    in her space instead)."""
    keys = [
        # (frame, point in hand, face place, offset, phi, psi, on the face)
        (14, CORK, "teeth", (0.0, -0.06, 0.12), -70, 12, 0.0),
        (24, CORK, "teeth", (0.0, -0.004, 0.012), -55, 12, 1.0),
        (28, CORK, "teeth", (0.0, 0.0, 0.0), -52, 12, 1.0),
        (30, SPOUT, "mouth", (-0.02, -0.07, 0.07), -62, 14, 1.0),
        (36, SPOUT, "mouth", (-0.03, -0.09, 0.08), -68, 14, 1.0),
        (40, SPOUT, "mouth", (-0.02, -0.07, 0.07), -72, 10, 1.0),
        # Under her nose.
        (44, SPOUT, "nose", (-0.005, -0.03, 0.022), -76, 6, 1.0),
        (49, SPOUT, "nose", (-0.015, -0.05, 0.075), -74, 8, 1.0),
        (56, SPOUT, "mouth", (-0.03, -0.10, 0.11), -78, 10, 1.0),
        (62, SPOUT, "mouth", (-0.03, -0.12, 0.12), -80, 10, 1.0),
        # To her lips, tipping up as she drinks.
        (67, SPOUT, "mouth", (0.0, -0.015, 0.025), -20, 12, 1.0),
        (73, SPOUT, "mouth", (0.0, 0.0, -0.004), 2, 12, 1.0),
        (90, SPOUT, "mouth", (0.0, 0.0, -0.004), 10, 12, 1.0),
        (108, SPOUT, "mouth", (0.0, 0.0, -0.004), 16, 12, 1.0),
        (126, SPOUT, "mouth", (0.0, 0.0, -0.004), 22, 12, 1.0),
        # Off it, and down.
        (134, SPOUT, "mouth", (-0.02, -0.06, 0.08), -45, 12, 1.0),
        (144, SPOUT, "mouth", (-0.04, -0.25, 0.14), -80, 10, 0.0),
    ]
    # Every offset taken from her lips, so a key on her nose and the next on
    # her lips blend without a jump.
    return [(k[0], k[1], "mouth", tuple(np.asarray(k[3], float) + FACE[k[2]] - FACE["mouth"])) + k[4:] for k in keys]


def _ease_between(keys, fr, idx):
    """A key's value at fr, smoothstep between the keys either side."""
    if fr <= keys[0][0]:
        return keys[0][idx]
    for a, b in zip(keys, keys[1:]):
        if fr <= b[0]:
            u = (fr - a[0]) / (b[0] - a[0])
            u = u * u * (3 - 2 * u)
            va, vb = a[idx], b[idx]
            if isinstance(va, str):
                return va if u < 0.5 else vb
            return np.asarray(va, float) + (np.asarray(vb, float) - np.asarray(va, float)) * u
    return keys[-1][idx]


def _hand_char(keys, fr):
    """A hand keyed in her space: (pos, blade, knuckles, pole) eased between keys."""
    out = []
    for i in range(1, 5):
        v = _ease_between(keys, fr, i)
        out.append(np.asarray(v, float))
    return out


# The right hand in her space, away from her face.
FLASK_R = [
    # (frame, wrist, blade, knuckles, pole)
    (0, (-0.21, 1.04, 0.05), (0.05, -0.2, 1.0), (-0.1, -1.0, 0.0), (-0.3, 0.0, -1.0)),
    (14, (-0.10, 1.22, 0.20), (0.15, 1.0, 0.1), (0.2, 0.0, 1.0), (-0.8, -0.6, -0.1)),
    (144, (-0.08, 1.21, 0.22), (0.25, 1.0, 0.15), (0.3, -0.1, 1.0), (-0.7, -0.7, -0.1)),
    (158, (-0.05, 1.12, 0.20), (0.3, 1.0, 0.2), (0.4, -0.2, 1.0), (-0.6, -0.8, -0.1)),
    (350, (-0.05, 1.11, 0.20), (0.3, 1.0, 0.2), (0.4, -0.2, 1.0), (-0.6, -0.8, -0.1)),
]
# The left hand: at her side; up for the cork; the cork held at her chest,
# then at her side while she drinks; then to the flask at her waist.
CORK_L = [
    (0, (0.21, 1.04, 0.04), (-0.05, -0.2, 1.0), (0.1, -1.0, 0.0), (0.3, 0.0, -1.0)),
    (22, (0.21, 1.05, 0.05), (-0.05, -0.2, 1.0), (0.1, -1.0, 0.0), (0.3, 0.0, -1.0)),
    (48, (0.12, 1.25, 0.20), (-0.3, 0.4, 0.9), (-0.2, 0.9, -0.2), (0.7, -0.7, -0.2)),
    (60, (0.13, 1.20, 0.18), (-0.3, 0.4, 0.9), (-0.2, 0.9, -0.2), (0.7, -0.7, -0.2)),
    (78, (0.20, 1.05, 0.07), (-0.05, -0.1, 1.0), (0.1, -1.0, 0.1), (0.4, 0.0, -1.0)),
    (140, (0.20, 1.05, 0.07), (-0.05, -0.1, 1.0), (0.1, -1.0, 0.1), (0.4, 0.0, -1.0)),
    (166, (0.05, 1.14, 0.22), (-0.4, 0.6, 0.6), (-0.6, 0.0, 0.8), (0.6, -0.8, -0.1)),
    (350, (0.05, 1.13, 0.22), (-0.4, 0.6, 0.6), (-0.6, 0.0, 0.8), (0.6, -0.8, -0.1)),
]
# The left hand at her teeth for the cork (head space): pinch on the cork,
# the fingers up toward her mouth from below and to her left.
CORK_FACE = [
    (30, (0.03, -0.09, 0.10), 0.0),
    (36, (0.01, -0.01, 0.025), 1.0),
    (40, (0.01, 0.0, 0.012), 1.0),
    (45, (0.04, -0.06, 0.08), 1.0),
    (52, (0.06, -0.14, 0.14), 0.0),
]


def _cork_face(fr):
    if fr <= CORK_FACE[0][0] or fr >= CORK_FACE[-1][0]:
        return None, 0.0
    off = _ease_between(CORK_FACE, fr, 1)
    w = float(_ease_between(CORK_FACE, fr, 2))
    return off, w


def _fingers_r(fr):
    return FLASK_GRIP


def _fingers_l(fr):
    if fr < 30:
        return HANG
    if fr < 38:
        return READY
    if fr < 160:
        return PINCHED
    return PINCHED


def flask_drink(rig: Rig):
    sk = rig.sk
    n = 350
    base = standing(rig, "Neutral", seconds=n / 30 + 0.2)
    body = Track(_body_keys())
    # The body alone first, to know where her face is each frame.
    poses = []
    for fr in range(n):
        p = body(fr)
        p["head"] = (p["head"][0], p["head"][1] + _swallows(fr), p["head"][2])
        poses.append(p)
    first = solved("flask_body", rig, poses, base=base)
    g, gp = sk.fk(first.rot, first.pos)
    I = sk.index
    fk = _flask(0)
    keys = []
    for fr in range(n):
        pose = dict(poses[fr])
        # The right hand: on her face where the flask is, else in her space.
        pos_c, blade_c, knuck_c, pole_c = _hand_char(FLASK_R, fr)
        w = float(_ease_between(fk, fr, 6))
        if w > 0:
            local = _ease_between(fk, fr, 1)
            place = _ease_between(fk, fr, 2)
            off = _ease_between(fk, fr, 3)
            phi = float(_ease_between(fk, fr, 4))
            psi = float(_ease_between(fk, fr, 5))
            neck, knuck = flask_dirs(phi, psi)
            blade_f, knuck_f = in_head(sk, g, gp, fr, neck), in_head(sk, g, gp, fr, knuck)
            pos_f = wrist_for(face_point(sk, g, gp, fr, place, off), local, blade_f, knuck_f)
            pos_c = pos_c + (pos_f - pos_c) * w
            blade_c = slerp_dir(blade_c, blade_f, w)
            knuck_c = slerp_dir(knuck_c, knuck_f, w)
            pole_c = slerp_dir(pole_c, (-0.35, -0.6, 0.7), w)
        pose["hand_r"] = {"pos": tuple(pos_c), "blade": tuple(blade_c), "knuckles": tuple(knuck_c), "pole": tuple(pole_c), "frame": "char"}
        # The left hand: to her teeth for the cork, else in her space.
        pos_l, blade_l, knuck_l, pole_l = _hand_char(CORK_L, fr)
        off, wl = _cork_face(fr)
        if wl > 0:
            bl = in_head(sk, g, gp, fr, (-0.2, 0.75, 0.6))
            kl = in_head(sk, g, gp, fr, (-0.45, 0.55, -0.7))
            pl = wrist_for(face_point(sk, g, gp, fr, "teeth", off), PINCH_L, bl, kl)
            pos_l = pos_l + (pl - pos_l) * wl
            blade_l = slerp_dir(blade_l, bl, wl)
            knuck_l = slerp_dir(knuck_l, kl, wl)
            pole_l = slerp_dir(pole_l, (0.8, -0.6, 0.0), wl)
        pose["hand_l"] = {"pos": tuple(pos_l), "blade": tuple(blade_l), "knuckles": tuple(knuck_l), "pole": tuple(pole_l), "frame": "char"}
        pose["fingers_r"] = _fingers_r(fr)
        pose["fingers_l"] = _fingers_l(fr)
        keys.append(pose)
    meta = dict(base.meta, layer="full", hold=True,
                note="C04 A6-A7: the flask uncorked with her teeth, smelt, drunk anyway; held, breathing")
    meta["source"] = "keyed over " + base.meta["source"]
    return solved("flask_drink", rig, keys, base=base, meta=meta)


ALL = (("flask_drink", flask_drink),)
JUDGED: set[str] = set()


def clips(rig, want):
    return [f(rig) for name, f in ALL
            if (want and any(w in name for w in want)) or (not want and name in JUDGED)]
