"""Everything else she does in a fight: the dash, being struck, falling and
rising, loosing a spell, a bolt or a knife, the war cry, and the daggers'
cuts.

All keyed. The same rule as the swings (clips/sword.py) for anything the
game fires at a moment (a bolt, a spell, a thrown knife, a flinch): the clip
starts at the moment itself, the anticipation is the blend in, and the
weight comes after.
"""
from __future__ import annotations

import math

import numpy as np

from clips.sword import _n
from gait import arc_of
from keyed import STRIKE, _flatten, _unflatten, build, merge
from rig import qeuler, qrot


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


# ------------------------------------------------------------ on her knees --
# Where a knee rests on the ground and an ankle lies with the instep flat
# (rig units; the game draws her 1.04 times this): the knee's joint a
# kneecap's radius (45 mm) up, the ankle as the lying pose has it.
KNEE_Y, INSTEP_Y = 0.048, 0.0596
# The knees' place on the ground (z) from her dropping to them till she is
# up again: they pivot there through the fall and the rise.
KNEE_Z = 0.0
# How far forward of where it was keyed the lying pose is laid, so its knees
# rest where she knelt (it was keyed with her hips over the spot she stood
# on, which slid her knees 70 cm back along the ground as she went down).
DOWN_DZ = 0.66
# A kneeling foot's ankle up on tucked toes (rig units), and on its way over
# between the tops of the toes and tucked toes: lifted, so the toe tips clear
# the ground while the foot stands on end (judge 12: rolled over low, they
# stood on their tips 2-5 cm into it).
TUCK_Y, ON_END_Y = 0.16, 0.19
# High enough that a foot hanging straight down from it clears the ground
# with its toes (the ankle to the toe tip is about 0.19).
FLIP_Y = 0.27
# How far a hand flat on the ground under her weight bends back at the wrist
# (held to 65, the hands under her shoulders went in up to the knuckles).
PUSH_EXT = 108.0
# Where the hands are set down to push her up, and stay till she is on her
# knees: beside her chest as she lies, under her shoulders on all fours.
# (Set under her shoulders as she lay, they slid 12 cm back as she pushed
# back, and the forearms leant back past what a wrist can lay flat.)
PUSH_L, PUSH_R = (0.27, 0.04, 0.71), (-0.25, 0.04, 0.70)
# The elbows back and out, as at the bottom of a push-up, so the forearms
# lean forward over the hands (pointed out and forward, the forearms leant
# back and no wrist could lay the hand flat: the fingers went into the ground).
PUSH_POLE_L, PUSH_POLE_R = (0.6, 1, -0.8), (-0.6, 1, -0.8)
# Fingers pressed flat on the ground under her weight.
FLAT = "flat"
# get_up_back's hands on the tops of her knees in the crouch, and on the
# outsides of her thighs as she rises (judge 13: at least 12 cm out from her
# middle, never the inner thigh).
KNEE_L = {"pos": (0.20, 0.50, -0.14), "pole": (1, 0.2, -0.6), "knuckles": (0.1, -0.8, 0.6)}
KNEE_R = {"pos": (-0.20, 0.50, -0.10), "pole": (-1, 0.2, -0.6), "knuckles": (-0.1, -0.8, 0.6)}
THIGH_L = {"pos": (0.24, 0.62, -0.12), "pole": (1, 0.2, -0.6), "knuckles": (0.2, -1, 0.3)}
THIGH_R = {"pos": (-0.24, 0.62, -0.10), "pole": (-1, 0.2, -0.6), "knuckles": (-0.2, -1, 0.3)}
# Tucked toes bent so the pads lie flat under a foot standing on end, keyed
# 59 degrees on from the rest foot (more, and it leant back past upright,
# which no toes can bend far enough to lie flat under).
TUCK_TOE = 64
# The rest foot's pitch (ankle to ball, degrees below level), its length,
# and the ball's joint over the ground when she stands on it (rig units).
FOOT_PITCH, FOOT_LEN, BALL_Y = 31.0, 0.131, 0.034


def _ankle_path(fr, path):
    """The ankle's height at frame fr along (frame, height) points, held at
    either end."""
    if fr <= path[0][0]:
        return path[0][1]
    for (f0, y0), (f1, y1) in zip(path, path[1:]):
        if fr <= f1:
            return y0 + (y1 - y0) * (fr - f0) / (f1 - f0)
    return path[-1][1]


def _legs(rig):
    I, P = rig.I, rig.prest
    pel = P[I["pelvis"]]
    hips = {s: P[I[f"thigh_{s}"]] - pel for s in "lr"}
    calves = {s: P[I[f"calf_{s}"]] - pel for s in "lr"}
    L = float(np.linalg.norm(P[I["calf_l"]] - P[I["thigh_l"]]))
    S = float(np.linalg.norm(P[I["foot_l"]] - P[I["calf_l"]]))
    return pel, hips, L, S, {s: P[I[f"foot_{s}"]] for s in "lr"}, calves


