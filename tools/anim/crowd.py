"""The crowd's own motion, keyed on the kit's bodies (folk.py packs it with
the townsfolk's clips, "f_<name>" and "m_<name>", and the crowd bakes it:
Vat.cs, FolkClips.Crowd).

- lurch, lurch_armed: the walking dead's gait. The crowd closes at a jog
  (Risen 2.7 m/s), far faster than any captured shamble (Kimodo's are 0.6
  to 1 m/s: at the crowd's pace their feet would skate). So the lurch is
  solved from the stride (gait.py) at the crowd's own speed and made dead
  on top of it: pitched forward from the ankles, always about to fall into
  the next step; the left leg dragged through on its toes, the body
  dipping onto it; the head hung and lolling late on the bounce; one arm
  dead weight, swinging on its own; the other half raised, reaching for
  the living.
- rally, rally_armed: a caster's cast (a call, a horn, a drum, "To me!"):
  a dip, then the weapon or the fist thrust up overhead and shaken, the
  chest thrown open, the free hand flung out to call them on. Held up for
  as long as the cast lasts (the longest is 1.5 s).
- die_back, die_front, die_side (and _armed, _pistol): three ways to fall,
  the crowd's "die", "die2" and "die3" (FolkClips.Deaths), so a field of
  the dead does not lie alike. Armed, what is held is laid flat on the
  ground with the hand (a crossbow on its side); see "the fallen" below.
"""
from __future__ import annotations

import math
from dataclasses import replace

import numpy as np

from clips.actions import arm, body, stance
from gait import Gait, arc_of, pose_at
from keyed import Rig, build, merge
from rig import Clip, qinv, qmul, qrot

LURCH = Gait(frames=22, speed=2.6, duty=0.52, drop=0.11, bob=0.05, lean=19.0, spine_lean=13.0, hip_yaw=11.0,
             hip_roll=7.0, hip_shift=0.05, chest_yaw=5.0, width=0.10, reach=0.42, kick=0.18, knee=0.22, toe_off=16.0,
             arm_fwd=(0.02, -0.46, 0.10), arm_back=(0.04, -0.46, -0.06), elbow_out=0.1, fingers="relaxed", head_up=-16.0,
             shoulders=(-4, 10))


def _lurch_pose(g: Gait, rig: Rig, ph, armed=False):
    p = pose_at(g, rig, ph)
    ph = ph % 1.0
    # The dragged left leg: swung through stiff, out round the side with the
    # hip hitched to clear it, toes down and scraping, turned out; set down
    # flat at the end.
    hike = 0.0
    if ph >= g.duty:
        s = (ph - g.duty) / (1 - g.duty)
        f = p["foot_l"]
        x, y, z = f["pos"]
        drag = math.sin(math.pi * min(1.0, s / 0.85))
        hike = drag
        lift = 0.25 + 0.75 * max(0.0, (s - 0.75) / 0.25)
        p["foot_l"] = {**f, "pos": (x + 0.11 * drag, y * lift + 0.02 * drag, z), "toe": 0, "pole": (0.7, 0.0, 1.0),
                       "rot": (4 + 16 * drag, 22 * drag + f["rot"][1] * (1 - drag), 0)}
    # The body drops onto the weak leg as it takes the weight, and hitches
    # up over the good one to swing it through.
    on_left = 1.0 if ph < g.duty else 0.0
    dip = 0.035 * on_left * math.sin(math.pi * min(1.0, ph / g.duty))
    hx, hy, hz = p["hips"]["pos"]
    yaw, pitch, roll = p["hips"]["rot"]
    p["hips"] = {"pos": (hx + 0.015 * on_left - 0.03 * hike, hy - dip + 0.025 * hike, hz + 0.02),
                 "rot": (yaw, pitch, roll + 5 * dip / 0.035 + 11 * hike)}
    # The head hung and tipped to one side, bouncing late.
    ny, npitch, nroll = p["neck"]
    p["neck"] = (ny, npitch + 6, nroll + 6)
    hy_, hp, hr = p["head"]
    p["head"] = (hy_ * 0.4 + 6, hp + 8 + 5 * math.sin(4 * math.pi * (ph - 0.14)), hr + 12 + 4 * math.sin(2 * math.pi * (ph - 0.2)))
    # One arm swings as dead weight, late on the body; the other is half
    # raised and reaching, the fingers hooked. Unarmed, the right reaches;
    # armed, the left does, and the weapon hangs in the right, trailing.
    k = 0.5 - 0.5 * math.cos(2 * math.pi * (ph - 0.62))
    reach = 0.5 - 0.5 * math.cos(2 * math.pi * (ph - 0.1))
    # (The chest is pitched some 30 degrees forward: hanging straight down
    # is down and forward in its frame.)
    if not armed:
        p["hand_l"] = {"arc": arc_of((0.07, -0.44, 0.14 + 0.14 * k)), "pole": (0.2, -0.3, -1.0)}
        p["hand_r"] = {"arc": arc_of((0.03, 0.02 + 0.04 * reach, 0.40 + 0.04 * reach)), "pole": (-0.7, -0.6, -0.3),
                       "knuckles": (0.0, -0.3, 1.0)}
        p["clav_r"], p["clav_l"] = (2, 14), (-6, 6)
        p["fingers_l"], p["fingers_r"] = "relaxed", "claw"
    else:
        k = 1 - k
        p["hand_r"] = {"arc": arc_of((-0.08, -0.42, 0.12 + 0.12 * k)), "pole": (-0.2, -0.3, -1.0), "frame": "char",
                       "blade": (0.0, -0.55, -0.85)}
        p["hand_l"] = {"arc": arc_of((-0.03, 0.02 + 0.04 * reach, 0.40 + 0.04 * reach)), "pole": (0.7, -0.6, -0.3),
                       "knuckles": (0.0, -0.3, 1.0)}
        p["clav_l"], p["clav_r"] = (2, 14), (-8, 4)
        p["fingers_r"], p["fingers_l"] = "grip", "claw"
    return p


