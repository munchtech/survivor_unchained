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

from clips.actions import arm
from keyed import build, merge


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
        "hips": {"pos": (0.0, -0.86, 0.0), "rot": (0, 10, 90 - 34 * up)},
        "spine": (0, 12, -6 * up), "neck": (0, 18 + 8 * sag, -6), "head": (0, 22 + 10 * sag, -10),
        "foot_r": {"pos": (0.70, -0.04, 0.30), "rot": (0, 0, 90), "pole": (0, 0, 1)},
        "foot_l": {"pos": (0.62, 0.07, 0.42), "rot": (0, 10, 86), "pole": (0, 0, 1)},
        "hand_r": {"pos": (-0.52, 0.05, 0.28), "pole": (-0.3, -1, -0.4), "knuckles": (-0.5, 0, 1)},
        "hand_l": {"pos": (-0.22, 0.05, 0.40), "pole": (0.6, 1, 0), "knuckles": (-0.3, 0, 1)},
        "clav_l": (4, 10), "clav_r": (14, 6),
        "fingers_l": OPEN, "fingers_r": OPEN,
    }


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
    return build("lie_side_wake", rig, keys, meta={"layer": "full", "hold": True,
                                                    "note": "keyed (C01): on her right side, then up onto the elbow"})


def _heels(look=1.0, hands=1.0, breath=0.0):
    """Kneeling back on her heels, facing +Z, the shins flat behind, the
    hands held up before her, palms up, the head bowed to look at them
    (hands 0: resting on her thighs)."""
    lap = 0.30 + 0.02 * hands
    return {
        "hips": {"pos": (0.0, -0.78, -0.06), "rot": (0, 6, 0)},
        "spine": (0, 10 + 8 * look + 2 * breath, 0), "neck": (0, 10 + 8 * look, 0), "head": (0, 10 + 16 * look, 0),
        "foot_l": {"pos": (0.11, -0.05, -0.22), "rot": (4, -168, 0), "pole": (0.1, 0, 1)},
        "foot_r": {"pos": (-0.11, -0.05, -0.22), "rot": (-4, -168, 0), "pole": (-0.1, 0, 1)},
        "hand_l": {"pos": (0.09 + 0.03 * (1 - hands), lap, 0.20 + 0.14 * hands), "pole": (0.7, -0.5, -0.3),
                   "knuckles": (0.1, 0.25 * hands - 0.6 * (1 - hands), 1.0), "blade": (1.0, 0.0, -0.1)},
        "hand_r": {"pos": (-0.09 - 0.03 * (1 - hands), lap, 0.20 + 0.14 * hands), "pole": (-0.7, -0.5, -0.3),
                   "knuckles": (-0.1, 0.25 * hands - 0.6 * (1 - hands), 1.0), "blade": (-1.0, 0.0, -0.1)},
        "clav_l": (0, 6), "clav_r": (0, 6),
        "fingers_l": _f(0.3, 0.2), "fingers_r": _f(0.3, 0.2),
    }