def _kneel(rig, pose, a=None, kz=KNEE_Z, sides="lr", ankle_y=INSTEP_Y):
    """The pose with its hips set so each thigh swings `a` degrees forward of
    upright about a knee resting on the ground at z `kz` (None: as far as the
    keyed hips have it, the hips brought to a thigh's length from the knee),
    and the shins laid flat behind the knees, the insteps on the ground
    (or the ankles at `ankle_y`: up on tucked toes).
    Only the hips' place and the kneeling feet's place change: what the
    hips, spine, arms and feet turn is the pose's own. (Each knee is then
    put at its own thigh's length from its own hip, which a rolled pelvis
    sets a little higher or lower than the other: so it rests on its cap,
    neither in the ground nor off it.)"""
    pel, hip, L, S, ankle, calf = _legs(rig)
    h = pose.get("hips", {})
    q = qeuler(*h.get("rot", (0, 0, 0)))
    hp = np.array(h.get("pos", (0, 0, 0)), float)
    at = {s: pel + hp + qrot(q, hip[s]) for s in "lr"}
    mid = (at["l"] + at["r"]) / 2
    # Each knee straight ahead of its ankle (a shin turned in or out under
    # it left the knee 1 cm into the ground).
    kx = {s: (pose.get(f"foot_{s}", {}).get("pos") or ankle[s])[0] for s in "lr"}
    # Each thigh runs out to the side too (knees wider than the hips):
    # what is left of its length in the side view.
    dx = np.mean([abs(at[s][0] - kx[s]) for s in sides])
    Lyz = math.sqrt(max(L * L - dx * dx, 1e-6))
    if a is None:
        a = math.degrees(math.atan2(mid[2] - kz, mid[1] - KNEE_Y))
    want = np.array([mid[0], KNEE_Y + Lyz * math.cos(math.radians(a)), kz + Lyz * math.sin(math.radians(a))])
    hp = hp + (want - mid)
    out = merge(pose, hips={"pos": tuple(float(x) for x in hp)})
    for s in sides:
        H = at[s] + (want - mid)
        k = np.array([kx[s], KNEE_Y, 0.0])
        k[2] = H[2] - math.sqrt(max(L * L - (H[1] - KNEE_Y) ** 2 - (H[0] - k[0]) ** 2, 1e-6))
        f = dict(out.get(f"foot_{s}", {}))
        x = kx[s]
        # The ankle a shin's length behind the knee, on the ground.
        dz = math.sqrt(max(S * S - (ankle_y - KNEE_Y) ** 2 - (x - k[0]) ** 2, 1e-6))
        f["pos"] = (x, ankle_y - ankle[s][1], float(k[2] - dz))
        # The knee's way aimed at the knee itself: the leg's solve lays the
        # knee in the plane of hip, ankle and pole, so it lands there (a
        # pole only "down" took the lowest place it could reach, 1-2 cm
        # into the ground when the shin runs wider than the thigh).
        f["pole"] = tuple(float(v) for v in k - (pel + hp + qrot(q, calf[s])))
        out[f"foot_{s}"] = f
    return out


def _planted(rig, window):
    """A post pass for build: in the frames `window(fr)` names (a knee z,
    the kneeling sides and, if given, the ankles' height; or None), the
    in-betweens' hips brought back onto the knees' pivot, so a knee neither
    lifts nor sinks between keys."""
    def post(fr, pose):
        w = window(fr)
        return pose if w is None else _kneel(rig, pose, None, kz=w[0], sides=w[1], ankle_y=w[2] if len(w) > 2 else INSTEP_Y)
    return post


# ----------------------------------------------------------- death, rise --
def _mix(a, b, t):
    """Two poses mixed: their numbers in between at t (0 is a, 1 is b),
    anything else (a preset) from the nearer one."""
    fa, fb = _flatten(a), _flatten(b)
    out = {}
    for k in fa.keys() | fb.keys():
        x, y = fa.get(k, fb.get(k)), fb.get(k, fa.get(k))
        out[k] = x + (y - x) * t if isinstance(x, float) and isinstance(y, float) else (y if t >= 0.5 else x)
    return _unflatten(out)


def _down_pose():
    """Face down where she fell, one arm under her, one flung out, her legs
    long on the ground: the end of the fall, and the start of rising. Laid
    DOWN_DZ forward, so her knees rest where she knelt."""
    d = DOWN_DZ
    return {
        # (Judge 13: the hips were propped, the front of the pelvis 7.5 cm
        # off the ground: it rests on the ground now, 1.4 cm, and the chest,
        # held up by her breasts, slopes up to it; so the neck bends down to
        # lay the head.)
        "hips": {"pos": (0.02, -0.96, -0.22 + d), "rot": (6, 80, 6)},
        # (Judge 12: the head was propped 13-15 cm up, looking about: it lies
        # on its cheek, turned to her right, toward the hand by her face.)
        "spine": (4, 10, 4), "neck": (-15, 44, 0), "head": (-60, 0, 15),
        # Her legs lie on the ground, the knees a little bent and down, the
        # shins and the tops of her feet on the ground, the toes pointed
        # back. (The feet turned forward through toes-down, +135, not back
        # through toes-up, -225: the same at rest, but a fall eased from a
        # kneel turned the feet up past the shins, the ankles broken.)
        # (The toes a little curled, as feet lie when nothing holds them:
        # pointed straight they went 2 cm into the ground.)
        # (Curled -15, the toes still went 2 cm in: -28.)
        "foot_l": {"pos": (0.21, -0.045, -1.16 + d), "rot": (6, 135, 0), "pole": (0.25, -1.0, 0.0), "toe": -28},
        "foot_r": {"pos": (-0.13, -0.045, -1.17 + d), "rot": (-4, 135, 0), "pole": (-0.15, -1.0, 0.0), "toe": -28},
        # The flung arm palm down, so a shield strapped to it lies face up
        # on it (the forearm takes the whole roll); the arm under her palm
        # up, so what is in the hand lies flat out from under her. (Left as
        # the arms fell, the shield stood on its edge 18 cm into the ground
        # and the blade stood up over her back. The elbow lies on the ground:
        # turned up, the forearm could not roll far enough to lay the shield.)
        # (Each hand rolled a little onto its little finger's side, the thumb
        # lying on the ground: flat, the thumb stood 2-3 cm into it.)
        "hand_l": {"pos": (0.56, 0.05, 0.16 + d), "pole": (0.5, -1.0, -0.3), "knuckles": (0.6, 0, 0.8), "blade": (-0.8, 0.2, 0.6),
                   "twist": 1.0},
        # (Judge 12: the hand under her chin read as a claw held in the air:
        # it lies flat beside her face, palm down, the elbow out on the ground.)
        "hand_r": {"pos": (-0.30, 0.05, 0.34 + d), "pole": (-1, -0.4, -0.4), "knuckles": (0.1, 0, 1), "blade": (1, 0.25, 0.1)},
        "fingers_l": "open", "fingers_r": "open",
    }