def lurch(name, rig: Rig, g: Gait = LURCH, armed=False) -> Clip:
    n = g.frames
    rot = np.empty((n + 1, len(rig.sk), 4))
    pos = np.empty((n + 1, len(rig.sk), 3))
    for f in range(n + 1):
        rot[f], pos[f] = rig.solve(_lurch_pose(g, rig, f / n, armed))
    meta = {"layer": "full", "speed": g.speed, "cycle": n / 30.0, "steps": 2, "source": "keyed (tools/anim/crowd.py)",
            "licence": "own work", "changes": "", "note": "the Risen's lurch, at the crowd's pace" + (", armed" if armed else "")}
    return Clip(name, 30, rot, pos, loop=True, meta=meta)


def rally(name, rig: Rig, armed=False) -> Clip:
    hold = "grip" if armed else "fist"

    def up(lift, out=0.0):
        """The right hand high over the head (lift 0..1: to full reach), the
        weapon held upright."""
        h = arm((-0.12 - 0.04 * out, 0.26 + 0.30 * lift, 0.10 + 0.08 * (1 - lift)), (-0.9, 0.1, 0.3))
        if armed:
            # Brandished: the shaft tipped forward over the head.
            h["blade"] = (0.0, 0.55, 0.85)
            h["frame"] = "char"
        return h

    def calling(k):
        """The left hand flung out ahead, pointing them on at her (k 0..1: out)."""
        return arm((0.14 + 0.06 * k, -0.30 + 0.30 * k, 0.12 + 0.36 * k), (0.8, -0.4, -0.4), knuckles=(0.1, -0.1, 1.0))

    base = stance(0.04, l=(0.14, 0.10), r=(-0.15, -0.10))
    wide = stance(0.08, l=(0.16, 0.16), r=(-0.17, -0.14))
    keys = [
        (0, body(base, hand_l=arm((0.06, -0.44, 0.06), (0.6, -0.4, -0.5)), hand_r=arm((-0.06, -0.44, 0.06), (-0.6, -0.4, -0.5)),
                 fingers_l="relaxed", fingers_r=hold), "ease"),
        # The gather: down and turned to the right, the arm drawn in low (it
        # rises in front of the body from here, never out to the side).
        (5, body(wide, hips=(-8, 6, 0), spine=(-10, 10, 0), neck=(0, 4, 0), head=(4, 6, 0), clav_r=(-4, -10),
                 hand_l=arm((0.10, -0.40, 0.14), (0.6, -0.4, -0.5)), hand_r=arm((-0.16, -0.36, 0.08), (-0.8, -0.2, -0.4)),
                 fingers_l="relaxed", fingers_r=hold), "auto"),
        # Up: thrust high, the chest thrown open, head back on the shout,
        # the free hand flung out ahead.
        (10, body(wide, hips=(6, -4, 0), spine=(8, -12, 0), neck=(0, -6, 0), head=(0, -14, 0), clav_r=(16, 6), clav_l=(6, 8),
                  hand_l=calling(1.0), hand_r=up(1.0), fingers_l="point", fingers_r=hold), "fast"),
    ]
    # Shaken: pumped on each beat, the body bobbing with it, the head nodding the beat.
    beats = [(15, 0.4), (20, 1.0), (25, 0.4), (30, 1.0), (35, 0.4), (40, 1.0), (47, 0.9)]
    for i, (f, lift) in enumerate(beats):
        k = 1.0 - 0.35 * min(1.0, i / 3)
        bob = 0.035 * (1 - lift)
        keys.append((f, body(stance(0.08 + bob, l=(0.16, 0.16), r=(-0.17, -0.14)), hips=(6, -4 + 6 * (1 - lift), 0),
                             spine=(8, -10 + 8 * (1 - lift), 0), neck=(0, -4, 0), head=(0, -10 + 10 * (1 - lift), 0),
                             clav_r=(10 + 6 * lift, 6), clav_l=(4, 6), hand_l=calling(k), hand_r=up(lift),
                             fingers_l="point" if i < 3 else "open", fingers_r=hold), "auto"))
    meta = {"layer": "full", "note": "a caster's rally" + (", armed" if armed else ""), "source": "keyed (tools/anim/crowd.py)"}
    return build(name, rig, keys, meta=meta)


