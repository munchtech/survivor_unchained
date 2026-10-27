"""elbow_sweep.py: her elbow measured through a bend (Body 14, 26 Oct), on any body, with A/B toggles on the rig.

The upper arm hung straight down (or swung forward), the elbow bent about its hinge 0..145 degrees as bend() reads it,
posed with skin.Body (the game's stack), then measured in the posed upper arm's own frame (u down the humerus, f the
bend's front: the crease side, h the hinge):
  - weights: along the humerus (t 0 shoulder joint, 1 elbow joint, at rest), the share of the elbow's bend each point
    follows (lowerarm + its twists all, the elbow share and point half), back and front;
  - outline: the side view's back (triceps) and front (biceps) edge per t, against the same points hung straight
    (elbow 0): how far each edge moves out (+) or in (-) and where along t;
  - girth: the cross-section's hull perimeter at t .25/.5/.75/.9 against elbow 0;
  - front normals: the spread (deg) of the biceps' normals round the arm in the bend plane (small = flat);
  - crease: the inner elbow's closest skin to the joint, and the share of crease points folded through the upper
    arm's front edge.

    python tools/anim/elbow_sweep.py --body X.glb --skeleton Y.json [--side l] [--fwd 45] [--toggle nobulge,...]

Toggles: nobulge (share stretch off), nopush (point bone push off), nocorr (elbow_point shape off), share=X (the
share's amount), trim=T (the elbow's weights eased out of the humerus above t=T, handed to the upper arm),
pivot=MM (the elbow joint moved MM mm along the humerus, + toward the hand).
"""
from __future__ import annotations

import argparse
import copy
import json
import math
import os
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import helpers as hp   # noqa: E402
import skin            # noqa: E402
from rig import Skeleton, qaxis, qbetween, qinv, qmul, qrot  # noqa: E402

BENDS = [0, 30, 60, 90, 120, 145]
TS = [0.25, 0.5, 0.75, 0.9]
SPEC0 = copy.deepcopy(hp.SPEC)


def load(body_file, skeleton_file):
    sk = Skeleton.load(Path(skeleton_file))
    return skin.Body(sk, [(Path(body_file), lambda n: n == "Heroine", "skin")], None, label="her", helpers=True)


def lower_set(sk, s):
    """Bones that follow the elbow's bend, with how much of it: the forearm's all, the shares' half."""
    out = {}
    for n, j in sk.index.items():
        if not n.endswith("_" + s):
            continue
        b = n[:-2]
        if b in ("lowerarm", "lowerarm_twist_01", "lowerarm_twist_02", "hand") or b.split("_")[0] in (
                "index", "middle", "ring", "pinky", "thumb"):
            out[j] = 1.0
        elif b in ("lowerarm_share", "lowerarm_point"):
            out[j] = 0.5
    return out


def dense(body, rows):
    D = np.zeros((len(rows), len(body.sk.names)))
    for k in range(body.J.shape[1]):
        np.add.at(D, (np.arange(len(rows)), body.J[rows, k]), body.W[rows, k])
    return D


def set_dense(body, rows, D):
    n = body.J.shape[1]
    order = np.argsort(-D, axis=1)[:, :n]
    w = np.take_along_axis(D, order, 1)
    w = w / np.maximum(w.sum(1, keepdims=True), 1e-12)
    body.J[rows] = order
    body.Jv[rows] = order
    body.W[rows] = w