def _on_balls(rig, pose):
    """The feet up on their balls as the heels rise: each ankle set at the
    height its foot's pitch puts it over a ball resting on the ground, and
    the toes bent as far as the foot is pitched, so the pads stay flat.
    (Left to the spline, the ankles lagged the pitch and the balls went 2-3
    cm into the ground, the toes behind them, tips down.)"""
    out = dict(pose)
    for s in "lr":
        f = dict(out[f"foot_{s}"])
        # The foot's pitch below level: its keyed pitch plus the rest foot's.
        pitch = f.get("rot", (0, 0, 0))[1] + FOOT_PITCH
        ank = BALL_Y + FOOT_LEN * math.sin(math.radians(pitch))
        x, _, z = f["pos"]
        f["pos"] = (x, ank - rig.prest[rig.I[f"foot_{s}"]][1], z)
        # (The rest toes are bent 20 degrees off the foot's line: bent the
        # foot's pitch less that, they lie level.)
        f["toe"] = float(np.clip(pitch - 20 - 4, 0, TUCK_TOE))
        out[f"foot_{s}"] = f
    return out


def death(rig):
    """A blow that takes her: rocked back, the knees go, she drops to them,
    sways, and falls forward onto her face, an arm out. Held there.

    The fall (judge 11): the arms give first, the chest reaching the ground
    while the hips are still up over the knees; the knees stay where they
    are, the pivot, and the shins and insteps stay on the ground; then the
    hips come down and forward as the legs straighten, and settle."""
    base = stance(0.06)
    d = DOWN_DZ
    knees = {"foot_l": {"rot": (6, 135, 0), "pole": (0.2, -1, 0.5), "toe": -15},
             "foot_r": {"rot": (-4, 135, 0), "pole": (-0.2, -1, 0.5), "toe": -15},
             "hips": {"pos": (0, -0.50, -0.08)}}
    kneel = _kneel(rig, body(knees, hips=(6, 44, 6), spine=(6, 26, 8), neck=(0, 10, 0), head=(14, 6, 10),
                             hand_l=arm((0.10, -0.20, 0.36), (0.8, 0.2, -0.3)), hand_r=arm((-0.06, -0.22, 0.30), (-0.8, 0.2, -0.3)),
                             fingers_l="open", fingers_r="open"), a=0)
    down = _down_pose()
    # Hands down flat ahead of her as she tips, the elbows already soft.
    # (The left set down as far ahead as the right: 6 cm nearer her, its
    # forearm stood too steep for the wrist to lay the hand flat, and the
    # fingers went 5 cm into the ground.)
    touch_l = {"pos": (0.27, 0.074, 0.77), "pole": (1, 0.3, -0.4), "knuckles": (0.2, 0, 1), "blade": (-0.9, 0.35, 0.2)}
    touch_r = {"pos": (-0.25, 0.06, 0.76), "pole": (-1, 0.3, -0.4), "knuckles": (-0.2, 0, 1)}
    reach_l, reach_r = merge(touch_l, pos=(0.27, 0.20, 0.68)), merge(touch_r, pos=(-0.21, 0.19, 0.68))
    # (The left slides out to where it is flung as the elbow gives; the
    # right is under her as she comes down on it.)
    # (Judge 12: the right one ended under her chin; it gives out to the side,
    # the elbow out, and lies by her face.)
    give_l, give_r = merge(touch_l, pos=(0.42, 0.045, 0.86)), merge(touch_r, pos=(-0.28, 0.045, 0.90), pole=(-1, -0.2, -0.4))
    buckle = body({"foot_l": {"pos": (0.13, 0, 0.06), "rot": (10, 0, 0)}, "foot_r": {"pos": (-0.15, 0, -0.14), "rot": (-14, 0, 0)},
                  "hips": {"pos": (0, -0.20, -0.06)}},
                 hips=(4, -4, 4), spine=(4, 10, 6), neck=(0, 6, 0), head=(4, 10, 8),
                 hand_l=arm((0.04, -0.36, 0.08), (0.6, -0.4, -0.5)), hand_r=arm((-0.04, -0.36, 0.06), (-0.6, -0.4, -0.5)),
                 fingers_l="relaxed", fingers_r="relaxed")
    knelt = body(knees, hips=(4, 10, 6), spine=(6, 22, 8), neck=(0, 12, 0), head=(6, 14, 10),
                 hand_l=arm((0.0, -0.42, 0.04), (0.6, -0.4, -0.5)), hand_r=arm((0.0, -0.42, 0.02), (-0.6, -0.4, -0.5)),
                 fingers_l="relaxed", fingers_r="relaxed")
    on_knees = _kneel(rig, knelt, a=-4)
    heels_up = merge(_mix(buckle, on_knees, 0.45),
                     foot_l={"pos": (0.15, 0.07, -0.16), "rot": (8, 60, 0), "toe": TUCK_TOE, "pole": (0.2, -0.3, 1)},
                     foot_r={"pos": (-0.15, 0.07, -0.28), "rot": (-8, 60, 0), "toe": TUCK_TOE, "pole": (-0.2, -0.3, 1)})
    # (Lifted as they roll over, so the toes clear the ground while the
    # foot stands on end.)
    # (Judge 12: the toes stay tucked till the knees are down, f15, then the
    # feet go over onto their tops in two frames, lifted as they stand on end.)
    rolled = _mix(heels_up, on_knees, 0.5)
    for s in "lr":
        x, _, z = rolled[f"foot_{s}"]["pos"]
        rolled[f"foot_{s}"] = {**heels_up[f"foot_{s}"], "pos": (x, 0.06, z), "rot": ((8 if s == "l" else -8), 60, 0)}
    tucked_k = _kneel(rig, merge(knelt, foot_l={**knelt["foot_l"], "rot": (8, 50, 0), "toe": TUCK_TOE},
                                 foot_r={**knelt["foot_r"], "rot": (-8, 50, 0), "toe": TUCK_TOE}), a=-4, ankle_y=TUCK_Y)
    # (Judge 13: going over in a frame, low, they stood on their straight toes
    # at f16.) The shins swing up off the ground about the knees, so the feet
    # turn over in the air, the toes letting go, and come down onto their tops.
    on_end = merge(_mix(on_knees, kneel, 1 / 6), foot_l={**on_knees["foot_l"], "rot": (8, 85, 0), "toe": 8},
                   foot_r={**on_knees["foot_r"], "rot": (-8, 85, 0), "toe": 8})
    over = merge(_mix(on_knees, kneel, 2 / 6), foot_l={**on_knees["foot_l"], "rot": (8, 118, 0), "toe": -10},
                 foot_r={**on_knees["foot_r"], "rot": (-8, 118, 0), "toe": -10})
    tip = _kneel(rig, body(knees, hips=(6, 66, 6), spine=(6, 34, 8), neck=(4, 4, 0), head=(10, 4, 8),
                           hand_l=reach_l, hand_r=reach_r, fingers_l="open", fingers_r="open"), a=12)
    keys = [
        (0, body(base, hips=(8, -10, 0), spine=(10, -18, -4), neck=(0, -10, 0), head=(8, -20, -6),
                 clav_l=(10, 0), clav_r=(10, 0),
                 hand_l=arm((0.10, -0.16, 0.10), (0.8, -0.2, -0.3)), hand_r=arm((-0.10, -0.16, 0.10), (-0.8, -0.2, -0.3)),
                 fingers_l="spread", fingers_r="relaxed"), "ease"),
        (8, buckle, "auto"),
        # Going down: the heels up, on the balls of her feet, the toes bent;
        # the feet slide back under her as the shins swing back.
        (11, heels_up, "auto"),
        # The feet rolled over onto their tops, the toes trailing.
        (13, rolled, "auto"),
        # On her knees, the toes still tucked; over onto the tops of the feet.
        (15, tucked_k, "auto"),
        (16, on_end, "auto"),
        (17, over, "auto"),
        (18, _mix(on_knees, kneel, 3 / 6), "auto"),
        (21, kneel, "auto"),
        # (A frame on, the hands where the arcs had them, as points: so the
        # reach for the ground runs point to point. Cross-faded from an arc
        # carried along by the tipping chest to a point on the ground, the
        # arm was thrown straight.)
        (22, merge(_kneel(rig, _mix(kneel, tip, 0.2)), hand_l=merge(tip["hand_l"], pos=(0.33, 0.41, 0.335)),
                   hand_r=merge(tip["hand_r"], pos=(-0.20, 0.34, 0.30))), "auto"),
        # Tipping: the arms reach for the ground, the elbows soft.
        (26, {k: v for k, v in tip.items() if k not in ("hand_l", "hand_r")}, "auto"),
        # The hands meet it.
        (28, _kneel(rig, body(knees, hips=(6, 80, 6), spine=(6, 28, 7), neck=(-8, -6, 0), head=(-18, -6, -6),
                              hand_l=touch_l, hand_r=touch_r, fingers_l="open", fingers_r="open"), a=22), "auto"),
        # The arms give: the chest goes down between them, the hips still up.
        (30, _kneel(rig, body(knees, hips=(6, 94, 6), spine=(6, 14, 6), neck=(-12, -14, 0), head=(-28, -10, -4),
                              hand_l=give_l, hand_r=give_r, fingers_l="open", fingers_r="open"), a=40), "auto"),
        # The chest on the ground, the face turned; the hips still up, the
        # back sloping down to the chest.
        (32, _kneel(rig, merge(down, hips={"rot": (6, 104, 6)}, spine=(5, -12, 4), neck=(-15, 0, 0), head=(-52, -6, 10)), a=60), "auto"),
        # The hips come down and forward as the legs straighten.
        # (The neck bending as the hips come down and the chest tips up onto
        # her breasts, so the head never lifts.)
        (35, _kneel(rig, merge(down, hips={"rot": (6, 92, 6)}, spine=(5, 2, 4), neck=(-15, 24, 0)), a=70), "auto"),
        (38, _kneel(rig, merge(down, spine=(4, 9, 4), neck=(-15, 40, 0))), "ease"),
        # A settle: the last of the weight going out of her (judge 12: only
        # ever down from here). Where she ends is where get_up starts.
        (40, _kneel(rig, merge(down, spine=(4, 9.5, 4), neck=(-15, 42, 0))), "ease"),
        (45, _kneel(rig, down), "ease"),
    ]
    planted = _planted(rig, lambda fr: (KNEE_Z, "lr", _ankle_path(fr, ((15, TUCK_Y), (16, FLIP_Y), (17, 0.17), (18, INSTEP_Y))))
                       if fr >= 15 else None)
    return build("death", rig, keys, meta={"layer": "full", "hold": True},
                 post=lambda fr, pose: _on_balls(rig, pose) if 8 < fr < 15 else planted(fr, pose))


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
    """From where the fall left her: the hands brought under her shoulders,
    a push up on them, the hips back over the knees, a knee up, a breath on
    one knee, and up, shaking it off.

    (Judge 11: the arms push first; the legs never leave the ground. The
    knees stay where they lay, the pivot, and the hips go back over them.)"""
    # On her hands and knees: the hips pushed back over the knees, the hands
    # still where they pushed, the back level, the shins along the ground
    # behind, the insteps flat. (The back tipped 70 degrees held her
    # shoulders too high for the hands to reach the ground.)
    fours = _kneel(rig, {"hips": {"pos": (0.0, -0.53, 0.0), "rot": (2, 98, 2)}, "spine": (0, 6, 0), "neck": (0, -30, 0),
                         "head": (0, -16, 0),
                         "foot_l": {"pos": (0.16, 0, 0), "rot": (6, 135, 0), "toe": -15},
                         "foot_r": {"pos": (-0.14, 0, 0), "rot": (-6, 135, 0), "toe": -15},
                         "hand_l": {"pos": PUSH_L, "pole": PUSH_POLE_L, "knuckles": (0.1, 0, 1), "ext": PUSH_EXT},
                         "hand_r": {"pos": PUSH_R, "pole": PUSH_POLE_R, "knuckles": (-0.1, 0, 1), "ext": PUSH_EXT},
                         "fingers_l": FLAT, "fingers_r": FLAT}, a=14)
    down = _down_pose()
    # The hands under the shoulders, palms down (the one under her drawn
    # out, the flung one drawn in), the head up off the ground.
    hands = merge(down, spine=(4, -6, 4), neck=(-10, -24, 0), head=(-20, -14, 0),
                  hand_l={"pos": PUSH_L, "pole": PUSH_POLE_L, "knuckles": (0.1, 0, 1), "ext": PUSH_EXT},
                  hand_r={"pos": PUSH_R, "pole": PUSH_POLE_R, "knuckles": (-0.1, 0, 1), "ext": PUSH_EXT},
                  fingers_l=FLAT, fingers_r=FLAT)
    for s in ("hand_l", "hand_r"):
        hands[s].pop("blade", None)
        hands[s].pop("twist", None)
    # The push: the arms straighten under her, the chest comes up, the
    # back hollowed, the hips still down.
    push = _kneel(rig, merge(hands, hips={"rot": (4, 80, 4)}, spine=(2, -24, 2), neck=(4, -10, 0), head=(6, -10, 0),
                             hand_l=hands["hand_l"], hand_r=hands["hand_r"]), a=62)
    # Up on one knee: the left foot brought through under her and set down
    # ahead; the right knee stays down, its toes tucked under to push off.
    TUCK = TUCK_Y
    tucked = {"rot": (-8, 50, 0), "toe": TUCK_TOE, "pole": (-0.2, -1, 0.4)}
    knee_up = _kneel(rig, body({"foot_l": {"pos": (0.15, 0.0, 0.22), "rot": (8, 0, 0), "pole": (0.2, 0, 1)},
                                "foot_r": {"pos": (-0.15, 0, 0), **tucked},
                                "hips": {"pos": (0, -0.50, -0.12)}},
                               hips=(0, 24, 0), spine=(0, 16, 0), neck=(0, -6, 0), head=(0, -6, 0),
                               hand_l={"pos": (0.16, 0.50, 0.24), "pole": (0.8, 0, -0.5)},
                               hand_r=arm((-0.02, -0.36, 0.10), (-0.6, -0.4, -0.5)),
                               fingers_l="relaxed", fingers_r="relaxed"), sides="r", ankle_y=TUCK)
    # The left foot on its way through: knee drawn up under her chest, the
    # foot lifted clear, the toes hanging; her weight still on her hands.
    through = merge(fours, hips={"rot": (2, 90, 2)}, spine=(0, 10, 0), neck=(0, -24, 0),
                    foot_l={"pos": (0.15, 0.17, -0.12), "rot": (8, 22, 0), "toe": 0, "pole": (0.2, -0.2, 1)},
                    foot_r={**tucked})
    through = _kneel(rig, through, sides="r", ankle_y=TUCK)
    # (Judge 12: both feet stood on their toe tips 2-8 cm into the ground
    # going over.) Half way: the left foot lifted with the knee, its top
    # still facing down, the toes trailing; the right standing on end, lifted,
    # its toes already bending under.
    half = _mix(fours, through, 0.5)
    lp = half["foot_l"]["pos"]
    # (Judge 13: going through, the left foot hung straight down with its toes
    # 1.5 cm off the ground, and the right stood on its tips turning over:
    # the left is lifted higher and turns up ahead of the shin; the right
    # turns over in the air, its toes only bending under as they come down.)
    half = merge(half, foot_l={"pos": (lp[0], lp[1] + 0.10, lp[2]), "rot": (8, 100, 0), "toe": -10, "pole": (0.2, -0.4, 1)},
                 foot_r={"rot": (-8, 80, 0), "toe": -20, "pole": (-0.2, -1, 0.4)})
    # The hands lifted off the ground on their way in (judge 12: they skidded
    # 25-30 cm along it), set down at f4.
    hk = _kneel(rig, hands)
    lift = _mix(down, hk, 0.5)
    for h in ("hand_l", "hand_r"):
        a_, b_ = down[h]["pos"], hk[h]["pos"]
        lift[h] = {"pos": ((a_[0] + b_[0]) / 2, max(a_[1], b_[1]) + 0.05, (a_[2] + b_[2]) / 2), "pole": hk[h]["pole"],
                   "knuckles": hk[h]["knuckles"]}
    keys = [
        (0, down, "ease"),
        (2, lift, "auto"),
        (4, hk, "auto"),
        (9, push, "auto"),
        (16, fours, "auto"),
        (18, half, "auto"),
        (20, through, "auto"),
        (27, knee_up, "auto"),
        (35, body({"foot_l": {"pos": (0.15, 0.0, 0.22), "rot": (8, 0, 0), "pole": (0.2, 0, 1)},
                   # (On the ball of the back foot, pushing off: keyed toes-up, it hung
                   # level 12 cm off the ground.)
                   "foot_r": {"pos": (-0.15, 0.03, -0.40), "rot": (-8, 24, 0), "toe": 45},
                   "hips": {"pos": (0, -0.38, -0.08)}},
                  hips=(0, 18, 0), spine=(0, 10, 0), head=(0, -4, 0),
                  hand_l={"pos": (0.16, 0.52, 0.24), "pole": (0.8, 0, -0.5)}, hand_r=arm((-0.05, -0.40, 0.08), (-0.6, -0.4, -0.5)),
                  fingers_l="relaxed", fingers_r="relaxed"), "auto"),
        # Up, the weight settling, a roll of the shoulders; the arms hanging at
        # her sides (judge 12: held bent, the hands swept her groin).
        (45, body(stance(0.06), hips=(0, 4, 0), spine=(0, 2, 0), clav_l=(6, 0), clav_r=(6, 0),
                  hand_l=arm((0.05, -0.42, 0.06), (0.6, -0.4, -0.5)), hand_r=arm((-0.05, -0.42, 0.06), (-0.6, -0.4, -0.5)),
                  fingers_l="relaxed", fingers_r="relaxed"), "auto"),
        (55, body(stance(0.05), hand_l=arm((0.05, -0.43, 0.04), (0.6, -0.4, -0.5)),
                  hand_r=arm((-0.05, -0.43, 0.04), (-0.6, -0.4, -0.5)), fingers_l="relaxed", fingers_r="relaxed"), "ease"),
    ]

    def window(fr):
        if fr <= 16:
            return KNEE_Z, "lr"
        if fr <= 27:
            # The right knee kept down while its toes tuck under.
            return KNEE_Z, "r", _ankle_path(fr, ((16, INSTEP_Y), (17, 0.18), (18, 0.25), (19, 0.215), (20, TUCK)))
        return None
    planted = _planted(rig, window)

    def post(fr, pose):
        # The right foot turned upright in the air and its toes bent under
        # before they reach the ground (judge 13: left to the keys, the toes
        # were still bending as they touched, a frame on their tips).
        if 18 < fr < 20:
            f = dict(pose["foot_r"])
            f["rot"] = (-8, _ankle_path(fr, ((18, 80), (19, 56), (20, 50))), 0)
            f["toe"] = _ankle_path(fr, ((18, -20), (19, 56), (20, TUCK_TOE)))
            pose = {**pose, "foot_r": f}
        return planted(fr, pose)
    return build("get_up", rig, keys, meta={"layer": "full"}, post=post)