# ------------------------------------------------------------------ the fallen --
# Three ways down, so a field of the dead is not one body printed thirty
# times: over onto the back, onto the face, and in a heap on the side. Each
# is a body with nothing left in it: no hand goes out to break a fall, the
# head lolls where it lands, the joints fold at angles the living would not
# allow. Every one is a fall of 0.8 s (the crowd plays a death in 0.78 s and
# holds its last frame as the corpse for up to 18 s, so the last pose is
# what is seen most, from above).
#
# Positions are keyed for the kit's man and scaled to the body; the hips are
# given as the height of the pelvis off the ground.

def _kit(rig: Rig):
    py = float(rig.prest[rig.I["pelvis"]][1])
    k = py / 0.949

    def P(x, y, z):
        return (x * k, y * k, z * k)

    def H(x, y, z):
        """The hips' offset that sets the pelvis at (x, y, z)."""
        return (x * k, y * k - py, z * k - float(rig.prest[rig.I["pelvis"]][2]))

    return P, H


def _globals(rig: Rig, pose):
    return rig.globals(*rig.solve(pose))


def _in_char(rig: Rig, keys):
    """Every hand keyed in her character's space. A hand keyed about the
    chest (actions.arm) has its elbow's way and its aim turned out of the
    chest's frame for that key; mixed frames switch at the nearest key, and a
    fall turns the chest over so far that the switch is a jump."""
    s3 = rig.I["spine_03"]
    out = []
    for fr, pose, ease in keys:
        pose = merge(pose)
        chest = None
        for side in "lr":
            h = pose.get(f"hand_{side}")
            if not h or h.get("frame", "char") != "chest":
                continue
            if chest is None:
                grot, _ = _globals(rig, pose)
                chest = qmul(grot[0, s3], qinv(rig.grest[s3]))
            h = dict(h, frame="char")
            for k in ("pole", "blade", "knuckles"):
                if k in h:
                    h[k] = tuple(float(x) for x in qrot(chest, np.array(h[k], float)))
            pose[f"hand_{side}"] = h
        out.append((fr, pose, ease))
    return out


def _held(rig: Rig, keys, laid, pistol=False):
    """What is held laid down with the hands: from the key `laid` names on,
    each hand turned so what it holds lies flat on the ground (a blade along
    it, a shield on the forearm face up over it, a crossbow on its side);
    before then, held as the arm carries it."""
    first = min(laid)
    out = []
    for fr, pose, ease in keys:
        pose = merge(pose)
        if fr < first:
            grot, gpos = _globals(rig, pose)
        for side in "lr":
            h = dict(pose.get(f"hand_{side}") or {})
            if not h:
                continue
            if fr >= first:
                blade, knuckles = laid[max(k for k in laid if k <= fr)][side]
                if side == "r" and pistol:
                    # A crossbow lies on its flat with the thumb up, the stock along the fingers.
                    blade, knuckles = (0.0, 1.0, 0.0), knuckles
            else:
                q = grot[0, rig.I[f"hand_{side}"]]
                blade, knuckles = qrot(q, [0, 0, 1.0]), qrot(q, [0, 1.0, 0])
                # A hand near the ground does not drive the point into it: the
                # blade (taken as a long sword's, 1.2 m) is lifted to clear it.
                hy = float(gpos[0, rig.I[f"hand_{side}"]][1])
                low = (0.05 - hy) / 1.2
                if blade[1] < low:
                    flat = np.array([blade[0], 0.0, blade[2]])
                    flat = flat / np.linalg.norm(flat) if np.linalg.norm(flat) > 1e-3 else np.array([0, 0, 1.0])
                    blade = flat * math.sqrt(max(0.0, 1 - low * low)) + np.array([0, low, 0])
            h.update(blade=tuple(float(x) for x in blade), knuckles=tuple(float(x) for x in knuckles), frame="char")
            # The forearm turns with the hand, so a shield strapped to it lies as the hand does.
            if side == "l":
                h["twist"] = 1.0
            pose[f"hand_{side}"] = h
        pose["fingers_r"] = "grip"
        out.append((fr, pose, ease))
    return out


