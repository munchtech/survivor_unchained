#!/usr/bin/env python
"""P1: OUR base topology, generated from the loop plan (tools/body/loopplan.json) around OUR skeleton on a reference
surface. MakeHuman (hm08, CC0) is only the shape reference (run_a's close surface) and, for v1, the hands and feet
(tools/body/base/hand_l.obj, foot_l.obj: (b) converted once from hm08, our own files now).

    python tools/body/topo.py [--plan tools/body/loopplan.json] [--out tools/body/out/topo] [--tiers close,play,far]
    python tools/body/topo.py --make-templates        # once: hm08's hand and foot -> tools/body/base/*.obj

Writes <out>/<tier>.npz (V, Q quads, UV per corner, region per quad, tags), <out>/<tier>.obj, <out>/corr_<tier>.npz
(each vertex -> a reference triangle + barycentrics, and a sparse map onto hm08's base points for slider targets),
tools/body/base/landmarks.json (named vertex sets on our close mesh) and <out>/topo.json (the measures).
Pure numpy/scipy/embreex; no Blender. Built on the LEFT half (x >= 0), mirrored; the neck's right side then snapped
to the head's own ring (the head is not symmetric to the mm) and eased below.

Patterns (the judged part), each a function with its diagram: trunk_lattice() (rows and columns, the shoulder hole
and the breast hole in it, the neck rows), shoulder(), breast(), crotch(), joint_fan().
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
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import gl  # noqa: E402
import ray  # noqa: E402
from surfdist import Surface  # noqa: E402

TH = np.linspace(0, np.pi, 721)
TRUNK, ARM, LEG, HAND, FOOT = 0, 1, 2, 3, 4          # reference labels (left side; the right side gets +5)
REGIONS = {4: "neck_decolletage", 5: "torso_front", 6: "torso_back", 7: "upper_arms", 8: "forearms", 9: "hands",
           10: "pelvis_glutes", 11: "thighs", 12: "lower_legs", 13: "feet"}


def U(v):
    v = np.asarray(v, float)
    return v / np.maximum(np.linalg.norm(v, axis=-1, keepdims=True), 1e-12)


def smooth01(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def rot(axis, ang):
    a = U(axis)
    K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    return np.eye(3) + np.sin(ang) * K + (1 - np.cos(ang)) * K @ K


# ------------------------------------------------------------------------------------------------ the reference --
class Ref:
    """The shape reference (b): run_a's close surface (glTF frame: y up, front +z, her left +x), our skeleton (a) as
    run_a placed it, the head's open ring (c). Labels per triangle: trunk / arm / leg / hand / foot (left 0-4, right
    5-9), cut by the plan's arm-root plane, leg-crease plane, wrist and ankle cuts."""

    def __init__(self, plan):
        r = plan["reference"]
        z = np.load(os.path.join(REPO, r["close"]))
        self.P = z["P"].astype(float)
        self.Fq = z["F"].astype(np.int64)
        self.T = np.concatenate([self.Fq[:, [0, 1, 2]], self.Fq[:, [0, 2, 3]]])
        self.C = self.P[self.T].mean(1)
        sk = gl.Glb(os.path.join(REPO, r["skeleton"])).skeleton()
        self.J = {n: sk.head(i).astype(float) for i, n in enumerate(sk.names)}
        self.ring = head_ring(os.path.join(REPO, r["head"]), r["head_mesh"])
        self.lab = np.zeros(len(self.T), np.int64)
        self._sc, self._sf = {}, {}

    def kinds(self, ks):
        return np.isin(self.lab, ks)

    def scene(self, ks):
        key = tuple(ks)
        if key not in self._sc:
            idx = np.where(self.kinds(ks))[0]
            self._sc[key] = (ray.scene(self.P, self.T[idx]), idx)
        return self._sc[key]

    def cast(self, ks, O, D):
        sc, idx = self.scene(ks)
        O = np.asarray(O, float).reshape(-1, 3)
        D = np.asarray(D, float).reshape(-1, 3)
        pid, tf = ray.hits(sc, O, D)
        return O + D * np.where(pid >= 0, tf, np.nan)[:, None]

    def project(self, ks, X):
        key = tuple(ks)
        if key not in self._sf:
            idx = np.where(self.kinds(ks))[0]
            self._sf[key] = (Surface(self.P, self.T[idx]), idx)
        S, idx = self._sf[key]
        q, n, t, d = S.closest(np.asarray(X, float), k=16)
        return q, idx[t]