class Arm:
    """One arm of a body: rest frame and labels."""

    def __init__(self, body, s):
        self.body, self.s = body, s
        sk = body.sk
        I = sk.index
        self.ua, self.la, self.hd = I[f"upperarm_{s}"], I[f"lowerarm_{s}"], I[f"hand_{s}"]
        R = body.rest
        self.sh0, self.el0 = R[self.ua][:3, 3].copy(), R[self.la][:3, 3].copy()
        ax = self.el0 - self.sh0
        self.L = float(np.linalg.norm(ax))
        self.u0 = ax / self.L
        f = np.array([0, 0, 1.0]) - self.u0 * self.u0[2]
        self.f0 = f / np.linalg.norm(f)
        self.h0 = np.cross(self.u0, self.f0)
        rel = body.P - self.sh0
        self.t = rel @ self.u0 / self.L
        perp = rel - np.outer(rel @ self.u0, self.u0)
        self.r = np.linalg.norm(perp, axis=1)
        self.ang = np.degrees(np.arctan2(perp @ self.h0, perp @ self.f0))   # 0 front, +-180 back
        lw = lower_set(sk, s)
        arm = np.array([n.endswith("_" + s) and n.split("_")[0] in skin.ARM_PARTS + ("upperarm", "lowerarm")
                        or n.startswith(("upperarm_", "lowerarm_", "delt_")) and n.endswith("_" + s) for n in sk.names])
        aw = np.zeros(len(body.P))
        fb = np.zeros(len(body.P))
        for k in range(body.J.shape[1]):
            aw += body.W[:, k] * arm[body.J[:, k]]
            fb += body.W[:, k] * np.array([lw.get(j, 0.0) for j in range(len(sk.names))])[body.J[:, k]]
        self.armw, self.follow = aw, fb
        self.skin = body.kind == "skin"
        self.sel = self.skin & (aw > 0.6) & (self.t > -0.1) & (self.t < 1.6) & (self.r < 0.08)

    def profile(self):
        """Per t (rest), the share of the elbow's bend followed: back and front (mean, |t| bins of 0.05)."""
        out = []
        for t0 in np.arange(0.2, 1.21, 0.05):
            m = self.sel & (np.abs(self.t - t0) < 0.025)
            back = m & (np.abs(self.ang) > 135)
            front = m & (np.abs(self.ang) < 45)
            out.append((round(float(t0), 2), float(self.follow[back].mean()) if back.any() else np.nan,
                        float(self.follow[front].mean()) if front.any() else np.nan))
        return out

    def bones_along(self, names):
        """Mean weight per named bone (suffix added) per t bin, all round."""
        sk = self.body.sk
        rows = np.nonzero(self.sel)[0]
        D = dense(self.body, rows)
        t = self.t[rows]
        res = {}
        for n in names:
            j = sk.index.get(f"{n}_{self.s}")
            if j is None:
                continue
            res[n] = [(round(float(t0), 2), float(D[np.abs(t - t0) < 0.025, j].mean())) for t0 in np.arange(0.2, 1.21, 0.05)]
        return res

    def landmarks(self):
        """The rest elbow's olecranon (the back's furthest point out near the joint) and the crease (the front's
        deepest point near it), along the humerus from the joint (mm, + toward the hand), and out from the line."""
        m = self.sel & (self.t > 0.75) & (self.t < 1.25)
        out = {}
        for tag, side in (("back", np.abs(self.ang) > 150), ("front", np.abs(self.ang) < 30)):
            k = m & side
            ts = np.arange(0.76, 1.25, 0.02)
            prof = [(t0, float(self.r[k & (np.abs(self.t - t0) < 0.012)].max())) for t0 in ts
                    if (k & (np.abs(self.t - t0) < 0.012)).any()]
            out[tag] = prof
        return out


DEV_AT = ((0, 0.0), (20, 16.0), (45, 16.0), (90, 10.0), (135, 3.0), (180, 0.0))   # flexion -> sideways swing (deg)
HINGE = "rig"   # --hinge: the bend's axis, "rig" (across the humerus and her front) or "x" (the elbow share's own X)


