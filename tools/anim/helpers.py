"""Her helper bones: twist bones down each forearm and at each shoulder, and a
share bone at each shoulder, elbow and knee, as AAA rigs have them. This is
the one description of them: tools/assets/heroine_rig.py builds them into her
body (and the hero's) from it, godot/src/Actors/HerJoints.cs drives them in
the game from its copy (godot/art/people/rig_helpers.json, written here), and
the motion tools pose them as the game does.

Why: with only an upper arm, a forearm and a hand, linear skinning can only
blend between them. A forearm turned about its length (the radius rolling
over the ulna) wrings the skin at the elbow or the wrist like a sweet
wrapper, and a bent elbow or knee folds flat at the crease. The helpers
spread the turn and the bend over the flesh as a body does:

- **forearm twist** (`lowerarm_twist_01`, `_02`): the hand's turn about the
  forearm shared along it, two fifths and four fifths, as the radius rolls;
  the forearm bone itself never rolls on the elbow (it is the ulna, on a
  hinge): whatever roll a clip gives it is handed down to the hand;
- **shoulder twist** (`upperarm_twist_01`): the upper arm's turn about its
  length, half undone at the shoulder, where the deltoid is held by the
  shoulder girdle; on her (Body 5 A2) a chain of four (`_01`-`_04`) and five
  weight nodes down the humerus carries the roll evenly (SPEC "twist_chain"),
  gated on `upperarm_twist_02` so a body without it moves as before;
- **shares** (`upperarm_share`, `lowerarm_share`, `calf_share`): half the
  joint's bend, carrying the ring of flesh round the joint, so it bends
  round a corner instead of folding; at the elbow and knee also pushed out
  across the bend as a bent tube is (`bulge`, held on the crease side), and
  kept off the crease itself, which folds in deep as it did (`crease`).

They are children of the bones they help, laid along them, and bound where
those bones' weight was, so a body without the driver moves as before.
"""
from __future__ import annotations

import json
import math

import numpy as np

from rig import REPO, Skeleton, qaxis, qbetween, qinv, qmatrix, qmul, qnorm, qrot, qslerp

SPEC_FILE = REPO / "godot" / "art" / "people" / "rig_helpers.json"

