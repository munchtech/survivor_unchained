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

from clips.actions import _hop, arm
from held import contact_build, forearm_on_ground, knee_clear, slerp_dir
from keyed import Track, _one_frame, build, merge, smoothstep_
from rig import qbetween, qeuler, qfrom_basis, qinv, qmatrix, qmul, qrot, qslerp


def _f(curl, thumb, cascade=0.25, spread=0.0):
    """Fingers, every key the same shape (a preset name and a dict do not
    blend)."""
    return {"curl": curl, "thumb": thumb, "cascade": cascade, "spread": spread}


RELAXED, OPEN = _f(0.28, 0.15), _f(0.05, 0.0, 0.0, 4.0)


# The left hand resting on her hip and thigh while she lies and rises (lead 14,
# judge 37 and its solver: planted on the ground before her chest, the hand
# was out of reach, hung 8-11 cm over the ground, and the upper arm went
# 64-77 mm into her breast). Keyed here (the elbow back behind her trunk);
# the clips' contacts lay it on the thigh each frame (_hand_on_thigh_l), `u`
# of the way from hip to knee, the wrist `off` over the thigh's line.
HAND_ON_HIP_L = {"pos": (0.10, 0.42, 0.08), "pole": (0.5, -0.2, -1.0), "knuckles": (0.3, -0.2, 0.93)}
HIP_REST_L = (0.3, 0.185)


def _knee_at(rig, gpos, fr, side, foot):
    """Where knee_clear sets the knee (the place its pole aims the solve at)."""
    s = 1 if side == "l" else -1
    rest = rig.prest[rig.I[f"foot_{side}"]]
    p = np.asarray(foot.get("pos", (rest[0], 0, rest[2])), float)
    target = np.array([p[0] + s * rig.feet_out * ("pos" in foot), rest[1] + p[1], p[2]])
    top = gpos[fr, rig.I[f"thigh_{side}"]]
    return (top + target) / 2 + np.asarray(knee_clear(rig, gpos, fr, side, foot)["pole"], float) / 10.0


def _hand_on_thigh_l(rig, gpos, fr, pose, u=HIP_REST_L[0], off=HIP_REST_L[1], hip=None, knee=None):
    """The left hand laid on her left thigh (_on_thigh, on its top), the thigh
    as solved this frame (knee_clear's knee unless given)."""
    hip = gpos[fr, rig.I["thigh_l"]] if hip is None else hip
    knee = _knee_at(rig, gpos, fr, "l", pose["foot_l"]) if knee is None else knee
    return _on_thigh(pose["hand_l"], hip, knee, 0.0, 1.0, u=u, off=(off, off))


def _side(breath=0.0, stir=0.0):
    """Lying on her right side, a little curled: the knees drawn up, the
    left leg over the right, the right arm out under her head, the left
    hand resting on her hip (put on her thigh by the clips' contacts: fallen
    on the ground before her chest, the arm went through her breast, judge 37)."""
    return {
        "hips": {"pos": (0.0, -0.87, 0.0), "rot": (0, 8, 90)},
        "spine": (0, 14 + 2 * breath, -4), "neck": (0, 6, 16), "head": (0, 8 - 3 * stir, 14 - 6 * stir),
        "foot_r": {"pos": (0.70, -0.04, 0.30), "rot": (0, 0, 90), "pole": (0, 0, 1)},
        "foot_l": {"pos": (0.62, 0.07, 0.40), "rot": (0, 10, 88), "pole": (0, 0, 1)},
        # (Arms in character space: she lies along -X, the ground at y 0.)
        "hand_r": {"pos": (-0.90, 0.05, 0.24), "pole": (0, 0.3, 1), "knuckles": (-0.6, 0, 0.8)},
        "hand_l": HAND_ON_HIP_L,
        "clav_l": (0, 8), "clav_r": (0, -4),
        "fingers_l": _f(0.28 + 0.3 * stir, 0.15 + 0.15 * stir),
        "fingers_r": RELAXED,
    }


