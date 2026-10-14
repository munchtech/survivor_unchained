"""Her right fist on a held piece's grip: measured in the built clips, and re-derived (keyed.py WRAP) from her hand.
    python tools/anim/fistfit.py sword                  the table: every clip that holds it, at each contact frame
                                                        (and its rest frame), against the pass below
    python tools/anim/fistfit.py sword --fit            re-fit WRAP["sword"] on the hand as it is now, then the table
                                                        for the fitted fist (laid on each clip's frames)
    python tools/anim/fistfit.py sword --fit --seat 127,137,147   also try the grip's line moved along her fingers (mm,
                                                        hand_r y of the line at the seat's height); the best seat wins
    python tools/anim/fistfit.py sword --fit --seat 95,105 --hand '{"knuckles": 20}'   the same on a corrected hand
                                                        (set_hand: the body build's change, modelled; never written)
    python tools/anim/fistfit.py sword --fit --write    write the fitted WRAP["sword"] into keyed.py (and the seat into
                                                        WeaponSockets.cs if it moved: then rebuild the clips and re-dump
                                                        arms_local, tools_scenes/arms_dump.gd)
Everything is read, nothing typed in: her finger bones from the skeleton dump (data/heroine_skeleton.json), the pads'
offsets from her skinned body (skin.Body.heroine, the piece's outfit), the hilt's profile from data/arms_local.json
(the piece as the game seats it, hand_r space), the seat from godot/logic/Play/WeaponSockets.cs. So when her hand is
rebuilt (outfits) this re-derives the fist in one command.

The pass (PASS below), per finger at every measured frame: the two outer pads (02, 03 bones) on the leather (gap
-0.5..1.5 mm), nothing of the hand more than 0.5 mm into the hilt, the finger's end not past the grip's far side in
the hand's frame (HANG: the end of its skin no further from the palm than the grip's far surface: a fist, not fingers hooked
over a bar with their ends hanging below it), adjacent fingers touching (ADJ), the last joint at most CAP3 degrees (a
claw past that). And every clip that holds the piece lays the same fist (OFF: its fingers within 3 deg of WRAP's).
Wrist: flex (+ toward the palm) and deviation (+ away from the thumb) at each frame, reported (the swing's drape).
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import minimize
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from rig import Skeleton, DATA, Clip, qrot, qinv, qmul, qaxis, qmatrix  # noqa: E402
import audit  # noqa: E402
import keyed  # noqa: E402
import skin  # noqa: E402

ROOT = HERE.parent.parent
CLIPS = HERE / "out" / "clips"
SOCKETS = ROOT / "godot" / "logic" / "Play" / "WeaponSockets.cs"
FINGERS = ("index", "middle", "ring", "pinky")
ALLF = FINGERS + ("thumb",)
# A piece: its mesh in arms_local, its seat's constants in WeaponSockets.cs, the outfit whose hand holds it, and the
# frame its rest is fitted on.
PIECES = {"sword": dict(arms="chevalier_sword@hand_r", at="BladeAtR", dir="BladeDirR", outfit="warden", rest=("idle_warden", 76))}
PAD = (-0.5, 1.5)     # mm: the 02/03 pads' gap to the leather
IN_MAX = 0.5          # mm: deepest any of the hand may go into the hilt
HANG_MAX = 0.0        # mm: the finger's end past the grip's far surface (along the palm's normal). Its end is its skin's
                      # (end_point): on her 0.93 hand (080103ba) the tip joints sit 3.6-6.3 mm out past the skin, in the air.
ADJ_MAX = 2.0         # mm: adjacent fingers' outer bones apart
CAP3 = 62.0           # deg: the last joint's bend
WRAP_MIN = 180.0      # deg: how far round the line the finger's end has come (from the palm, the way the fingers
                      # close; 180 the far side). HANG alone passed fingers that never go round: laid along the grip
                      # or balled up in front of it with their ends near the palm (a search found such "passes").
OFF_MAX = 3.0         # deg: a held clip's fingers off WRAP's

sk = Skeleton.load(DATA / "heroine_skeleton.json")
I = sk.index
RIG = keyed.Rig(sk)
HB = [n for n in I if n.endswith("_r") and any(n.startswith(k) for k in ("hand",) + ALLF)]
CHAIN = sorted(j for n, j in I.items() if n.endswith("_r") and any(n.startswith(k) for k in ALLF))


def read_seat(piece):
    s = SOCKETS.read_text(encoding="utf-8")
    def vec(name):
        m = re.search(rf"{name}\s*=\s*new\(([^)]*)\)", s)
        return np.array([float(v.strip().rstrip("f")) for v in m.group(1).split(",")])
    return vec(PIECES[piece]["at"]), vec(PIECES[piece]["dir"])


def hilt_profile(piece, A, D, step=2.0):
    """(t mm along the line from the grip point, r mm): the piece's outer radius per slice (arms_local, as seated)."""
    V = np.array(json.load(open(DATA / "arms_local.json"))[PIECES[piece]["arms"]]["v"], float)
    dd = V - A; t = dd @ D * 1000; r = np.linalg.norm(dd - np.outer(dd @ D, D), axis=1) * 1000
    out = []
    for a in np.arange(np.floor(t.min()), t.max(), step):
        m = (t >= a) & (t < a + step)
        if m.sum() >= 3:
            out.append((a + step / 2, float(r[m].max())))
    return out


