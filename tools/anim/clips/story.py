"""Her clips for the cinematics (godot/data/cinematics/*.json, played whole
on the timeline's clock by PersonView.Cue): keyed where a performance has to
hit a mark the camera is built round.

- lie_side_wake (C01): on her right side on the cold ground where she was
  left, utterly still but for the breath; a stir; then, slowly, worn out,
  up onto her right elbow, the head hanging, the other hand pushing at the
  ground. She lies along her right (the head toward -X), facing +Z, so the
  camera finds her face from in front of her.
- sit_back_heels (C01): from the elbow, up onto the hand, the legs drawn
  round under her into a side-sit, over onto her knees, and back onto her
  heels, facing +Z; then the hands come up before her, palms up, and she
  looks down at them. Held.
- reach_coals (C01): kneeling so, the right hand goes out low over the
  fire, palm down, and stops there; held, not drawn back.
"""
from __future__ import annotations

import math

import numpy as np

from clips.actions import arm
from held import contact_build, forearm_on_ground, knee_clear, slerp_dir
from keyed import build, merge, smoothstep_


def _f(curl, thumb, cascade=0.25, spread=0.0):
    """Fingers, every key the same shape (a preset name and a dict do not
    blend)."""
    return {"curl": curl, "thumb": thumb, "cascade": cascade, "spread": spread}


RELAXED, OPEN = _f(0.28, 0.15), _f(0.05, 0.0, 0.0, 4.0)


def _side(breath=0.0, stir=0.0):
    """Lying on her right side, a little curled: the knees drawn up, the
    left leg over the right, the right arm out under her head, the left
    hand fallen on the ground before her chest."""
    return {
        "hips": {"pos": (0.0, -0.87, 0.0), "rot": (0, 8, 90)},
        "spine": (0, 14 + 2 * breath, -4), "neck": (0, 6, 16), "head": (0, 8 - 3 * stir, 14 - 6 * stir),
        "foot_r": {"pos": (0.70, -0.04, 0.30), "rot": (0, 0, 90), "pole": (0, 0, 1)},
        "foot_l": {"pos": (0.62, 0.07, 0.40), "rot": (0, 10, 88), "pole": (0, 0, 1)},
        # (Arms in character space: she lies along -X, the ground at y 0.)
        "hand_r": {"pos": (-0.90, 0.05, 0.24), "pole": (0, 0.3, 1), "knuckles": (-0.6, 0, 0.8)},
        "hand_l": {"pos": (-0.30 + 0.02 * stir, 0.05, 0.30), "pole": (0, 1, 0.4), "knuckles": (-0.3, 0, 1)},
        "clav_l": (0, 8), "clav_r": (0, -4),
        "fingers_l": _f(0.28 + 0.3 * stir, 0.15 + 0.15 * stir),
        "fingers_r": RELAXED,
    }


def _elbow(up=1.0, sag=0.0):
    """Propped on her right forearm, the chest lifted off the ground, the
    left hand flat before her bearing some of it; the head hanging."""
    return {
        "hips": {"pos": (0.0, -0.87, 0.0), "rot": (0, 10, 90 - 31 * up)},
        "spine": (0, 12, -6 * up), "neck": (0, 18 + 8 * sag, -6), "head": (0, 22 + 10 * sag, -10),
        "foot_r": {"pos": (0.70, -0.015, 0.30), "rot": (0, 0, 90), "pole": (0, 0.4, 1)},
        "foot_l": {"pos": (0.62, 0.07, 0.42), "rot": (0, 10, 86), "pole": (0, 0, 1)},
        "hand_r": {"pos": (-0.52, 0.05, 0.28), "pole": (-0.3, -1, -0.4), "knuckles": (-0.5, 0, 1)},
        "hand_l": {"pos": (-0.22, 0.05, 0.40), "pole": (0.6, 1, 0), "knuckles": (-0.3, 0, 1)},
        "clav_l": (4, 10), "clav_r": (14, 6),
        "fingers_l": OPEN, "fingers_r": OPEN,
    }


def _aimed_only(spec):
    """A keyed hand without its place (a contact puts it), keeping its aim."""
    return {k: v for k, v in spec.items() if k not in ("arc", "mix", "pos")}


PROP_TOWARD = (-0.55, 0.0, 0.83)  # her right forearm along the ground, toward her head and before her


def lie_side_wake(rig):
    keys = []
    # Still, two slow breaths.
    for f in range(0, 61, 15):
        keys.append((f, _side(breath=math.sin(f / 30 * math.pi)), "ease"))
    # The stir: a deeper breath, the fingers close on the ground.
    keys.append((75, _side(breath=1.5, stir=1.0), "ease"))
    keys.append((90, _side(breath=0.2, stir=1.0), "ease"))
    # Up onto the elbow, slow and heavy: a first try that barely lifts, then the weight onto it.
    keys.append((110, merge(_elbow(0.25, 1.0), neck=(0, 10, -12), head=(0, 12, -14)), "auto"))
    keys.append((130, _elbow(0.6, 1.0), "auto"))
    keys.append((150, _elbow(1.0, 0.6), "ease"))
    # Held there, breathing hard, the head hanging.
    keys.append((170, _elbow(0.96, 1.0), "ease"))
    keys.append((190, _elbow(1.0, 0.7), "ease"))
    keys.append((210, _elbow(0.96, 1.0), "ease"))

    def contacts(fr, g, p, pose):
        # The right arm comes in from under her head to lie along the ground
        # under her shoulder, and she rises onto that forearm.
        # The arm sweeps along the ground from over her head (her -X) round to
        # before her, the elbow drawn in as the shoulder lifts.
        w = smoothstep_((fr - 92) / 26.0)
        if w <= 0:
            return {}
        toward = slerp_dir((-1.0, 0.0, 0.12), PROP_TOWARD, w)
        hand, pole = forearm_on_ground(rig.sk, p, fr, "r", toward, ground=0.035)
        keyed = pose["hand_r"]
        k = min(1.0, w * 3)
        at = np.asarray(keyed["pos"], float) * (1 - k) + hand * k
        return {"hand_r": {**_aimed_only(keyed), "pos": tuple(at), "pole": tuple(np.asarray(keyed["pole"], float) * (1 - k) + pole * k),
                           "knuckles": tuple(slerp_dir(keyed["knuckles"], toward, k))}}

    return contact_build("lie_side_wake", rig, keys, contacts,
                         meta={"layer": "full", "hold": True, "source": "keyed (tools/anim/clips/story.py)", "licence": "own work",
                               "note": "keyed (C01): on her right side, then up onto the forearm"})


