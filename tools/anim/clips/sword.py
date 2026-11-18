"""The warden's sword (and buckler).

How the game swings (BattleFx, Hits.Arc): the damage, the arc and the clip
start in the same frame; the arc's head crosses in 0.12 s and alternate
swings are mirrored, the first sweeping from her left to her right. The
clips play at 1.6 times, so the blade must cross in the first five or six
frames here. So each swing starts already cocked (its anticipation is the
blend in), cuts through frames 0-5, holds the end of the cut a beat (where
hit-stop lands), then follows through and recovers into the guard; the
next swing may cut that short.

- sword_back: backhand, her left to her right (the game's first swing).
- sword_fore: forehand, her right to her left.
- sword_heavy: a full turn from the hips, low and wide, for the wide arcs.

The buckler never drops: through every cut it stays up before her, riding
the turn of her body.

Hands are placed on arcs about the shoulder in the chest's frame, so the
blade travels round her, not through her; the blade points out along the
cut, edge leading.
"""
from __future__ import annotations

import numpy as np

from gait import arc_of
from keyed import STRIKE, build


def _n(*v):
    v = np.array(v, float)
    return tuple(v / np.linalg.norm(v))


def feet(weight=0.0, pivot=0.0):
    """A fighting stance, left foot forward (the buckler's side); weight
    -1 back on the right, +1 onto the left; pivot: the back heel turning
    out as the hips come round."""
    return {
        "foot_l": {"pos": (0.15, 0, 0.17), "rot": (12, 0, 0)},
        "foot_r": {"pos": (-0.17, 0.0 + 0.03 * max(pivot, 0), -0.13), "rot": (-25 - 20 * pivot, 0, 0), "toe": 25 * max(pivot, 0)},
        "hips": {"pos": (0.03 * weight, -0.07 - 0.02 * abs(weight), 0.02 * weight)},
    }


# The buckler's hand in the guard (chest frame, from the shoulder) and its elbow's way: out
# ahead, the elbow open at 122 degrees (at (-0.12, -0.26, 0.22) it closed to 101 and the rim
# cut her upper arm 14/25 mm and sat on her pauldron).
GUARD_L_AT = (-0.07, -0.22, 0.34)
GUARD_L_POLE = (1.0, -0.5, -0.4)


def shield_l(at, pole):
    """The buckler's hand at `at` (chest frame, from the shoulder), the elbow `pole`'s way."""
    return {"arc": arc_of(at), "pole": pole, "frame": "chest", "blade": _n(-0.3, 0.75, 0.6), "twist": 0.3}


def guard_l(lift=0.0):
    """The buckler held up before her, a little to the left."""
    x, y, z = GUARD_L_AT
    return shield_l((x, y + lift, z), GUARD_L_POLE)


def with_shield(keys, track):
    """The buckler keyed on its own [(frame, hand, elbow's way, ease)]: set in the body's key of the
    same frame, or a key of its own between them."""
    keys = [(t, dict(p), e) for t, p, e in keys]
    at_t = {t: k for k, (t, _, _) in enumerate(keys)}
    for t, at, pole, e in track:
        if t in at_t:
            keys[at_t[t]][1]["hand_l"] = shield_l(at, pole)
        else:
            keys.append((t, {"hand_l": shield_l(at, pole)}, e))
    return sorted(keys, key=lambda k: k[0])


def pose(hips_yaw, spine_yaw, hand, blade, pole=(-0.7, -0.5, -0.3), left=None, pitch=6, roll=0, head=None,
         weight=0.0, pivot=0.0, fingers="grip"):
    p = feet(weight, pivot)
    p["hips"]["rot"] = (hips_yaw, 4, 0)
    p["spine"] = (spine_yaw, pitch, roll)
    # The head keeps on the foe: it turns against the back.
    p["head"] = head if head is not None else (-(hips_yaw + spine_yaw) * 0.6, -4, 0)
    p["hand_r"] = {"arc": arc_of(hand), "blade": blade, "pole": pole, "frame": "chest", "twist": 0.5}
    if left is not False:
        p["hand_l"] = left or guard_l()
    p["fingers_r"] = fingers
    p["fingers_l"] = "fist"
    return p


GUARD = pose(0, 0, (-0.05, -0.30, 0.20), _n(-0.25, 0.65, 0.7), pole=(-0.6, -0.4, -0.6))