def sit_back_heels(rig):
    end = _elbow(0.96, 1.0)
    keys = [
        (0, end, "ease"),
        # Up onto the right hand, the arm straightening under her.
        (30, merge(end, hips={"pos": (0.0, -0.82, 0.04), "rot": (0, 12, 44)}, spine=(0, 8, -4), neck=(0, 12, -4), head=(0, 14, -6),
                   hand_r={"pos": (-0.40, 0.05, 0.10), "pole": (-0.6, 0, -1), "knuckles": (-0.4, 0, 1)},
                   hand_l={"pos": (-0.10, 0.05, 0.40), "pole": (0.6, 1, 0), "knuckles": (-0.2, 0, 1)}), "auto"),
        # Sat up sideways, the legs folded round to her left.
        (60, {"hips": {"pos": (0.0, -0.86, 0.0), "rot": (-30, 4, 16)}, "spine": (0, 4, -10), "neck": (0, 12, -4), "head": (0, 18, -4),
              "foot_l": {"pos": (0.55, -0.02, -0.10), "rot": (-60, -150, 10), "pole": (0.3, 0.2, 1)},
              "foot_r": {"pos": (0.38, -0.02, -0.30), "rot": (-80, -150, 20), "pole": (0.2, 0, 1)},
              "hand_r": {"pos": (-0.30, 0.05, 0.02), "pole": (-0.6, 0, -1), "knuckles": (-0.4, 0, 1)},
              "hand_l": {"pos": (0.10, 0.30, 0.24), "pole": (0.6, -0.5, -0.4), "knuckles": (0.1, -0.5, 1)},
              "clav_l": (0, 6), "clav_r": (10, 4), "fingers_l": RELAXED, "fingers_r": OPEN}, "auto"),
        # Over onto her knees, a hand down to take the weight.
        (90, {"hips": {"pos": (0.0, -0.58, -0.10), "rot": (0, 24, 0)}, "spine": (0, 20, 0), "neck": (0, 10, 0), "head": (0, 14, 0),
              "foot_l": {"pos": (0.12, -0.05, -0.52), "rot": (4, -150, 0), "pole": (0.1, -0.3, 1)},
              "foot_r": {"pos": (-0.12, -0.05, -0.52), "rot": (-4, -150, 0), "pole": (-0.1, -0.3, 1)},
              "hand_r": {"pos": (-0.16, 0.05, 0.36), "pole": (-0.6, 0, -1), "knuckles": (-0.1, 0, 1)},
              "hand_l": {"pos": (0.14, 0.32, 0.20), "pole": (0.7, -0.5, -0.3), "knuckles": (0.1, -0.6, 1)},
              "clav_l": (0, 6), "clav_r": (8, 8), "fingers_l": RELAXED, "fingers_r": OPEN}, "auto"),
        # Back onto her heels, the hands to her thighs; a breath.
        (120, _heels(look=0.4, hands=0.0, breath=1.0), "ease"),
        # The hands come up before her, and she looks down at them.
        (150, _heels(look=1.0, hands=1.0), "ease"),
        (180, _heels(look=1.0, hands=1.0, breath=0.6), "ease"),
    ]
    return build("sit_back_heels", rig, keys, meta={"layer": "full", "hold": True,
                                                     "note": "keyed (C01): from the elbow to kneeling on her heels, looking at her hands"})


def reach_coals(rig):
    start = _heels(look=1.0, hands=1.0, breath=0.6)
    out = merge(start, spine=(0, 22, 0), neck=(0, 6, 0), head=(0, 4, 0), clav_r=(-2, 14),
                hand_r={"pos": (-0.06, 0.24, 0.66), "pole": (-0.8, -0.2, 0), "knuckles": (0.0, -0.2, 1.0), "blade": (1.0, -0.1, 0.0)},
                hand_l={"pos": (0.12, 0.28, 0.22), "pole": (0.7, -0.5, -0.3), "knuckles": (0.1, -0.6, 1), "blade": (1.0, 0.0, -0.1)},
                fingers_r=_f(0.12, 0.05, 0.2))
    keys = [
        (0, start, "ease"),
        # Out, slow, palm down over the warmth; the left hand falls to her thigh.
        (24, merge(out, hand_r={"pos": (-0.09, 0.30, 0.52)}), "auto"),
        (36, out, "ease"),
        # Held: only the breath, and the fingers spreading a little to the heat.
        (66, merge(out, spine=(0, 23, 0), fingers_r=_f(0.06, 0.0, 0.2, 3.0)), "ease"),
        (96, merge(out, spine=(0, 22, 0), fingers_r=_f(0.04, 0.0, 0.2, 5.0)), "ease"),
        (126, merge(out, spine=(0, 23, 0), fingers_r=_f(0.04, 0.0, 0.2, 5.0)), "ease"),
    ]
    return build("reach_coals", rig, keys, meta={"layer": "full", "hold": True,
                                                  "note": "keyed (C01): kneeling, the right hand held out over the fire, palm down"})


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
       ("nod", nod), ("exhale", exhale), ("shiver", shiver))
# Judged on sheets (still to be judged in the cinematic itself). Anything
# else here is work in progress, built only when named.
JUDGED = {"lie_side_wake", "sit_back_heels", "reach_coals", "nod", "exhale", "shiver"}


def clips(rig, want):
    return [f(rig) for name, f in ALL
            if (want and any(w in name for w in want)) or (not want and name in JUDGED)]