SPEC = {
    "helpers": [
        # The shoulder's twist bone, a quarter of the way down the upper arm.
        {"name": "upperarm_twist_01_{s}", "parent": "upperarm_{s}", "kind": "counter_twist", "bone": "upperarm_{s}",
         "at": 0.25, "amount": 0.5},
        # The forearm's, two fifths and four fifths of the way to the wrist.
        {"name": "lowerarm_twist_01_{s}", "parent": "lowerarm_{s}", "kind": "forearm_twist", "bone": "hand_{s}",
         "at": 0.4, "amount": 0.4},
        {"name": "lowerarm_twist_02_{s}", "parent": "lowerarm_{s}", "kind": "forearm_twist", "bone": "hand_{s}",
         "at": 0.8, "amount": 0.8},
        # Shares: at the joint, half its bend.
        {"name": "upperarm_share_{s}", "parent": "clavicle_{s}", "kind": "share", "bone": "upperarm_{s}", "amount": 0.5,
         "bulge": 0.0, "bulge_max": 1.0, "way": "front"},
        {"name": "lowerarm_share_{s}", "parent": "upperarm_{s}", "kind": "share", "bone": "lowerarm_{s}", "amount": 0.5,
         "bulge": 0.45, "bulge_max": 1.45, "pivot": 0.047, "way": "front"},
        # The elbow's point: the share's twin, pushed out across the bend
        # (away from the crease, -Z) by `push` metres eased in from `from`
        # to `to` degrees of bend; it takes the share's weight on the
        # patch weights.point gives it.
        {"name": "lowerarm_point_{s}", "parent": "upperarm_{s}", "kind": "point", "bone": "lowerarm_{s}", "amount": 0.5,
         "share": "lowerarm_share_{s}", "push": 0.03, "from": 70, "to": 145, "way": "front",
         # and drawn in across the bend (its X, the hinge axis) toward
         # `squeeze_x` metres along it, losing `squeeze` of its width there
         # by `to` degrees, eased in from `squeeze_from`: from behind, the
         # tip narrows to a point in line with the forearm's back edge.
         "squeeze": 0.0, "squeeze_x": 0.0, "squeeze_from": 100},
        {"name": "calf_share_{s}", "parent": "thigh_{s}", "kind": "share", "bone": "calf_{s}", "amount": 0.5,
         "bulge": 0.5, "bulge_max": 1.5, "pivot": 0.059, "way": "back"},
        # Her upper arm's twist chain (Body 5 A2, "twist_chain" below): three more counter-twists down the humerus,
        # built into HER body only (extend(chain=True), heroine_rig.add_bones(chain=True)); a body without them (the
        # hero, the NPCs) drives and splits as before. `amount`: how much of the upper arm's roll each undoes.
        {"name": "upperarm_twist_02_{s}", "parent": "upperarm_{s}", "kind": "counter_twist", "bone": "upperarm_{s}",
         "at": 0.25, "amount": 0.525, "chain": True},
        {"name": "upperarm_twist_03_{s}", "parent": "upperarm_{s}", "kind": "counter_twist", "bone": "upperarm_{s}",
         "at": 0.5, "amount": 0.35, "chain": True},
        {"name": "upperarm_twist_04_{s}", "parent": "upperarm_{s}", "kind": "counter_twist", "bone": "upperarm_{s}",
         "at": 0.75, "amount": 0.175, "chain": True},
    ],
    # The forearm bone's own roll on the elbow handed down to the hand.
    "unroll": ["lowerarm_{s}"],
    "weights": {
        # Upper arm: to its twist bone at the shoulder, easing to none this
        # far down the upper arm (smoothly).
        "shoulder_twist_to": 0.55,
        # Forearm: shared between the forearm bone and its twist bones by
        # where a point lies along it (0 elbow, 1 wrist), as hats over these.
        "forearm_nodes": [0.0, 0.4, 0.8],
        # Shares: of a point's blend between the bones above and below, how
        # much the share bone takes (1: a half-and-half point is all its).
        "share": 1.0,
        # The shares cut as a quadratic Bezier (smooth), not a tent: see split.
        "profile": "smooth",
        # (above, below, share)
        "pairs": [["clavicle_{s}", "upperarm_{s}", "upperarm_share_{s}"], ["upperarm_{s}", "lowerarm_{s}", "lowerarm_share_{s}"],
                  ["thigh_{s}", "calf_{s}", "calf_share_{s}"]],
        "cap": 4,
        # The crease (the inside of the bend, the share's `way`): none of the
        # share there, eased out from the joint's line to `reach` metres into
        # the crease. A share there holds the crease's skin out at its rest
        # distance, which leaves it just past the point where a bend folds
        # it: a shallow fold, turned over at the skin itself, which shows at
        # the crease's ends (the tick behind the knee at 120-145). Without
        # it the crease folds in deep, with the bones each side, hidden
        # under them as before the helpers; the share rounds the outside.
        "crease": {"cut": 1.0, "reach": 0.035},
        # The point of a joint (the elbow's olecranon): on the side away
        # from the crease, a patch round the joint's line whose share weight
        # goes to its point bone (a share's twin, pushed out from the joint
        # as it bends: helpers kind "point"), so the tip stands out of the
        # round the share makes. A step in the blend there instead (the
        # bone below carrying the tip) turned the tip's faces over past 120
        # degrees: across a short band the skin is blended between places
        # 145 degrees apart round the joint, and the chord runs into it.
        # half/fade: the patch round the back, degrees (full, then eased
        # out); reach/feather: along the bone either side of `at`, metres.
        "point": {"lowerarm_point_{s}": {"half": 20, "fade": 40, "at": 0.008, "reach": 0.0, "feather": 0.03}},
    },
    # Corrective shapes (pose-space, as Maya's): a move of her skin at rest
    # that a joint's bend eases in, made here (corrective), built into her
    # body and every piece she wears near it as a shape key
    # (heroine_rig.py) and set in the game from the same bend (HerJoints.cs).
    # Bones only blend matrices, so a point standing out of the joint (the
    # olecranon) is beyond them: three helper-bone tries left the elbow,
    # seen from behind, a blunt round cap.
    "correctives": [
        # The elbow's point: bent `full` degrees (bend: drive's measure), the
        # skin at the far side of the bend from the crease pushed out along
        # the bend's outward line (between the upper arm's line and the
        # forearm's, reversed; `lean` -1..1 turns it toward the upper arm or
        # the forearm) by `amount` metres at the tip, falling off smoothly
        # ((1 - r^2)^3: a rounded tip, soft flanks) over `radius` metres:
        # across the hinge, along the bend's plane, and in depth. The tip is
        # her skin's furthest point out along that line within `near` of it.
        # The shape's weight: smoothstep from `from` to `to` degrees of bend
        # (none below `from`). Pieces she wears take the skin's move at the
        # nearest skin point, whole within garment[0] metres of the skin,
        # easing out to none at garment[1].
        {"name": "elbow_point_{s}", "bone": "lowerarm_{s}", "way": "front", "full": 145, "from": 90, "to": 145,
         # (6 mm over 18-26 mm barely showed and read as a nub where it did;
         # broad flanks make the cap a cone with a point: tick.py previews)
         "amount": 0.012, "radius": [0.028, 0.06, 0.045], "lean": 0.0, "near": 0.008, "garment": [0.02, 0.04]},
    ],
    # Panel bones: one centred bone (no {s}) for a hanging front panel (the
    # Reaver's loincloth), a child of the pelvis that swings forward with the
    # leading thigh, so the thigh coming through at a stride's foot strike
    # lifts the panel instead of showing through it (a linear blend of the
    # two thighs averages them: the leading one went through it). panel_turn
    # is the law, HerJoints.cs the game's copy.
    # - rest: at the pelvis's head + `pivot` (metres, her rest axes: +Y up,
    #   +Z her front; 6 cm in front of the pelvis bone at its height, about
    #   6 cm behind the panel's face and 2.5 cm above its top: a pivot inside
    #   her swings the panel's top forward with it, clear of the thigh's
    #   crease, without lifting it into her belly), laid along the panel:
    #   its +Y down, its +Z her front, its +X her right; `length` (Blender).
    # - turn: about her lateral axis (the panel's bottom forward and up) by
    #   amount * softrelu(smooth max of the thighs' forward swing), the swing
    #   read in the pelvis's frame as degrees in her side plane from rest; the
    #   smooth max (polynomial, `soft` degrees wide, less soft/4 so equal
    #   thighs give their own swing) keeps it smooth as the legs cross, and
    #   softrelu (quadratic over the first `soft` degrees) never turns it
    #   back. Damped by up to `spread_damp` as the thighs spread (their mean
    #   abduction from `spread_from` to `spread_to` degrees, smoothstep): on
    #   a seat with the knees apart (sit_log) it lifts 38, not 87.
    # Measured offline on Godot's own poses against the ea6a9417 Reaver build
    # (thigh points inside the panel, run/sprint mean -> frame 14):
    # run_warden 521 -> 0 (f14 2106 -> 0), sprint_warden 478 -> 27 (f14 0),
    # run_reaver 946 -> 33, sprint_reaver 1097 -> 63, walk_tired 1514 -> 0,
    # idle_reaver 0 -> 0; sit_log stretch>1.6x 13% -> 3%, inside 299 -> 161;
    # never into her belly or the trailing thigh.
    # - fall (panel_fall, in time, so only where frames follow each other:
    #   the game, drive's `state`): it rises with the law at once, but falls
    #   as a loose flap does, a first-order lag of `fall_tau` seconds toward
    #   the law and never faster than `fall_rate` degrees a second (15 a
    #   30 fps frame), never below the law (so never into the thigh). On
    #   run_reaver it trails the law's fall by about a frame (90 -> 84, 71,
    #   56, 46 over f6-f9, was 79, 60, 43, 38), the rise and crossovers as
    #   they were.
    #
    # Weighting recipe (heroine_outfits.py, the Reaver's front panel: the
    # loincloth's front piece, the one-piece part FRINGE_ONE moves today):
    # every panel vertex gets W = (1 - k) * W_built + k * panel_front, with
    # W_built its weights as built now (ea6a9417: near the belt pelvis ~0.73,
    # thighs ~0.09 each, spine_01 ~0.09) and k = smoothstep(0, 0.06,
    # top - y), y its rest height and top the panel's top edge (1.047 m on
    # today's body): none at the belt, all of it 6 cm down and below. Keep
    # the thighs' small share in that top band (taking it to the pelvis left
    # the thigh 20-38 mm through the panel's top in a sprint).
    "panels": [
        {"name": "panel_front", "parent": "pelvis", "thighs": ["thigh_l", "thigh_r"], "pivot": [0.0, 0.0, 0.06],
         "length": 0.45, "amount": 1.15, "soft": 12.0, "spread_from": 8.0, "spread_to": 20.0, "spread_damp": 0.6,
         "fall_tau": 0.04, "fall_rate": 450.0},
    ],
    # Her upper arm's twist chain (Body 5 A2; design: A1 solver, 24 Oct). One twist bone a quarter down the arm
    # undoing half the roll left the turn all in two bands (shear 10.8 deg/cm at reaver_show's +105 roll, girth
    # 0.78 mid-arm); five weight nodes down the humerus carry it evenly. All of it only on a side that has `gate`
    # (a body without the chain: the legacy split and drive, unchanged). Per side:
    "twist_chain": {
        "gate": "upperarm_twist_02_{s}",
        # the upper arm's roll (its twist about its own +Y, from rest) read off this bone
        "roll_bone": "upperarm_{s}",
        # a legacy helper's amount in a chained arm: twist_01 carries 0.30 of the roll (the chain 0.30, 0.475,
        # 0.65, 0.825 of it; the elbow all)
        "amounts": {"upperarm_twist_01_{s}": 0.70},
        # the shoulder's share also takes this much of the roll (the deltoid follows the humerus by 30%): its
        # pose rest x slerp(swing, amount) x twist_y(roll x k) x own
        "roll": {"upperarm_share_{s}": 0.30},
        # the roll unwrapped frame to frame (nearest to the last frame's, within +-this many degrees), so a
        # roll through +-180 doesn't flip the chain's counter-twists; one frame on its own reads it as it is
        "unwrap_max": 270.0,
        # weights: the upper arm's (after the shares) spread as hats over these nodes, t along the humerus
        # (0 shoulder, 1 elbow), each a bone (1.0: the upper arm itself)
        "nodes": [["upperarm_twist_01_{s}", 0.0], ["upperarm_twist_02_{s}", 0.25], ["upperarm_twist_03_{s}", 0.5],
                  ["upperarm_twist_04_{s}", 0.75], ["upperarm_{s}", 1.0]],
        # the shoulder share's and the clavicle's weight handed to the chain from t reach[0], all by reach[1]
        # (smoothstep), so the share no longer reaches down the arm; only near the humerus's line: whole within
        # radius[0] of it, none past radius[1] (smoothstep; in upper-arm lengths), so her torso keeps its own
        "reach": [0.10, 0.60],
        "reach_from": ["upperarm_share_{s}", "clavicle_{s}"],
        "radius": [0.30, 0.40],
    },
}