def get_up_back(rig):
    """From where death_back left her, on her back: the head lifts first and
    the knees draw up, the flung arm comes down round her side, she sits up
    onto her hands, pushes off them and rocks forward over her feet into a
    crouch, the hands going to her knees, then rises pushing on her thighs
    and steps back into her stance. (The game played get_up, which starts
    face down, after any fall: a pop after a fall onto her back.)
    She lay 0.6 m behind where she stood; the feet are drawn in under her and
    the rock forward brings her most of the way back, the last step the rest.

    (Judge 13: the sit-up was a kip-up, f0-f6; the push and rock popped in
    three frames, f12-f15; the hands went to her groin, f24-f27. Now: the
    head curls first and the trunk comes up at most 8 degrees a frame; the
    hips leave the ground only once the trunk is past upright, at f16, and
    lift at most about 1.5 m/s; the hands go through the air to the tops of
    her knees, then up the outsides of her thighs.)"""
    lie = _back_pose(1.0)
    flat_l = {"rot": (10, 0, 0), "pole": (0.2, 1, 0.6)}
    flat_r = {"rot": (-10, 0, 0), "pole": (-0.2, 1, 0.6)}
    # The feet drawn in under her knees, where she rocks over them.
    fl = {"pos": (0.14, 0.0, -0.30), **flat_l}
    fr = {"pos": (-0.15, 0.0, -0.25), **flat_r}
    # The hands planted behind her hips as she sits, pushing.
    pl = {"pos": (0.25, 0.04, -0.86), "pole": (1, 0.3, -0.8), "knuckles": (0.3, 0, 1), "ext": PUSH_EXT}
    pr = {"pos": (-0.25, 0.04, -0.86), "pole": (-1, 0.3, -0.8), "knuckles": (-0.3, 0, 1), "ext": PUSH_EXT}

    def sit(fr_, hips_y, hips_z, pitch, spine, neck, head, hl, hr, feet=(fl, fr), fingers=("relaxed", "relaxed")):
        return {"hips": {"pos": (0.0, hips_y, hips_z), "rot": (0, pitch, 0)}, "spine": (0, spine, 0), "neck": (0, neck, 0),
                "head": (0, head, 0), "foot_l": feet[0], "foot_r": feet[1], "hand_l": hl, "hand_r": hr,
                "fingers_l": fingers[0], "fingers_r": fingers[1]}
    keys = [
        (0, lie, "ease"),
        # The head and shoulders curl first; the knees begin to draw up; the
        # flung arm lifts off the ground and swings out round her side.
        (3, merge(lie, hips={"rot": (-5, -86, -3)}, spine=(2, 10, -4), neck=(6, 24, 0), head=(10, 14, 6),
                  foot_l={"pos": (0.10, 0.06, -0.10), "rot": (30, -15, 25), "pole": (0.8, 0.6, 0.3)},
                  foot_r={"pos": (-0.16, 0.06, 0.12), "rot": (-15, -30, -5), "pole": (-0.4, 1, 0.3)},
                  hand_l={"pos": (0.68, 0.16, -1.12), "pole": (1, 0.4, -0.2), "knuckles": (0.6, 0, -0.6)},
                  hand_r={"pos": (-0.40, 0.10, -0.70), "pole": (-1, 0.4, -0.2), "knuckles": (-0.3, 0, -1)},
                  fingers_l="relaxed", fingers_r="relaxed"), "auto"),
        # Up on her elbows' way, the knees up, the feet flat; the arms coming
        # down at her sides to plant behind her.
        (6, sit(6, -0.95, -0.62, -70, 18, 18, 8,
                {"pos": (0.40, 0.13, -0.90), "pole": (1, 0.3, -0.6), "knuckles": (0.4, 0, -0.8)},
                {"pos": (-0.36, 0.12, -0.80), "pole": (-1, 0.3, -0.6), "knuckles": (-0.3, 0, -1)},
                feet=({"pos": (0.13, 0.0, -0.24), **flat_l}, {"pos": (-0.15, 0.0, -0.18), **flat_r})), "auto"),
        (8, sit(8, -0.95, -0.62, -55, 16, 14, 6, pl, pr, fingers=("flat", "flat")), "auto"),
        # Sat up, leaning back on her hands.
        (11, sit(11, -0.95, -0.61, -38, 14, 10, 4, pl, pr, fingers=("flat", "flat")), "auto"),
        # The push: a little further back onto the hands, then the trunk swings
        # forward over the hips, which roll forward on the ground.
        (13, sit(13, -0.95, -0.60, -34, 12, 6, 2, pl, pr, fingers=("flat", "flat")), "auto"),
        # Off the hands: the trunk upright, the hips still down, the hands in
        # the air on their way forward.
        (16, sit(16, -0.945, -0.56, 0, 16, -4, -4,
                 {"pos": (0.27, 0.16, -0.68), "pole": (1, -0.2, -0.6), "knuckles": (0.2, -0.5, 1)},
                 {"pos": (-0.27, 0.16, -0.66), "pole": (-1, -0.2, -0.6), "knuckles": (-0.2, -0.5, 1)}), "auto"),
        # The weight over the feet, the hips lifting.
        (20, sit(20, -0.82, -0.47, 32, 18, -10, -6,
                 {"pos": (0.25, 0.36, -0.30), "pole": (1, -0.4, -0.4), "knuckles": (0.1, -0.7, 0.7)},
                 {"pos": (-0.25, 0.36, -0.28), "pole": (-1, -0.4, -0.4), "knuckles": (-0.1, -0.7, 0.7)}), "auto"),
        # In the crouch, the hands on her knees.
        (24, sit(24, -0.68, -0.42, 40, 18, -10, -6, KNEE_L, KNEE_R), "auto"),
        # Rising, pushing on her thighs, the hands sliding up their outsides.
        (32, body({"foot_l": fl, "foot_r": fr, "hips": {"pos": (0.0, -0.36, -0.30)}},
                  hips=(0, 22, 0), spine=(0, 10, 0), neck=(0, -6, 0), head=(0, -4, 0),
                  hand_l=THIGH_L, hand_r=THIGH_R, fingers_l="relaxed", fingers_r="relaxed"), "auto"),
        # Up over the feet, the left one stepping through into her stance.
        (38, body({"foot_l": {"pos": (0.13, 0.04, -0.06), "rot": (10, 0, 0)}, "foot_r": {"pos": (-0.15, 0, -0.18), "rot": (-14, 0, 0)},
                   "hips": {"pos": (0.0, -0.10, -0.16)}},
                  hips=(0, 8, 0), spine=(0, 4, 0),
                  hand_l=arm((0.05, -0.40, 0.08), (0.6, -0.4, -0.5)), hand_r=arm((-0.05, -0.40, 0.08), (-0.6, -0.4, -0.5)),
                  fingers_l="relaxed", fingers_r="relaxed"), "auto"),
        (43, body(stance(0.06), hips=(0, 4, 0), spine=(0, 2, 0), clav_l=(6, 0), clav_r=(6, 0),
                  hand_l=arm((0.05, -0.42, 0.06), (0.6, -0.4, -0.5)), hand_r=arm((-0.05, -0.42, 0.06), (-0.6, -0.4, -0.5)),
                  fingers_l="relaxed", fingers_r="relaxed"), "auto"),
        (50, body(stance(0.05), hand_l=arm((0.05, -0.43, 0.04), (0.6, -0.4, -0.5)),
                  hand_r=arm((-0.05, -0.43, 0.04), (-0.6, -0.4, -0.5)), fingers_l="relaxed", fingers_r="relaxed"), "ease"),
    ]
    return build("get_up_back", rig, keys, meta={"layer": "full"})


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
    return build("cast_bolt", rig, keys, lead=STRIKE, meta={"layer": "upper", "contact": 0.0, "weapon": "staff"})


