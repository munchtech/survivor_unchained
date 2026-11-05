#!/usr/bin/env python
"""P1 pass 2: the loop plan (tools/body/loopplan.json) BUILT into one joined, closed quad body (open only at the neck,
where it meets her approved head's 94-point ring one-to-one). topo.py holds the reference, the trunk canvas and rays;
this file holds the patterns and the assembly. Density is by edge length (the plan's spacings), never fixed counts:
every count is a length over a spacing, rounded to the parity the junctions need.

    python tools/body/topo_build.py [--tiers close,play] [--out tools/body/out/topo] [--check-determinism]

Pieces (left half, x >= 0, mirrored at the end; midline vertices shared):
  trunk()      rows (half rings, front middle -> back middle) in three column bands F | S or T | B; the shoulder hole
               (S above row i_s0 and T below row i_s1 cut out), the breast hole in F, the collar transitions in F and
               B (kites: one quad over 3 vertices of the longer row and 1 of the shorter, a 3-pole and a 5-pole)
  shoulder()   the hole's rim -> k concentric loops -> the arm root ring (a plane section through the armpit's
               saddle); the hole's 4 corners are the only shoulder poles
  breast()     the breast hole's rim -> k shrinking loops -> a w x h grid cap (4 5-poles at the rim, 4 3-poles at the cap)
  crotch()     the midline strip under the perineum (b quads a side) between the two leg roots
  tube()       a limb: rings at stations along our bones, twist-free angles, reduction bands (kites on the hidden
               side, mid-segment, never in a bend zone), the elbow / knee loops on the bend's bisector
  template()   the hand and foot (tools/body/base/*.obj, (b) converted from MakeHuman) at their base level
Saved per vertex: region id, part id, ring (row) and column index, constraint flag: the entry points for UVs,
landmarks, weights and the hm08 correspondence (the next pass).
"""
import argparse
import hashlib
import json
import os
import sys
import time

import numpy as np
import scipy.sparse as sp
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import topo as T  # noqa: E402
import topo_gates as G  # noqa: E402
from topo import ARM, FOOT, HAND, LEG, TRUNK, U, fill_nan, frame, rot, smooth01  # noqa: E402

REPO = T.REPO
PARTS = ["neck", "trunk", "breast", "shoulder", "arm", "elbow", "forearm", "hand", "crotch", "thigh", "knee", "shin",
         "foot"]
FREE, MID, FIXED, PLANE, TEMPLATE = 0, 1, 2, 3, 4
REG = {"neck_decolletage": 4, "torso_front": 5, "torso_back": 6, "upper_arms": 7, "forearms": 8, "hands": 9,
       "pelvis_glutes": 10, "thighs": 11, "lower_legs": 12, "feet": 13}


# --------------------------------------------------------------------------------------------- the quad mesh --
class QM:
    """The mesh under construction: vertices with (part, ring, column, flag, region, reference labels), quads."""

    def __init__(self):
        self.V, self.part, self.ring, self.col, self.flag, self.aux, self.reg, self.labs = ([] for _ in range(8))
        self.designed = []
        self.Q, self.qreg, self.qpart = [], [], []
        self.planes = []

    def add(self, X, part, ring=-1, col0=0, flag=FREE, reg=5, labs=(TRUNK,), aux=-1):
        X = np.atleast_2d(np.asarray(X, float))
        n, i0 = len(X), len(self.V)
        self.V.extend(list(X))
        self.part += [PARTS.index(part)] * n
        self.ring += [int(ring)] * n
        self.col += list(range(col0, col0 + n))
        self.flag += [flag] * n
        self.aux += [aux] * n
        self.reg += [reg] * n
        self.labs += [tuple(labs)] * n
        self.designed += [0] * n
        return np.arange(i0, i0 + n)

    def plane(self, p, n):
        self.planes.append((np.asarray(p, float), U(n)))
        return len(self.planes) - 1

    def quad(self, a, b, c, d, reg, part):
        self.Q.append((int(a), int(b), int(c), int(d)))
        self.qreg.append(reg)
        self.qpart.append(PARTS.index(part))

    def strip(self, A, B, reg, part, closed=False, kites=()):
        """Quads between rows A and B (vertex ids, same direction). If one row has 2r more edges, `kites` gives the r
        start indices (in the longer row) of the kite quads: 3 vertices of the long row, 1 of the short."""
        A, B = list(A), list(B)
        eA, eB = (len(A), len(B)) if closed else (len(A) - 1, len(B) - 1)
        if eA == eB:
            for k in range(eA):
                self.quad(A[k], A[(k + 1) % len(A)], B[(k + 1) % len(B)], B[k], reg, part)
            return
        longA = eA > eB
        L, S = (A, B) if longA else (B, A)
        eL, eS = max(eA, eB), min(eA, eB)
        ks = sorted(int(k) % eL for k in kites)
        assert eL - eS == 2 * len(ks), (eL, eS, len(ks))
        assert all(b - a >= 2 for a, b in zip(ks, ks[1:])), ks
        i = j = 0
        kset = set(ks)
        nL, nS = len(L), len(S)
        while i < eL:
            if i in kset:
                l0, l1, l2, s0 = L[i % nL], L[(i + 1) % nL], L[(i + 2) % nL], S[j % nS]
                if longA:
                    self.quad(l0, l1, l2, s0, reg, part)
                else:
                    self.quad(s0, l2, l1, l0, reg, part)
                i += 2
            else:
                l0, l1, s0, s1 = L[i % nL], L[(i + 1) % nL], S[j % nS], S[(j + 1) % nS]
                if longA:
                    self.quad(l0, l1, s1, s0, reg, part)
                else:
                    self.quad(s0, s1, l1, l0, reg, part)
                i += 1
                j += 1
        assert j == eS, (j, eS)

    def arrays(self):
        return np.array(self.V, float), np.array(self.Q, np.int64)


def spread(n_edges, r, lo=2, hi=None, offset=0.5):
    """r kite starts spread evenly over edges [lo, hi - 2] of an open row (each kite covers 2 edges)."""
    hi = n_edges - lo if hi is None else hi
    if r <= 0:
        return []
    span = hi - lo - 2
    ks = [int(round(lo + span * (q + offset) / r)) for q in range(r)]
    for q in range(1, r):
        ks[q] = max(ks[q], ks[q - 1] + 2)
    return ks


def to_parity(n, like):
    """n rounded, then moved up one if its parity differs from `like`'s."""
    n = int(round(n))
    return n if (n - like) % 2 == 0 else n + 1


# ---------------------------------------------------------------------------------------------- canvas helpers --
def mapk(cv, th, t, ks):
    O, D = cv.rays(th, t)
    sh = O.shape
    return cv.ref.cast(ks, O.reshape(-1, 3), D.reshape(-1, 3)).reshape(sh)


def along_k(cv, ks, th_a, th_b, t_of, g, ns=200):
    """Points on the canvas curve t = t_of(theta), theta_a -> theta_b, at arc-length fractions g (0..1)."""
    th = np.linspace(th_a, th_b, ns)
    X = fill_nan(mapk(cv, th, t_of(th), ks))
    s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(X, axis=0), axis=1))])
    gg = np.asarray(g, float) * s[-1]
    return np.stack([np.interp(gg, s, X[:, k]) for k in range(3)], 1), float(s[-1])


def arc_fracs(X):
    s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(X, axis=0), axis=1))])
    return s / max(s[-1], 1e-12)


def graded(L, s0, s1):
    """Fractions 0..1 along a length L whose step grows linearly from s0 (at 0) to s1 (at L)."""
    n = max(1, int(round(2 * L / (s0 + s1))))
    w = np.linspace(s0, s1, n)
    c = np.concatenate([[0], np.cumsum(w)])
    return c / c[-1]


def t_on_plane(cv, th, p, n, t_lo=0.80, t_hi=1.25, ns=226):
    """Canvas t where each meridian theta crosses the plane (p, n) going up (the leg crease row R0)."""
    ts = np.linspace(t_lo, t_hi, ns)
    TH_, TS = np.meshgrid(th, ts, indexing="ij")
    X = mapk(cv, TH_, TS, [TRUNK, LEG])
    s = (X - p) @ n
    out = np.full(len(th), np.nan)
    for i in range(len(th)):
        si = s[i]
        ok = np.isfinite(si)
        idx = np.where(ok[:-1] & ok[1:] & (si[:-1] < 0) & (si[1:] >= 0))[0]
        if len(idx):
            k = idx[-1]
            out[i] = ts[k] + (ts[k + 1] - ts[k]) * (-si[k]) / (si[k + 1] - si[k])
    bad = ~np.isfinite(out)
    if bad.any():
        out[bad] = np.interp(np.where(bad)[0], np.where(~bad)[0], out[~bad])
    return out


# ------------------------------------------------------------------------------------------- the shoulder rim --
def shoulder_rim(ref, cv, L, plan, tp, m=360):
    """(a, pass 3) The trunk's shoulder hole: the arm root ring offset along the trunk's surface by the gap G (each
    root point marched G away from the arm, perpendicular to the ring), so the rim-to-root gap is even all round
    (the rectangle of pass 2 ran 19-87 mm). Returns the dense rim and root (same index = same root angle) in the
    lattice's order (canvas counter-clockwise: bottom front -> back, up the back, top back -> front, down the
    front), rolled so index 0 is the front-bottom corner, and the four corners (the diagonal extremes)."""
    c, n, _ = arm_root_plane(L, plan)
    e1 = ring_frame(c, n, np.array([0, 1.0, 0]))[0]
    X = dense_ring(ref, [TRUNK, ARM], c, n, e1, m)[2][:-1]
    G = tp["shoulder_gap"]
    S = ref._sf.get((TRUNK,))
    if S is None:
        ref.project([TRUNK], X[:1])
        S = ref._sf[(TRUNK,)]
    S = S[0]
    tang = np.roll(X, -1, 0) - np.roll(X, 1, 0)
    _, N0, _, _ = S.closest(X, k=16)
    w = U(np.cross(N0, tang))
    w = np.where(((w @ n) > 0)[:, None], -w, w)
    Y = X.copy()
    k = max(1, int(round(G / 0.003)))
    for _ in range(k):
        Y = Y + (G / k) * w
        Y, Nn, _, _ = S.closest(Y, k=16)
        w = U(w - (w * Nn).sum(1, keepdims=True) * Nn)
    th, t = cv.inv(Y)
    area = np.sum(th * np.roll(t, -1) - np.roll(th, -1) * t)
    if area < 0:
        X, Y, th, t = X[::-1], Y[::-1], th[::-1], t[::-1]
    uu = (th - th.mean()) / np.ptp(th)
    vv = (t - t.mean()) / np.ptp(t)
    cn = {"FB": int(np.argmax(-uu - vv)), "BB": int(np.argmax(uu - vv)), "BT": int(np.argmax(uu + vv)),
          "FT": int(np.argmax(-uu + vv))}
    r0 = cn["FB"]
    X, Y, th, t = (np.roll(a, -r0, 0) for a in (X, Y, th, t))
    cn = {q: (i - r0) % m for q, i in cn.items()}
    assert 0 == cn["FB"] < cn["BB"] < cn["BT"] < cn["FT"] < m, cn
    Yc = np.vstack([Y, Y[:1]])
    sc = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(Yc, axis=0), axis=1))])
    arcs = {"bottom": (cn["FB"], cn["BB"]), "back": (cn["BB"], cn["BT"]), "top": (cn["BT"], cn["FT"]),
            "front": (cn["FT"], m)}
    gap = np.linalg.norm(Y - X, axis=1)
    return {"X": X, "Y": Y, "th": th, "t": t, "s": sc, "corners": cn, "arcs": arcs, "m": m,
            "len": {a: float(sc[b] - sc[a_]) for a, (a_, b) in arcs.items()},
            "gap_mm": [round(float(gap.min()) * 1000, 1), round(float(np.median(gap)) * 1000, 1),
                       round(float(gap.max()) * 1000, 1)]}