class Grip:
    def __init__(self, A, D, prof):
        self.A = np.asarray(A, float); self.D = np.asarray(D, float) / np.linalg.norm(D)
        self.pt = np.array([p[0] for p in prof]) / 1000; self.pr = np.array([p[1] for p in prof]) / 1000

    def R(self, t):
        return np.interp(t, self.pt, self.pr, left=np.nan, right=np.nan)

    def gap(self, X):
        """mm outside the surface (negative: inside), nan off the piece; t mm along the line."""
        dd = X - self.A; t = dd @ self.D
        r = np.linalg.norm(dd - np.outer(t, self.D), axis=1)
        return (r - self.R(t)) * 1000, t * 1000


_bodies = {}

# ------------------------------------------------------------ a modelled hand --
# A corrected hand for the body build, tried here before it is built (--hand, never written): finger joints' pivots
# moved in hand_r space with her skin left where it is, so the skin weighted to a bone turns about its moved pivot
# (the bind moves with the joint), and the skin a knuckle moved back passes over handed from the palm to its finger,
# ramped KNUCKLE_RAMP mm either side of the new pivot (as a skinning tool weights a joint).
HAND = {}
KNUCKLE_RAMP = 10.0     # mm


def set_hand(spec):
    """spec: "knuckles" mm each finger's 01 joint goes back along its metacarpal (toward the wrist's pivot);
    "knuckle_depth" mm each 01 joint goes toward the palm (hand -x); "dips" mm each 03 joint goes along its finger
    (+ toward the tip: a shorter end bone); "moves" {joint: [x, y, z] mm} as given. Before the first body()."""
    global HAND
    assert not _bodies, "set_hand before the first body()"
    grot, gpos = sk.rest_globals(); grot, gpos = grot[0], gpos[0]
    Rh = qmatrix(grot[I["hand_r"]]); ph = gpos[I["hand_r"]]
    loc = lambda n: Rh.T @ (gpos[I[n]] - ph)
    moves = {}
    for fn in FINGERS:
        p1 = loc(f"{fn}_01_r"); d = np.zeros(3)
        d -= p1 / np.linalg.norm(p1) * spec.get("knuckles", 0.0) / 1000
        d[0] -= spec.get("knuckle_depth", 0.0) / 1000
        if d.any():
            moves[f"{fn}_01_r"] = d
        if spec.get("dips"):
            a, b = loc(f"{fn}_02_r"), loc(f"{fn}_03_r")
            moves[f"{fn}_03_r"] = (b - a) / np.linalg.norm(b - a) * spec["dips"] / 1000
    for n, v in spec.get("moves", {}).items():
        moves[n] = moves.get(n, np.zeros(3)) + np.asarray(v, float) / 1000
    new = gpos.copy()
    for n, d in moves.items():
        new[I[n]] = gpos[I[n]] + Rh @ d
    moved = {I[n] for n in moves}
    for j in moved | {j for j in range(len(sk.parent)) if sk.parent[j] in moved}:
        sk.rest_pos[j] = qrot(qinv(grot[sk.parent[j]]), new[j] - new[sk.parent[j]])
    HAND = dict(spec=spec, moves={n: np.round(d * 1000, 1).tolist() for n, d in moves.items()}, old=gpos, new=new,
                Rh=Rh)
    print(f"modelled hand {json.dumps(spec)}: " + "; ".join(f"{n} {v}" for n, v in HAND["moves"].items()), flush=True)


