#!/usr/bin/env python
"""P1 R1 round 10: her torso, breasts, hips and legs from A as ONE source file on our topology: the designed slider her_a
(designed/her.json, rule "target"; other bodies leave it at 0), so the one-command build reads this, not heroine.glb.

    python tools/body/her_a_target.py tools/body/specs/her_b.json [--maps] [--tiers close,play]

Writes tools/body/base/targets/her_a_{close,play}.npz: "D" [n,3] (glTF m, the move at v = 1, laid by build_topo stage 1
after the join and the stance, before seam_g1), "topology" (build_topo.topo_sha), "M" [n] (the mask), "about".
--maps also carries A's paint once onto our UVs: base/targets/her_a_maps/ (topo_bake.SOURCE_MAPS + bake.json).

The fit is the existing one: her_topo.json's sliders, stance and residual (wrap_topo.py, forms/her_topo_{tier}.npz, A posed
by her_target world=True; TIGHT p95 about 1.8 mm), the topology's hash asserted. D = M (fit - body) + (1 - M) t, where
body = this spec's stage 1 at her_a = 0 and t = spec "her_a" "arm_move_m" (dx away from the midline on each side): the
arm and deltoid keep OUR form and only ride to A's shoulder line. D is 0 on the head's ring.

M, spec "her_a" (a function of the topology's parts and rings and these numbers; no paint): 0 on "zero_parts" (default arm,
elbow, forearm and hand; round 11: the hand only, the fit's arm taken) and on the shoulder band's rings from "zero_ring" out
(null: none), 1 farther than "band_m" along the surface (reference surface, edge
lengths), biharmonic between (L^2 M = 0 on an inverse-edge-length Laplacian, the known sets thick enough that the slope
leaves them at 0), mirror-averaged. Play takes close's M through the shared reference surface. Derivation: (a) the owner,
6 Nov: A is the quality floor, B's job is one topology and sliders; (b) A; (c) the arm is ours: A's arm surface was the
fault of 27 Oct.
"""
import argparse
import json
import os
import shutil
import sys

import numpy as np
import scipy.sparse as sp
from scipy.sparse.csgraph import dijkstra

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import build_topo as bt  # noqa: E402
import headbake  # noqa: E402
from gl import Glb  # noqa: E402
from sliders import load_spec, carry_to_tier  # noqa: E402
from surfdist import Surface  # noqa: E402

TARGETS = os.path.join(HERE, "base", "targets")
OUT_FILE = "her_a_{tier}.npz"


def edges(Q):
    e = np.concatenate([Q[:, [0, 1]], Q[:, [1, 2]], Q[:, [2, 3]], Q[:, [3, 0]]])
    return np.unique(np.sort(e, 1), axis=0)


def mirror(z):
    n = len(z["V"])
    pr = np.arange(n)
    mo = z["mirror_of"]
    r = np.where(mo >= 0)[0]
    pr[r] = mo[r]
    pr[mo[r]] = r
    return pr


def quad_normals(V, Q):
    """Area-weighted vertex normals of a quad mesh (each quad as two triangles)."""
    N = np.zeros_like(V)
    for T in (Q[:, [0, 1, 2]], Q[:, [0, 2, 3]]):
        fn = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
        for c in range(3):
            np.add.at(N, T[:, c], fn)
    return N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-15)


def mask(z, cfg):
    """M on a tier's reference surface (see the module's doc); (M, zero, one) with zero and one the known sets."""
    V, Q = z["V"].astype(np.float64), z["Q"]
    parts = list(map(str, z["parts"]))
    part, ring = z["part"], z["ring"]
    arm = np.isin(part, [parts.index(p) for p in cfg.get("zero_parts", ("arm", "elbow", "forearm", "hand"))])
    zero = arm | ((part == parts.index("shoulder")) & (ring >= cfg["zero_ring"])) if cfg.get("zero_ring") is not None else arm
    e = edges(Q)
    ln = np.linalg.norm(V[e[:, 0]] - V[e[:, 1]], axis=1)
    n = len(V)
    # the surface distance from the zero set: a virtual source joined to it
    ze = np.where(zero)[0]
    r = np.r_[e[:, 0], e[:, 1], np.full(len(ze), n)]
    c = np.r_[e[:, 1], e[:, 0], ze]
    G = sp.coo_matrix((np.r_[ln, ln, np.full(len(ze), 1e-9)], (r, c)), shape=(n + 1, n + 1)).tocsr()
    d = dijkstra(G, indices=n)[:n]
    one = (d >= cfg["band_m"]) & ~zero
    w = 1.0 / np.maximum(ln, 1e-4)
    W = sp.coo_matrix((np.r_[w, w], (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])), shape=(n, n)).tocsr()
    L = (sp.diags(np.asarray(W.sum(1)).ravel()) - W).tocsr()
    known = np.where(zero | one)[0]
    free = np.where(~(zero | one))[0]
    M = bt.biharmonic(L, known, one[known][:, None].astype(float), free)[:, 0]
    pr = mirror(z)
    M = np.clip(0.5 * (M + M[pr]), 0.0, 1.0)
    return M, zero, one


def bodies(spec, fit_spec, tier, A, baked):
    """(this spec's stage 1 at her_a = 0, the fit on A, z). stage_base for both (the fit through stages 2 and 2b too)."""
    pre = bt.load_tier(tier)
    z = pre[0]
    s0 = dict(spec)
    s0["sliders"] = {k: v for k, v in spec["sliders"].items() if k != "her_a"}
    _, V0 = bt.stage_base(s0, tier, {}, pre=pre)
    r = np.load(os.path.join(REPO, fit_spec["forms_topo"].format(tier=tier)))
    assert str(r["topology"]) == bt.topo_sha(z), ("the fit is for another topology", tier)
    _, Vf = bt.stage_base(fit_spec, tier, {}, pre=pre)
    Vf, ring, _ = bt.stage_place(fit_spec, z, Vf, A, baked, {})
    Vf = bt.stage_forms(fit_spec, tier, z, Vf, ring, {})
    return V0, Vf, z