def head_ring(path, name):
    """Her head's open boundary, ordered: index 0 the front middle point (max z), then over her left (x > 0)."""
    h = gl.Glb(path).mesh(name)
    rep = gl.weld(h.P.astype(float), 1e-7)
    first = {}
    for i, r_ in enumerate(rep):
        first.setdefault(r_, i)
    be = gl.boundary_edges(rep[h.T])
    adj = {}
    for a, b in be:
        adj.setdefault(int(a), []).append(int(b))
        adj.setdefault(int(b), []).append(int(a))
    loop = [int(be[0][0])]
    while True:
        nx = [n for n in adj[loop[-1]] if len(loop) < 2 or n != loop[-2]]
        if nx[0] == loop[0]:
            break
        loop.append(nx[0])
    R = h.P[[first[k] for k in loop]].astype(float)
    R = np.roll(R, -int(np.argmax(R[:, 2])), 0)
    if R[1, 0] < R[-1, 0]:
        R = np.concatenate([R[:1], R[1:][::-1]])
    return R


def seg_dist(P, a, b):
    d = b - a
    t = np.clip((P - a) @ d / (d @ d), 0, 1)
    return np.linalg.norm(P - (a + t[:, None] * d), axis=1)


def label(ref, L):
    """(a) the cuts that split the reference into the parts our pieces lie on (left rules, mirrored for the right)."""
    C = ref.C
    side = C[:, 0] < 0
    Cm = C * np.where(side, -1, 1)[:, None]
    lab = np.full(len(C), TRUNK)
    a = L["arm_root"]
    arm = ((Cm - a["p"]) @ a["n"] > 0) & (seg_dist(Cm, L["shoulder"], L["hand_tip"]) < 0.13) & (Cm[:, 0] > 0.07)
    lab[arm] = ARM
    lg = L["leg"]
    leg = ((Cm - lg["p"]) @ lg["n"] < 0) & (Cm[:, 1] < 1.15)
    lab[leg] = LEG
    w = L["wrist_cut"]
    lab[arm & ((Cm - w["p"]) @ w["n"] > 0)] = HAND
    k = L["ankle_cut"]
    lab[leg & ((Cm - k["p"]) @ k["n"] > 0)] = FOOT
    ref.lab = np.where(side & (lab > 0), lab + 5, lab)
    ref._sc, ref._sf = {}, {}


def landmarks_ref(ref, plan):
    """Joints (a: our skeleton) and the few surface points the plan keys to (found on the reference, b)."""
    J = ref.J
    L = {"shoulder": J["upperarm_l"], "elbow": J["lowerarm_l"], "wrist": J["hand_l"], "hip": J["thigh_l"],
         "knee": J["calf_l"], "ankle": J["foot_l"], "hand_tip": J["middle_04_leaf_l"], "ball": J["ball_leaf_l"]}
    P = ref.P
    xs, zs = np.linspace(0.13, 0.26, 66), np.linspace(-0.07, 0.01, 41)   # the armpit's dome: rays straight up
    X, Z = np.meshgrid(xs, zs)
    O = np.stack([X.ravel(), np.full(X.size, 1.25), Z.ravel()], 1)
    pid, tf = ray.hits(ray.scene(P, ref.T), O, np.tile([0, 1.0, 0], (len(O), 1)))
    y = np.where(pid >= 0, tf, -1)
    i = int(np.argmax(y))
    L["armpit"] = O[i] + [0, tf[i], 0]
    d_up = U(L["elbow"] - L["shoulder"])
    sh = plan["shoulder"]
    L["arm_root"] = {"p": L["armpit"], "n": U((1 - sh["root_tilt"]) * d_up + sh["root_tilt"] * np.array([1.0, 0, 0]))}
    hp = plan["hip"]
    nl = U(np.array([-np.tan(np.radians(hp["beta"])), 1.0, -np.tan(np.radians(hp["gamma"]))]))
    L["leg"] = {"p": np.array([0, hp["y_c"], 0.0]), "n": nl}
    d_fo = U(L["wrist"] - L["elbow"])
    L["wrist_cut"] = {"p": L["wrist"] - plan["limbs"]["wrist_cut"] * d_fo, "n": d_fo}
    d_ca = U(L["ankle"] - L["knee"])
    L["ankle_cut"] = {"p": L["ankle"] - plan["limbs"]["ankle_cut"] * d_ca, "n": d_ca}
    m = (P[:, 0] > 0.05) & (P[:, 0] < 0.17) & (P[:, 1] > 1.38) & (P[:, 1] < 1.52)
    L["breast_apex"] = P[m][np.argmax(P[m, 2])]
    return L