def _heels(look=1.0, hands=1.0, breath=0.0):
    """Kneeling back on her heels, facing +Z, the shins flat behind, the
    hands held up before her, palms up, the head bowed to look at them
    (hands 0: resting on her thighs)."""
    # Sat on her heels: the ankles under the hips, the tops of the feet flat
    # on the ground behind and the toes pointing back, so the knees come
    # down onto the ground a thigh's length ahead (her thigh 0.49, shin
    # 0.45). The hands rest on the thighs, or are held up before her.
    lap = 0.29 + 0.05 * hands
    return {
        "hips": {"pos": (0.0, -0.80, -0.08), "rot": (0, 6, 0)},
        "spine": (0, 10 + 8 * look + 2 * breath, 0), "neck": (0, 10 + 8 * look, 0), "head": (0, 10 + 16 * look, 0),
        "foot_l": {"pos": (0.11, -0.045, -0.11), "rot": (4, 140, 0), "pole": (0.1, 0, 1)},
        "foot_r": {"pos": (-0.11, -0.045, -0.11), "rot": (-4, 140, 0), "pole": (-0.1, 0, 1)},
        # (Her arms are short for her legs: resting, the hands lie high on the thighs.)
        "hand_l": {"pos": (0.12 - 0.01 * hands, lap, 0.14 + 0.18 * hands), "pole": (0.7, -0.5, -0.3),
                   "knuckles": (0.1, 0.25 * hands - 0.35 * (1 - hands), 1.0), "blade": (1.0, 0.0, -0.1), "aim": 1.0},
        "hand_r": {"pos": (-0.12 + 0.01 * hands, lap, 0.14 + 0.18 * hands), "pole": (-0.7, -0.5, -0.3),
                   "knuckles": (-0.1, 0.25 * hands - 0.35 * (1 - hands), 1.0), "blade": (-1.0, 0.0, -0.1), "aim": 1.0},
        "clav_l": (0, 6), "clav_r": (0, 6),
        "fingers_l": _f(0.3, 0.2), "fingers_r": _f(0.3, 0.2),
    }


def _zsit(lean=1.0):
    """Sat up sideways on her right hip, the legs folded round to her left
    (the right shin across in front, the left foot back by her left hip),
    leaning on her right hand on the ground; the head bowed."""
    return {
        "hips": {"pos": (-0.04, -0.94, 0.0), "rot": (-22, -4, 16)},
        "spine": (12, 6 + 4 * lean, -8 - 4 * lean), "neck": (6, 12, -2), "head": (4, 16, -2),
        "foot_r": {"pos": (0.20, -0.045, 0.24), "rot": (78, 20, -70), "pole": (0.2, 0.3, 1)},
        "foot_l": {"pos": (0.44, -0.05, -0.20), "rot": (-10, 140, 0), "pole": (0.6, 0.0, 1)},
        "hand_r": {"pos": (-0.36, 0.05, 0.04), "pole": (-0.5, 0, -1), "knuckles": (-0.4, 0, 1)},
        "hand_l": {"pos": (0.16, 0.28, 0.20), "pole": (0.6, -0.5, -0.4), "knuckles": (0.1, -0.5, 1)},
        "clav_l": (0, 6), "clav_r": (10, 2), "fingers_l": RELAXED, "fingers_r": OPEN,
    }


def sit_back_heels(rig):
    start = _elbow(0.96, 1.0)
    z = _zsit()
    keys = [
        (0, start, "ease"),
        # A breath; the head comes up.
        (12, merge(start, neck=(0, 12, -6), head=(0, 14, -10)), "ease"),
        # Up onto the right hand, the arm straightening under her, the left
        # hand pushing; the hips rolling under her.
        (34, merge(start, hips={"pos": (-0.02, -0.89, 0.02), "rot": (-10, 6, 40)}, spine=(4, 8, -6), neck=(2, 10, -4), head=(2, 12, -6),
                   hand_l={"pos": (-0.12, 0.05, 0.38), "pole": (0.6, 1, 0), "knuckles": (-0.2, 0, 1)}), "auto"),
        # Sat up sideways on the right hip, the legs round to her left.
        (58, z, "auto"),
        (64, merge(z, spine=(10, 14, -8), neck=(4, 10, -2), head=(2, 12, 0)), "auto"),
        # Over onto her knees: the hips up off the ground and over them, the
        # right leg drawn under; the right hand pushes off the ground.
        (78, {"hips": {"pos": (0.0, -0.66, -0.02), "rot": (-6, 30, 4)}, "spine": (4, 22, -2), "neck": (0, 8, 0), "head": (0, 10, 0),
              "foot_l": {"pos": (0.14, -0.055, -0.30), "rot": (2, 140, 0), "pole": (0.15, 0, 1)},
              "foot_r": {"pos": (-0.10, -0.04, -0.24), "rot": (-6, 135, 0), "pole": (-0.1, 0, 1)},
              "hand_r": {"pos": (-0.16, 0.30, 0.22), "pole": (-0.6, -0.5, -0.4), "knuckles": (-0.1, -0.4, 1)},
              "hand_l": {"pos": (0.15, 0.32, 0.20), "pole": (0.7, -0.5, -0.3), "knuckles": (0.1, -0.5, 1)},
              "clav_l": (0, 6), "clav_r": (4, 6), "fingers_l": RELAXED, "fingers_r": RELAXED}, "auto"),
        # Back onto her heels, the hands to her thighs; a breath.
        (96, _heels(look=0.3, hands=0.0, breath=1.0), "ease"),
        (118, _heels(look=0.5, hands=0.0, breath=-0.5), "ease"),
        # The hands come up before her, and she looks down at them.
        (142, _heels(look=1.0, hands=1.0), "ease"),
        (180, _heels(look=1.0, hands=1.0, breath=0.6), "ease"),
    ]
    def contacts(fr, g, p, pose):
        # The knees kept on the ground, not through it, whatever the legs do.
        out = {f"foot_{s}": knee_clear(rig, p, fr, s, pose[f"foot_{s}"]) for s in "lr" if f"foot_{s}" in pose}
        # The right forearm on the ground as she starts up off it.
        if fr < 30:
            w = 1.0 - smoothstep_((fr - 6) / 24.0)
            hand, pole = forearm_on_ground(rig.sk, p, fr, "r", PROP_TOWARD, ground=0.035)
            keyed = pose["hand_r"]
            at = hand * w + np.asarray(keyed["pos"], float) * (1 - w)
            out["hand_r"] = {**_aimed_only(keyed), "pos": tuple(at), "pole": tuple(pole * w + np.asarray(keyed["pole"], float) * (1 - w)),
                             "knuckles": tuple(slerp_dir(keyed.get("knuckles", PROP_TOWARD), PROP_TOWARD, w))}
        return out

    return contact_build("sit_back_heels", rig, keys, contacts,
                         meta={"layer": "full", "hold": True, "source": "keyed (tools/anim/clips/story.py)", "licence": "own work",
                               "note": "keyed (C01): from the forearm to sitting sideways, onto her knees and back on her heels, looking at her hands"})