def kabsch(P, Q):
    """The rigid motion (R, t) taking points P onto Q (least squares)."""
    pc, qc = P.mean(0), Q.mean(0)
    U, _, Vt = np.linalg.svd((P - pc).T @ (Q - qc))
    R = Vt.T @ np.diag([1.0, 1.0, np.sign(np.linalg.det(Vt.T @ U.T))]) @ U.T
    return R, qc - R @ pc


class ARest:
    """her_a "a_rest" (round 12): the chain bones that stay at A's OWN rest in the target, e.g. ["clavicle", "upperarm"].
    The fit was solved on A posed into the slider stage's rest (forms/her_topo_target_bones.json); here A is posed
    twice through her_target (the fit's pose, and the same with those bones unturned) and each fit point rides A's
    surface from the first to the second: its closest point's triangle and barycentrics, the offset turned with the
    triangle's frame. Exact on A's own surface (no weights: both poses are A's game stack). B's rest girdle and arm
    then ARE A's, so the game turns B from where A turns from, and the target needs no skinning round trip there.
    The hand (a zero part: ours) rides rigidly: onto the fit's hand in the fit's pose, then with A's hand points."""

    def __init__(self, cfg):
        import her_target as ht
        with open(os.path.join(HERE, "forms", "her_topo_target_bones.json")) as f:
            fb = {k: (np.asarray(v[0], float), np.asarray(v[1], float)) for k, v in json.load(f)["bones"].items()}
        keep = [f"{b}_{s}" for b in cfg["a_rest"] for s in "lr"]
        self.t0 = ht.target(None, world=True, want=fb)
        self.t1 = ht.target(None, world=True, want={k: (None if k in keep else v) for k, v in fb.items()})
        T = self.t0["T"]
        self.S0 = Surface(self.t0["P"], T)
        names = self.t0["names"]
        self.hand = {}
        for s in "lr":
            hb = [i for i, n in enumerate(names) if n.endswith(f"_{s}") and n.split("_")[0] in ("hand", "thumb", "index", "middle", "ring", "pinky")]
            share = (self.t0["W"] * np.isin(self.t0["J"], hb)).sum(1)
            sel = share > 0.999
            self.hand[s] = kabsch(self.t0["P"][sel], self.t1["P"][sel])
        self.turns = self.t1["turns"]

    @staticmethod
    def frames(P, T):
        e1 = P[T[:, 1]] - P[T[:, 0]]
        e2 = P[T[:, 2]] - P[T[:, 0]]
        n = np.cross(e1, e2)
        n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-15)
        e1 = e1 / np.maximum(np.linalg.norm(e1, axis=1, keepdims=True), 1e-15)
        return np.stack([e1, np.cross(n, e1), n], 2)       # columns: edge, in-plane, normal

    def carry(self, V):
        """Points on (near) A in the fit's pose -> the same surface points on A at the a_rest pose."""
        T = self.t0["T"]
        q, _, tri, d = self.S0.closest(V, k=16)
        a, b, c = (self.t0["P"][T[tri, i]] for i in range(3))
        v0, v1, v2 = b - a, c - a, q - a
        d00, d01, d11 = (v0 * v0).sum(1), (v0 * v1).sum(1), (v1 * v1).sum(1)
        d20, d21 = (v2 * v0).sum(1), (v2 * v1).sum(1)
        den = np.maximum(d00 * d11 - d01 * d01, 1e-30)
        wb = (d11 * d20 - d01 * d21) / den
        wc = (d00 * d21 - d01 * d20) / den
        wa = 1.0 - wb - wc
        P1 = self.t1["P"]
        q1 = wa[:, None] * P1[T[tri, 0]] + wb[:, None] * P1[T[tri, 1]] + wc[:, None] * P1[T[tri, 2]]
        F0, F1 = self.frames(self.t0["P"], T)[tri], self.frames(P1, T)[tri]
        off = np.einsum("nji,nj->ni", F0, V - q)               # the offset in the fit-pose triangle's frame
        return q1 + np.einsum("nij,nj->ni", F1, off), d

    def tight(self, V, z, cfg):
        """her_a "a_tight" {"parts": [...], "fade_parts": [...], "lam": [...], "iters": k}: the fit's LOOSE arm (wrap_topo:
        her girth over our loops, 10-23 mm off her skin) laid ON A's skin over those parts (the shoulder and upper arm:
        the cap, the armpit and the arm's top are A's surface, as the trunk's already is), fading to the fit's own over
        fade_parts (biharmonic). Non-rigid ICP as wrap_topo's TIGHT (point-to-plane + 0.1 point-to-point + lam |L U|^2,
        lam stepped down), closest points on A at this pose whose normal agrees (> 0.5) within 40 mm, mirror-averaged."""
        import scipy.sparse.linalg as spl
        Q = z["Q"]
        parts = list(map(str, z["parts"]))
        part = z["part"]
        on = np.isin(part, [parts.index(p) for p in cfg["parts"]])
        off = ~(on | np.isin(part, [parts.index(p) for p in cfg.get("fade_parts", ())]))
        e = edges(Q)
        n = len(V)
        W = sp.coo_matrix((np.ones(2 * len(e)), (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])), shape=(n, n)).tocsr()
        L = (sp.diags(np.asarray(W.sum(1)).ravel()) - W).tocsr()
        known = np.where(on | off)[0]
        w = bt.biharmonic(L, known, on[known][:, None].astype(float), np.where(~(on | off))[0])[:, 0]
        pr = mirror(z)
        w = np.clip(0.5 * (w + w[pr]), 0.0, 1.0)
        free = np.where(w > 1e-4)[0]
        Lf = L[free][:, free]
        LtL = (Lf.T @ Lf).tocsr()
        P1, T = self.t1["P"], self.t0["T"]
        S1 = Surface(P1, T)
        U = np.zeros((len(free), 3))
        X0 = V[free]
        stats = []
        n3 = 3 * len(free)
        ii = np.repeat(np.arange(len(free)) * 3, 9) + np.tile(np.repeat(np.arange(3), 3), len(free))
        jj = np.repeat(np.arange(len(free)) * 3, 9) + np.tile(np.tile(np.arange(3), 3), len(free))
        K = sp.kron(LtL, sp.eye(3)).tocsr()
        for lam in cfg["lam"]:
            for _ in range(int(cfg.get("iters", 4))):
                X = X0 + U
                q, nA, _, d = S1.closest(X, k=16)
                Vc = V.copy()
                Vc[free] = X
                ok = (d < 0.04) & ((nA * quad_normals(Vc, Q)[free]).sum(1) > 0.5)
                Bw = (w[free] * ok)[:, None, None] * (np.einsum("ni,nj->nij", nA, nA) + 0.1 * np.eye(3)[None])
                Am = sp.coo_matrix((Bw.ravel(), (ii, jj)), shape=(n3, n3)).tocsr() + lam * K
                U = spl.spsolve(Am.tocsc(), np.einsum("nij,nj->ni", Bw, q - X0).ravel()).reshape(-1, 3)
                Uf = np.zeros((n, 3))
                Uf[free] = U
                U = (0.5 * (Uf + Uf[pr] * np.array([-1.0, 1.0, 1.0])))[free]
            core = w[free] > 0.99
            stats.append((lam, round(float(np.percentile(d[core] * 1e3, 50)), 2), round(float(np.percentile(d[core] * 1e3, 95)), 2), int((~ok).sum())))
        out = V.copy()
        out[free] = X0 + U
        return out, w, stats

    def hand_wrap(self, Vh, z, cfg, head):
        """her_a "a_hand" (P1 R1 round 28): B's hand ON A's hand surface at the a_rest pose, as B's trunk, girdle and upper
        arm already are, and B's hand and finger joints A's, so A's hand and its curl in every clip are carried. Her left
        hand: (1) each of our hand points mapped by its segment (hand_segments: B's own joints, landmarks on Vh, onto A's;
        seg_maps), blended over the nearest segments (exp(-(d - dmin) / blend_m)); (2) laid on A's skin by non-rigid ICP
        as a_tight's (point-to-plane + 0.1 point-to-point + lam |L U|^2, lam stepped down), each point's closest point on
        A's own part of the hand (its digit or the palm: never a neighbour finger), normals agreeing; (3) eased in from
        the hand part's open edge over ease_m along the surface (0 there: the forearm's points are the fit's). The right
        hand is the left's move mirrored on its own points. Returns (V, ease, joints {"ends:<bone>": [head, tail]}, stats).
        Derivation: (a) gate judge 1 (3): B's hand 27% thinner and 13% shorter than A's, stiff and splayed at the Look
        and close-up; the lead's route: A's hand into her_a; (b) A."""
        import scipy.sparse.linalg as spl
        import skeleton as skm
        with open(os.path.join(HERE, "skeleton.json")) as f:
            skel = json.load(f)
        with open(os.path.join(HERE, "base", "landmarks.json")) as f:
            table = json.load(f)["tiers"]["close"]
        _, _, _, ends, _ = skm.place_skeleton_ours(skel, Vh, table, head)
        Q = z["Q"]
        parts = list(map(str, z["parts"]))
        part = z["part"]
        n = len(Vh)
        hand = part == parts.index("hand")
        Lh = np.where(hand & (z["V"][:, 0] > 0))[0]
        # A's left hand at the a_rest pose: its points weighted to the hand's bones
        P1, T = self.t1["P"], self.t0["T"]
        hb = [i for i, nm in enumerate(self.t1["names"]) if nm.endswith("_l") and nm.split("_")[0] in ("hand",) + HAND_FINGERS]
        a_on = (self.t1["W"] * np.isin(self.t1["J"], hb)).sum(1) > 0.5
        ia = np.where(a_on)[0]
        seg = hand_segments(ends, self.t1["heads"])
        PB = Vh[Lh].astype(np.float64)
        maps, own_a = seg_maps(seg, PB, P1[ia])
        Db = np.stack([seg_dist(PB, s[1], s[2])[0] for s in seg], 1)
        wb = np.exp(-(Db - Db.min(1, keepdims=True)) / float(cfg["blend_m"]))
        wb[wb < 0.01] = 0.0
        wb /= wb.sum(1, keepdims=True)
        Pm = sum(wb[:, k:k + 1] * seg_apply(maps[k], PB) for k in range(len(seg)))
        # the ease from the hand part's open edge (geodesic over our edges)
        e = edges(Q)
        ln = np.linalg.norm(Vh[e[:, 0]] - Vh[e[:, 1]], axis=1)
        edge_v = np.unique(np.r_[e[hand[e[:, 0]] & ~hand[e[:, 1]], 0], e[hand[e[:, 1]] & ~hand[e[:, 0]], 1]])
        inside = hand[e[:, 0]] & hand[e[:, 1]]
        r = np.r_[e[inside, 0], e[inside, 1], np.full(len(edge_v), n)]
        c = np.r_[e[inside, 1], e[inside, 0], edge_v]
        G = sp.coo_matrix((np.r_[ln[inside], ln[inside], np.full(len(edge_v), 1e-9)], (r, c)), shape=(n + 1, n + 1)).tocsr()
        dg = dijkstra(G, indices=n)[:n]
        ease = np.zeros(n)
        ease[Lh] = smoothstep(dg[Lh] / float(cfg["ease_m"]))
        el = ease[Lh]
        X0 = PB + el[:, None] * (Pm - PB)
        # each digit's own part of A's hand (A's points by their nearest A segment; a triangle by its points' majority)
        lab = np.array([s[0].split("_")[1] if s[0].startswith("palm") else s[0].split("_")[0] for s in seg])
        is_palm = np.array([s[0].startswith("palm") for s in seg])
        a_lab = np.full(len(P1), "", dtype=object)
        a_lab[ia] = np.where(is_palm[own_a], "palm", lab[own_a])
        tl = a_lab[T]
        tri_on = np.all(tl != "", 1)
        tmaj = np.where(tl[:, 0] == tl[:, 1], tl[:, 0], np.where(tl[:, 1] == tl[:, 2], tl[:, 1], tl[:, 2]))
        own_b = Db.argmin(1)
        b_grp = np.where(is_palm[own_b], "palm", lab[own_b])
        groups = {}
        for g in ("palm",) + HAND_FINGERS:
            keep = tri_on & ((tmaj == g) | (tmaj == "palm")) if g != "palm" else tri_on
            groups[g] = (Surface(P1, T[keep]), np.where(b_grp == g)[0])
        # ICP
        pr = mirror(z)
        free = Lh
        W1 = sp.coo_matrix((np.ones(2 * len(e)), (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])), shape=(n, n)).tocsr()
        Lap = (sp.diags(np.asarray(W1.sum(1)).ravel()) - W1).tocsr()
        Lf = Lap[free][:, free]
        K = sp.kron((Lf.T @ Lf).tocsr(), sp.eye(3)).tocsr()
        m = len(free)
        ii = np.repeat(np.arange(m) * 3, 9) + np.tile(np.repeat(np.arange(3), 3), m)
        jj = np.repeat(np.arange(m) * 3, 9) + np.tile(np.tile(np.arange(3), 3), m)
        U = np.zeros((m, 3))
        stats = {"segments": {mp["label"]: [round(mp["la"] / mp["lb"], 3), round(mp["g"], 3)] for mp in maps}}
        icp = []
        Vc = Vh.astype(np.float64).copy()
        for lam in cfg["lam"]:
            for _ in range(int(cfg.get("iters", 2))):
                X = X0 + U
                q = np.zeros_like(X)
                nA = np.zeros_like(X)
                d = np.full(len(X), np.inf)
                for g, (S, ids) in groups.items():
                    if len(ids):
                        q[ids], nA[ids], _, d[ids] = S.closest(X[ids], k=16)
                Vc[free] = X
                ok = (d < 0.03) & ((nA * quad_normals(Vc, Q)[free]).sum(1) > 0.3)
                Bw = (el * ok)[:, None, None] * (np.einsum("ni,nj->nij", nA, nA) + 0.1 * np.eye(3)[None])
                Am = sp.coo_matrix((Bw.ravel(), (ii, jj)), shape=(3 * m, 3 * m)).tocsr() + lam * K
                U = spl.spsolve(Am.tocsc(), np.einsum("nij,nj->ni", Bw, q - X0).ravel()).reshape(-1, 3)
            core = el > 0.99
            icp.append((lam, round(float(np.percentile(d[core] * 1e3, 50)), 2), round(float(np.percentile(d[core] * 1e3, 95)), 2), int((~ok).sum())))
        stats["icp (lam, core p50, p95 mm, rejected)"] = icp
        X = X0 + U
        out = Vh.astype(np.float64).copy()
        out[Lh] = X
        Mx = np.array([-1.0, 1.0, 1.0])
        out[pr[Lh]] = Vh[pr[Lh]] + (X - PB) * Mx
        ease[pr[Lh]] = el
        # the joints: A's where B's map them (01-03 heads and the tips: A's own; a metacarpal's head by its palm segment)
        mp = {x["label"]: x for x in maps}
        H = self.t1["heads"]
        joints = {"x:hand_l": [round(float(v), 6) for v in self.t1["rots"]["hand_l"][:, 0]]}
        for f in HAND_FINGERS:
            for k in (1, 2, 3):
                nb = f"{f}_0{k}_l"
                joints["ends:" + nb] = [[round(float(v), 6) for v in H[nb]],
                                        [round(float(v), 6) for v in (H[f"{f}_0{k + 1}_l"] if k < 3 else H[f"{f}_04_leaf_l"])]]
                joints["x:" + nb] = [round(float(v), 6) for v in self.t1["rots"][nb][:, 0]]
            if f != "thumb":
                mh = seg_apply(mp[f"palm_{f}"], np.asarray(ends[f"{f}_metacarpal_l"][0], float)[None])[0]
                joints["ends:" + f"{f}_metacarpal_l"] = [[round(float(v), 6) for v in mh], [round(float(v), 6) for v in H[f"{f}_01_l"]]]
        stats["ease_points"] = int((el > 1e-4).sum())
        stats["wrist_edge_mm_from_hand_joint"] = round(float(np.median(np.linalg.norm(Vh[edge_v[z["V"][edge_v, 0] > 0]] - np.asarray(ends["hand_l"][0]), axis=1))) * 1e3, 1)
        return out, ease, joints, stats

    def hand_field(self, V0, Vf, zero_hand, x):
        """Every point moved as our hand rides: rigidly onto the fit's hand (fit pose), then with A's hand (per side by x)."""
        out = V0.copy()
        for s, sgn in (("l", 1.0), ("r", -1.0)):
            side = x * sgn > 0
            h = zero_hand & side
            R0, t0 = kabsch(V0[h], Vf[h])
            R1, t1 = self.hand[s]
            P = V0[side] @ R0.T + t0
            out[side] = P @ R1.T + t1
        return out