def rim_arc(SR, name, n):
    """n + 1 points at even arc length along one of the rim's four arcs, with their dense index (fractional)."""
    a, b = SR["arcs"][name]
    m, sc = SR["m"], SR["s"]
    g = np.linspace(sc[a], sc[b], n + 1)
    idx = np.interp(g, sc, np.arange(m + 1))
    Yc = np.vstack([SR["Y"], SR["Y"][:1]])
    P = np.stack([np.interp(idx, np.arange(m + 1), Yc[:, k]) for k in range(3)], 1)
    return P, idx


def arc_profile(SR, name):
    """The arc's canvas t as a function of theta (sorted), for the rows that run along it."""
    a, b = SR["arcs"][name]
    th = np.concatenate([SR["th"], SR["th"][:1]])[a:b + 1]
    t = np.concatenate([SR["t"], SR["t"][:1]])[a:b + 1]
    o = np.argsort(th)
    return th[o], t[o]


# ------------------------------------------------------------------------------------------------- the trunk --
def trunk_plan(ref, cv, L, plan, tp, SR):
    """Every trunk count from a length (a: the spacings), rounded to what the junctions need:
    the collar kites in F and B need F_L + n_t + B_L odd (the head's half ring has 47 edges); the arm root
    (n_b + n_t + 2 n_f) even; so K_low = F_L + n_b + B_L is odd and the crotch strip b odd. The hole is the
    shoulder rim (shoulder_rim): its corners FB, BB, BT, FT (theta, t) and its four arcs set n_b, n_t, n_f."""
    s, sr = tp["spacing"], tp["spacing"] * tp.get("row_scale", 1.0)
    cn, th, t = SR["corners"], SR["th"], SR["t"]
    FB, BB, BT, FT = (float(th[cn[q]]) for q in ("FB", "BB", "BT", "FT"))
    tFB, tBB, tBT, tFT = (float(t[cn[q]]) for q in ("FB", "BB", "BT", "FT"))

    def blen(a, b, tt):
        return along_k(cv, [TRUNK], a, b, lambda x: np.full_like(np.asarray(x, float), tt), [0, 1])[1]

    n_b = max(2, int(round(SR["len"]["bottom"] / s)))
    n_t = max(2, int(round(SR["len"]["top"] / s)))
    n_t += (n_t - n_b) % 2
    n_f = max(2, int(round(0.5 * (SR["len"]["front"] + SR["len"]["back"]) / sr)))
    F_L = int(round(max([blen(0, FB, x) for x in [1.08, 1.12, 1.2, 1.3] + list(tp.get("F_L_heights", []))] +
                        [blen(0, float(a), float(b)) for a, b in zip(th[cn["FT"]::12], t[cn["FT"]::12])]) / s))
    B_L = int(round(max([blen(BB, np.pi, x) for x in (1.08, 1.12, 1.2, 1.3, 1.42)] +
                        [blen(float(a), np.pi, float(b)) for a, b in zip(th[cn["BB"]:cn["BT"]:12],
                                                                         t[cn["BB"]:cn["BT"]:12])]) / s))
    if (F_L + n_t + B_L) % 2 == 0:
        B_L += 1
    tot = F_L + n_t + B_L
    F_N = to_parity(47 * F_L / tot, F_L)
    T_N = to_parity(47 * n_t / tot, n_t)
    B_N = 47 - F_N - T_N
    assert (B_N - B_L) % 2 == 0 and min(F_N, T_N, B_N) >= 4, (F_N, T_N, B_N)
    return {"s": s, "sr": sr, "FB": FB, "BB": BB, "FT": FT, "BT": BT, "t_FB": tFB, "t_BB": tBB, "t_BT": tBT,
            "t_FT": tFT, "t_s0": min(tFB, tBB), "t_s1": max(tFT, tBT), "n_b": n_b, "n_t": n_t, "n_f": n_f,
            "F_L": F_L, "B_L": B_L, "F_N": F_N, "T_N": T_N, "B_N": B_N, "K_low": F_L + n_b + B_L,
            "N_arm_rim": n_b + n_t + 2 * n_f, "shoulder_gap_mm": SR["gap_mm"]}