def _elbow(up=1.0, sag=0.0):
    """Propped on her right forearm, the chest lifted off the ground, the
    left hand on her thigh; the head hanging."""
    return {
        "hips": {"pos": (0.0, -0.87, 0.0), "rot": (0, 10, 90 - 31 * up)},
        "spine": (0, 12, -6 * up), "neck": (0, 18 + 8 * sag, -6), "head": (0, 22 + 10 * sag, -10),
        "foot_r": {"pos": (0.70, -0.015, 0.30), "rot": (0, 0, 90), "pole": (0, 0.4, 1)},
        "foot_l": {"pos": (0.62, 0.07, 0.42), "rot": (0, 10, 86), "pole": (0, 0, 1)},
        "hand_r": {"pos": (-0.52, 0.05, 0.28), "pole": (-0.3, -1, -0.4), "knuckles": (-0.5, 0, 1)},
        "hand_l": HAND_ON_HIP_L,
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
        # The knees kept off the ground as sit_back_heels keeps them (lead 14:
        # left to the keys, the left knee was 7.5 cm lower at her last frame
        # than at sit_back_heels' first), and the left hand on her thigh.
        out = {f"foot_{s}": knee_clear(rig, p, fr, s, pose[f"foot_{s}"]) for s in "lr"}
        out["hand_l"] = _hand_on_thigh_l(rig, p, fr, pose)
        # The right arm comes in from under her head to lie along the ground
        # under her shoulder, and she rises onto that forearm.
        # The arm sweeps along the ground from over her head (her -X) round to
        # before her, the elbow drawn in as the shoulder lifts.
        w = smoothstep_((fr - 92) / 26.0)
        if w <= 0:
            return out
        toward = slerp_dir((-1.0, 0.0, 0.12), PROP_TOWARD, w)
        hand, pole = forearm_on_ground(rig.sk, p, fr, "r", toward, ground=0.035)
        keyed = pose["hand_r"]
        k = min(1.0, w * 6)
        at = np.asarray(keyed["pos"], float) * (1 - k) + hand * k
        out["hand_r"] = {**_aimed_only(keyed), "pos": tuple(at), "pole": tuple(np.asarray(keyed["pole"], float) * (1 - k) + pole * k),
                         "knuckles": tuple(slerp_dir(keyed["knuckles"], toward, k))}
        return out

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
    """Sat sideways on her right hip, the legs folded under to her left as if
    she had knelt and slid off her heels (both shins back, the feet behind
    her left hip, their tops down), leaning on her right hand; the head
    bowed. From here she only has to lift her hips up and over onto her
    knees: no leg has to be drawn round under her."""
    return {
        "hips": {"pos": _SBH_HIPS[0][1], "rot": _SBH_HIPS[0][2]},
        "spine": (-10, 6 + 4 * lean, -6 - 2 * lean), "neck": (6, 12, -2), "head": (4, 16, -2),
        "foot_r": _sbh_foot("r", 62), "foot_l": _sbh_foot("l", 62),
        "hand_r": {"pos": (-0.52, 0.05, 0.28), "pole": (-0.5, 0, -1), "knuckles": (-0.4, 0, 1)},
        "hand_l": {"pos": (-0.10, 0.22, 0.12), "pole": (0.6, -0.5, -0.4), "knuckles": (0.1, -0.5, 1)},
        "clav_l": (0, 6), "clav_r": (10, 2), "fingers_l": RELAXED, "fingers_r": OPEN,
    }


# sit_back_heels' legs from lying on her side to her heels (f34-f96), laid
# by hand rather than left to the keys' blend and knee_clear (whose pick of
# the knee's side flipped from one edge to the other as an ankle swept
# under her: the right knee thrown 68 cm in a frame). Per side: (frame,
# ankle as a foot control's pos, foot turn or None, the knee's place). The
# knees come forward as the feet are drawn back along the ground, settle
# on the ground in the side-sit, and stay there, barely moving, while the
# hips go up over them and back down onto the heels; the feet, unweighted
# then, lift a little and come in behind them. From the side-sit on, the
# knee leads (its place exact, the foot following on the shin). The foot
# turns are the kneel's, from where each knee lands (_sbh_leg).
_SBH_LEGS = {
    # (The side-sit's places: on the circle the f62 hip and ankle allow, the
    # joint 47 mm up, so the kneecap just meets the ground.)
    "r": [(48, (0.28, -0.05, 0.06), None, (0.06, 0.12, 0.40)),
          (62, (-0.13, -0.05, -0.11), None, (-0.154, 0.047, 0.342)),
          (64, (-0.13, -0.05, -0.11), None, (-0.154, 0.047, 0.342)),
          (77, (-0.115, -0.03, -0.115), (-1, 140, 0), (-0.154, 0.047, 0.342)),
          (88, (-0.115, -0.03, -0.115), (-1, 140, 0), (-0.154, 0.047, 0.342))],
    # (The left knee rides up on the right while the legs are drawn up, a
    # knee's breadth over it, and its foot on the right one. Coming up onto
    # the knees it goes out to its side in the air and is set straight down,
    # judge 23b: landing while still going sideways read as a skid.)
    "l": [(48, (0.34, 0.0, 0.10), None, (0.08, 0.235, 0.42)),
          (62, (0.03, -0.05, -0.15), None, (-0.011, 0.047, 0.301)),
          (64, (0.03, -0.05, -0.15), None, (-0.011, 0.047, 0.301)),
          (67, (0.05, -0.035, -0.14), None, (0.04, 0.10, 0.315)),
          (71, (0.09, -0.02, -0.125), None, (0.13, 0.115, 0.335)),
          (73, (0.105, -0.02, -0.12), None, (0.15, 0.10, 0.341)),
          (77, (0.11, -0.03, -0.115), (1, 140, 0), (0.15, 0.047, 0.341)),
          (88, (0.11, -0.03, -0.115), (1, 140, 0), (0.15, 0.047, 0.341))],
}
# Where each knee is set down on the ground: from here its hip is kept a
# thigh's length from it (_sbh_plan).
_SBH_LAND = {"r": 62, "l": 77}

# Her hips from the side-sit up onto her knees and back down onto her heels
# (frame, the hips control's pos, rot): each a thigh's length from where the
# right knee is planted (worked out from the rig's rest hip), so the knee
# stays put as they go round it. Laid over the keys from f62 to f96 (the
# keys alone cut the corner and pushed the knees through the floor).
_SBH_HIPS = [
    (62, (-0.327, -0.920, -0.077), (12, -4, 14)),
    (64, (-0.327, -0.920, -0.077), (12, -4, 14)),
    # (Points every frame or two: between sparser ones the ease cut inside the
    # arc and pressed the planted knee 22 mm down and up, judge 23b.)
    (65, (-0.304, -0.892, -0.082), (11.0, -1.9, 13.0)),
    (66, (-0.283, -0.868, -0.085), (10.2, -0.1, 12.2)),
    (67, (-0.258, -0.841, -0.085), (9.2, 2.0, 11.2)),
    (68, (-0.232, -0.815, -0.083), (8.3, 4.1, 10.3)),
    (69, (-0.208, -0.793, -0.079), (7.4, 5.9, 9.4)),
    (70, (-0.181, -0.769, -0.072), (6.5, 8.0, 8.5)),
    (72, (-0.139, -0.735, -0.057), (5.0, 11.1, 7.0)),
    (73, (-0.096, -0.705, -0.037), (3.6, 14.2, 5.6)),
    (75, (-0.031, -0.667, 0.004), (1.4, 18.9, 3.4)),
    # Up off her hip only to a low kneel, spent, the hips well short of over
    # the knees (judge 23: a full tall kneel read as a fit kneel-up).
    (77, (0.011, -0.647, 0.036), (0, 22, 2)),
    (84, (0.008, -0.695, -0.012), (0.0, 16.4, 1.3)),
    (90, (0.005, -0.749, -0.053), (0.0, 10.8, 0.6)),
    (96, (0.0, -0.80, -0.08), (0, 6, 0)),
]


# The rise from the side-sit onto her knees, slowed and evened (lead 12): at
# the tables' own pace the hips went from still to 36 mm a frame in one
# frame and on unevenly (the shoulders 63, 26, 62 mm a frame), up off the
# ground at 2 m/s, the right hand hung off the shoulder going with them.
# The tables and windows here keep their frames (design frames): clip frame
# fr shows design frame _sbh_u(fr), half speed through the rise, `frames`
# added in all; and along the rise (_SBH_RISE) the
# hips go their path at an even, eased pace (_sbh_rise, _sbh_plan).
_SBH_SLOW = (63.0, 6.0, 0.5, 11)
_SBH_RISE = (64, 77)


def _sbh_u(fr):
    """The design frame clip frame `fr` shows (_SBH_SLOW: from `a` the
    design frames go at `r` a clip frame, eased into and out of over `ramp`,
    until `frames` are added)."""
    a, ramp, r, s = _SBH_SLOW
    flat = s / (1.0 - r) - ramp
    x = min(max(fr - a, 0.0), 2 * ramp + flat)
    lag = x / 2 - ramp / (2 * math.pi) * math.sin(math.pi * x / ramp) if x <= ramp else ramp / 2 + min(x - ramp, flat)
    if x > ramp + flat:
        y = x - ramp - flat
        lag += y / 2 + ramp / (2 * math.pi) * math.sin(math.pi * y / ramp)
    return fr - (1.0 - r) * lag


def _rise_len(path, n=261):
    """(table frames, length gone) along a hips path over the rise: the
    hips' travel and their turn at 25 cm a radian."""
    a, b = _SBH_RISE
    ts = np.linspace(a, b, n)
    q = [path(t) for t in ts]
    d = [0.0] + [np.linalg.norm(np.subtract(q[i]["pos"], q[i - 1]["pos"]))
                 + 0.25 * math.radians(np.linalg.norm(np.subtract(q[i]["rot"], q[i - 1]["rot"]))) for i in range(1, len(q))]
    return ts, np.cumsum(d)


def _sbh_rise(u, lengths):
    """The tables' frame the hips are at, design frame `u` of the rise: the
    path's length (`lengths`, _rise_len) gone along smoothstep's ease."""
    a, b = _SBH_RISE
    ts, L = lengths
    return float(np.interp(L[-1] * smoothstep_((u - a) / (b - a)), L, ts))


def _sbh_table(fr):
    return {"pos": tuple(float(v) for v in _hermite(fr, [(f, q) for f, q, _ in _SBH_HIPS])),
            "rot": tuple(float(v) for v in _hermite(fr, [(f, r) for f, _, r in _SBH_HIPS]))}


def _hip_at(rig, side, hips):
    """Where a hips control puts a hip joint."""
    I = rig.I
    p0 = rig.prest[I["pelvis"]]
    return p0 + np.asarray(hips["pos"], float) + qrot(qeuler(*hips["rot"]), rig.prest[I[f"thigh_{side}"]] - p0)


def _sbh_foot(side, fr):
    """A foot control at one of _SBH_LEGS' frames, for the keys."""
    # (Only the keys' first solve sees this turn: from f35 to f95 the legs
    # are laid over them. Where a point has none, the kneel's.)
    turn = next(r for f, _, r, _ in _SBH_LEGS[side] if f >= fr and r is not None)
    for f, pos, rot, knee in _SBH_LEGS[side]:
        if f == fr:
            return {"pos": pos, "rot": turn, "pole": (0.1 if side == "l" else -0.1, 0, 1)}
    raise KeyError(fr)


def _on_thigh(keyed, hip, knee, side_w, w, u=0.55, off=(0.17, 0.21), settle=0.0):
    """A left hand laid on the thigh from hip to knee, `u` of the way down
    it, the wrist `off` from its line, the fingers along it toward the knee
    (side_w 0), or hanging free at its outside, the palm toward it and the
    thumb forward (1); turned `settle` of the way to the keyed hand's own
    way (the heels key's palm up, coming to rest); blended `w` over the
    keyed hand. (Her thigh's surface
    stands 0.13-0.14 from that line on top, 0.11-0.12 at the outside,
    measured on her body: on top the wrist rides about 3.5 cm over it.)"""
    a = (knee - hip) / np.linalg.norm(knee - hip)
    top = np.array([0.0, 1.0, 0.0]) - a * a[1]
    top = top / np.linalg.norm(top)
    out_ = np.array([1.0, 0.0, 0.0]) - a * a[0]
    out_ = out_ / np.linalg.norm(out_)
    d = slerp_dir(top, out_, side_w)
    # (Lifted wider on its way round the thigh's front edge.)
    reach = off[0] + (off[1] - off[0]) * side_w + 0.05 * math.sin(math.pi * side_w)
    pos = hip + a * (u * np.linalg.norm(knee - hip)) + d * reach - a * 0.06
    blade = slerp_dir(np.cross(a, d), (0.0, 0.0, 1.0), side_w)
    a = slerp_dir(a, (0.0, -1.0, 0.0), side_w)
    at = np.asarray(keyed["pos"], float) * (1 - w) + pos * w
    k0 = np.asarray(keyed.get("knuckles", a), float)
    b0 = np.asarray(keyed.get("blade", blade), float)
    a, blade = slerp_dir(a, k0, settle), slerp_dir(blade, b0, settle)
    return {**{k: v for k, v in keyed.items() if k not in ("pos", "knuckles", "blade", "arc")}, "pos": tuple(at),
            "knuckles": tuple(slerp_dir(k0, a, w)), "blade": tuple(slerp_dir(b0, blade, w))}


def _hermite(fr, pts):
    """A value along (frame, value) points: still at the first and last and
    wherever two points hold the same value, Catmull-Rom between."""
    ts = [t for t, _ in pts]
    vs = [np.asarray(v, float) for _, v in pts]
    if fr <= ts[0]:
        return vs[0]
    if fr >= ts[-1]:
        return vs[-1]
    k = max(i for i in range(len(ts) - 1) if ts[i] <= fr)

    def tan(i):
        if i == 0 or i == len(ts) - 1 or np.allclose(vs[i], vs[i - 1]) or np.allclose(vs[i], vs[i + 1]):
            return np.zeros_like(vs[i])
        return (vs[i + 1] - vs[i - 1]) / (ts[i + 1] - ts[i - 1])

    h = ts[k + 1] - ts[k]
    u = (fr - ts[k]) / h
    h00, h10, h01, h11 = 2 * u ** 3 - 3 * u ** 2 + 1, u ** 3 - 2 * u ** 2 + u, -2 * u ** 3 + 3 * u ** 2, u ** 3 - u ** 2
    return h00 * vs[k] + h10 * h * tan(k) + h01 * vs[k + 1] + h11 * h * tan(k + 1)


def _euler(q):
    """(yaw, pitch, roll) of a turn: rig.qeuler undone."""
    m = qmatrix(q)
    return (math.degrees(math.atan2(m[0, 2], m[2, 2])), math.degrees(math.asin(max(-1.0, min(1.0, -m[1, 2])))),
            math.degrees(math.atan2(m[1, 0], m[1, 1])))


# sit_back_heels' right hand on the ground: where the forearm left it, and
# under her right shoulder as she leans on it in the side-sit (the fingers
# out to her right, the elbow back); and how far she leans onto it (spine
# roll, degrees).
SBH_HAND_R = ({"pos": (-0.508, 0.05, 0.235), "pole": (-0.3, -1.0, -0.4), "knuckles": (-0.5, 0.0, 1.0)},
              {"pos": (-0.65, 0.05, -0.03), "pole": (-0.2, 0.3, -1.0), "knuckles": (-1.0, 0.0, 0.35)})
SBH_LEAN = 22.0
# The left hand onto her left thigh as it comes round (design frames: from, over).
SBH_ONTHIGH = (54.0, 6.0)
# How far it lifts off the thigh on the way (m), and how many degrees of her
# lean she sits up out of while the right hand is in the air (f36-54).
SBH_LIFT_L = 0.03
SBH_UPRIGHT = 15.0
# The right hand's hop to under her shoulder (clip frames from f34), and its
# fingers let go of the ground (design frames: from, over).
SBH_HOP = 20.0
SBH_LIFT = (62.5, 2.5)
SBH_HOP_LAY = 0.2  # (the share of the hop over which the fingers let go and lay again)
# The most of an arm's length her hands use in it (Rig: "reach"): kneeling
# up, both arms hung locked straight with the hands dragged after them.
SBH_REACH = 0.95

# sit_back_heels' right hand from pushing off the ground to resting palm up
# on her right thigh as she sits back (design frame, wrist place): the way of
# least top speed that stays within 445 mm (on her, 91% of the arm) of her
# shoulder and 35 mm higher off her thigh's line than it rests until it is
# set down, made the smoothest within 8% of that (lead 13, worked out over
# the shoulder's and thigh's paths in build v28). Hung off the shoulder at
# its reach, the hand had run with it at 35 mm a frame and then swung in at
# 29 as the shoulder stopped, the fingertips at 48-51. Here the arm trails out and
# back as she comes up and the hand comes round onto the thigh after. (Work
# it out again if her rise or the keys that carry her shoulder change.)
SBH_PUSH_R = [
    (64.91, (-0.649, 0.046, -0.028)), (66.41, (-0.636, 0.074, -0.017)), (67.5, (-0.615, 0.125, -0.003)),
    (68.5, (-0.594, 0.178, 0.01)), (69.5, (-0.573, 0.231, 0.021)), (70.5, (-0.553, 0.285, 0.033)),
    (71.5, (-0.53, 0.337, 0.045)), (72.5, (-0.505, 0.386, 0.06)), (73.5, (-0.476, 0.429, 0.075)),
    (74.5, (-0.444, 0.462, 0.092)), (75.5, (-0.408, 0.486, 0.108)), (76.59, (-0.371, 0.498, 0.124)),
    (78.09, (-0.332, 0.499, 0.139)), (80.0, (-0.294, 0.49, 0.15)), (82.0, (-0.257, 0.471, 0.159)),
    (84.0, (-0.222, 0.444, 0.163)), (86.0, (-0.191, 0.412, 0.164)), (88.0, (-0.165, 0.378, 0.161)),
    (90.0, (-0.145, 0.345, 0.155)), (92.0, (-0.131, 0.316, 0.148)), (94.0, (-0.123, 0.297, 0.142)),
    (96.0, (-0.12, 0.29, 0.14)),
]
# Its turn, from flat on the ground (Rig._planted's) to palm up on the
# thigh (the heels key's, as knuckles and blade): 153 degrees, done mostly where
# the hand goes slowest (_paced; spread evenly, the turn carried the
# fingertips 41 mm a frame as the wrist went 27).
SBH_PUSH_TURN = ((-0.1, -0.35, 1.0), (-1.0, 0.0, -0.1))


# The left hand back from where it hung at her left thigh's outside onto its
# top, palm up, as she sits back (clip frames f86-f107; design frame, wrist
# place): worked out as SBH_PUSH_R, kept 80 mm higher off the thigh's line
# than it rests until it is set down (35 let the fingers into the thigh) (lead 13; left
# to the keys it hung at full stretch, then came round in 8 frames at 34 mm a
# frame, the fingertips 51-55); then carried up to 40 mm further out and 26 mm
# higher about design f82 (lead 14: the palm turning up swept the ring and
# pinky tips 23 mm into the thigh's outside at f90-94); and its turn, from how
# it hung to the heels key's.
SBH_BACK_L = [
    (76.01, (0.304, 0.36, 0.166)), (77.27, (0.305, 0.362, 0.166)), (79.01, (0.309, 0.379, 0.168)),
    (81.0, (0.311, 0.405, 0.174)), (83.0, (0.295, 0.427, 0.181)), (85.0, (0.257, 0.43, 0.188)),
    (87.0, (0.213, 0.419, 0.19)), (89.0, (0.177, 0.398, 0.185)), (91.0, (0.152, 0.366, 0.173)),
    (93.0, (0.133, 0.327, 0.156)), (95.0, (0.122, 0.296, 0.143)), (96.0, (0.12, 0.29, 0.14)),
]
SBH_BACK_TURN = (((0.046, -0.99, 0.136), (-0.042, 0.134, 0.99)), ((0.1, -0.35, 1.0), (1.0, 0.0, -0.1)))

def _even(x, e=0.15):
    """0..1 at an even pace, eased in and out over `e` of the way at each end."""
    x = min(max(x, 0.0), 1.0)
    if x < e:
        return x * x / (2 * e * (1 - e))
    if x > 1 - e:
        return 1.0 - (1 - x) ** 2 / (2 * e * (1 - e))
    return (x - e / 2) / (1 - e)



_PACED = {}


def _paced(path, a, b, floor=12.0, add=5.0, power=3, box=7, ramp=5):
    """How much of a hand's turn is done by each clip frame a..b as it goes
    along `path` (a design-frame table of wrist places): a frame's share as
    1 / (its speed in mm, at least `floor`, + `add`) ** `power`, smoothed
    over `box` frames and eased in and out over `ramp`; as (frames, done)."""
    key = (id(path), a, b)
    if key not in _PACED:
        at = np.array([_hermite(_sbh_u(f), path) for f in range(a, b + 1)], float)
        v = np.linalg.norm(np.diff(at, axis=0), axis=1) * 1040
        w = 1.0 / (np.maximum(v, floor) + add) ** power
        w = np.convolve(np.pad(w, box // 2, mode="edge"), np.ones(box) / box, mode="valid")
        k = np.arange(len(w))
        w = w * np.minimum(1.0, np.minimum((k + 0.5) / ramp, (len(w) - k - 0.5) / ramp))
        done = np.concatenate([[0.0], np.cumsum(w)])
        _PACED[key] = (np.arange(a, b + 1), done / done[-1])
    return _PACED[key]

def _basis_q(knuckles, blade):
    z = np.asarray(blade, float) / np.linalg.norm(blade)
    y = np.asarray(knuckles, float) - z * np.dot(knuckles, z)
    y = y / np.linalg.norm(y)
    return qfrom_basis(np.cross(y, z), y, z)

# The lowest the ball of a foot's joint and its toes' tips go in
# sit_back_heels' laid legs, as (along the ankle-to-ball line, height):
# standing, the ball's joint is 37 mm over its pad; the tips are about a
# third again past it, a centimetre or two thick.
SBH_TOES = ((1.0, 0.045), (1.4, 0.02))


def _sbh_plan(rig, p, first, last, ends):
    """sit_back_heels' legs and hips from f34 to f96, worked out once from
    the keys' first solve `p` (`first`, `last`: the f34 and f96 keys' foot
    controls; `ends`: per side the knees those two frames end up with):
    per side the (frame, ankle, foot turn, knee place) points from
    those keys' own legs through _SBH_LEGS, the thigh and shin lengths, and
    at any design frame from f62 the hips along _SBH_HIPS, moved the least that keeps
    each knee on the ground a thigh's length from its hip (so it stays put
    as the hips go round it: judge 23b, eased hips cut inside the arc and
    pressed the planted knee in and out)."""
    I = rig.I
    plan = {"pts": {}, "l1": {}, "l2": {}, "hips": {}}
    for s in "lr":
        plan["l1"][s] = float(np.linalg.norm(rig.prest[I[f"calf_{s}"]] - rig.prest[I[f"thigh_{s}"]]))
        plan["l2"][s] = float(np.linalg.norm(rig.prest[I[f"foot_{s}"]] - rig.prest[I[f"calf_{s}"]]))
        plan["pts"][s] = ([(34, first[f"foot_{s}"]["pos"], first[f"foot_{s}"]["rot"], ends[s][0])] + _SBH_LEGS[s]
                          + [(96, last[f"foot_{s}"]["pos"], last[f"foot_{s}"]["rot"], ends[s][1])])

    def place(s, f):
        return np.asarray(_hermite(f, [(g, k) for g, _, _, k in plan["pts"][s]]), float)

    def project(h, f):
        """A hips control `h` moved the least that keeps each planted knee a
        thigh's length from its hip at design frame f."""
        pos, rot = np.asarray(h["pos"], float), h["rot"]

        def resid(at):
            return [np.linalg.norm(_hip_at(rig, s, {"pos": at, "rot": rot}) - place(s, f)) - plan["l1"][s] for s in "rl"]

        # The left knee comes into it as it is set down.
        w = {"r": 1.0, "l": smoothstep_((f - _SBH_LAND["l"] + 4) / 4.0)}
        e0 = resid(pos)
        want = [(1.0 - w[s]) * e for s, e in zip("rl", e0)]
        for _ in range(8):
            e = resid(pos)
            rows = [(_hip_at(rig, s, {"pos": pos, "rot": rot}) - place(s, f)) for s in "rl"]
            J = np.array([r / np.linalg.norm(r) for r in rows])
            r = np.array(e) - np.array(want)
            pos = pos - J.T @ np.linalg.solve(J @ J.T + 1e-9 * np.eye(2), r)
        return {"pos": tuple(float(v) for v in pos), "rot": tuple(float(v) for v in rot)}

    def hips(f):
        """The hips at design frame f (from f62). Along the rise they go the
        kept path (the table's, moved to keep the knees) at an even, eased
        pace: timed along the table's own path, the moving-in that keeps the
        right knee came on over two frames and the hips went 14, 10, 16 mm a
        frame (lead 13)."""
        if f in plan["hips"]:
            return plan["hips"][f]
        a, b = _SBH_RISE
        if a < f < b:
            if "rise" not in plan:
                # The kept path, densely, then gone along by its own length.
                table = _rise_len(_sbh_table)
                us = np.linspace(a, b, 261)
                kept = [project(_sbh_table(_sbh_rise(u, table)), u) for u in us]
                plan["rise"] = (us, _rise_len(lambda u: kept[int(round((u - a) / (b - a) * 260))])[1], kept)
            us, L, kept = plan["rise"]
            x = float(np.interp(L[-1] * smoothstep_((f - a) / (b - a)), L, us))
            i = min(max(int(np.searchsorted(us, x)), 1), len(us) - 1)
            k = (x - us[i - 1]) / (us[i] - us[i - 1])
            plan["hips"][f] = {key: tuple(float(v) for v in np.asarray(kept[i - 1][key]) * (1 - k) + np.asarray(kept[i][key]) * k)
                               for key in ("pos", "rot")}
        else:
            plan["hips"][f] = project(_sbh_table(f), f)
        return plan["hips"][f]

    plan["hips_at"] = hips
    plan["place"] = place
    return plan


def _sbh_leg(rig, plan, p, fr, side):
    """A foot control for sit_back_heels between its keys' f34 and f96, along
    the plan's points (_sbh_plan). Drawn up (to f62), the ankle leads: the
    knee goes on the circle its hip and ankle allow nearest its place
    (_knee_on), so it goes round with the leg and never across. From the
    side-sit the knee leads: put a thigh's length from the hip toward its
    place (exactly on it once planted), the ankle a shin's length from it
    toward its own point. The foot rides the shin, turned on it only as an
    ankle can (judge 23b: turned in the world, the feet had twisted up to 90
    degrees about the shin and rolled 20 degrees a frame): from the lying
    foot to the kneel's pointed one, slowly while the feet are dragged (a
    pointed foot drives its toes into the ground under a sloping shin), the
    rest as the shins come down flat."""
    I = rig.I
    th = I[f"thigh_{side}"]
    rest_y = rig.prest[I[f"foot_{side}"]][1]
    s = 1 if side == "l" else -1
    pts = plan["pts"][side]
    l1, l2 = plan["l1"][side], plan["l2"][side]

    def leg(f):
        pos = np.asarray(_hermite(f, [(g, a) for g, a, _, _ in pts]), float)
        hip = _hip_at(rig, side, plan["hips_at"](f)) if f >= 62 else p[int(round(f)), th]
        ankle = np.array([pos[0] + s * rig.feet_out, rest_y + pos[1], pos[2]])
        want = plan["place"](side, f)
        if f < 62:
            return pos, hip, _knee_on(rig, side, hip, ankle, want), ankle
        knee = hip + l1 * (want - hip) / np.linalg.norm(want - hip)
        ankle = knee + l2 * (ankle - knee) / np.linalg.norm(ankle - knee)
        return np.array([ankle[0] - s * rig.feet_out, ankle[1] - rest_y, ankle[2]]), hip, knee, ankle

    def shin(f):
        # The shin's own axes: across the knee's bend, and along it.
        _, hip, knee, ankle = leg(f)
        y = (ankle - knee) / np.linalg.norm(ankle - knee)
        x = np.cross(knee - hip, ankle - knee)
        x = x / np.linalg.norm(x)
        return qfrom_basis(x, y, np.cross(x, y))

    def on_shin(f, rot):
        return qmul(qinv(shin(f)), qeuler(*rot))

    # The kneel's turns (from f77), riding the shin.
    turns = [(g, r) for g, _, r, _ in pts if r is not None and g >= 77]
    lie, kneel = on_shin(34, pts[0][2]), on_shin(turns[0][0], turns[0][1])
    pos, hip, knee, ankle = leg(fr)
    if fr < turns[0][0]:
        u = 1.0 if fr >= 66 else float(_hermite(fr, [(34, 0.0), (48, 0.2), (66, 1.0)]))
        q = qmul(shin(fr), qslerp(lie, kneel, u))
    else:
        k = max(i for i in range(len(turns) - 1) if turns[i][0] <= fr)
        (f0, r0), (f1, r1) = turns[k], turns[k + 1]
        q = qmul(shin(fr), qslerp(on_shin(f0, r0), on_shin(f1, r1), smoothstep_((fr - f0) / (f1 - f0))))
    # The ball and toes kept out of the ground: where the turn on the shin
    # would put them under, the foot is tipped up about the ankle just enough
    # (as a dragged foot is pushed up by the ground; v17 had it 51 mm in).
    vb = rig.prest[I[f"ball_{side}"]] - rig.prest[I[f"foot_{side}"]]
    for reach, floor in SBH_TOES:
        b = qrot(q, vb * reach)
        low = floor - ankle[1]
        if b[1] < low:
            hz = np.array([b[0], 0.0, b[2]])
            n = np.linalg.norm(b)
            y = min(low, n * 0.98)
            to = hz / max(np.linalg.norm(hz), 1e-9) * math.sqrt(max(n * n - y * y, 0.0)) + np.array([0.0, y, 0.0])
            q = qmul(qbetween(b, to), q)
    # (The solver aims the knee at its own unsolved place plus the pole, so a
    # short pole let that place tip the knee off this one by up to 43 mm, the
    # planted right knee pumping as the hips went round, judge 23b G2: a long
    # one makes the place negligible.)
    spec = {"pos": tuple(float(v) for v in pos), "rot": _euler(q), "pole": tuple(1000.0 * (knee - (hip + ankle) / 2)), "laid": True}
    return spec, hip, knee


def _knee_on(rig, side, hip, ankle, want, floor=0.05):
    """Where a knee goes for a hip and an ankle: on the circle they allow,
    nearest `want`, and, if that is under `floor`, turned round the circle
    the shorter way until it is on it (so it leaves and meets the ground
    by degrees, never by a pick from one edge to the other)."""
    I = rig.I
    l1 = np.linalg.norm(rig.prest[I[f"calf_{side}"]] - rig.prest[I[f"thigh_{side}"]])
    l2 = np.linalg.norm(rig.prest[I[f"foot_{side}"]] - rig.prest[I[f"calf_{side}"]])
    d = ankle - hip
    dist = min(max(np.linalg.norm(d), abs(l1 - l2) + 1e-4), (l1 + l2) * 0.9995)
    u = d / max(np.linalg.norm(d), 1e-9)
    a = (l1 * l1 - l2 * l2 + dist * dist) / (2 * dist)
    c = hip + u * a
    r = math.sqrt(max(0.0, l1 * l1 - a * a))
    e1 = (want - c) - u * np.dot(want - c, u)
    if np.linalg.norm(e1) < 1e-6:
        return want
    e1 = e1 / np.linalg.norm(e1)
    e2 = np.cross(u, e1)
    at = lambda th: c + r * (math.cos(th) * e1 + math.sin(th) * e2)
    if at(0.0)[1] >= floor:
        return at(0.0)
    for k in range(1, 181):
        for sg in (1, -1):
            th = math.radians(sg * k)
            if at(th)[1] >= floor:
                lo, hi = math.radians(sg * (k - 1)), th
                for _ in range(20):
                    m = 0.5 * (lo + hi)
                    lo, hi = (lo, m) if at(m)[1] >= floor else (m, hi)
                return at(hi)
    return at(0.0)


# Where sit_back_heels' hip limit starts to press and what it tends to.
HIP_SOFT = (55.0, 85.0)


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
                   hand_l=HAND_ON_HIP_L), "auto"),
        # Sat up sideways on the right hip, the legs round to her left.
        (62, z, "auto"),
        # Leaning forward and onto the right hand, gathering to rise.
        # (Into the first frames of the rise, lead 13: in the two frames before
        # it the neck went 11 to 31 mm a frame.)
        (67, merge(z, spine=(-8, 18, -2), neck=(4, 10, -2), head=(2, 12, 0)), "auto"),
        # Over onto her knees: the hips up off the ground and over them, the
        # right leg drawn under; the right hand pushes off the ground. (From
        # here the keys are 11 frames on from the design frames: _SBH_SLOW.)
        (88, {"hips": {"pos": _SBH_HIPS[6][1], "rot": _SBH_HIPS[6][2]}, "spine": (2, 24, -2), "neck": (0, 8, 0), "head": (0, 10, 0),
              "foot_l": _sbh_foot("l", 77), "foot_r": _sbh_foot("r", 77),
              "hand_r": {"pos": (-0.16, 0.30, 0.22), "pole": (-0.6, -0.5, -0.4), "knuckles": (-0.1, -0.4, 1)},
              "hand_l": {"pos": (0.15, 0.32, 0.20), "pole": (0.7, -0.5, -0.3), "knuckles": (0.1, -0.5, 1)},
              "clav_l": (0, 6), "clav_r": (4, 6), "fingers_l": RELAXED, "fingers_r": RELAXED}, "auto"),
        # Back onto her heels, the hips going round on the planted knees (a
        # thigh's length from them all the way down), the hands to her thighs;
        # a breath.
        (107, _heels(look=0.3, hands=0.0, breath=1.0), "ease"),
        (129, _heels(look=0.5, hands=0.0, breath=-0.5), "ease"),
        # The hands come up before her, and she looks down at them.
        (153, _heels(look=1.0, hands=1.0), "ease"),
        (191, _heels(look=1.0, hands=1.0, breath=0.6), "ease"),
    ]
    plan = {}

    def contacts(fr, g, p, pose):
        # The knees kept on the ground, not through it, whatever the legs do.
        out = {f"foot_{s}": knee_clear(rig, p, fr, s, pose[f"foot_{s}"]) for s in "lr" if f"foot_{s}" in pose}
        # (Below, frames are design frames: _SBH_SLOW.)
        u = _sbh_u(fr)
        # The left hand on her thigh from the first frame (HAND_ON_HIP_L),
        # lifted a little and set down again mid-thigh as she sits up (f34-54),
        # where the side-sit has it (below).
        if u < 60:
            t = smoothstep_((u - 34) / 20.0)
            on_l = {"u": HIP_REST_L[0] + (0.55 - HIP_REST_L[0]) * t, "off": HIP_REST_L[1] + SBH_LIFT_L * math.sin(math.pi * t)}
            if u <= 34:
                out["hand_l"] = _hand_on_thigh_l(rig, p, fr, pose, **on_l)
        # From her side to her heels the legs go as laid by hand.
        if 34 < u < 96:
            if not plan:
                # The knees at f34 and f96 as those frames are solved (with
                # knee_clear), for the legs to leave and meet them exactly.
                track, ends = Track(_one_frame(rig, keys)), {"l": [], "r": []}
                for f in (34, 96 + _SBH_SLOW[3]):
                    at = track(f)
                    at = {**at, **{f"foot_{s}": knee_clear(rig, p, f, s, at[f"foot_{s}"]) for s in "lr"}}
                    r_, q_ = rig.solve(at)
                    _, at_p = rig.sk.fk(r_[None], q_[None])
                    for s in "lr":
                        ends[s].append(at_p[0, rig.I[f"calf_{s}"]].copy())
                plan.update(_sbh_plan(rig, p, start, _heels(look=0.3, hands=0.0, breath=1.0), ends))
            if u >= 62:
                out["hips"] = plan["hips_at"](u)
            legs = {s: _sbh_leg(rig, plan, p, u, s) for s in "lr"}
            out.update({f"foot_{s}": legs[s][0] for s in "lr"})
            if u < 60:
                out["hand_l"] = _hand_on_thigh_l(rig, p, fr, pose, hip=legs["l"][1], knee=legs["l"][2], **on_l)
            # The left hand on her left thigh from the side-sit, pressing on
            # it as she comes up, then at its outside while the thigh stands
            # (judge 23: left to the keys it sank into the thigh), settling
            # onto its top again as she sits back (the heels key's own).
            w = smoothstep_((u - SBH_ONTHIGH[0]) / SBH_ONTHIGH[1]) * (1.0 - smoothstep_((u - 91) / 4.0))
            if w > 0:
                free = smoothstep_((u - 65) / 14.0) * (1.0 - smoothstep_((u - 79) / 15.0))
                # Coming to rest palm up as the heels key has it (judge 23 round
                # b: turned over from palm down in the last frames, the
                # fingers swung 20 cm a frame).
                out["hand_l"] = _on_thigh(out.get("hand_l", pose["hand_l"]), legs["l"][1], legs["l"][2], free, w, settle=smoothstep_((u - 72) / 22.0))
                # Flatter on the thigh, the fingers not curled into it.
                fl, k = pose["fingers_l"], w * (1.0 - free)
                if isinstance(fl, dict):
                    out["fingers_l"] = {**fl, "curl": fl["curl"] * (1 - k) + 0.1 * k}
            if fr >= 86:
                # Back onto the thigh's top along SBH_BACK_L, turning palm up
                # the while (the elbow's way eased from the thigh's to the key's).
                k = _even((fr - 86) / 21.0)
                q = qslerp(_basis_q(*SBH_BACK_TURN[0]), _basis_q(*SBH_BACK_TURN[1]), k)
                was = out.get("hand_l", pose["hand_l"])
                out["hand_l"] = {**_aimed_only(pose["hand_l"]), "pos": tuple(_hermite(u, SBH_BACK_L)),
                                 "knuckles": tuple(qrot(q, [0, 1.0, 0])), "blade": tuple(qrot(q, [0, 0, 1.0])), "aim": 1.0,
                                 "pole": tuple(slerp_dir(was.get("pole", pose["hand_l"]["pole"]), pose["hand_l"]["pole"], k))}
                fl = pose["fingers_l"]
                if isinstance(fl, dict):
                    out["fingers_l"] = {**fl, "curl": fl["curl"] * (1 - 0.1 * (1 - k)) + 0.01 * (1 - k)}
        # The right hand: planted where the forearm left it as she pushes up
        # off it, moved once to under her shoulder, and leant on there through
        # the side-sit (judge 23b: left to the keys it skidded, then hung off
        # a locked arm 13 cm over the ground), until she pushes off it to come
        # up onto her knees. She leans toward it the while, as one does onto a
        # straight arm.
        if 30 <= u < 96:
            if u < 84:
                lean = smoothstep_((u - 34 - (SBH_HOP - 16.0)) / 14.0) * (1.0 - smoothstep_((u - 64) / 10.0))
                # Sat up nearer upright while neither hand bears her (lead 14,
                # judge 37: tilted 30 degrees over the hopping hand, nothing held
                # her), and over again onto it as it lands.
                up_ = SBH_UPRIGHT * math.sin(math.pi * min(1.0, max(0.0, (u - 36) / 18.0))) ** 2
                out["spine"] = tuple(np.asarray(pose["spine"], float) + (0.0, 0.0, SBH_LEAN * lean - up_))
                out["neck"] = tuple(np.asarray(pose["neck"], float) - (0.0, 0.0, 0.35 * (SBH_LEAN * lean - up_)))
            keyed = pose["hand_r"]
            # (Pressed flat as the weight comes onto it.)
            first, under = {**SBH_HAND_R[0], "plant": smoothstep_((fr - 24) / 10.0)}, {**SBH_HAND_R[1], "plant": 1.0}
            if fr < 34:
                hand = first
            elif fr < 34 + SBH_HOP:
                # Lifted off as it leaves, flat again as it lands; turned on
                # the way.
                # (Over 16 frames, lead 13: over 13 the wrist ran 40 mm a
                # frame, the fingertips 60-86; at an even pace it landed hard.)
                # (Over 20, lead 14, the fingers letting go and laying again
                # in its first and last fifth, where the wrist is slow: over 16
                # the fingertips ran 40-48 mm a frame; the lean waits for it.)
                t = smoothstep_((fr - 34) / SBH_HOP)
                hand = {**_hop(first, under, t, 0.05 * math.sin(math.pi * t)),
                        "plant": max(1.0 - smoothstep_(t / SBH_HOP_LAY), smoothstep_((t - 1.0 + SBH_HOP_LAY) / SBH_HOP_LAY)),
                        "pole": tuple(slerp_dir(first["pole"], under["pole"], t))}
                # Kept flat, turned from one planted way to the other (lead 13:
                # let go of by the plant, it rolled to ride the forearm and back,
                # the fingertips 60-89 mm a frame).
                q1 = rig._planted("r", SBH_HAND_R[0], None, np.array([0.0, 0.0, 0.0, 1.0]))
                q = qslerp(q1, rig._planted("r", SBH_HAND_R[1], None, np.array([0.0, 0.0, 0.0, 1.0])), t)
                hand.update(knuckles=tuple(qrot(q, [0, 1.0, 0])), blade=tuple(qrot(q, [0, 0, 1.0])), aim=1.0)
            elif u <= 64:
                # (The fingers let go of the ground just before the hand
                # leaves it, the palm kept flat: let go of as it rose, they
                # peeled off at 39 mm a frame, lead 13.)
                hand = {**under, "plant": 1.0 - smoothstep_((u - SBH_LIFT[0]) / SBH_LIFT[1])}
                if u > SBH_LIFT[0]:
                    q = rig._planted("r", SBH_HAND_R[1], None, np.array([0.0, 0.0, 0.0, 1.0]))
                    hand.update(knuckles=tuple(qrot(q, [0, 1.0, 0])), blade=tuple(qrot(q, [0, 0, 1.0])), aim=1.0)
            else:
                # Pushed off (the plant let go by then: 13 cm up its finger
                # laying stops at once, Rig._lay) and brought round
                # to her thigh along SBH_PUSH_R, turning palm up the while
                # (clip frames f65-f107; the turn _paced, done by f106).
                k = float(np.interp(fr, *_paced(SBH_PUSH_R, 64, 106)))
                q = qslerp(rig._planted("r", SBH_HAND_R[1], None, np.array([0.0, 0.0, 0.0, 1.0])), _basis_q(*SBH_PUSH_TURN), k)
                hand = {**_aimed_only(keyed), "pos": tuple(_hermite(u, SBH_PUSH_R)), "plant": 1.0 - smoothstep_((u - SBH_LIFT[0]) / SBH_LIFT[1]),
                        "knuckles": tuple(qrot(q, [0, 1.0, 0])), "blade": tuple(qrot(q, [0, 0, 1.0])), "aim": 1.0,
                        "pole": tuple(slerp_dir(under["pole"], keyed["pole"], k))}
            out["hand_r"] = hand
        # Neither arm hung locked straight with its hand dragged after it
        # (eased in on the left from where it leaves the ground, on the right
        # once its hand is lifted to move, out by the heels).
        if 30 <= u < 96:
            end = 1.0 - smoothstep_((u - 88) / 8.0)
            # (The hands' ways laid by hand, SBH_PUSH_R and SBH_BACK_L, keep within reach themselves.)
            for s, k in (("l", smoothstep_((fr - 30) / 10.0) * (fr < 86)), ("r", smoothstep_((fr - 36) / 6.0) * (u <= 64))):
                if k * end > 0:
                    out[f"hand_{s}"] = {**out.get(f"hand_{s}", pose[f"hand_{s}"]), "reach": SBH_REACH, "reach_w": k * end}
        # The right forearm on the ground as she starts up off it.
        if fr < 30:
            # Coming onto the hand where it is first planted (SBH_HAND_R), the
            # hand laid flat on the ground as the weight comes onto it; its
            # fingers kept out of the ground from the first frames (lead 13:
            # the pinky was 3-5 cm into it until f29, then thrown out of it
            # in a frame as the plant began).
            w = 1.0 - smoothstep_((fr - 6) / 24.0)
            hand, pole = forearm_on_ground(rig.sk, p, fr, "r", PROP_TOWARD, ground=0.035)
            keyed, to = pose["hand_r"], SBH_HAND_R[0]
            at = hand * w + np.asarray(to["pos"], float) * (1 - w)
            out["hand_r"] = {**_aimed_only(keyed), "pos": tuple(at), "pole": tuple(pole * w + np.asarray(to["pole"], float) * (1 - w)),
                             "knuckles": tuple(slerp_dir(to["knuckles"], PROP_TOWARD, w)),
                             "plant": smoothstep_((fr - 24) / 10.0), "lay": smoothstep_((fr - 2) / 12.0)}
        return out

    # The side-sit turns her right hip out 64-77 degrees, past the rig's hard
    # 45: here the limit is eased in (Rig._hip_soft) so the knee's swing
    # grows with the turn instead of switching on in a frame.
    rig.hip_soft = HIP_SOFT
    try:
        return contact_build("sit_back_heels", rig, keys, contacts,
                             meta={"layer": "full", "hold": True, "source": "keyed (tools/anim/clips/story.py)", "licence": "own work",
                                   "note": "keyed (C01): from the forearm to sitting sideways, onto her knees and back on her heels, looking at her hands"})
    finally:
        rig.hip_soft = None


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
    from clips.actions import _hop, arm

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
    from clips.actions import _hop, arm
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
    from clips.actions import _hop, arm
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

    from clips.actions import _hop, arm
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