def hang_pose(body, s, deg, fwd=0.0):
    """Rest rotations with her upper arm hung straight down (then swung `fwd` degrees forward) and the elbow bent
    `deg` (as bend reads it) about its hinge (across the humerus and her front)."""
    sk = body.sk
    I = sk.index
    ua, la = I[f"upperarm_{s}"], I[f"lowerarm_{s}"]
    rot = sk.rest_rot.copy()
    grot, gpos = sk.fk(rot[None])
    d = gpos[0, la] - gpos[0, ua]
    d = d / np.linalg.norm(d)
    want = np.array([0, -1.0, 0])
    if fwd:
        want = qrot(qaxis([1.0, 0, 0], -fwd), want)
    sw = qbetween(d, want)
    g_ua = qmul(sw, grot[0, ua])
    rot[ua] = qmul(qinv(grot[0, sk.parent[ua]]), g_ua)
    grot, gpos = sk.fk(rot[None])
    # the hinge: the rig's (across the humerus and her front at rest, as hinge_turn sets the shares), carried by the
    # upper arm's swing, so the forearm bends in the shares' own plane
    h = np.cross(d, [0, 0, 1.0])
    h = qrot(sw, h / np.linalg.norm(h))
    if HINGE == "flex":
        # (Body 19) as her clips bend it: the forearm FLEXED deg about its own X (helpers.flexion) and swung toward
        # the humerus' line as her clips carry it at that flexion (DEV_AT, Body 19's census); its local turn only
        la_rest = sk.rest_rot[la]
        hum = gpos[0, la] - gpos[0, ua]
        sx = math.copysign(1.0, float(hum @ qrot(grot[0, la], [1.0, 0, 0])))
        dv = math.radians(float(np.interp(deg, *zip(*DEV_AT))))
        f = math.radians(deg)
        want = np.array([sx * math.sin(dv), math.cos(dv) * math.cos(f), math.cos(dv) * math.sin(f)])
        r = rot.copy()
        r[la] = qmul(la_rest, qbetween([0, 1.0, 0], want))
        return r
    if HINGE == "x":
        # the share's own X (square to the forearm: a bend about it rolls the forearm none), as the clips bend
        h = qrot(qmul(grot[0, ua], sk.rest_rot[I[f"lowerarm_share_{s}"]]), [1.0, 0, 0])
        h = h * np.sign(h @ qrot(sw, np.cross(d, [0, 0, 1.0])))
    g_la0 = grot[0, la]

    def at(a):
        r = rot.copy()
        r[la] = qmul(qinv(grot[0, ua]), qmul(qaxis(h, a), g_la0))
        return r
    a = float(deg)
    for _ in range(5):
        a += deg - hp.bend(sk, at(a), f"lowerarm_{s}")
    return at(a)


def posed(body, rot):
    clip = skin.Clip("sweep", 30.0, rot[None], body.sk.rest_pos[None].copy(), False)
    G = body.globals(clip, 0, {}, 1 / 30)
    return G, body.pose(G)


def frame(G, arm):
    """The posed upper arm's frame: its rest frame (u down the humerus, f her front square to it, h across) carried
    by the upper arm bone's own turn, so it is the same material frame at every bend."""
    sh, el = G[arm.ua][:3, 3], G[arm.la][:3, 3]
    R = G[arm.ua][:3, :3] @ np.linalg.inv(arm.body.rest[arm.ua][:3, :3])
    u = (el - sh) / np.linalg.norm(el - sh)
    f = R @ arm.f0
    f = f - u * (f @ u)
    f = f / np.linalg.norm(f)
    return sh, el, u, f, np.cross(u, f)


def outline(V, G, arm, keep=None):
    """Side view (along the hinge) of the arm's points: per posed t bin, the front (+f) and back (-f) edge (mm out
    from the humerus' line)."""
    sh, el, u, f, h = frame(G, arm)
    L = np.linalg.norm(el - sh)
    sel = arm.sel if keep is None else keep
    rel = V[sel] - sh
    t = rel @ u / L
    y = rel @ f
    x = rel @ h * (-1.0 if arm.s == "l" else 1.0)   # + her outer side (lateral)
    out = []
    for t0 in np.arange(0.15, 1.01, 0.05):
        m = np.abs(t - t0) < 0.025
        if m.sum() < 5:
            out.append((t0, np.nan, np.nan, np.nan, np.nan))
            continue
        out.append((round(float(t0), 2), float(y[m].max() * 1000), float(-y[m].min() * 1000),
                    float(x[m].max() * 1000), float(-x[m].min() * 1000)))
    return out


def upper_only(arm):
    """Points that are the upper arm's at rest (t .1-.95): the forearm's own excluded from the side view."""
    return arm.sel & (arm.t > 0.1) & (arm.t < 0.97)


def girth(V, G, arm):
    from scipy.spatial import ConvexHull
    sh, el, u, f, h = frame(G, arm)
    L = np.linalg.norm(el - sh)
    rel = V[upper_only(arm)] - sh
    t = rel @ u / L
    out = {}
    for t0 in TS:
        m = np.abs(t - t0) < 0.012
        q = np.stack([rel[m] @ f, rel[m] @ h], 1)
        if len(q) < 8:
            out[t0] = np.nan
            continue
        out[t0] = float(ConvexHull(q).area * 1000)   # 2D hull: area is the perimeter
    return out


def normals(V, T):
    return skin._normals(V, T)


