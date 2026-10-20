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


# Her left hand laid over the crossbow's fore-stock, palm down, a hand ahead of the right fist, the fingers over its
# far side; the elbow bent and hanging by her side (animation 38, 18 Oct). Under the stock (as keyed before) the fore-
# stock sits 55 cm from her shoulder, past her reach with the stock carried this low: the arm went straight across her
# and the upper arm 60 mm into her side and breast. Shared by the crossbow's shot and the stops (which end here).
# The crossbow's carry moved as one (both hands, chest frame, m): ahead of her, so its butt clears her waist.
STALKER_SHIFT = (0.0, 0.0, 0.06)
STALKER_HAND_L = {"hand_l": {"arc": arc_of(np.add((-0.058, -0.335, 0.255), STALKER_SHIFT)), "pole": (0.0, -0.5, -1.0), "frame": "chest",
                             "knuckles": _n((-0.71, 0.33, 0.63)), "blade": _n((-0.49, 0.41, -0.77)), "twist": 0.4}}


STALKER_HAND_R = {"hand_r": {"arc": arc_of(np.add((0.12, -0.38, 0.20), STALKER_SHIFT)), "pole": (-0.7, -0.4, -0.5),
                             "frame": "chest", "knuckles": _n((0.5, -0.15, 0.85)), "twist": 0.5}}


def stalker(t, f):
    return {
        # The crossbow low across her, pointing ahead and to her left, the
        # left hand laid over its fore-stock.
        **STALKER_HAND_R, **STALKER_HAND_L,
        "fingers_r": "grip", "fingers_l": "relaxed",
    }


_STOCK = {}
STOCK_DROP = 0.003


def _stock_rel(rig):
    """Her left hand on the fore-stock as the idle lays it (stalker(), the base's first frame), in her right hand's
    frame: (wrist offset, turn). Made once per body."""
    from keyed import grip_of
    from rig import qinv, qmul, qrot
    key = id(rig)
    if key not in _STOCK:
        base = base_of(rig, "stalker")
        grip0 = rig.grip
        rig.grip = grip_of("crossbow") if rig.grips else {}
        rig.swivel_force = {}
        local, pos = rig.solve(stalker(0, 0), base=(base.rot[0], base.pos[0]))
        rig.swivel_force = None
        rig.grip = grip0
        g, p = rig.globals(local, pos)
        hr, hl, s3 = rig.I["hand_r"], rig.I["hand_l"], rig.I["spine_03"]
        # (Laid STOCK_DROP lower onto the stock, in the chest's frame: the idle's first frame has her palm 4-5 mm
        # over it, where the loop's breath lays it 1.5-4.5.)
        drop = qrot(qmul(g[0, s3], qinv(rig.grest[s3])), [0.0, -STOCK_DROP, 0.0])
        _STOCK[key] = (qrot(qinv(g[0, hr]), p[0, hl] + drop - p[0, hr]), qmul(qinv(g[0, hr]), g[0, hl]))
        # (And the crossbow's top there, in the chest's frame: a clip that keys the right hand's blade lands on it.)
        _STOCK[("top", key)] = tuple(float(x) for x in qrot(qinv(qmul(g[0, s3], qinv(rig.grest[s3]))), qrot(g[0, hr], [0, 0, 1.0])))
    return _STOCK[key]


def stalker_top(rig):
    """The crossbow's top (hand_r +Z) in her idle, in the chest's frame."""
    _stock_rel(rig)
    return _STOCK[("top", id(rig))]


# The fore-stock's centre line in hand_r's space (m): along +Y at this x, z (the stock 40 mm wide, its top at +z 0.09).
STOCK_AXIS = (-0.041, 0.045)