def _model_body(b):
    """The modelled hand on a Body: each moved joint's bind, and the palm's skin a knuckle moved back passes over
    weighted to its finger (the share it had on hand_r, ramped about the new pivot)."""
    old, new = HAND["old"], HAND["new"]
    for j in range(len(new)):
        if not np.allclose(old[j], new[j]):
            b.rest[j][:3, 3] = new[j]
    b.rest_inv = np.linalg.inv(b.rest)
    hj = I["hand_r"]; fj = [I[f"{fn}_01_r"] for fn in FINGERS]
    if all(np.allclose(old[j], new[j]) for j in fj):
        return
    side = HAND["Rh"] @ np.array([0, 0, 1.0])            # across the knuckles (hand +z), character space
    kw = (b.J == hj) * b.W; wh = kw.sum(1)
    cand = np.nonzero(wh > 0)[0]
    P = b.P[cand]
    lat = np.stack([(P - new[j]) @ side for j in fj], 1)
    lane = np.argmin(np.abs(lat), 1)
    for li, j in enumerate(fj):
        m = old[j] - new[j]; L = np.linalg.norm(m)
        if L < 1e-6:
            continue
        m /= L
        sel = cand[(lane == li) & (np.abs(lat[:, li]) < 0.014)]
        t = (b.P[sel] - new[j]) @ m * 1000
        s = np.clip((t + KNUCKLE_RAMP) / (2 * KNUCKLE_RAMP), 0, 1); want = s * s * (3 - 2 * s)
        for v, wc in zip(sel, want):
            if wc <= 0:
                continue
            kh = int(np.nonzero(b.J[v] == hj)[0][0])
            kf = np.nonzero(b.J[v] == j)[0]
            if len(kf):
                kf = int(kf[0])
            else:
                order = [k for k in np.argsort(b.W[v]) if k != kh]
                kf = int(order[0]); b.W[v, kf] = 0.0; b.J[v, kf] = j
            tot = b.W[v, kh] + b.W[v, kf]; nf = max(b.W[v, kf], tot * wc)
            b.W[v, kf], b.W[v, kh] = nf, tot - nf
        b.W[sel] /= b.W[sel].sum(1, keepdims=True)


def body(outfit):
    if outfit not in _bodies:
        b = skin.Body.heroine(outfit=outfit, jiggle=False)
        if HAND:
            _model_body(b)
        Wst = np.stack([(b.W * (b.J == I[n])).sum(1) for n in HB], 1)
        sel = np.nonzero(Wst.max(1) > 0.5)[0]
        b._fist = dict(sel=sel, bone=np.array([HB[i] for i in Wst.argmax(1)[sel]]), kind=b.kind[sel])
        _bodies[outfit] = b
    return _bodies[outfit]


def load(path):
    d, rot, pos = audit.load(Path(path), sk)
    return d, rot, pos


class Hand:
    """One clip frame's right hand region (skin points, hand_r space), its finger chain re-posable."""
    def __init__(self, rot_f, pos_f, outfit):
        self.b = body(outfit); F = self.b._fist
        self.rot_f, self.pos_f = rot_f.copy(), pos_f.copy()
        sk_ = F["kind"] == "skin"
        self.idx = F["sel"][sk_]; self.bone = F["bone"][sk_]
        self.fing = {fn: np.nonzero(np.char.startswith(self.bone.astype(str), fn))[0] for fn in ALLF}
        self.palm = np.nonzero(self.bone == "hand_r")[0]
        self.G0 = self.b.globals(Clip("x", 30, self.rot_f[None], self.pos_f[None], False, {}), 0)
        h = I["hand_r"]; self.Rh = self.G0[h][:3, :3]; self.ph = self.G0[h][:3, 3]

    def G(self, rot_f):
        G = self.G0.copy()
        for j in CHAIN:
            L = np.eye(4); L[:3, :3] = qmatrix(rot_f[j]); L[:3, 3] = sk.rest_pos[j]   # the dump's bone lengths
            G[j] = G[sk.parent[j]] @ L
        return G

    def pose(self, rot_f, sub=None):
        sub = np.arange(len(self.idx)) if sub is None else sub
        return (self.b.pose(self.G(rot_f), self.idx[sub]) - self.ph) @ self.Rh

    def joints(self, rot_f):
        G = self.G(rot_f)
        return {n: (G[I[n]][:3, 3] - self.ph) @ self.Rh for n in HB}

    def rotf(self, ang, oppose=0.0, roll=0.0, spread=None):
        """Finger bends {finger: (a1, a2, a3)} laid as keyed.Rig.solve lays a WRAP (rest, the thumb's oppose and roll,
        each finger's spread at its base knuckle (spread {finger: deg}, keyed.spread_axis), then each bend about its
        joint's axis); fingers not given keep the frame's own."""
        r = self.rot_f.copy(); spread = spread or {}
        for name, angles in ang.items():
            for k, a in enumerate(angles):
                j = I[f"{name}_0{k + 1}_r"]
                q = sk.rest_rot[j]
                if k == 0 and spread.get(name):
                    q = qmul(q, qaxis(keyed.spread_axis(RIG, j), spread[name]))
                if name == "thumb" and k == 0:
                    if oppose:
                        along = qrot(qinv(RIG.grest[j]), qrot(RIG.grest[I["hand_r"]], [0, 1.0, 0]))
                        q = qmul(q, qaxis(along / np.linalg.norm(along), -oppose * 55))
                    if roll:
                        q = qmul(q, qaxis([0, 1.0, 0], roll))
                r[j] = qmul(q, qaxis(RIG.finger_axis[j], a)) if a else q
        return r