# ------------------------------------------------------------------------------------------------- the canvas --
class Canvas:
    """(a) The trunk's chart: canvas (theta, t) -> the first hit of a ray from the trunk's middle line. theta: 0 the
    front middle, 90 deg her left side, 180 the back middle. t: the height on the middle part [h_lo, h_hi] (horizontal
    rays); above h_hi the ray tilts up from the top point (t - h_hi = R_hi x elevation), below h_lo down."""

    def __init__(self, ref, c):
        self.ref, self.hlo, self.hhi, self.Rlo, self.Rhi = ref, c["h_lo"], c["h_hi"], c["R_lo"], c["R_hi"]
        hs = np.linspace(0.95, 1.66, 143)
        O = np.stack([np.zeros_like(hs), hs, np.full_like(hs, 0.6)], 1)
        f = ref.cast([TRUNK], O, np.tile([0, 0, -1.0], (len(hs), 1)))[:, 2]
        b = ref.cast([TRUNK], O * [1, 1, -1], np.tile([0, 0, 1.0], (len(hs), 1)))[:, 2]
        zc = (f + b) / 2
        ok = np.isfinite(zc)
        z = np.convolve(np.pad(zc[ok], 4, mode="edge"), np.ones(9) / 9, "valid")
        self.hs, self.zs = hs[ok], z

    def zc(self, h):
        return np.interp(h, self.hs, self.zs)

    def rays(self, th, t):
        th, t = np.broadcast_arrays(np.asarray(th, float), np.asarray(t, float))
        ho = np.clip(t, self.hlo, self.hhi)
        a = np.where(t > self.hhi, (t - self.hhi) / self.Rhi, np.where(t < self.hlo, (t - self.hlo) / self.Rlo, 0.0))
        a = np.clip(a, -1.5, 1.5)
        O = np.stack([np.zeros_like(ho), ho, self.zc(ho)], -1)
        D = np.stack([np.sin(th) * np.cos(a), np.sin(a), np.cos(th) * np.cos(a)], -1)
        return O, D

    def map(self, th, t):
        O, D = self.rays(th, t)
        return self.ref.cast([TRUNK], O, D).reshape(O.shape)

    def inv(self, X):
        X = np.asarray(X, float)
        y = X[..., 1]
        ho = np.clip(y, self.hlo, self.hhi)
        r = X - np.stack([np.zeros_like(ho), ho, self.zc(ho)], -1)
        a = np.arctan2(r[..., 1], np.hypot(r[..., 0], r[..., 2]))
        t = np.where(y > self.hhi, self.hhi + a * self.Rhi, np.where(y < self.hlo, self.hlo + a * self.Rlo, y))
        return np.arctan2(r[..., 0], r[..., 2]), t


def fill_nan(X):
    """Rays that missed (a hole's rim): the neighbours' straight blend (then projected and relaxed)."""
    X = np.array(X, float)
    bad = ~np.isfinite(X[:, 0])
    if bad.all():
        raise RuntimeError("row missed the surface")
    if bad.any():
        i = np.arange(len(X))
        for k in range(3):
            X[bad, k] = np.interp(i[bad], i[~bad], X[~bad, k])
    return X