def cradle_rel(at, fingers=35.0, roll=0.0, lift=0.0, palm=0.020, reach=0.045):
    """A palm-up cradle under the fore-stock, in hand_r's space: (wrist offset, turn), as _stock_rel returns. at: the
    palm's centre (x, y, z; the stock's underside is z 0.00-0.02 from y 0.14 on); fingers: deg from the stock (+Y)
    toward its far side (+X); roll: deg the palm tips about the fingers toward her (-X, the heel of the hand down the
    near side); lift: deg the fingers rise toward the stock's top (+Z), up its far side. palm, reach: the palm's centre from the wrist's bone, out of the palm and along the fingers."""
    from rig import qfrom_basis
    a, r, l = math.radians(fingers), math.radians(roll), math.radians(lift)
    f = np.array([math.sin(a) * math.cos(l), math.cos(a) * math.cos(l), math.sin(l)])
    side = np.array([math.cos(a), -math.sin(a), 0.0])        # across the fingers, toward the far side
    up = np.cross(side, f)                                   # the palm's normal before the roll
    n = up * math.cos(r) - side * math.sin(r)                # the palm's normal (hand_l +X)
    z = np.cross(n, f)
    return (np.array(at, float) - reach * f - palm * n, qfrom_basis(n, f, z))


def blend_rel(a, b, t, via=None, out=0.0):
    """Between two of the left hand's relations to the stock: the wrist swung about the stock's centre line (round
    its near side, never through it), its turn slerped; via: a relation passed at t 0.5 (each half on its own), out:
    m the wrist stands off the stock at the middle (sin bump)."""
    from rig import qslerp
    if via is not None:
        p, q = (blend_rel(a, via, 2 * t) if t < 0.5 else blend_rel(via, b, 2 * t - 1))[:2]
        if out:
            c = np.array([STOCK_AXIS[0], p[1], STOCK_AXIS[1]])
            d = p - c
            p = p + d / max(1e-6, np.linalg.norm(d)) * out * math.sin(math.pi * t)
        return p, q
    (pa, qa), (pb, qb) = a[:2], b[:2]
    c = np.array([STOCK_AXIS[0], 0.0, STOCK_AXIS[1]])
    da, db = pa - c, pb - c
    ang = lambda d: math.atan2(d[2], d[0])
    ra, rb = math.hypot(da[0], da[2]), math.hypot(db[0], db[2])
    t1, t2 = ang(da), ang(db)
    t1 %= 2 * math.pi; t2 %= 2 * math.pi                     # (0 = +x far side, pi = the near side: no crossing 0)
    th = t1 + (t2 - t1) * t; rr = ra + (rb - ra) * t + out * math.sin(math.pi * t)
    p = c + np.array([rr * math.cos(th), da[1] + (db[1] - da[1]) * t, rr * math.sin(th)])
    return p, qslerp(qa, qb, t)


def ride_stock(rig, make, weight=lambda f: 1.0, rel=None):
    """A crossbow clip whose left hand rides the fore-stock wherever the crossbow goes (animation 38: keyed on its own
    arc from her shoulder, it parted from the stock or the stock swung through it as the two arms' arcs drifted apart:
    the crossbow 6-18 mm into her left hand in the shot, the show and the stops). make(post) builds the clip; the right
    hand's path is read from a first build and the left hand put where the idle lays it on the stock in the right
    hand's frame (weight(frame) 0..1: how far from its keyed place onto the stock)."""
    from rig import qinv, qmul, qrot
    idle_rel = _stock_rel(rig)
    c0 = make(None)
    g, p = rig.sk.fk(c0.rot, c0.pos)
    hr, s3 = rig.I["hand_r"], rig.I["spine_03"]
    tg = []
    for f in range(c0.frames):
        r = (rel(f, idle_rel) if rel else None) or idle_rel
        rel_p, rel_q = r[0], r[1]
        q = qmul(g[f, hr], rel_q)
        tg.append((p[f, hr] + qrot(g[f, hr], rel_p), qrot(q, [0, 0, 1.0]), qrot(q, [0, 1.0, 0]),
                   qmul(g[f, s3], qinv(rig.grest[s3])), r[2] if len(r) > 2 else 1.0, r[3] if len(r) > 3 else None))

    def post(fr, pose):
        w = float(weight(fr))
        if w <= 0 or not isinstance(pose.get("hand_l"), dict):
            return pose
        pos, bl, kn, chest, aim, fingers = tg[min(fr, len(tg) - 1)]
        spec = dict(pose["hand_l"])
        if spec.get("frame") == "chest":
            bl, kn = qrot(qinv(chest), bl), qrot(qinv(chest), kn)
        for k, v in (("blade", bl), ("knuckles", kn)):
            if w < 1 and k in spec:
                v = np.array(spec[k], float) * (1 - w) + v * w
            spec[k] = tuple(float(x) for x in v / np.linalg.norm(v))
        spec.pop("thumb", None)
        spec["pos"] = tuple(float(x) for x in pos)
        spec["mix"] = w if "arc" in spec else 1.0
        if aim < 1.0:
            spec["aim"] = aim     # (rel's third: how far the hand is turned to it, 0 = riding the forearm)
        if fingers is not None:
            return {**pose, "hand_l": spec, "fingers_l": fingers}   # (rel's fourth: the left fingers there)
        return {**pose, "hand_l": spec}
    return make(post)