def smoothstep(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


HAND_FINGERS = ("thumb", "index", "middle", "ring", "pinky")


def hand_segments(ends_b, heads_a):
    """Her left hand's segments, one list for B and A: (label, B head, B tail, A head, A tail). The palm: the hand joint to
    each digit's 01 head (both rigs: A has no metacarpals); each digit's 01, 02, 03 head to the next head, the 03 to its
    tip (B: the 03's own tail; A: its 04 leaf's head)."""
    hb = lambda n: np.asarray(ends_b[n][0], float)        # noqa: E731
    tb = lambda n: np.asarray(ends_b[n][1], float)        # noqa: E731
    ha = lambda n: np.asarray(heads_a[n], float)          # noqa: E731
    seg = []
    for f in HAND_FINGERS:
        seg.append((f"palm_{f}", hb("hand_l"), hb(f"{f}_01_l"), ha("hand_l"), ha(f"{f}_01_l")))
        for k in (1, 2, 3):
            nb = f"{f}_0{k}_l"
            seg.append((nb, hb(nb), hb(f"{f}_0{k + 1}_l") if k < 3 else tb(nb), ha(nb),
                        ha(f"{f}_0{k + 1}_l") if k < 3 else ha(f"{f}_04_leaf_l")))
    return seg


def seg_dist(P, h, t):
    """(distance to the segment h-t, the fraction along it, unclamped)."""
    d = t - h
    s = ((P - h) @ d) / max(float(d @ d), 1e-12)
    q = h + np.clip(s, 0.0, 1.0)[:, None] * d
    return np.linalg.norm(P - q, axis=1), s


def seg_maps(seg, PB, PA):
    """Each segment's map, B onto A: B's head on A's, B's axis turned onto A's (the least turn after the hand's own turn,
    so the digits keep the hand's roll), lengths by A's over B's; across the axis by A's girth over B's (the median
    distance of each rig's own points off its segment, its middle half; the palm's 1: a palm is not round)."""
    J_b = np.array([s[1] for s in seg] + [s[2] for s in seg])
    J_a = np.array([s[3] for s in seg] + [s[4] for s in seg])
    Rg, _ = kabsch(J_b, J_a)
    db = np.stack([seg_dist(PB, s[1], s[2])[0] for s in seg], 1)
    da = np.stack([seg_dist(PA, s[3], s[4])[0] for s in seg], 1)
    own_b, own_a = db.argmin(1), da.argmin(1)
    maps = []
    for k, (lab, bh, bt, ah, at) in enumerate(seg):
        ub, ua = bt - bh, at - ah
        lb, la = np.linalg.norm(ub), np.linalg.norm(ua)
        ub, ua = ub / lb, ua / la
        v = Rg @ ub
        ax = np.cross(v, ua)
        sn, cs = np.linalg.norm(ax), float(np.clip(v @ ua, -1, 1))
        if sn > 1e-9:
            ax /= sn
            K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]])
            R = np.eye(3) + sn * K + (1 - cs) * (K @ K)
        else:
            R = np.eye(3)
        R = R @ Rg
        g = 1.0
        if not lab.startswith("palm"):
            _, sb = seg_dist(PB, bh, bt)
            _, sa = seg_dist(PA, ah, at)
            mb = (own_b == k) & (sb > 0.25) & (sb < 0.75)
            ma = (own_a == k) & (sa > 0.25) & (sa < 0.75)
            if mb.sum() > 8 and ma.sum() > 8:
                g = float(np.median(da[ma, k]) / np.median(db[mb, k]))
        maps.append({"label": lab, "bh": bh, "ub": ub, "lb": lb, "ah": ah, "ua": ua, "la": la, "R": R, "g": g})
    return maps, own_a