def reach_coals(rig):
    start = _heels(look=1.0, hands=1.0, breath=0.6)
    out = merge(start, spine=(0, 22, 0), neck=(0, 6, 0), head=(0, 4, 0), clav_r=(-2, 14),
                hand_r={"pos": (-0.10, 0.37, 0.42), "pole": (-0.8, -0.3, 0), "knuckles": (0.0, -0.25, 1.0), "blade": (1.0, -0.1, 0.0)},
                hand_l={"pos": (0.12, 0.29, 0.14), "pole": (0.7, -0.5, -0.3), "knuckles": (0.1, -0.35, 1), "blade": (1.0, 0.0, -0.1)},
                fingers_r=_f(0.12, 0.05, 0.2))
    keys = [
        (0, start, "ease"),
        # Out, slow, palm down over the warmth; the left hand falls to her thigh.
        (24, merge(out, hand_r={"pos": (-0.11, 0.39, 0.37)}), "auto"),
        (36, out, "ease"),
        # Held: only the breath, and the fingers spreading a little to the heat.
        (66, merge(out, spine=(0, 23, 0), fingers_r=_f(0.06, 0.0, 0.2, 3.0)), "ease"),
        (96, merge(out, spine=(0, 22, 0), fingers_r=_f(0.04, 0.0, 0.2, 5.0)), "ease"),
        (126, merge(out, spine=(0, 23, 0), fingers_r=_f(0.04, 0.0, 0.2, 5.0)), "ease"),
    ]
    return build("reach_coals", rig, keys, meta={"layer": "full", "hold": True,
                                                  "note": "keyed (C01): kneeling, the right hand held out over the fire, palm down"})


# ------------------------------------------------------------------ letter --
# C01 shot 6 (7 s), on her heels by the embers: the hand comes back from the
# coals; she turns her right wrist up and looks at the cord wound on it and
# the full flask (to 1.6 s); across at the bedroll, dry (1.6 to 2.6 s); then
# the left hand goes inside her top at the right breast and brings out a
# folded letter (3.2 s); both hands open it before her (to 4.1 s) and she
# looks: the ink has run to blue water, no word left (to 5.5 s). She folds
# it (to 6.2 s) and puts it back (6.8 s), and the hand comes down.
#
# The letter (a prop for cinematics): folded twice, about 10 by 7 cm, held in
# the left hand's pinch until it opens; open, 20 by 14 cm, a hand at each
# side edge. The letter's place in each hand: PINCH_L/PINCH_R, below.

PINCH = {"curl": 0.42, "thumb": 0.55, "cascade": 0.3, "spread": 0.0}
LOOSE = {"curl": 0.3, "thumb": 0.15, "cascade": 0.25, "spread": 0.0}