# The buckler through each cut: its own keys (frame, hand, elbow's way, ease), chest frame
# from the shoulder.
BACK_L = [
    (0, (0.12, -0.24, 0.33), (1.0, -0.6, -0.3), "fast"),
    (2.5, (0.10, -0.26, 0.34), (1.0, -0.6, -0.3), "linear"),
    (5, (0.16, -0.16, 0.34), (1.0, -0.6, -0.3), "ease"),
    (8, (0.16, -0.16, 0.34), (1.0, -0.6, -0.3), "ease"),
    (15, GUARD_L_AT, GUARD_L_POLE, "auto"),
    (24, GUARD_L_AT, GUARD_L_POLE, "ease"),
]
FORE_L = [
    (0, (-0.04, -0.20, 0.36), (1.0, -0.5, -0.4), "fast"),
    (2.5, (0.04, -0.18, 0.37), (1.0, -0.5, -0.3), "linear"),
    (5, (0.17, -0.04, 0.36), (1.0, -0.6, -0.5), "ease"),
    (13, (0.17, -0.04, 0.36), (1.0, -0.6, -0.5), "ease"),
    (19, (0.0, -0.20, 0.36), (1.0, -0.5, -0.4), "auto"),
    (24, GUARD_L_AT, GUARD_L_POLE, "ease"),
]
HEAVY_L = [
    (0, (-0.02, -0.18, 0.37), (1.0, -0.5, -0.4), "fast"),
    (3, (0.04, -0.18, 0.37), (1.0, -0.5, -0.3), "linear"),
    (6, (0.19, 0.0, 0.35), (1.0, -0.6, -0.5), "ease"),
    (15, (0.19, 0.0, 0.35), (1.0, -0.6, -0.5), "ease"),
    (22, (0.02, -0.18, 0.37), (1.0, -0.5, -0.4), "auto"),
    (30, GUARD_L_AT, GUARD_L_POLE, "ease"),
]
BACK_COCK = (0.28, 0.10, 0.26)   # the cocked fist off her chest (at (0.30, 0.02, 0.10) the hilt was 11 mm into it)


def _fill(keys):
    """(body-b-skill-clips, 17 Nov) A key that sets only the buckler or one foot (with_shield's own keys, _land's step)
    carries each turn it leaves out as the keys that do set it give it at that frame: keyed's Track reads a turn or
    offset a key leaves out as none (hips, spine, head, the feet's turns at zero), and the hips dropping to zero there
    (fore f11-12 and f17-18: the pelvis up 8 cm, 19 deg round) locked the front knee straight for frames and bent it
    again in one (calf_l 29 deg at fore f13). Places (a foot's, a hand's) were already eased between the keys."""
    from keyed import _flatten, _hermite, _unflatten, _zero_default
    flats = [_flatten(p) for _, p, _ in keys]
    names = {n for f in flats for n in f if _zero_default(n) and isinstance(f[n], float)}
    out = []
    for (t, p, e), f in zip(keys, flats):
        miss = [n for n in names if n not in f]
        if miss:
            f = dict(f)
            for n in miss:
                have = [(k[0], g[n], k[2]) for k, g in zip(keys, flats) if n in g]
                f[n] = _hermite([h[0] for h in have], [h[1] for h in have], [h[2] for h in have], t)
            p = _unflatten(f)
        out.append((t, p, e))
    return out


def _build(name, rig, keys, meta, pin_first=0, pin_path=None):
    return build(name, rig, _fill(keys), lead=STRIKE, meta=meta, pin_first=pin_first, pin_path=pin_path)


def _body(p):
    return {k: v for k, v in p.items() if k != "hand_l"}


_PROWL = {}


def prowl_end(rig):
    """(aim-move, the owner 15 Nov: her idle out of town is Prowl, and every skill lands on it.) Prowl's frame 0 as
    keys (clips/prowl.end_keys: body, feet, both hands in the chest frame, fingers): the swings' recovery ends there,
    the blade let down to its trail at her right, not raised into the old high guard. None with WARDEN_IDLE=old."""
    import os
    if os.environ.get("WARDEN_IDLE", "prowl") != "prowl":
        return None
    if id(rig) not in _PROWL:
        from clips import idle, prowl
        # (solver 6a) the skills hold at grip tilt 0: keyed to land the idle's hand bone (the blade then turns in her
        # fist by the idle's tilt as the game eases it over the fade)
        _PROWL[id(rig)] = prowl.end_keys(rig, fingers_l=idle.warden(0, 0)["fingers_l"], tilt=0.0)
    return {k: (dict(v) if isinstance(v, dict) else v) for k, v in _PROWL[id(rig)].items()}


