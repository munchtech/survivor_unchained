"""Everything else she does in a fight: the dash, being struck, falling and
rising, loosing a spell, a bolt or a knife, the war cry, and the daggers'
cuts.

All keyed. The same rule as the swings (clips/sword.py) for anything the
game fires at a moment (a bolt, a spell, a thrown knife, a flinch): the clip
starts at the moment itself, the anticipation is the blend in, and the
weight comes after.
"""
from __future__ import annotations

import numpy as np

from clips.sword import _n
from gait import arc_of
from keyed import STRIKE, build, merge


def stance(crouch=0.06, l=(0.13, 0.10), r=(-0.15, -0.08), weight=0.0):
    return {
        "foot_l": {"pos": (l[0], 0, l[1]), "rot": (10, 0, 0)},
        "foot_r": {"pos": (r[0], 0, r[1]), "rot": (-14, 0, 0)},
        "hips": {"pos": (0.03 * weight, -crouch, 0.0)},
    }


def arm(v, pole, blade=None, knuckles=None, twist=0.45):
    h = {"arc": arc_of(v), "pole": pole, "frame": "chest", "twist": twist}
    if blade is not None:
        h["blade"] = blade
    if knuckles is not None:
        h["knuckles"] = knuckles
    return h


def body(base, hips=(0, 0, 0), spine=(0, 0, 0), neck=(0, 0, 0), head=(0, 0, 0), **over):
    p = dict(base)
    p["hips"] = dict(p.get("hips", {}))
    p["hips"]["rot"] = hips
    p["spine"] = spine
    p["neck"] = neck
    p["head"] = head
    p.update(over)
    return p


# ------------------------------------------------------------------ dash --
def dash(rig):
    """5.5 m in 0.2 s: thrown forward low and long, the arms swept back, the
    back leg stretched out behind, landing on the front foot and rising
    into the run. Reads from above as one long streak."""
    low = {"foot_l": {"pos": (0.10, 0.02, 0.62), "rot": (4, 10, 0), "pole": (0.1, 0.2, 1)},
           "foot_r": {"pos": (-0.10, 0.22, -0.62), "rot": (-4, -60, 0), "toe": 10, "pole": (-0.1, -0.3, 1)},
           "hips": {"pos": (0, -0.30, 0.10)}}
    swept = {"hand_l": arm((0.08, -0.16, -0.34), (0.5, 0.6, 0.2)), "hand_r": arm((-0.08, -0.16, -0.34), (-0.5, 0.6, 0.2)),
             "fingers_l": "open", "fingers_r": "grip"}
    keys = [
        (0, body({**low, **swept}, hips=(0, 34, 0), spine=(0, 14, 0), neck=(0, -18, 0), head=(0, -20, 0)), "ease"),
        (5, body({**low, **swept, "foot_r": {"pos": (-0.10, 0.30, -0.66), "rot": (-4, -70, 0), "toe": 10}},
                 hips=(0, 36, 0), spine=(0, 14, 0), neck=(0, -18, 0), head=(0, -22, 0)), "ease"),
        # Down on the front foot, the back one coming through.
        (8, body({"foot_l": {"pos": (0.08, 0, 0.30), "rot": (4, 0, 0)},
                  "foot_r": {"pos": (-0.08, 0.30, -0.25), "rot": (-4, -40, 0), "toe": 15},
                  "hips": {"pos": (0, -0.22, 0.04)},
                  "hand_l": arm((0.02, -0.26, 0.10), (0.5, -0.3, -0.6)), "hand_r": arm((-0.02, -0.30, -0.10), (-0.5, -0.3, -0.6)),
                  "fingers_l": "relaxed", "fingers_r": "grip"},
                 hips=(0, 22, 0), spine=(0, 10, 0), neck=(0, -12, 0), head=(0, -12, 0)), "auto"),
        (14, body({"foot_l": {"pos": (0.08, 0.05, 0.05), "rot": (4, 0, 0)},
                   "foot_r": {"pos": (-0.08, 0.0, 0.25), "rot": (-4, 0, 0)},
                   "hips": {"pos": (0, -0.10, 0.04)},
                   "hand_l": arm((0.0, -0.20, 0.22), (0.5, -0.3, -0.8)), "hand_r": arm((0.0, -0.30, -0.18), (-0.5, -0.3, -0.8)),
                   "fingers_l": "relaxed", "fingers_r": "grip"},
                  hips=(0, 14, 0), spine=(0, 8, 0), neck=(0, -6, 0), head=(0, -8, 0)), "ease"),
    ]
    return build("dash", rig, keys, meta={"layer": "full"})