def front_spread(V, N, G, arm):
    """The biceps' patch (rest t .45-.85, within 50 deg of the front): normals' angle round the arm in the posed
    frame, its spread (std, deg), and their mean tilt along the arm (deg; + toward the hand: the patch facing down)."""
    sh, el, u, f, h = frame(G, arm)
    m = arm.sel & (arm.t > 0.45) & (arm.t < 0.85) & (np.abs(arm.ang) < 50)
    n = N[m]
    around = np.degrees(np.arctan2(n @ h, n @ f))
    tilt = np.degrees(np.arcsin(np.clip(n @ u, -1, 1)))
    return float(np.std(around)), float(np.mean(tilt)), float(np.std(tilt))


def crease(V, G, arm):
    """The inner elbow: rest points within 4 cm of the joint on the front (|ang| < 40): their closest posed
    distance to the joint (mm, rest's min alongside), and how many sit behind the upper arm's front edge line."""
    m = arm.sel & (np.abs(arm.t - 1.0) * arm.L < 0.04) & (np.abs(arm.ang) < 40)
    el = G[arm.la][:3, 3]
    d = np.linalg.norm(V[m] - el, axis=1)
    d0 = np.linalg.norm(arm.body.P[m] - arm.el0, axis=1)
    return float(d.min() * 1000), float(d0.min() * 1000)


def olecranon(V, G, arm):
    """(Body 19, as solver 1's am.py) the elbow's back point: in the posed upper arm's frame, the back edge (|across|
    < 25 mm) per 7.5 mm along the humerus from the joint, against the upper arm's back line (z -60..-30 mm) carried on:
    its most beyond that line at z -7.5..+22.5 mm (mm)."""
    sh, el, u, f, h = frame(G, arm)
    rel = V[arm.sel] - el
    y, z, x = rel @ f, rel @ u * 1000, rel @ h
    near = np.abs(x) < 0.025
    rows = []
    for z0 in np.arange(-60, 31, 7.5):
        k = near & (np.abs(z - z0) < 3.75)
        rows.append((z0, -y[k].min() * 1000 if k.any() else np.nan))
    rows = np.array(rows)
    up = rows[(rows[:, 0] >= -60) & (rows[:, 0] <= -30)]
    c = np.polyfit(up[:, 0], up[:, 1], 1)
    tip = rows[(rows[:, 0] >= -7.5) & (rows[:, 0] <= 22.5)]
    return float(np.nanmax(tip[:, 1] - np.polyval(c, tip[:, 0])))


KEEP_V = False


def elbow_volume(V, G, arm, T):
    """A closed-ish measure: the arm's points within 6 cm of the joint, their hull volume (cm^3)."""
    from scipy.spatial import ConvexHull
    el = G[arm.la][:3, 3]
    m = arm.sel & (np.linalg.norm(V - el, axis=1) < 0.06)
    return float(ConvexHull(V[m]).volume * 1e6)


# ------------------------------------------------------------------ toggles --
def apply_toggles(body, s, toggles):
    """Set hp.SPEC (and the body's weights, shapes, rest) for the toggles; returns an undo."""
    hp.SPEC.clear()
    hp.SPEC.update(copy.deepcopy(SPEC0))
    saved = (body.W.copy(), body.J.copy(), body.Jv.copy(), dict(body.corr), body.sk.rest_pos.copy(), body.rest.copy(),
             body.rest_inv.copy())
    for tg in toggles:
        k, _, v = tg.partition("=")
        if k == "nobulge":
            for h in hp.SPEC["helpers"]:
                if h["name"] == "lowerarm_share_{s}":
                    h["bulge"] = 0.0
        elif k == "nopush":
            for h in hp.SPEC["helpers"]:
                if h["name"] == "lowerarm_point_{s}":
                    h["push"] = 0.0
        elif k == "nocorr":
            body.corr = {c: d for c, d in body.corr.items() if not c.startswith("elbow_point")}
        elif k == "share":
            for h in hp.SPEC["helpers"]:
                if h["name"] in ("lowerarm_share_{s}", "lowerarm_point_{s}"):
                    h["amount"] = float(v)
        elif k in ("hinge", "nohinge"):
            for h in hp.SPEC["helpers"]:
                if h["name"] in ("lowerarm_share_{s}", "lowerarm_point_{s}"):
                    h["hinge"] = k == "hinge"
        elif k == "trim":
            trim(body, s, float(v))
        elif k == "etrim":
            # helpers.elbow_trim (SPEC "elbow_trim"; v "bf0:bf1:side0:side1" overrides its cuts)
            if v:
                q = [float(x) for x in v.split(":")]
                hp.SPEC["elbow_trim"]["bf"], hp.SPEC["elbow_trim"]["side"] = q[:2], q[2:4]
            etrim(body, s)
        elif k == "pivot":
            move_pivot(body, s, float(v) / 1000)
    return saved