def along(cv, th_a, th_b, t_of, n, ns=120):
    """n+1 points at even 3D arc length along the canvas curve t = t_of(theta) from th_a to th_b."""
    th = np.linspace(th_a, th_b, ns)
    X = fill_nan(cv.map(th, t_of(th)))
    s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(X, axis=0), axis=1))])
    g = np.linspace(0, s[-1], n + 1)
    return np.interp(g, s, th), np.stack([np.interp(g, s, X[:, k]) for k in range(3)], 1)


# ---------------------------------------------------------------------------------------------- mesh building --
class Mesh:
    def __init__(self):
        self.V, self.Q, self.tag, self.reg = [], [], [], []

    def add(self, X, tag):
        X = np.atleast_2d(np.asarray(X, float))
        i0 = len(self.V)
        self.V.extend(list(X))
        self.tag.extend([tag] * len(X))
        return np.arange(i0, i0 + len(X))

    def quad(self, a, b, c, d, reg):
        self.Q.append((int(a), int(b), int(c), int(d)))
        self.reg.append(reg)

    def strip(self, A, B, reg, closed=False):
        n = len(A) if closed else len(A) - 1
        for k in range(n):
            k1 = (k + 1) % len(A)
            self.quad(A[k], A[k1], B[k1], B[k], reg)