def seg_apply(mp, P):
    """One segment's map on points P (see seg_maps)."""
    r = P - mp["bh"]
    along = r @ mp["ub"]
    radial = r - along[:, None] * mp["ub"]
    return mp["ah"] + (along * mp["la"] / mp["lb"])[:, None] * mp["ua"] + mp["g"] * (radial @ mp["R"].T)


def a_source(cfg, fit_spec):
    """A posed as the maps carry poses it (the fit's bones, her_a's a_rest chain at A's own rest), its normals the ones
    A's file stores, posed as Godot skins them (topo_bake.Source a_normals "file")."""
    import topo_bake
    mb = cfg.get("maps_bake", {})
    return topo_bake.Source(None, pose=fit_spec["bake"].get("pose"), a_rest=mb.get("a_rest", cfg.get("a_rest")),
                            a_normals="file")


def a_normals(cfg, z, Vt, M, src):
    """her_a "normals" (P1 R1 bake round 2): A's normals as its FILE stores them, at each of our vertices on the target
    surface Vt, so B's exported vertex normals can be A's where B lies on A (build_topo.her_a_normals) and the carried
    map holds only A's own detail. Why: B's points lie on A (p50 0.2-0.6 mm over the trunk and breasts) but B's own
    area-weighted normals there are B's facets over A's (edges 7 mm on both): against A's file normals they are p90 14,
    p99 35 deg off on the upper chest (73 where B's quads stand steep under the breast), and a map that carried that
    correction from one half lit the other half's different facets wrong (round 1: lumps, L/R p90 4.5-6.4 deg).
    Each vertex its own half's closest point on A (not a ray along B's normal: that normal is what is wrong), A's file
    normal interpolated there; the midline (z "side" 0, one vertex for both walls) the two walls' mean (x taken off).
    NW, the weight B's export gives A's normal: M (the her_a mask) * near (1 within near_mm[0] of A, 0 beyond
    near_mm[1]) * agree (cos(A's, B's) from agree_cos[0] to [1]: never the other sheet, e.g. the inner thigh's
    neighbour), relaxed over smooth_iters rings, mirror-averaged. NG: B's own normals of Vt (stages.vertex_normals on
    the quads' triangles, as the build's), the frame the build turns A's normal from when the built body is not Vt."""
    import stages as st
    import topo_uv as tu
    nc = cfg["normals"]
    Q = z["Q"]
    T = np.concatenate([Q[:, [0, 1, 2]], Q[:, [0, 2, 3]]])
    NG = st.vertex_normals(Vt, T)
    q, _, tri, d = src.surf.closest(Vt, k=16)
    a, b, c = (src.P[src.T[tri, k]] for k in range(3))
    w = np.clip(tu.bary(q, a, b, c), 0, None)
    w /= w.sum(1, keepdims=True)
    NA = src.sample(tri, w)["form"]
    fit = nc.get("fit")
    fit_stats = None
    if fit:
        # (fit {"sub": k, "lam": l}: the vertex normals whose linear blend over each of OUR triangles (what the game
        # interpolates) best matches A's file normal field there, least squares over k*k points per triangle (the
        # centroids of its k-fold subdivision, area-weighted), held to the point samples by lam (a share of the mean
        # diagonal). Point samples alone leave B's interpolation p90 1.4-2.6 deg off A's field over the chest and
        # torso, each half differently, and that per-half residual is what one shared texel cannot serve)
        k = int(fit["sub"])
        bc = np.array([((i + 1 / 3) / k, (j + 1 / 3) / k) for i in range(k) for j in range(k - i)] +
                      [((i + 2 / 3) / k, (j + 2 / 3) / k) for i in range(k) for j in range(k - i - 1)])
        bw = np.stack([1 - bc.sum(1), bc[:, 0], bc[:, 1]], 1)               # [s,3] barycentrics on (v0, v1, v2)
        ns = len(bw)
        X = np.einsum("sk,tkd->tsd", bw, Vt[T]).reshape(-1, 3)
        Nx = np.einsum("sk,tkd->tsd", bw, NG[T]).reshape(-1, 3)
        qs, _, ts_, ds = src.surf.closest(X, k=16)
        a2, b2, c2 = (src.P[src.T[ts_, j]] for j in range(3))
        ws = np.clip(tu.bary(qs, a2, b2, c2), 0, None)
        ws /= ws.sum(1, keepdims=True)
        As = src.sample(ts_, ws)["form"]
        area = 0.5 * np.linalg.norm(np.cross(Vt[T[:, 1]] - Vt[T[:, 0]], Vt[T[:, 2]] - Vt[T[:, 0]]), axis=1)
        sw = np.repeat(area / ns, ns) * ((As * Nx).sum(1) > 0)                 # (no sample from the other sheet)
        rows = np.repeat(np.arange(len(X)), 3)
        cols = np.repeat(T, ns, axis=0).ravel()
        Bm = sp.coo_matrix((np.tile(bw, (len(T), 1)).ravel(), (rows, cols)), shape=(len(X), len(Vt))).tocsr()
        BtB = (Bm.T @ sp.diags(sw) @ Bm).tocsr()
        lam = float(fit["lam"]) * float(BtB.diagonal().mean())
        import scipy.sparse.linalg as spl
        Am = (BtB + lam * sp.eye(len(Vt))).tocsc()
        rhs = Bm.T @ (sw[:, None] * As) + lam * NA
        lu = spl.splu(Am)
        NF = np.stack([lu.solve(rhs[:, j]) for j in range(3)], 1)
        NF /= np.maximum(np.linalg.norm(NF, axis=1, keepdims=True), 1e-12)
        def res(Nv):
            Ni = np.einsum("sk,tkd->tsd", bw, Nv[T]).reshape(-1, 3)
            Ni /= np.maximum(np.linalg.norm(Ni, axis=1, keepdims=True), 1e-12)
            return np.degrees(np.arccos(np.clip((Ni * As).sum(1), -1, 1)))
        r0, r1 = res(NA), res(NF)
        on_s = (sw > 0) & (ds < nc["near_mm"][0] * 1e-3)
        fit_stats = {"interp_vs_A_deg_p50_p90_p99_points": [round(float(x), 2) for x in np.percentile(r0[on_s], [50, 90, 99])],
                     "interp_vs_A_deg_p50_p90_p99_fit": [round(float(x), 2) for x in np.percentile(r1[on_s], [50, 90, 99])]}
        NA = NF
    mid = z["side"] == 0
    NA[mid, 0] = 0.0
    NA /= np.maximum(np.linalg.norm(NA, axis=1, keepdims=True), 1e-12)
    lo, hi = nc["near_mm"]
    near = 1.0 - smoothstep((d * 1e3 - lo) / (hi - lo))
    c0, c1 = nc["agree_cos"]
    agree = smoothstep(((NA * NG).sum(1) - c0) / (c1 - c0))
    NW = M * near * agree
    e = edges(Q)
    n = len(Vt)
    W = sp.coo_matrix((np.ones(2 * len(e)), (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])), shape=(n, n)).tocsr()
    deg = np.asarray(W.sum(1)).ravel()
    for _ in range(int(nc.get("smooth_iters", 2))):
        NW = np.minimum(NW, 0.5 * NW + 0.5 * (W @ NW) / np.maximum(deg, 1))     # (only eases down: no A normal off A)
    pr = mirror(z)
    NW = np.clip(0.5 * (NW + NW[pr]), 0.0, 1.0)
    ang = np.degrees(np.arccos(np.clip((NA * NG).sum(1), -1, 1)))
    on = NW > 0.99
    stats = {"on_A": int(on.sum()), "some": int((NW > 1e-3).sum()), "of": int(n),
             "dist_mm_p50_p90_on": [round(float(x), 2) for x in np.percentile(d[on] * 1e3, [50, 90])],
             "A_vs_B_deg_p50_p90_p99_on": [round(float(x), 2) for x in np.percentile(ang[on], [50, 90, 99])],
             **(fit_stats or {})}
    return {"N": NA.astype(np.float32), "NG": NG.astype(np.float32), "NW": NW.astype(np.float32),
            "P": Vt.astype(np.float32)}, stats