# ------------------------------------------------------------------- hit --
def hit(rig):
    """Struck from the front: the head snaps, the chest twists away and
    caves, the shoulders come up, the arms jerk; big enough to read at 31 m;
    then she gathers herself."""
    base = stance(0.08)
    calm = body(base, hand_l=arm((-0.02, -0.30, 0.20), (0.6, -0.4, -0.5)), hand_r=arm((0.02, -0.30, 0.20), (-0.6, -0.4, -0.5)),
                fingers_l="relaxed", fingers_r="grip")
    keys = [
        (0, body(base, hips=(10, -6, 0), spine=(18, -16, -6), neck=(8, -10, 0), head=(14, -18, -10),
                 clav_l=(14, -6), clav_r=(14, -6),
                 hand_l=arm((0.12, -0.18, 0.12), (0.8, -0.2, -0.3)), hand_r=arm((-0.14, -0.14, 0.10), (-0.8, -0.2, -0.3)),
                 fingers_l="spread", fingers_r="grip"), "ease"),
        (3, body(base, hips=(12, -8, 0), spine=(22, -20, -8), neck=(10, -12, 0), head=(16, -22, -12),
                 clav_l=(16, -8), clav_r=(16, -8),
                 hand_l=arm((0.14, -0.14, 0.10), (0.8, -0.2, -0.3)), hand_r=arm((-0.16, -0.10, 0.08), (-0.8, -0.2, -0.3)),
                 fingers_l="spread", fingers_r="grip"), "ease"),
        (10, body(base, hips=(4, 2, 0), spine=(6, 4, -2), head=(4, 2, -3),
                  hand_l=arm((0.0, -0.26, 0.18), (0.6, -0.4, -0.5)), hand_r=arm((0.0, -0.26, 0.18), (-0.6, -0.4, -0.5)),
                  fingers_l="relaxed", fingers_r="grip"), "auto"),
        (18, calm, "ease"),
    ]
    return build("hit", rig, keys, meta={"layer": "upper"})


# ----------------------------------------------------------- death, rise --
def _down_pose():
    """Face down where she fell, one arm under her, one flung out, a knee
    drawn up: the end of the fall, and the start of rising."""
    return {
        "hips": {"pos": (0.02, -0.90, -0.22), "rot": (6, 90, 6)},
        "spine": (4, 2, 4), "neck": (20, -22, 0), "head": (42, -12, 0),
        "foot_l": {"pos": (0.24, 0.0, -1.12), "rot": (10, -88, 0), "pole": (0.6, -1, 0.2)},
        "foot_r": {"pos": (-0.12, 0.04, -1.02), "rot": (-6, -80, 0), "pole": (-0.4, -1, 0.3)},
        "hand_l": {"pos": (0.56, 0.04, 0.16), "pole": (1, 0.3, -0.3), "knuckles": (0.6, 0, 0.8)},
        "hand_r": {"pos": (-0.14, 0.05, 0.20), "pole": (-1, 0.5, 0), "knuckles": (0.2, 0, 1)},
        "fingers_l": "open", "fingers_r": "relaxed",
    }


def death(rig):
    """A blow that takes her: rocked back, the knees go, she drops to them,
    sways, and falls forward onto her face, an arm out. Held there."""
    base = stance(0.06)
    keys = [
        (0, body(base, hips=(8, -10, 0), spine=(10, -18, -4), neck=(0, -10, 0), head=(8, -20, -6),
                 clav_l=(10, 0), clav_r=(10, 0),
                 hand_l=arm((0.10, -0.16, 0.10), (0.8, -0.2, -0.3)), hand_r=arm((-0.10, -0.16, 0.10), (-0.8, -0.2, -0.3)),
                 fingers_l="spread", fingers_r="relaxed"), "ease"),
        (8, body({"foot_l": {"pos": (0.13, 0, 0.06), "rot": (10, 0, 0)}, "foot_r": {"pos": (-0.15, 0, -0.14), "rot": (-14, 0, 0)},
                  "hips": {"pos": (0, -0.20, -0.06)}},
                 hips=(4, -4, 4), spine=(4, 10, 6), neck=(0, 6, 0), head=(4, 10, 8),
                 hand_l=arm((0.04, -0.36, 0.08), (0.6, -0.4, -0.5)), hand_r=arm((-0.04, -0.36, 0.06), (-0.6, -0.4, -0.5)),
                 fingers_l="relaxed", fingers_r="relaxed"), "auto"),
        # On her knees.
        (15, body({"foot_l": {"pos": (0.15, 0.02, -0.42), "rot": (8, -70, 0), "pole": (0.2, -1, 0.5)},
                   "foot_r": {"pos": (-0.15, 0.02, -0.44), "rot": (-8, -70, 0), "pole": (-0.2, -1, 0.5)},
                   "hips": {"pos": (0, -0.52, -0.08)}},
                  hips=(4, 10, 6), spine=(6, 22, 8), neck=(0, 12, 0), head=(6, 14, 10),
                  hand_l=arm((0.0, -0.42, 0.04), (0.6, -0.4, -0.5)), hand_r=arm((0.0, -0.42, 0.02), (-0.6, -0.4, -0.5)),
                  fingers_l="relaxed", fingers_r="relaxed"), "auto"),
        (21, body({"foot_l": {"pos": (0.16, 0.02, -0.55), "rot": (8, -75, 0), "pole": (0.3, -1, 0.3)},
                   "foot_r": {"pos": (-0.15, 0.02, -0.58), "rot": (-8, -78, 0), "pole": (-0.2, -1, 0.3)},
                   "hips": {"pos": (0, -0.64, -0.14)}},
                  hips=(6, 44, 6), spine=(6, 26, 8), neck=(0, 10, 0), head=(14, 6, 10),
                  hand_l=arm((0.10, -0.20, 0.36), (0.8, 0.2, -0.3)), hand_r=arm((-0.06, -0.22, 0.30), (-0.8, 0.2, -0.3)),
                  fingers_l="open", fingers_r="open"), "auto"),
        (27, _down_pose(), "ease"),
        (34, merge(_down_pose(), spine=(4, 2, 4)), "ease"),
    ]
    return build("death", rig, keys, meta={"layer": "full", "hold": True})