def letter(rig):
    rest = _heels(look=0.3, hands=0.0)

    def kneel(spine=(0, 14, 0), neck=(0, 12, 0), head=(0, 16, 0), clav_l=(0, 6), clav_r=(0, 6), **over):
        p = merge(rest, spine=spine, neck=neck, head=head, clav_l=clav_l, clav_r=clav_r, fingers_l=LOOSE, fingers_r=LOOSE)
        p.update(over)
        return p

    thigh_l, thigh_r = rest["hand_l"], rest["hand_r"]
    # The right wrist turned up before her, the flask hanging off it.
    wrist_up = {"pos": (-0.06, 0.40, 0.26), "pole": (-0.7, -0.6, -0.2), "knuckles": (0.3, 0.35, 0.9), "blade": (-0.3, 0.9, -0.2)}
    # Inside her top at the right breast, under the shoulder strap.
    inside = {"pos": (-0.05, 0.60, 0.12), "pole": (0.8, -0.5, 0.0), "knuckles": (-0.6, 0.4, -0.2), "blade": (0.3, 0.3, 0.9)}
    out = {"pos": (-0.01, 0.52, 0.24), "pole": (0.8, -0.6, -0.1), "knuckles": (-0.5, 0.6, 0.4), "blade": (0.2, 0.4, 0.9)}
    # The letter open before her, a hand at each edge, the thumbs on its face.
    open_l = {"pos": (0.10, 0.47, 0.28), "pole": (0.8, -0.6, -0.2), "knuckles": (-0.15, 0.95, 0.1), "blade": (-0.7, -0.1, -0.7)}
    open_r = {"pos": (-0.10, 0.47, 0.28), "pole": (-0.8, -0.6, -0.2), "knuckles": (0.15, 0.95, 0.1), "blade": (-0.7, 0.1, 0.7)}
    near_l = dict(open_l, pos=(0.025, 0.48, 0.28))
    near_r = dict(open_r, pos=(-0.035, 0.48, 0.28))
    read = dict(spine=(0, 16, 0), neck=(0, 16, 0), head=(0, 22, 0))
    keys = [
        (0, kneel(), "ease"),
        # The right hand turned up; she looks at the cord and the flask.
        (14, kneel(spine=(-4, 14, 0), neck=(-6, 14, 0), head=(-10, 20, 0), hand_r=wrist_up, clav_r=(2, 8)), "auto"),
        (40, kneel(spine=(-4, 15, 0), neck=(-6, 15, 0), head=(-12, 22, -2), hand_r=dict(wrist_up, pos=(-0.06, 0.41, 0.27)), clav_r=(2, 8)), "ease"),
        # Across at the bedroll; the hand going back to her thigh.
        (52, kneel(spine=(6, 12, 0), neck=(10, 8, 0), head=(18, 6, 2), hand_r=thigh_r), "auto"),
        (76, kneel(spine=(7, 12, 0), neck=(11, 8, 0), head=(20, 7, 2), hand_r=thigh_r), "ease"),
        # Back; the left hand inside her top.
        (86, kneel(spine=(0, 13, 0), neck=(0, 12, 0), head=(0, 16, 0), hand_l=dict(inside, pos=(-0.02, 0.56, 0.17)), hand_r=thigh_r,
                   fingers_l=dict(PINCH, curl=0.2)), "auto"),
        (94, kneel(spine=(0, 13, -2), neck=(0, 14, 0), head=(-4, 20, 0), hand_l=inside, hand_r=thigh_r, clav_l=(4, 12), fingers_l=PINCH), "ease"),
        # Out with it, folded; the right hand comes up to meet it.
        (106, kneel(spine=(0, 14, 0), neck=(0, 14, 0), head=(0, 20, 0), hand_l=out, hand_r=dict(near_r, pos=(-0.06, 0.46, 0.26)),
                    clav_l=(2, 8), fingers_l=PINCH, fingers_r=dict(PINCH, curl=0.25)), "auto"),
        (114, kneel(spine=(0, 15, 0), neck=(0, 15, 0), head=(0, 21, 0), hand_l=near_l, hand_r=near_r, fingers_l=PINCH, fingers_r=PINCH), "ease"),
        # Opened before her.
        (124, kneel(**read, hand_l=open_l, hand_r=open_r, fingers_l=PINCH, fingers_r=PINCH), "ease"),
        # She looks: nothing left. A breath, and the hands go down a little.
        (150, kneel(spine=(0, 17, 0), neck=(0, 17, 0), head=(2, 23, 0), hand_l=open_l, hand_r=open_r, fingers_l=PINCH, fingers_r=PINCH), "ease"),
        (166, kneel(spine=(0, 19, 0), neck=(0, 16, 0), head=(2, 22, 2), hand_l=dict(open_l, pos=(0.10, 0.44, 0.27)),
                    hand_r=dict(open_r, pos=(-0.10, 0.44, 0.27)), fingers_l=PINCH, fingers_r=PINCH), "ease"),
        # Folded.
        (178, kneel(spine=(0, 17, 0), neck=(0, 15, 0), head=(0, 20, 0), hand_l=near_l, hand_r=near_r, fingers_l=PINCH, fingers_r=PINCH), "auto"),
        (186, kneel(spine=(0, 16, 0), neck=(0, 14, 0), head=(0, 19, 0), hand_l=out, hand_r=dict(near_r, pos=(-0.07, 0.45, 0.25)),
                    fingers_l=PINCH, fingers_r=dict(PINCH, curl=0.25)), "auto"),
        # Put back inside; the hands to her thighs.
        (196, kneel(spine=(0, 14, -2), neck=(0, 13, 0), head=(-2, 17, 0), hand_l=inside, hand_r=thigh_r, clav_l=(4, 12), fingers_l=PINCH), "auto"),
        (212, kneel(spine=(0, 13, 0), neck=(0, 12, 0), head=(0, 14, 0), hand_l=thigh_l, hand_r=thigh_r), "ease"),
        (230, kneel(spine=(0, 12, 0), neck=(0, 11, 0), head=(0, 12, 0), hand_l=thigh_l, hand_r=thigh_r), "ease"),
    ]
    return build("letter", rig, keys, meta={"layer": "full", "hold": True,
                                             "note": "keyed (C01 shot 6): on her heels, the flask looked at, then the letter taken out, opened, looked at, folded and put back"})


# ------------------------------------------------------- kneel_to_stand_snap --
# C01 shot 10: kneeling back on her heels by the embers, she hears the frost
# break. Her head snaps round to it (her left) at 0.13 s, the eyes first and
# the shoulders after; she comes up off her heels onto her knees as the left
# foot swings through to plant ahead, toward it; she drives up off that foot
# without a hand put down, the back foot brought under, and is standing by
# 0.77 s, low and ready, facing it (55 degrees to the left of where she
# knelt facing), the hands up and open. Then she breathes, hard, on it.

SNAP_TURN = 55.0


def _yaw(v, deg):
    """A point or direction in her space turned about the up axis (+ toward her left)."""
    a = math.radians(deg)
    x, y, z = v
    return (x * math.cos(a) + z * math.sin(a), y, -x * math.sin(a) + z * math.cos(a))


def _hips_at(y, fwd=0.0, side=0.0, turn=0.0):
    """The hips' offset that sets the pelvis y above the ground, fwd ahead
    and side to her left in a frame turned `turn` degrees."""
    x, _, z = _yaw((side, 0.0, fwd), turn)
    return (x, y - 1.072, z)