def wrap_args(w):
    ang = {k: list(v) for k, v in w["bends"].items()}
    return ang, w.get("oppose", 0.0), w.get("thumb_roll", 0.0), dict(w.get("spreads", {}))


def palm_dir(h, rf, gr):
    """The way from the grip's line to the palm (square to the line), hand_r space."""
    Xp = h.pose(rf, h.palm); g, _ = gr.gap(Xp)
    near = (g < 8) & ~np.isnan(g)
    if near.sum() < 3:      # the palm off the grip (a seat out along the fingers): its nearest points
        near = np.argsort(np.where(np.isnan(g), np.inf, g))[:30]
    P = Xp[near].mean(0)
    v = P - gr.A; u = v - (v @ gr.D) * gr.D
    return u / np.linalg.norm(u)


def wrap_angle(p, gr, u):
    """deg round the line from the palm (u) the way the fingers close (over the front, 180 the far side), -30..330."""
    q = p - gr.A; w0 = np.array([0, 1.0, 0]) - gr.D[1] * gr.D; w0 -= (w0 @ u) * u; w0 /= np.linalg.norm(w0)
    a = float(np.degrees(np.arctan2(q @ w0, q @ u)))
    return a + 360 if a < -30 else a


def end_point(X3, J, fn):
    """A finger's end: its last bone's skin point furthest along that bone (X3: that bone's skin points)."""
    a = J[f"{fn}_03_r"]; d = J[f"{fn}_04_leaf_r"] - a
    return X3[int(np.argmax((X3 - a) @ d))]


def measure(h, rf, gr):
    """Per finger: pads (01, 02, 03 min gap mm), deepest into the hilt, the tip's hang past the far side; the palm's
    gap, adjacent fingers' distance."""
    X = h.pose(rf); g, t = gr.gap(X); J = h.joints(rf); u = palm_dir(h, rf, gr)
    out = {}
    for fn in ALLF:
        sub = h.fing[fn]; B = h.bone[sub]; gs = g[sub]; ok = ~np.isnan(gs)
        pads = [round(float(gs[(B == f"{fn}_0{k}_r") & ok].min()), 1) if ((B == f"{fn}_0{k}_r") & ok).any() else None for k in (1, 2, 3)]
        e = end_point(X[sub][B == f"{fn}_03_r"], J, fn); v = e - gr.A; R = gr.R(v @ gr.D)
        out[fn] = dict(pads=pads, deepest=round(float(gs[ok].min()), 1) if ok.any() else None,
                       hang=round(float((-(v @ u) - R) * 1000), 1) if not np.isnan(R) else None,
                       wrap=round(wrap_angle(e, gr, u)))
    okp = ~np.isnan(g[h.palm])
    out["palm"] = round(float(g[h.palm][okp].min()), 1) if okp.any() else None
    out["deepest"] = round(float(np.nanmin(g)), 1)
    adj = {}
    for f1, f2 in zip(FINGERS, FINGERS[1:]):
        s1 = h.fing[f1][np.isin(h.bone[h.fing[f1]], [f"{f1}_02_r", f"{f1}_03_r"])]
        s2 = h.fing[f2][np.isin(h.bone[h.fing[f2]], [f"{f2}_02_r", f"{f2}_03_r"])]
        adj[f1[0] + f2[0]] = round(float(cKDTree(X[s2]).query(X[s1])[0].min() * 1000), 1)
    out["adj"] = adj
    return out


def verdict(m, ang=None):
    bad = []
    for fn in FINGERS:
        f = m[fn]
        for k, p in zip((2, 3), f["pads"][1:]):
            if p is None or not PAD[0] <= p <= PAD[1]:
                bad.append(f"{fn}{k} pad {p}")
        if f["hang"] is None or f["hang"] > HANG_MAX:
            bad.append(f"{fn} tip hangs {f['hang']}")
        if f["wrap"] < WRAP_MIN:
            bad.append(f"{fn} only {f['wrap']} deg round")
        if ang is not None and ang[fn][2] > CAP3:
            bad.append(f"{fn} end joint {ang[fn][2]:.0f}")
    if m["deepest"] < -IN_MAX:
        bad.append(f"into the hilt {m['deepest']}")
    for k, v in m["adj"].items():
        if v > ADJ_MAX:
            bad.append(f"{k} apart {v}")
    return bad