def _land(keys, rig, step=None):
    """The last key (the guard) made Prowl's; `step` = (frame, rise): her right foot lifted that much at that frame on
    its way from the stance's place to Prowl's (it is 7 cm back and 22 degrees out from the stance's), not slid."""
    end = prowl_end(rig)
    if end is None:
        return keys
    t, _, e = keys[-1]
    keys = keys[:-1] + [(t, end, e)]
    if step:
        f, rise = step
        a = np.array(feet()["foot_r"]["pos"], float); b = np.array(end["foot_r"]["pos"], float)
        mid = (a + b) / 2 + np.array([0, rise, 0])
        keys.append((f, {"foot_r": {"pos": tuple(mid), "rot": ((-25 + end["foot_r"]["rot"][0]) / 2, 0, 0), "toe": 0}}, "auto"))
        keys.sort(key=lambda k: k[0])
    return keys


def sword_back(rig):
    keys = [
        # Cocked: the blade drawn back across her to the left, high; hips and
        # back wound to the left.
        (0, pose(18, 30, BACK_COCK, _n(0.55, 0.6, -0.55), pole=(-0.4, 0.3, 0.8), left=False, weight=0.4, pitch=4), "fast"),
        # Through the middle at full reach, the blade level and leading.
        (2.5, pose(4, 4, (-0.08, -0.12, 0.46), _n(0.05, 0.5, 0.86), pole=(-0.6, -0.6, 0.0), left=False, weight=0.0), "linear"),
        # Out to her right: the cut ends.
        (5, pose(-16, -32, (-0.36, -0.14, 0.30), _n(-0.93, 0.26, 0.24), pole=(-0.2, -1.0, 0.2), left=False, weight=-0.5), "ease"),
        # Held, the blade carrying on a hair (the weight of it).
        (8, pose(-19, -38, (-0.38, -0.18, 0.24), _n(-0.99, 0.04, -0.05), pole=(-0.1, -1.0, 0.3), left=False, weight=-0.6), "ease"),
        # Recovering: the blade comes round and up into the guard.
        (15, pose(-6, -10, (-0.15, -0.26, 0.24), _n(-0.34, 0.51, 0.79), pole=(-0.6, -0.5, -0.4), left=False, weight=-0.2), "auto"),
        (24, _body(GUARD), "ease"),
    ]
    if prowl_end(rig) is not None:
        # (aim-move) Out of the cut at her right the blade drops on down to its trail, not up into the guard and down again.
        keys[4] = (15, pose(-10, -18, (-0.30, -0.32, 0.16), _n(-0.9, -0.38, 0.2), pole=(-0.3, -0.9, 0.2), left=False, weight=-0.4), "auto")
    keys = with_shield(keys, BACK_L)
    keys = _land(keys, rig, step=(20, 0.035))
    # (body-b-skill-clips) pin_first: frame 0's right elbow is the cocked key's own (the pole's), eased into the
    # smoothed path over two frames; smoothed, the cut's later elbows drew it in and the arm sat 19 mm into her trunk (A).
    return _build("sword_back", rig, keys, meta={"layer": "upper", "contact": 2.5 / 30, "weapon": "sword+shield"},
                  pin_first={"r": 2})