def _ready(turn, breath=0.0, over=None):
    """Standing set and ready, empty-handed, facing `turn` degrees to her
    left: the left foot a little ahead, the knees soft, the weight forward,
    the hands up and open before her; breathing (breath -1..1)."""
    from clips.actions import arm

    def foot(at, side):
        return {"pos": _yaw(at, turn), "rot": (turn + 6 * side, 0, 0), "pole": _yaw((0.15 * side, 0.0, 1.0), turn)}

    b = breath
    pose = {"hips": {"pos": _hips_at(0.985 + 0.004 * b, 0.12, 0.0, turn), "rot": (turn, 8, 0)}, "spine": (0, 8 - 2.5 * b, 0),
            "neck": (0, -2 + b, 0), "head": (4, -1, 0),
            "foot_l": foot((0.13, 0.0, 0.24), 1), "foot_r": foot((-0.13, 0.0, -0.02), -1),
            # (Not aimed: the hands hang off the forearms as they fall.)
            "hand_l": {**arm((0.09, -0.21, 0.30), (0.7, -0.6, -0.3)), "aim": 0.0},
            "hand_r": {**arm((-0.07, -0.25, 0.26), (-0.7, -0.6, -0.3)), "aim": 0.0},
            "clav_l": (4 + 2.5 * b, 4), "clav_r": (4 + 2.5 * b, 4), "fingers_l": _f(0.45, 0.3), "fingers_r": _f(0.45, 0.3)}
    pose.update(over or {})
    return pose


def kneel_to_stand_snap(rig):
    T = SNAP_TURN
    from clips.actions import arm
    start = _heels(look=0.3, hands=0.0)
    knelt_l, knelt_r = start["foot_l"], start["foot_r"]

    def foot(at, turn, pitch=0.0, roll=0.0, toe=0.0, pole=None, side=1):
        f = {"pos": _yaw(at, turn), "rot": (turn + 6 * side, pitch, roll)}
        if toe:
            f["toe"] = toe
        if pole is not None:
            f["pole"] = _yaw(pole, turn)
        return f

    keys = [
        (0, start, "ease"),
        (3, merge(start, head=(0, 14, 0)), "ease"),
        # The snap: the head round to it, a little up; the eyes are already there.
        (7, merge(start, neck=(14, 6, 0), head=(44, 2, -4), spine=(4, 12, 0), clav_l=(3, 0), clav_r=(3, 0)), "auto"),
        # The shoulders after it; up off her heels, the hips swinging up and
        # forward about the knees (a thigh's length from them), the hands off
        # her thighs.
        (10, merge(start, hips={"pos": _hips_at(0.40, -0.02, 0.0, 10), "rot": (12, 16, 0)}, spine=(12, 10, 0), neck=(14, 2, 0),
                   head=(26, 0, -2), clav_l=(4, 2), clav_r=(4, 2),
                   hand_l=arm((0.12, -0.34, 0.12), (0.7, -0.4, -0.5)), hand_r=arm((-0.12, -0.36, 0.08), (-0.7, -0.4, -0.5)),
                   fingers_l=_f(0.35, 0.2), fingers_r=_f(0.35, 0.2)), "auto"),
        # On her knees, the left knee coming up and through, the chest going
        # forward over where the foot will land.
        (13, {"hips": {"pos": _hips_at(0.52, 0.06, 0.0, 30), "rot": (30, 22, -4)}, "spine": (8, 14, 0), "neck": (8, -2, 0), "head": (12, -4, -2),
              "foot_l": foot((0.13, 0.16, 0.06), 30, pitch=-70, pole=(0.2, 0.3, 1.0)),
              "foot_r": merge(knelt_r, pos=_yaw((-0.11, -0.045, -0.12), 20), rot=(16, 140, 0)),
              "hand_l": arm((0.13, -0.26, 0.22), (0.7, -0.6, -0.3)), "hand_r": arm((-0.14, -0.36, -0.02), (-0.6, -0.4, -0.6)),
              "clav_l": (2, 4), "clav_r": (2, 0), "fingers_l": _f(0.35, 0.2), "fingers_r": _f(0.35, 0.2)}, "auto"),
        # The foot planted ahead, toward it; the weight onto it, the back toes tucked under.
        (16, {"hips": {"pos": _hips_at(0.60, 0.14, 0.02, T), "rot": (T - 6, 26, -4)}, "spine": (6, 14, 0), "neck": (4, -6, 0), "head": (6, -6, 0),
              "foot_l": foot((0.14, 0.0, 0.30), T, pole=(0.25, 0.3, 1.0)),
              "foot_r": foot((-0.12, 0.07, -0.40), T - 10, pitch=50, toe=55, pole=(-0.05, -0.8, 1.0), side=-1),
              "hand_l": arm((0.13, -0.22, 0.26), (0.7, -0.6, -0.3)), "hand_r": arm((-0.13, -0.32, -0.04), (-0.6, -0.4, -0.6)),
              "clav_l": (2, 4), "clav_r": (0, 0), "fingers_l": _f(0.35, 0.2), "fingers_r": _f(0.35, 0.2)}, "auto"),
        # The drive up off it, the back knee off the ground and coming through.
        (20, {"hips": {"pos": _hips_at(0.86, 0.17, 0.03, T), "rot": (T - 2, 14, -3)}, "spine": (2, 8, 0), "neck": (2, -4, 0), "head": (4, -4, 0),
              "foot_l": foot((0.14, 0.0, 0.30), T, pole=(0.25, 0.2, 1.0)),
              "foot_r": foot((-0.13, 0.11, -0.14), T - 6, pitch=-30, toe=10, pole=(-0.05, -0.2, 1.0), side=-1),
              "hand_l": arm((0.11, -0.24, 0.26), (0.7, -0.6, -0.3)), "hand_r": arm((-0.09, -0.29, 0.14), (-0.7, -0.5, -0.4)),
              "clav_l": (2, 2), "clav_r": (2, 2), "fingers_l": _f(0.35, 0.2), "fingers_r": _f(0.35, 0.2)}, "auto"),
        # On her feet, square to it, set, the hands up and open.
        (23, _ready(T, 1.0, over=dict(hips={"pos": _hips_at(1.0, 0.13, 0.0, T), "rot": (T, 7, 0)}, fingers_l=_f(0.4, 0.25), fingers_r=_f(0.4, 0.25))), "auto"),
        # It lands in her knees, and settles.
        (27, _ready(T, 0.6), "ease"),
    ]
    # Held on it, breathing hard and fast, then slowing.
    for i, fr in enumerate(range(36, 106, 9)):
        keys.append((fr, _ready(T, (1.0 if i % 2 == 0 else -0.6) * max(0.3, 1.0 - i * 0.1)), "ease"))
    return contact_build("kneel_to_stand_snap", rig, keys, _knees_clear(rig),
                         meta={"layer": "full", "hold": True, "source": "keyed (tools/anim/clips/story.py)", "licence": "own work",
                               "note": f"keyed (C01 shot 10): from her heels to her feet without her hands, turned {SNAP_TURN:.0f} degrees to her left"})