def _smooth(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3 - 2 * t)

# Where along a parent's line a twist bone lies: toward its main child.
MAIN_CHILD = {"upperarm": "lowerarm", "lowerarm": "hand"}


def each(text):
    return [text.replace("{s}", s) for s in "lr"]


def write_spec():
    SPEC_FILE.write_text(json.dumps(SPEC, indent=1) + "\n")


def names():
    return [n for h in SPEC["helpers"] for n in each(h["name"])] + [p["name"] for p in SPEC.get("panels", [])]


def has_helpers(sk: Skeleton):
    return "lowerarm_twist_01_l" in sk.index


def has_chain(index, s):
    """The upper arm's twist chain on side `s` (SPEC "twist_chain"): `index` any name lookup (a dict, a set)."""
    return SPEC["twist_chain"]["gate"].replace("{s}", s) in index


def unwrap_roll(last, deg, lim=None):
    """The roll `deg` (-180..180) as the turn nearest `last` (the last frame's, None: the first), deg or deg +-360
    within +-lim (SPEC twist_chain unwrap_max), so a roll through +-180 carries on instead of flipping."""
    if last is None:
        return deg
    lim = SPEC["twist_chain"]["unwrap_max"] if lim is None else lim
    best = deg
    for c in (deg - 360.0, deg + 360.0):
        if abs(c) <= lim and abs(c - last) < abs(best - last):
            best = c
    return best


# --------------------------------------------------------------- geometry --
def _twist_y(d):
    """d split as swing * twist, the twist about the bone's own +Y:
    (swing, twist, twist angle in degrees)."""
    t = np.array([0.0, d[1], 0.0, d[3]])
    n = np.linalg.norm(t)
    t = t / n if n > 1e-9 else np.array([0, 0, 0, 1.0])
    if t[3] < 0:
        t = -t
    ang = math.degrees(2 * math.atan2(t[1], t[3]))
    return qmul(d, qinv(t)), t, ang


def hinge_turn(child_global_rot, joint_from, joint_at, way, front=(0, 0, 1.0)):
    """Degrees about the bone below a joint, along its own line, that bring
    its X onto the axis the joint bends about (as keyed.Rig keeps it: across
    the bone above and her front for an elbow, her back for a knee), read
    from a right-angle bend. `front` is her front in the space given (+Z in
    the game's; -Y in Blender's)."""
    u = np.asarray(joint_at, float) - np.asarray(joint_from, float)
    u = u / np.linalg.norm(u)
    w = np.asarray(front, float) * (1.0 if way == "front" else -1.0)
    h = np.cross(u, w)
    h = h / np.linalg.norm(h)
    g = np.asarray(child_global_rot, float)
    d = qmul(qinv(g), qmul(qaxis(h, 90), g))
    sw, _, _ = _twist_y(d)
    a = sw[:3] / max(np.linalg.norm(sw[:3]), 1e-9)
    return math.degrees(math.atan2(-a[2], a[0]))


# ------------------------------------------------------------- skeleton --
def extend(sk: Skeleton, chain=False) -> Skeleton:
    """The skeleton with her helper bones added after its own (if missing),
    rests as heroine_rig.py builds them. The upper arm's twist chain
    (SPEC "twist_chain") only with `chain` (hers, explicitly)."""
    names_, parent = list(sk.names), list(sk.parent)
    rot, pos = list(sk.rest_rot), list(sk.rest_pos)
    I = dict(sk.index)
    grot, gpos = sk.rest_globals()
    for h in SPEC["helpers"]:
        if h.get("chain") and not chain:
            continue
        for s in "lr":
            n = h["name"].replace("{s}", s)
            if n in I:
                continue
            p = I[h["parent"].replace("{s}", s)]
            if h["kind"] in ("share", "point"):
                b = I[h["bone"].replace("{s}", s)]
                above = sk.parent[b]
                turn = hinge_turn(grot[0, b], gpos[0, above], gpos[0, b], h["way"])
                r, t = qmul(sk.rest_rot[b], qaxis([0, 1.0, 0], turn)), sk.rest_pos[b]
            else:
                main = MAIN_CHILD[sk.names[p].split("_")[0]] + "_" + s
                t = sk.rest_pos[I[main]] * h["at"]
                r = np.array([0, 0, 0, 1.0])
            I[n] = len(names_)
            names_.append(n)
            parent.append(p)
            rot.append(np.array(r, float))
            pos.append(np.array(t, float))
    for pn in SPEC.get("panels", []):
        if pn["name"] in I or pn["parent"] not in I:
            continue
        p = I[pn["parent"]]
        gp = grot[0, p]
        # laid along the panel: +Y down, +Z her front (so +X her right)
        r = qmul(qinv(gp), PANEL_REST)
        t = qrot(qinv(gp), np.asarray(pn["pivot"], float))
        I[pn["name"]] = len(names_)
        names_.append(pn["name"])
        parent.append(p)
        rot.append(np.array(r, float))
        pos.append(np.array(t, float))
    out = Skeleton(names=names_, parent=parent, rest_rot=np.array(rot), rest_pos=np.array(pos), path=sk.path)
    out.index = I
    return out


