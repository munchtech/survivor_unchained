"""Hands that hold things to a face: a flask to the lips, a cork in the
teeth, a letter before the eyes. The hand is placed by the thing it holds,
and the thing by a point on her face, so the contact lands whatever her
head and back are doing.

Places on her face come from her head's mesh (art/people/heroine.glb,
HeroineHead at rest): the lips meet at (0, 1.685, 0.10) and the nose's tip
is at (0, 1.715, 0.114) in her character space, against the Head joint at
(0, 1.666, -0.036). Each is kept as an offset from the Head joint at rest,
and carried by the head's turn from rest.

What a hand holds hangs on its grip, Arms.Hold's mount: 7.5 cm along the
fingers and 2.5 cm to the palm (the hand's -X on her right, which is its
palm side), the piece's up out of the thumb side (the hand's +Z). A flask
held so has its spout 9 cm up from the grip.
"""
from __future__ import annotations

import numpy as np

from rig import qinv, qmul, qrot

HEAD_AT_REST = np.array([0.0, 1.666, -0.036])
FACE = {
    "mouth": np.array([0.0, 1.685, 0.100]) - HEAD_AT_REST,
    "teeth": np.array([0.0, 1.683, 0.088]) - HEAD_AT_REST,
    "nose": np.array([0.0, 1.715, 0.114]) - HEAD_AT_REST,
    "eyes": np.array([0.0, 1.749, 0.080]) - HEAD_AT_REST,
    "chin": np.array([0.0, 1.648, 0.088]) - HEAD_AT_REST,
}
GRIP = np.array([-0.025, 0.075, 0.0])  # Arms.Hold's mount on her right hand


def head_frame(sk, grot, gpos, fr):
    """Her head's turn from rest and its joint, at frame fr of a solved clip
    (globals from sk.fk)."""
    H = sk.index["Head"]
    rest = sk.rest_globals()[0][0, H]
    return qmul(grot[fr, H], qinv(rest)), gpos[fr, H]


def face_point(sk, grot, gpos, fr, name, off=(0, 0, 0)):
    """A place on her face (FACE), moved by `off` in her head's own frame
    (x her left, y up, z out of her face, as at rest)."""
    turn, at = head_frame(sk, grot, gpos, fr)
    return at + qrot(turn, FACE[name] + np.asarray(off, float))


def in_head(sk, grot, gpos, fr, v):
    """A direction given in her head's frame, in character space."""
    turn, _ = head_frame(sk, grot, gpos, fr)
    return qrot(turn, np.asarray(v, float))


def hand_basis(blade, knuckles):
    """The hand's axes for a wanted blade (+Z) and knuckles (+Y), made
    orthonormal as Rig.solve makes them (the blade kept)."""
    z = np.asarray(blade, float)
    z = z / np.linalg.norm(z)
    y = np.asarray(knuckles, float)
    y = y - z * np.dot(y, z)
    y = y / np.linalg.norm(y)
    return np.cross(y, z), y, z


def wrist_for(point, local, blade, knuckles):
    """Where the wrist (the hand bone) must be for a point fixed in the hand
    (`local`, in the hand bone's frame) to land on `point`, the hand aimed
    by blade and knuckles."""
    x, y, z = hand_basis(blade, knuckles)
    lo = np.asarray(local, float)
    return np.asarray(point, float) - (x * lo[0] + y * lo[1] + z * lo[2])


def flask_dirs(phi, psi=0.0):
    """A flask's neck and the knuckles round it, in her head's frame, for
    the neck pointing back at her face: phi the neck's angle below the
    head's level (negative: the neck up, as for a cork in the teeth), psi
    its turn coming in from her right (degrees)."""
    p, s = np.radians(phi), np.radians(psi)
    neck = np.array([0.0, -np.sin(p), -np.cos(p)])
    knuck = np.array([0.0, np.cos(p), -np.sin(p)])
    c, sn = np.cos(s), np.sin(s)
    # Turned about the head's up: the neck from her right points to her left.
    turn = lambda v: np.array([v[0] * c - v[2] * sn, v[1], v[0] * sn + v[2] * c])
    return turn(neck), turn(knuck)


def contact_build(name, rig, keys, contacts, base=None, meta=None):
    """A clip whose hands (or feet) are placed by where the body has gone:
    the keys solved once without them, then `contacts(fr, grot, gpos,
    pose)` gives the controls to lay over each frame (a hand flat on the
    ground under the shoulder, a flask at the lips), and the whole solved
    again."""
    from keyed import Track
    track = Track(keys)
    poses = [track(fr) for fr in range(track.frames)]
    first = solved(name, rig, poses, base=base)
    g, p = rig.sk.fk(first.rot, first.pos)
    return solved(name, rig, [{**pose, **contacts(fr, g, p, pose)} for fr, pose in enumerate(poses)], base=base, meta=meta)