def trunk_lattice(M, cv, L, plan, tp, head_half):
    """The trunk, left half: rows (half rings from the front middle, theta 0, to the back middle, 180) and columns.

          neck ring (the head's own points; K_top = c_f + n_t + c_k edges)
      F ====================== UPPER (n_t cols) ======================== B     F: FRONT band, c_f columns
      R |  decollete           | shoulder top: its columns end on   |       A    B: BACK band, c_k columns
      O |                     FT-------------top n_t--------------BT      C    the rows between FB..FT (n_f edges)
      N |  [breast hole:       |        OUTER SHOULDER LOOP          |    K    end on the hole's front side, the
      T |   rings + cap]  front n_f    (the arm root inside)    back n_f       same rows behind on its back side
        |                     FB-----------bottom n_b-------------BB
        |                      | LOWER (n_b cols): the side under the arm
      row 0 = R_0, the leg crease ring (K = c_f + n_b + c_k edges): the groin crease in front, the glute fold behind

    FB, BB, FT, BT (canvas corners from the plan) are the shoulder's four 5-poles: a shoulder-loop band out of the
    deltoid and the axillary folds. Below the hole the columns run at even arc length, eased into FB/BB over ~5 cm;
    above it they move from FT/BT to the neck ring's columns (the head's points: a fan into the 4 mm neck spacing)."""
    c_f, n_t, n_b, n_f = tp["c_f"], tp["n_t"], tp["n_b"], tp["n_f"]
    K_top = len(head_half) - 1
    c_k = K_top - c_f - n_t
    K = c_f + n_b + c_k
    sp_ = tp["spacing"]
    tr = plan["trunk"]
    th0, t0 = cv.inv(L["R0"])
    o = np.argsort(th0)
    t_R0 = np.interp(TH, th0[o], t0[o])
    thn, tn = cv.inv(head_half)
    t_N = np.interp(TH, thn, tn)
    root_th, root_t = cv.inv(L["root_ring"])
    sh = plan["shoulder"]
    t_s0 = float(cv.inv(L["armpit"][None])[1][0]) + sh["FB"][1]
    t_s1 = float(root_t.max()) + sh["FT"][1]
    cor = {k: np.radians(sh[k][0]) for k in ("FB", "BB", "FT", "BT")}

    def nrows(ta, tb, th_mid):
        a = ta if np.isscalar(ta) else float(np.interp(th_mid, TH, ta))
        b = tb if np.isscalar(tb) else float(np.interp(th_mid, TH, tb))
        X = fill_nan(cv.map(np.full(17, th_mid), np.linspace(a, b, 17)))
        return max(1, int(round(np.linalg.norm(np.diff(X, axis=0), axis=1).sum() / sp_)))

    full = lambda v: np.full_like(TH, v) if np.isscalar(v) else v
    keys = [t_R0, tr["waist_y"], tr["underbust_y"], t_s0]
    T_rows = []
    for ta, tb in zip(keys[:-1], keys[1:]):
        n = int(round(0.5 * (nrows(ta, tb, np.radians(20)) + nrows(ta, tb, np.radians(160)))))
        for r in range(n):
            T_rows.append((1 - r / n) * full(ta) + (r / n) * full(tb))
    i_s0 = len(T_rows)
    for r in range(n_f + 1):
        T_rows.append(full(t_s0 + (t_s1 - t_s0) * r / n_f))
    i_s1 = len(T_rows) - 1
    n_up = nrows(t_s1, t_N, np.radians(15))
    for r in range(1, n_up + 1):
        T_rows.append((1 - r / n_up) * full(t_s1) + (r / n_up) * t_N)
    i_n = len(T_rows) - 1
    m = max(2, int(round(0.05 / sp_)))
    rows = []
    for i, trow in enumerate(T_rows):
        t_of = (lambda tt: (lambda th: np.interp(th, TH, tt)))(trow)
        if i == i_n:
            ids = M.add(head_half, "neck")
            rows.append({"F": ids[:c_f + 1], "M": ids[c_f:c_f + n_t + 1], "B": ids[c_f + n_t:]})
            continue
        if i == 0:
            ids = M.add(L["R0_pts"], "R0")
            rows.append({"F": ids[:c_f + 1], "M": ids[c_f:c_f + n_b + 1], "B": ids[c_f + n_b:]})
            continue
        if i <= i_s0:
            ths, _ = along(cv, 0, np.pi, t_of, K, 240)
            w = smooth01((i - (i_s0 - m)) / m)
            a, b = (1 - w) * ths[c_f] + w * cor["FB"], (1 - w) * ths[c_f + n_b] + w * cor["BB"]
            nm = n_b
        elif i < i_s1:
            f = (i - i_s0) / (i_s1 - i_s0)
            a, b = (1 - f) * cor["FB"] + f * cor["FT"], (1 - f) * cor["BB"] + f * cor["BT"]
            idf = M.add(along(cv, 0, a, t_of, c_f)[1], "trunk")
            idb = M.add(along(cv, b, np.pi, t_of, c_k)[1], "trunk")
            rows.append({"F": idf, "M": None, "B": idb})
            continue
        else:
            f = (i - i_s1) / (i_n - i_s1)
            a, b = (1 - f) * cor["FT"] + f * thn[c_f], (1 - f) * cor["BT"] + f * thn[c_f + n_t]
            nm = n_t
        XF = along(cv, 0, a, t_of, c_f)[1]
        XM = along(cv, a, b, t_of, nm)[1]
        XB = along(cv, b, np.pi, t_of, c_k)[1]
        ids = M.add(np.concatenate([XF, XM[1:], XB[1:]]), "trunk")
        rows.append({"F": ids[:c_f + 1], "M": ids[c_f:c_f + nm + 1], "B": ids[c_f + nm:]})
    for r in rows:
        M.tag[r["F"][0]] = "mid"
        M.tag[r["B"][-1]] = "mid"
    for k in (0, -1):
        M.tag[rows[0]["F"][0] if k == 0 else rows[0]["B"][-1]] = "R0mid"
    dec = np.radians(10)
    i_dec = int(np.argmin([abs(float(np.interp(dec, TH, t)) - tr["decollete_y"]) for t in T_rows]))
    info = {"K": K, "K_top": K_top, "c_k": c_k, "rows": len(rows), "i_s0": i_s0, "i_s1": i_s1, "i_n": i_n,
            "i_dec": max(i_dec, i_s0), "t_s0": t_s0, "t_s1": t_s1, "T_rows": T_rows}
    return rows, info