def cast_raise(rig):
    """The arcanist's great working: the staff swept up overhead in both
    hands, held across the sky, and brought down upright, its foot striking
    the ground before her, both fists on it.

    (A staff goes through the fist square to it: held upright overhead it
    asked a wrist bent back along the forearm, and brought down to a hand
    hanging low it asked the same the other way; the hand turned over in a
    frame. Across overhead and upright before her chest, it sits in the
    fists as staffs do.)"""
    keys = [
        (0, body(stance(0.06), spine=(0, -6, 0), head=(0, -14, 0),
                 hand_r=arm((0.06, 0.32, 0.10), (-0.6, 0.2, -0.6), blade=_n(1.0, 0.1, 0.1)),
                 hand_l=arm((0.0, 0.34, 0.10), (0.6, 0.2, -0.6)), fingers_l="grip", fingers_r="grip"), "ease"),
        (6, body(stance(0.06), spine=(0, -10, 0), head=(0, -20, 0),
                 hand_r=arm((0.06, 0.40, 0.08), (-0.6, 0.2, -0.6), blade=_n(1.0, 0.15, 0.1)),
                 hand_l=arm((0.0, 0.42, 0.08), (0.6, 0.2, -0.6)), fingers_l="grip", fingers_r="grip"), "fast"),
        (10, body(stance(0.14, weight=0.3), hips=(0, 14, 0), spine=(0, 18, 0), head=(0, -10, 0),
                  hand_r=arm((0.10, -0.24, 0.30), (-0.7, -0.6, -0.2), blade=_n(0.0, 0.97, -0.25)),
                  hand_l=arm((-0.26, -0.06, 0.26), (0.8, -0.4, -0.3)), fingers_l="grip", fingers_r="grip"), "ease"),
        (16, body(stance(0.14, weight=0.3), hips=(0, 15, 0), spine=(0, 19, 0), head=(0, -10, 0),
                  hand_r=arm((0.10, -0.25, 0.30), (-0.7, -0.6, -0.2), blade=_n(0.0, 0.97, -0.25)),
                  hand_l=arm((-0.26, -0.07, 0.26), (0.8, -0.4, -0.3)), fingers_l="grip", fingers_r="grip"), "auto"),
        (28, body(stance(0.06), hand_l=arm((-0.02, -0.40, -0.05), (1.0, 0.0, -0.7), knuckles=_n(0.2, -0.6, 0.6)),
                  hand_r=arm((-0.16, -0.28, 0.12), (-0.8, -0.3, -0.6), blade=_n(-0.12, 1.0, 0.18)),
                  fingers_l="relaxed", fingers_r="grip"), "ease"),
    ]
    return build("cast_raise", rig, keys, meta={"layer": "upper", "contact": 10 / 30, "weapon": "staff"})


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
    return build("cast_flick", rig, keys, lead=STRIKE, meta={"layer": "upper", "contact": 0.0, "weapon": "wand"})


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
    return build("crossbow_shoot", rig, keys, meta={"layer": "upper", "contact": 0.0, "weapon": "crossbow"})