def wrist(rot, pos, f):
    g, p = sk.fk(rot[f:f + 1], pos[f:f + 1])
    h, la = I["hand_r"], I["lowerarm_r"]
    d = qrot(qinv(g[0, h]), p[0, h] - p[0, la]); d /= np.linalg.norm(d)
    return round(float(np.degrees(np.arctan2(d[0], d[1]))), 1), round(float(np.degrees(np.arctan2(d[2], d[1]))), 1)


def finger_off(rot_f, h, ang, opp, roll, spr=None):
    ref = h.rotf(ang, opp, roll, spr)
    return max(float(np.degrees(2 * np.arccos(min(1.0, abs(float(np.dot(rot_f[j], ref[j]))))))) for j in CHAIN)


# ------------------------------------------------------------------ fitting --
def seat_x(h, y0, w, D, prof, ang, opp, roll, spr=None):
    """The line's depth (hand x) at which the palm and the thumb's base sit 0.3 mm off the hilt (the fist as fitted
    so far: pass all its fingers, not only the thumb, or the frame's own fingers stand in for them)."""
    sub = np.concatenate([h.palm, h.fing["thumb"][h.bone[h.fing["thumb"]] == "thumb_01_r"]])
    X = h.pose(h.rotf(ang, opp, roll, spr), sub)
    lo, hi = -0.080, 0.0
    for _ in range(30):
        x = (lo + hi) / 2
        g, _ = Grip(np.array([x, y0, 0]) + w * D, D, prof).gap(X)
        if np.nanmin(g) > 0.3: lo = x
        else: hi = x
    return lo


# deg: each finger's spread at its base knuckle in a fist (+ toward the thumb side). Her rest hand is fanned (straight,
# her outer bones 8-11 mm apart: knuckles 22-23 mm apart, fingers 14-15 mm across), so closing them takes the outer
# fingers well in from it, the forefinger toward the little finger and the little finger toward the forefinger.
SPREAD = {"index": (-30.0, 8.0), "middle": (-20.0, 8.0), "ring": (-8.0, 20.0), "pinky": (-8.0, 30.0)}
ADJ_FIT = 1.2           # mm: the fit's aim for adjacent fingers' outer bones (ADJ_MAX the pass)


def _outer(h, fn):
    return h.fing[fn][np.isin(h.bone[h.fing[fn]], [f"{fn}_02_r", f"{fn}_03_r"])]


def _axis_dist(P, J, fn):
    """mm from each point to a finger's outer bones' line (02 -> 03 -> tip joints)."""
    pts = [J[f"{fn}_02_r"], J[f"{fn}_03_r"], J[f"{fn}_04_leaf_r"]]
    best = np.full(len(P), np.inf)
    for a, b in zip(pts, pts[1:]):
        d = b - a; L2 = float(d @ d); t = np.clip((P - a) @ d / L2, 0, 1)
        best = np.minimum(best, np.linalg.norm(P - (a + np.outer(t, d)), axis=1))
    return best * 1000