def undo(body, saved):
    body.W, body.J, body.Jv, body.corr = saved[0], saved[1], saved[2], saved[3]
    body.sk.rest_pos[:] = saved[4]
    body.rest, body.rest_inv = saved[5], saved[6]
    hp.SPEC.clear()
    hp.SPEC.update(copy.deepcopy(SPEC0))


def trim(body, s, t_cut, fade=0.15):
    """The elbow's bones' weight eased out of the humerus above t_cut (none left by t_cut - fade), given to the
    upper arm's own chain there (its node by t)."""
    arm = Arm(body, s)
    sk = body.sk
    rows = np.nonzero(arm.skin & (arm.t < t_cut) & (arm.armw > 0.3))[0]
    D = dense(body, rows)
    t = arm.t[rows]
    keep = hp._smooth((t - (t_cut - fade)) / fade)
    lw = lower_set(sk, s)
    moved = np.zeros(len(rows))
    for j in lw:
        moved += D[:, j] * (1 - keep)
        D[:, j] *= keep
    # to the upper arm: its chain node nearest by t, else the bone itself
    tc = hp.SPEC["twist_chain"]
    nodes = [(sk.index.get(n.replace("{s}", s)), tt) for n, tt in tc["nodes"]]
    nodes = [(j, tt) for j, tt in nodes if j is not None] if hp.has_chain(sk.index, s) else [(sk.index[f"upperarm_{s}"], 1.0)]
    near = np.array([min(nodes, key=lambda n: abs(n[1] - x))[0] for x in t])
    D[np.arange(len(rows)), near] += moved
    set_dense(body, rows, D)


def etrim(body, s):
    """helpers.elbow_trim on the body's weights (its rest space, her front +Z)."""
    sk = body.sk
    rows = np.nonzero(body.kind == "skin")[0]
    D = dense(body, rows)
    heads = {n: body.rest[j][:3, 3] for n, j in sk.index.items()}
    D2 = hp.elbow_trim(D, body.P[rows], sk.names, heads, s)
    ch = np.nonzero(np.abs(D2 - D).max(1) > 0)[0]
    set_dense(body, rows[ch], D2[ch])


def move_pivot(body, s, d):
    """The elbow joint (and its helpers at it) moved d m along the humerus; the hand's offset kept in the world."""
    sk = body.sk
    I = sk.index
    la, ua = I[f"lowerarm_{s}"], I[f"upperarm_{s}"]
    grot, gpos = sk.rest_globals()
    u = gpos[0, la] - gpos[0, ua]
    u = u / np.linalg.norm(u)
    du = qrot(qinv(grot[0, ua]), u * d)   # in the upper arm's frame
    for n in (f"lowerarm_{s}", f"lowerarm_share_{s}", f"lowerarm_point_{s}"):
        if n in I:
            sk.rest_pos[I[n]] = sk.rest_pos[I[n]] + du
    for j, p in enumerate(sk.parent):
        if p == la:   # its children: back by the same, in the forearm's frame
            sk.rest_pos[j] = sk.rest_pos[j] - qrot(qinv(grot[0, la]), u * d)
    grot, gpos = sk.rest_globals()
    body.rest = body._mats(grot[0], gpos[0])
    body.rest_inv = np.linalg.inv(body.rest)


# ------------------------------------------------------------------ report --
def sweep(body, s, fwd=0.0, toggles=(), bends=BENDS, quiet=False):
    saved = apply_toggles(body, s, toggles)
    try:
        arm = Arm(body, s)
        Ts = body.T[(body.kind[body.T] == "skin").all(1)]
        rows = []
        ref = None
        for deg in bends:
            rot = hang_pose(body, s, deg, fwd)
            G, V = posed(body, rot)
            N = normals(V, Ts)
            ol = outline(V, G, arm, upper_only(arm))
            gi = girth(V, G, arm)
            fs = front_spread(V, N, G, arm)
            cr = crease(V, G, arm)
            vol = elbow_volume(V, G, arm, Ts)
            rows.append(dict(deg=deg, outline=ol, girth=gi, spread=fs, crease=cr, vol=vol, ole=olecranon(V, G, arm),
                             V=V if KEEP_V else None))
        return rows
    finally:
        undo(body, saved)