def stalker_daggers(t, f):
    """The stalker's idle with a dagger in each hand (the game asks for idle_<calling>_<kind> first: OwnClips.For). Her
    crossbow idle let the left hang "relaxed" round the second dagger, an open hand with the blade stuck to it (judge,
    17 October); here both fists close on their hilts (the daggers' fitted WRAP, the left's mirrored: keyed.wrap_of)."""
    # Her own arms (animation 38: on the crossbow's, the right dagger lay 20 mm into her left hand): a relaxed ready
    # stance, both fists low ahead of her hips, a hand's width apart, the elbows soft by her sides, the wrists
    # straight and the forearms rolled so the blades rise forward and a little out (the left a little ahead, over
    # her leading foot).
    return {"hand_r": {"arc": arc_of(DAGGERS_HAND_R), "pole": (-0.7, -0.5, -0.4), "frame": "chest",
                       "thumb": _n((-0.25, 0.75, 0.6)), "twist": 0.5},
            "hand_l": {"arc": arc_of(DAGGERS_HAND_L), "pole": (0.7, -0.5, -0.4), "frame": "chest",
                       "thumb": _n((0.25, 0.75, 0.6)), "twist": 0.5},
            "fingers_r": "grip", "fingers_l": "grip"}


# The daggers' ready fists (chest frame, from each shoulder, m).
DAGGERS_HAND_R = (0.05, -0.34, 0.24)
DAGGERS_HAND_L = (-0.05, -0.33, 0.27)


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


def free_arms(hand_l=(0.16, -0.46, 0.08), hand_r=(-0.14, -0.46, 0.08), reach=1.0, swing=0.012, pole_l=(0.3, -0.2, -1.0),
              pole_r=(-0.3, -0.2, -1.0)):
    """warden_town's free arms for another calling's town stand (its weapons sheathed): each hand (chest frame, from
    the shoulder) moved clear of what that calling wears sheathed, `reach` the arm let out (1.025: the elbows soft at
    20-25 deg, not 35), the same small counter-swing to the hips' sway."""
    hl, hr = np.array(hand_l, float) * reach, np.array(hand_r, float) * reach

    def arms(t, f):
        sw = swing * math.sin(2 * math.pi * t * 2)
        return {
            "hand_l": {"arc": arc_of(hl + (0, 0, sw)), "pole": pole_l, "frame": "chest", "thumb": _n((-0.15, -0.1, 1.0)), "twist": 1.0},
            "hand_r": {"arc": arc_of(hr - (0, 0, sw)), "pole": pole_r, "frame": "chest", "thumb": _n((0.15, -0.1, 1.0)), "twist": 1.0},
            "fingers_l": "relaxed", "fingers_r": "relaxed",
        }
    return arms