def _mirrored(pose):
    """The pose as its own reflection, left for right."""
    def turn(v):
        return (-v[0], v[1], -v[2])

    def at(v):
        return (-v[0], v[1], v[2])

    out = {}
    for k, v in pose.items():
        side = {"_l": "_r", "_r": "_l"}.get(k[-2:]) if k[-2:] in ("_l", "_r") else None
        key = k[:-2] + side if side else k
        if k in ("spine", "neck", "head"):
            v = turn(v)
        elif k == "hips":
            v = {**v, **({"pos": at(v["pos"])} if "pos" in v else {}), **({"rot": turn(v["rot"])} if "rot" in v else {})}
        elif k.startswith(("foot_", "hand_")):
            v = dict(v)
            for c in ("pos", "pole", "blade", "knuckles"):
                if c in v:
                    v[c] = at(v[c])
            if "rot" in v:
                v["rot"] = turn(v["rot"])
            if "arc" in v:
                v["arc"] = (-v["arc"][0], v["arc"][1], v["arc"][2])
        out[key] = v
    return out


def _fall(name, rig, keys, note, laid, armed, pistol):
    keys = _in_char(rig, keys)
    if armed:
        keys = _held(rig, keys, laid, pistol)
    return build(name, rig, keys, meta={"layer": "full", "hold": True, "source": "keyed (tools/anim/crowd.py)",
                                        "note": note + (", armed" if armed else "")})


def _on_back(P, H, settle=0.0):
    """On its back, a knee fallen out, an arm flung up past the head, the
    other dropped at its side, the face turned away."""
    return {
        "hips": {"pos": H(0.0, 0.11, -0.60), "rot": (-6, -87, -4)},
        "spine": (4, 3 - 2 * settle, -5), "neck": (10, 4, 0), "head": (36 + 4 * settle, -6, 10),
        "foot_l": {"pos": P(0.08, -0.01, 0.0), "rot": (50, -40, 40), "pole": (1, 0.3, 0.5)},
        "foot_r": {"pos": P(-0.20, -0.01, 0.22), "rot": (-24, -55, -10), "pole": (-0.4, 1, 0)},
        "hand_l": {"frame": "char", "pos": P(0.52, 0.04, -1.28), "pole": (1, 0.1, 0.2), "knuckles": (0.4, 0, -1)},
        "hand_r": {"frame": "char", "pos": P(-0.36, 0.04, -0.66), "pole": (-1, 0.4, 0), "knuckles": (-0.2, 0, 1)},
        "fingers_l": "open", "fingers_r": "relaxed",
    }