def flinch(rig):
    """A blow taken on the move: the chest caves and twists away from it,
    the shoulders jerk up round the neck and the head snaps back, in two
    frames, and she shakes it off over a third of a second. Laid over a run
    or a cut (the legs keep going, the arms keep what they hold): only the
    back, the shoulders and the head move, so nothing is added to the legs
    or the arms. Big enough to read at 31 m."""
    keys = [
        (0, _still(), "ease"),
        (2, _still(spine=(16, -16, -8), neck=(6, -10, 0), head=(12, -20, -10), clav_l=(14, -8), clav_r=(14, -8)), "ease"),
        (5, _still(spine=(9, -8, -4), neck=(3, -5, 0), head=(7, -10, -5), clav_l=(7, -4), clav_r=(7, -4)), "auto"),
        (14, _still(), "ease"),
    ]
    return build("flinch", rig, keys, meta={"layer": "gesture", "note": "struck on the move: the back caves, the head snaps, 0.47 s"})


ALL = (("lie_side_wake", lie_side_wake), ("sit_back_heels", sit_back_heels), ("reach_coals", reach_coals),
       ("letter", letter), ("kneel_to_stand_snap", kneel_to_stand_snap), ("take_from_log", take_from_log),
       ("cup_hands", cup_hands), ("nod", nod), ("exhale", exhale), ("shiver", shiver), ("flinch", flinch))
# Judged on sheets (still to be judged in the cinematic itself). Anything
# else here is work in progress, built only when named.
JUDGED = {"lie_side_wake", "sit_back_heels", "reach_coals", "nod", "exhale", "shiver", "flinch"}


def clips(rig, want):
    return [f(rig) for name, f in ALL
            if (want and any(w in name for w in want)) or (not want and name in JUDGED)]