# --------------------------------------------------------------- driving --
def forearm_turn(sk, h, hand_local):
    """The hand's turn about the forearm (degrees), on the forearm's own
    frame: its thumb side's way across the forearm against where it lies at
    rest (neither a bend toward the palm nor to the side changes it)."""
    a = sk.rest_pos[h] / np.linalg.norm(sk.rest_pos[h])
    t0 = qrot(sk.rest_rot[h], [0, 0, 1.0])
    t = qrot(hand_local, [0, 0, 1.0])
    t0 = t0 - a * np.dot(t0, a)
    t = t - a * np.dot(t, a)
    if np.linalg.norm(t0) < 1e-9 or np.linalg.norm(t) < 1e-9:
        return 0.0
    return math.degrees(math.atan2(float(np.dot(np.cross(t0, t), a)), float(np.dot(t0, t))))


def _swing_deg(swing):
    """Degrees a swing (no turn about the bone's own line) turns."""
    return 2 * math.degrees(math.acos(min(1.0, abs(float(swing[3])))))


def bend(sk: Skeleton, rot, bone):
    """Degrees the joint above `bone` is bent in the pose (local rotations):
    the bone's swing from its rest, its turn about its own line left out.
    The shares are driven by it and the correctives keyed on it."""
    j = sk.index[bone]
    swing, _, _ = _twist_y(qmul(qinv(sk.rest_rot[j]), rot[j]))
    return _swing_deg(swing)


def corrective_weight(c, deg):
    """A corrective shape's weight at `deg` degrees of its joint's bend:
    eased in (smoothstep) from c["from"] to c["to"], none below."""
    t = min(max((deg - c["from"]) / (c["to"] - c["from"]), 0.0), 1.0)
    return t * t * (3 - 2 * t)


def corrective_weights(sk: Skeleton, rot):
    """{shape name: weight} for the pose (local rotations, as drive takes them)."""
    out = {}
    for c in SPEC.get("correctives", []):
        for s in "lr":
            b = c["bone"].replace("{s}", s)
            if b in sk.index:
                out[c["name"].replace("{s}", s)] = corrective_weight(c, bend(sk, rot, b))
    return out


def bulge(bend, h):
    """How far the flesh round a joint bent `bend` degrees is pushed out
    across the bend, as a stretch along the share bone's Z. With the skin's
    weights a quadratic Bezier over the joint (split, "smooth"), a point
    halfway round lies at (cos(bend/2) + stretch) / 2 of its rest distance
    from the joint, so a stretch of 2 - cos(bend/2) keeps it there: the
    joint bends round as a rounded corner, neither cut across nor pushed to
    a point. `bulge` of that stretch, at most `bulge_max`.

    With a `pivot` (metres along the share's Z: the flexor side, the inside
    of the bend, which is +Z at the elbow and the knee) the stretch is about
    that point, not the bone's line: the crease side is held where it is (a
    stretch there pushed the crease's skin over itself: a fold-over tick
    behind the knee), and the extensor side, twice as far from the pivot,
    takes the whole push from half the bulge."""
    k = 2.0 - math.cos(math.radians(min(bend, 180.0) / 2))
    return float(min(1.0 + h.get("bulge", 0.0) * (k - 1.0), h.get("bulge_max", 1.0)))


def point_push(bend, h):
    """How far a point bone is pushed out across the bend (metres, along
    its -Z: away from the crease), eased in from h["from"] to h["to"]
    degrees of bend. Nothing for a share."""
    if h["kind"] != "point":
        return 0.0
    t = min(max((bend - h["from"]) / (h["to"] - h["from"]), 0.0), 1.0)
    return float(h["push"] * t * t * (3 - 2 * t))


def point_squeeze(bend, h):
    """How much of a point bone's width along its X (the hinge axis) is drawn
    in toward h["squeeze_x"], eased in from h["squeeze_from"] to h["to"]
    degrees of bend. Nothing for a share."""
    if h["kind"] != "point" or not h.get("squeeze"):
        return 0.0
    t = min(max((bend - h["squeeze_from"]) / (h["to"] - h["squeeze_from"]), 0.0), 1.0)
    return float(h["squeeze"] * t * t * (3 - 2 * t))


# A panel's rest in her rest axes: half a turn about +Z (+Y down, +X her right).
PANEL_REST = np.array([0.0, 0.0, 1.0, 0.0])


def _smax(a, b, k):
    """Polynomial smooth max, `k` wide (max + k/4 where a == b)."""
    h = max(k - abs(a - b), 0.0) / k
    return max(a, b) + h * h * k / 4


def _softrelu(x, k):
    """0 below 0, x - k/2 above k, a quadratic between (smooth, never < 0)."""
    return 0.0 if x <= 0 else (x * x / (2 * k) if x < k else x - k / 2)


def panel_turn(pn, fl, fr, al, ar):
    """Degrees a panel turns forward (SPEC "panels"): from each thigh's
    forward swing (fl, fr) and spread (al, ar), degrees from rest."""
    k = pn["soft"]
    lead = _smax(fl, fr, k) - k / 4
    spread = (al + ar) / 2
    damp = 1.0 - pn["spread_damp"] * float(_smooth((spread - pn["spread_from"]) / (pn["spread_to"] - pn["spread_from"])))
    return pn["amount"] * _softrelu(lead, k) * damp


def panel_fall(pn, prev, target, dt):
    """The panel's turn this frame (degrees) from last frame's (`prev`, None
    at the first) and the law's (`target`), `dt` seconds on: up at once,
    down as a first-order lag (`fall_tau`), at most `fall_rate` deg/s, never
    below the law. PanelSwing.Fall's twin."""
    if prev is None or target >= prev:
        return target
    if dt <= 0:
        return prev
    y = target + (prev - target) * math.exp(-dt / pn["fall_tau"])
    return max(target, y, prev - pn["fall_rate"] * dt)