def _back_pose(settle=0.0):
    """On her back where she fell, a knee fallen out, an arm flung up past
    her head, the other limp at her side, the face turned away."""
    return {
        "hips": {"pos": (0.0, -0.95, -0.62), "rot": (-6, -88, -4)},
        "spine": (4, 4 - 2 * settle, -6), "neck": (10, 6, 0), "head": (34 + 4 * settle, -8, 10),
        "foot_l": {"pos": (0.04, 0.07, -0.02), "rot": (60, -30, 50), "pole": (1, 0.15, 0.3)},
        "foot_r": {"pos": (-0.17, 0.07, 0.31), "rot": (-24, -55, -10), "pole": (-0.4, 1, 0)},
        "hand_l": {"pos": (0.52, 0.05, -1.30), "pole": (1, 0.4, 0), "knuckles": (0.4, 0, -1)},
        "hand_r": {"pos": (-0.40, 0.04, -0.62), "pole": (-1, 0.4, 0), "knuckles": (-0.2, 0, 1)},
        "fingers_l": "open", "fingers_r": "relaxed",
    }


def death_back(rig):
    """A blow from in front that takes her: the chest caved, the head
    snapped back, a stagger back on the right foot, the knees go, she sits
    down hard and the back hits, the legs bounced up by it; then limp."""
    keys = [
        # The blow: chest punched in, the head thrown back, arms up and out
        # with it.
        (0, body({"foot_l": {"pos": (0.13, 0, 0.12), "rot": (10, 0, 0)}, "foot_r": {"pos": (-0.15, 0, -0.06), "rot": (-14, 0, 0)},
                  "hips": {"pos": (0, -0.08, 0.06)}},
                 hips=(0, -10, 0), spine=(0, -16, 0), neck=(0, -8, 0), head=(0, -18, 0), clav_l=(12, 10), clav_r=(12, 10),
                 hand_l=arm((0.16, -0.34, 0.24), (0.9, -0.6, -0.2)), hand_r=arm((-0.16, -0.36, 0.22), (-0.9, -0.6, -0.2)),
                 fingers_l="spread", fingers_r="relaxed"), "fast"),
        # The stagger back: the right foot caught behind her, the body
        # still going.
        (5, body({"foot_l": {"pos": (0.14, 0.04, 0.16), "rot": (10, -10, 0), "toe": 0},
                  "foot_r": {"pos": (-0.16, 0, -0.42), "rot": (-16, 0, 0)},
                  "hips": {"pos": (0, -0.20, -0.20)}},
                 hips=(0, -16, 4), spine=(-4, -14, 4), neck=(0, -6, 0), head=(0, -16, 0), clav_l=(16, 4), clav_r=(16, 4),
                 hand_l=arm((0.40, -0.22, 0.18), (0.9, -0.2, -0.3)), hand_r=arm((-0.40, -0.26, 0.16), (-0.9, -0.2, -0.3)),
                 fingers_l="spread", fingers_r="open"), "auto"),
        # The knees go: down over the back foot.
        (10, body({"foot_l": {"pos": (0.16, 0.0, 0.10), "rot": (14, 0, 0)},
                   "foot_r": {"pos": (-0.17, 0, -0.40), "rot": (-16, 0, 0), "pole": (-0.4, 0.2, 1)},
                   "hips": {"pos": (0, -0.55, -0.42)}},
                  hips=(0, -24, 6), spine=(-4, -12, 6), neck=(0, 4, 0), head=(0, 6, 0), clav_l=(10, 0), clav_r=(10, 0),
                  hand_l=arm((0.46, -0.36, -0.04), (0.9, 0.2, -0.4)), hand_r=arm((-0.46, -0.38, -0.06), (-0.9, 0.2, -0.4)),
                  fingers_l="open", fingers_r="open"), "auto"),
        # Sat down hard, the feet thrown out in front.
        (13, body({"foot_l": {"pos": (0.20, 0.02, 0.12), "rot": (16, -30, 0), "pole": (0.3, 1, 0.3)},
                   "foot_r": {"pos": (-0.18, 0.03, 0.02), "rot": (-16, -30, 0), "pole": (-0.3, 1, 0.3)},
                   "hips": {"pos": (0, -0.92, -0.58)}},
                  hips=(0, -36, 4), spine=(-4, -4, 4), neck=(0, 10, 0), head=(0, 16, 0), clav_l=(14, 0), clav_r=(14, 0),
                  hand_l=arm((0.42, -0.06, 0.10), (0.9, 0.3, -0.4)), hand_r=arm((-0.42, -0.08, 0.09), (-0.9, 0.3, -0.4)),
                  fingers_l="open", fingers_r="open"), "linear"),
        # The back hits: the head whipped back, the legs bounced up.
        (17, {"hips": {"pos": (0.0, -0.97, -0.64), "rot": (0, -84, 0)},
              "spine": (0, -2, 0), "neck": (0, -6, 0), "head": (6, -14, 4),
              "foot_l": {"pos": (0.22, 0.30, 0.34), "rot": (20, -70, 10), "pole": (0.4, 1, 0.3)},
              "foot_r": {"pos": (-0.18, 0.40, 0.38), "rot": (-16, -70, -10), "pole": (-0.3, 1, 0.3)},
              "hand_l": {"pos": (0.62, 0.10, -1.10), "pole": (1, 0.4, 0), "knuckles": (0.4, 0, -1)},
              "hand_r": {"pos": (-0.66, 0.10, -0.90), "pole": (-1, 0.4, 0), "knuckles": (-0.4, 0, -1)},
              "fingers_l": "spread", "fingers_r": "spread"}, "auto"),
        # Bounced: the head comes up and turns, the legs fall.
        (21, merge(_back_pose(), hips={"pos": (0.0, -0.93, -0.63), "rot": (-4, -84, -2)}, head=(24, 6, 8),
                   foot_l={"pos": (0.10, 0.14, 0.04), "rot": (45, -40, 35), "pole": (1, 0.5, 0.3)},
                   foot_r={"pos": (-0.17, 0.14, 0.32), "rot": (-20, -60, -10), "pole": (-0.3, 1, 0)}), "auto"),
        (27, _back_pose(), "ease"),
        (40, _back_pose(1.0), "ease"),
    ]
    return build("death_back", rig, keys, meta={"layer": "full", "hold": True,
                                                 "note": "keyed: struck from in front, onto her back, held"})