def trunk(M, ref, cv, L, plan, tp, C, SR):
    """The trunk's left half: rows from R0 (the leg crease) to the head's ring.

        head ring (47 edges: F_N | n_t | B_N, the head's own points)
        |  F_N  |        T: n_t          |  B_N  |   rows graded to the neck's spacing
        |  ...collar kites (F: F_L - F_N, B: B_L - B_N)... (at collar_y front / back)
        |       FT------- top n_t -------BT      |   i_s1
        |  F_L  |   SHOULDER HOLE (rim:   |  B_L  |   zone A: n_f rows; F ends on the hole's front side FB->FT,
        |  [breast |  n_b+n_t+2n_f)       |       |   B starts on its back side BB->BT
        |   hole]  FB------ bottom n_b ---BB      |   i_s0 (just under the armpit's saddle)
        |  F_L  |        S: n_b          |  B_L  |
        R0: the leg crease plane section (K_low = F_L + n_b + B_L edges): front middle (pubis) -> back middle (cleft)
    FB, BB, FT, BT are the shoulder's four 5-poles. Kites spread along their row, never at a band's end."""
    sr = C["sr"]
    tr, bp = plan["trunk"], plan["breast"]
    TH = np.linspace(0, np.pi, 721)
    t_R0 = t_on_plane(cv, TH, L["leg"]["p"], L["leg"]["n"])
    ring = ref.ring[:48]
    thN, tN = cv.inv(ring)
    t_N = np.interp(TH, thN, tN)
    FB, BB, FT, BT = C["FB"], C["BB"], C["FT"], C["BT"]
    tFB, tBB, tBT, tFT = C["t_FB"], C["t_BB"], C["t_BT"], C["t_FT"]
    n_f = C["n_f"]
    P_bot, _ = rim_arc(SR, "bottom", C["n_b"])                    # FB -> BB
    P_back, _ = rim_arc(SR, "back", n_f)                          # BB -> BT  (row k from the bottom)
    P_top, _ = rim_arc(SR, "top", C["n_t"])                       # BT -> FT
    P_front, _ = rim_arc(SR, "front", n_f)                        # FT -> FB
    P_front = P_front[::-1]                                       # row k from the bottom
    thF, tF = cv.inv(P_front)
    thB, tB = cv.inv(P_back)
    tb_th, tb_t = arc_profile(SR, "bottom")
    tt_th, tt_t = arc_profile(SR, "top")

    def prof(kind):
        """Row i_s0 (the rim's bottom arc between FB and BB) or i_s1 (its top arc between FT and BT)."""
        if kind == "s0":
            return np.where(TH <= FB, tFB, np.where(TH >= BB, tBB, np.interp(TH, tb_th, tb_t)))
        return np.where(TH <= FT, tFT, np.where(TH >= BT, tBT, np.interp(TH, tt_th, tt_t)))

    def prof_A(k):
        """Zone A row k: the front midline to the rim's front arc point k, the back arc point k to the back middle."""
        f = k / n_f
        tm, tb_ = (1 - f) * tFB + f * tFT, (1 - f) * tBB + f * tBT
        return np.interp(TH, [0.0, thF[k], thB[k], np.pi], [tm, tF[k], tB[k], tb_])

    def full(v):
        return np.full_like(TH, v) if np.isscalar(v) else np.asarray(v, float)

    def mer_len(ta, tb, ths=(15, 45, 90, 135, 165), avg=False):
        out = []
        for d in ths:
            a = float(np.interp(np.radians(d), TH, full(ta)))
            b = float(np.interp(np.radians(d), TH, full(tb)))
            X = fill_nan(mapk(cv, np.full(25, np.radians(d)), np.linspace(a, b, 25), [TRUNK, LEG]))
            out.append(np.linalg.norm(np.diff(X, axis=0), axis=1).sum())
        return float(np.mean(out)) if avg else max(out)

    rows = []
    p_s0, p_s1 = prof("s0"), prof("s1")
    n_g = max(1, int(round(mer_len(t_R0, tr["waist_y"]) / (sr * tp.get("glute_scale", 1.0)))))
    for r in range(n_g):
        rows.append({"t": (1 - r / n_g) * full(t_R0) + (r / n_g) * full(tr["waist_y"]), "zone": "low", "f": 0.0})
    # waist -> the rim's bottom arc: through the underbust at the front (the breast's fold), even at the side and
    # the back (the arc dips to the armpit there: anchoring the underbust would crowd the rows under it)
    n_a = max(1, int(round(mer_len(tr["waist_y"], tr["underbust_y"]) / sr)))
    n_c = max(1, int(round(mer_len(tr["underbust_y"], p_s0, ths=(15, 45)) / (sr * tp.get("bust_scale", 1.0)))))
    wf = 1 - smooth01((TH - np.radians(55)) / np.radians(25))
    for r in range(n_a + n_c):
        t_even = tr["waist_y"] + (p_s0 - tr["waist_y"]) * r / (n_a + n_c)
        t_fr = (tr["waist_y"] + (tr["underbust_y"] - tr["waist_y"]) * r / n_a if r <= n_a
                else tr["underbust_y"] + (p_s0 - tr["underbust_y"]) * (r - n_a) / n_c)
        rows.append({"t": wf * t_fr + (1 - wf) * t_even, "zone": "low", "f": 0.0})
    i_s0 = len(rows)
    for k in range(n_f + 1):
        rows.append({"t": p_s0 if k == 0 else (p_s1 if k == n_f else prof_A(k)), "zone": "A", "f": k / n_f, "k": k})
    i_s1 = len(rows) - 1
    g = graded(mer_len(p_s1, t_N, avg=True), C["s"], tp["neck_spacing"])
    for f in g[1:]:
        rows.append({"t": (1 - f) * p_s1 + f * t_N, "zone": "U", "f": float(f)})
    i_n = len(rows) - 1
    for r in rows:
        r["t_of"] = (lambda tt: (lambda th: np.interp(th, TH, tt)))(r["t"])
        r["y"] = {d: float(mapk(cv, np.radians(d), float(np.interp(np.radians(d), TH, r["t"])), [TRUNK, LEG])[1])
                  for d in (10, 170)}
    yfront = np.array([r["y"][10] for r in rows])
    yback = np.array([r["y"][170] for r in rows])
    fz = np.array([r["f"] if r["zone"] == "U" else -1.0 for r in rows])
    F_tr = B_tr = T_tr = int(np.argmax(fz >= tp["collar_f"]))         # the collar row: the neck's base all round
    if tp.get("collar_F_y"):                         # (a, pass 3b) the front's collar kites down on the upper chest
        F_tr = int(np.argmin(np.abs(yfront[:i_s1] - tp["collar_F_y"])))
    C["rows_y_front"] = [round(float(y), 3) for y in yfront]
    C["rows_y_back"] = [round(float(y), 3) for y in yback]
    C.update({"i_s0": i_s0, "i_s1": i_s1, "i_n": i_n, "F_tr": F_tr, "B_tr": B_tr, "T_tr": T_tr, "rows": len(rows)})

    for i, r in enumerate(rows):                       # the band edges (theta) and counts per row
        nF = C["F_L"] if i < F_tr else C["F_N"]
        nB = C["B_L"] if i < B_tr else C["B_N"]
        if r["zone"] == "low" or i == i_s0:
            r["bands"] = [("F", 0.0, FB, nF), ("S", FB, BB, C["n_b"]), ("B", BB, np.pi, nB)]
        elif r["zone"] == "A" and i < i_s1:
            r["bands"] = [("F", 0.0, float(thF[r["k"]]), nF), ("B", float(thB[r["k"]]), np.pi, nB)]
        else:                                          # i_s1 and zone U
            f = r["f"] if i > i_s1 else 0.0
            a = (1 - f) * FT + f * thN[C["F_N"]]
            b = (1 - f) * BT + f * thN[C["F_N"] + C["T_N"]]
            r["bands"] = [("F", 0.0, a, nF), ("T", a, b, C["n_t"] if i < T_tr else C["T_N"]), ("B", b, np.pi, nB)]

    # the breast window: rows by height at the apex's theta, columns by theta on its rows (b: the reference)
    ap = L["breast_apex"]
    th_ap = float(cv.inv(ap[None])[0][0])
    yap = np.array([float(mapk(cv, th_ap, float(np.interp(th_ap, TH, r["t"])), [TRUNK])[1]) for r in rows])
    yap = np.where(np.isfinite(yap) & (np.arange(len(rows)) < i_s1), yap, 9.0)
    i_b0 = int(np.argmin(np.abs(yap - bp["y"][0])))
    i_b1 = int(np.argmin(np.abs(yap - bp["y"][1])))
    assert i_b1 + 1 < F_tr, ("the breast window reaches the collar kites", i_b1, F_tr)
    th_cols = {}                                       # straight F columns over the window (blended under -> over)
    for i in (i_b0 - 1, i_b1 + 1):
        r = rows[i]
        nm, a, b, n = r["bands"][0]
        X, _ = along_k(cv, [TRUNK], a, b, r["t_of"], np.linspace(0, 1, n + 1))
        th_cols[i] = np.clip(cv.inv(X)[0], 0, np.pi)
        th_cols[i][0] = 0.0
    for i in range(i_b0, i_b1 + 1):
        f = (i - i_b0 + 1) / (i_b1 - i_b0 + 2)
        th_cols[i] = (1 - f) * th_cols[i_b0 - 1] + f * th_cols[i_b1 + 1]
    for i in (i_b0 - 1, i_b1 + 1):
        del th_cols[i]
    thm = 0.5 * (th_cols[i_b0] + th_cols[i_b1])
    j_b0 = int(np.argmin(np.abs(thm - np.radians(bp["theta"][0]))))
    j_b1 = int(np.argmin(np.abs(thm - np.radians(bp["theta"][1]))))
    C.update({"breast_rows": [i_b0, i_b1], "breast_cols": [j_b0, j_b1]})

    ringF = arc_fracs(ring[:C["F_N"] + 1])                      # sample the rows
    ringT = arc_fracs(ring[C["F_N"]:C["F_N"] + C["T_N"] + 1])
    ringB = arc_fracs(ring[C["F_N"] + C["T_N"]:])
    for i, r in enumerate(rows):
        ids = {}
        if i == i_n:
            F_N, n_t = C["F_N"], C["T_N"]
            ids["F"] = M.add(ring[:F_N + 1], "neck", i, 0, FIXED, 4)
            ids["T"] = np.concatenate([ids["F"][-1:], M.add(ring[F_N + 1:F_N + n_t + 1], "neck", i, F_N + 1, FIXED, 4)])
            ids["B"] = np.concatenate([ids["T"][-1:], M.add(ring[F_N + n_t + 1:], "neck", i, F_N + n_t + 1, FIXED, 4)])
            assert len(ids["B"]) == C["B_N"] + 1
            r["ids"] = ids
            continue
        col, prev = 0, None
        part = "neck" if (r["zone"] == "U" and r["f"] > 0.5) else "trunk"
        for nm, a, b, n in r["bands"]:
            gfr = np.linspace(0, 1, n + 1)
            if r["zone"] == "U":
                w = smooth01((r["f"] - 0.35) / 0.65)
                own = {"F": ringF, "T": ringT, "B": ringB}[nm]
                if len(own) == n + 1:
                    gfr = (1 - w) * gfr + w * own
            if nm == "F" and i in th_cols:
                tc = th_cols[i]
                X = fill_nan(mapk(cv, tc, r["t_of"](tc), [TRUNK]))
            elif nm == "S" and i == i_s0:
                X = P_bot.copy()
            elif nm == "T" and i == i_s1:
                X = P_top[::-1].copy()
            else:
                X, _ = along_k(cv, [TRUNK], a, b, r["t_of"], gfr)
            if i_s0 <= i <= i_s1 and nm == "F":
                X[-1] = P_front[r["k"]]
            if i_s0 <= i <= i_s1 and nm == "B":
                X[0] = P_back[r["k"]]
            if prev is not None and r["bands"][0][0] == "F" and len(r["bands"]) == 3:
                ids[nm] = np.concatenate([ids[prev][-1:], M.add(X[1:], part, i, col + 1)])
            else:
                ids[nm] = M.add(X, part, i, col)
            col += n
            prev = nm
        r["ids"] = ids
    for r in rows:
        for v in (r["ids"]["F"][0], r["ids"]["B"][-1]):
            if M.flag[v] != FIXED:
                M.flag[v] = MID

    def reg_of(nm, i, j, n):
        y = rows[i]["y"][10 if nm == "F" else 170]
        if nm == "T" or (nm == "F" and y > tr["decollete_y"]) or (nm == "B" and i >= B_tr):
            return REG["neck_decolletage"]
        if nm in ("F", "S") and y < tr["hip_y"][0] and (nm == "F" or j < n / 2):
            return REG["pelvis_glutes"]
        if nm in ("B", "S") and y < tr["hip_y"][1] and (nm == "B" or j >= n / 2):
            return REG["pelvis_glutes"]
        return REG["torso_front"] if nm == "F" or (nm == "S" and j < n / 2) else REG["torso_back"]

    kites_log = []
    for i in range(len(rows) - 1):
        A, B = rows[i]["ids"], rows[i + 1]["ids"]
        part = "neck" if rows[i]["zone"] == "U" and rows[i]["f"] > 0.5 else "trunk"
        for nm in ("F", "S", "T", "B"):
            if nm not in A or nm not in B:
                continue
            a, b = A[nm], B[nm]
            na, nb = len(a) - 1, len(b) - 1
            if na == nb:
                for j in range(na):
                    if nm == "F" and i_b0 <= i < i_b1 and j_b0 <= j < j_b1:
                        continue
                    M.quad(a[j], a[j + 1], b[j + 1], b[j], reg_of(nm, i, j, na), part)
            else:
                ks = spread(max(na, nb), abs(na - nb) // 2, lo=3)
                kites_log.append((nm, i, ks))
                M.strip(a, b, reg_of(nm, i, 0, na), part, kites=ks)
    C["kites"] = kites_log

    rim = list(rows[i_s0]["ids"]["S"])                 # the shoulder hole's rim: FB -> BB, up to BT, over to FT, down
    rim += [rows[i]["ids"]["B"][0] for i in range(i_s0 + 1, i_s1 + 1)]
    rim += list(rows[i_s1]["ids"]["T"][::-1][1:])
    rim += [rows[i]["ids"]["F"][-1] for i in range(i_s1 - 1, i_s0, -1)]
    corners = {"FB": rows[i_s0]["ids"]["S"][0], "BB": rows[i_s0]["ids"]["S"][-1], "BT": rows[i_s1]["ids"]["T"][-1],
               "FT": rows[i_s1]["ids"]["T"][0]}
    br = list(rows[i_b0]["ids"]["F"][j_b0:j_b1 + 1])   # the breast hole's rim
    br += [rows[i]["ids"]["F"][j_b1] for i in range(i_b0 + 1, i_b1 + 1)]
    br += list(rows[i_b1]["ids"]["F"][j_b0:j_b1][::-1])
    br += [rows[i]["ids"]["F"][j_b0] for i in range(i_b1 - 1, i_b0, -1)]
    R0 = np.concatenate([rows[0]["ids"]["F"], rows[0]["ids"]["S"][1:], rows[0]["ids"]["B"][1:]])
    for v in R0:
        M.labs[v] = (TRUNK, LEG)
    return {"rows": rows, "rim": np.array(rim), "corners": corners, "breast_rim": np.array(br),
            "breast_wh": (j_b1 - j_b0, i_b1 - i_b0), "R0": R0}


# ------------------------------------------------------------------------------------------------ ring helpers --
def ring_frame(c, n, e1):
    e1, e2 = frame(U(n), e1)
    return e1, e2


def ring_angles(X, c, n, e1):
    e1, e2 = ring_frame(c, n, e1)
    r = np.asarray(X) - c
    return np.unwrap(np.arctan2(r @ e2, r @ e1))


def dense_ring(ref, ks, c, n, e1, m=720):
    ph = np.linspace(0, 2 * np.pi, m + 1)
    X = T.ring_by_rays(ref, ks, c, U(n), e1, ph[:-1])
    X = np.vstack([X, X[:1]])
    s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(X, axis=0), axis=1))])
    return ph, s, X


def ang_to_u(ph, s, a):
    """Angle(s) -> arc-length fraction on a dense ring (angles mod 2 pi)."""
    return np.interp(np.mod(a, 2 * np.pi), ph, s) / s[-1]


def u_to_ang(ph, s, u):
    """Arc-length fraction(s) (any real; whole turns kept) -> angle."""
    u = np.asarray(u, float)
    k = np.floor(u)
    return np.interp((u - k) * s[-1], s, ph) + 2 * np.pi * k


def circ_len(ref, ks, c, n, e1):
    return dense_ring(ref, ks, c, n, e1, 360)[1][-1]


# ---------------------------------------------------------------------------------------------- the shoulder --
def arm_root_plane(L, plan):
    """(a) The arm root ring's plane: through the armpit's saddle (the dome), its normal half-way between the
    upper arm's axis and lateral; its centre on the upper arm's bone line."""
    d_up = U(L["elbow"] - L["shoulder"])
    tilt = plan["shoulder"]["root_tilt"]
    n = U((1 - tilt) * d_up + tilt * np.array([1.0, 0, 0]))
    t = ((L["armpit"] - L["shoulder"]) @ n) / (d_up @ n)
    return L["shoulder"] + t * d_up, n, d_up