def _knees_clear(rig):
    """Contacts that keep both knees on or above the ground (held.knee_clear)."""
    def contacts(fr, g, p, pose):
        return {f"foot_{s}": knee_clear(rig, p, fr, s, pose[f"foot_{s}"]) for s in "lr" if f"foot_{s}" in pose}
    return contacts


# ------------------------------------------------------------ take_from_log --
# C01 shot 11 (every calling but the arcanist): standing, facing the log, her
# weapon leaning on it before her, its grip 0.55 m ahead and a little to her
# right at 0.78 m up. A step in with the right foot, down for it, the grip
# taken at 0.6 s (the cinematic swaps the prop for her own weapon here);
# up with it, and round to her left, 110 degrees, onto the threat, low and
# ready, the weapon before her. The calling's own idle takes over from there.

GRIP_AT = (-0.10, 0.78, 0.55)
TAKE_TURN = 110.0


def take_from_log(rig):
    from clips.actions import arm
    T = TAKE_TURN

    def foot(at, turn, side, pitch=0.0, toe=0.0):
        f = {"pos": _yaw(at, turn), "rot": (turn + 8 * side, pitch, 0)}
        if toe:
            f["toe"] = toe
        return f

    stand = {"foot_l": foot((0.14, 0, 0.04), 0, 1), "foot_r": foot((-0.14, 0, -0.02), 0, -1)}
    ready_l = arm((0.10, -0.28, 0.24), (0.7, -0.6, -0.3))
    grip = {"curl": 0.9, "thumb": 0.65, "cascade": 0.08, "spread": 0.0}
    open_ = {"curl": 0.15, "thumb": 0.1, "cascade": 0.1, "spread": 3.0}
    half = {"curl": 0.45, "thumb": 0.3, "cascade": 0.25, "spread": 0.0}
    held = {"frame": "char", "pole": (-0.7, -0.6, -0.3)}
    keys = [
        (0, {**stand, "hips": {"pos": (0, -0.05, 0), "rot": (0, 8, 0)}, "spine": (0, 6, 0), "neck": (0, 4, 0), "head": (0, 10, 0),
             "hand_l": ready_l, "hand_r": arm((-0.08, -0.30, 0.22), (-0.7, -0.6, -0.3)), "clav_l": (3, 4), "clav_r": (3, 4),
             "fingers_l": half, "fingers_r": half}, "ease"),
        # The step in, the eyes on the grip, the hand going for it.
        (8, {"foot_l": foot((0.14, 0, 0.04), 0, 1), "foot_r": foot((-0.15, 0.06, 0.16), 0, -1, pitch=-10),
             "hips": {"pos": (-0.02, -0.08, 0.06), "rot": (-6, 14, 0)}, "spine": (-4, 16, 0), "neck": (0, 8, 0), "head": (-4, 16, 0),
             "hand_l": arm((0.14, -0.30, 0.10), (0.7, -0.5, -0.4)), "hand_r": dict(held, pos=(-0.13, 0.95, 0.42), knuckles=(0.0, -0.4, 1.0), blade=(0.2, 1.0, 0.1)),
             "clav_l": (2, 2), "clav_r": (0, 10), "fingers_l": half, "fingers_r": open_}, "auto"),
        # Down to it; the grip in her hand.
        (16, {"foot_l": foot((0.14, 0, 0.04), 0, 1), "foot_r": foot((-0.15, 0, 0.30), 0, -1),
              "hips": {"pos": (-0.03, -0.16, 0.12), "rot": (-8, 26, 0)}, "spine": (-6, 22, 0), "neck": (0, 4, 0), "head": (-4, 10, 0),
              "hand_l": arm((0.16, -0.32, 0.04), (0.7, -0.5, -0.4)), "hand_r": dict(held, pos=GRIP_AT, knuckles=(0.0, -0.2, 1.0), blade=(0.15, 1.0, 0.1)),
              "clav_l": (0, 2), "clav_r": (-2, 14), "fingers_l": half, "fingers_r": open_}, "auto"),
        (18, {"foot_l": foot((0.14, 0, 0.04), 0, 1), "foot_r": foot((-0.15, 0, 0.30), 0, -1),
              "hips": {"pos": (-0.03, -0.17, 0.12), "rot": (-8, 27, 0)}, "spine": (-6, 22, 0), "neck": (0, 4, 0), "head": (-4, 10, 0),
              "hand_l": arm((0.16, -0.32, 0.04), (0.7, -0.5, -0.4)), "hand_r": dict(held, pos=GRIP_AT, knuckles=(0.0, -0.2, 1.0), blade=(0.15, 1.0, 0.1)),
              "clav_l": (0, 2), "clav_r": (-2, 14), "fingers_l": half, "fingers_r": grip}, "ease"),
        # Up with it, already turning; the left foot steps round.
        (26, {"foot_l": foot((0.22, 0.08, 0.10), T * 0.45, 1, pitch=-8), "foot_r": foot((-0.15, 0, 0.30), 0, -1),
              "hips": {"pos": (0.0, -0.10, 0.14), "rot": (T * 0.35, 12, 0)}, "spine": (T * 0.15, 8, 0), "neck": (T * 0.08, 0, 0), "head": (T * 0.08, 2, 0),
              "hand_l": arm((0.14, -0.26, 0.18), (0.7, -0.6, -0.3)),
              "hand_r": dict(held, pos=_yaw((-0.22, 0.95, 0.30), T * 0.4), knuckles=_yaw((0.0, -0.3, 1.0), T * 0.4), blade=_yaw((0.0, 0.85, 0.5), T * 0.4)),
              "clav_l": (2, 4), "clav_r": (2, 6), "fingers_l": half, "fingers_r": grip}, "auto"),
        # Round onto it, low and set, the weapon before her.
        (36, {"foot_l": foot((0.26, 0, 0.18), T * 0.85, 1), "foot_r": foot((-0.07, 0, 0.18), T * 0.6, -1),
              "hips": {"pos": _hips_at(0.99, 0.18, 0.06, T * 0.75), "rot": (T * 0.8, 10, 0)}, "spine": (T * 0.12, 6, 0), "neck": (T * 0.05, -2, 0), "head": (T * 0.05, 0, 0),
              "hand_l": ready_l, "hand_r": dict(held, pos=_yaw((-0.14, 0.92, 0.42), T * 0.92), knuckles=_yaw((0.1, -0.3, 1.0), T), blade=_yaw((0.1, 0.6, 0.8), T)),
              "clav_l": (3, 4), "clav_r": (3, 6), "fingers_l": half, "fingers_r": grip}, "auto"),
        (44, {"foot_l": foot((0.22, 0, 0.30), T, 1), "foot_r": foot((-0.05, 0, 0.06), T, -1),
              "hips": {"pos": _hips_at(1.0, 0.17, 0.08, T), "rot": (T, 8, 0)}, "spine": (0, 6, 0), "neck": (0, -2, 0), "head": (0, 0, 0),
              "hand_l": ready_l, "hand_r": dict(held, pos=_yaw((-0.12, 0.92, 0.40), T), knuckles=_yaw((0.1, -0.35, 1.0), T), blade=_yaw((0.1, 0.55, 0.85), T)),
              "clav_l": (3, 4), "clav_r": (3, 6), "fingers_l": half, "fingers_r": grip}, "ease"),
        (60, {"foot_l": foot((0.22, 0, 0.30), T, 1), "foot_r": foot((-0.05, 0, 0.06), T, -1),
              "hips": {"pos": _hips_at(1.003, 0.17, 0.08, T), "rot": (T, 8, 0)}, "spine": (0, 5, 0), "neck": (0, -2, 0), "head": (0, 0, 0),
              "hand_l": ready_l, "hand_r": dict(held, pos=_yaw((-0.12, 0.93, 0.40), T), knuckles=_yaw((0.1, -0.35, 1.0), T), blade=_yaw((0.1, 0.55, 0.85), T)),
              "clav_l": (3, 4), "clav_r": (3, 6), "fingers_l": half, "fingers_r": grip}, "ease"),
    ]
    return build("take_from_log", rig, keys, meta={"layer": "full", "hold": True,
                                                    "note": f"keyed (C01 shot 11): the weapon taken off the log (grip in hand at 0.6 s), round {TAKE_TURN:.0f} degrees to her left, ready"})