def lattice_quads(M, rows, info, plan, hole):
    """Quads of the FRONT, BACK and the two middles (the breast hole's cells skipped); regions by row and band."""
    i_s0, i_s1 = info["i_s0"], info["i_s1"]
    hip_i = max(1, int(round(plan["trunk"]["hip_line_row"] * info["i_waist"])))
    smb_i = max(1, int(round(plan["trunk"]["small_of_back_row"] * info["i_waist"])))
    bi0, bi1, bj0, bj1 = hole if hole else (-1, -1, -1, -1)
    for i in range(len(rows) - 1):
        A, B = rows[i], rows[i + 1]
        regF = 10 if i < hip_i else (4 if i >= info["i_dec"] else 5)
        for j in range(len(A["F"]) - 1):
            if bi0 <= i < bi1 and bj0 <= j < bj1:
                continue
            M.quad(A["F"][j], A["F"][j + 1], B["F"][j + 1], B["F"][j], regF)
        regB = 10 if i < smb_i else 6
        for j in range(len(A["B"]) - 1):
            M.quad(A["B"][j], A["B"][j + 1], B["B"][j + 1], B["B"][j], regB)
        if A["M"] is not None and B["M"] is not None and len(A["M"]) == len(B["M"]) and not (i < i_s0 <= i + 1 and False):
            nm = len(A["M"]) - 1
            if i == i_s0 or (i_s0 < i < i_s1):
                continue
            for j in range(nm):
                if i >= i_s1:
                    reg = 4 if j < nm / 2 else 6
                else:
                    reg = 10 if i < hip_i else (5 if j < nm / 2 else 6)
                M.quad(A["M"][j], A["M"][j + 1], B["M"][j + 1], B["M"][j], reg)
    return hip_i, smb_i


def outer_loop(rows, info):
    """The hole's rim: FB under the arm to BB, up the back side to BT, over the top to FT, down the front side."""
    i_s0, i_s1 = info["i_s0"], info["i_s1"]
    out = list(rows[i_s0]["M"])
    out += [rows[i]["B"][0] for i in range(i_s0 + 1, i_s1 + 1)]
    out += list(rows[i_s1]["M"][::-1][1:])
    out += [rows[i]["F"][-1] for i in range(i_s1 - 1, i_s0, -1)]
    return np.array(out)


def frame(n, e1):
    e1 = U(e1 - (e1 @ n) * n)
    return e1, np.cross(n, e1)


def ring_by_rays(ref, ks, c, n, e1, phis, outside=False):
    """The plane section (centre c, normal n) at angles phis from e1: the first exit of rays from the centre."""
    e1, e2 = frame(n, e1)
    D = np.cos(phis)[:, None] * e1 + np.sin(phis)[:, None] * e2
    if outside:
        return fill_nan(ref.cast(ks, c + 0.4 * D, -D))
    return fill_nan(ref.cast(ks, np.repeat(c[None], len(D), 0), D))


def ring_angles(X, c, n, e1):
    e1, e2 = frame(n, e1)
    r = X - c
    return np.unwrap(np.arctan2(r @ e2, r @ e1))


def even_angles(ref, ks, c, n, e1, n_pts, phi0, sense):
    ph = phi0 + sense * np.linspace(0, 2 * np.pi, 361)
    X = ring_by_rays(ref, ks, c, n, e1, ph)
    s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(X, axis=0), axis=1))])
    return np.interp(np.linspace(0, s[-1], n_pts + 1)[:-1], s, ph)


def limb(M, ref, ks, top_ids, stations, bottom_ids, regs, e1_0, tag):
    """A tube from the ring `top_ids` down `stations` ((centre, normal, kind) per ring, the first the top ring's own
    plane) to the ring `bottom_ids` (a template's rim): each station a plane section by rays from the bone's axis,
    its N points at angles blended from the top ring's (first 4 rings) to even arc length, then to the bottom
    ring's (last 5); the angle frame is carried ring to ring (no twist). regs(k): the region of band k."""
    N = len(top_ids)
    c0, n0 = stations[0][0], stations[0][1]
    e1 = frame(n0, e1_0)[0]
    phi_top = ring_angles(np.asarray(M.V)[top_ids], c0, n0, e1)
    sense = np.sign(np.median(np.diff(phi_top)))
    rings, kinds = [np.asarray(top_ids)], [stations[0][2]]
    ns = len(stations)
    for k in range(1, ns):
        c, n, kind = stations[k]
        e1 = frame(n, e1)[0]
        if k == ns - 1 and bottom_ids is not None:
            rings.append(np.asarray(bottom_ids))
            kinds.append(kind)
            break
        ev = even_angles(ref, ks, c, n, e1, N, phi_top[0], sense)
        w = 1 - smooth01(k / 4.0)
        phi = w * (phi_top - phi_top[0] + ev[0]) + (1 - w) * ev
        if bottom_ids is not None and k > ns - 6:
            pb = ring_angles(np.asarray(M.V)[bottom_ids], c, n, e1)
            pb = pb - 2 * np.pi * np.round((pb[0] - phi[0]) / (2 * np.pi))
            wb = smooth01((k - (ns - 6)) / 5.0)
            phi = (1 - wb) * phi + wb * pb
        rings.append(M.add(ring_by_rays(ref, ks, c, n, e1, phi), tag))
        kinds.append(kind)
    for k, (a, b) in enumerate(zip(rings[:-1], rings[1:])):
        M.strip(a, b, regs(k, kinds), closed=True)
    return rings, kinds


