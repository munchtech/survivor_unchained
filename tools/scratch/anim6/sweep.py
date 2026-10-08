"""Her joints' volume under set bends and turns, before the helpers, the Python
prototype of them, and the body built with them.

    python -u sweep.py before proto built
"""
import math
import sys
from pathlib import Path

WT = Path(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ae2a9884e3e51609c")
S = Path(r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\0b33992d-1e38-4eb8-80a1-d5c23b1a44e6\scratchpad\an")
sys.path.insert(0, str(WT / "tools" / "anim"))

import numpy as np  # noqa: E402
from rig import Skeleton, qaxis, qinv, qmul  # noqa: E402
from skin import Body, Clip  # noqa: E402
import motion  # noqa: E402

FRONT = np.array([0, 0, 1.0])


def body(which):
    if which in ("before", "proto"):
        sk = Skeleton.load(S / "before" / "data" / "heroine_skeleton.json")
        f = S / "before" / "people" / "heroine.glb"
    else:
        sk = Skeleton.load(WT / "tools" / "anim" / "data" / "heroine_skeleton.json")
        f = WT / "godot" / "art" / "people" / "heroine.glb"
    return Body(sk, [(f, lambda n: n == "Heroine", "skin")], None, helpers=which != "before")


def turned(sk, rot, j, axis_world, deg):
    """rot with bone j turned deg about a world axis through its head (its
    parents as posed in rot)."""
    grot, _ = sk.fk(rot[None])
    p = sk.parent[j]
    gp = grot[0, p]
    gj = qmul(gp, rot[j])
    new = qmul(qaxis(axis_world, deg), gj)
    rot[j] = qmul(qinv(gp), new)
    return rot


def pose(b, edits):
    sk = b.sk
    rot = sk.rest_rot.copy()
    for fn in edits:
        rot = fn(sk, rot)
    c = Clip("sweep", 30.0, rot[None], sk.rest_pos[None].copy(), False)
    return b.globals(c, 0)


def bone_dir(sk, rot, a, c):
    _, gpos = sk.fk(rot[None])
    d = gpos[0, sk.index[c]] - gpos[0, sk.index[a]]
    return d / np.linalg.norm(d)


def elbow(s, deg):
    def f(sk, rot):
        u = bone_dir(sk, rot, f"upperarm_{s}", f"lowerarm_{s}")
        h = np.cross(u, FRONT)
        return turned(sk, rot, sk.index[f"lowerarm_{s}"], h, deg)
    return f


def knee(s, deg):
    def f(sk, rot):
        u = bone_dir(sk, rot, f"thigh_{s}", f"calf_{s}")
        h = np.cross(u, -FRONT)
        return turned(sk, rot, sk.index[f"calf_{s}"], h, deg)
    return f


def wrist_turn(s, deg, share=0.0):
    """The hand turned about the forearm; `share` of it put into the forearm
    bone's own roll (as keyed.Rig.solve does), the rest into the hand."""
    def f(sk, rot):
        a = bone_dir(sk, rot, f"lowerarm_{s}", f"hand_{s}")
        rot = turned(sk, rot, sk.index[f"lowerarm_{s}"], a, deg * share)
        return turned(sk, rot, sk.index[f"hand_{s}"], a, deg * (1 - share))
    return f


def arm_twist(s, deg):
    def f(sk, rot):
        a = bone_dir(sk, rot, f"upperarm_{s}", f"lowerarm_{s}")
        return turned(sk, rot, sk.index[f"upperarm_{s}"], a, deg)
    return f


def arm_raise(s, deg):
    """The upper arm lifted out to her side (abducted) by deg."""
    def f(sk, rot):
        u = bone_dir(sk, rot, f"upperarm_{s}", f"lowerarm_{s}")
        h = np.cross(u, FRONT)
        side = 1 if s == "l" else -1
        # out and up: about her front axis, away from her body
        return turned(sk, rot, sk.index[f"upperarm_{s}"], FRONT * side, deg)
    return f


class Regions:
    """Volumes round joints: the motion tool's elbow, wrist, knee, and a
    shoulder region (the deltoid's cap: 6 cm up into the collarbone's flesh
    to 12 cm down the upper arm)."""

    def __init__(self, b):
        self.m = motion.Measure(b)
        self.b = b
        sk = b.sk
        I = sk.index
        _, rp = sk.rest_globals()
        rp = rp[0]
        T = self.m.Tskin
        self.extra = {}
        for s in "lr":
            sh, el = rp[I[f"upperarm_{s}"]], rp[I[f"lowerarm_{s}"]]
            u = (el - sh) / np.linalg.norm(el - sh)
            P = b.P
            ok = (((P - (sh - u * 0.06)) @ u) > 0) & (((P - (sh + u * 0.12)) @ u) < 0)
            ok &= np.linalg.norm(np.cross(P - sh, u), axis=1) < 0.11
            self.extra[("shoulder", s)] = (T[ok[T].all(1)], I[f"upperarm_{s}"])

    def volumes(self, P, G):
        out = self.m.volumes(P, G)
        for key, (T, j) in self.extra.items():
            o = G[j][:3, 3]
            a, bb, c = P[T[:, 0]] - o, P[T[:, 1]] - o, P[T[:, 2]] - o
            out[key] = float(np.einsum("ij,ij->i", a, np.cross(bb, c)).sum() / 6)
        return out


def run(which):
    b = body(which)
    R = Regions(b)
    rest = R.volumes(b.P, b.rest)
    rows = []

    def meas(label, edits, keys):
        G = pose(b, edits)
        P = b.pose(G)
        v = R.volumes(P, G)
        rows.append((label, {k: v[k] / rest[k] for k in keys}))

    for deg in (45, 90, 120, 145):
        meas(f"elbow {deg}", [elbow("l", deg), elbow("r", deg)], [("elbow", "l"), ("elbow", "r")])
    for deg in (45, 90, 120, 145):
        meas(f"knee {deg}", [knee("l", deg), knee("r", deg)], [("knee", "l"), ("knee", "r")])
    for deg in (-80, 80):
        meas(f"wrist turn {deg} (hand only)", [wrist_turn("l", deg), wrist_turn("r", deg)],
             [("wrist", "l"), ("wrist", "r"), ("elbow", "l"), ("elbow", "r")])
        meas(f"wrist turn {deg} (half forearm)", [wrist_turn("l", deg, 0.5), wrist_turn("r", deg, 0.5)],
             [("wrist", "l"), ("wrist", "r"), ("elbow", "l"), ("elbow", "r")])
    for deg in (-70, 70):
        meas(f"upper arm twist {deg}", [arm_twist("l", deg), arm_twist("r", deg)],
             [("shoulder", "l"), ("shoulder", "r"), ("elbow", "l"), ("elbow", "r")])
    for deg in (60, 100, 130):
        meas(f"arm raised {deg}", [arm_raise("l", deg), arm_raise("r", deg)], [("shoulder", "l"), ("shoulder", "r")])
    meas("elbow 120 + wrist 80", [elbow("l", 120), elbow("r", 120), wrist_turn("l", 80, 0.5), wrist_turn("r", 80, 0.5)],
         [("elbow", "l"), ("elbow", "r"), ("wrist", "l"), ("wrist", "r")])
    return rows


if __name__ == "__main__":
    allrows = {}
    for w in sys.argv[1:]:
        allrows[w] = run(w)
        print("done", w, flush=True)
    labels = [r[0] for r in next(iter(allrows.values()))]
    for i, lab in enumerate(labels):
        cells = []
        for w, rows in allrows.items():
            d = rows[i][1]
            cells.append(w + " " + " ".join(f"{k[0][:2]}{k[1]} {100 * v:5.1f}" for k, v in d.items()))
        print(f"{lab:32s} | " + " | ".join(cells))