def solved(name, rig, poses, base=None, meta=None, fps=30):
    """A clip of one pose a frame, each solved as it is (keyed.build without
    the keys' timing, for poses already worked out frame by frame)."""
    from rig import Clip
    n = len(poses)
    rot = np.empty((n, len(rig.sk), 4))
    pos = np.empty((n, len(rig.sk), 3))
    for fr, pose in enumerate(poses):
        b = None if base is None else (base.rot[min(fr, base.frames - 1)], base.pos[min(fr, base.frames - 1)])
        rot[fr], pos[fr] = rig.solve(pose, base=b)
    m = {"source": "keyed (tools/anim)", "licence": "own work"}
    m.update(meta or {})
    return Clip(name, fps, rot, pos, loop=False, meta=m)


def forearm_on_ground(sk, gpos, fr, side, toward, ground=0.045, upper=0.251, fore=0.216):
    """A forearm laid along the ground pointing `toward` (a direction along
    the ground), the elbow on the ground as near under the shoulder as the
    upper arm lets it come (ahead of it, along `toward`, while the shoulder
    is low; under it once the shoulder is an upper arm's length up): the
    hand's place and the elbow's way, for a body propped on it."""
    s = gpos[fr, sk.index[f"upperarm_{side}"]]
    t = np.array([toward[0], 0.0, toward[2]], float)
    t = t / np.linalg.norm(t)
    drop = max(0.0, s[1] - ground)
    ahead = np.sqrt(max(0.0, upper * upper - drop * drop))
    elbow = np.array([s[0] + t[0] * ahead, ground if drop < upper else s[1] - upper, s[2] + t[2] * ahead])
    hand = elbow + t * fore
    hand[1] = max(hand[1], ground - 0.01)
    return hand, elbow - (s + hand) / 2


def joint_clear(top, end, l1, l2, pole, floor):
    """The way to bend a two-bone limb (hip to ankle, shoulder to wrist) so
    its middle joint (knee, elbow) is as near the wanted bend as it can be
    without going under `floor`: the pole for Rig.solve. The joint lies on
    a circle about the line from top to end; the point nearest the wanted
    side that clears the floor is taken (the highest, if none clears)."""
    top, end, pole = (np.asarray(v, float) for v in (top, end, pole))
    d = end - top
    dist = min(max(np.linalg.norm(d), abs(l1 - l2) + 1e-4), (l1 + l2) * 0.9995)
    u = d / max(np.linalg.norm(d), 1e-9)
    a = (l1 * l1 - l2 * l2 + dist * dist) / (2 * dist)
    r = np.sqrt(max(0.0, l1 * l1 - a * a))
    c = top + u * a
    e1 = pole - u * np.dot(pole, u)
    if np.linalg.norm(e1) < 1e-6:
        e1 = np.cross(u, [0.0, 1.0, 0.0])
    e1 = e1 / np.linalg.norm(e1)
    e2 = np.cross(u, e1)
    best = None
    for k in range(73):
        th = np.radians(k * 5 - 180)
        pt = c + r * (np.cos(th) * e1 + np.sin(th) * e2)
        ok = pt[1] >= floor
        score = (0 if ok else 1, abs(th) if ok else -pt[1])
        if best is None or score < best[0]:
            best = (score, pt)
    # (Rig.solve bends toward the joint's place before solving plus the pole:
    # a long pole makes that place not matter.)
    return tuple(10.0 * (best[1] - (top + end) / 2))


def knee_clear(rig, gpos, fr, side, foot, floor=0.05):
    """A foot's control with its knee's way set so the knee stays on or above
    the ground (joint_clear), from the body as solved without it."""
    sk, I = rig.sk, rig.I
    rest = rig.prest[I[f"foot_{side}"]]
    s = 1 if side == "l" else -1
    p = np.asarray(foot.get("pos", (rest[0], 0, rest[2])), float)
    target = np.array([p[0] + s * rig.feet_out * ("pos" in foot), rest[1] + p[1], p[2]])
    top = gpos[fr, I[f"thigh_{side}"]]
    l1 = np.linalg.norm(rig.prest[I[f"calf_{side}"]] - rig.prest[I[f"thigh_{side}"]])
    l2 = np.linalg.norm(rig.prest[I[f"foot_{side}"]] - rig.prest[I[f"calf_{side}"]])
    pole = foot.get("pole", (s * 0.15, 0, 1.0))
    return dict(foot, pole=joint_clear(top, target, l1, l2, pole, floor))


def slerp_dir(a, b, u):
    """Directions blended along the arc between them."""
    a = np.asarray(a, float) / np.linalg.norm(a)
    b = np.asarray(b, float) / np.linalg.norm(b)
    d = float(np.clip(np.dot(a, b), -1, 1))
    if d > 0.9999:
        v = a + (b - a) * u
    else:
        w = np.arccos(d)
        v = (np.sin((1 - u) * w) * a + np.sin(u * w) * b) / np.sin(w)
    return v / np.linalg.norm(v)