def shoulder(M, ref, L, plan, tp, tk, C, SR):
    """(a, pass 3) The rim (N = n_b + n_t + 2 n_f, on the even-gap rim) -> nl loops -> the arm root ring (the plan's
    arm_root_n, ~40 close). The count is shed on the TRUNK side by four corner chains: kites stacked loop after loop
    at the rim's corners (front-bottom: the pectoral's fold; back-bottom: the lat; back-top: the scapula; front-top:
    the trapezius), each kite's middle on the previous kite's short vertex, so a chain is one diagonal seam: its
    first kite cancels the lattice's corner 5-pole and only its last leaves a 5-pole. Loops are blends rim -> root
    at the same root angle (dense index), put back on the reference, their points blended toward even arc length."""
    rim = np.roll(np.asarray(tk["rim"]), -(C["n_b"] // 2))   # start mid-bottom: no corner kite wraps
    N = len(rim)
    Nr = int(tp["arm_root_n"])
    m = SR["m"]
    c, n, _ = arm_root_plane(L, plan)
    e1 = ring_frame(c, n, np.array([0, 1.0, 0]))[0]
    Xd, Yd = SR["X"], SR["Y"]
    V = np.asarray(M.V)
    Yc = np.vstack([Yd, Yd[:1]])
    sY = SR["s"]
    # each rim vertex's dense index: nearest dense rim point, then refined by arc length; unwrapped monotone
    j0 = cKDTree(Yd).query(V[rim])[1].astype(float)
    idx = j0[0] + np.unwrap((j0 - j0[0]) * 2 * np.pi / m) * m / (2 * np.pi)
    corner_ids = [tk["corners"][q] for q in ("FB", "BB", "BT", "FT")]
    cpos = [int(np.where(rim == v)[0][0]) for v in corner_ids]
    nl = max(1, int(round(tp["shoulder_gap"] / tp["shoulder_spacing"])) - 1)
    r_tot = (N - Nr) // 2
    assert (N - Nr) % 2 == 0 and r_tot >= 0, (N, Nr)
    order = [0, 1, 2, 3]                                   # FB, BB first (farthest from the deltoid), then BT, FT
    kq = [r_tot // 4 + (1 if q < r_tot % 4 else 0) for q in order]
    assert max(kq) <= nl + 1, ("chains longer than the loops", kq, nl)
    C["shoulder_loops"] = nl
    C["shoulder_chains"] = {q: k for q, k in zip(("FB", "BB", "BT", "FT"), kq)}

    def curve(f):
        Q = (1 - f) * Yd + f * Xd
        if 0 < f < 1:
            Q, _ = ref.project([TRUNK, ARM], Q)
        Q = np.vstack([Q, Q[:1]])
        sq = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(Q, axis=0), axis=1))])
        return Q, sq

    def at(Q, ii):
        return np.stack([np.interp(np.mod(ii, m), np.arange(m + 1), Q[:, k]) for k in range(3)], 1)

    def even(Q, sq, ii, w):
        a = np.interp(np.mod(ii, m), np.arange(m + 1), sq) / sq[-1]
        a = a[0] + np.unwrap((a - a[0]) * 2 * np.pi) / (2 * np.pi)
        k = np.arange(len(ii))
        a0 = a[0] + np.angle(np.mean(np.exp(2j * np.pi * (a - a[0] - k / len(ii))))) / (2 * np.pi)
        a2 = (1 - w) * a + w * (a0 + k / len(ii))
        kk = np.floor(a2)
        out = np.interp((a2 - kk) * sq[-1], sq, np.arange(m + 1)) + m * kk
        return out

    prev, cur_idx, cur_c = rim, idx, list(cpos)
    ends = {}
    for j in range(1, nl + 2):
        f = j / (nl + 1)
        Q, sq = curve(f)
        act = [q for q in range(4) if j - 1 < kq[q]]
        starts = sorted((cur_c[q] - 1) % len(prev) for q in act)
        eL = len(prev)
        kset = set(starts)
        anchor, i = [0], 0
        while i < eL:
            if i in kset:
                anchor[-1] = i + 1
                i += 2
            else:
                anchor.append(i + 1)
                i += 1
        last = anchor.pop()
        if last != eL:
            anchor[0] = last
        anchor = [a % eL for a in anchor]
        new_idx = np.array([cur_idx[a] for a in anchor])
        new_idx = new_idx[0] + np.unwrap((new_idx - new_idx[0]) * 2 * np.pi / m) * m / (2 * np.pi)
        new_c = [anchor.index(cur_c[q] % eL) if cur_c[q] % eL in anchor else None for q in range(4)]
        w = tp["root_even"] if j == nl + 1 else 0.35
        new_idx = even(Q, sq, new_idx, w)
        X = at(Q, new_idx)
        if j == nl + 1:
            X = T.ring_by_rays(ref, [TRUNK, ARM], c, n, e1, ring_angles(X, c, n, e1))
        ids = M.add(X, "shoulder", j, 0, FREE, REG["upper_arms"] if f > 0.5 else REG["torso_front"], (TRUNK, ARM))
        M.strip(prev, ids, REG["upper_arms"], "shoulder", closed=True, kites=starts)
        for q in act:
            if j == kq[q]:
                ends[q] = int(ids[new_c[q]])
        prev, cur_idx, cur_c = ids, new_idx, [x if x is not None else 0 for x in new_c]
    assert len(prev) == Nr, (len(prev), Nr)
    C["shoulder_kite_verts"] = sorted(ends.values())
    C["N_arm"] = Nr
    return {"root": prev, "c": c, "n": n, "e1": e1}


# ------------------------------------------------------------------------------------------------ the breast --
def breast(M, ref, L, plan, tp, tk, C):
    """The breast hole's rim (2(w + h)) -> k shrinking loops -> a w x h grid cap, in the breast's own view (the
    reference's normal at the apex), cast back onto the reference along it. The rim's corners are 5-poles, the cap's
    3-poles (the 8 a breast has); the loops are concentric about the apex."""
    rim = tk["breast_rim"]
    w, h = tk["breast_wh"]
    N = len(rim)
    assert N == 2 * (w + h)
    ap = L["breast_apex"]
    _, nrm, _, _ = ref._sf[(TRUNK,)][0].closest(ap[None], k=16) if (TRUNK,) in ref._sf else (None, None, None, None)
    if nrm is None:
        ref.project([TRUNK], ap[None])
        _, nrm, _, _ = ref._sf[(TRUNK,)][0].closest(ap[None], k=16)
    Xr = np.asarray(M.V)[rim]
    ax = U(0.5 * U(nrm[0]) + 0.5 * U(ap - Xr.mean(0)))
    e1, e2 = frame(ax, np.array([0, 1.0, 0]))
    P2 = np.stack([(Xr - ap) @ e1, (Xr - ap) @ e2], 1)
    o2 = P2.mean(0) * tp["breast_centre_pull"]
    k = tp["breast_loops"]
    cr = tp["breast_cap"]

    def to3(Q2):
        O = ap + 0.25 * ax + Q2[:, :1] * e1 + Q2[:, 1:] * e2
        return fill_nan(ref.cast([TRUNK], O, np.tile(-ax, (len(O), 1))))

    prev = rim
    for j in range(1, k + 1):
        f = j / (k + 1) * (1 - cr)
        ids = M.add(to3(o2 + (P2 - o2) * (1 - f)), "breast", j, 0, FREE, REG["torso_front"])
        M.strip(prev, ids, REG["torso_front"], "breast", closed=True)
        prev = ids
    B2 = o2 + (P2 - o2) * (cr if not tp.get("breast_cap_on_loop") else (1 - k / (k + 1) * (1 - cr)))
    bot, rgt = B2[0:w + 1], B2[w:w + h + 1]
    top = B2[w + h:2 * w + h + 1][::-1]
    lft = np.vstack([B2[2 * w + h:], B2[:1]])[::-1]
    G = np.zeros((w + 1, h + 1), np.int64)
    for a in range(w + 1):
        for b_ in range(h + 1):
            kk = [a, w + b_, 2 * w + h - a, (2 * w + 2 * h - b_) % N]
            if b_ == 0:
                G[a, b_] = prev[kk[0]]
            elif a == w:
                G[a, b_] = prev[kk[1]]
            elif b_ == h:
                G[a, b_] = prev[kk[2]]
            elif a == 0:
                G[a, b_] = prev[kk[3]]
    inner = [(a, b_) for a in range(1, w) for b_ in range(1, h)]
    Q2 = []
    for a, b_ in inner:
        u_, v_ = a / w, b_ / h
        p = ((1 - v_) * bot[a] + v_ * top[a] + (1 - u_) * lft[b_] + u_ * rgt[b_]
             - ((1 - u_) * (1 - v_) * bot[0] + u_ * (1 - v_) * bot[w] + (1 - u_) * v_ * top[0] + u_ * v_ * top[w]))
        Q2.append(p)
    ids = M.add(to3(np.array(Q2)), "breast", k + 1, 0, FREE, REG["torso_front"])
    for (a, b_), v in zip(inner, ids):
        G[a, b_] = v
    for a in range(w):
        for b_ in range(h):
            M.quad(G[a, b_], G[a + 1, b_], G[a + 1, b_ + 1], G[a, b_ + 1], REG["torso_front"], "breast")
    return {"cap": G}


# ------------------------------------------------------------------------------------------------ the crotch --
def crotch(M, ref, L, plan, tp, tk, C):
    """The midline strip under the perineum: b quads a side from the pubis (R0's front middle) to the cleft (its
    back middle); its ends meet R0 one edge off the middle (the two 5-poles a side). The leg's root ring is R0[1..K-1]
    and the strip's lateral side back to the front: K_low - 2 + b points."""
    R0 = tk["R0"]
    K = len(R0) - 1
    V = np.asarray(M.V)
    m0, mb = V[R0[0]], V[R0[K]]
    ks = [TRUNK, LEG, LEG + 5]
    c0 = np.array([0.0, max(m0[1], mb[1]) + 0.03, 0.5 * (m0[2] + mb[2])])
    a0 = np.arctan2(m0[1] - c0[1], m0[2] - c0[2])
    a1 = np.arctan2(mb[1] - c0[1], mb[2] - c0[2])
    if a1 > a0:
        a1 -= 2 * np.pi
    aa = np.linspace(a0, a1, 400)
    D = np.stack([np.zeros_like(aa), np.sin(aa), np.cos(aa)], 1)
    X = fill_nan(ref.cast(ks, np.tile(c0, (len(aa), 1)), D))
    X[:, 0] = 0.0
    X[0], X[-1] = m0, mb
    sl = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(X, axis=0), axis=1))])
    b = to_parity(sl[-1] / tp["spacing"], 1)
    g = np.linspace(0, sl[-1], b + 1)
    Mx = np.stack([np.interp(g, sl, X[:, k]) for k in range(3)], 1)
    mid = np.concatenate([[R0[0]], M.add(Mx[1:-1], "crotch", 0, 1, MID, REG["pelvis_glutes"], tuple(ks)), [R0[K]]])
    wl = V[R0[1]][0] * 0.5 + V[R0[K - 1]][0] * 0.5
    wl = tp.get("crotch_half_width", wl)
    q, _ = ref.project(ks, Mx[1:-1] + np.array([wl, 0, 0]))
    lat = np.concatenate([[R0[1]], M.add(q, "crotch", 1, 1, FREE, REG["thighs"], tuple(ks)), [R0[K - 1]]])
    for i in range(b):
        M.quad(mid[i], mid[i + 1], lat[i + 1], lat[i], REG["pelvis_glutes"], "crotch")
    root = np.concatenate([R0[1:K], lat[1:-1][::-1]])
    C["b"] = int(b)
    C["N_leg"] = int(len(root))
    C["perineum_mm"] = round(float(sl[-1]) * 1000, 1)
    return {"root": root, "mid": mid, "lat": lat}


# ---------------------------------------------------------------------------------------------- the templates --
def load_template(name):
    V, F = [], []
    with open(os.path.join(HERE, "base", name + ".obj")) as f:
        for ln in f:
            if ln.startswith("v "):
                V.append([float(a) for a in ln.split()[1:4]])
            elif ln.startswith("f "):
                F.append([int(a.split("/")[0]) - 1 for a in ln.split()[1:]])
    V, F = np.array(V), np.array(F, np.int64)
    he = {(int(a), int(b)) for q in F for a, b in zip(q, np.roll(q, -1))}
    nxt = {a: b for (a, b) in he if (b, a) not in he}
    start = min(nxt)
    loop = [start]
    while nxt[loop[-1]] != start:
        loop.append(nxt[loop[-1]])
    assert len(loop) == len(nxt), "the template has more than one open boundary"
    return V, F, np.array(loop)


def template(M, name, part, reg):
    """(b) a hand / foot template at its base level, joined by its rim (22 points). Returns the rim's ids, its
    centre and plane normal (pointing out of the limb, toward the hand / foot)."""
    V, F, loop = load_template(name)
    ids = M.add(V, part, -1, 0, TEMPLATE, reg, ())
    for q in F:
        M.quad(*ids[q], reg, part)
    R = V[loop]
    c = R.mean(0)
    n = np.linalg.svd(R - c)[2][2]
    if (V.mean(0) - c) @ n < 0:
        n = -n
    return ids[loop], c, n