def get_up(rig):
    """From where the fall left her: a push up on the hands, a knee under
    her, a breath on one knee, and up, shaking it off."""
    keys = [
        (0, _down_pose(), "ease"),
        (8, {"hips": {"pos": (0.0, -0.70, -0.30), "rot": (2, 60, 2)}, "spine": (0, 10, 0), "neck": (0, -10, 0),
             "head": (0, -20, 0),
             "foot_l": {"pos": (0.16, 0.02, -0.80), "rot": (6, -80, 0), "pole": (0.3, -1, 0.2)},
             "foot_r": {"pos": (-0.14, 0.02, -0.82), "rot": (-6, -80, 0), "pole": (-0.2, -1, 0.2)},
             "hand_l": {"pos": (0.24, 0.04, 0.22), "pole": (1, 0, -0.5), "knuckles": (0, 0, 1)},
             "hand_r": {"pos": (-0.24, 0.04, 0.20), "pole": (-1, 0, -0.5), "knuckles": (0, 0, 1)},
             "fingers_l": "open", "fingers_r": "open"}, "auto"),
        # One knee up.
        (16, body({"foot_l": {"pos": (0.15, 0.0, 0.22), "rot": (8, 0, 0), "pole": (0.2, 0, 1)},
                   "foot_r": {"pos": (-0.15, 0.02, -0.50), "rot": (-8, -70, 0), "pole": (-0.2, -1, 0.4)},
                   "hips": {"pos": (0, -0.55, -0.12)}},
                  hips=(0, 24, 0), spine=(0, 16, 0), neck=(0, -6, 0), head=(0, -6, 0),
                  hand_l={"pos": (0.16, 0.50, 0.24), "pole": (0.8, 0, -0.5)}, hand_r=arm((-0.02, -0.36, 0.10), (-0.6, -0.4, -0.5)),
                  fingers_l="relaxed", fingers_r="relaxed"), "auto"),
        (24, body({"foot_l": {"pos": (0.15, 0.0, 0.22), "rot": (8, 0, 0), "pole": (0.2, 0, 1)},
                   "foot_r": {"pos": (-0.15, 0.02, -0.40), "rot": (-8, -30, 0), "toe": 30},
                   "hips": {"pos": (0, -0.38, -0.08)}},
                  hips=(0, 18, 0), spine=(0, 10, 0), head=(0, -4, 0),
                  hand_l={"pos": (0.16, 0.52, 0.24), "pole": (0.8, 0, -0.5)}, hand_r=arm((-0.02, -0.34, 0.12), (-0.6, -0.4, -0.5)),
                  fingers_l="relaxed", fingers_r="relaxed"), "auto"),
        # Up, the weight settling, a roll of the shoulders.
        (34, body(stance(0.06), hips=(0, 4, 0), spine=(0, 2, 0), clav_l=(6, 0), clav_r=(6, 0),
                  hand_l=arm((-0.02, -0.34, 0.12), (0.6, -0.4, -0.5)), hand_r=arm((0.02, -0.34, 0.12), (-0.6, -0.4, -0.5)),
                  fingers_l="relaxed", fingers_r="relaxed"), "auto"),
        (44, body(stance(0.05), hand_l=arm((-0.02, -0.38, 0.06), (0.6, -0.4, -0.5)),
                  hand_r=arm((0.02, -0.38, 0.06), (-0.6, -0.4, -0.5)), fingers_l="relaxed", fingers_r="relaxed"), "ease"),
    ]
    return build("get_up", rig, keys, meta={"layer": "full"})