def die_back(name, rig: Rig, armed=False, pistol=False) -> Clip:
    """Struck in front: the chest caved and the head thrown back, a stagger
    on the back foot, the knees go, it sits down hard and goes over, the
    legs bounced up by the back hitting; then nothing."""
    P, H = _kit(rig)
    keys = [
        (0, {"hips": {"pos": H(0, 0.89, 0.02), "rot": (0, -10, 0)}, "spine": (0, -16, 0), "neck": (0, -8, 0), "head": (0, -20, 0),
             "clav_l": (12, 10), "clav_r": (12, 10),
             "foot_l": {"pos": P(0.13, 0, 0.12), "rot": (10, 0, 0)}, "foot_r": {"pos": P(-0.15, 0, -0.06), "rot": (-14, 0, 0)},
             "hand_l": arm((0.16, -0.34, 0.24), (0.9, -0.6, -0.2)), "hand_r": arm((-0.16, -0.36, 0.22), (-0.9, -0.6, -0.2)),
             "fingers_l": "spread", "fingers_r": "relaxed"}, "fast"),
        # The stagger: the back foot caught behind, the body still going.
        (4, {"hips": {"pos": H(0, 0.77, -0.16), "rot": (0, -16, 4)}, "spine": (-4, -14, 4), "neck": (0, -6, 0), "head": (0, -16, 0),
             "clav_l": (16, 4), "clav_r": (16, 4),
             "foot_l": {"pos": P(0.14, 0.04, 0.14), "rot": (10, -10, 0)}, "foot_r": {"pos": P(-0.16, 0, -0.38), "rot": (-16, 0, 0)},
             "hand_l": arm((0.40, -0.22, 0.18), (0.9, -0.2, -0.3)), "hand_r": arm((-0.40, -0.26, 0.16), (-0.9, -0.2, -0.3)),
             "fingers_l": "spread", "fingers_r": "open"}, "auto"),
        # The knees go, down over the back foot.
        (8, {"hips": {"pos": H(0, 0.46, -0.38), "rot": (0, -24, 6)}, "spine": (-4, -10, 6), "neck": (0, 4, 0), "head": (0, 8, 0),
             "clav_l": (8, 0), "clav_r": (8, 0),
             "foot_l": {"pos": P(0.16, 0.0, 0.10), "rot": (14, 0, 0)},
             "foot_r": {"pos": P(-0.17, 0, -0.36), "rot": (-16, 0, 0), "pole": (-0.4, 0.2, 1)},
             "hand_l": arm((0.44, -0.38, -0.04), (0.9, 0.2, -0.4)), "hand_r": arm((-0.44, -0.40, -0.06), (-0.9, 0.2, -0.4)),
             "fingers_l": "open", "fingers_r": "open"}, "linear"),
        # Sat down hard, the feet thrown out in front, the head dropped forward by it.
        (11, {"hips": {"pos": H(0, 0.13, -0.52), "rot": (0, -38, 4)}, "spine": (-4, 0, 4), "neck": (0, 14, 0), "head": (0, 20, 0),
              "clav_l": (10, 0), "clav_r": (10, 0),
              "foot_l": {"pos": P(0.20, 0.02, 0.14), "rot": (16, -30, 0), "pole": (0.3, 1, 0.3)},
              "foot_r": {"pos": P(-0.18, 0.03, 0.04), "rot": (-16, -30, 0), "pole": (-0.3, 1, 0.3)},
              "hand_l": arm((0.70, -0.20, 0.10), (0.9, 0.3, -0.4)), "hand_r": arm((-0.70, -0.24, 0.08), (-0.9, 0.3, -0.4)),
              "fingers_l": "open", "fingers_r": "open"}, "linear"),
        # The back hits: the head whipped back, the legs bounced up, the arms flung wide.
        (15, {"hips": {"pos": H(0, 0.10, -0.60), "rot": (0, -84, 0)}, "spine": (0, -2, 0), "neck": (0, -6, 0), "head": (6, -14, 4),
              "foot_l": {"pos": P(0.22, 0.26, 0.30), "rot": (20, -70, 10), "pole": (0.4, 1, 0.3)},
              "foot_r": {"pos": P(-0.18, 0.34, 0.34), "rot": (-16, -70, -10), "pole": (-0.3, 1, 0.3)},
              "hand_l": {"frame": "char", "pos": P(0.58, 0.10, -1.08), "pole": (1, 0.4, 0), "knuckles": (0.4, 0, -1)},
              "hand_r": {"frame": "char", "pos": P(-0.62, 0.10, -0.90), "pole": (-1, 0.4, 0), "knuckles": (-0.4, 0, -1)},
              "fingers_l": "spread", "fingers_r": "spread"}, "auto"),
        # Bounced: the head comes up and rolls aside, the legs drop.
        (19, merge(_on_back(P, H), hips={"pos": H(0.0, 0.13, -0.60), "rot": (-4, -84, -2)}, head=(24, 6, 8),
                   foot_l={"pos": P(0.10, 0.12, 0.04), "rot": (45, -40, 35), "pole": (1, 0.5, 0.3)},
                   foot_r={"pos": P(-0.18, 0.12, 0.28), "rot": (-20, -60, -10), "pole": (-0.3, 1, 0)}), "auto"),
        (24, _on_back(P, H, 1.0), "ease"),
    ]
    # Laid down: the blade out to the right toward the feet; the shield arm's palm down.
    laid = {15: {"r": ((-0.8, 0, 0.6), (0.6, 0, 0.8)), "l": ((0.95, 0, 0.3), (0.3, 0, -0.95))}}
    return _fall(name, rig, keys, "the crowd's death: struck in front, over onto its back", laid, armed, pistol)