def _swing_spread(v, v0, side):
    """A thigh's line v (its +Y, in her rest axes carried with the pelvis)
    against its rest v0: (forward swing in her side plane, spread out to
    `side` (+1 her left, -1 her right)), degrees."""
    fwd = lambda u: math.degrees(math.atan2(u[2], -u[1]))
    out = lambda u: math.degrees(math.asin(min(1.0, max(-1.0, u[0] * side))))
    return fwd(v) - fwd(v0), out(v) - out(v0)


def _below(sk: Skeleton, rot, top, bone):
    """`bone`'s rotation in `top`'s frame (local rotations down the chain)."""
    q = np.array([0, 0, 0, 1.0])
    j = bone
    while j != top and j >= 0:
        q = qmul(rot[j], q)
        j = sk.parent[j]
    return q


def panel_angles(sk: Skeleton, rot, pn):
    """(fl, fr, al, ar): each thigh's forward swing and spread in the
    pelvis's frame, degrees from rest (local rotations as drive takes them)."""
    I = sk.index
    p = I[pn["parent"]]
    gp = sk.rest_globals()[0][0, p]
    res = []
    for name, side in zip(pn["thighs"], (1, -1)):
        t = I[name]
        v = qrot(gp, qrot(_below(sk, rot, p, t), [0, 1.0, 0]))
        v0 = qrot(gp, qrot(_below(sk, sk.rest_rot, p, t), [0, 1.0, 0]))
        res.append(_swing_spread(v, v0, side))
    (fl, al), (fr, ar) = res
    return fl, fr, al, ar


def drive_panels(sk: Skeleton, rot, state=None, dt=None):
    """The panel bones turned (local rotations, changed in place). With
    `state` (a dict kept from frame to frame, {} at the first) and `dt`
    (seconds since the last frame), each falls as panel_fall has it, as the
    game does; without, the law alone (one frame on its own)."""
    I = sk.index
    for pn in SPEC.get("panels", []):
        j = I.get(pn["name"])
        if j is None:
            continue
        p = I[pn["parent"]]
        deg = panel_turn(pn, *panel_angles(sk, rot, pn))
        if state is not None:
            deg = state[pn["name"]] = panel_fall(pn, state.get(pn["name"]), deg, dt if dt is not None else 0.0)
        # about her lateral axis (+X her right), in the pelvis's frame: the
        # panel's bottom forward and up
        gp = sk.rest_globals()[0][0, p]
        ax = qrot(qinv(gp), [-1.0, 0, 0])
        rot[j] = qnorm(qmul(qaxis(ax, deg), sk.rest_rot[j]))
    return rot


# ------------------------------------------------------------ clavicle lift --
# Her shoulder girdle as an arm rises (armor 17 C2; body5 lift, 24 Oct): a real clavicle and scapula carry the raise
# with the arm (scapulohumeral rhythm, about 2:1 glenohumeral to scapular), and many clips leave her clavicle where it
# rests, so the raised shoulder sat low and the arm plugged into a flat shelf at a V (judge 12: "a doll's ball joint").
# Per side: A = the upper arm's angle from her torso's down axis (pelvis to neck_01; 90 level, 180 overhead); the
# clavicle's wanted rise above its rest is SHRUG_MAX x smoothstep((A - SHRUG_FROM) / (SHRUG_TO - SHRUG_FROM)): nothing
# at and below SHRUG_FROM (60: her idles, the Look and the town untouched), eased in (no kink), 5 at level, 15 at 115,
# 25 at 140, easing out to SHRUG_MAX at SHRUG_TO (180). The clip's own rise counts (the larger wins, never a sum); the
# outer end rolls forward SHRUG_ROLL of the added rise. The hand stays where the clip puts it (two-bone re-aim of the
# upper and lower arm, the elbow kept in the clip's bend plane; its world turn kept); where the lifted shoulder can't
# reach the hand the lift is cut back until it can. The game's twin: Play/ClavicleLift.cs, run by HerShrug before
# HerRaise. SHRUG_OFF=1 (env) turns it off (the game: --shrug-off).
SHRUG_MAX, SHRUG_FROM, SHRUG_TO, SHRUG_ROLL, SHRUG_REACH = 34.0, 60.0, 180.0, 0.25, 0.999


def shrug_target(A):
    """The clavicle's wanted rise (degrees above rest) for an upper arm at A degrees."""
    x = (A - SHRUG_FROM) / (SHRUG_TO - SHRUG_FROM)
    if x <= 0:
        return 0.0
    x = min(x, 1.0)
    return SHRUG_MAX * x * x * (3 - 2 * x)


def _torso(grot, gpos, I):
    down = gpos[I["pelvis"]] - gpos[I["neck_01"]]
    down = down / np.linalg.norm(down)
    left = qrot(grot[I["spine_03"]], [1.0, 0, 0])
    left = left - (left @ down) * down
    left = left / np.linalg.norm(left)
    return down, left, np.cross(down, left)


def _elev(v, down):
    return math.degrees(math.asin(float(np.clip(-(v @ down) / np.linalg.norm(v), -1, 1))))


