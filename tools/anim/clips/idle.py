"""Her signature idles: a captured way of standing (100STYLE, CC BY 4.0) for
each calling's body, the arms re-solved to hold what that calling holds,
its way. The capture brings the weight shifts and the breath; the arms
ride the chest as it moves.

- Warden: Heavyset (tensed, square, settled). The shield at rest at her
  left side, its face turned a little to the front, off her body; the
  sword low at her right, point toward the ground ahead.
- Arcanist: Strutting (chin up, a little back, at ease). The staff upright
  at her side, the free hand on her hip.
- Reaver: Angry (tense, restless). The axe on her shoulder, its head
  behind her, the left hand a fist.
- Stalker: Crouched (low, ready). The crossbow low across her, the left
  hand under its stock.
"""
from __future__ import annotations

import math

import numpy as np

from clips.mocap import idle_loop
from gait import arc_of
from rig import Clip


def layered(name, rig, base: Clip, over, meta=None) -> Clip:
    """A clip with every frame of `base` under the controls `over(t, frame)`
    gives (hands, fingers, any extra turns)."""
    from keyed import solve_frames
    n = base.frames
    rot, pos = solve_frames(rig, [over(f / max(n - 1, 1), f) for f in range(n)], [(base.rot[f], base.pos[f]) for f in range(n)],
                            loop=base.loop, weapon=(meta or {}).get("weapon", ""))
    m = dict(base.meta)
    m.update(meta or {})
    return Clip(name, base.fps, rot, pos, loop=base.loop, meta=m)


def _n(v):
    v = np.array(v, float)
    return tuple(v / np.linalg.norm(v))


# Her sword hand at rest (chest frame), shared with the stops (sprint_stop.py).
WARDEN_HAND_R = (-0.09, -0.45, 0.04)


def warden(t, f):
    breath = 0.008 * math.sin(2 * math.pi * t * 2)
    return {
        # The shield at rest at her left side, off her body: the elbow out
        # about 19 degrees, the upper arm back about 14 and bent about 58, the
        # forearm forward and about 50 degrees down, turned in about 10, so
        # the shield's face (the back of the forearm) looks out to her
        # left-front about 15 degrees, its plane near upright. The shield is
        # strapped low on the forearm, its boss over her wrist, so its top rim
        # sits about 145 cm up, level with her armpit and the top of her cup,
        # with air under the shoulder armour, and its bottom is 8 cm or more
        # clear of her hip and thigh. The wrist straight, the fist on the
        # strap; the forearm turned palm-up a little (the whole roll in the
        # forearm, which carries the shield), not wrung at the wrist.
        # (Carried across her body, the 66 cm shield sank 5 cm into her
        # breast and trunk.) The upper arm turned 8 degrees out about its
        # length (judges 46-47): the rim clear of her cup's outline from the
        # front by 2-5 cm. In the game the forearm bone keeps to its hinge
        # (HerJoints hands its roll to the hand), so the shield on it does not
        # take the forearm's roll: measure with the helpers driven.
        "hand_l": {"arc": arc_of((0.0817, -0.3796 + breath, 0.1299)), "pole": (0.3281, -0.4168, -0.8477), "frame": "chest",
                   "thumb": (-0.1498, 0.7455, 0.6495), "twist": 1.0},
        # The sword low at her right, its point 34 degrees below the chest's
        # level ahead and a little out: the hand near in line with the
        # forearm, its thumb forward, the turn shared by the forearm and the
        # wrist. The elbow swung 25 degrees out and forward about the
        # shoulder-wrist line (pole), so the forearm comes down over the
        # hilt: wrist flex -12, toward the little finger 19 (animation
        # 31: with the elbow back and the point 39 down the wrist sat 32 toward
        # the little finger, "a very weird angle at the wrists"; the swing alone
        # gets no lower than 23). (Keyed by the blade alone, the wrist cocked
        # back 42 degrees and 34 to the side.)
        "hand_r": {"arc": arc_of(WARDEN_HAND_R), "pole": (-0.744, 0.09, -0.662), "frame": "chest",
                   "blade": _n((-0.142, -0.560, 0.816)), "knuckles": _n((0.123, -0.828, -0.548)), "twist": 0.5},
        # The left thumb closed round the grip, swung in across the palm
        # (judge 47: held straight, it showed between the rim and her skirt).
        "fingers_l": {"curl": 0.95, "cascade": 0.05, "thumb": 1.6, "oppose": 0.9}, "fingers_r": "grip",
    }