# Her town stands (animation 44): warden_town's base, the WiggleHips take (the owner, 19 Oct: "I adore the idle sway"),
# another stretch of it each (TOWN_WINDOW, seconds into the take), her arms free and clear of her sheathed pieces.
TOWN = {
    # The axe (or two) on the hip loop at her right (and left) hip: the hands a little ahead of the heads.
    "reaver_town": free_arms(hand_r=(-0.16, -0.46, 0.035), reach=1.03),
    # The wand on the belt at her right hip.
    "arcanist_town": free_arms(reach=1.03),
    # The crossbow slung on her back, the daggers at the back of her belt.
    "stalker_town": free_arms(reach=1.03),
}
# A staff stays in her hand in town (WeaponSockets.SocketOf: a walking staff), slid STAFF_WALK down through her fist
# along its line (Arms.Walking, WeaponSockets.StaffWalk: m, hand_r's space, along FistDirR).
STAFF_WALK = 0.26
def staff_town(t, f):
    """The staff upright at her right side as her armed stand holds it (idle_arcanist's arm: the grip forward of her
    hip, the elbow easy by her side), a little lower, riding her chest as she sways; slid down through her fist
    (STAFF_WALK) so its foot hangs a hand off the ground. The left arm free. (Planted on the ground it cannot be: on
    the fitted fist's diagonal, WRAP["staff"], the shaft runs head-toward-the-fingers, so an upright staff needs the
    forearm near level and the wrist at 1.1 m or more, and the plain shaft above the drawn grip allows a slide of
    25 cm at most before her fingers reach the head: its foot stays 15 cm or more up. A pinned staff in her root
    frame drifted 24 cm, the wrist unable to hold its line as she swayed.)"""
    d = free_arms(reach=1.03)(t, f)
    # (The wrist rides her chest, the staff's line is kept in her character's space, "char": on the chest's, its foot
    # swung 57 cm across as the WiggleHips chest rolls.)
    d["hand_r"] = {"arc": arc_of((-0.16, -0.31, 0.18)), "pole": (-0.2, -0.6, -0.75), "frame": "char",
                   "blade": _n((0.03, 1.0, 0.06)), "twist": 0.5}
    d["fingers_r"] = "grip"
    return d


# (staff_town is not shipped: it needs a walking-staff fist fit, a later item.)
# (Animation 44, solver idle 2: the arcanist's stretch from (4, 12) to (2, 10), 100STYLE frames 876-1218: on the old one
# the chest rolled against her hips, so her right wrist rose 13 cm to her hip's height and out at 25/75 %; on this one
# it rides her hip as the warden's does, 26-28 cm out of the hip joint and within 5 cm of its height; the warden's
# 26-27 and 2. It shares 3 s with the reaver's (frames 744-1050), 2.2 s out of phase.)
TOWN_WINDOW = {"reaver_town": (0, 8), "arcanist_town": (2, 10), "stalker_town": (9, 16)}


def level_head(rig, clip: Clip, keep=0.4) -> Clip:
    """Her head's mean tilt to one side taken down to `keep` of itself (the take's sway of it kept): the WiggleHips
    stretches hold the head 3-8 deg toward one shoulder, more on some stretches than on warden_town's."""
    from rig import qinv, qmul, qrot
    sk = rig.sk
    h = sk.i("Head")
    grest = sk.rest_globals()[0][0]
    g, _ = sk.fk(clip.rot, clip.pos)
    left = np.array([qrot(qmul(g[f, h], qinv(grest[h])), [1.0, 0, 0]) for f in range(clip.frames)])
    roll = float(np.degrees(np.mean(np.arcsin(np.clip(left[:, 1], -1, 1)))))
    turn = qaxis_((0.0, 0.0, 1.0), -(1 - keep) * roll)
    rot = clip.rot.copy()
    par = sk.parent[h]
    for f in range(clip.frames):
        rot[f, h] = qmul(qinv(g[f, par]), qmul(turn, g[f, h]))
    return Clip(clip.name, clip.fps, rot, clip.pos, loop=clip.loop,
                meta={**clip.meta, "changes": clip.meta.get("changes", "") + f"; head's mean tilt {roll:+.1f} deg taken to {keep:.0%}"})