def _on_face(P, H, settle=0.0):
    """Face down, the head turned on its cheek, one arm bent up by the head
    and the other along its side, palm up; one knee drawn up and out."""
    return {
        "hips": {"pos": H(0.0, 0.14, 0.36), "rot": (8, 88, 6)},
        "spine": (4, 2 - 2 * settle, 4), "clav_l": (-6, 25), "clav_r": (-6, 25), "neck": (16, 0, 0), "head": (60 + 4 * settle, 6, 0),
        "foot_l": {"pos": P(0.32, -0.01, -0.38), "rot": (20, 150, -40), "pole": (1, 0.1, 0.4)},
        "foot_r": {"pos": P(-0.16, -0.03, -0.56), "rot": (-15, 150, 0), "pole": (-0.2, -1, 0)},
        "hand_l": {"frame": "char", "pos": P(0.42, 0.04, 0.96), "pole": (1, -0.15, -0.3), "knuckles": (0.2, 0, 1)},
        "hand_r": {"frame": "char", "pos": P(-0.30, 0.04, 0.46), "pole": (-1, 0.5, 0.2), "knuckles": (-0.1, 0, -1)},
        "fingers_l": "relaxed", "fingers_r": "open",
    }


def die_front(name, rig: Rig, armed=False, pistol=False) -> Clip:
    """The legs go first: it drops onto its knees, sways there for a beat
    with the head hanging, and goes over onto its face without a hand put
    out; the legs slide out behind."""
    P, H = _kit(rig)
    hang_l = arm((0.10, -0.42, 0.10), (0.6, -0.4, -0.5))
    hang_r = arm((-0.10, -0.42, 0.08), (-0.6, -0.4, -0.5))
    keys = [
        # Struck: the body folds round the blow, the head drops.
        (0, {"hips": {"pos": H(0, 0.90, 0.0), "rot": (0, 6, 0)}, "spine": (4, 18, 0), "neck": (0, 10, 0), "head": (6, 20, 6),
             "clav_l": (4, 12), "clav_r": (4, 12),
             "foot_l": {"pos": P(0.13, 0, 0.10), "rot": (10, 0, 0)}, "foot_r": {"pos": P(-0.15, 0, -0.08), "rot": (-14, 0, 0)},
             "hand_l": arm((0.08, -0.36, 0.16), (0.6, -0.4, -0.5)), "hand_r": arm((-0.08, -0.34, 0.16), (-0.6, -0.4, -0.5)),
             "fingers_l": "relaxed", "fingers_r": "relaxed"}, "ease"),
        # The knees buckle forward.
        (4, {"hips": {"pos": H(0, 0.70, 0.04), "rot": (4, 10, 4)}, "spine": (6, 22, 4), "neck": (0, 12, 0), "head": (8, 24, 12),
             "foot_l": {"pos": P(0.13, 0, 0.10), "rot": (10, 0, 0), "pole": (0.2, 0, 1)},
             "foot_r": {"pos": P(-0.15, 0.02, -0.10), "rot": (-14, -10, 0), "pole": (-0.2, 0, 1)},
             "hand_l": hang_l, "hand_r": hang_r, "fingers_l": "relaxed", "fingers_r": "relaxed"}, "auto"),
        # Down on its knees, the head hanging.
        (8, {"hips": {"pos": H(0, 0.50, -0.02), "rot": (4, 14, 6)}, "spine": (6, 20, 6), "neck": (0, 14, 0), "head": (10, 26, 16),
             "foot_l": {"pos": P(0.14, 0.02, -0.36), "rot": (8, -70, 0), "pole": (0.2, -1, 0.5)},
             "foot_r": {"pos": P(-0.15, 0.02, -0.38), "rot": (-8, -70, 0), "pole": (-0.2, -1, 0.5)},
             "hand_l": arm((0.06, -0.44, 0.02), (0.6, -0.4, -0.5)), "hand_r": arm((-0.04, -0.44, 0.0), (-0.6, -0.4, -0.5)),
             "fingers_l": "relaxed", "fingers_r": "relaxed"}, "linear"),
        # The sway on the knees, then over: the hips go, the arms trail.
        (11, {"hips": {"pos": H(0, 0.48, 0.02), "rot": (6, 30, 8)}, "spine": (6, 22, 6), "neck": (0, 10, 0), "head": (14, 16, 18),
              "foot_l": {"pos": P(0.14, 0.02, -0.38), "rot": (8, -72, 0), "pole": (0.2, -1, 0.5)},
              "foot_r": {"pos": P(-0.15, 0.02, -0.40), "rot": (-8, -72, 0), "pole": (-0.2, -1, 0.5)},
              "hand_l": arm((0.10, -0.40, -0.06), (0.6, -0.4, -0.5)), "hand_r": arm((-0.08, -0.40, -0.08), (-0.6, -0.4, -0.5)),
              "fingers_l": "relaxed", "fingers_r": "relaxed"}, "auto"),
        (14, {"hips": {"pos": H(0, 0.40, 0.14), "rot": (8, 58, 8)}, "spine": (6, 14, 6), "neck": (6, -2, 0), "head": (20, 4, 14),
              "foot_l": {"pos": P(0.16, 0.02, -0.50), "rot": (8, -80, 0), "pole": (0.2, -0.2, 1)},
              "foot_r": {"pos": P(-0.15, 0.03, -0.54), "rot": (-8, -80, 0), "pole": (-0.2, -0.2, 1)},
              "hand_l": arm((0.14, -0.36, -0.16), (0.6, -0.2, -0.5)), "hand_r": arm((-0.12, -0.36, -0.18), (-0.6, -0.2, -0.5)),
              "fingers_l": "relaxed", "fingers_r": "open"}, "linear"),
        # The face hits; the chest takes it and the legs are thrown out behind.
        (17, merge(_on_face(P, H), hips={"pos": H(0.0, 0.13, 0.34), "rot": (6, 90, 4)}, neck=(10, -6, 0), head=(24, -2, 0),
                   foot_l={"pos": P(0.30, 0.10, -0.34), "rot": (20, 120, -30), "pole": (1, 0.1, 0.4)},
                   foot_r={"pos": P(-0.16, 0.08, -0.58), "rot": (-15, 120, 0), "pole": (-0.2, -1, 0)},
                   hand_l={"frame": "char", "pos": P(0.30, 0.08, 0.80), "pole": (1, 0.3, -0.2), "knuckles": (0.2, 0, 1)}), "auto"),
        # A bounce, and the head rolls onto its cheek.
        (20, merge(_on_face(P, H), hips={"pos": H(0.0, 0.16, 0.36), "rot": (8, 86, 6)}, neck=(16, -14, 0), head=(36, -10, 0)), "auto"),
        (24, _on_face(P, H, 1.0), "ease"),
    ]
    laid = {17: {"r": ((-0.7, 0, -0.7), (0.7, 0, -0.7)), "l": ((1, 0, -0.2), (0.2, 0, 1))}}
    return _fall(name, rig, keys, "the crowd's death: to its knees and over onto its face", laid, armed, pistol)


