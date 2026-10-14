"""Her right fist on a held piece's grip: measured in the built clips, and re-derived (keyed.py WRAP) from her hand.
    python tools/anim/fistfit.py sword                  the table: every clip that holds it, at each contact frame
                                                        (and its rest frame), against the pass below
    python tools/anim/fistfit.py sword --fit            re-fit WRAP["sword"] on the hand as it is now, then the table
                                                        for the fitted fist (laid on each clip's frames)
    python tools/anim/fistfit.py sword --fit --seat 127,137,147   also try the grip's line moved along her fingers (mm,
                                                        hand_r y of the line at the seat's height); the best seat wins
    python tools/anim/fistfit.py sword --fit --write    write the fitted WRAP["sword"] into keyed.py (and the seat into
                                                        WeaponSockets.cs if it moved: then rebuild the clips and re-dump
                                                        arms_local, tools_scenes/arms_dump.gd)
Everything is read, nothing typed in: her finger bones from the skeleton dump (data/heroine_skeleton.json), the pads'
offsets from her skinned body (skin.Body.heroine, the piece's outfit), the hilt's profile from data/arms_local.json
(the piece as the game seats it, hand_r space), the seat from godot/logic/Play/WeaponSockets.cs. So when her hand is
rebuilt (outfits) this re-derives the fist in one command.

The pass (PASS below), per finger at every measured frame: the two outer pads (02, 03 bones) on the leather (gap
-0.5..1.5 mm), nothing of the hand more than 0.5 mm into the hilt, the finger's end not past the grip's far side in
the hand's frame (HANG: its tip joint no further from the palm than the grip's far surface: a fist, not fingers hooked
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
HANG_MAX = 0.0        # mm: the tip joint past the grip's far surface (along the palm's normal)
ADJ_MAX = 2.0         # mm: adjacent fingers' outer bones apart
CAP3 = 62.0           # deg: the last joint's bend
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


def body(outfit):
    if outfit not in _bodies:
        b = skin.Body.heroine(outfit=outfit, jiggle=False)
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

    def rotf(self, ang, oppose=0.0, roll=0.0):
        """Finger bends {finger: (a1, a2, a3)} laid as keyed.Rig.solve lays a WRAP (rest, the thumb's oppose and roll,
        each bend about its joint's axis); fingers not given keep the frame's own."""
        r = self.rot_f.copy()
        for name, angles in ang.items():
            for k, a in enumerate(angles):
                j = I[f"{name}_0{k + 1}_r"]
                q = sk.rest_rot[j]
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
    return ang, w.get("oppose", 0.0), w.get("thumb_roll", 0.0)


def palm_dir(h, rf, gr):
    """The way from the grip's line to the palm (square to the line), hand_r space."""
    Xp = h.pose(rf, h.palm); g, _ = gr.gap(Xp)
    P = Xp[(g < 8) & ~np.isnan(g)].mean(0)
    v = P - gr.A; u = v - (v @ gr.D) * gr.D
    return u / np.linalg.norm(u)


def measure(h, rf, gr):
    """Per finger: pads (01, 02, 03 min gap mm), deepest into the hilt, the tip's hang past the far side; the palm's
    gap, adjacent fingers' distance."""
    X = h.pose(rf); g, t = gr.gap(X); J = h.joints(rf); u = palm_dir(h, rf, gr)
    out = {}
    for fn in ALLF:
        sub = h.fing[fn]; B = h.bone[sub]; gs = g[sub]; ok = ~np.isnan(gs)
        pads = [round(float(gs[(B == f"{fn}_0{k}_r") & ok].min()), 1) if ((B == f"{fn}_0{k}_r") & ok).any() else None for k in (1, 2, 3)]
        v = J[f"{fn}_04_leaf_r"] - gr.A; R = gr.R(v @ gr.D)
        out[fn] = dict(pads=pads, deepest=round(float(gs[ok].min()), 1) if ok.any() else None,
                       hang=round(float((-(v @ u) - R) * 1000), 1) if not np.isnan(R) else None)
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


def finger_off(rot_f, h, ang, opp, roll):
    ref = h.rotf(ang, opp, roll)
    return max(float(np.degrees(2 * np.arccos(min(1.0, abs(float(np.dot(rot_f[j], ref[j]))))))) for j in CHAIN)


# ------------------------------------------------------------------ fitting --
def seat_x(h, y0, w, D, prof, ang, opp, roll):
    """The line's depth (hand x) at which the palm and the thumb's base sit 0.3 mm off the hilt."""
    sub = np.concatenate([h.palm, h.fing["thumb"][h.bone[h.fing["thumb"]] == "thumb_01_r"]])
    X = h.pose(h.rotf(ang, opp, roll), sub)
    lo, hi = -0.080, 0.0
    for _ in range(30):
        x = (lo + hi) / 2
        g, _ = Grip(np.array([x, y0, 0]) + w * D, D, prof).gap(X)
        if np.nanmin(g) > 0.3: lo = x
        else: hi = x
    return lo


def fit_finger(h, fn, base, gr, u, x0):
    sub = h.fing[fn]; B = h.bone[sub]
    lims = ((-10.0 if fn == "index" else 0.0, 95.0), (0.0, 105.0), (0.0, CAP3 - 2))
    def cost(th):
        a = dict(base); a[fn] = list(th)
        rf = h.rotf(a)
        X = h.pose(rf, sub); g, _ = gr.gap(X); J = h.joints(rf)
        c = 0.0
        for k, wt in (("01", 1.0 if fn in ("ring", "pinky") else 0.5), ("02", 1.0), ("03", 1.0)):
            m = (B == f"{fn}_{k}_r") & ~np.isnan(g)
            if not m.any(): c += 400; continue
            d = g[m].min() - 0.6
            c += wt * (d * d if d > 0 else 25 * d * d)
        tip = (np.linalg.norm(X - J[f"{fn}_04_leaf_r"], axis=1) < 0.012) & ~np.isnan(g)
        d = (g[tip].min() if tip.any() else 20.0) - 1.0
        if d > 0: c += d * d
        v = J[f"{fn}_04_leaf_r"] - gr.A; R = gr.R(v @ gr.D)
        hang = (-(v @ u) - (0.016 if np.isnan(R) else R)) * 1000
        if hang > HANG_MAX - 2: c += 0.5 * (hang - HANG_MAX + 2) ** 2
        gg = g[~np.isnan(g)]
        c += 50 * float((np.clip(-0.3 - gg, 0, None) ** 2).sum())
        gp, _ = gr.gap(h.pose(rf, h.palm)); gp = gp[~np.isnan(gp)]
        c += 50 * float((np.clip(-0.3 - gp, 0, None) ** 2).sum())
        for v_, (lo, hi) in zip(th, lims):
            if v_ < lo: c += (lo - v_) ** 2
            if v_ > hi: c += (v_ - hi) ** 2
        return c
    best = None
    for s0 in (x0, (40, 70, 50), (60, 60, 40), (30, 90, 55), (70, 80, 30)):
        s = minimize(cost, np.array(s0, float), method="Nelder-Mead", options={"xatol": 0.2, "fatol": 0.01, "maxiter": 600})
        if best is None or s.fun < best.fun: best = s
    return [round(float(v), 1) for v in best.x]


def fit_thumb(h, gr, ang, x0, span, tgt=0.4, d_lo=1.0, d_hi=3.0):
    """Oppose, roll and three bends: its outer pads on the grip, none of it inside, its last bone over the forefinger's
    or middle finger's outer bones (d_lo..d_hi mm off them), its tip within `span` (mm along the line)."""
    sub_t = h.fing["thumb"]; sub_i = np.concatenate([h.fing["index"], h.fing["middle"]])
    tb = h.bone[sub_t]; ib = h.bone[sub_i]
    over = np.isin(ib, ["index_02_r", "index_03_r", "middle_02_r", "middle_03_r"])
    def cost(x):
        opp, roll, a1, a2, a3 = x
        a = dict(ang); a["thumb"] = [a1, a2, a3]
        rf = h.rotf(a, opp, roll)
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


def fit(piece, y0s=None):
    """Re-derive the WRAP (and, given y0s, the seat) on the rest frame. Returns (wrap, A, report)."""
    P = PIECES[piece]; A0, D = read_seat(piece); D = D / np.linalg.norm(D)
    prof = hilt_profile(piece, A0, D)
    _, rot, pos = load(CLIPS / f"{P['rest'][0]}.json"); h = Hand(rot[P["rest"][1]], pos[P["rest"][1]], P["outfit"])
    # A = (x, y0, 0) + w D: w (where along the hilt the hand is) kept; y0 the line's place along her fingers, x its depth.
    w = float(A0[2] / D[2]); base0 = A0 - w * D
    old, opp0, roll0 = wrap_args(keyed.WRAP[piece])
    best = None
    for y0 in (y0s or [base0[1] * 1000]):
        y0 /= 1000
        ang = {fn: list(old[fn]) for fn in FINGERS}; th = [opp0, roll0] + list(old["thumb"])
        x0 = {fn: tuple(old[fn]) for fn in FINGERS}
        for it in range(3):
            x = base0[0] if (y0s is None) else seat_x(h, y0, w, D, prof, {"thumb": th[2:]}, th[0], th[1])
            gr = Grip(np.array([x, y0, 0]) + w * D, D, prof)
            u = palm_dir(h, h.rotf(dict(ang, thumb=th[2:]), th[0], th[1]), gr)
            for fn in FINGERS:
                ang[fn] = fit_finger(h, fn, dict(ang, thumb=th[2:]), gr, u, ang[fn] if it else x0[fn])
            J = h.joints(h.rotf(dict(ang, thumb=th[2:]), th[0], th[1]))
            ti, tm = [float((J[f"{fn}_03_r"] - gr.A) @ D) * 1000 for fn in ("index", "middle")]
            th = fit_thumb(h, gr, dict(ang), th, (tm - 5, ti + 5))
        a = dict(ang, thumb=th[2:])
        m = measure(h, h.rotf(a, th[0], th[1]), gr); bad = verdict(m, a)
        # Into the hilt or the palm through it disqualifies a seat; then the fewest fails, then the least hang.
        score = (100 if m["deepest"] < -IN_MAX or (m["palm"] or 0) < -IN_MAX else 0) + len(bad)             + sum(max(0.0, m[fn]["hang"] or 0) for fn in FINGERS) / 10
        print(f"  seat y0 {y0 * 1000:.0f}: A {np.round(gr.A * 1000, 1).tolist()} fails {len(bad)}: {'; '.join(bad) or 'none'}")
        if best is None or score < best[0]:
            best = (score, dict(bends={k: tuple(v) for k, v in a.items()}, oppose=th[0], thumb_roll=th[1]), gr.A)
    return best[1], best[2], prof


def write_wrap(piece, wrap):
    p = HERE / "keyed.py"; s = p.read_text(encoding="utf-8")
    b = wrap["bends"]
    body_ = (f'"{piece}": {{"bends": {{' + ", ".join(f'"{k}": ({", ".join(f"{v:.1f}" for v in b[k])})' for k in ALLF)
             + f'}},\n                  "oppose": {wrap["oppose"]:.2f}, "thumb_roll": {wrap["thumb_roll"]:.1f}}}')
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
    built, bopp, broll = wrap_args(keyed.WRAP[piece])
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
            off = finger_off(rot[f], h, built, bopp, broll)
            if wrap is None:
                rf = rot[f]
            else:
                a, o, r = wrap_args(wrap); rf = h.rotf(a, o, r)
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
    a = ap.parse_args(argv)
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