def throw(rig):
    """Overhand: the hand already back behind her head, whipped through,
    released high and in front, the arm following through across her."""
    def windup(c):
        # The wind-up (the owner, 11 October: the arm went straight up at the
        # ball joint, twisted thin, the forearm over her crown and the wrist
        # bent back hard): the shoulder drawn back, the elbow forward and up,
        # the hand in behind her ear, the haft laid 25-35 degrees back so the
        # axe head sits behind her right shoulder; the other arm reaching
        # forward at chest height (judges 10 and 11). c 0..1: drawn back.
        hand_r = {"pos": (-0.315, 1.651 + 0.01 * c, -0.19 - 0.02 * c), "pole": (-0.9, 0.0, -0.3),
                  # The hand as the straight wrist left it (forearm rolled as far as
                  # it goes), then turned 20 degrees out about her forward axis
                  # (judge 12: the haft's top leant 24 degrees in over her head).
                  "blade": _n(0.068, 0.868, -0.492 - 0.05 * c),
                  "knuckles": _n(-0.236, 0.493, 0.837), "frame": "char", "twist": 0.45}
        hand_l = arm((0.05, -0.22, 0.36), (0.8, -0.5, -0.2))
        return body(stance(0.07, weight=-0.4), hips=(-16, -2 - 2 * c, 0), spine=(-26, -8 - 3 * c, 0), head=(30, -2 + 4 * c, 0),
                    clav_r=(16, -6), hand_r=hand_r, hand_l=hand_l, fingers_r="grip", fingers_l="open")

    keys = [
        # The wind-up (the owner, 11 October: the arm went straight up at the
        # ball joint, twisted thin, the forearm over her crown and the wrist
        # bent back hard): the shoulder shrugged and drawn back, the elbow
        # out to the side at shoulder height, the hand behind her ear, the
        # wrist straight with the forearm until the release.
        # (judge 11: the haft still stood upright and the hand out to the
        # side; the haft is the weapon mount's shaft, Arms.Hold, so it is
        # keyed in her space, not the leaned chest's. The wind-up is held a
        # frame, drawn a little further back, so it is seen at all: a "fast"
        # key left at once read only as the in-between; the hips lead
        # 1.5 frames, so the hold runs two and the release comes a frame later.)
        (0, windup(0.0), "ease"),
        (2.0, windup(1.0), "fast"),
        (3.5, body(stance(0.08), hips=(-2, 6, 0), spine=(0, 8, 0), head=(4, -4, 0),
                   hand_r=arm((-0.04, 0.10, 0.44), (-0.8, -0.3, -0.2), blade=_n(0.0, 0.3, 1.0)),
                   hand_l=arm((0.06, -0.30, 0.18), (0.6, -0.2, -0.6)), fingers_r="open", fingers_l="relaxed"), "linear"),
        (7, body(stance(0.10, weight=0.5), hips=(12, 10, 0), spine=(22, 14, 0), head=(-26, -6, 0),
                 hand_r=arm((0.22, -0.34, 0.30), (-0.8, -0.2, 0.0)),
                 # The other arm swept down to her hip as she turns in, not
                 # behind her back (it read as a raised arm at the play camera):
                 # the elbow a little behind her, the wrist straight.
                 hand_l=arm((-0.02, -0.42, 0.14), (0.4, -0.1, -0.9)), fingers_r="relaxed", fingers_l="relaxed"), "ease"),
        (10, body(stance(0.10, weight=0.5), hips=(13, 10, 0), spine=(24, 14, 0), head=(-28, -6, 0),
                 hand_r=arm((0.24, -0.36, 0.26), (-0.8, -0.2, 0.0)),
                 hand_l=arm((-0.01, -0.44, 0.12), (0.4, -0.1, -0.9)), fingers_r="relaxed", fingers_l="relaxed"), "auto"),
        (21, body(stance(0.07), hand_r=arm((0.0, -0.34, 0.16), (-0.6, -0.4, -0.5)),
                  # (the hand at the side of her thigh, off her groin: judge 10)
                  hand_l=arm((0.06, -0.38, 0.06), (0.6, -0.4, -0.5)), fingers_r="grip", fingers_l="relaxed"), "ease"),
    ]
    return build("throw", rig, keys, lead=STRIKE, meta={"layer": "upper", "contact": 3.5 / 30, "weapon": "daggers"})


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


ALL = (("dash", dash), ("hit", hit), ("death", death), ("death_back", death_back), ("get_up", get_up), ("get_up_back", get_up_back),
       ("cast_bolt", cast_bolt),
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