# Her free hand on her hip (15 Oct, animation 30; judge l30-r1 chose it over the hand on the thigh: "a confident witch
# silhouette", the thigh hand read limp at the game camera). The palm on the front-side of her hip above the hip bone,
# fingers forward and down over it, the fan closed (index-middle 0.5 mm, ring-little 2.5), the thumb forward along the
# forefinger (r2: not a straight peg out of the glove: base 15, end 22, 22 deg off the index); elbow out ~107, back
# ~95. Wrist flex -13..-14, dev -2..+5. Every part 1.1-2.5 mm off what it lies on (the leotard's outer face, ~7-9 mm
# off her skin there; the trim; the little finger on bare skin past the leg opening). Kept on her pelvis as she sways
# (idle_arcanist, below): the wrist (character space at rest) and the hand's way in the pelvis's frame.
ARC_HIP = {"pos": (0.17502, 1.18299, 0.03956), "knuckles": (-0.3373, -0.70768, 0.62077), "blade": (-0.23811, 0.70218, 0.671)}
ARC_HIP_FINGERS = {"thumb": 0.1, "oppose": 0.05, "thumb_in": 15.4, "thumb_roll": -23.6,
                   "bends": {"index": [25.268, 25.268, 12.629], "middle": [23.594, 23.594, 11.792],
                             "ring": [23.795, 23.795, 11.892], "pinky": [17.923, 24.487, 11.913], "thumb": [0.5, 15.2, 22.1]},
                   "spreads": {"index": -13.35, "middle": 0.0, "ring": 8.3, "pinky": 13.4}}


def _arc_hand_fingers():
    from keyed import FINGER_PRESETS
    return dict(FINGER_PRESETS["relaxed"], **ARC_HIP_FINGERS)


def arcanist(t, f):
    return {
        # (ARC_HIP at the captured standing's first frame, in the chest's frame, for the clips that take the idle's
        # arms as they are: its breaks, the stops, the Flare's settle.)
        "hand_l": {"arc": arc_of((-0.0251, -0.3226, 0.1052)), "pole": (1.0, 0.032, -1.243), "frame": "chest",
                   "knuckles": _n((-0.3849, -0.4502, 0.8057)), "blade": _n((-0.1819, 0.8929, 0.4120)), "twist": 0.3},
        # The staff upright at her side, its head leaning in a little and its foot out past her right leg
        # (13 Oct: on the seated bound staff, blade (-0.12, 1.0, 0.18) crossed its lower half behind her right
        # thigh and calf every frame; now >= 10 mm off her legs and her hat).
        # (18 Oct, animation 38: the grip 7 cm forward and the elbow's pole turned down and in, from (0.12 forward,
        # pole (-0.8, -0.3, -0.6)): at the close-up the elbow stood cocked out and back; now 20 deg out of her
        # side, not 32 (the hip arm's 26), 85 mm out from the shoulder, not 132, and 15 deg back, not 35.)
        "hand_r": {"arc": arc_of((-0.16, -0.28, 0.19)), "pole": (-0.2, -0.6, -0.75), "frame": "chest",
                   "blade": _n((0.03, 1.0, 0.06)), "twist": 0.5},
        "fingers_l": _arc_hand_fingers(), "fingers_r": "grip",
    }


def _on_hip(rig, base, arms):
    """`arms` with the left hand kept on her pelvis (ARC_HIP) frame by frame, in the chest's frame the solver reads."""
    from rig import qmul, qinv, qrot
    I = rig.I
    grest, prest = (a[0] for a in rig.sk.rest_globals())
    pel, s3, ua = I["pelvis"], I["spine_03"], I["upperarm_l"]
    g, p = rig.sk.fk(base.rot, base.pos)

    def over(t, f):
        d = dict(arms(t, f))
        dp = qmul(g[f, pel], qinv(grest[pel]))
        ic = qinv(qmul(g[f, s3], qinv(grest[s3])))
        W = p[f, pel] + qrot(dp, np.array(ARC_HIP["pos"]) - prest[pel])
        d["hand_l"] = dict(d["hand_l"], arc=arc_of(qrot(ic, W - p[f, ua])),
                           knuckles=tuple(qrot(ic, qrot(dp, np.array(ARC_HIP["knuckles"])))),
                           blade=tuple(qrot(ic, qrot(dp, np.array(ARC_HIP["blade"])))))
        return d
    return over