# ------------------------------------------------------------ loosing --
def cast_bolt(rig):
    """A spell thrown from the open hand: the left hand already drawn back
    in a claw by her ribs, her left shoulder back; it drives out spread at
    the foe as the shoulder comes through, the staff hand pulled back the
    other way; held a beat; back."""
    staff = arm((-0.16, -0.30, 0.10), (-0.8, -0.3, -0.6), blade=_n(-0.12, 1.0, 0.18), twist=0.5)
    keys = [
        (0, body(stance(0.07), hips=(8, 4, 0), spine=(16, 4, 0), head=(-20, -2, 0),
                 hand_l=arm((-0.02, -0.20, -0.04), (0.9, -0.3, -0.5), knuckles=_n(-0.2, 0.6, 0.6)),
                 hand_r=staff, fingers_l="claw", fingers_r="grip"), "fast"),
        (3, body(stance(0.08, weight=0.4), hips=(-10, 6, 0), spine=(-18, 6, 0), head=(24, -4, 0),
                 hand_l=arm((-0.14, -0.04, 0.52), (0.8, -0.5, -0.2), knuckles=_n(0.0, 0.9, 0.3)),
                 hand_r=arm((-0.14, -0.32, -0.04), (-0.8, -0.3, -0.4), blade=_n(-0.2, 1.0, 0.0), twist=0.5),
                 fingers_l="spread", fingers_r="grip"), "ease"),
        (8, body(stance(0.08, weight=0.4), hips=(-11, 6, 0), spine=(-20, 6, 0), head=(26, -4, 0),
                 hand_l=arm((-0.14, -0.05, 0.50), (0.8, -0.5, -0.2), knuckles=_n(0.0, 0.85, 0.35)),
                 hand_r=arm((-0.14, -0.32, -0.04), (-0.8, -0.3, -0.4), blade=_n(-0.2, 1.0, 0.0), twist=0.5),
                 fingers_l="spread", fingers_r="grip"), "auto"),
        (20, body(stance(0.06), hand_l=arm((-0.02, -0.40, -0.05), (1.0, 0.0, -0.7), knuckles=_n(0.2, -0.6, 0.6)),
                  hand_r=staff, fingers_l="relaxed", fingers_r="grip"), "ease"),
    ]
    return build("cast_bolt", rig, keys, lead=STRIKE, meta={"layer": "upper", "contact": 0.0})


def cast_raise(rig):
    """The arcanist's great working: the staff swept up overhead in both
    hands and brought down, its foot striking the ground before her."""
    keys = [
        (0, body(stance(0.06), spine=(0, -6, 0), head=(0, -14, 0),
                 hand_r=arm((-0.04, 0.30, 0.12), (-0.6, 0.2, -0.6), blade=_n(0.0, 1.0, -0.1)),
                 hand_l=arm((0.06, 0.34, 0.14), (0.6, 0.2, -0.6)), fingers_l="spread", fingers_r="grip"), "ease"),
        (6, body(stance(0.06), spine=(0, -10, 0), head=(0, -20, 0),
                 hand_r=arm((-0.02, 0.40, 0.10), (-0.6, 0.2, -0.6), blade=_n(0.0, 1.0, -0.15)),
                 hand_l=arm((0.10, 0.44, 0.08), (0.6, 0.2, -0.6)), fingers_l="spread", fingers_r="grip"), "fast"),
        (10, body(stance(0.14, weight=0.3), hips=(0, 14, 0), spine=(0, 18, 0), head=(0, -10, 0),
                  hand_r=arm((0.02, -0.40, 0.34), (-0.8, -0.3, -0.3), blade=_n(0.0, 0.88, -0.48)),
                  hand_l=arm((0.10, -0.18, 0.30), (0.8, -0.3, -0.3)), fingers_l="grip", fingers_r="grip"), "ease"),
        (16, body(stance(0.14, weight=0.3), hips=(0, 15, 0), spine=(0, 19, 0), head=(0, -10, 0),
                  hand_r=arm((0.02, -0.42, 0.33), (-0.8, -0.3, -0.3), blade=_n(0.0, 0.88, -0.48)),
                  hand_l=arm((0.10, -0.20, 0.29), (0.8, -0.3, -0.3)), fingers_l="grip", fingers_r="grip"), "auto"),
        (28, body(stance(0.06), hand_l=arm((-0.02, -0.40, -0.05), (1.0, 0.0, -0.7), knuckles=_n(0.2, -0.6, 0.6)),
                  hand_r=arm((-0.16, -0.28, 0.12), (-0.8, -0.3, -0.6), blade=_n(-0.12, 1.0, 0.18)),
                  fingers_l="relaxed", fingers_r="grip"), "ease"),
    ]
    return build("cast_raise", rig, keys, meta={"layer": "upper", "contact": 10 / 30})