def shrug(sk: Skeleton, rot, report=None):
    """Her clavicle lift (the block above) on local rotations rot [J, 4], changed in place. `report` (a dict), if
    given, gets per side (A, rise before, added lift, hand move m, elbow move m)."""
    import os
    I = sk.index
    if os.environ.get("SHRUG_OFF") or "clavicle_l" not in I or "pelvis" not in I:
        return rot
    rest = getattr(sk, "_shrug_rest", None)
    if rest is None:
        g0, p0 = sk.fk(sk.rest_rot[None])
        d0 = _torso(g0[0], p0[0], I)[0]
        rest = {s: _elev(p0[0][I["upperarm_" + s]] - p0[0][I["clavicle_" + s]], d0) for s in "lr"}
        sk._shrug_rest = rest
    grot, gpos = sk.fk(rot[None])
    grot, gpos = grot[0], gpos[0]
    down, left, fwd = _torso(grot, gpos, I)
    for s in "lr":
        c, u, lo, h = (I[n + "_" + s] for n in ("clavicle", "upperarm", "lowerarm", "hand"))
        lat = left if s == "l" else -left
        Pc, S, E, H = gpos[c], gpos[u], gpos[lo], gpos[h]
        A = math.degrees(math.acos(float(np.clip((E - S) / np.linalg.norm(E - S) @ down, -1, 1))))
        rise = _elev(S - Pc, down) - rest[s]
        t = shrug_target(A)
        d = min(t, max(0.0, t - rise))   # (none at and below SHRUG_FROM, even with the clip's clavicle dropped)
        if d < 1e-4:
            if report is not None:
                report[s] = (A, rise, 0.0, 0.0, 0.0)
            continue
        up_ax, roll_ax = np.cross(down, lat), np.cross(lat, fwd)   # outer end up; outer end forward
        L1, L2 = np.linalg.norm(E - S), np.linalg.norm(H - E)

        def lifted(k):
            q = qmul(qaxis(roll_ax, SHRUG_ROLL * k), qaxis(up_ax, k))
            return q, Pc + qrot(q, S - Pc)
        q, S2 = lifted(d)
        if np.linalg.norm(H - S2) > SHRUG_REACH * (L1 + L2):        # cut back until the hand is in reach
            lo_k, hi_k = 0.0, d
            for _ in range(20):
                m = 0.5 * (lo_k + hi_k)
                if np.linalg.norm(H - lifted(m)[1]) > SHRUG_REACH * (L1 + L2):
                    hi_k = m
                else:
                    lo_k = m
            d = lo_k
            q, S2 = lifted(d)
        Dv = H - S2
        D = np.linalg.norm(Dv)
        ax = Dv / D
        pole = (E - S) - ((E - S) @ ax) * ax                      # the clip's bend plane
        if np.linalg.norm(pole) < 1e-6:
            pole = qrot(q, E - S) - (qrot(q, E - S) @ ax) * ax
        pole = pole / max(np.linalg.norm(pole), 1e-12)
        ca = float(np.clip((L1 * L1 + D * D - L2 * L2) / (2 * L1 * D), -1, 1))
        E2 = S2 + L1 * (ca * ax + math.sqrt(1 - ca * ca) * pole)
        Cg = qmul(q, grot[c])
        Ug = qnorm(qmul(qbetween(E - S, E2 - S2), grot[u]))
        Lg = qnorm(qmul(qbetween(H - E, H - E2), grot[lo]))
        rot[c] = qnorm(qmul(qinv(grot[sk.parent[c]]), Cg))
        rot[u] = qnorm(qmul(qinv(Cg), Ug))
        rot[lo] = qnorm(qmul(qinv(Ug), Lg))
        rot[h] = qnorm(qmul(qinv(Lg), grot[h]))
        if report is not None:
            g2, p2 = sk.fk(rot[None])
            report[s] = (A, rise, d, float(np.linalg.norm(p2[0][h] - H)), float(np.linalg.norm(p2[0][lo] - E)))
    return rot


def drive(sk: Skeleton, rot, scale=None, shift=None, state=None, dt=None):
    """Her helpers posed from the pose (local rotations [J, 4], changed in
    place): the forearm's roll handed to the hand, the twists shared out, the
    shares half bent and swollen across the bend (`scale` [J, 3], if given,
    takes their stretch, and `shift` [J, 3] the move in the bone's own frame
    that holds its pivot still). As HerJoints.cs does it, after every other layer;
    her clavicle lift first (shrug, as HerShrug does before HerRaise).
    `state` and `dt`: the panels' fall from frame to frame (drive_panels)."""
    I = sk.index
    ident = np.array([0, 0, 0, 1.0])
    shrug(sk, rot)   # her clavicle lift first (HerShrug runs before every other layer of hers)
    for s in "lr":
        la, h = I.get(f"lowerarm_{s}"), I.get(f"hand_{s}")
        if f"lowerarm_twist_01_{s}" not in I:
            continue
        # The forearm bone kept on its hinge: its roll goes to the hand.
        d = qmul(qinv(sk.rest_rot[la]), rot[la])
        sw, tw, _ = _twist_y(d)
        rot[la] = qnorm(qmul(sk.rest_rot[la], sw))
        rot[h] = qnorm(qmul(tw, rot[h]))
        turn = forearm_turn(sk, h, rot[h])
        # The upper arm's twist chain (SPEC "twist_chain"): its roll read once, unwrapped from the last frame's.
        tc = SPEC["twist_chain"]
        chain = has_chain(I, s)
        if chain:
            ub = I[tc["roll_bone"].replace("{s}", s)]
            _, _, roll = _twist_y(qmul(qinv(sk.rest_rot[ub]), rot[ub]))
            if state is not None:
                key = "roll:" + sk.names[ub]
                roll = state[key] = unwrap_roll(state.get(key), roll)
            amounts = {k.replace("{s}", s): v for k, v in tc["amounts"].items()}
            rolls = {k.replace("{s}", s): v for k, v in tc["roll"].items()}
        for hh in SPEC["helpers"]:
            j = I.get(hh["name"].replace("{s}", s))
            if j is None:
                continue
            if hh["kind"] == "forearm_twist":
                rot[j] = qaxis([0, 1.0, 0], turn * hh["amount"])
            elif hh["kind"] == "counter_twist":
                b = I[hh["bone"].replace("{s}", s)]
                if chain and b == ub:
                    rot[j] = qaxis([0, 1.0, 0], -roll * amounts.get(sk.names[j], hh["amount"]))
                    continue
                _, _, ang = _twist_y(qmul(qinv(sk.rest_rot[b]), rot[b]))
                rot[j] = qaxis([0, 1.0, 0], -ang * hh["amount"])
            elif hh["kind"] in ("share", "point"):
                b = I[hh["bone"].replace("{s}", s)]
                swing, _, _ = _twist_y(qmul(qinv(sk.rest_rot[b]), rot[b]))
                own = qmul(qinv(sk.rest_rot[b]), sk.rest_rot[j])        # its turn about the line
                if chain and sk.names[j] in rolls:
                    # (and its share of the upper arm's roll, about its own line)
                    own = qmul(qaxis([0, 1.0, 0], roll * rolls[sk.names[j]]), own)
                rot[j] = qnorm(qmul(sk.rest_rot[b], qmul(qslerp(ident, swing, hh["amount"]), own)))
                if scale is not None:
                    deg = _swing_deg(swing)
                    hs = hh if hh["kind"] == "share" else next(x for x in SPEC["helpers"] if x["name"] == hh["share"])
                    k = bulge(deg, hs)
                    q = point_squeeze(deg, hh)
                    scale[j] = (1.0 - q, 1.0, k)
                    if shift is not None:
                        shift[j] = (q * hh.get("squeeze_x", 0.0), 0.0, (1.0 - k) * hs.get("pivot", 0.0) - point_push(deg, hh))
    drive_panels(sk, rot, state, dt)
    return rot