def a_joints(cfg, ar, hand=None):
    """The target's "joints" json: A's own joints at the pose its skin was taken in (her left; the skeleton mirrors). The
    girdle and arm skin are A's, so are their joints (keyed by landmark cube); and (her_a "a_joints", P1 R1 rig root) the
    trunk: B bone b's head at A bone a's ({b: a}, keyed "head:b"), where B's trunk is A's surface at A's rest (the target
    pose turns no trunk bone), so B's trunk joints are A's and the game turns B about A's points."""
    j = {c: [round(float(x), 6) for x in ar.t1["bones"][b][0]] for c, b in (
        ("joint-l-clavicle", "clavicle_l"), ("joint-l-shoulder", "upperarm_l"), ("joint-l-elbow", "lowerarm_l"), ("joint-l-hand", "hand_l"))}
    for b, a in (cfg.get("a_joints") or {}).items():
        if b != "why":
            j["head:" + b] = [round(float(x), 6) for x in ar.t1["heads"][a]]
    j.update(hand or {})          # (her_a "a_hand": the hand's and fingers' ends, ARest.hand_wrap)
    return np.array(json.dumps(j))


def joints_only(spec_path, tiers, out_dir, from_dir=None):
    """Re-writes only the targets' "joints" (a_joints above) from A posed as make() poses it: every other array is the
    file's own, unchanged (from_dir: the files read; default the designed slider's)."""
    spec = bt.with_defaults(load_spec(spec_path))
    cfg = spec["her_a"]
    ar = ARest(cfg)
    for tier in tiers:
        src = os.path.join(from_dir or TARGETS, OUT_FILE.format(tier=tier))
        z = dict(np.load(src))
        old = json.loads(str(z["joints"])) if "joints" in z else {}
        j = a_joints(cfg, ar, {k: v for k, v in old.items() if k.startswith(("ends:", "x:"))})   # (the hand's ends kept)
        z["joints"] = j
        z["about"] = np.array(str(z["about"]) + f" | joints: python tools/body/her_a_target.py --joints-only (a_joints {json.dumps({k: v for k, v in (cfg.get('a_joints') or {}).items() if k != 'why'})})")
        np.savez_compressed(os.path.join(out_dir, OUT_FILE.format(tier=tier)), **z)
        print(tier, "joints", json.loads(str(j)), flush=True)