def cast_flick(rig):
    """The wand's spell: the whole arm whipped out from over the shoulder at
    the foe, ending pointed straight at it, the free hand flung open behind
    for balance."""
    keys = [
        (0, body(stance(0.07, weight=-0.3), hips=(-10, -2, 0), spine=(-18, -4, 0), head=(22, 0, 0),
                 hand_r=arm((-0.08, 0.14, -0.06), (-0.7, 0.2, -0.3), blade=_n(-0.1, 0.6, -0.8)),
                 hand_l=arm((0.06, -0.20, 0.30), (0.8, -0.4, -0.3)), fingers_r="grip", fingers_l="open"), "fast"),
        (3, body(stance(0.09, weight=0.4), hips=(6, 6, 0), spine=(10, 8, 0), head=(-12, -4, 0),
                 hand_r=arm((0.02, -0.04, 0.52), (-0.8, -0.4, -0.2), blade=_n(0.0, -0.05, 1.0)),
                 hand_l=arm((0.10, -0.22, -0.22), (0.8, -0.2, -0.3)), fingers_r="grip", fingers_l="spread"), "ease"),
        (8, body(stance(0.09, weight=0.4), hips=(6, 6, 0), spine=(11, 8, 0), head=(-13, -4, 0),
                 hand_r=arm((0.02, -0.06, 0.51), (-0.8, -0.4, -0.2), blade=_n(0.0, -0.1, 1.0)),
                 hand_l=arm((0.10, -0.23, -0.22), (0.8, -0.2, -0.3)), fingers_r="grip", fingers_l="spread"), "auto"),
        (18, body(stance(0.06), hand_r=arm((0.0, -0.36, 0.14), (-0.6, -0.4, -0.5), blade=_n(-0.1, 0.5, 0.85)),
                  hand_l=arm((0.0, -0.38, 0.08), (0.6, -0.4, -0.5)), fingers_r="grip", fingers_l="relaxed"), "ease"),
    ]
    return build("cast_flick", rig, keys, lead=STRIKE, meta={"layer": "upper", "contact": 0.0})


def crossbow_shoot(rig):
    """The crossbow up at the eye and loosed: the kick throws the fists up
    and the shoulder back, she rides it and lowers."""
    aim_r = arm((0.06, -0.02, 0.40), (-0.8, -0.5, -0.2), knuckles=_n(0.08, 0.02, 1.0))
    aim_l = arm((-0.10, -0.08, 0.40), (0.8, -0.5, -0.2), knuckles=_n(0.1, -0.2, 1.0))
    keys = [
        (0, body(stance(0.08), spine=(-8, 4, 0), head=(10, 4, -4), hand_r=aim_r, hand_l=aim_l,
                 fingers_r="grip", fingers_l="relaxed"), "fast"),
        (2, body(stance(0.08, weight=-0.3), spine=(-10, -4, 0), head=(10, -2, -4), clav_r=(6, -6),
                 hand_r=arm((0.06, 0.04, 0.34), (-0.8, -0.4, -0.2), knuckles=_n(0.08, 0.3, 0.95)),
                 hand_l=arm((-0.10, 0.0, 0.34), (0.8, -0.4, -0.2), knuckles=_n(0.1, 0.1, 1.0)),
                 fingers_r="grip", fingers_l="relaxed"), "ease"),
        (8, body(stance(0.08), spine=(-8, 2, 0), head=(10, 2, -4), hand_r=aim_r, hand_l=aim_l,
                 fingers_r="grip", fingers_l="relaxed"), "auto"),
        (18, body(stance(0.08), hand_r=arm((0.12, -0.38, 0.20), (-0.7, -0.4, -0.5), knuckles=_n(0.5, -0.15, 0.85)),
                  hand_l=arm((-0.16, -0.42, 0.30), (0.7, -0.4, -0.5), knuckles=_n(0.2, -0.2, 0.95)),
                  fingers_r="grip", fingers_l="relaxed"), "ease"),
    ]
    return build("crossbow_shoot", rig, keys, meta={"layer": "upper", "contact": 0.0})