def fit_finger(h, fn, base, spr, gr, u, x0, opp=0.0, roll=0.0):
    """A finger's three bends and its spread: its pads on the grip, its end not past the far side, its outer bones
    against its neighbours' (ADJ_FIT mm, not into them), none of it or the palm into the hilt."""
    sub = h.fing[fn]; B = h.bone[sub]; outer = np.isin(B, [f"{fn}_02_r", f"{fn}_03_r"])
    lims = ((-10.0 if fn == "index" else 0.0, 95.0), (0.0, 105.0), (0.0, CAP3 - 2), SPREAD[fn])
    rf0 = h.rotf(base, opp, roll, spr); J0 = h.joints(rf0)
    nbs = []
    for f2 in FINGERS:
        if abs(FINGERS.index(f2) - FINGERS.index(fn)) == 1:
            Pn = h.pose(rf0, _outer(h, f2))
            nbs.append((f2, cKDTree(Pn), _axis_dist(Pn, J0, f2)))

    def cost(th):
        a = dict(base); a[fn] = list(th[:3]); s = dict(spr); s[fn] = th[3]
        rf = h.rotf(a, opp, roll, s)
        X = h.pose(rf, sub); g, _ = gr.gap(X); J = h.joints(rf)
        c = 0.0
        for k, wt in (("01", 1.0 if fn in ("ring", "pinky") else 0.5), ("02", 1.0), ("03", 1.0)):
            m = (B == f"{fn}_{k}_r") & ~np.isnan(g)
            if not m.any(): c += 400; continue
            d = g[m].min() - 0.6
            c += wt * (d * d if d > 0 else 25 * d * d)
        e = end_point(X[B == f"{fn}_03_r"], J, fn)
        tip = (np.linalg.norm(X - e, axis=1) < 0.010) & ~np.isnan(g)
        d = (g[tip].min() if tip.any() else 20.0) - 1.0
        if d > 0: c += d * d
        v = e - gr.A; R = gr.R(v @ gr.D)
        hang = (-(v @ u) - (0.016 if np.isnan(R) else R)) * 1000
        if hang > HANG_MAX - 1.5: c += 2 * (hang - HANG_MAX + 1.5) ** 2
        wa = wrap_angle(e, gr, u)
        if wa < WRAP_MIN + 10: c += 0.05 * (WRAP_MIN + 10 - wa) ** 2
        gg = g[~np.isnan(g)]
        c += 50 * float((np.clip(-0.3 - gg, 0, None) ** 2).sum())
        gp, _ = gr.gap(h.pose(rf, h.palm)); gp = gp[~np.isnan(gp)]
        c += 50 * float((np.clip(-0.3 - gp, 0, None) ** 2).sum())
        Xo = X[outer]
        for f2, tree, rax in nbs:
            dd, ii = tree.query(Xo); dmin = dd.min() * 1000
            if dmin > ADJ_FIT: c += 5 * (dmin - ADJ_FIT) ** 2
            # Into the neighbour: nearer its line than its own skin there.
            ins = rax[ii] - _axis_dist(Xo, J0, f2) - 0.3
            c += 20 * float((np.clip(ins, 0, None) ** 2).sum())
        for v_, (lo, hi) in zip(th, lims):
            if v_ < lo: c += 4 * (lo - v_) ** 2
            if v_ > hi: c += 4 * (v_ - hi) ** 2
        return c
    best = None
    lean = {"index": -20, "middle": -8, "ring": 8, "pinky": 20}[fn]
    for s0 in (tuple(x0), (40, 70, 50, lean), (60, 60, 40, lean / 2), (30, 90, 55, lean), (70, 80, 30, lean * 1.3),
               (50, 85, 55, 0)):
        s = minimize(cost, np.array(s0, float), method="Nelder-Mead",
                     options={"xatol": 0.2, "fatol": 0.01, "maxiter": 1200, "adaptive": True})
        if best is None or s.fun < best.fun: best = s
    return [round(float(v), 1) for v in best.x[:3]], round(float(best.x[3]), 1)


def fit_thumb(h, gr, ang, x0, span, tgt=0.4, d_lo=1.0, d_hi=3.0, spr=None):
    """Oppose, roll and three bends: its outer pads on the grip, none of it inside, its last bone over the forefinger's
    or middle finger's outer bones (d_lo..d_hi mm off them), its tip within `span` (mm along the line)."""
    sub_t = h.fing["thumb"]; sub_i = np.concatenate([h.fing["index"], h.fing["middle"]])
    tb = h.bone[sub_t]; ib = h.bone[sub_i]
    over = np.isin(ib, ["index_02_r", "index_03_r", "middle_02_r", "middle_03_r"])
    def cost(x):
        opp, roll, a1, a2, a3 = x
        a = dict(ang); a["thumb"] = [a1, a2, a3]
        rf = h.rotf(a, opp, roll, spr)
        Xt = h.pose(rf, sub_t); Xi = h.pose(rf, sub_i); g, _ = gr.gap(Xt)
        c = 0.0
        for n, w in (("thumb_02_r", 0.5), ("thumb_03_r", 1.0)):
            m = (tb == n) & ~np.isnan(g)
            if not m.any(): c += 400; continue
            d = g[m].min() - tgt; c += w * (d * d if d > 0 else 25 * d * d)
        c += 50 * float((np.clip(-0.4 - g[~np.isnan(g)], 0, None) ** 2).sum())
        d3 = cKDTree(Xi[over]).query(Xt[tb == "thumb_03_r"])[0].min() * 1000
        dall = cKDTree(Xi).query(Xt)[0].min() * 1000
        if d3 > d_hi: c += 2 * (d3 - d_hi) ** 2
        if dall < d_lo: c += 20 * (d_lo - dall) ** 2
        tt = float((h.joints(rf)["thumb_04_leaf_r"] - gr.A) @ gr.D) * 1000
        if tt < span[0]: c += (span[0] - tt) ** 2
        if tt > span[1]: c += (tt - span[1]) ** 2
        for v, lo, hi, s in ((opp, 0.0, 1.0, 30), (roll, -45, 45, 1), (a1, -15, 60, 1), (a2, -10, 80, 1), (a3, -10, 90, 1)):
            if v < lo: c += ((lo - v) * s) ** 2
            if v > hi: c += ((v - hi) * s) ** 2
        return c
    best = None
    for s0 in (x0, (0.3, -30, 20, 30, 50), (0.7, 0, 0, 40, 40), (0.5, -40, 30, 10, 60)):
        s = minimize(cost, np.array(s0, float), method="Nelder-Mead", options={"xatol": 0.05, "fatol": 0.005, "maxiter": 1500, "adaptive": True})
        if best is None or s.fun < best.fun: best = s
    return [round(float(v), 2) for v in best.x]