def hip_layer(rig, clip, w, curl=None, thumb_pow=1.0):
    """`clip` with her left hand laid on her hip (ARC_HIP, idle_arcanist's) where the weight w(frame) > 0, kept on
    the clip's OWN pelvis frame by frame, and the left arm and fingers slerped by w from the clip's own into it.
    For the clips that took the idle's frame-0 hand in the chest's frame (the breaks, the stops, the Flare's settle,
    the flourish): there the hand floated 3-17 mm off her hip, or sank into it, as her hips moved under the chest.
    `curl` ({finger: [deg per frame]}): each finger closed that much more (0.6 at the knuckle, 0.4 at the middle
    joint; opened at the knuckle alone) where the clip's legs move the surface under it (the stops; following the thigh instead sank the thumb).
    `thumb_pow`: the left thumb's joints slerped by w**thumb_pow instead of w, so the thumb takes the clip's own shape
    before the hand leaves her hip (the Flare's reach: at w 0.25, f4, her glove's thumb sleeve folded 1.3 mm into
    her hand's thenar)."""
    from keyed import solve_frames
    from rig import qmul, qinv, qrot, qslerp
    I = rig.I
    grest, prest = (a[0] for a in rig.sk.rest_globals())
    pel, s3, ua = I["pelvis"], I["spine_03"], I["upperarm_l"]
    g, p = rig.sk.fk(clip.rot, clip.pos)
    n = clip.frames
    ws = [min(1.0, max(0.0, float(w(f)))) for f in range(n)]
    thumb = {I[f"thumb_0{q}_l"] for q in (1, 2, 3)}
    arm = [ua]
    for j in arm:
        arm += [k for k, q in enumerate(rig.sk.parent) if q == j and k not in arm]
    hand0 = arcanist(0, 0)["hand_l"]

    def fingers(f):
        fx = _arc_hand_fingers()
        if curl:
            b = {k: list(v) for k, v in fx["bends"].items()}
            for k, c in curl.items():
                d = c[min(f, len(c) - 1)]
                # (Opened, all at the knuckle: the finger lifts off from its base; opening the middle joint too
                # took the little finger's middle bone into her thigh.)
                b[k][0] += 0.6 * d if d > 0 else d
                b[k][1] += 0.4 * d if d > 0 else 0.0
            fx = dict(fx, bends=b)
        return fx

    def spec(f):
        dp = qmul(g[f, pel], qinv(grest[pel]))
        ic = qinv(qmul(g[f, s3], qinv(grest[s3])))
        W = p[f, pel] + qrot(dp, np.array(ARC_HIP["pos"]) - prest[pel])
        return {"hand_l": dict(hand0, arc=arc_of(qrot(ic, W - p[f, ua])),
                               knuckles=tuple(qrot(ic, qrot(dp, np.array(ARC_HIP["knuckles"])))),
                               blade=tuple(qrot(ic, qrot(dp, np.array(ARC_HIP["blade"]))))),
                "fingers_l": fingers(f)}
    # Each run of weighted frames solved on its own (the solver settles the elbow over the frames it is given).
    f = 0
    while f < n:
        if ws[f] <= 0:
            f += 1
            continue
        e = f
        while e < n and ws[e] > 0:
            e += 1
        idx = list(range(f, e))
        rot, _ = solve_frames(rig, [spec(k) for k in idx], [(clip.rot[k], clip.pos[k]) for k in idx],
                              weapon=(clip.meta or {}).get("weapon", ""))
        for i, k in enumerate(idx):
            for j in arm:
                clip.rot[k, j] = qslerp(clip.rot[k, j], rot[i, j], ws[k] ** thumb_pow if j in thumb else ws[k])
        f = e
    return clip


