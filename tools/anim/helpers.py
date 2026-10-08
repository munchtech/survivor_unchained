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
  shoulder girdle;
- **shares** (`upperarm_share`, `lowerarm_share`, `calf_share`): half the
  joint's bend, carrying the ring of flesh round the joint, so it bends
  round a corner instead of folding; at the elbow and knee also pushed out
  across the bend as a bent tube is (`bulge`), so the crease keeps its flesh.

They are children of the bones they help, laid along them, and bound where
those bones' weight was, so a body without the driver moves as before.
"""
from __future__ import annotations

import json
import math

import numpy as np

from rig import REPO, Skeleton, qaxis, qinv, qmul, qnorm, qrot, qslerp

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
         "bulge": 1.0, "bulge_max": 2.0, "way": "front"},
        {"name": "calf_share_{s}", "parent": "thigh_{s}", "kind": "share", "bone": "calf_{s}", "amount": 0.5,
         "bulge": 1.0, "bulge_max": 2.0, "way": "back"},
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
    },
}

# Where along a parent's line a twist bone lies: toward its main child.
MAIN_CHILD = {"upperarm": "lowerarm", "lowerarm": "hand"}


def each(text):
    return [text.replace("{s}", s) for s in "lr"]


def write_spec():
    SPEC_FILE.write_text(json.dumps(SPEC, indent=1) + "\n")


def names():
    return [n for h in SPEC["helpers"] for n in each(h["name"])]


def has_helpers(sk: Skeleton):
    return "lowerarm_twist_01_l" in sk.index


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
def extend(sk: Skeleton) -> Skeleton:
    """The skeleton with her helper bones added after its own (if missing),
    rests as heroine_rig.py builds them."""
    names_, parent = list(sk.names), list(sk.parent)
    rot, pos = list(sk.rest_rot), list(sk.rest_pos)
    I = dict(sk.index)
    grot, gpos = sk.rest_globals()
    for h in SPEC["helpers"]:
        for s in "lr":
            n = h["name"].replace("{s}", s)
            if n in I:
                continue
            p = I[h["parent"].replace("{s}", s)]
            if h["kind"] == "share":
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


def bulge(bend, h):
    """How far the flesh round a joint bent `bend` degrees is pushed out
    across the bend, as a stretch along the share bone's Z. With the skin's
    weights a quadratic Bezier over the joint (split, "smooth"), a point
    halfway round lies at (cos(bend/2) + stretch) / 2 of its rest distance
    from the joint, so a stretch of 2 - cos(bend/2) keeps it there: the
    joint bends round as a rounded corner, neither cut across nor pushed to
    a point. `bulge` of that stretch, at most `bulge_max`."""
    k = 2.0 - math.cos(math.radians(min(bend, 180.0) / 2))
    return float(min(1.0 + h.get("bulge", 0.0) * (k - 1.0), h.get("bulge_max", 1.0)))


def drive(sk: Skeleton, rot, scale=None):
    """Her helpers posed from the pose (local rotations [J, 4], changed in
    place): the forearm's roll handed to the hand, the twists shared out, the
    shares half bent and swollen across the bend (`scale` [J, 3], if given,
    takes their stretch). As HerJoints.cs does it, after every other layer."""
    I = sk.index
    ident = np.array([0, 0, 0, 1.0])
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
        for hh in SPEC["helpers"]:
            j = I.get(hh["name"].replace("{s}", s))
            if j is None:
                continue
            if hh["kind"] == "forearm_twist":
                rot[j] = qaxis([0, 1.0, 0], turn * hh["amount"])
            elif hh["kind"] == "counter_twist":
                b = I[hh["bone"].replace("{s}", s)]
                _, _, ang = _twist_y(qmul(qinv(sk.rest_rot[b]), rot[b]))
                rot[j] = qaxis([0, 1.0, 0], -ang * hh["amount"])
            elif hh["kind"] == "share":
                b = I[hh["bone"].replace("{s}", s)]
                swing, _, _ = _twist_y(qmul(qinv(sk.rest_rot[b]), rot[b]))
                own = qmul(qinv(sk.rest_rot[b]), sk.rest_rot[j])        # its turn about the line
                rot[j] = qnorm(qmul(sk.rest_rot[b], qmul(qslerp(ident, swing, hh["amount"]), own)))
                if scale is not None:
                    bend = 2 * math.degrees(math.acos(min(1.0, abs(float(swing[3])))))
                    scale[j] = (1.0, 1.0, bulge(bend, hh))
    return rot


# --------------------------------------------------------------- weights --
def split(W, P, index, heads):
    """Weights [V, J] (columns by `index`, name to column, the helpers'
    included) shared onto the helpers by where each point lies (P [V, 3]),
    with `heads` each bone's head at rest (name to point), then cut back to
    `cap` bones a point (each weight less the point's (cap+1)-th, so
    neighbours cut alike) and made whole. The space is any: only lengths
    along her bones are read."""
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
                mid = tot * x * (1 - x)
                k = cfg["share"]
                W[:, c] += 2 * k * mid
                W[:, a] = tot * (1 - x) ** 2 + (1 - k) * mid
                W[:, b] = tot * x ** 2 + (1 - k) * mid
            else:
                m = np.minimum(W[:, a], W[:, b]) * 2 * cfg["share"]
                W[:, c] += m
                W[:, a] -= m / 2
                W[:, b] -= m / 2
        # The shoulder's twist bone.
        ua, el = I[f"upperarm_{s}"], I[f"lowerarm_{s}"]
        sh, ax = np.asarray(heads[f"upperarm_{s}"], float), np.asarray(heads[f"lowerarm_{s}"], float) - np.asarray(heads[f"upperarm_{s}"], float)
        u = ((P - sh) @ ax) / (ax @ ax)
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


if __name__ == "__main__":
    write_spec()
    print("wrote", SPEC_FILE)