def throw(rig):
    """Overhand: the hand already back behind her head, whipped through,
    released high and in front, the arm following through across her."""
    keys = [
        (0, body(stance(0.07, weight=-0.4), hips=(-16, -2, 0), spine=(-26, -8, 0), head=(30, -2, 0),
                 hand_r=arm((-0.14, 0.20, -0.16), (-0.6, -0.3, 0.6), blade=_n(-0.2, 0.6, -0.8)),
                 hand_l=arm((0.06, -0.08, 0.36), (0.8, -0.5, -0.2)), fingers_r="grip", fingers_l="open"), "fast"),
        (2.5, body(stance(0.08), hips=(-2, 6, 0), spine=(0, 8, 0), head=(4, -4, 0),
                   hand_r=arm((-0.04, 0.10, 0.44), (-0.8, -0.3, -0.2), blade=_n(0.0, 0.3, 1.0)),
                   hand_l=arm((0.10, -0.20, 0.10), (0.8, -0.3, -0.3)), fingers_r="open", fingers_l="relaxed"), "linear"),
        (6, body(stance(0.10, weight=0.5), hips=(12, 10, 0), spine=(22, 14, 0), head=(-26, -6, 0),
                 hand_r=arm((0.22, -0.34, 0.30), (-0.8, -0.2, 0.0)),
                 hand_l=arm((0.08, -0.26, -0.18), (0.8, -0.2, -0.3)), fingers_r="relaxed", fingers_l="relaxed"), "ease"),
        (9, body(stance(0.10, weight=0.5), hips=(13, 10, 0), spine=(24, 14, 0), head=(-28, -6, 0),
                 hand_r=arm((0.24, -0.36, 0.26), (-0.8, -0.2, 0.0)),
                 hand_l=arm((0.08, -0.27, -0.18), (0.8, -0.2, -0.3)), fingers_r="relaxed", fingers_l="relaxed"), "auto"),
        (20, body(stance(0.07), hand_r=arm((0.0, -0.34, 0.16), (-0.6, -0.4, -0.5)),
                  hand_l=arm((0.0, -0.36, 0.14), (0.6, -0.4, -0.5)), fingers_r="grip", fingers_l="relaxed"), "ease"),
    ]
    return build("throw", rig, keys, lead=STRIKE, meta={"layer": "upper", "contact": 2.5 / 30})


def warcry(rig):
    """Gathered in, then thrown open: arms flung wide and down, chest out,
    chin forward, a roar held; then the shoulders roll and settle."""
    keys = [
        (0, body(stance(0.10), spine=(0, 16, 0), head=(0, 10, 0), clav_l=(8, 10), clav_r=(8, 10),
                 hand_l=arm((-0.12, -0.24, 0.14), (0.7, -0.5, -0.4)), hand_r=arm((0.12, -0.24, 0.14), (-0.7, -0.5, -0.4)),
                 fingers_l="fist", fingers_r="fist"), "fast"),
        (4, body(stance(0.12), spine=(0, -14, 0), neck=(0, -6, 0), head=(0, -16, 0), clav_l=(-4, -12), clav_r=(-4, -12),
                 hand_l=arm((0.40, -0.24, 0.06), (0.4, -0.8, -0.3)), hand_r=arm((-0.40, -0.24, 0.06), (-0.4, -0.8, -0.3)),
                 fingers_l="claw", fingers_r="claw"), "ease"),
        (14, body(stance(0.12), spine=(0, -16, 0), neck=(0, -6, 0), head=(0, -18, 0), clav_l=(-4, -14), clav_r=(-4, -14),
                  hand_l=arm((0.40, -0.26, 0.04), (0.4, -0.8, -0.3)), hand_r=arm((-0.40, -0.26, 0.04), (-0.4, -0.8, -0.3)),
                  fingers_l="claw", fingers_r="claw"), "auto"),
        (24, body(stance(0.07), clav_l=(4, 0), clav_r=(4, 0), hand_l=arm((-0.02, -0.36, 0.10), (0.6, -0.4, -0.5)),
                  hand_r=arm((0.02, -0.36, 0.10), (-0.6, -0.4, -0.5)), fingers_l="fist", fingers_r="fist"), "ease"),
    ]
    return build("warcry", rig, keys, meta={"layer": "upper"})


# ------------------------------------------------------------- daggers --
def _dag(hy, sy, r, rb, rp, l, lb, lp, weight=0.0, pitch=10):
    p = stance(0.10, weight=weight)
    p["hips"]["rot"] = (hy, 6, 0)
    p["spine"] = (sy, pitch, 0)
    p["head"] = (-(hy + sy) * 0.6, -6, 0)
    p["hand_r"] = arm(r, rp, blade=rb, twist=0.5)
    p["hand_l"] = arm(l, lp, blade=lb, twist=0.5)
    p["fingers_r"] = "grip"
    p["fingers_l"] = "grip"
    return p


DAG_GUARD = _dag(0, 0, (0.0, -0.26, 0.26), _n(-0.2, 0.6, 0.75), (-0.7, -0.5, -0.4),
                 (0.0, -0.28, 0.22), _n(0.2, 0.6, 0.75), (0.7, -0.5, -0.4))