def _on_side(P, H, settle=0.0):
    """In a heap on its right side, curled: the knees drawn up, the head
    bowed onto the ground, the lower arm out under it, the upper one fallen
    over in front."""
    return {
        "hips": {"pos": H(0.0, 0.18, 0.0), "rot": (12, 10, 86)},
        "spine": (6, 22 + 3 * settle, -14), "clav_r": (35, 25), "neck": (0, 14, 24), "head": (4, 18 + 3 * settle, 30),
        "foot_l": {"pos": P(0.40, 0.14, 0.28), "rot": (10, 40, 80), "pole": (0, -0.3, 1)},
        "foot_r": {"pos": P(0.46, -0.02, 0.12), "rot": (10, 40, 80), "pole": (0, 0.15, 1)},
        "hand_l": {"frame": "char", "pos": P(-0.32, 0.05, 0.30), "pole": (0, 0.5, 1), "knuckles": (-0.3, 0, 1)},
        "hand_r": {"frame": "char", "pos": P(-0.78, 0.04, 0.62), "pole": (0, 0.6, 1), "knuckles": (0, 0, 1)},
        "fingers_l": "relaxed", "fingers_r": "relaxed",
    }


def die_side(name, rig: Rig, armed=False, pistol=False) -> Clip:
    """The strings cut: the knees fold where it stands, it drops straight
    down onto them twisting, lands on its hip and goes over onto its side
    in a heap, the head knocking the ground last."""
    P, H = _kit(rig)
    keys = [
        # Struck: a twist off the blow, the head thrown to the side.
        (0, {"hips": {"pos": H(0, 0.88, 0.0), "rot": (10, 4, -4)}, "spine": (16, 6, -6), "neck": (6, 0, 0), "head": (12, 4, -16),
             "clav_l": (10, 0), "clav_r": (6, 0),
             "foot_l": {"pos": P(0.13, 0, 0.10), "rot": (10, 0, 0)}, "foot_r": {"pos": P(-0.15, 0, -0.08), "rot": (-14, 0, 0)},
             "hand_l": arm((0.20, -0.30, 0.10), (0.8, -0.3, -0.4)), "hand_r": arm((-0.12, -0.36, 0.14), (-0.6, -0.4, -0.5)),
             "fingers_l": "spread", "fingers_r": "relaxed"}, "ease"),
        # The knees fold in under it.
        (4, {"hips": {"pos": H(0.02, 0.66, 0.02), "rot": (16, 8, 4)}, "spine": (18, 10, 4), "neck": (4, 6, 0), "head": (10, 12, 10),
             "foot_l": {"pos": P(0.13, 0, 0.10), "rot": (10, 0, 0), "pole": (-0.4, 0, 1)},
             "foot_r": {"pos": P(-0.15, 0.02, -0.08), "rot": (-14, -10, 0), "pole": (0.3, 0, 1)},
             "hand_l": arm((0.14, -0.38, 0.06), (0.6, -0.4, -0.5)), "hand_r": arm((-0.10, -0.40, 0.08), (-0.6, -0.4, -0.5)),
             "fingers_l": "relaxed", "fingers_r": "relaxed"}, "auto"),
        # Dropped onto its knees, going over to its right.
        (8, {"hips": {"pos": H(0.0, 0.47, 0.0), "rot": (20, 14, 18)}, "spine": (14, 14, 10), "neck": (0, 8, 6), "head": (6, 12, 20),
             "foot_l": {"pos": P(0.20, 0.02, -0.30), "rot": (20, -60, 10), "pole": (0.1, -0.2, 1)},
             "foot_r": {"pos": P(-0.08, 0.02, -0.34), "rot": (0, -60, 0), "pole": (0.1, -0.2, 1)},
             "hand_l": arm((0.10, -0.42, 0.06), (0.6, -0.4, -0.5)), "hand_r": arm((-0.12, -0.42, 0.0), (-0.6, -0.4, -0.5)),
             "fingers_l": "relaxed", "fingers_r": "relaxed"}, "linear"),
        # On its hip: the legs folded off to the left, the trunk tipping.
        (11, {"hips": {"pos": H(-0.04, 0.20, 0.02), "rot": (20, 14, 44)}, "spine": (10, 18, 10), "neck": (0, 6, 4), "head": (4, 6, 14),
              "foot_l": {"pos": P(0.40, 0.10, 0.06), "rot": (20, 20, 50), "pole": (0, 0.2, 1)},
              "foot_r": {"pos": P(0.36, -0.01, -0.06), "rot": (20, 20, 50), "pole": (0, 0.2, 1)},
              "hand_l": arm((0.10, -0.40, 0.14), (0.6, -0.4, -0.5)), "hand_r": {"frame": "char", "pos": P(-0.45, 0.12, 0.26), "pole": (-0.6, 0.4, -0.4)},
              "fingers_l": "relaxed", "fingers_r": "relaxed"}, "linear"),
        # The shoulder and then the head hit.
        (15, merge(_on_side(P, H), hips={"pos": H(0.0, 0.18, 0.0), "rot": (14, 10, 84)}, spine=(6, 14, -10), neck=(0, 2, 6), head=(4, 6, 4),
                   hand_l={"frame": "char", "pos": P(-0.26, 0.24, 0.22), "pole": (0, 0.5, 1), "knuckles": (-0.3, 0, 1)}), "auto"),
        # A rebound of the head, the upper arm falling over in front.
        (19, merge(_on_side(P, H), head=(4, 12, 4), hand_l={"frame": "char", "pos": P(-0.30, 0.12, 0.28), "pole": (0, 0.5, 1), "knuckles": (-0.3, 0, 1)}), "auto"),
        (24, _on_side(P, H, 1.0), "ease"),
    ]
    laid = None
    if armed:
        # Armed, it goes down on its left side instead: the shield arm is
        # then the one out along the ground, the shield flat under it (on
        # top, the forearm cannot come down level to the ground, and a
        # shield strapped to it stands on edge); the weapon lies out in
        # front from the hand fallen over the belly.
        keys = [(fr, _mirrored(pose), ease) for fr, pose, ease in keys]
        laid = {15: {"r": ((0.3, 0, 0.95), (-0.95, 0, 0.3)), "l": ((0.8, 0, -0.6), (0.6, 0, 0.8))}}
    return _fall(name, rig, keys, "the crowd's death: the knees fold and it goes down in a heap on its side", laid, armed, pistol)


# name: function(name, rig) -> Clip, for each body.
KEYED = {"lurch": lurch, "lurch_armed": lambda name, rig: lurch(name, rig, armed=True),
         "rally": rally, "rally_armed": lambda name, rig: rally(name, rig, armed=True),
         "die_back": die_back, "die_front": die_front, "die_side": die_side,
         "die_back_armed": lambda name, rig: die_back(name, rig, armed=True),
         "die_front_armed": lambda name, rig: die_front(name, rig, armed=True),
         "die_side_armed": lambda name, rig: die_side(name, rig, armed=True),
         "die_back_pistol": lambda name, rig: die_back(name, rig, armed=True, pistol=True),
         "die_front_pistol": lambda name, rig: die_front(name, rig, armed=True, pistol=True),
         "die_side_pistol": lambda name, rig: die_side(name, rig, armed=True, pistol=True)}