def make(spec_path, tiers, out_dir=TARGETS):
    spec = bt.with_defaults(load_spec(spec_path))
    cfg = spec["her_a"]
    fit_spec = load_spec(os.path.join(REPO, cfg["fit_spec"]))
    A = Glb(os.path.join(REPO, spec["ref"]))
    baked = headbake.bake(A, ["HeroineHead"])
    zc = dict(np.load(os.path.join(HERE, "out", "topo", "close.npz")))
    Mc, _, _ = mask(zc, cfg)
    t = np.asarray(cfg.get("arm_move_m", [0, 0, 0]), float)
    ar = ARest(cfg) if cfg.get("a_rest") else None
    src = a_source(cfg, fit_spec) if cfg.get("normals") else None
    tight_d = None
    hand_d, hand_j, hand_ease = None, None, None
    if ar is not None:
        assert list(cfg.get("zero_parts", ())) == ["hand"] and cfg.get("zero_ring") is None and not np.any(t), \
            "a_rest: the arm and shoulder are the fit's (zero_parts [hand], zero_ring null, no arm_move_m)"
        print("a_rest", cfg["a_rest"], "A's turns", {k: v for k, v in ar.turns.items() if "arm" in k or "clav" in k or "hand" in k}, flush=True)
    for tier in tiers:
        V0, Vf, z = bodies(spec, fit_spec, tier, A, baked)
        ring = bt.boundary_ring(z["Q"], len(V0))
        M = Mc if tier == "close" else np.clip(carry_to_tier(Mc[:, None], "close", tier)[:, 0], 0.0, 1.0)
        M = np.where(M < 1e-3, 0.0, np.where(M > 1 - 1e-3, 1.0, M))
        if ar is None:
            ts = t[None, :] * np.stack([np.where(z["V"][:, 0] >= 0, 1.0, -1.0), np.ones(len(V0)), np.ones(len(V0))], 1)
        else:
            parts = list(map(str, z["parts"]))
            Vh = ar.hand_field(V0, Vf, z["part"] == parts.index("hand"), z["V"][:, 0])
            Vf, dist = ar.carry(Vf)
            ts = Vh - V0
            print(tier, "a_rest carry: fit to A p50/p95/max mm", np.round(np.percentile(dist, [50, 95, 100]) * 1e3, 2).tolist(), flush=True)
            if cfg.get("a_hand"):
                # (her_a "a_hand", P1 R1 round 28: our hand laid on A's, close first; play takes close's move)
                if tier == "close":
                    Vw, hand_ease, hand_j, hstats = ar.hand_wrap(Vh, z, cfg["a_hand"], baked["HeroineHead"]["P"])
                    hand_d = Vw - Vh
                    print(tier, "a_hand", json.dumps(hstats), flush=True)
                else:
                    assert hand_d is not None, "a_hand: close first (play takes close's move)"
                    hand_d = carry_to_tier(hand_d, "close", tier)
                    hand_ease = np.clip(carry_to_tier(hand_ease[:, None], "close", tier)[:, 0], 0.0, 1.0)
                ts = ts + hand_d
            if cfg.get("a_tight"):
                if tier == "close":
                    Vt, wt, stats = ar.tight(Vf, z, cfg["a_tight"])
                    tight_d = Vt - Vf
                    print(tier, "a_tight (lam, core p50, p95 mm, rejected):", stats, "points", int((wt > 1e-4).sum()), flush=True)
                else:
                    assert tight_d is not None, "a_tight: close first (play takes close's move)"
                    tight_d = carry_to_tier(tight_d, "close", tier)
                Vf = Vf + tight_d
        D = M[:, None] * (Vf - V0) + (1.0 - M[:, None]) * ts
        ring_max = float(np.abs(D[ring]).max())
        assert ring_max < 1e-4, ("the fit is not the head's on the ring", ring_max)
        D[ring] = 0.0
        about = (f"made_by: python tools/body/her_a_target.py {os.path.relpath(os.path.abspath(spec_path), REPO)}".replace("\\", "/") +
                 f" (fit {cfg['fit_spec']}, band_m {cfg['band_m']}, zero_parts {cfg.get('zero_parts', 'arm..hand')}, zero_ring {cfg.get('zero_ring')}, arm_move_m {list(t)}, a_rest {cfg.get('a_rest')})")
        extra = {}
        if ar is not None:
            extra["joints"] = a_joints(cfg, ar, hand_j)
        if src is not None:
            # (her_a "normals": A's file normals at the target surface, for the build's export; see a_normals)
            # (a_hand: the hand lies on A too, so A's normals there as on the trunk)
            nrm, stats = a_normals(cfg, z, V0 + D, M if hand_ease is None else np.maximum(M, hand_ease), src)
            extra.update(nrm)
            extra["normals_about"] = np.array(json.dumps({"normals": cfg["normals"], **stats}))
            about += f" normals {json.dumps({k: v for k, v in cfg['normals'].items() if k != 'why'})}"
            print(tier, "normals", stats, flush=True)
        np.savez_compressed(os.path.join(out_dir, OUT_FILE.format(tier=tier)), D=D.astype(np.float32), M=M.astype(np.float32),
                            topology=np.array(bt.topo_sha(z)), about=np.array(about), **extra)
        print(tier, "D max mm", round(float(np.linalg.norm(D, axis=1).max()) * 1e3, 1), "M<1", int((M < 1).sum()), "of", len(M), flush=True)