def summarize(rows):
    ref = rows[0]
    lines = []
    for r in rows:
        dback = [(o[0], o[2] - o0[2]) for o, o0 in zip(r["outline"], ref["outline"])]
        dfront = [(o[0], o[1] - o0[1]) for o, o0 in zip(r["outline"], ref["outline"])]
        dlat = np.array([o[3] - o0[3] for o, o0 in zip(r["outline"], ref["outline"])])
        dmed = np.array([o[4] - o0[4] for o, o0 in zip(r["outline"], ref["outline"])])
        db = np.array([x for _, x in dback])
        dfr = np.array([x for _, x in dfront])
        ts = np.array([t for t, _ in dback])
        upto = ts <= 0.86
        ib = int(np.nanargmax(np.abs(db[upto])))
        jf = int(np.nanargmax(np.abs(dfr[upto])))
        lines.append(
            f"{r['deg']:4d}  back d(mm) " + " ".join(f"{x:+5.1f}" for x in db[::2]) +
            f" | max {db[upto][ib]:+5.1f}@t{ts[upto][ib]:.2f}"
            f"  front " + " ".join(f"{x:+5.1f}" for x in dfr[::2]) + f" | max {dfr[upto][jf]:+5.1f}@t{ts[upto][jf]:.2f}"
            f"  lat " + " ".join(f"{x:+5.1f}" for x in dlat[::2]) + "  med " + " ".join(f"{x:+5.1f}" for x in dmed[::2]) +
            f"  girth% " + " ".join(f"{100 * (r['girth'][t] / ref['girth'][t] - 1):+5.1f}" for t in TS) +
            f"  bic spread {r['spread'][0]:4.1f} tilt {r['spread'][1]:+5.1f}  crease {r['crease'][0]:4.1f}mm  vol {r['vol']:5.0f}"
            f" ({100 * (r['vol'] / ref['vol'] - 1):+4.0f}%)  ole {r['ole']:+5.1f}")
    lines.insert(0, "deg   back/front edge change vs elbow 0 at t=" + " ".join(f"{o[0]:.2f}" for o in ref["outline"][::2]))
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--body", required=True)
    ap.add_argument("--skeleton", required=True)
    ap.add_argument("--side", default="lr")
    ap.add_argument("--fwd", type=float, default=0.0)
    ap.add_argument("--toggle", default="")
    ap.add_argument("--weights", action="store_true")
    ap.add_argument("--hinge", default="rig", choices=["rig", "x", "flex"])
    ap.add_argument("--bends", default="")
    a = ap.parse_args()
    global HINGE
    HINGE = a.hinge
    body = load(a.body, a.skeleton)
    for s in a.side:
        arm = Arm(body, s)
        print(f"== side {s}: humerus {arm.L * 1000:.0f} mm")
        if a.weights:
            print("t     follow(back) follow(front)")
            for t0, b, f in arm.profile():
                print(f"{t0:.2f}  {b:.3f}  {f:.3f}")
            names = ["upperarm", "upperarm_twist_01", "upperarm_twist_02", "upperarm_twist_03", "upperarm_twist_04",
                     "lowerarm_share", "lowerarm_point", "lowerarm", "lowerarm_twist_01", "upperarm_share", "clavicle", "delt"]
            ba = arm.bones_along(names)
            print("t     " + " ".join(f"{n[-10:]:>10s}" for n in ba))
            for i in range(len(next(iter(ba.values())))):
                print(f"{ba['upperarm'][i][0]:.2f}  " + " ".join(f"{ba[n][i][1]:10.3f}" for n in ba))
            lm = arm.landmarks()
            for tag, prof in lm.items():
                print(tag, " ".join(f"{(t - 1) * arm.L * 1000:+.0f}:{r * 1000:.1f}" for t, r in prof))
        tg = [x for x in a.toggle.split(",") if x]
        bends = [int(x) for x in a.bends.split(",")] if a.bends else BENDS
        print(summarize(sweep(body, s, a.fwd, tg, bends)))


if __name__ == "__main__":
    main()