# --------------------------------------------------------------- weights --
def split(W, P, index, heads, front=None):
    """Weights [V, J] (columns by `index`, name to column, the helpers'
    included) shared onto the helpers by where each point lies (P [V, 3]),
    with `heads` each bone's head at rest (name to point), then cut back to
    `cap` bones a point (each weight less the point's (cap+1)-th, so
    neighbours cut alike) and made whole. The space is any: only lengths
    along her bones are read, and with `front` (her front in that space:
    +Z in the game's, -Y in Blender's) which side of a joint is its crease."""
    W = np.array(W, float)
    I = index
    cfg = SPEC["weights"]
    for s in "lr":
        if f"lowerarm_twist_01_{s}" not in I:
            continue
        # The shares first: the blend between the bones above and below
        # each joint, carried by its share bone.
        for top, low, share in cfg["pairs"]:
            a, b, c = I.get(top.replace("{s}", s)), I.get(low.replace("{s}", s)), I.get(share.replace("{s}", s))
            if a is None or b is None or c is None:
                continue
            if cfg.get("profile") == "smooth":
                # As a quadratic Bezier's weights over the point's blend x
                # toward the bone below: (1-x)^2, 2x(1-x), x^2. Each point
                # turns on average as it did (x of the bend), and the skin
                # round the joint is a smooth curve through the share's ring.
                # (Weights cut as a tent, the most a share can take, leave
                # it two straight runs meeting in a ridge: at a deep bend the
                # knee came to a point.)
                tot = W[:, a] + W[:, b]
                x = np.where(tot > 1e-9, W[:, b] / np.maximum(tot, 1e-9), 0.0)
                k = cfg["share"]
                hs = next(h for h in SPEC["helpers"] if h["name"] == share)
                mid = tot * x * (1 - x)
                cr = cfg.get("crease")
                if cr and front is not None and "pivot" in hs:
                    # How far into the crease a point lies: along her front
                    # (elbow) or back (knee), square to the bone above.
                    j = np.asarray(heads[low.replace("{s}", s)], float)
                    ax = j - np.asarray(heads[top.replace("{s}", s)], float)
                    ax = ax / np.linalg.norm(ax)
                    w = np.asarray(front, float) * (1.0 if hs["way"] == "front" else -1.0)
                    w = w - ax * (w @ ax)
                    w = w / np.linalg.norm(w)
                    depth = np.clip(((P - j) @ w) / cr["reach"], 0.0, 1.0)
                    k = k * (1.0 - cr["cut"] * depth * depth * (3 - 2 * depth))
                W[:, c] += 2 * k * mid
                W[:, a] = tot * (1 - x) ** 2 + (1 - k) * mid
                W[:, b] = tot * x ** 2 + (1 - k) * mid
                for pn, po in (cfg.get("point") or {}).items():
                    hp_ = next(h for h in SPEC["helpers"] if h["name"] == pn)
                    d = I.get(pn.replace("{s}", s))
                    if hp_["share"] != share or d is None or front is None:
                        continue
                    # The patch round the joint's far side from the crease.
                    j = np.asarray(heads[low.replace("{s}", s)], float)
                    ax = j - np.asarray(heads[top.replace("{s}", s)], float)
                    ax = ax / np.linalg.norm(ax)
                    w = np.asarray(front, float) * (1.0 if hs["way"] == "front" else -1.0)
                    w = w - ax * (w @ ax)
                    w = w / np.linalg.norm(w)
                    rel = P - j
                    along = rel @ ax
                    perp = rel - along[:, None] * ax
                    cosang = (perp @ -w) / np.maximum(np.linalg.norm(perp, axis=1), 1e-9)
                    c0, c1 = math.cos(math.radians(po["half"] + po["fade"])), math.cos(math.radians(po["half"]))
                    f = _smooth((cosang - c0) / (c1 - c0))
                    f = f * _smooth((po["reach"] + po["feather"] - np.abs(along - po["at"])) / po["feather"])
                    W[:, d] += W[:, c] * f
                    W[:, c] *= 1 - f
            else:
                m = np.minimum(W[:, a], W[:, b]) * 2 * cfg["share"]
                W[:, c] += m
                W[:, a] -= m / 2
                W[:, b] -= m / 2
        # The shoulder's twist bone.
        ua, el = I[f"upperarm_{s}"], I[f"lowerarm_{s}"]
        sh, ax = np.asarray(heads[f"upperarm_{s}"], float), np.asarray(heads[f"lowerarm_{s}"], float) - np.asarray(heads[f"upperarm_{s}"], float)
        u = ((P - sh) @ ax) / (ax @ ax)
        if has_chain(I, s):
            _chain_split(W, P, I, s, sh, ax, u)
        else:
            frac = np.clip(1 - u / cfg["shoulder_twist_to"], 0, 1)
            frac = frac * frac * (3 - 2 * frac)
            tw = I[f"upperarm_twist_01_{s}"]
            W[:, tw] += W[:, ua] * frac
            W[:, ua] *= 1 - frac
        # The forearm's twist bones: hats over the nodes along it.
        la = I[f"lowerarm_{s}"]
        el_p = np.asarray(heads[f"lowerarm_{s}"], float)
        ax = np.asarray(heads[f"hand_{s}"], float) - el_p
        t = ((P - el_p) @ ax) / (ax @ ax)
        nodes = cfg["forearm_nodes"]
        bones = [la, I[f"lowerarm_twist_01_{s}"], I[f"lowerarm_twist_02_{s}"]]
        w = W[:, la].copy()
        W[:, la] = 0
        x = np.clip(t, nodes[0], nodes[-1])
        for k, (n0, b0) in enumerate(zip(nodes, bones)):
            hat = np.ones_like(x)
            if k > 0:
                hat = np.where(x < n0, (x - nodes[k - 1]) / (n0 - nodes[k - 1]), hat)
            if k + 1 < len(nodes):
                hat = np.where(x > n0, (nodes[k + 1] - x) / (nodes[k + 1] - n0), hat)
            W[:, b0] += w * np.clip(hat, 0, 1)
    W = np.maximum(W, 0)
    cap = cfg["cap"]
    if cap and W.shape[1] > cap:
        nth = -np.partition(-W, cap, axis=1)[:, cap]
        W = np.maximum(W - nth[:, None], 0)
    return W / np.maximum(W.sum(1, keepdims=True), 1e-12)