def daggers_back(rig):
    """A quick backhand rip with the right, her left to her right."""
    keys = [
        (0, _dag(14, 24, (0.26, -0.04, 0.16), _n(0.6, 0.5, -0.5), (0.2, -0.4, -1.0),
                 (0.0, -0.30, 0.16), _n(0.2, 0.6, 0.7), (0.7, -0.5, -0.4), weight=0.3), "fast"),
        (2, _dag(2, 2, (-0.04, -0.12, 0.44), _n(-0.2, 0.0, 1.0), (-0.3, -0.8, -0.4),
                 (0.04, -0.28, 0.18), _n(0.2, 0.6, 0.7), (0.7, -0.5, -0.4)), "linear"),
        (4, _dag(-12, -24, (-0.32, -0.16, 0.30), _n(-0.95, -0.1, 0.2), (-0.2, -1.0, 0.2),
                 (0.10, -0.22, 0.30), _n(0.3, 0.6, 0.7), (0.7, -0.5, -0.3), weight=-0.4), "ease"),
        (6, _dag(-13, -27, (-0.33, -0.18, 0.27), _n(-0.9, -0.2, -0.2), (-0.1, -1.0, 0.3),
                 (0.10, -0.22, 0.30), _n(0.3, 0.6, 0.7), (0.7, -0.5, -0.3), weight=-0.4), "auto"),
        (16, DAG_GUARD, "ease"),
    ]
    return build("daggers_back", rig, keys, lead=STRIKE, meta={"layer": "upper", "contact": 2 / 30, "weapon": "daggers"})


def daggers_fore(rig):
    """The left blade's answer, her right to her left... as the game's arcs
    go: the right hand forehand, the left following it through."""
    keys = [
        (0, _dag(-14, -24, (-0.22, 0.04, 0.14), _n(-0.5, 0.6, -0.5), (-0.8, -0.1, -0.5),
                 (0.08, -0.24, 0.26), _n(0.3, 0.6, 0.7), (0.7, -0.5, -0.4), weight=-0.3), "fast"),
        (2, _dag(-2, -2, (0.0, -0.12, 0.44), _n(0.2, 0.0, 1.0), (-0.6, -0.7, -0.3),
                 (0.10, -0.24, 0.24), _n(0.4, 0.5, 0.7), (0.7, -0.5, -0.4)), "linear"),
        (4, _dag(12, 24, (0.26, -0.22, 0.28), _n(0.9, -0.2, 0.3), (-0.9, -0.2, 0.2),
                 (0.30, -0.18, 0.10), _n(0.9, 0.1, -0.3), (0.6, -0.6, -0.1), weight=0.4), "ease"),
        (6, _dag(13, 27, (0.28, -0.24, 0.24), _n(0.85, -0.3, -0.1), (-0.9, -0.1, 0.3),
                 (0.32, -0.20, 0.06), _n(0.85, 0.0, -0.45), (0.6, -0.6, -0.1), weight=0.4), "auto"),
        (16, DAG_GUARD, "ease"),
    ]
    return build("daggers_fore", rig, keys, lead=STRIKE, meta={"layer": "upper", "contact": 2 / 30, "weapon": "daggers"})


def daggers_heavy(rig):
    """Both blades in a crossing cut, out from the middle."""
    keys = [
        (0, _dag(0, 0, (0.16, 0.10, 0.18), _n(0.4, 0.7, -0.5), (-0.4, 0.2, -0.8),
                 (-0.16, 0.10, 0.18), _n(-0.4, 0.7, -0.5), (0.4, 0.2, -0.8)), "fast"),
        (3, _dag(0, 0, (0.0, -0.10, 0.44), _n(-0.3, -0.1, 1.0), (-0.6, -0.6, -0.3),
                 (0.0, -0.08, 0.44), _n(0.3, -0.1, 1.0), (0.6, -0.6, -0.3), pitch=16), "linear"),
        (6, _dag(0, 0, (-0.30, -0.24, 0.24), _n(-0.9, -0.3, 0.2), (-0.3, -1.0, 0.2),
                 (0.30, -0.24, 0.24), _n(0.9, -0.3, 0.2), (0.3, -1.0, 0.2), pitch=20, weight=0.2), "ease"),
        (9, _dag(0, 0, (-0.32, -0.26, 0.20), _n(-0.85, -0.4, -0.1), (-0.2, -1.0, 0.3),
                 (0.32, -0.26, 0.20), _n(0.85, -0.4, -0.1), (0.2, -1.0, 0.3), pitch=20, weight=0.2), "auto"),
        (20, DAG_GUARD, "ease"),
    ]
    return build("daggers_heavy", rig, keys, lead=STRIKE, meta={"layer": "upper", "contact": 3 / 30, "weapon": "daggers"})


ALL = (("dash", dash), ("hit", hit), ("death", death), ("death_back", death_back), ("get_up", get_up), ("cast_bolt", cast_bolt),
       ("cast_raise", cast_raise), ("cast_flick", cast_flick), ("crossbow_shoot", crossbow_shoot), ("throw", throw),
       ("warcry", warcry), ("daggers_back", daggers_back), ("daggers_fore", daggers_fore),
       ("daggers_heavy", daggers_heavy))


def clips(rig, want):
    out = []
    for name, fn in ALL:
        if want and not any(w in name for w in want):
            continue
        out.append(fn(rig))
    return out