# --------------------------------------------------------------- cup_hands --
# C01 shot 11, the arcanist: standing (from the snap), she does not reach for
# her staff. Her hands come together before her, cupped, and she looks down
# into them; nothing. She waits (0.6 to 1.4 s). Then the spark (the cinematic's
# light, from 1.4 s): the hands lift a little to it as her palms fill, the
# breath catches, and she holds them so.

def cup_hands(rig):
    T = SNAP_TURN

    def foot(at, side):
        return {"pos": _yaw(at, T), "rot": (T + 6 * side, 0, 0), "pole": _yaw((0.15 * side, 0.0, 1.0), T)}

    def body(y, spine, neck, head, cl=(3, 4), cr=(3, 4)):
        return {"foot_l": foot((0.13, 0.0, 0.24), 1), "foot_r": foot((-0.13, 0.0, -0.02), -1),
                "hips": {"pos": _hips_at(y + 0.05, 0.12, 0.0, T), "rot": (T, 8, 0)}, "spine": spine, "neck": neck, "head": head,
                "clav_l": cl, "clav_r": cr}

    def cup(rise=0.0, part=0.0):
        """The two hands cupped together before her chest, the little fingers'
        edges touching, palms up and tilted to her."""
        # Palms up side by side (her left hand's palm is its +X, her right's
        # its -X), the fingers forward and a little up, the thumbs outward.
        y = 1.15 + rise
        l = {"frame": "char", "pos": _yaw((0.05 + part, y, 0.36), T), "pole": _yaw((0.8, -0.5, -0.3), T),
             "knuckles": _yaw((0.12, 0.25, 1.0), T), "blade": _yaw((1.0, 0.15, -0.1), T)}
        r = {"frame": "char", "pos": _yaw((-0.05 - part, y, 0.36), T), "pole": _yaw((-0.8, -0.5, -0.3), T),
             "knuckles": _yaw((-0.12, 0.25, 1.0), T), "blade": _yaw((-1.0, 0.15, -0.1), T)}
        return {"hand_l": l, "hand_r": r}

    from clips.actions import arm
    ready = {"hand_l": arm((0.10, -0.26, 0.26), (0.7, -0.6, -0.3)), "hand_r": arm((-0.08, -0.30, 0.22), (-0.7, -0.6, -0.3))}
    cupped = {"curl": 0.32, "thumb": 0.25, "cascade": 0.12, "spread": 0.0}
    half = {"curl": 0.45, "thumb": 0.3, "cascade": 0.25, "spread": 0.0}
    keys = [
        (0, {**body(0.935, (0, 8, 0), (0, -2, 0), (4, -1, 0), (4, 4), (4, 4)), **ready, "fingers_l": half, "fingers_r": half}, "ease"),
        # The hands come together, cupped, and she looks into them.
        (12, {**body(0.94, (0, 10, 0), (0, 10, 0), (0, 14, 0)), **cup(-0.03, 0.02), "fingers_l": cupped, "fingers_r": cupped}, "auto"),
        (18, {**body(0.94, (0, 12, 0), (0, 14, 0), (0, 20, 0)), **cup(), "fingers_l": cupped, "fingers_r": cupped}, "ease"),
        # Nothing. She waits, still.
        (42, {**body(0.94, (0, 13, 0), (0, 15, 0), (0, 21, 0)), **cup(-0.005), "fingers_l": cupped, "fingers_r": cupped}, "ease"),
        # The spark, and her palms fill: the hands lift to it, the breath in.
        (52, {**body(0.945, (0, 9, 0), (0, 12, 0), (0, 18, 0), (6, 4), (6, 4)), **cup(0.035), "fingers_l": cupped, "fingers_r": cupped}, "auto"),
        (60, {**body(0.945, (0, 8, 0), (0, 12, 0), (0, 18, 0), (5, 4), (5, 4)), **cup(0.04), "fingers_l": cupped, "fingers_r": cupped}, "ease"),
        (90, {**body(0.94, (0, 10, 0), (0, 13, 0), (0, 19, 0), (3, 4), (3, 4)), **cup(0.035), "fingers_l": cupped, "fingers_r": cupped}, "ease"),
        (105, {**body(0.94, (0, 10, 0), (0, 13, 0), (0, 19, 0), (3, 4), (3, 4)), **cup(0.035), "fingers_l": cupped, "fingers_r": cupped}, "ease"),
    ]
    return build("cup_hands", rig, keys, meta={"layer": "full", "hold": True,
                                                "note": "keyed (C01 shot 11, the arcanist): standing, the hands cupped before her, waiting; they fill (1.4 s) and lift"})