def fit(piece, y0s=None, prof=None, iters=3):
    """Re-derive the WRAP (and, given y0s, the seat) on the rest frame. Returns (wrap, A, prof)."""
    P = PIECES[piece]; A0, D = read_seat(piece); D = D / np.linalg.norm(D)
    prof = prof or hilt_profile(piece, A0, D)
    _, rot, pos = load(CLIPS / f"{P['rest'][0]}.json"); h = Hand(rot[P["rest"][1]], pos[P["rest"][1]], P["outfit"])
    # A = (x, y0, 0) + w D: w (where along the hilt the hand is) kept; y0 the line's place along her fingers, x its depth.
    w = float(A0[2] / D[2]); base0 = A0 - w * D
    old, opp0, roll0, spr0 = wrap_args(keyed.WRAP[piece])
    best = None
    for y0 in (y0s or [base0[1] * 1000]):
        y0 /= 1000
        ang = {fn: list(old[fn]) for fn in FINGERS}; th = [opp0, roll0] + list(old["thumb"])
        spr = {fn: float(spr0.get(fn, 0.0)) for fn in FINGERS}
        for it in range(iters):
            a = dict(ang, thumb=th[2:])
            # The line's depth for the fist as fitted so far (its fingers too, not the frame's own).
            x = base0[0] if (y0s is None) else seat_x(h, y0, w, D, prof, a, th[0], th[1], spr)
            gr = Grip(np.array([x, y0, 0]) + w * D, D, prof)
            u = palm_dir(h, h.rotf(a, th[0], th[1], spr), gr)
            for fn in FINGERS:
                ang[fn], spr[fn] = fit_finger(h, fn, dict(ang, thumb=th[2:]), spr, gr, u,
                                              tuple(ang[fn]) + (spr[fn],), th[0], th[1])
            J = h.joints(h.rotf(dict(ang, thumb=th[2:]), th[0], th[1], spr))
            ti, tm = [float((J[f"{fn}_03_r"] - gr.A) @ D) * 1000 for fn in ("index", "middle")]
            th = fit_thumb(h, gr, dict(ang), th, (tm - 5, ti + 5), spr=spr)
        a = dict(ang, thumb=th[2:])
        m = measure(h, h.rotf(a, th[0], th[1], spr), gr); bad = verdict(m, a)
        # Into the hilt or the palm through it disqualifies a seat; then the fewest fails, then the least hang.
        score = (100 if m["deepest"] < -IN_MAX or (m["palm"] or 0) < -IN_MAX else 0) + len(bad) \
            + sum(max(0.0, m[fn]["hang"] or 0) for fn in FINGERS) / 10
        print(f"  seat y0 {y0 * 1000:.0f}: A {np.round(gr.A * 1000, 1).tolist()} spreads {spr} fails {len(bad)}: "
              f"{'; '.join(bad) or 'none'}", flush=True)
        if best is None or score < best[0]:
            best = (score, dict(bends={k: tuple(v) for k, v in a.items()}, spreads=dict(spr), oppose=th[0],
                                thumb_roll=th[1]), gr.A)
    return best[1], best[2], prof


def write_wrap(piece, wrap):
    p = HERE / "keyed.py"; s = p.read_text(encoding="utf-8")
    b = wrap["bends"]
    body_ = (f'"{piece}": {{"bends": {{' + ", ".join(f'"{k}": ({", ".join(f"{v:.1f}" for v in b[k])})' for k in ALLF)
             + "}" + (", \"spreads\": {" + ", ".join(f'"{k}": {v:.1f}' for k, v in wrap["spreads"].items()) + "}"
                      if wrap.get("spreads") else "")
             + f',\n                  "oppose": {wrap["oppose"]:.2f}, "thumb_roll": {wrap["thumb_roll"]:.1f}}}')
    s2, n = re.subn(rf'"{piece}": \{{"bends": \{{.*?"thumb_roll": [-0-9.]+\}}', body_, s, count=1, flags=re.S)
    assert n == 1, "WRAP entry not found"
    p.write_text(s2, encoding="utf-8")