def _smooth(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)


def reaver(t, f):
    return {
        # The axe on her shoulder, its head behind her.
        "hand_r": {"arc": arc_of((-0.03, -0.13, 0.11)), "pole": (-0.6, -1.0, 0.0), "frame": "chest",
                   "blade": _n((-0.15, 0.35, -0.95)), "twist": 0.5},
        "hand_l": {"arc": arc_of((-0.02, -0.42, 0.06)), "pole": (0.4, 0.0, -1.0), "frame": "chest"},
        "fingers_r": "grip", "fingers_l": "fist",
    }


def stalker(t, f):
    return {
        # The crossbow low across her, pointing ahead and to her left, the
        # left hand under its stock.
        "hand_r": {"arc": arc_of((0.12, -0.38, 0.20)), "pole": (-0.7, -0.4, -0.5), "frame": "chest",
                   "knuckles": _n((0.5, -0.15, 0.85)), "twist": 0.5},
        "hand_l": {"arc": arc_of((-0.16, -0.42, 0.30)), "pole": (0.7, -0.4, -0.5), "frame": "chest",
                   "knuckles": _n((0.2, -0.2, 0.95)), "twist": 0.4},
        "fingers_r": "grip", "fingers_l": "relaxed",
    }


def stalker_daggers(t, f):
    """The stalker's idle with a dagger in each hand (the game asks for idle_<calling>_<kind> first: OwnClips.For). Her
    crossbow idle let the left hang "relaxed" round the second dagger, an open hand with the blade stuck to it (judge,
    17 October); here both fists close on their hilts (the daggers' fitted WRAP, the left's mirrored: keyed.wrap_of)."""
    return {**stalker(t, f), "fingers_l": "grip"}


def warden_town(t, f):
    """In town, her weapons sheathed (the sword at her left hip, the shield
    on her back): the arms hang free and easy at her sides, the elbows soft,
    the wrists straight (the thumb forward, the palm to the thigh), clear of
    her hips and skirt; a small counter-swing to the hips' sway."""
    sw = 0.012 * math.sin(2 * math.pi * t * 2)
    return {
        "hand_l": {"arc": arc_of((0.16, -0.46, 0.08 + sw)), "pole": (0.3, -0.2, -1.0), "frame": "chest",
                   "thumb": _n((-0.15, -0.1, 1.0)), "twist": 1.0},
        "hand_r": {"arc": arc_of((-0.14, -0.46, 0.08 - sw)), "pole": (-0.3, -0.2, -1.0), "frame": "chest",
                   "thumb": _n((0.15, -0.1, 1.0)), "twist": 1.0},
        "fingers_l": "relaxed", "fingers_r": "relaxed",
    }


IDLES = {
    "idle_warden": ("Heavyset", warden, "sword+shield"),
    "idle_arcanist": ("Strutting", arcanist, "staff"),
    "idle_reaver": ("Angry", reaver, "axe"),
    "idle_stalker": ("Crouched", stalker, "crossbow"),
    "idle_stalker_daggers": ("Crouched", stalker_daggers, "daggers"),
    # In town, weapons sheathed (the game asks for idle_<calling>_town).
    "idle_warden_town": ("WiggleHips", warden_town, ""),
}


_bases = {}
# An idle that stands on another's captured base (the same standing, other arms).
SHARES_BASE = {"idle_stalker_daggers": "stalker"}


def base_of(rig, calling):
    """A calling's captured standing (made once a run, shared by its idle,
    its breaks and its flourish)."""
    if calling not in _bases:
        style = IDLES[f"idle_{calling}"][0]
        _bases[calling] = idle_loop(f"idle_{calling}_base", rig, style, seconds=(5.0, 8.0))
    return _bases[calling]


def clips(rig, want):
    out = []
    for name, (style, arms, weapon) in IDLES.items():
        if want and not any(w in name for w in want):
            continue
        base = base_of(rig, SHARES_BASE.get(name, name[5:]))
        if arms is arcanist:
            arms = _on_hip(rig, base, arms)
        out.append(layered(name, rig, base, arms, {"weapon": weapon}))
    return out