def qaxis_(axis, deg):
    from rig import qaxis
    return qaxis(axis, deg)


IDLES = {
    "idle_warden": ("Heavyset", warden, "sword+shield"),
    "idle_arcanist": ("Strutting", arcanist, "staff"),
    "idle_reaver": ("Angry", reaver, "axe"),
    "idle_stalker": ("Crouched", stalker, "crossbow"),
    "idle_stalker_daggers": ("Crouched", stalker_daggers, "daggers"),
    # In town, weapons sheathed (the game asks for idle_<calling>_town).
    "idle_warden_town": ("WiggleHips", warden_town, ""),
    "idle_reaver_town": ("WiggleHips", TOWN["reaver_town"], ""),
    "idle_arcanist_town": ("WiggleHips", TOWN["arcanist_town"], ""),
    "idle_stalker_town": ("WiggleHips", TOWN["stalker_town"], ""),
}


_bases = {}
# An idle that stands on another's captured base (the same standing, other arms).
SHARES_BASE = {"idle_stalker_daggers": "stalker"}


# A captured standing stood up (18 Oct, the owner: the stalker "always crouching like they have to go to the
# bathroom"). The Crouched take's knees bent 55 deg with her hips 17 cm behind her feet and her chest 19 deg over; she
# keeps its breath and sway, her hips lifted and carried over the middle of her feet (the knees to about a third of
# the bend), the hips and everything above turned back so the chest leans a little and the head comes level, the legs
# reaching again for the same planted ankles. knee: the mean knee bend wanted (deg); over: the hips ahead of the
# middle of her feet, ankle to ball (m); pitch: the hips turned back (deg); width: her ankles apart (m; the take's,
# drawn in to her hips, were 14 cm apart, near touching once she stood); stagger: her left foot ahead of her right (m),
# a shooter's stance under the crossbow held across her.
STAND = {"stalker": {"knee": 19.0, "over": 0.03, "pitch": 10.0, "width": 0.21, "stagger": 0.05}}