def _chain_split(W, P, I, s, sh, ax, u):
    """The upper arm's twist chain's weights (SPEC "twist_chain"), W changed in place: the upper arm's weight (with
    whatever its chain already had) spread as hats over the nodes by u (along the humerus, 0 shoulder, 1 elbow), the
    shoulder share's and clavicle's handed to the chain as they reach down the arm, near its line only."""
    tc = SPEC["twist_chain"]
    nodes = [(I[n.replace("{s}", s)], t) for n, t in tc["nodes"]]
    w = np.zeros(len(W))
    for j, _ in nodes:
        w += W[:, j]
        W[:, j] = 0
    r = np.linalg.norm((P - sh) - u[:, None] * ax, axis=1) / math.sqrt(ax @ ax)
    r0, r1 = tc["reach"]
    q0, q1 = tc["radius"]
    f = _smooth((u - r0) / (r1 - r0)) * (1 - _smooth((r - q0) / (q1 - q0)))
    for n in tc["reach_from"]:
        j = I.get(n.replace("{s}", s))
        if j is None:
            continue
        w += W[:, j] * f
        W[:, j] *= 1 - f
    ts = [t for _, t in nodes]
    x = np.clip(u, ts[0], ts[-1])
    for k, (j, t) in enumerate(nodes):
        hat = np.ones_like(x)
        if k > 0:
            hat = np.where(x < t, (x - ts[k - 1]) / (t - ts[k - 1]), hat)
        if k + 1 < len(nodes):
            hat = np.where(x > t, (ts[k + 1] - x) / (ts[k + 1] - t), hat)
        W[:, j] += w * np.clip(hat, 0, 1)


# ----------------------------------------------------------- correctives --
def mats(grot, gpos, scale=None, shift=None):
    """Bone globals [J, 4, 4] from global rotations and positions, a
    helper's stretch (`scale` [J, 3]) and move (`shift` [J, 3]) in its own
    frame, as the game and skin.Body build them."""
    M = np.tile(np.eye(4), (len(grot), 1, 1))
    for j in range(len(grot)):
        R = qmatrix(grot[j])
        M[j, :3, :3] = R if scale is None else R @ np.diag(scale[j])
        M[j, :3, 3] = gpos[j] if shift is None else gpos[j] + R @ shift[j]
    return M


def bent(sk: Skeleton, bone, deg, front=(0, 0, 1.0), way="front"):
    """Her rest pose with the joint above `bone` bent `deg` degrees as bend
    reads it, about its hinge (across the bone above and her front, or her
    back for a knee: `way`), as the review's test poses bend it."""
    j = sk.index[bone]
    p = sk.parent[j]
    grot, gpos = sk.rest_globals()
    u = gpos[0, j] - gpos[0, p]
    u = u / np.linalg.norm(u)
    h = np.cross(u, np.asarray(front, float) * (1.0 if way == "front" else -1.0))
    h = h / np.linalg.norm(h)

    def at(a):
        rot = sk.rest_rot.copy()
        rot[j] = qmul(qinv(grot[0, p]), qmul(qaxis(h, a), grot[0, j]))
        return rot
    a = float(deg)
    for _ in range(4):          # (a hinge a little off the bone's own frame reads a little less)
        a += deg - bend(sk, at(a), bone)
    return at(a)


def corrective(P, W, sk: Skeleton, front=(0, 0, 1.0)):
    """Her corrective shapes as moves of her points at rest: {name: [V, 3]}.
    P [V, 3] her rest points, W [V, J] their weights (the helpers' split in,
    columns by sk's bones), both in sk's space; `front` her front there (+Z
    in the game's, -Y in Blender's). Each shape is made where it is whole:
    the joint bent c["full"] degrees and her helpers driven as the game
    drives them; the move wanted there, posed, is carried back to rest
    through the inverse of each point's blended skin matrix, so skinned at
    that bend the shape is exactly that move, and at other bends it turns
    with the limb."""
    P = np.asarray(P, float)
    W = np.asarray(W, float)
    front = np.asarray(front, float)
    grot0, gpos0 = sk.rest_globals()
    rest_inv = np.linalg.inv(mats(grot0[0], gpos0[0]))
    out = {}
    for c in SPEC.get("correctives", []):
        for s in "lr":
            name, bone = c["name"].replace("{s}", s), c["bone"].replace("{s}", s)
            if bone not in sk.index:
                continue
            j = sk.index[bone]
            p = sk.parent[j]
            kid = sk.index[MAIN_CHILD[bone.split("_")[0]] + "_" + s]
            rot = bent(sk, bone, c["full"], front, c.get("way", "front"))
            scale, shift = np.ones((len(sk.names), 3)), np.zeros((len(sk.names), 3))
            rot = drive(sk, rot, scale, shift)
            grot, gpos = sk.fk(rot[None])
            S = mats(grot[0], gpos[0], scale, shift) @ rest_inv
            # This limb's points round the joint (the bones each side of it,
            # their helpers, the one below): only they move.
            heads = (sk.names[p].split("_")[0], bone.split("_")[0], sk.names[kid].split("_")[0])
            cols = [k for k, n in enumerate(sk.names) if n.endswith("_" + s) and n.split("_")[0] in heads]
            limb = W[:, cols].sum(1)
            cand = np.nonzero((limb > 0.02) & (np.linalg.norm(P - gpos0[0, j], axis=1) < 0.15))[0]
            A = np.einsum("vk,kab->vab", W[cand], S)
            q = np.einsum("vab,vb->va", A[:, :3, :3], P[cand]) + A[:, :3, 3]
            cj = gpos[0, j]
            u = cj - gpos[0, p]
            u = u / np.linalg.norm(u)
            f = gpos[0, kid] - cj
            f = f / np.linalg.norm(f)
            lean = c.get("lean", 0.0)
            n = (1 - lean) * u - (1 + lean) * f
            n = n / np.linalg.norm(n)
            h = np.cross(u, f)
            h = h / np.linalg.norm(h)
            t = np.cross(n, h)
            rel = q - cj
            along = rel @ n
            off = np.linalg.norm(rel - along[:, None] * n, axis=1)
            ray = off < c["near"]
            tip = cj + n * (along[ray].max() if ray.any() else along.max())
            d = q - tip
            rh, rt, rn = c["radius"]
            r2 = (d @ h / rh) ** 2 + (d @ t / rt) ** 2 + (d @ n / rn) ** 2
            fall = np.clip(1.0 - r2, 0.0, 1.0) ** 3 * np.clip(limb[cand], 0.0, 1.0)
            mv = fall > 0
            delta = np.zeros_like(P)
            want = c["amount"] * fall[mv, None] * n[None, :]
            delta[cand[mv]] = np.linalg.solve(A[mv, :3, :3], want[..., None])[..., 0]
            out[name] = delta
    return out


def corrective_names():
    return [n for c in SPEC.get("correctives", []) for n in each(c["name"])]


if __name__ == "__main__":
    write_spec()
    print("wrote", SPEC_FILE)