def maps(spec_path):
    """A's paint carried once: topo_bake on the carrier (the fit's build, on A) into base/targets/her_a_maps."""
    import topo_bake
    spec = load_spec(spec_path)
    cfg = spec["her_a"]
    fit = load_spec(os.path.join(REPO, cfg["fit_spec"]))
    work = os.path.join(HERE, "out", "her_a_maps_work")
    # (spec her_a "maps_bake", P1 R1 round 13: "carrier" a build whose surface is the target's (a published round: the
    # girdle and arm at A's rest are A's), "a_rest" A posed so (default her_a's a_rest), "mirror" and "form_near" as
    # topo_bake.run has them; without it the round 10 carry)
    mb = cfg.get("maps_bake", {})
    carrier = mb.get("carrier", cfg["carrier"])
    r, _ = topo_bake.run(os.path.join(REPO, carrier), work, size=int(fit["bake"].get("size", 2048)), pose=fit["bake"].get("pose"),
                         a_rest=mb.get("a_rest", cfg.get("a_rest")) if mb else None, mirror=mb.get("mirror", "avg"),
                         form_near=mb.get("form_near"), a_normals=mb.get("a_normals"), mirror_normal=mb.get("mirror_normal"),
                         ring_flat=mb.get("ring_flat_mm"))
    dest = os.path.join(TARGETS, "her_a_maps")
    os.makedirs(dest, exist_ok=True)
    for k in topo_bake.SOURCE_MAPS:
        shutil.copy2(os.path.join(work, f"{k}.png"), os.path.join(dest, f"{k}.png"))
    r = {k: r[k] for k in ("version", "size", "covered", "projection", "normal_inverted_texels", "normal_form", "mirror", "mirror_normal", "a_normals", "ring_flat_mm", "gates") if k in r}
    r["made_by"] = "tools/body/her_a_target.py --maps, from " + carrier + (" (her_a maps_bake " + json.dumps(mb) + ")" if mb else "")
    with open(os.path.join(dest, "bake.json"), "w") as f:
        json.dump(r, f, indent=1, default=float)
    print("maps", r["gates"]["pass"], r["projection"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--maps", action="store_true")
    ap.add_argument("--tiers", default="close,play")
    ap.add_argument("--out-dir", default=TARGETS, help="a trial's folder (the spec's \"target_files\" reads it); default the shipped base/targets")
    ap.add_argument("--joints-only", action="store_true", help="re-write only the targets' joints (her_a a_joints), every other array kept")
    ap.add_argument("--from-dir", default=None, help="--joints-only: the target files read (default the shipped base/targets)")
    a = ap.parse_args()
    os.makedirs(a.out_dir, exist_ok=True)
    if a.joints_only:
        joints_only(a.spec, a.tiers.split(","), a.out_dir, a.from_dir)
        return
    make(a.spec, a.tiers.split(","), a.out_dir)
    if a.maps:
        maps(a.spec)


if __name__ == "__main__":
    main()