def stand(rig, clip: Clip, knee, over, pitch, width=None, stagger=0.0) -> Clip:
    from rig import qaxis, qbetween, qinv, qmul, qrot, two_bone_ik
    sk = rig.sk
    rot, pos = clip.rot.copy(), clip.pos.copy()
    T = rot.shape[0]
    pel, root = sk.i("pelvis"), sk.i("root")
    g, p = sk.fk(rot, pos)
    ank = {s: p[:, sk.i(f"foot_{s}")].copy() for s in "lr"}
    ball = {s: p[:, sk.i(f"ball_{s}")] for s in "lr"}
    foot_g = {s: g[:, sk.i(f"foot_{s}")].copy() for s in "lr"}
    bend0 = {s: p[:, sk.i(f"calf_{s}")] - (p[:, sk.i(f"thigh_{s}")] + ank[s]) / 2 for s in "lr"}
    fwd = sum(ball[s] - ank[s] for s in "lr").mean(axis=0)
    fwd[1] = 0
    fwd /= np.linalg.norm(fwd)
    left = np.cross([0.0, 1.0, 0.0], fwd)
    side = 1.0 if np.mean(np.sum((ank["l"] - ank["r"]) * left, axis=1)) > 0 else -1.0
    apart = np.mean(np.abs(np.sum((ank["l"] - ank["r"]) * left, axis=1)))
    for s, k in (("l", 1.0), ("r", -1.0)):
        # The feet set out (a fixed offset each, so planted stays planted).
        d = left * side * k * ((width - apart) / 2 if width else 0.0) + fwd * k * stagger / 2
        ank[s] = ank[s] + d
        ball[s] = ball[s] + d
    mid = sum(ank[s] + ball[s] for s in "lr") / 4
    # The hips turned back about her left-right axis (a turn about `left` tips her up toward her front).
    turn = qaxis(left, -pitch)
    rot[:, pel] = qmul(qinv(g[:, root]), qmul(turn, g[:, pel]))
    # Carried forward over her feet (the sway about it kept), then the whole of her moved back so her hips sway about
    # the root as the take's did (in_place): her feet go back under her rather than her hips forward off the root.
    shift = fwd * (over - np.mean(np.sum((p[:, pel] - mid) * fwd, axis=1)))
    centre = p[:, pel].mean(axis=0) + shift
    centre[1] = 0.0
    for s in "lr":
        ank[s] = ank[s] - centre
    shift = shift - centre

    def legs(dy):
        r, q = rot.copy(), pos.copy()
        d = shift + np.array([0.0, dy, 0.0])
        q[:, pel] = q[:, pel] + qrot(qinv(g[:, root]), np.broadcast_to(d, (T, 3)))
        gl, gp = sk.fk(r, q)
        bends = []
        for s in "lr":
            th, ca, fo = sk.i(f"thigh_{s}"), sk.i(f"calf_{s}"), sk.i(f"foot_{s}")
            for t in range(T):
                a, b_, c_ = gp[t, th], gp[t, ca], gp[t, fo]
                k = bend0[s][t] / max(np.linalg.norm(bend0[s][t]), 1e-6)
                nb, nc = two_bone_ik(a, b_, c_, ank[s][t], (a + ank[s][t]) / 2 + k)
                r1 = qbetween(b_ - a, nb - a)
                gth = qmul(r1, gl[t, th])
                c2 = nb + qrot(r1, c_ - b_)
                gca = qmul(qbetween(c2 - nb, nc - nb), qmul(r1, gl[t, ca]))
                r[t, th] = qmul(qinv(gl[t, sk.parent[th]]), gth)
                r[t, ca] = qmul(qinv(gth), gca)
                r[t, fo] = qmul(qinv(gca), foot_g[s][t])
                u, v = nb - a, nc - nb
                bends.append(math.degrees(math.acos(np.clip(np.dot(u, v) / np.linalg.norm(u) / np.linalg.norm(v), -1, 1))))
        return r, q, float(np.mean(bends))

    lo, hi = 0.0, 0.25
    for _ in range(18):
        dy = (lo + hi) / 2
        _, _, b = legs(dy)
        lo, hi = (dy, hi) if b > knee else (lo, dy)
    r, q, _ = legs((lo + hi) / 2)
    meta = {**clip.meta, "changes": clip.meta.get("changes", "") +
            f"; stood up: hips raised and carried over her feet, knees to {knee:.0f} deg, the body turned back {pitch:.0f} deg"}
    return Clip(clip.name, clip.fps, r, q, loop=clip.loop, meta=meta)


def base_of(rig, calling):
    """A calling's captured standing (made once a run, shared by its idle,
    its breaks and its flourish)."""
    if calling not in _bases:
        style = IDLES[f"idle_{calling}"][0]
        base = idle_loop(f"idle_{calling}_base", rig, style, seconds=(5.0, 8.0), window=TOWN_WINDOW.get(calling))
        if calling in STAND:
            base = stand(rig, base, **STAND[calling])
        _bases[calling] = base
    return _bases[calling]


def clips(rig, want):
    out = []
    for name, (style, arms, weapon) in IDLES.items():
        if want and not any(w in name for w in want):
            continue
        base = base_of(rig, SHARES_BASE.get(name, name[5:]))
        if arms is arcanist:
            arms = _on_hip(rig, base, arms)
        clip = layered(name, rig, base, arms, {"weapon": weapon})
        if name[5:] in TOWN:
            clip = level_head(rig, clip)
        out.append(clip)
    return out