# ---------------------------------------------------------------------------------------------------- limbs --
def walk_anchor(phi, ks, eL, sense):
    """The shorter ring's angles after kites on the longer ring: each short vertex sits under its long anchor
    (a kite's middle vertex for the one under a kite)."""
    kset = set(ks)
    anchor = [0]
    i = 0
    while i < eL:
        if i in kset:
            anchor[-1] = i + 1
            i += 2
        else:
            anchor.append(i + 1)
            i += 1
    last = anchor.pop()
    if last != eL:                                  # the last kite wrapped onto S[0]
        anchor[0] = last
    out = np.array([phi[a % eL] for a in anchor], float)
    if anchor[0] == eL - 1:
        out[0] -= sense * 2 * np.pi
    return out


def kite_starts(phi, sense, psi_h, r, sector, stagger):
    """r kite starts on a ring (angles phi), middles spread over the hidden side (psi_h +- sector/2)."""
    n = len(phi)
    if r <= 0:
        return []
    d = sector / r
    out = []
    for q in range(r):
        tgt = psi_h + (q - (r - 1) / 2) * d + stagger * d
        m = int(np.argmin(np.abs(np.angle(np.exp(1j * (phi - tgt))))))
        out.append(min(max(m - 1, 0), n - 2))
    out = sorted(set(out))
    for q in range(1, len(out)):
        out[q] = max(out[q], out[q - 1] + 3)
    assert len(out) == r and out[-1] <= n - 2 and (out[0] + n - out[-1] >= 3), (out, n)
    return out


def tube(M, ref, ks, top, stations, rim, hidden, C, name, n_rim_blend=5, w_even=0.35, joint=None):
    """A limb from the ring top = (ids, c, n, e1) through `stations` [(c, n, kind, N, r, part, reg)] (r: kites in
    the strip from the previous ring), ending on the template rim = (ids, c, n) when given. Angles twist-free (the
    frame carried ring to ring), each ring blended toward even arc length; the last rings toward the rim's angles;
    crease and fan rings keep their planes (PLANE flag)."""
    V = np.asarray(M.V)
    ids0, c0, n0, e10 = top
    e1 = ring_frame(c0, n0, e10)[0]
    phi = ring_angles(V[ids0], c0, n0, e1)
    sense = 1.0 if np.median(np.diff(phi)) > 0 else -1.0
    frames = [(c0, n0, e1)]
    for st in stations:
        frames.append((st[0], st[1], ring_frame(st[0], st[1], frames[-1][2])[0]))
    rim_ids = None
    if rim is not None:
        rids, rc, rn = rim
        fc, fn, fe = frames[-1]
        pr = ring_angles(V[rids], fc, fn, fe)
        if np.sign(np.median(np.diff(pr))) != sense:
            rids = rids[::-1]
            pr = ring_angles(V[rids], fc, fn, fe)
        sh = int(np.argmin(np.abs(np.angle(np.exp(1j * (pr - phi[0]))))))
        rim_ids = np.roll(rids, -sh)
    rings, log, creases = [np.asarray(ids0)], [], []
    prev_c, prev_n, prev_e1 = c0, n0, e1
    nst = len(stations)
    for k, (c, n, kind, N, r, part, reg) in enumerate(stations, start=1):
        _, _, e1 = frames[k]
        eL = len(phi)
        starts = []
        if r > 0:
            e1p, e2p = ring_frame(prev_c, prev_n, prev_e1)
            hp = hidden - (hidden @ prev_n) * prev_n
            psi = np.arctan2(hp @ e2p, hp @ e1p)
            stag = (len(log) % 3 - 1) / 3.0
            starts = kite_starts(phi, sense, psi, r, np.radians(C["kite_sector"]), stag)
            phi_c = walk_anchor(phi, starts, eL, sense)
            log.append({"ring": k, "kites": len(starts), "from": eL, "to": eL - 2 * len(starts)})
        else:
            phi_c = phi
        assert len(phi_c) == N, (name, k, len(phi_c), N)
        if kind == "rim":
            ids = rim_ids
            phi_new = ring_angles(V[ids], c, n, e1) if False else phi_c
        else:
            ph_d, s_d, _ = dense_ring(ref, ks, c, n, e1, 360)
            uc = ang_to_u(ph_d, s_d, phi_c)
            uc = uc[0] + np.unwrap((uc - uc[0]) * 2 * np.pi) / (2 * np.pi)
            j = np.arange(N)
            u0 = uc[0] + np.angle(np.mean(np.exp(2j * np.pi * (uc - uc[0] - sense * j / N)))) / (2 * np.pi)
            u = (1 - w_even) * uc + w_even * (u0 + sense * j / N)
            if rim_ids is not None and k > nst - 1 - n_rim_blend:
                ur = ang_to_u(ph_d, s_d, ring_angles(V[rim_ids], c, n, e1))
                ur = ur - np.round(ur - u)
                wb = smooth01((k - (nst - 1 - n_rim_blend)) / n_rim_blend)
                u = (1 - wb) * u + wb * ur
            phi_new = u_to_ang(ph_d, s_d, u)
            X = T.ring_by_rays(ref, ks, c, U(n), e1, phi_new)
            pl = M.plane(c, n) if kind in ("crease", "fan") else -1
            ids = M.add(X, part, k, 0, PLANE if pl >= 0 else FREE, reg, tuple(ks), pl)
        if kind == "crease" or (k >= 2 and stations[k - 2][2] == "crease"):
            assert not starts, (name, k, "kites next to the crease")
            if kind == "crease":
                creases.append((len(rings), part, reg))
        else:
            M.strip(rings[-1], ids, reg, part, closed=True, kites=starts)
        rings.append(ids)
        phi = phi_new
        prev_c, prev_n, prev_e1 = c, n, e1
    for kc, part, reg in creases:
        joint_patch(M, ref, ks, rings[kc - 1], rings[kc], rings[kc + 1], joint, C, name, part, reg)
    C.setdefault("bands", {})[name] = log
    return rings


def joint_patch(M, ref, ks, P, Cr, D, j, C, name, part, reg):
    """(a, pass 3) The joint between the rings P, C (the crease) and D (same count, columns aligned):

        flexor side (the fossa)          extensor side (olecranon / patella), columns 0..m (0, m: the epicondyles)
        P ---- P ---- P                  P ---- P ---- P ---- P
        |      |      |                  |  A ---- A ---- A  |      A: halfway P -> C, from c_0 to c_m
        C ---- C ---- C                  C ---- C ---- C ---- C      A-C sheared one column (a 3-pole at A_1)
        |      |      |                  |  B ---- B ---- B  |      B: halfway C -> D, from c_1 to c_m-1
        D ---- D ---- D                  D ---- D ---- D ---- D      C-B sheared the other way (a 3-pole at c_2)
    The fossa keeps one gap a side (s_b), the extensor side two (s_b each); the loops end in 5-3 pairs at the
    epicondyles (c_0 5, A_1 3, c_1 5, c_2 3; c_m 5, B_m-2 3), on the hinge axis where the skin moves least."""
    V = np.asarray(M.V)
    N = len(Cr)
    side = (V[Cr] - j["J"]) @ j["ext"]
    on = side >= 0
    assert 0 < on.sum() < N
    e0 = int(np.where(on & ~np.roll(on, 1))[0][0])
    m = int(on.sum()) - 1
    assert m >= 5, (name, m)
    idx = [(e0 + k) % N for k in range(N)]
    p = [int(P[i]) for i in idx]
    c = [int(Cr[i]) for i in idx]
    d = [int(D[i]) for i in idx]
    qa, _ = ref.project(ks, 0.5 * (V[p[1:m]] + V[c[1:m]]))
    qb, _ = ref.project(ks, 0.5 * (V[c[2:m - 1]] + V[d[2:m - 1]]))
    a_ids = M.add(np.asarray(qa), part, -2, 0, FREE, reg, tuple(ks))
    b_ids = M.add(np.asarray(qb), part, -3, 0, FREE, reg, tuple(ks))
    A = [c[0]] + [int(x) for x in a_ids] + [c[m]]
    B = {k: int(b_ids[k - 2]) for k in range(2, m - 1)}
    B[1], B[m - 1] = c[1], c[m - 1]
    for k in range(m):
        M.quad(p[k], p[k + 1], A[k + 1], A[k], reg, part)
    M.quad(c[0], A[1], A[2], c[1], reg, part)
    for k in range(2, m - 1):
        M.quad(c[k - 1], A[k], A[k + 1], c[k], reg, part)
    M.quad(c[m - 2], A[m - 1], c[m], c[m - 1], reg, part)
    for k in range(m, N):
        M.quad(p[k], p[(k + 1) % N], c[(k + 1) % N], c[k], reg, part)
    M.quad(c[1], c[2], c[3], B[2], reg, part)
    for i in range(2, m - 3):
        M.quad(B[i], c[i + 1], c[i + 2], B[i + 1], reg, part)
    M.quad(B[m - 3], c[m - 2], c[m - 1], B[m - 2], reg, part)
    for k in range(1, m - 1):
        M.quad(B[k], B[k + 1], d[k + 1], d[k], reg, part)
    for k in list(range(m - 1, N)) + [0]:
        M.quad(c[k % N], c[(k + 1) % N], d[(k + 1) % N], d[k % N], reg, part)
    poles = [c[0], A[1], c[1], c[2], c[m], B[m - 2]]
    for v in poles:
        M.designed[v] = 1
    V = np.asarray(M.V)
    ep = V[[c[0], c[m]]]
    dist = max(float(np.min(np.linalg.norm(ep - V[v], axis=1))) for v in poles)
    C["joint_pole_hinge_mm"] = max(C.get("joint_pole_hinge_mm", 0.0), round(dist * 1000, 1))
    C.setdefault("joint_patch", {})[name] = {"m": m, "N": N, "r_e_mm": round(j["r_e"] * 1000, 1),
                                             "r_f_mm": round(j["r_f"] * 1000, 1), "g0_mm": round(j["g0"] * 1000, 2),
                                             "tilt_deg": round(j["tau_deg"], 2)}


def joint_loops(J, d_in, d_out, fan_deg, off):
    hinge = U(np.cross(d_in, d_out))
    return T.joint_fan(J, d_in, d_out, hinge, fan_deg, off, 3), hinge


def slerp_n(a, b, w):
    return U((1 - w) * a + w * b)