def sword_fore(rig):
    keys = [
        # Cocked over the right shoulder, the back wound to the right.
        (0, pose(-18, -32, (-0.20, 0.10, 0.14), _n(-0.3, 0.79, -0.69), pole=(-0.8, -0.2, -0.5), left=False, weight=-0.4), "fast"),
        (2.5, pose(-3, -4, (-0.125, -0.0925, 0.46), _n(0.015, 0.49, 0.88), pole=(-0.8, 0.0, 0.0), left=False, weight=0.0), "linear"),
        # Out to her left, across her: the cut ends low.
        (5, pose(16, 30, (0.12, -0.12, 0.45), _n(0.9, 0.0175, 0.0), pole=(-1.0, 0.3, 0.2), left=False, weight=0.6, pivot=0.6), "ease"),
        (8, pose(19, 36, (0.10, -0.17, 0.44), _n(0.86, -0.26, -0.17), pole=(-1.0, 0.3, 0.2), left=False, weight=0.7, pivot=0.7), "ease"),
        (15, pose(6, 10, (0.02, -0.28, 0.24), _n(0.2, 0.5, 0.8), pole=(-0.6, -0.5, -0.4), left=False, weight=0.2, pivot=0.2),
         "auto"),
        (24, _body(GUARD), "ease"),
    ]
    keys = with_shield(keys, FORE_L)
    keys = _land(keys, rig, step=(20, 0.035))
    return _build("sword_fore", rig, keys, meta={"layer": "upper", "contact": 2.5 / 30, "weapon": "sword+shield"})


def sword_heavy(rig):
    keys = [
        # Wound far round to the right and low.
        (0, pose(-30, -40, (-0.30, -0.20, 0.06), _n(-0.6, 0.1, -0.8), pole=(-0.6, -0.8, 0.0), left=False, weight=-0.7, pitch=14), "fast"),
        (3, pose(-6, -8, (-0.165, -0.14, 0.47), _n(-0.4, 0.29, 1.0), pole=(-0.9, 0.2, 0.1), left=False, weight=0.0, pitch=12), "linear"),
        # All the way round to her left, the whole back behind it.
        (6, pose(26, 44, (0.16, -0.06, 0.46), _n(0.95, 0.175, 0.075), pole=(-1.0, 0.3, 0.2), left=False, weight=0.8, pivot=1.0, pitch=10), "ease"),
        (10, pose(30, 50, (0.12, -0.12, 0.45), _n(0.8, -0.25, -0.3), pole=(-1.0, 0.3, 0.2), left=False, weight=0.9, pivot=1.0, pitch=10), "ease"),
        (19, pose(10, 14, (0.04, -0.28, 0.24), _n(0.2, 0.5, 0.8), pole=(-0.6, -0.5, -0.4), left=False, weight=0.3, pivot=0.3), "auto"),
        (30, _body(GUARD), "ease"),
    ]
    keys = with_shield(keys, HEAVY_L)
    keys = _land(keys, rig, step=(25, 0.035))
    if prowl_end(rig) is not None:
        # (aim-move solver 7) Prowl reached a frame early and held: solve_frames smooths each elbow's way over +-6
        # frames, one-sided at a clip's end, so a recovery still turning into its last key (3.7 deg a frame) left the
        # hand 12.2 deg off the idle's frame 0 (the back and fore cuts 4.0). Held from 29 it lands 4.0 off, easing in
        # (0.2 deg the last frame); the cut's own elbows keep their smoothing (elbow_sigma 1 also gave 4.0, clip-wide).
        import os
        hold = float(os.environ.get("SWORD_HEAVY_HOLD", "29"))
        keys = sorted(keys + [(hold, prowl_end(rig), "ease")], key=lambda k: k[0])
    meta = {"layer": "upper", "contact": 3 / 30, "weapon": "sword+shield"}
    if prowl_end(rig) is not None:
        # (aim-move solver 9a) The cut keys her hand 170 deg about the forearm at f4 (past the 95 it turns; the swivel at
        # its 42 edge), and keyed's twist, taken nearest the last frame's, read f5's -41 as 319: from there every frame
        # sat a whole turn up, pinned at +95 (f30 keyed 68: the hand 27.6 deg off the idle's, the forearm 11.8). Let go
        # over 24-29 (keyed meta "twist_unwind"): the end lands 4.0 / 4.7, the twist easing one way 95 -> 72 (f29, its
        # keys' 68 at f30), the hand's turn f19-30 at most 13.2 deg a frame (was 17.1); f0-24 as before.
        meta["twist_unwind"] = [24, 29]
    return _build("sword_heavy", rig, keys, meta=meta)


def clips(rig, want):
    out = []
    for name, fn in (("sword_back", sword_back), ("sword_fore", sword_fore), ("sword_heavy", sword_heavy),
                     ("sword_guard", None)):
        if want and not any(w in name for w in want):
            continue
        if fn:
            out.append(fn(rig))
    return out