def write_seat(piece, A):
    s = SOCKETS.read_text(encoding="utf-8"); name = PIECES[piece]["at"]
    s2, n = re.subn(rf"({name}\s*=\s*new\()[^)]*\)", rf"\g<1>{A[0]:.4f}f, {A[1]:.4f}f, {A[2]:.4f}f)", s, count=1)
    assert n == 1
    SOCKETS.write_text(s2, encoding="utf-8")


# -------------------------------------------------------------------- table --
def table(piece, wrap=None, A=None, prof=None):
    """Every built clip holding the piece: at its contact frame(s) (else its first) and the rest frame, the fist on the
    hilt (the clip's own fingers, or `wrap` laid on its frames), the wrist, and whether its fingers are WRAP's."""
    P = PIECES[piece]; A0, D = read_seat(piece); D = D / np.linalg.norm(D)
    prof = prof or hilt_profile(piece, A0, D)
    gr = Grip(A0 if A is None else A, D, prof)
    built, bopp, broll, bspr = wrap_args(keyed.WRAP[piece])
    rows, fails = [], 0
    for path in sorted(CLIPS.glob("*.json")):
        d = json.load(open(path)); meta = d.get("meta", {})
        if (meta.get("weapon") or "").split("+")[0] != piece:
            continue
        _, rot, pos = load(path); fps = d.get("fps", 30); n = len(rot)
        c = meta.get("contact")
        cs = c if isinstance(c, list) else ([c] if c is not None else [])
        frames = sorted({min(n - 1, k) for t in cs for k in (int(np.floor(t * fps)), int(np.ceil(t * fps)))}) or [0]
        if path.stem == P["rest"][0]:
            frames = [P["rest"][1]]
        for f in frames:
            h = Hand(rot[f], pos[f], P["outfit"])
            off = finger_off(rot[f], h, built, bopp, broll, bspr)
            if wrap is None:
                rf = rot[f]
            else:
                a, o, r, sp = wrap_args(wrap); rf = h.rotf(a, o, r, sp)
            m = measure(h, rf, gr); bad = verdict(m) + ([f"fingers off WRAP {off:.0f} deg"] if off > OFF_MAX else [])
            fails += bool(bad)
            rows.append((path.stem, f, m, wrist(rot, pos, f), off, bad))
    print(f"{'clip':16s} {'fr':>3s} " + " ".join(f"{fn[:4]:>16s}" for fn in FINGERS) + "   in  palm  adj(im,mr,rp)  wrist(flex,dev)  off")
    print(f"{'':16s} {'':3s} " + " ".join(f"{'pad02/03 hang':>16s}" for _ in FINGERS))
    for name, f, m, wr, off, bad in rows:
        cells = " ".join(f"{str(m[fn]['pads'][1]):>5s}/{str(m[fn]['pads'][2]):<5s}{str(m[fn]['hang']):>5s}" for fn in FINGERS)
        print(f"{name:16s} {f:3d} {cells} {m['deepest']:5.1f} {str(m['palm']):>5s} {','.join(str(v) for v in m['adj'].values()):>13s}  {str(wr):>15s} {off:4.0f}"
              + ("  PASS" if not bad else "  FAIL: " + "; ".join(bad[:4]) + (" ..." if len(bad) > 4 else "")))
    print(f"{len(rows)} frames, {fails} failing")
    return fails


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("piece", choices=sorted(PIECES))
    ap.add_argument("--fit", action="store_true")
    ap.add_argument("--seat", default=None, help="comma-separated y0 (mm) to try for the grip's line")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--hand", default=None, help="a corrected hand to try (JSON for set_hand, e.g. {\"knuckles\": 20}); "
                    "never written")
    a = ap.parse_args(argv)
    if a.hand:
        assert not a.write, "--hand models a hand that isn't built: nothing is written for it"
        set_hand(json.loads(a.hand))
    if not a.fit:
        return table(a.piece)
    y0s = [float(v) for v in a.seat.split(",")] if a.seat else None
    wrap, A, prof = fit(a.piece, y0s)
    A0, _ = read_seat(a.piece)
    print(f'WRAP["{a.piece}"] = {json.dumps(wrap)}')
    moved = np.linalg.norm(A - A0) > 5e-4   # 0.5 mm: the seat search's own tolerance below that
    print(f"seat {PIECES[a.piece]['at']} = {np.round(A, 4).tolist()}" + (" (moved)" if moved else " (kept)"))
    fails = table(a.piece, wrap, A, prof)
    if a.write:
        write_wrap(a.piece, wrap)
        if moved:
            write_seat(a.piece, A)
        print("written: rebuild the clips (tools/anim/build.py sword idle run sprint stop show bull)" + (", re-dump arms_local" if moved else ""))
    return fails


if __name__ == "__main__":
    main(sys.argv[1:])