def stations_line(a, na, b, nb_, sp_, keep_out=()):
    """Stations from a to b at the tier's spacing, normals blended na -> nb_, none within 0.6 spacing of keep_out."""
    n = max(1, int(round(np.linalg.norm(b - a) / sp_)))
    out = []
    for k in range(n + 1):
        f = k / n
        p = a + (b - a) * f
        if all(np.linalg.norm(p - q) > 0.6 * sp_ for q in keep_out):
            out.append((p, U((1 - f) * na + f * nb_), "ring"))
    return out


def joint_fan(Jc, d_in, d_out, hinge, fan_deg, off, n_loops):
    """(a) The joint's loops on the bend's bisector planes. The crease loop on the bisector through the joint; with 3
    loops two more, offset +-off along the bisector normal and turned fan_deg about the hinge so they close on the
    crease on the flexor side and spread over the olecranon / patella:

          proximal  \\ | /  distal          extensor side (olecranon / patella): loops spread
                     \\|/                   flexor side (the crease): loops meet
    """
    nb = U(d_in + d_out)
    flex = U(d_out - d_in)
    loops = [(Jc, nb, "crease")]
    if n_loops >= 3:
        fan = []
        for s in (-1, 1):
            c = Jc + s * off * nb
            cand = [U(rot(hinge, g) @ nb) for g in (np.radians(fan_deg), -np.radians(fan_deg))]
            p_flex = Jc + 0.035 * flex
            gaps = [abs((p_flex - c) @ nn) for nn in cand]
            fan.append((c, cand[int(np.argmin(gaps))], "fan"))
        loops = [fan[0], loops[0], fan[1]]
    return loops


# ------------------------------------------------------------------------------------------------ templates --
def make_templates(plan):
    """(b) Once: hm08's base-level hand and foot (run_a's placed, smoothed base points; hm08's quads and UVs) cut at a
    clean wrist / ankle edge loop (22 points each; 44 once subdivided) -> tools/body/base/hand_l.obj, foot_l.obj.
    From then on they are our source files (right side = their mirror); nothing else reads hm08's topology."""
    r = plan["reference"]
    b = np.load(os.path.join(REPO, r["base"]))
    z = np.load(os.path.join(REPO, r["close"]))
    F, UVb = b["F"], b["U"]
    P = z["P"][:13380].astype(float)                    # the used base points come first, in order (subdiv.py)
    sk = gl.Glb(os.path.join(REPO, r["skeleton"])).skeleton()
    H = {n: sk.head(i) for i, n in enumerate(sk.names)}
    out = {}
    for name, (a, j, off) in {"hand_l": ("lowerarm_l", "hand_l", 0.012), "foot_l": ("calf_l", "foot_l", 0.02)}.items():
        d = U(H[j] - H[a])
        s = (P - (H[j] - off * d)) @ d
        near = np.linalg.norm(P - H[j], axis=1) < 0.35
        keep = np.all((s[F] > 0) & near[F] & (P[F][..., 0] > 0), axis=1)
        Fk, Uk = F[keep], UVb[keep]
        used = np.unique(Fk)
        remap = -np.ones(len(P), np.int64)
        remap[used] = np.arange(len(used))
        Fl = remap[Fk]
        e = np.sort(np.concatenate([Fl[:, [k, (k + 1) % 4]] for k in range(4)]), 1)
        u, c = np.unique(e, axis=0, return_counts=True)
        rim = u[c == 1]
        path = os.path.join(HERE, "base", name + ".obj")
        with open(path, "w", newline="\n") as f:
            f.write(f"# {name}: (b) converted once from MakeHuman hm08 (CC0) base mesh, our source file from here on\n")
            f.write(f"# quads {len(Fl)}, rim points {len(rim)} (the {'wrist' if 'hand' in name else 'ankle'} ring)\n")
            for p in P[used]:
                f.write("v %.6f %.6f %.6f\n" % tuple(p))
            for q in Uk.reshape(-1, 2):
                f.write("vt %.6f %.6f\n" % tuple(q))
            for k, q in enumerate(Fl):
                f.write("f " + " ".join(f"{q[i] + 1}/{4 * k + i + 1}" for i in range(4)) + "\n")
        out[name] = {"quads": int(len(Fl)), "points": int(len(used)), "rim": int(len(rim)), "cut_m": off}
    return out