def limb_stations(c0, n0, J, d_in, d_out, c_end, n_end, jp, tp, N0, N_mid, N_end, part_reg, bands, ref=None, ks=None):
    """Stations of a two-segment limb: root (c0, n0) -> joint J -> end (the template rim's centre / normal).
    Spacing: tp limb_spacing, bend_spacing (s_b) inside the joint's bend zone (+-bend). The joint (a, pass 3): the
    crease ring C on the bisector, and either side of it one ring P / D on a plane turned about the hinge so that
    it sits s_b from C in the fossa and 2 s_b over the olecranon / patella, where the partial loops A / B (built in
    tube(): joint_patch) halve the gap and end at the epicondyles. Ring counts N0 -> N_mid -> N_end by `bands`."""
    s_l, s_b, bz = tp["limb_spacing"], tp["bend_spacing"], jp["bend"]
    nb = U(d_in + d_out)
    hinge = U(np.cross(d_in, d_out))
    flex = U(d_out - d_in)
    ext = -flex
    r_f = r_e = 0.035
    if ref is not None:
        X = T.ring_by_rays(ref, ks, J, nb, flex, np.array([0.0, np.pi]))
        r_f, r_e = [float(np.linalg.norm(x - J)) for x in X]
    tau = s_b / (r_e + r_f)
    g0 = s_b + r_f * tau
    n_P, n_D = U(nb + tau * ext), U(nb - tau * ext)
    u_el = float((J - c0) @ d_in)
    u_end = u_el + float(np.linalg.norm(c_end - J))
    us = []
    n1 = max(1, int(round((u_el - bz) / s_l)))
    us += [("ring", u) for u in np.linspace(0, u_el - bz, n1 + 1)[1:]]
    n2 = max(1, int(round((bz - g0) / s_b)))
    us += [("bend", u) for u in np.linspace(u_el - bz, u_el - g0, n2 + 1)[1:-1]]
    us += [("fan", u_el - g0), ("crease", u_el), ("fan", u_el + g0)]
    us += [("bend", u) for u in np.linspace(u_el + g0, u_el + bz, n2 + 1)[1:]]
    n3 = max(1, int(round((u_end - u_el - bz - jp["end_bend"]) / s_l)))
    us += [("ring", u) for u in np.linspace(u_el + bz, u_end - jp["end_bend"], n3 + 1)[1:]]
    n4 = max(1, int(round(jp["end_bend"] / s_b)))
    us += [("ring", u) for u in np.linspace(u_end - jp["end_bend"], u_end, n4 + 1)[1:]]
    st = []
    u_rb = tp["root_blend"] * u_el
    for kind, u in us:
        if kind == "fan":
            c, n = (J - g0 * nb, n_P) if u < u_el else (J + g0 * nb, n_D)
        elif kind == "crease":
            c, n = J, nb
        elif u < u_el:
            c = c0 + u * d_in
            n = slerp_n(n0, d_in, smooth01(u / u_rb)) if u < u_rb else d_in
            if u > u_el - bz:
                n = slerp_n(d_in, n_P, smooth01((u - (u_el - bz)) / (bz - g0)))
        else:
            c = J + (u - u_el) * d_out
            n = d_out
            if u < u_el + bz:
                n = slerp_n(n_D, d_out, smooth01((u - u_el - g0) / (bz - g0)))
            ue = u_end - jp["end_bend"] - 2 * s_l
            if u > ue:
                n = slerp_n(d_out, n_end, smooth01((u - ue) / (u_end - ue)))
        st.append([c, U(n), kind, u])
    st[-1][2] = "rim"
    st[-1][0], st[-1][1] = c_end, n_end
    # counts: band 1 mid upper segment, band 2 mid lower segment (kite strips every other ring)
    N = [N0] * len(st)
    R = [0] * len(st)
    u_all = np.array([x[3] for x in st])
    for (ua, ub, Nf, Nt) in ((0.0, u_el - bz, N0, N_mid), (u_el + bz, u_end - jp["end_bend"], N_mid, N_end)):
        r_tot = (Nf - Nt) // 2
        if r_tot <= 0:
            continue
        nstr = int(min(bands["strips"], max(1, r_tot // bands["min_per_strip"])))
        uc = ua + bands["at"] * (ub - ua)
        kc = int(np.argmin(np.abs(u_all - uc)))
        ksel = [kc + 2 * (q - (nstr - 1) // 2) for q in range(nstr)]
        per = [r_tot // nstr + (1 if q < r_tot % nstr else 0) for q in range(nstr)]
        for kk, rr in zip(ksel, per):
            R[kk] = rr
    cur = N0
    for k in range(len(st)):
        cur -= 2 * R[k]
        N[k] = cur
    assert N[-1] == N_end, (N[-1], N_end)
    out = []
    for (c, n, kind, u), Nk, Rk in zip(st, N, R):
        part, reg = part_reg(kind, u, u_el)
        out.append((c, n, kind, Nk, Rk, part, reg))
    return out, {"u_joint": u_el, "u_end": u_end, "hinge": hinge, "bisector": nb, "J": J, "d_in": d_in,
                 "d_out": d_out, "bend": bz, "end_bend": jp["end_bend"], "c_end": c_end, "n_end": n_end, "ext": ext,
                 "r_e": r_e, "r_f": r_f, "g0": g0, "tau_deg": float(np.degrees(np.arctan(tau)))}


# ------------------------------------------------------------------------------------------------- assembly --
def tier_params(plan, tier):
    tp = dict(plan["tiers"][tier])
    tp.update({k: v for k, v in plan["build"]["tiers"][tier].items() if k != "why"})
    return tp


def orient(Q):
    """Make every quad agree with its neighbours (BFS over shared edges); returns the flipped Q and the count of
    edges with more than two quads (non-manifold: must be 0)."""
    Q = np.array(Q, np.int64)
    from collections import deque
    E = {}
    for qi, q in enumerate(Q):
        for k in range(4):
            a, b = int(q[k]), int(q[(k + 1) % 4])
            E.setdefault((min(a, b), max(a, b)), []).append(qi)
    bad = sum(1 for v in E.values() if len(v) > 2)
    seen = np.zeros(len(Q), bool)

    def has(q, a, b):
        for k in range(4):
            if q[k] == a and q[(k + 1) % 4] == b:
                return True
        return False

    for s0 in range(len(Q)):
        if seen[s0]:
            continue
        seen[s0] = True
        dq = deque([s0])
        while dq:
            qi = dq.popleft()
            q = Q[qi]
            for k in range(4):
                a, b = int(q[k]), int(q[(k + 1) % 4])
                for qj in E[(min(a, b), max(a, b))]:
                    if qj == qi or seen[qj]:
                        continue
                    if has(Q[qj], a, b):
                        Q[qj] = Q[qj][::-1]
                    seen[qj] = True
                    dq.append(qj)
    return Q, bad


def mirror(M, V, Q, extra_shared):
    """The right half: every vertex but the shared middle ones copied with x -> -x; quads reversed."""
    n = len(V)
    flag = np.array(M.flag)
    shared = (flag == MID)
    shared[list(extra_shared)] = True
    src = np.where(~shared)[0]
    mp = np.arange(n)
    mp[src] = n + np.arange(len(src))
    VR = V[src] * [-1.0, 1, 1]
    QR = mp[Q][:, ::-1]
    return np.vstack([V, VR]), np.vstack([Q, QR]), src, mp


def project_groups(ref, M, X, idx):
    """Each vertex onto the reference parts it lies on (its labels); returns positions and normals."""
    labs = [M.labs[i] for i in idx]
    out, nrm = X.copy(), np.zeros_like(X)
    for key in sorted(set(labs)):
        sel = np.array([j for j, l_ in enumerate(labs) if l_ == key])
        S = ref._sf.get(key)
        if S is None:
            ref.project(list(key), X[sel[:1]])
            S = ref._sf[key]
        q, fn, _, _ = S[0].closest(X[sel], k=16)
        out[sel], nrm[sel] = q, fn
    return out, nrm


def relax(ref, M, VF, QF, src, n_left, iters, lam):
    """Tangential umbrella relaxation of the left half on the reference (the right half its mirror each step);
    middle vertices stay on x = 0, crease / fan rings on their planes, the head ring and the templates fixed."""
    nF = len(VF)
    e = np.concatenate([QF[:, [0, 1]], QF[:, [1, 2]], QF[:, [2, 3]], QF[:, [3, 0]]])
    A = sp.coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(nF, nF)).tocsr()
    A = ((A + A.T) > 0).astype(float)
    deg = np.asarray(A.sum(1)).ravel()
    flag = np.array(M.flag)
    mov = np.where(np.isin(flag, [FREE, MID, PLANE]) & (deg[:n_left] > 0))[0]
    deg = np.maximum(deg, 1)
    mid = np.intersect1d(np.where(flag == MID)[0], mov)
    pl = np.intersect1d(np.where(flag == PLANE)[0], mov)
    aux = np.array(M.aux)
    P0 = np.array([M.planes[a][0] for a in aux[pl]]) if len(pl) else np.zeros((0, 3))
    N0 = np.array([M.planes[a][1] for a in aux[pl]]) if len(pl) else np.zeros((0, 3))
    V = VF[:n_left].copy()
    _, nrm = project_groups(ref, M, V[mov], mov)
    for it in range(iters):
        VF[:n_left] = V
        VF[n_left:] = V[src] * [-1.0, 1, 1]
        d = (A @ VF)[:n_left] / deg[:n_left, None] - V
        dm = d[mov]
        dm -= (dm * nrm).sum(1, keepdims=True) * nrm
        V[mov] += lam * dm
        V[mid, 0] = 0.0
        if len(pl):
            V[pl] -= ((V[pl] - P0) * N0).sum(1, keepdims=True) * N0
        q, nrm = project_groups(ref, M, V[mov], mov)
        V[mov] = q
        if len(pl):
            for _ in range(2):
                V[pl] -= ((V[pl] - P0) * N0).sum(1, keepdims=True) * N0
                V[pl] = project_groups(ref, M, V[pl], pl)[0]
        V[mid, 0] = 0.0
    VF[:n_left] = V
    VF[n_left:] = V[src] * [-1.0, 1, 1]
    return VF


def neck_snap(ref, M, VF, tk, mp, C, n_ease):
    """The right side of the neck onto the head's own ring points (the head is 2-8 mm off mirror), eased over the
    rows below; the eased points put back on the reference."""
    R = ref.ring
    rows = tk["rows"]
    i_n = C["i_n"]

    def row_ids(i):
        ids = rows[i]["ids"]
        return np.concatenate([ids["F"], ids["T"][1:], ids["B"][1:]])

    top = row_ids(i_n)
    assert len(top) == 48
    dmax = 0.0
    disp = np.zeros((48, 3))
    for j in range(1, 47):
        r = mp[top[j]]
        tgt = R[(94 - j) % 94]
        disp[j] = tgt - VF[r]
        dmax = max(dmax, float(np.linalg.norm(disp[j])))
        VF[r] = tgt
    moved = []
    for m in range(1, n_ease + 1):
        ids = row_ids(i_n - m)
        if len(ids) != 48:
            break
        w = 1 - m / (n_ease + 1)
        for j in range(1, 47):
            r = mp[ids[j]]
            VF[r] += w * disp[j]
            moved.append(r)
    if moved:
        mv = np.array(moved)
        S = ref._sf[(TRUNK,)][0]
        VF[mv] = S.closest(VF[mv], k=16)[0]
    C["neck_snap_mm_max"] = round(dmax * 1000, 2)
    return VF


def resample_poly(X, f):
    """A polyline at arc-length fractions f."""
    s = arc_fracs(X)
    return np.stack([np.interp(f, s, X[:, k]) for k in range(3)], 1)


def neck_meet(ref, M, VF, QF, tk, mp, C, K, n_smooth, ease_pow, untwist_rows=2):
    """(a, pass 3b) The neck meets her head's ring one to one. The reference's front neck turns forward under the
    jaw, where the canvas rays cannot reach it (the rows bunched 15-28 mm below the ring), and the head's ring has
    3-6 mm steps (its own rows ending, some stepping back along the ring). So the top K rows are re-placed, per
    side, between the base row (row i_n - K - 1, as built) and the side's own ring points (left R[j], right
    R[94 - j]): along each column a surface curve (the chord, projected on the reference), the rows at even arc
    length on it; the rail's top is the ring smoothed (its steps eased out) and sampled at the ring's own arc
    fractions, so every row runs forward under the ring's back-steps; the steps' rise eases in over the top rows
    (weight s^ease_pow). The midline columns (shared) carry the head's own 2-3 mm midline offset, easing it to
    zero at the base row: the field is continuous through the midline and nothing crosses it."""
    R = ref.ring
    rows = tk["rows"]
    i_n = C["i_n"]
    S = ref._sf[(TRUNK,)][0]

    def row_ids(i):
        ids = rows[i]["ids"]
        return np.concatenate([ids["F"], ids["T"][1:], ids["B"][1:]])

    base = row_ids(i_n - K - 1)
    assert len(base) == 48, ("the neck meet reaches the collar kites", K)
    band = [row_ids(i_n - m) for m in range(1, K + 1)]
    assert all(len(b) == 48 for b in band)
    s_rows = np.array([1 - m / (K + 1) for m in range(1, K + 1)])
    mirror = np.array([-1.0, 1, 1])
    out = {}
    for side in (1, -1):
        Rs = R[np.arange(48)] if side == 1 else R[(94 - np.arange(48)) % 94] * mirror
        B = VF[base] if side == 1 else VF[mp[base]] * mirror
        Z = Rs.copy()                                  # the ring smoothed: umbrella steps, the midline ends fixed
        for _ in range(n_smooth):
            Z[1:-1] += 0.5 * (0.5 * (Z[:-2] + Z[2:]) - Z[1:-1])
        Z = S.closest(Z, k=16)[0]
        Z[0], Z[-1] = Rs[0], Rs[-1]
        dense = resample_poly(Z, np.linspace(0, 1, 481))
        top = resample_poly(dense, arc_fracs(Rs))      # the smooth rail, at the ring's own arc fractions
        tg = U(np.gradient(top, axis=0))
        dev = Rs - top
        dev -= (dev * tg).sum(1, keepdims=True) * tg       # the steps' rise only: never along the row
        cols = np.zeros((48, K, 3))
        for j in range(48):
            ch = B[j] + np.linspace(0, 1, 25)[:, None] * (top[j] - B[j])
            ch = S.closest(ch, k=16)[0]
            ch[0], ch[-1] = B[j], top[j]
            ch = S.closest(resample_poly(ch, np.linspace(0, 1, 25)), k=16)[0]
            ch[0], ch[-1] = B[j], top[j]
            cols[j] = resample_poly(ch, s_rows) + (s_rows ** ease_pow)[:, None] * dev[j]
        for m in range(K):
            P = S.closest(cols[:, m], k=16)[0]
            if side == -1:
                P = P * mirror
            out[(side, m)] = P
    for m in range(K):
        ids = band[m]
        for j in range(48):
            if j in (0, 47):
                VF[ids[j]] = out[(1, m)][j]            # the shared midline: the left's (the same column)
            else:
                VF[ids[j]] = out[(1, m)][j]
                VF[mp[ids[j]]] = out[(-1, m)][j]
    for j in range(1, 47):
        VF[mp[row_ids(i_n)[j]]] = R[(94 - j) % 94]
    mv = [v for m in range(untwist_rows) for v in list(band[m]) + [mp[x] for x in band[m][1:-1]]]
    VF = untwist(S, VF, QF, mv, 0.0008, 3)
    C["neck_meet"] = {"rows": int(K), "smooth": int(n_smooth), "ease_pow": float(ease_pow),
                      "midline_offset_mm": [round(float(R[0][0]) * 1000, 2), round(float(R[47][0]) * 1000, 2)]}
    return VF


def untwist(S, VF, QF, ids, step, iters, e_min=0.0025):
    """(a, pass 3b) A deterministic local search: each vertex in `ids` (in order) tries the 5 x 5 grid of tangent
    offsets (+-2 step) on the surface S and keeps the one that lowers the largest fold across its quads' edges
    (edges under e_min and quad aspect over 3.5 penalised). The neck's top rows under the head ring's steps."""
    vq = {}
    for q, quad in enumerate(QF):
        for v in quad:
            vq.setdefault(int(v), []).append(q)
    E, qa, qb = G.edge_pairs(QF)
    eq = {}
    for k in range(len(E)):
        eq.setdefault(int(qa[k]), []).append(k)
        eq.setdefault(int(qb[k]), []).append(k)
    grid = np.array([(a, b) for a in range(-2, 3) for b in range(-2, 3)], float) * step
    for _ in range(iters):
        for v in ids:
            v = int(v)
            qs = vq[v]
            ks = np.array(sorted({k for q in qs for k in eq[q]}))
            p0 = VF[v].copy()
            nrm = U(G.quad_normals(VF, QF[qs]).sum(0))
            t1 = U(np.cross(nrm, [1.0, 0, 0]) if abs(nrm[0]) < 0.9 else np.cross(nrm, [0, 1.0, 0]))
            t2 = np.cross(nrm, t1)
            cand = S.closest(p0 + grid[:, :1] * t1 + grid[:, 1:] * t2, k=16)[0]
            cand = np.concatenate([p0[None], cand])
            allq = np.array(sorted(set(qa[ks]) | set(qb[ks])))
            P = np.broadcast_to(VF[QF[allq]], (len(cand), len(allq), 4, 3)).copy()
            hit = QF[allq] == v
            P[:, hit] = cand[:, None, :]
            n = U(np.cross(P[:, :, 2] - P[:, :, 0], P[:, :, 3] - P[:, :, 1]))
            loc = {q: i for i, q in enumerate(allq)}
            ia = np.array([loc[q] for q in qa[ks]])
            ib = np.array([loc[q] for q in qb[ks]])
            dih = np.degrees(np.arccos(np.clip((n[:, ia] * n[:, ib]).sum(-1), -1, 1))).max(1)
            own = np.array([loc[q] for q in qs])
            L4 = np.linalg.norm(P[:, own] - np.roll(P[:, own], -1, axis=2), axis=-1)
            pen = (200.0 * np.maximum(0.0, e_min - L4.min(-1)) / e_min
                   + 10.0 * np.maximum(0.0, L4.max(-1) / L4.min(-1) - 3.5)).sum(1)
            sc = dih + pen
            VF[v] = cand[int(np.argmin(sc - 1e-9 * (np.arange(len(sc)) == 0)))]
    return VF

def part_reg_fn(names, regs):
    def f(kind, u, u_j):
        if kind in ("fan", "crease", "bend") or (kind == "ring" and False):
            return names[1], regs[0] if u < u_j else regs[1]
        return (names[0], regs[0]) if u < u_j else (names[2], regs[1])
    return f


def build(plan, tier, ref, cv, L):
    tp = tier_params(plan, tier)
    M = QM()
    C = {"tier": tier, "kite_sector": tp["kite_sector"]}
    c_ar, n_ar, _ = arm_root_plane(L, plan)
    SR = shoulder_rim(ref, cv, L, plan, tp)
    C.update(trunk_plan(ref, cv, L, plan, tp, SR))
    tk = trunk(M, ref, cv, L, plan, tp, C, SR)
    sh = shoulder(M, ref, L, plan, tp, tk, C, SR)
    bc = breast(M, ref, L, plan, tp, tk, C)
    cr = crotch(M, ref, L, plan, tp, tk, C)
    lim = plan["limbs"]
    joints = {}
    # the arm: root ring -> elbow -> the hand's rim
    hid, hc, hn = template(M, "hand_l", "hand", REG["hands"])
    J = L["elbow"]
    d_in, d_out = U(J - L["shoulder"]), U(hc - J)
    ka = [TRUNK, ARM, HAND]
    circ = circ_len(ref, ka, J, U(d_in + d_out), np.array([0, 0, 1.0]))
    N_el = int(np.clip(to_parity(circ / tp["ring_spacing"], C["N_arm"]), 22, C["N_arm"]))
    if not tp.get("upper_arm_band", True):
        N_el = C["N_arm"]          # (a) no window for poles between the shoulder zone and the elbow zone
    jp = dict(lim["elbow"], **tp["elbow"])
    st, joints["elbow"] = limb_stations(c_ar, n_ar, J, d_in, d_out, hc, hn, jp, tp, C["N_arm"], N_el, 22,
                                        part_reg_fn(("arm", "elbow", "forearm"), (REG["upper_arms"], REG["forearms"])),
                                        tp["bands"], ref, ka)
    hidden = U(np.array(tp["hidden"]))
    tube(M, ref, ka, (sh["root"], c_ar, n_ar, sh["e1"]), st, (hid, hc, hn), hidden, C, "arm", joint=joints["elbow"])
    # the leg: root ring (R0 + the crotch strip's side) -> knee -> the foot's rim
    fid, fc, fn = template(M, "foot_l", "foot", REG["feet"])
    J = L["knee"]
    d_in, d_out = U(J - L["hip"]), U(fc - J)
    p, nl = L["leg"]["p"], L["leg"]["n"]
    c_lg = L["hip"] + ((p - L["hip"]) @ nl) / (d_in @ nl) * d_in
    kl = [TRUNK, LEG, FOOT]
    circ = circ_len(ref, kl, J, U(d_in + d_out), np.array([0, 0, 1.0]))
    N_kn = int(np.clip(to_parity(circ / tp["ring_spacing"], C["N_leg"]), 22, C["N_leg"]))
    jp = dict(lim["knee"], **tp["knee"])
    st, joints["knee"] = limb_stations(c_lg, -nl, J, d_in, d_out, fc, fn, jp, tp, C["N_leg"], N_kn, 22,
                                       part_reg_fn(("thigh", "knee", "shin"), (REG["thighs"], REG["lower_legs"])),
                                       tp["bands"], ref, kl)
    tube(M, ref, kl, (cr["root"], c_lg, -nl, np.array([0, 0, 1.0])), st, (fid, fc, fn), hidden, C, "leg",
         joint=joints["knee"])
    C.update({"N_el": N_el, "N_kn": N_kn})
    # the whole: orient, mirror, relax, the neck's right side, orient outward
    V, Q = M.arrays()
    n_left = len(V)
    bad = ~np.isfinite(V).all(1)
    if bad.any():
        raise RuntimeError("NaN vertices: " + str(sorted({(PARTS[M.part[i]], M.ring[i]) for i in np.where(bad)[0]})[:12]))
    top = tk["rows"][C["i_n"]]["ids"]
    shared = [top["F"][0], top["B"][-1]]
    VF, QF, src, mp = mirror(M, V, Q, shared)
    QF, nonman = orient(QF)
    C["non_manifold_edges"] = int(nonman)
    VF = relax(ref, M, VF, QF, src, n_left, tp["relax_iters"], tp["relax_lambda"])
    if tp.get("neck_meet_rows"):
        VF = neck_meet(ref, M, VF, QF, tk, mp, C, tp["neck_meet_rows"], tp["neck_ring_smooth"], tp["neck_step_ease"],
                       tp.get("neck_untwist_rows", 0))
    else:
        VF = neck_snap(ref, M, VF, tk, mp, C, tp["neck_ease_rows"])
    C["_hip_ring"] = VF[cr["root"]].copy()
    Gc = bc["cap"]                                   # (a, pass 3b) the cap corners vs the apex, the wrist / ankle
    cn = [Gc[0, 0], Gc[-1, 0], Gc[-1, -1], Gc[0, -1]]
    C["breast_cap_corner_mm"] = [round(float(np.linalg.norm(VF[v] - L["breast_apex"])) * 1000, 1) for v in cn]
    C["ankle_points"], C["wrist_points"] = int(len(fid)), int(len(hid))
    fnq = np.cross(VF[QF[:, 2]] - VF[QF[:, 0]], VF[QF[:, 3]] - VF[QF[:, 1]])
    ctr = VF[QF].mean(1)
    vol = float((fnq * ctr).sum())
    if vol < 0:
        QF = QF[:, ::-1]
    used = np.zeros(len(VF), bool)                   # drop the vertices left inside the breast window
    used[QF.ravel()] = True
    keep = np.where(used)[0]
    remap = -np.ones(len(VF), np.int64)
    remap[keep] = np.arange(len(keep))
    nr = len(src)
    info = {
        "part": np.concatenate([np.array(M.part), np.array(M.part)[src]]),
        "ring": np.concatenate([np.array(M.ring), np.array(M.ring)[src]]),
        "col": np.concatenate([np.array(M.col), np.array(M.col)[src]]),
        "flag": np.concatenate([np.array(M.flag), np.array(M.flag)[src]]),
        "vreg": np.concatenate([np.array(M.reg), np.array(M.reg)[src]]),
        "side": np.concatenate([np.where(np.array(M.flag) == MID, 0, 1), np.full(nr, -1)]),
        "qreg": np.concatenate([np.array(M.qreg), np.array(M.qreg)]),
        "qpart": np.concatenate([np.array(M.qpart), np.array(M.qpart)]),
        "mirror_of": np.concatenate([np.full(n_left, -1), src]),
        "designed_pole": np.concatenate([np.array(M.designed), np.array(M.designed)[src]]),
    }
    info["side"][shared] = 0
    info["mirror_of"] = np.where(info["mirror_of"] >= 0, remap[np.maximum(info["mirror_of"], 0)], -1)
    info = {k: (v[keep] if k not in ("qreg", "qpart") else v) for k, v in info.items()}
    return VF[keep], remap[QF], info, C, joints, M, tk


# ------------------------------------------------------------------------------------------------- measures --
def pct(x, q=(5, 50, 95), k=1000.0):
    return [round(float(v) * k, 2) for v in np.percentile(x, q)] if len(x) else []


def bend_zones(joints, L):
    """(a) where poles may not sit: each joint's slab +-bend along the limb (both sides), the wrist / ankle slab."""
    Z = []
    for nm, j in joints.items():
        Z.append((nm, j["J"], j["bisector"], j["bend"]))
        Z.append((nm + "_end", j["c_end"], j["n_end"], j["end_bend"]))
    return Z


def zone_dist(X, Z):
    """Signed distance (m) from each point to the nearest bend zone (negative inside), mirrored for x < 0."""
    Xm = X * np.where(X[:, :1] < 0, [-1.0, 1, 1], 1.0)
    best = np.full(len(X), 9.0)
    name = np.array([""] * len(X), object)
    for nm, c, n, half in Z:
        a = np.abs((Xm - c) @ n) - half
        near = np.linalg.norm(Xm - c, axis=1) < half + 0.12
        a = np.where(near, a, 9.0)
        m = a < best
        best[m], name[m] = a[m], nm
    return best, name


def measure(ref, V, Q, info, C, joints, L, plan, tier):
    n = len(V)
    e = np.concatenate([Q[:, [0, 1]], Q[:, [1, 2]], Q[:, [2, 3]], Q[:, [3, 0]]])
    es = np.sort(e, 1)
    uniq, cnt = np.unique(es, axis=0, return_counts=True)
    bnd = uniq[cnt == 1]
    out = {"tier": tier, "vertices": int(n), "quads": int(len(Q)), "triangles_body": int(2 * len(Q)),
           "quad_share": 1.0, "boundary_edges": int(len(bnd)), "non_manifold_edges": int((cnt > 2).sum())}
    hd = plan["reference"]["head_tris"]
    out["triangles_whole"] = int(2 * len(Q) + hd + plan["build"]["rest_tris"])
    bv = np.unique(bnd)
    R = ref.ring
    d_ring = cKDTree(R).query(V[bv])[0]
    out["open_boundary_is_head_ring"] = bool(len(bnd) == 94 and d_ring.max() < 1e-9)
    val = np.bincount(uniq.ravel(), minlength=n)
    used = val > 0
    out["isolated_vertices"] = int((~used).sum())
    inner = used.copy()
    inner[bv] = False
    tmpl = info["flag"] == TEMPLATE
    h = np.bincount(val[inner & ~tmpl])
    out["valence_hist_body"] = {int(k): int(v) for k, v in enumerate(h) if v}
    h = np.bincount(val[inner & tmpl])
    out["valence_hist_templates"] = {int(k): int(v) for k, v in enumerate(h) if v}
    poles = np.where(inner & ~tmpl & (val != 4))[0]
    Z = bend_zones(joints, L)
    zd, zn = zone_dist(V[poles], Z)
    out["poles"] = [{"v": int(p), "valence": int(val[p]), "part": PARTS[int(info["part"][p])],
                     "pos_mm": [int(round(c * 1000)) for c in V[p]], "bend_zone": str(zn[k]),
                     "zone_dist_mm": round(float(zd[k]) * 1000, 1)} for k, p in enumerate(poles)]
    out["poles_in_bend_zone"] = int((zd < 0).sum())
    # template rims: poles where the templates join (valence counted on the whole mesh)
    el = np.linalg.norm(V[uniq[:, 0]] - V[uniq[:, 1]], axis=1)
    qr = info["qreg"]
    inv = {v: k for k, v in REG.items()}
    out["edge_mm_by_region"] = {}
    for r in sorted(set(qr.tolist())):
        qe = np.sort(np.concatenate([Q[qr == r][:, [0, 1]], Q[qr == r][:, [1, 2]], Q[qr == r][:, [2, 3]],
                                     Q[qr == r][:, [3, 0]]]), 1)
        qe = np.unique(qe, axis=0)
        out["edge_mm_by_region"][inv[r]] = pct(np.linalg.norm(V[qe[:, 0]] - V[qe[:, 1]], axis=1))
    out["edge_mm_by_part"] = {}
    qp = info["qpart"]
    for r in sorted(set(qp.tolist())):
        qe = np.unique(np.sort(np.concatenate([Q[qp == r][:, [k, (k + 1) % 4]] for k in range(4)]), 1), axis=0)
        out["edge_mm_by_part"][PARTS[r]] = pct(np.linalg.norm(V[qe[:, 0]] - V[qe[:, 1]], axis=1))
    out["edge_mm_all"] = pct(el)
    # crease rings: plane fit vs the bisector
    cr = {}
    for nm, j in joints.items():
        sel = np.where((info["part"] == PARTS.index("elbow" if nm == "elbow" else "knee")) &
                       (info["flag"] == PLANE) & (V[:, 0] > 0))[0]
        best = None
        for rg in sorted(set(info["ring"][sel].tolist())):
            X = V[sel[info["ring"][sel] == rg]]
            c = X.mean(0)
            nn = np.linalg.svd(X - c)[2][2]
            if abs((c - j["J"]) @ j["bisector"]) < 0.002:
                best = round(float(np.degrees(np.arccos(min(1.0, abs(nn @ j["bisector"]))))), 3)
        cr[nm] = best
    out["crease_plane_vs_bisector_deg"] = cr
    # the surface distance to the reference: vertices and quad centres (the chord's sag), templates apart
    S = Surface_all(ref)
    body = ~tmpl & used
    dv = S.closest(V[body], k=16)[3]
    qb = ~np.isin(info["qpart"], [PARTS.index("hand"), PARTS.index("foot")])
    dq = S.closest(V[Q[qb]].mean(1), k=16)[3]
    out["surface_mm_vertices"] = pct(dv, (50, 95, 100))
    out["surface_mm_quad_centres"] = pct(dq, (50, 95, 100))
    dt = S.closest(V[tmpl & used], k=16)[3]
    out["surface_mm_templates"] = pct(dt, (50, 95, 100))
    a = np.linalg.norm(np.cross(V[Q[:, 2]] - V[Q[:, 0]], V[Q[:, 3]] - V[Q[:, 1]]), axis=1) / 2
    out["quad_area_mm2_min"] = round(float(a.min()) * 1e6, 3)
    out["degenerate_quads"] = int((a < 1e-7).sum())
    out["counts"] = {k: (round(float(v), 4) if isinstance(v, (float, np.floating)) else v) for k, v in C.items()
                     if k not in ("rows_y_front", "rows_y_back", "kites", "bands") and not k.startswith("_")}
    tmpl_q = np.isin(info["qpart"], [PARTS.index("hand"), PARTS.index("foot")])
    out["collar_and_trunk_kites"] = [[k[0], int(k[1]), len(k[2])] for k in C["kites"]]
    out["limb_bands"] = C["bands"]
    out["triangles_templates"] = int(2 * tmpl_q.sum())
    out["triangles_body_without_templates"] = int(2 * len(Q) - 2 * tmpl_q.sum())
    out["gates"] = G.gates(ref, V, Q, info, C, joints, L, out["poles"], poles, C["_hip_ring"], PARTS)
    out["gates"]["pass"]["surface_p95_0.5mm"] = out["surface_mm_quad_centres"][1] <= 0.5
    return out


def Surface_all(ref):
    from surfdist import Surface
    if not hasattr(ref, "_all"):
        ref._all = Surface(ref.P, ref.T)
    return ref._all


def save(out_dir, tier, V, Q, info):
    os.makedirs(out_dir, exist_ok=True)
    np.savez_compressed(os.path.join(out_dir, tier + ".npz"), V=V.astype(np.float32), Q=Q.astype(np.int32),
                        **{k: np.asarray(v) for k, v in info.items()},
                        parts=np.array(PARTS), regions=np.array([f"{v}:{k}" for k, v in REG.items()]))
    with open(os.path.join(out_dir, tier + ".obj"), "w") as f:
        f.write(f"# Survivor Unchained body, {tier} tier: our own base topology (tools/body/topo_build.py)\n")
        f.write("".join(f"v {x:.6f} {y:.6f} {z:.6f}\n" for x, y, z in V))
        f.write("".join(f"f {a + 1} {b + 1} {c + 1} {d + 1}\n" for a, b, c, d in Q))


def mesh_hash(V, Q):
    h = hashlib.sha256()
    h.update(np.round(V, 6).astype(np.float64).tobytes())
    h.update(np.asarray(Q, np.int64).tobytes())
    return h.hexdigest()[:16]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", default=os.path.join(HERE, "loopplan.json"))
    ap.add_argument("--out", default=os.path.join(HERE, "out", "topo"))
    ap.add_argument("--tiers", default="close,play")
    ap.add_argument("--check-determinism", action="store_true")
    a = ap.parse_args()
    with open(a.plan) as f:
        plan = json.load(f)
    ref = T.Ref(plan)
    L = T.landmarks_ref(ref, plan)
    T.label(ref, L)
    cv = T.Canvas(ref, plan["canvas"])
    rep = {}
    for tier in a.tiers.split(","):
        t0 = time.time()
        V, Q, info, C, joints, M, tk = build(plan, tier, ref, cv, L)
        m = measure(ref, V, Q, info, C, joints, L, plan, tier)
        m["hash"] = mesh_hash(V, Q)
        if a.check_determinism:
            V2, Q2 = build(plan, tier, ref, cv, L)[:2]
            m["hash_second_run"] = mesh_hash(V2, Q2)
            m["deterministic"] = m["hash"] == m["hash_second_run"]
        m["seconds"] = round(time.time() - t0, 1)
        save(a.out, tier, V, Q, info)
        rep[tier] = m
        print(tier, json.dumps({k: m[k] for k in ("quads", "triangles_body", "triangles_whole", "boundary_edges",
                                                  "non_manifold_edges", "open_boundary_is_head_ring",
                                                  "poles_in_bend_zone", "valence_hist_body", "surface_mm_quad_centres",
                                                  "hash")}))
        g = m["gates"]
        print("  gates", json.dumps({k: g[k] for k in ("fold_edges_over_60", "fold_deg_p99_max_body", "aspect_over_4",
                                                         "aspect_p95_max", "edges_under_2mm", "edge_min_mm_body",
                                                         "poles_within_40mm_of_a_zone", "poles_within_40mm_by_zone",
                                                         "poles_designed_at_epicondyles", "cleft_edges_over_60")
                                     if k in g}), json.dumps(g["pass"]))
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "topo.json"), "w") as f:
        json.dump(rep, f, indent=1, default=str)


if __name__ == "__main__":
    main()