# ---------------------------------------------------------------- gestures --
# Laid over whatever she is doing (Gestures.cs: only each bone's change from
# the first frame is added), so one nod serves her standing, on the log or
# kneeling on her heels. Keyed from a plain stance; only the back, the
# shoulders, the neck and the head move, the arms riding the chest.

def _still(**over):
    pose = {"foot_l": {"pos": (0.12, 0, 0.02), "rot": (8, 0, 0)}, "foot_r": {"pos": (-0.12, 0, -0.02), "rot": (-8, 0, 0)},
            "hand_l": arm((0.06, -0.44, 0.06), (0.6, -0.4, -0.5)), "hand_r": arm((-0.06, -0.44, 0.06), (-0.6, -0.4, -0.5)),
            "fingers_l": RELAXED, "fingers_r": RELAXED}
    pose.update(over)
    return pose


def nod(rig):
    """A nod: the head goes down eight degrees, the chin a little in, and
    stays there for a breath before it comes up; a yes, or an acceptance."""
    keys = [
        (0, _still(), "ease"),
        (7, _still(neck=(0, 3, 0), head=(0, 5, 0)), "ease"),
        (19, _still(neck=(0, 3.5, 0), head=(0, 5.5, 0)), "ease"),
        (31, _still(), "ease"),
    ]
    return build("nod", rig, keys, meta={"layer": "gesture", "note": "the head down 8 degrees, held 0.4 s"})


def exhale(rig):
    """The long breath out: a short lift as the breath comes in, then over
    1.2 s the chest sinks, the shoulders drop and roll forward and the head
    goes down with them. It holds there till the next cue lets it go."""
    keys = [
        (0, _still(), "ease"),
        (9, _still(spine=(0, -2, 0), neck=(0, -1, 0), clav_l=(3, -1), clav_r=(3, -1)), "ease"),
        (45, _still(spine=(0, 4, 0), neck=(0, 2, 0), head=(0, 3, 0), clav_l=(-4, 3), clav_r=(-4, 3)), "ease"),
    ]
    return build("exhale", rig, keys, meta={"layer": "gesture", "hold": True, "note": "the shoulders settle over 1.2 s, held"})


def shiver(rig):
    """The cold goes through her: the shoulders snap up four centimetres
    round the neck, the back hunches, two fast shudders, and they ease back
    down."""
    def up(raise_, roll=0.0):
        return _still(spine=(0, 3, roll), neck=(0, 4, 0), head=(0, -2, 0), clav_l=(raise_, 4), clav_r=(raise_, 4))
    keys = [
        (0, _still(), "linear"),
        (3, up(15), "auto"),
        (5, up(11, 2), "auto"),
        (7, up(16, -2), "auto"),
        (9, up(11, 1.5), "auto"),
        (11, up(15, -1.5), "auto"),
        (20, up(7), "auto"),
        (32, _still(), "ease"),
    ]
    return build("shiver", rig, keys, meta={"layer": "gesture", "note": "the shoulders up 4 cm, a fast double tremor"})


ALL = (("lie_side_wake", lie_side_wake), ("sit_back_heels", sit_back_heels), ("reach_coals", reach_coals),
       ("letter", letter), ("kneel_to_stand_snap", kneel_to_stand_snap), ("take_from_log", take_from_log),
       ("cup_hands", cup_hands), ("nod", nod), ("exhale", exhale), ("shiver", shiver))
# Judged on sheets (still to be judged in the cinematic itself). Anything
# else here is work in progress, built only when named.
JUDGED = {"lie_side_wake", "sit_back_heels", "reach_coals", "nod", "exhale", "shiver"}


def clips(rig, want):
    return [f(rig) for name, f in ALL
            if (want and any(w in name for w in want)) or (not want and name in JUDGED)]