def tier_ties(plan, ring_half=47):
    """The plan's counts must close: the neck half ring, the arm root = the wrist template, the leg root = the ankle."""
    rows = {}
    for t, tp in plan["tiers"].items():
        k_top = ring_half if tp["neck"] == "all" else tp["neck"]
        c_k = k_top - tp["c_f"] - tp["n_t"]
        K = tp["c_f"] + tp["n_b"] + c_k
        rows[t] = {"K_top": k_top, "c_k": c_k, "K": K, "trunk_ring": 2 * K,
                   "N_arm": 2 * tp["n_f"] + tp["n_t"] + tp["n_b"], "N_leg": K - 2 + tp["b"],
                   "rim": 44 if tp["template"] == "sub" else 22}
        rows[t]["closes"] = rows[t]["N_arm"] == rows[t]["rim"] and rows[t]["N_leg"] == rows[t]["rim"]
    return rows


def probe(plan):
    """Part 1 on the reference: labels, landmarks, the canvas, the leg-crease arc and the arm-root ring (WIP)."""
    ref = Ref(plan)
    L = landmarks_ref(ref, plan)
    label(ref, L)
    cv = Canvas(ref, plan["canvas"])
    rep = {"head_ring_points": len(ref.ring), "armpit": np.round(L["armpit"], 4).tolist(),
           "breast_apex": np.round(L["breast_apex"], 4).tolist(),
           "labels": {k: int((ref.lab == v).sum()) for k, v in (("trunk", 0), ("arm_l", 1), ("leg_l", 2), ("hand_l", 3),
                                                                ("foot_l", 4))}}
    a = L["arm_root"]
    c = L["shoulder"] + ((a["p"] - L["shoulder"]) @ a["n"]) / (U(L["elbow"] - L["shoulder"]) @ a["n"]) * U(
        L["elbow"] - L["shoulder"])
    X = ring_by_rays(ref, [TRUNK, ARM], c, a["n"], np.array([0, 1.0, 0]), np.linspace(0, 2 * np.pi, 361)[:-1])
    rep["arm_root_perimeter_m"] = round(float(np.linalg.norm(np.diff(np.vstack([X, X[:1]]), axis=0), axis=1).sum()), 4)
    th, t = cv.inv(ref.ring[:48])
    rep["neck_canvas_t"] = [round(float(t.min()), 4), round(float(t.max()), 4)]
    Xc = cv.map(np.radians([0, 45, 90, 135, 180]), np.full(5, 1.30))
    rep["canvas_hits_t1.30"] = int(np.isfinite(Xc[:, 0]).sum())
    return rep


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", default=os.path.join(HERE, "loopplan.json"))
    ap.add_argument("--make-templates", action="store_true")
    ap.add_argument("--probe", action="store_true")
    a = ap.parse_args()
    with open(a.plan) as f:
        plan = json.load(f)
    if a.make_templates:
        print(json.dumps(make_templates(plan), indent=1))
    print(json.dumps(tier_ties(plan), indent=1))
    if a.probe:
        print(json.dumps(probe(plan), indent=1))


if __name__ == "__main__":
    main()
