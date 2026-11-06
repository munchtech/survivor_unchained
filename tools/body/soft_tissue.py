"""Stage 6's soft-tissue solve for the hip (correctives.json joint "fold": "fem"; correctives.run picks it). P1 R5.

Why: four rounds of skinning plus a corrective (D, D2, r3 field, r4 membrane) never beat a cut line at 112-135 (judge E:
"a hard, dark, straight line ... nowhere does the belly roll over the thigh"): every one moved SKIN, a sheet, so what
the thigh pushed in had nowhere to go. Here the pelvis and both thighs are a VOLUME (the AAA route: a tissue solve baked
to correctives), so the tissue the flexing thigh presses is conserved and rolls up over the crease by itself.

  region   her rest skin round the hips cut by three planes (the trunk `top_m` above the hips, each thigh `cut` of
           its length down its own axis), the largest piece kept, each cut loop capped by a fan: a closed surface
  tets     TetGen (pyvista/tetgen 0.8, MIT wrapper of Hang Si's TetGen; an offline build tool, nothing of it ships)
           with the skin kept as it is (`nobisect`): the skin's points are the first nodes, so the solve's surface
           IS her mesh, no embedding
  bones    nodes rigid with a bone, by her own skeleton (shape-agnostic): each femur a capsule from the thigh's head
           to its calf head, `femur_r` round it, from `femur_from` down; the pelvis's core every trunk node deeper
           than `core_m` under the skin between the hips' level - `core_lo` and + `core_hi`; the cut caps and the skin
           within `cut_band` of a cut follow the skinning (X): the solve fades to the skin's own pose at its edges
  energy   co-rotational elasticity (per tet: |F - R|^2, R the polar rotation of F, the volume's weight) plus a
           near-incompressible volume term (|F - S|^2, S = F's singular values scaled to det 1, weight `vol_w`),
           projective dynamics (Bouaziz et al. 2014): local projections, a global solve with one sparse factor per
           contact set (the same matrix for x, y and z)
  contact  every skin node inside the region's posed closed surface (ray parity, embree) is pushed to its partner:
           the nearest point on the posed skin whose rest place is over `far_m` from it (not its own sheet folding),
           `margin` out along that face's normal; both sides, re-tested every `contact_every` iterations
  march    from the rest angle to the last key in `step` degree steps, each from the last one's result (quasi-static)
Output: [(deg, Y, f, free, M, G, log)] per key, Y the whole welded body (the skinning X off the region), as
contact_field.solve_chain gives it (correctives.run turns each into a rest-space shape, law "arc").
"""
from __future__ import annotations

import time

import numpy as np
import scipy.sparse as sp
from scipy.sparse.csgraph import connected_components
from scipy.sparse.linalg import splu
from scipy.spatial import cKDTree

import bends
import ray
from contact_fold import closest_on_tris
from correctives import key_pose, smooth01


# ------------------------------------------------------------------ region --
def _components(T, n):
    """Face components by shared edges."""
    e = np.concatenate([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]])
    f = np.tile(np.arange(len(T)), 3)
    key = np.sort(e, 1)
    k = key[:, 0].astype(np.int64) * n + key[:, 1]
    o = np.argsort(k)
    k, f = k[o], f[o]
    same = np.nonzero(k[1:] == k[:-1])[0]
    g = sp.coo_matrix((np.ones(len(same)), (f[same], f[same + 1])), shape=(len(T), len(T)))
    return connected_components(g, directed=False)[1]


def _loops(T):
    """The boundary loops of a face set (directed edges seen once), each as an ordered vertex list."""
    e = np.concatenate([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]])
    s = {(int(a), int(b)) for a, b in e}
    bd = [(a, b) for a, b in s if (b, a) not in s]
    nxt = {}
    for a, b in bd:
        nxt.setdefault(a, []).append(b)
    loops, seen = [], set()
    for a, _ in bd:
        if a in seen:
            continue
        lp, v = [], a
        while v not in seen:
            seen.add(v)
            lp.append(v)
            v = nxt[v][0]
        loops.append(lp)
    return loops


def region(mesh, st, cf):
    """The closed region round both hips: mesh node ids of its skin `sv`, the skin + cap triangles in local ids `F`,
    the cap centres (rest) `C`, and the per-skin-node cut it belongs to (-1 none)."""
    p = mesh.p
    I = p.index
    fr = st.fr
    sides = {}
    for s in ("l", "r"):
        o = p.rest[I[bends.bone(p, st.rig, "thigh", s)]][:3, 3]
        k = p.rest[I[bends.bone(p, st.rig, "calf", s)]][:3, 3]
        sides[s] = (o, bends.unit(k - o), float(np.linalg.norm(k - o)))
    mid = 0.5 * (sides["l"][0] + sides["r"][0])
    P0 = mesh.P0
    h = (P0 - mid) @ fr.up
    x = (P0 - mid) @ fr.lat
    keep = h < cf["top_m"]
    for s, (o, u, L) in sides.items():
        on = (x > 0) if s == "l" else (x < 0)
        keep &= ~(on & (((P0 - o) @ u) > cf["cut"] * L))
    keep &= ~mesh.held
    T = mesh.Tw
    T = T[keep[T].all(1)]
    comp = _components(T, mesh.n)
    # the piece that holds the hips (the hands and forearms hang below the cut as their own pieces)
    near = cKDTree(P0[T].mean(1)).query(mid)[1]
    T = T[comp == comp[near]]
    sv = np.unique(T)
    loc = -np.ones(mesh.n, np.int64)
    loc[sv] = np.arange(len(sv))
    F = loc[T]
    caps, C = [], []
    cut_of = -np.ones(len(sv), np.int64)
    V = P0[sv]
    for i, lp in enumerate(_loops(F)):
        lp = np.array(lp)
        c = V[lp].mean(0)
        ci = len(V) + len(C)
        C.append(c)
        nx = np.roll(lp, -1)
        caps.append(np.stack([nx, lp, np.full(len(lp), ci)], 1))   # the loop's edges reversed: the cap faces out
        cut_of[lp] = i
    F = np.concatenate([F] + caps)
    return sv, F, np.array(C), cut_of, sides, mid


def tetmesh(V, F, cf):
    import tetgen
    tg = tetgen.TetGen(V.astype(np.float64), F.astype(np.int32))
    nodes, tets, _, _ = tg.tetrahedralize(nobisect=True, quality=True, minratio=cf.get("minratio", 1.5),
                                          maxvolume=cf["tet_edge"] ** 3 / 8.48, fixedvolume=True, steinerleft=1_000_000, quiet=True)
    if not np.allclose(nodes[:len(V)], V, atol=1e-9):
        raise RuntimeError("tetgen moved the skin's points")
    return nodes, tets.astype(np.int64)


# ------------------------------------------------------------------- the FEM --
class Tets:
    """Linear tets on the rest nodes: the gradient operator (F = x[T]^T B per tet), rest volumes, the PD matrix."""

    def __init__(self, X0, T):
        D = np.transpose(X0[T[:, 1:]] - X0[T[:, [0]]], (0, 2, 1))
        bad = np.linalg.det(D) < 0
        T = T.copy()
        T[bad, 1], T[bad, 2] = T[bad, 2].copy(), T[bad, 1].copy()
        D = np.transpose(X0[T[:, 1:]] - X0[T[:, [0]]], (0, 2, 1))
        self.T = T
        self.vol = np.linalg.det(D) / 6.0
        Bi = np.linalg.inv(D)                                    # F = Ds @ Bi
        B = np.zeros((len(T), 4, 3))
        B[:, 1:, :] = Bi
        B[:, 0, :] = -Bi.sum(1)
        self.B = B
        m, n = len(T), len(X0)
        rows = np.broadcast_to((np.arange(m)[:, None, None] * 3 + np.arange(3)[None, None, :]), (m, 4, 3))
        cols = np.broadcast_to(T[:, :, None], (m, 4, 3))
        self.G = sp.csr_matrix((B.ravel(), (rows.ravel(), cols.ravel())), shape=(3 * m, n))

    def F(self, x):
        return np.einsum("tjc,tjk->tck", x[self.T], self.B)

    def matrix(self, w):
        return (self.G.T @ sp.diags(np.repeat(w, 3)) @ self.G).tocsr()

    def rhs(self, w, P):
        """sum_t w_t G_t^T P_t, per coordinate: [n,3]."""
        wr = np.repeat(w, 3)
        return np.stack([self.G.T @ (wr * P[:, c, :].ravel()) for c in range(3)], 1)


def rotation_fit(F, R, iters=3):
    """The rotation of each F, warm-started from the last one R (Mueller et al. 2016, "A robust method to extract
    the rotational part of deformations"): R turned by w = sum_i r_i x a_i / |sum_i r_i . a_i| until it settles.
    Robust under inversion (it never flips to a reflection) and ~20x faster than a batched SVD."""
    for _ in range(iters):
        w = np.cross(R[:, :, 0], F[:, :, 0]) + np.cross(R[:, :, 1], F[:, :, 1]) + np.cross(R[:, :, 2], F[:, :, 2])
        w /= (np.abs(np.einsum("tij,tij->t", R, F)) + 1e-9)[:, None]
        a = np.linalg.norm(w, axis=1)
        if a.max() < 1e-9:
            break
        k = w / np.maximum(a, 1e-12)[:, None]
        K = np.zeros((len(F), 3, 3))
        K[:, 0, 1], K[:, 0, 2], K[:, 1, 2] = -k[:, 2], k[:, 1], -k[:, 0]
        K[:, 1, 0], K[:, 2, 0], K[:, 2, 1] = k[:, 2], -k[:, 1], k[:, 0]
        s, c = np.sin(a)[:, None, None], np.cos(a)[:, None, None]
        Rot = np.eye(3)[None] + s * K + (1 - c) * (K @ K)
        R = Rot @ R
    return R


def sl3(s, iters=6):
    """The nearest det-1 singular values to s (min |s' - s|^2 with prod s' = 1; Newton on the constraint's linearization,
    the PD volume projection of Bouaziz et al. 2014). F / cbrt(det F) is NOT that: a near-flat tet's F scaled by up to 10x
    on every axis, a wild target that kept PD from settling (the energy rose and fell, a few nodes jumping 4-5 mm)."""
    D = np.zeros_like(s)
    for _ in range(iters):
        z = s + D
        C = z.prod(1) - 1.0
        g = np.stack([z[:, 1] * z[:, 2], z[:, 0] * z[:, 2], z[:, 0] * z[:, 1]], 1)
        D = (((g * D).sum(1) - C) / np.maximum((g * g).sum(1), 1e-12))[:, None] * g
    return s + D


def project_iso(F, R, cap=2.0):
    """The volume target as F grown or shrunk evenly to det 1 (S = F det^-1/3, the scale capped at `cap`), the sl3
    target where F is inverted. Not the nearest det-1 matrix (that one squeezes the crushed axis alone open, which in
    linear tets locks: a stiffer volume turned MORE tets over), but a pressure: a crushed tet pushes out on every side,
    so the tissue the thigh presses swells round the contact (the roll) instead of folding inside."""
    R, S = project_fast(F, R)
    d = np.linalg.det(F)
    ok = d > 0
    sc = np.minimum(np.cbrt(1.0 / np.maximum(d[ok], 1e-12)), cap)
    S[ok] = F[ok] * sc[:, None, None]
    return R, S


def project_fast(F, R):
    """The co-rotational target R (rotation_fit, warm-started: no SVD) and the volume target S: F's stretch R^T F on
    its own axes (eigh), singular values clamped to [0.05, 20] (an inverted or flat tet aims to open) then projected to
    det 1 (sl3)."""
    R = rotation_fit(F, R, iters=2)
    Sy = np.einsum("tji,tjk->tik", R, F)
    Sy = 0.5 * (Sy + np.transpose(Sy, (0, 2, 1)))
    w, Q = np.linalg.eigh(Sy)
    sp_ = sl3(np.clip(w, 0.05, 20.0))
    S = np.einsum("tij,tjk,tj,tlk->til", R, Q, sp_, Q)
    return R, S


def project(F):
    """The co-rotational target R (polar rotation) and the volume target S (det 1, same axes) of each F."""
    U, s, Vt = np.linalg.svd(F)
    neg = np.linalg.det(U @ Vt) < 0
    U[neg, :, 2] *= -1
    s = s.copy()
    s[neg, 2] *= -1                                     # inverted: the smallest axis flipped, R a rotation
    R = U @ Vt
    sa = np.maximum(np.abs(s), 1e-3)
    S = np.einsum("tij,tj,tjk->tik", U, sa / np.cbrt(sa.prod(1))[:, None], Vt)
    return R, S


def _closest(Y, Tc, Q, P0c, Q0, far_m, k=48, Nq=None, facing=None, faces=False):
    """Closest points on the posed faces Tc to Q among faces whose rest centre is over far_m from Q's rest place
    and, given the nodes' normals Nq, whose own normal faces the node's (n_face . n_node < facing: a fold's two lips
    face each other; the node's own sheet round it does not, so a small far_m is enough)."""
    A, B, C = Y[Tc[:, 0]], Y[Tc[:, 1]], Y[Tc[:, 2]]
    if facing is not None:
        nf = np.cross(B - A, C - A)
        nf /= np.maximum(np.linalg.norm(nf, axis=1, keepdims=True), 1e-18)
    _, cand = cKDTree((A + B + C) / 3).query(Q, k=min(k, len(Tc)))
    cand = cand.reshape(len(Q), -1)
    best = np.full(len(Q), np.inf)
    qb, fb = np.zeros_like(Q), np.zeros(len(Q), np.int64)
    bb = np.zeros_like(Q)
    for j in range(cand.shape[1]):
        t = cand[:, j]
        q, bc = closest_on_tris(Q, A[t], B[t], C[t])
        d = np.linalg.norm(Q - q, axis=1)
        m = (d < best) & (np.linalg.norm(P0c[t] - Q0, axis=1) > far_m)
        if facing is not None:
            m &= np.einsum("ij,ij->i", nf[t], Nq) < facing
        best[m], qb[m], fb[m], bb[m] = d[m], q[m], t[m], bc[m]
    n = np.cross(B[fb] - A[fb], C[fb] - A[fb])
    n = n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    if faces:
        return qb, n, np.isfinite(best), fb, bb
    return qb, n, np.isfinite(best)


def _pair_search(Y, Tc, Q, qi, ins, P0c, Q0, far_m, k, prism, reach_out):
    """Self-contact partners of any orientation (`pair_any`, R5 solver 2): past 100 deg every node the parity test put
    inside had a facing partner it sat OUTSIDE of (0-4.5 mm); each had gone under a face of its own sheet oriented its
    own way (n_face . n_node 0.6-1.0, rest 7-15 mm off: the crease apex tucked under its lips, a pleat), which the
    `facing` filter never sees. So: faces not touching the node with rest centre over far_m; an inside node takes the
    nearest face it is behind (the one it crossed), an outside node the nearest it is in front of within reach_out and
    inside the face's normal prism (sg >= prism * distance: a neighbour in the sheet's own plane is never a contact).
    Returns q, n, ok, face, barycentrics, sg."""
    A, B, C = Y[Tc[:, 0]], Y[Tc[:, 1]], Y[Tc[:, 2]]
    nf = np.cross(B - A, C - A)
    nf /= np.maximum(np.linalg.norm(nf, axis=1, keepdims=True), 1e-18)
    _, cand = cKDTree((A + B + C) / 3).query(Q, k=min(k, len(Tc)))
    cand = cand.reshape(len(Q), -1)
    best = np.full(len(Q), np.inf)
    qb, fb, bb, sb = np.zeros_like(Q), np.zeros(len(Q), np.int64), np.zeros_like(Q), np.zeros(len(Q))
    for j in range(cand.shape[1]):
        t = cand[:, j]
        q, bc = closest_on_tris(Q, A[t], B[t], C[t])
        d = np.linalg.norm(Q - q, axis=1)
        sg = np.einsum("ij,ij->i", Q - q, nf[t])
        m = (d < best) & (np.linalg.norm(P0c[t] - Q0, axis=1) > far_m) & ~(Tc[t] == qi[:, None]).any(1)
        m &= np.where(ins, sg < 0, (sg >= prism * d) & (sg < reach_out))
        best[m], qb[m], fb[m], bb[m], sb[m] = d[m], q[m], t[m], bc[m], sg[m]
    return qb, nf[fb], np.isfinite(best), fb, bb, sb


class Solve:
    """The region's tissue: tets, which nodes are held by what, and the march."""

    def __init__(self, mesh, st, jc, cf):
        t0 = time.time()
        p = mesh.p
        I = p.index
        self.mesh, self.st, self.cf = mesh, st, cf
        sv, F, Cc, cut_of, sides, mid = region(mesh, st, cf)
        self.sv, self.F, self.ns = sv, F, len(sv)
        Vs = np.concatenate([mesh.P0[sv], Cc])
        X0, T = tetmesh(Vs, F, cf)
        self.X0 = X0
        self.tets = Tets(X0, T)
        self.R = np.repeat(np.eye(3)[None], len(T), 0)          # each tet's last rotation (rotation_fit's warm start)
        n = len(X0)
        self.skinF = F[(F < self.ns).all(1)]
        self.P0c = X0[self.skinF].mean(1)
        up = st.fr.up
        # what holds each node: 0 free, 1 the skin's pose (the cut bands), 2 a femur, 3 the pelvis's core
        hold = np.zeros(n, np.int64)
        bone_of = -np.ones(n, np.int64)
        band = cf["cut_band"]
        h = (X0 - mid) @ up
        x = (X0 - mid) @ st.fr.lat
        hold[h > cf["top_m"] - band] = 1
        for s, (o, u, L) in sides.items():
            on = (x > 0) if s == "l" else (x < 0)
            hold[on & (((X0 - o) @ u) > cf["cut"] * L - band)] = 1
        depth, near = cKDTree(mesh.P0[sv]).query(X0)
        self.near_skin = sv[near]                        # each node's nearest skin node (its skin matrix at the bands)
        trunk = np.ones(n, bool)
        for s, (o, u, L) in sides.items():
            t = (X0 - o) @ u
            a = np.clip(t, cf["femur_from"], cf["cut"] * L)
            r = np.linalg.norm(X0 - (o + a[:, None] * u), axis=1)
            fm = (hold == 0) & (t > cf["femur_from"]) & (r < cf["femur_r"])
            hold[fm] = 2
            bone_of[fm] = I[bends.bone(p, st.rig, "thigh", s)]
            trunk &= ((X0 - o) @ bends.unit(up - u)) > -cf.get("core_lo", 0.0)
        # the pelvic floor: between the hips the bone ring (the pubic arch, the ischial tuberosities) reaches
        # `floor_lo` under the hips' level, so the perineum's deep tissue is the pelvis's, not a thigh's (judged by
        # its distance from the midline, inside `floor_w` of the half-way to each hip joint)
        hw = 0.5 * float(np.linalg.norm(sides["l"][0] - sides["r"][0]))
        floor = (np.abs(x) < cf.get("floor_w", 0.6) * hw) & (h > -cf.get("floor_lo", 0.07)) & \
            (depth > cf.get("floor_m", 0.02))
        # the core is the bony pelvis's: the iliac wings and the sacrum `core_from` over the hips' level, the floor
        # between the hips; never the hip joints' front (the iliopsoas and the femoral triangle are soft: a core
        # down to the joints' plane pinched the groin between it and the femur, 349 nodes crossing at 60 deg)
        joint = np.zeros(n, bool)
        for s_, (o, u, L) in sides.items():
            joint |= np.linalg.norm(X0 - o, axis=1) < cf.get("joint_r", 0.06)
        # `core_front`: the bony pelvis lies behind the lower belly; the abdomen in front of the hip joints' coronal plane
        # + core_front is soft (its viscera move), so the tissue the thigh presses there has somewhere to go
        fz = (X0 - mid) @ st.fr.front
        core = (hold == 0) & (np.arange(n) >= self.ns) & ~joint & (h < cf["core_hi"]) & \
            ((trunk & (depth > cf["core_m"]) & (h > cf.get("core_from", 0.04)) & (fz < cf.get("core_front", 9.0)))
             | floor)
        hold[core] = 3
        bone_of[core] = I[jc["proximal"].replace("{s}", st.s)]
        self.hold, self.bone_of = hold, bone_of
        self.free = np.nonzero(hold == 0)[0]
        self.fixed = np.nonzero(hold > 0)[0]
        # materials: the trunk's tissue mu 1, the thighs' `mu_thigh` (the thigh's muscle presses, the belly gives), by
        # each tet's rest centre on the thigh's side of the bisector plane between the trunk's up and that thigh's axis
        # (the check's seg_g rule); "vol_w" the volume's weight over the shape's
        vol = self.tets.vol
        cen = X0[self.tets.T].mean(1)
        mu = np.full(len(cen), cf.get("mu", 1.0))
        xc = (cen - mid) @ st.fr.lat
        for s_, (o, u, L) in sides.items():
            on = (xc > 0) if s_ == "l" else (xc < 0)
            mu[on & (((cen - o) @ bends.unit(up - u)) < 0)] = cf.get("mu_thigh", cf.get("mu", 1.0))
        self.mu = mu
        self.w_s = vol * mu
        self.w_v = vol * mu * cf["vol_w"]
        A = self.tets.matrix(self.w_s + self.w_v)
        # the skin's bending: each skin node's uniform Laplacian (over the skin's own edges) held to its rest one turned
        # by the tissue's local rotation (|L x - R_i L X0|^2, a PD bending term; Bouaziz et al. 2014): wrinkles at the
        # element's scale cost, one fold over the crease does not. Weight bend_w * h_i (h the node's edge length), so
        # it scales as the tets' vol * strain^2 does
        self.bend_w = cf.get("bend_w", 0.0)
        if self.bend_w > 0:
            ns = self.ns
            Fs = self.skinF
            e = np.concatenate([Fs[:, [0, 1]], Fs[:, [1, 2]], Fs[:, [2, 0]]])
            e = np.unique(np.sort(e, 1), axis=0)
            Ad = sp.coo_matrix((np.ones(2 * len(e)), (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])),
                               shape=(ns, n)).tocsr()
            deg = np.asarray(Ad.sum(1)).ravel()
            Ls = (sp.diags(1.0 / deg) @ Ad).tocsr()
            Ls = (sp.eye(ns, n, format="csr") - Ls).tocsr()
            ln = np.linalg.norm(X0[e[:, 0]] - X0[e[:, 1]], axis=1)
            hs = np.zeros(ns)
            np.add.at(hs, e[:, 0], ln)
            np.add.at(hs, e[:, 1], ln)
            hs /= deg
            self.Ls, self.wb = Ls, self.bend_w * hs
            self.d0 = Ls @ X0
            A = (A + Ls.T @ sp.diags(self.wb) @ Ls).tocsr()
            ti = np.repeat(np.arange(len(T)), 4)
            tn = self.tets.T.ravel()
            m_ = tn < ns
            cnt = np.bincount(tn[m_], minlength=ns).astype(float)
            self.avgR = sp.csr_matrix((1.0 / cnt[tn[m_]], (tn[m_], ti[m_])), shape=(ns, len(T)))
        self.A_bend = (A - self.tets.matrix(self.w_s + self.w_v)).tocsr() if self.bend_w > 0 else None
        # the patch volume (`cvol_w`): linear tets lock when each must keep its own volume (a stiffer per-tet volume
        # turned MORE of them over), so the tissue's volume is also kept per patch: the tets binned by rest centre in
        # `cvol_cell` cubes, each patch's nodes held to their own spread about the patch's centre scaled evenly by
        # (V0 / V)^(1/3) (a crushed patch swells on every side: the displaced tissue goes where the skin is free, the
        # roll). PD form: w |P x - s P x|^2 per patch, P the centring projector (a clique in the matrix)
        self.cvol_w = cf.get("cvol_w", 0.0)
        if self.cvol_w > 0:
            cell = cf.get("cvol_cell", 0.03)
            key = np.floor(cen / cell).astype(np.int64)
            _, cl = np.unique(key, axis=0, return_inverse=True)
            cl = cl.ravel()
            self.cl_tet = cl
            nC = int(cl.max()) + 1
            pr = np.unique(np.stack([np.repeat(cl, 4), self.tets.T.ravel()], 1), axis=0)   # (patch, node) pairs
            self.cl_c, self.cl_n = pr[:, 0], pr[:, 1]
            cnt = np.bincount(self.cl_c, minlength=nC).astype(float)
            V0c = np.bincount(cl, weights=vol, minlength=nC)
            self.cl_V0 = V0c
            xb = np.stack([np.bincount(self.cl_c, weights=X0[self.cl_n, k], minlength=nC) for k in range(3)], 1) / cnt[:, None]
            r2 = np.bincount(self.cl_c, weights=((X0[self.cl_n] - xb[self.cl_c]) ** 2).sum(1), minlength=nC) / cnt
            wC = self.cvol_w * V0c / np.maximum(cnt * r2, 1e-12)            # per node: the tissue's vol / h^2 scale
            self.cl_w, self.cl_cnt = wC, cnt
            # the matrix: w (I - 11^T / n) on each patch's nodes
            rows, cols, vals = [], [], []
            order = np.argsort(self.cl_c, kind="stable")
            starts = np.r_[0, np.cumsum(cnt.astype(int))]
            for c in range(nC):
                nn = self.cl_n[order[starts[c]:starts[c + 1]]]
                m = len(nn)
                rows.append(np.repeat(nn, m))
                cols.append(np.tile(nn, m))
                vals.append(wC[c] * (np.eye(m) - 1.0 / m).ravel())
            Ac = sp.coo_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), shape=(n, n)).tocsr()
            A = (A + Ac).tocsr()
            self.A_bend = (self.A_bend + Ac).tocsr() if self.A_bend is not None else Ac
            self.log_cl = {"patches": nC, "patch_nodes_mean": round(float(cnt.mean()), 1)}
        self.w_v0 = self.w_v.copy()
        self.boost = np.zeros(len(T), bool)
        self.diag = A.diagonal()
        self._build(A)
        self.log = {"skin_nodes": int(self.ns), "nodes": int(n), "tets": int(len(T)), "free": int(len(self.free)),
                    "femur": int((hold == 2).sum()), "core": int((hold == 3).sum()), "band": int((hold == 1).sum()),
                    "min_vol_mm3": round(float(vol.min() * 1e9), 4), "setup_s": round(time.time() - t0, 1),
                    **getattr(self, "log_cl", {})}

    def held_pos(self, X, M, G):
        """Where the held nodes are at this pose: the skin's pose at the bands (X on the skin, the nearest skin
        node's blended matrix inside), the bones' rigid motion on the femurs and the core."""
        p = self.mesh.p
        X0 = self.X0
        out = np.zeros((len(X0), 3))
        k = self.fixed
        hd = self.hold[k]
        b = k[hd == 1]
        skin = b < self.ns
        out[b[skin]] = X[self.sv[b[skin]]]
        bi = b[~skin]
        Mi = M[self.mesh.first[self.near_skin[bi]]]
        out[bi] = np.einsum("nij,nj->ni", Mi[:, :3, :3], X0[bi]) + Mi[:, :3, 3]
        for code in (2, 3):
            kk = k[hd == code]
            for j in np.unique(self.bone_of[kk]):
                m = kk[self.bone_of[kk] == j]
                S = G[j] @ p.skel.ibm[j]
                out[m] = X0[m] @ S[:3, :3].T + S[:3, 3]
        return out

    def skinned(self, M):
        """Every node by the skinning carried into the volume: each node's matrix the blend of its `init_k` nearest
        skin nodes' (inverse square distance), so neighbours start alike and no tet starts inverted."""
        if not hasattr(self, "_iw"):
            d, k = cKDTree(self.mesh.P0[self.sv]).query(self.X0, k=self.cf.get("init_k", 12))
            w = 1.0 / (d + 0.004) ** 2
            self._iw, self._ik = w / w.sum(1, keepdims=True), self.mesh.first[self.sv[k]]
        Mb = np.einsum("nk,nkij->nij", self._iw, M[self._ik])
        return Mb, np.einsum("nij,nj->ni", Mb[:, :3, :3], self.X0) + Mb[:, :3, 3]

    def _build(self, A=None):
        """The global matrix's free and free-fixed blocks; the volume weight `inv_k` times over on the boosted tets."""
        if A is None:
            self.w_v = self.w_v0 * (1.0 + self.cf.get("inv_k", 0.0) * self.boost)
            A = self.tets.matrix(self.w_s + self.w_v)
            if self.A_bend is not None:
                A = (A + self.A_bend).tocsr()
        self.Aff = A[self.free][:, self.free].tocsc()
        self.Afd = A[self.free][:, self.fixed].tocsc()
        self.lu_key, self.lu = None, None

    def factor(self, key, wc):
        if self.lu_key != key:
            self.lu = splu((self.Aff + sp.diags(wc)).tocsc())
            self.lu_key = key
        return self.lu

    def contacts(self, x, prev):
        """The skin nodes inside the posed region (and last round's contacts still within `release`): targets."""
        cf = self.cf
        ns = self.ns
        sc = ray.scene(x, self.F)
        Q = x[:ns]
        N = bends.normals(Q, self.skinF)
        ins = ray.inside(sc, Q + 3e-4 * N)
        cand = np.nonzero(ins | prev)[0]
        cand = cand[self.hold[cand] == 0]
        if not len(cand):
            self._cnq = np.zeros((0, 3))
            return cand, np.zeros((0, 3)), ins
        q, nq, ok = _closest(x, self.skinF, Q[cand], self.P0c, self.X0[cand], cf["far_m"], Nq=N[cand],
                             facing=cf.get("facing"))
        s = np.einsum("ij,ij->i", Q[cand] - q, nq)
        # an inside node's partner must have it on its inner side (s < 0 by a hair); a touching one stays held
        keep = ok & ((ins[cand] & (s < 1e-4)) | (~ins[cand] & (s < cf["release"]))) &             (np.linalg.norm(Q[cand] - q, axis=1) < cf["reach"])
        cand, q, nq, s = cand[keep], q[keep], nq[keep], s[keep]
        # both skins of a contact are pushed: each node `share` of the way to the other skin (the other side's
        # nodes take the rest, so the two meet between, not swap through each other), then the margin out
        sh = np.where(s < 0, cf.get("share", 0.5), 1.0)[:, None]
        self._cnq = nq                                  # the partner's outward normal (method "nh": a one-sided plane)
        # `touch_margin`: a touching node's (outside, within `release`) plane offset. Both skins of a touch each held
        # `margin` out of the other walked apart forever under one-sided planes (each re-found plane 0.8 mm past the
        # other side's new place: the contact set never settled); "nh" sets 0, the plane at the partner's skin
        mg = np.where(s < 0, cf["margin"], cf.get("touch_margin", cf["margin"]))[:, None]
        return cand, Q[cand] + sh * (q - Q[cand]) + mg * nq, ins

    def local(self, x, cn, tgt, wc):
        """The local step at x: the per-tet targets P, the right-hand side (free rows), and the energy at x."""
        F = self.tets.F(x)
        if self.cf.get("svd"):
            R, S = project(F)
        elif self.cf.get("iso"):
            R, S = project_iso(F, self.R, self.cf["iso"])
            self.R = R
        else:
            R, S = project_fast(F, self.R)
            self.R = R
        ws, wv = self.w_s, self.w_v
        E = float((ws * ((F - R) ** 2).sum((1, 2))).sum() + (wv * ((F - S) ** 2).sum((1, 2))).sum())
        wsum = ws + wv
        P = (ws[:, None, None] * R + wv[:, None, None] * S) / wsum[:, None, None]
        b = self.tets.rhs(wsum, P)
        if self.bend_w > 0:
            Ri = (self.avgR @ R.reshape(len(R), 9)).reshape(-1, 3, 3)
            U_, _, Vt_ = np.linalg.svd(Ri)
            Ri = U_ @ Vt_
            t = np.einsum("nij,nj->ni", Ri, self.d0)
            E += float((self.wb * ((self.Ls @ x - t) ** 2).sum(1)).sum())
            b = b + self.Ls.T @ (self.wb[:, None] * t)
        if self.cvol_w > 0:
            vt = np.linalg.det(F) * self.tets.vol
            nC = len(self.cl_V0)
            Vc = np.bincount(self.cl_tet, weights=vt, minlength=nC)
            sc = np.cbrt(np.clip(self.cl_V0 / np.maximum(Vc, 1e-12 * self.cl_V0), *self.cf.get("cvol_clamp", (0.8, 1.25))))
            xb = np.stack([np.bincount(self.cl_c, weights=x[self.cl_n, k], minlength=nC) for k in range(3)], 1) / self.cl_cnt[:, None]
            d = x[self.cl_n] - xb[self.cl_c]
            pc = (sc[self.cl_c] * self.cl_w[self.cl_c])[:, None] * d
            b = b + np.stack([np.bincount(self.cl_n, weights=pc[:, k], minlength=len(x)) for k in range(3)], 1)
            E += float((self.cl_w[self.cl_c] * (((1 - sc[self.cl_c])[:, None] * d) ** 2).sum(1)).sum())
            self.vol_ratio = float(Vc.sum() / self.cl_V0.sum())
        b = b[self.free] - self._bd
        if len(cn):
            pc = self._pos[cn]
            b[pc] += wc[pc, None] * tgt
            E += float((wc[pc] * ((x[cn] - tgt) ** 2).sum(1)).sum())
        return b, E

    def step(self, x, X, M, G, log):
        """Projective dynamics to rest at this pose, Anderson-accelerated (Peng et al. 2018, "Anderson acceleration for
        geometry optimization and physics simulation": AA(m) on the local-global map, an AA iterate kept only if it
        lowers the energy, else the plain PD step taken and the history cleared). `aa` 0: plain PD (+ Chebyshev rho)."""
        cf = self.cf
        fx = self.held_pos(X, M, G)
        x = x.copy()
        x[self.fixed] = fx[self.fixed]
        self._bd = self.Afd @ x[self.fixed]
        pos = -np.ones(len(x), np.int64)
        pos[self.free] = np.arange(len(self.free))
        self._pos = pos
        prev = np.zeros(self.ns, bool)
        cn, tgt = np.zeros(0, np.int64), np.zeros((0, 3))
        wc = np.zeros(len(self.free))
        dx = 0.0
        rho = cf.get("rho", 0.0)
        am = int(cf.get("aa", 0))
        xm1, om, k_ch = None, 1.0, 0
        Gh, Fh = [], []                                          # AA history: the map's values and residuals
        E_acc, g_acc, n_rej = np.inf, None, 0
        it = 0
        for it in range(int(cf["iters"])):
            if it % int(cf["contact_every"]) == 0:
                cn0 = cn
                cn, tgt, ins = self.contacts(x, prev)
                prev = np.zeros(self.ns, bool)
                prev[cn] = True
                wc = np.zeros(len(self.free))
                if len(cn):
                    wc[pos[cn]] = cf["contact"] * self.diag[cn]
                changed = False
                if cf.get("inv_k", 0) > 0:
                    # tets crushed or turned inside out get a stiffer volume (refactored when the set grows): ARAP's
                    # energy is finite through inversion, so a compressed groin turned its tets over (3.4k at 135 deg,
                    # 2 L lost) instead of pushing the tissue out; the set only grows over the march
                    J = np.linalg.det(self.tets.F(x))
                    nb = self.boost | (J < cf.get("inv_j", 0.5))
                    if nb.sum() > self.boost.sum():
                        self.boost = nb
                        self._build()
                        self._bd = self.Afd @ x[self.fixed]
                        changed = True
                if changed or len(cn) != len(cn0) or (cn != cn0).any() or it == 0:
                    xm1, om, k_ch = None, 1.0, 0            # the problem changed: restart the acceleration
                    Gh, Fh, E_acc, g_acc = [], [], np.inf, None
            b, E = self.local(x, cn, tgt, wc)
            if it == 0:
                log["inv0"] = int((np.linalg.det(self.tets.F(x)) < 0).sum())
            if am and g_acc is not None and E > E_acc:
                # the AA iterate raised the energy: take the plain PD step from the last accepted point instead
                n_rej += 1
                x[self.free] = g_acc
                Gh, Fh = [], []
                b, E = self.local(x, cn, tgt, wc)
            E_acc = E
            lu = self.factor(tuple(cn.tolist()), wc)
            cur = x[self.free].copy()
            g = np.stack([lu.solve(b[:, c]) for c in range(3)], 1)
            dx = float(np.abs(g - cur).max())
            if cf.get("trace") and log.get("deg", 0) >= cf["trace"] and it % 5 == 4:
                d_ = np.abs(g - cur).max(1)
                k_ = self.free[int(np.argmax(d_))]
                print(f"      it {it} E {E:.6e} dx {dx*1000:.3f} p99 {np.percentile(d_, 99)*1000:.3f} at node {k_} "
                      f"skin {k_ < self.ns} rej {n_rej}", flush=True)
            if (it > (2 if pair and inc else cf["contact_every"])) and dx < cf["tol"]:
                x[self.free] = g
                break
            if am:
                f = (g - cur).ravel()
                Gh.append(g.ravel().copy())
                Fh.append(f)
                if len(Gh) > am + 1:
                    Gh.pop(0)
                    Fh.pop(0)
                g_acc = g
                if len(Fh) > 1:
                    dF = np.stack([Fh[i + 1] - Fh[i] for i in range(len(Fh) - 1)], 1)
                    dG = np.stack([Gh[i + 1] - Gh[i] for i in range(len(Gh) - 1)], 1)
                    gam = np.linalg.lstsq(dF, f, rcond=None)[0]
                    xf = (g.ravel() - dG @ gam).reshape(-1, 3)
                else:
                    xf = g
            else:
                xf = g
                # Chebyshev semi-iterative acceleration (Wang 2015): rho the local-global map's spectral radius
                if rho > 0 and k_ch >= cf.get("cheb_delay", 3) and xm1 is not None:
                    om = 2.0 / (2.0 - rho * rho) if k_ch == cf.get("cheb_delay", 3) else 4.0 / (4.0 - rho * rho * om)
                    xf = om * (xf - xm1) + xm1
                xm1 = cur
                k_ch += 1
            x[self.free] = xf
        cn, tgt, ins = self.contacts(x, np.zeros(self.ns, bool))
        J = np.linalg.det(self.tets.F(x))
        vl = self.tets.vol
        log.update(iters=it + 1, last_dx_mm=round(dx * 1000, 3), contacts=int(len(cn)), inside=int(ins.sum()),
                   aa_rejects=n_rej, dvol_cm3=round(float(((J - 1) * vl).sum() * 1e6)),
                   dvol_neg_cm3=round(float((np.minimum(J - 1, 0) * vl).sum() * 1e6)), inverted=int((J < 0).sum()),
                   J_p1=round(float(np.percentile(J, 1)), 3), boosted=int(self.boost.sum()))
        if self.cf.get("diag") and (J < 0).any():
            fr = self.st.fr
            Bf = np.stack([fr.up, fr.front, fr.lat]).T
            iv = J < 0
            c = (self.X0[self.tets.T[iv]].mean(1) - self.st.O) @ Bf * 1000
            log.update(inv_at=np.round(np.percentile(c, [10, 50, 90], 0)).astype(int).tolist(),
                       inv_held=round(float((self.hold[self.tets.T[iv]] > 0).any(1).mean()), 2),
                       inv_skin=round(float((self.tets.T[iv] < self.ns).any(1).mean()), 2),
                       inv_thigh=round(float((self.mu[iv] != 1.0).mean()), 2))
        return x

    # ------------------------------------------------------------ method "nh": a hyperelastic minimum, not PD --
    def nh_energy(self, x, grad=True):
        """Stable Neo-Hookean (Smith et al. 2018, the form without the log term): per tet vol mu [(|F|^2 - 3) / 2 +
        lam / 2 (J - a)^2], a = 1 + 1 / lam (rest-stable), `lam` = lambda / mu (10: Poisson 0.45). Defined and restoring
        through inversion (an inverted tet's J term pushes it back open), and its volume is a pressure, so a crushed
        groin swells round the contact. Why not PD's volume targets (R5 lead 2, 6 Nov): the nearest-det-1 target
        (sl3) converges but crumples the femoral triangle (90 deg: 51 inside, 579 tets inverted, 0.5 L lost); the even
        swelling target (`iso`) is not a projection, so PD never settles under it (dx 1-3 mm after 200 iterations at
        48 deg with no contact at all): e10's roll was a snapshot of a solve still moving. Returns E, grad [n,3], J."""
        lam = self.cf.get("lam", 10.0)
        a = 1.0 + 1.0 / lam
        F = self.tets.F(x)
        c0 = np.cross(F[:, :, 1], F[:, :, 2])
        c1 = np.cross(F[:, :, 2], F[:, :, 0])
        c2 = np.cross(F[:, :, 0], F[:, :, 1])
        J = np.einsum("tc,tc->t", F[:, :, 0], c0)
        w = self.tets.vol * self.mu
        E = float((w * (0.5 * ((F * F).sum((1, 2)) - 3.0) + 0.5 * lam * (J - a) ** 2)).sum())
        # `j_min` (R5 lead 3): an inversion barrier, 1/2 j_k lam (j_min - J)^2 under j_min (C1, zero above): the
        # stable NH's own J term is only quadratic, so a crease pressed hard still crushes its tets through (74
        # inverted at 135 in g2) and the skin row on them dives under its own lips (the self-fold's inside nodes)
        jm = self.cf.get("j_min", 0.0)
        dJ = lam * (J - a)
        if jm > 0:
            u = np.maximum(jm - J, 0.0)
            kb = self.cf.get("j_k", 10.0) * lam
            E += float((w * 0.5 * kb * u * u).sum())
            dJ = dJ - kb * u
        fr_ = getattr(self, "_flip_r", None)
        if fr_ is not None:
            # `flip_k` (R5 lead 3): the skin's fold-over barrier. Each skin face's area vector a_f = (b - a) x (c - a)
            # against its rest normal turned by the skinning (r_f, the blend of its corners' matrices): s = a_f . r_f /
            # |a0_f| is its projected area ratio, and s < flip_c costs 1/2 k |a0| h (flip_c - s)^2. A crease's lips turn
            # at most half the flex from the blend (cos 67 deg = 0.4 at 135), so a true fold costs nothing; the
            # crease apex's element-scale overfold (its own faces turned against its normal, ndot -0.9: the check's
            # deep 'inside' row at 135, sitting 0.3 mm under its own 2-ring) does. Linear in each corner: exact gradient
            Fs = self.skinF
            A_, B_, C_ = x[Fs[:, 0]], x[Fs[:, 1]], x[Fs[:, 2]]
            sv_ = np.einsum("fc,fc->f", np.cross(B_ - A_, C_ - A_), fr_) / self._flip_a0
            u = np.maximum(self.cf.get("flip_c", 0.0) - sv_, 0.0)
            kf = self._flip_w
            E += float((0.5 * kf * u * u).sum())
            if grad:
                gs = (-kf * u / self._flip_a0)[:, None]                  # dE/ds / |a0|
                gb = np.cross(C_ - A_, fr_) * gs
                gc = np.cross(fr_, B_ - A_) * gs
                gf = np.zeros_like(x)
                np.add.at(gf, Fs[:, 1], gb)
                np.add.at(gf, Fs[:, 2], gc)
                np.add.at(gf, Fs[:, 0], -(gb + gc))
        if not grad:
            return E, None, J
        P = F + dJ[:, None, None] * np.stack([c0, c1, c2], 2)      # dPsi/dF (the cofactor is dJ/dF)
        gt = self.tets.rhs(w, P)
        return E, (gt + gf if fr_ is not None else gt), J

    def pairs(self, x):
        """`contact_model` "pair" (method "nh"): node-face pairs, the energy's own. Every skin node with a facing
        partner face (far_m, facing as contacts()) either inside the region and behind that face, or outside and within
        `c_reach` of it, is paired with the face's closest point (its barycentrics) and the face's normal, both frozen
        till the next refresh. The gap s(x) = (x_i - sum_k b_k x_tk) . n is linear in x, so the penalty
        1/2 k min(s - c_gap, 0)^2 is one C1 convex energy over BOTH sides (the node and the face's three nodes share the
        push by their own stiffness; no target re-found from a moving partner, no `share`), evaluated at every
        line-search point. Why (R5 solver 2, 6 Nov): the plane targets were re-found from the partner's last place and
        only for nodes already inside, so past 100 deg the active set chattered (40-50 refreshes, dx 0.4-1.25 mm) and
        6 nodes stayed inside with no plane at 90 deg. Returns dict(i, tri, b, n, k) or None."""
        cf = self.cf
        ns = self.ns
        Q = x[:ns]
        N = bends.normals(Q, self.skinF)
        ins = ray.inside(ray.scene(x, self.F), Q + 3e-4 * N)
        allq = np.arange(ns)
        # `c_k` face candidates per node: a node deep in a fold has its own sheet's faces nearest; 48 (contacts())
        # found no partner at all for most of the inside nodes
        if cf.get("pair_any"):
            q, nq, ok, fb, bc, sg = _pair_search(x, self.skinF, Q, allq, ins, self.P0c, self.X0[:ns],
                                                 cf.get("pair_far_m", 0.004), int(cf.get("c_k", 64)),
                                                 cf.get("prism", 0.8), cf.get("c_reach", 0.004))
        else:
            q, nq, ok, fb, bc = _closest(x, self.skinF, Q, self.P0c, self.X0[:ns], cf["far_m"], k=int(cf.get("c_k", 48)),
                                         Nq=N, facing=cf.get("facing"), faces=True)
            sg = np.einsum("ij,ij->i", Q - q, nq)
        d = np.linalg.norm(Q - q, axis=1)
        keep = ok & (d < cf["reach"]) & ((ins & (sg < 0)) | (~ins & (sg >= 0) & (sg < cf.get("c_reach", 0.004))))
        tri = self.skinF[fb[keep]]
        i = allq[keep]
        anyfree = (self.hold[i] == 0) | (self.hold[tri] == 0).any(1)
        i, tri, b, n = i[anyfree], tri[anyfree], bc[keep][anyfree], nq[keep][anyfree]
        k = cf["contact"] * np.maximum(self.diag_h0[i], (b * b * self.diag_h0[tri]).sum(1))
        fz = self.hold[:ns] == 0
        self._pairs_log = {"pairs": int(len(i)), "pairs_inside": int((ins[i]).sum()), "ins": int(ins.sum()),
                           "ins_nopart": int((ins & ~ok).sum()), "ins_out": int((ins & ok & (sg >= 0)).sum()),
                           "ins_far": int((ins & ok & (sg < 0) & (d >= cf["reach"])).sum()),
                           "ins_held": int((ins & ~fz).sum())}
        return dict(i=i, tri=tri, b=b, n=n, k=k, f=fb[keep][anyfree], ins=ins[i])

    @staticmethod
    def pair_gap(xv, PR):
        p = np.einsum("kj,kjc->kc", PR["b"], xv[PR["tri"]])
        return np.einsum("kc,kc->k", xv[PR["i"]] - p, PR["n"])

    def pair_phi(self, xv, PR):
        """Each skin node's deepest pair penalty displacement min(s - c_gap, 0) (0 with no pair)."""
        ph = np.zeros(self.ns)
        if PR is not None and len(PR["i"]):
            np.minimum.at(ph, PR["i"], np.minimum(self.pair_gap(xv, PR) - self.cf.get("c_gap", 0.0005), 0.0))
        return ph

    def pair_h0(self, PR, n):
        """The pairs' active terms as a scalar matrix (k a a^T, a = e_i - sum b_k e_tk), the H0's contact part."""
        if PR is None or not len(PR["i"]):
            return sp.csr_matrix((n, n))
        idx = np.concatenate([PR["i"][:, None], PR["tri"]], 1)
        c = np.concatenate([np.ones((len(idx), 1)), -PR["b"]], 1)
        v = PR["k"][:, None, None] * c[:, :, None] * c[:, None, :]
        r = np.repeat(idx[:, :, None], 4, 2)
        return sp.coo_matrix((v.ravel(), (r.ravel(), np.transpose(r, (0, 2, 1)).ravel())), shape=(n, n)).tocsr()

    def step_nh(self, x, X, M, G, log):
        """The pose's hyperelastic rest: min over the free nodes of nh_energy + the skin's smoothness against the
        skinning (1/2 smooth_w h |L x - L X|^2 over the skin's Laplacian: the solve's offset from LBS stays smooth, so
        no element-scale wrinkle) + the contacts' penalty (1/2 w |x - target|^2, re-found every `contact_every`).
        L-BFGS with the prefactored Laplacian-type matrix as its initial Hessian and an Armijo line search (Liu,
        Bouaziz, Kavan 2017, "Quasi-Newton methods for real-time simulation of hyperelastic materials"): every
        iterate lowers a true energy, so the march converges (`tol` the last step's largest move)."""
        cf = self.cf
        fr = self.free
        fx = self.held_pos(X, M, G)
        x = x.copy()
        x[self.fixed] = fx[self.fixed]
        pos = -np.ones(len(x), np.int64)
        pos[fr] = np.arange(len(fr))
        lam = cf.get("lam", 10.0)
        dref, wb = None, None
        if self.bend_w > 0:
            xr = np.zeros_like(x)
            xr[:self.ns] = X[self.sv]
            dref = self.Ls @ xr
            if cf.get("bend_ref") == "rest":
                # R5 lead 3: the skin's rest Laplacian turned by each node's blended skinning matrix (Mb L X0), not the
                # skinning's own Laplacian (L X_lbs): where the blend changes fast across the crease, L X_lbs carries
                # the skinning's element-scale pleat (the gradient of Mb times X0), and the smoothness kept it
                Mb, _ = self.skinned(M)
                d0 = np.asarray(self.d0)[:self.ns]
                dref = np.einsum("nij,nj->ni", Mb[:self.ns, :3, :3], d0)
            wb = cf.get("smooth_w", self.bend_w) * self.wb / self.bend_w
        self._flip_r = None
        if cf.get("flip_k", 0) > 0:
            Fs = self.skinF
            n0 = np.cross(self.X0[Fs[:, 1]] - self.X0[Fs[:, 0]], self.X0[Fs[:, 2]] - self.X0[Fs[:, 0]])
            a0 = np.linalg.norm(n0, axis=1)
            Mb, _ = self.skinned(M)
            Rf = Mb[Fs, :3, :3].mean(1)
            r = np.einsum("fij,fj->fi", Rf, n0 / a0[:, None])
            self._flip_r = r / np.linalg.norm(r, axis=1, keepdims=True)
            self._flip_a0 = a0
            h = np.sqrt(a0)
            self._flip_w = cf["flip_k"] * float(np.mean(self.mu)) * 0.5 * a0 * h
        if getattr(self, "_h0", None) is None:
            A = self.tets.matrix(self.tets.vol * self.mu * cf.get("h0_k", 1.0 + lam / 3.0))
            if wb is not None:
                A = A + self.Ls.T @ sp.diags(wb) @ self.Ls
            A = A.tocsr()
            self._h0 = (A[fr][:, fr].tocsc(), A.diagonal())
            self._h0_key, self._h0_lu = None, None
        Hff, Hd = self._h0
        self.diag_h0 = Hd
        pair = cf.get("contact_model") == "pair"
        c_gap = cf.get("c_gap", 0.0005)
        PR, Hc, x_pr = None, None, None
        inc = bool(cf.get("pair_inc", 0))
        pid = getattr(self, "_pid", 0)
        self._akey = None

        def total(xv, cn, tgt, wc):
            E, g, J = self.nh_energy(xv)
            if dref is not None:
                r = self.Ls @ xv - dref
                E += 0.5 * float((wb * (r * r).sum(1)).sum())
                g = g + self.Ls.T @ (wb[:, None] * r)
            if len(cn):
                # a one-sided plane through each target, on the partner's normal: a node pushed out of its partner
                # is held from going back in but never pulled on (a two-sided pull to a target re-found every few
                # iterations kept the deep fold chattering: E rising at each refresh, dx 2.5 mm at 300 iterations)
                ph = np.minimum(np.einsum("ij,ij->i", xv[cn] - tgt, nq), 0.0)
                E += 0.5 * float((wc[pos[cn]] * ph * ph).sum())
                g[cn] += (wc[pos[cn]] * ph)[:, None] * nq
            if PR is not None and len(PR["i"]):
                ph = np.minimum(self.pair_gap(xv, PR) - c_gap, 0.0)
                E += 0.5 * float((PR["k"] * ph * ph).sum())
                f = (PR["k"] * ph)[:, None] * PR["n"]
                np.add.at(g, PR["i"], f)
                for c_ in range(3):
                    np.add.at(g, PR["tri"][:, c_], -PR["b"][:, c_, None] * f)
            return E, g[fr], J

        prev = np.zeros(self.ns, bool)
        cn, tgt = np.zeros(0, np.int64), np.zeros((0, 3))
        wc = np.zeros(len(fr))
        ccd = bool(cf.get("ccd", 0))
        if ccd:
            # `ccd` (R5 lead 3): the skin never passes through itself. The 135 deep rows of every run so far were a
            # LOCAL self-crossing: the crease apex's sheet pushed through its own 2-3 rings (4-14 mm at rest, facing
            # the same way: no pair or plane sees it), its patch then enclosed (+N runs 66-150 mm inside the body).
            # A line-search step is accepted only if it adds no skin edge-through-face crossing (each skin edge a
            # ray, its hits on faces that share no corner with it), so the march, crossing-free at 60 deg, can lower
            # the count and never raise it
            Fs_ = self.skinF
            if not hasattr(self, "_ccd_e"):
                self._ccd_e = skin_edges(Fs_)
            Es = self._ccd_e

            bad_cur = skin_crossings(x[:self.ns], Fs_, Es)[0]
            log["cross0"] = int(bad_cur.sum())
            nblk = 0
        nq = np.zeros((0, 3))
        Sh, Yh = [], []
        m_h = int(cf.get("lbfgs_m", 8))
        cap = cf.get("max_move", 0.005)
        dx, it, nls, E = np.inf, 0, 0, None
        J0 = np.linalg.det(self.tets.F(x))
        log["inv0"] = int((J0 < 0).sum())
        settle = bool(cf.get("settle", 0))
        refresh, t0_, nref = False, None, 0
        for it in range(int(cf["iters"])):
            moved = pair and x_pr is not None and cf.get("c_move") and                 float(np.abs(x[:self.ns] - x_pr).max()) > cf["c_move"]
            if pair and (PR is None or refresh or moved or (not inc and it % int(cf["contact_every"]) == 0)):
                # `c_move`: pairs looked for again whenever a skin node moved over c_move since the last look (a node
                # crosses a face it is not paired with only by moving further than c_reach: with a refresh every 30
                # iterations, nodes crossed unpaired faces between and came back inside 7 mm deep, 101 deg never
                # settled). `pair_inc` (R5 solver 2): those looks only ADD the outside nodes' new pairs (zero or
                # near-zero energy where found, so the energy never jumps), and the full re-pair at the solve's rest
                # keeps each inside node's last pair while it is still behind that face (hysteresis): re-pairing
                # every node at every look (c_move alone) chattered, dx at the 2 mm cap after 600 iterations at 94 deg
                PR0 = PR
                new_ = self.pairs(x)
                if PR is None or not inc:
                    PR = new_
                elif not refresh:
                    have = set(zip(PR["i"].tolist(), PR["f"].tolist()))
                    m_ = ~new_["ins"] & np.array([(a_, b_) not in have for a_, b_ in
                                                  zip(new_["i"].tolist(), new_["f"].tolist())], bool)
                    PR = {k_: np.concatenate([PR[k_], new_[k_][m_]]) for k_ in PR}
                else:
                    ko = PR0["ins"] & (self.pair_gap(x, PR0) < 0)
                    m_ = ~(new_["ins"] & np.isin(new_["i"], PR0["i"][ko]))
                    PR = {k_: np.concatenate([PR0[k_][ko], new_[k_][m_]]) for k_ in PR0}
                x_pr = x[:self.ns].copy()
                nref += 1
                ph0 = self.pair_phi(x, PR0)
                ph1 = self.pair_phi(x, PR)
                if E is None or ((ph0 < 0) != (ph1 < 0)).any():
                    Sh, Yh = [], []
                E, g, J = total(x, cn, tgt, wc)
                # active-only H0 part (a pair at rest out of reach adds no stiffness); refactored only when that
                # active set changes
                PA = None
                if len(PR["i"]):
                    a_ = self.pair_gap(x, PR) < c_gap + cf.get("h0_reach", 0.001)
                    PA = {k_: v_[a_] for k_, v_ in PR.items()}
                akey = (PA["i"] * 10_000_000 + PA["f"]).tobytes() if PA is not None else b""
                if akey != getattr(self, "_akey", None):
                    self._akey = akey
                    pid += 1
                    Hc = self.pair_h0(PA, len(x))[fr][:, fr]
                if refresh:
                    # settled: re-paired at the solve's rest, every node's penalty displacement within settle_mm
                    refresh = False
                    dph = float(np.abs(ph1 - ph0).max()) if len(ph0) else 0.0
                    log["dph_mm"] = round(dph * 1000, 3)
                    if dph < cf.get("settle_mm", 0.05) * 1e-3:
                        log["settled"] = it
                        break
            elif not pair and (it % int(cf["contact_every"]) == 0 or refresh):
                cn0, tgt0 = cn, tgt
                cn, tgt, ins = self.contacts(x, prev)
                nref += 1
                nq = self._cnq
                prev = np.zeros(self.ns, bool)
                prev[cn] = True
                wc = np.zeros(len(fr))
                if len(cn):
                    wc[pos[cn]] = cf["contact"] * Hd[cn]
                if E is None or len(cn) != len(cn0) or (cn != cn0).any():
                    Sh, Yh = [], []
                # always re-evaluated: the same nodes' targets moved with their partners, and a stale E, g made the
                # line search fail (a stall at 94 deg, one contact node holding g 2.3)
                E, g, J = total(x, cn, tgt, wc)
                if refresh:
                    # `settle`: the planes were re-found after the solve settled on the last ones; the same nodes on
                    # planes within `settle_mm` of the last: the contact set is settled too, done
                    same = len(cn) == len(cn0) and (cn == cn0).all() and                         (not len(cn) or float(np.abs(tgt - tgt0).max()) < cf.get("settle_mm", 0.05) * 1e-3)
                    refresh = False
                    if same:
                        log["settled"] = it
                        break
            key = ("pair", id(self), pid) if pair else tuple(cn.tolist())
            if self._h0_key != key:
                self._h0_lu = splu((Hff + Hc).tocsc() if pair else (Hff + sp.diags(wc)).tocsc())
                self._h0_key = key
            lu = self._h0_lu
            q = g.copy()
            al = []
            for s_, y_ in zip(reversed(Sh), reversed(Yh)):
                r_ = 1.0 / float((y_ * s_).sum())
                a_ = r_ * float((s_ * q).sum())
                q -= a_ * y_
                al.append((r_, a_))
            z = np.stack([lu.solve(q[:, c]) for c in range(3)], 1)
            for (s_, y_), (r_, a_) in zip(zip(Sh, Yh), reversed(al)):
                z += s_ * (a_ - r_ * float((y_ * z).sum()))
            d = -z
            gd = float((g * d).sum())
            if gd >= 0:
                Sh, Yh = [], []
                d = -np.stack([lu.solve(g[:, c]) for c in range(3)], 1)
                gd = float((g * d).sum())
            t = min(1.0, cap / max(float(np.abs(d).max()), 1e-12))
            x0f = x[fr].copy()
            while True:
                x[fr] = x0f + t * d
                E1, g1, J1 = total(x, cn, tgt, wc)
                if E1 <= E + 1e-4 * t * gd:
                    if not ccd:
                        break
                    bad_n, hf_n = skin_crossings(x[:self.ns], Fs_, Es)
                    new_ = bad_n & ~bad_cur
                    if not new_.any():
                        bad_cur = bad_n
                        break
                    # the active set: a new crossing's nodes (its edge's, its face's) take no move this iteration and
                    # the rest go on (halving the whole step for them stalled every step past 112 in 5-20 iterations)
                    nd = np.unique(np.r_[Es[new_].ravel(), Fs_[hf_n[new_]].ravel()])
                    pz = pos[nd]
                    pz = pz[pz >= 0]
                    if len(pz) and np.abs(d[pz]).max() > 0:
                        d[pz] = 0.0
                        gd = float((g * d).sum())
                        nblk += len(pz)
                        if gd < 0:
                            continue
                    E1 = np.inf                      # a step that crosses the skin through itself: shorter
                t *= 0.5
                nls += 1
                if t < 1e-5:
                    if not Sh:
                        break                        # the plain H0 step fails too: a true stall, stop here
                    Sh, Yh = [], []                  # a stale history: restart from the H0 direction
                    d = -np.stack([lu.solve(g[:, c]) for c in range(3)], 1)
                    gd = float((g * d).sum())
                    t = min(1.0, cap / max(float(np.abs(d).max()), 1e-12))
            if E1 > E + 1e-4 * t * gd:
                x[fr] = x0f
                log["stalled"] = it
                break
            s = x[fr] - x0f
            y = g1 - g
            if float((s * y).sum()) > 1e-16:
                Sh.append(s)
                Yh.append(y)
                if len(Sh) > m_h:
                    Sh.pop(0)
                    Yh.pop(0)
            dx = float(np.abs(s).max())
            E, g, J = E1, g1, J1
            if cf.get("trace") and log.get("deg", 0) >= cf["trace"] and it % 10 == 9:
                print(f"      it {it} E {E:.6e} dx {dx*1000:.3f} |g| {np.abs(g).max():.3e} t {t:.3g} ls {nls}", flush=True)
            if it > cf["contact_every"] and dx < cf["tol"]:
                if not settle:
                    break
                refresh = True                       # settled on these planes: re-find them, stop if they hold
        if pair:
            ph = self.pair_phi(x, PR)
            log.update(getattr(self, "_pairs_log", {}), pen_max_mm=round(-float(ph.min()) * 1000, 3) if len(ph) else 0.0)
            self._pid = pid + 1                      # the next step's first pairing refactors
        if ccd:
            log["cross"] = int(bad_cur.sum())
            log["ccd_blocked"] = nblk
        cn, tgt, ins = self.contacts(x, np.zeros(self.ns, bool))
        J = np.linalg.det(self.tets.F(x))
        vl = self.tets.vol
        log.update(iters=it + 1, last_dx_mm=round(dx * 1000, 3), contacts=int(len(cn)), inside=int(ins.sum()),
                   backtracks=nls, refreshes=nref, g_max=float(np.abs(g).max()), dvol_cm3=round(float(((J - 1) * vl).sum() * 1e6)),
                   dvol_neg_cm3=round(float((np.minimum(J - 1, 0) * vl).sum() * 1e6)), inverted=int((J < 0).sum()),
                   J_p1=round(float(np.percentile(J, 1)), 3))
        if cf.get("diag"):
            # where the unsettled force sits: the free nodes with the largest gradient, their rest place (up, front,
            # lat mm from the hip joint), skin or deep, in a contact, and how far the nearest held node is (mm)
            gn = np.linalg.norm(g, axis=1)
            top = np.argsort(-gn)[:12]
            nd = fr[top]
            Bf = np.stack([self.st.fr.up, self.st.fr.front, self.st.fr.lat]).T
            dh, _ = cKDTree(self.X0[self.fixed]).query(self.X0[nd])
            for k_, n_ in zip(top, nd):
                print(f"      g {gn[k_]:.3e} node {n_} skin {n_ < self.ns} cn {n_ in set(cn.tolist())} rest "
                      f"{np.round((self.X0[n_] - self.st.O) @ Bf * 1000).astype(int).tolist()} held_mm "
                      f"{dh[list(nd).index(n_)] * 1000:.0f} hold_near {self.hold[self.fixed][_[list(nd).index(n_)]]}", flush=True)
            Ji = np.nonzero(J < 0)[0]
            if len(Ji):
                c = (self.X0[self.tets.T[Ji]].mean(1) - self.st.O) @ Bf * 1000
                print(f"      inverted at p10/50/90 {np.round(np.percentile(c, [10, 50, 90], 0)).astype(int).tolist()} "
                      f"touch held {float((self.hold[self.tets.T[Ji]] > 0).any(1).mean()):.2f}", flush=True)
        return x


def skin_edges(Fs):
    e = np.concatenate([Fs[:, [0, 1]], Fs[:, [1, 2]], Fs[:, [2, 0]]])
    return np.unique(np.sort(e, 1), axis=0)


def skin_crossings(Q, Fs, Es, eps=1e-5):
    """The skin's self-crossings (R5 lead 3, `ccd`): each edge of Es cast as a ray over its length, a hit on a face of
    Fs that shares no corner with it (past up to 3 incident-face hits). Returns (edge mask, the hit face per edge)."""
    sc = ray.scene(Q, Fs)
    a, b = Q[Es[:, 0]], Q[Es[:, 1]]
    L = np.linalg.norm(b - a, axis=1)
    d = (b - a) / np.maximum(L, 1e-12)[:, None]
    o = a + eps * d
    bad = np.zeros(len(Es), bool)
    hf = -np.ones(len(Es), np.int64)
    for _ in range(3):
        pid, tf = ray.hits(sc, o, d)
        hit = (pid >= 0) & (tf < L - 2 * eps)
        if not hit.any():
            break
        f = Fs[np.maximum(pid, 0)]
        inc = (f == Es[:, :1]).any(1) | (f == Es[:, 1:]).any(1)
        new = hit & ~inc & ~bad
        hf[new] = pid[new]
        bad |= hit & ~inc
        go = hit & inc
        if not go.any():
            break
        o = np.where(go[:, None], o + (tf[:, None] + eps) * d, o)
        L = np.where(go, L - tf - eps, 0.0)
    return bad, hf


def solve_chain(mesh, st, jc, cf):
    S_ = Solve(mesh, st, jc, cf)
    print(f"    fem setup {S_.log}", flush=True)
    keys = [float(k[1]) for k in jc["keys"]]
    a0 = st.rest_deg
    march = sorted(set([round(float(v), 3) for v in np.arange(a0 + cf["step"], keys[-1], cf["step"])] + keys))
    x, Mb0 = None, None
    out = {}
    free_w = np.zeros(mesh.n, bool)
    free_w[S_.sv] = True
    for th in march:
        t = time.time()
        V, G = key_pose(st, th)
        X = V[mesh.first]
        M = mesh.skin_mats(G)
        # each step starts from the skinning carried into the volume plus the last step's own offset from it, carried
        # through the change of each node's blended matrix (a quasi-static march: the held nodes never jump alone)
        Mb, xs = S_.skinned(M)
        if cf.get("init_prev"):
            # the last step's own result, the held nodes' move carried into the free ones by the tissue's own matrix
            # (one linear solve: x_f += -Aff^-1 Afd dx_held). The skinning carried in (below) starts the crease's tets
            # turned over (187 at 18 deg, 4k at 135), and ARAP keeps a tet it is given inverted
            if x is None:
                x = S_.X0.copy()
            fx = S_.held_pos(X, M, G)
            dfix = fx[S_.fixed] - x[S_.fixed]
            x = x.copy()
            x_prev0 = x.copy()
            if cf.get("init_prev") != 2:
                lu0 = S_.factor((), np.zeros(len(S_.free)))
                rhs = -(S_.Afd @ dfix)
                x[S_.free] += np.stack([lu0.solve(rhs[:, c]) for c in range(3)], 1)
            # init_prev 2 (R5 lead 3, with `ccd`): the free nodes start where the last step left them and only the
            # held ones move (the cut bands and the femur, far from the crease): the linear carry crossed the crease's
            # skin through itself before the solve began (176 crossing edges at 112), which the guard can only keep
            x[S_.fixed] = fx[S_.fixed]
            if cf.get("ccd") and cf.get("init_prev") != 2:
                # `ccd`'s init (R5 lead 3): the linear carry crossed the crease's skin through itself before the
                # solve (10-176 crossing edges at 101-112), which the guard can only keep. The nodes of each NEW
                # crossing (its edge, its face) and their skin ring take half their carry, until none is new
                Fs_ = S_.skinF
                if not hasattr(S_, "_ccd_e"):
                    S_._ccd_e = skin_edges(Fs_)
                Es = S_._ccd_e
                x_old = x_prev0
                bad0, _ = skin_crossings(x_old[:S_.ns], Fs_, Es)
                car = x[:S_.ns] - x_old[:S_.ns]
                if not hasattr(S_, "_ring"):
                    S_._ring = sp.coo_matrix((np.ones(2 * len(Es)), (np.r_[Es[:, 0], Es[:, 1]], np.r_[Es[:, 1], Es[:, 0]])),
                                             shape=(S_.ns, S_.ns)).tocsr()
                frac = np.ones(S_.ns)
                for _ in range(12):
                    bad, hf = skin_crossings(x[:S_.ns], Fs_, Es)
                    new_ = bad & ~bad0
                    if not new_.any():
                        break
                    nd = np.zeros(S_.ns, bool)
                    nd[Es[new_].ravel()] = True
                    nd[Fs_[hf[new_]].ravel()] = True
                    nd |= (S_._ring @ nd.astype(float)) > 0
                    nd &= S_.hold[:S_.ns] == 0
                    frac[nd] *= 0.5
                    x[:S_.ns] = x_old[:S_.ns] + frac[:, None] * car
                S_._lg_init = {"init_new_cross": int((bad & ~bad0).sum()), "init_lag": int((frac < 1).sum())}
            xs = x
        elif x is not None:
            dev = np.einsum("nji,nj->ni", Mb0[:, :3, :3], x - xs0)          # into rest space (rotation part)
            xs = xs + np.einsum("nij,nj->ni", Mb[:, :3, :3], dev)
        x = xs
        Mb0 = Mb
        lg = {"deg": th}
        lg.update(getattr(S_, "_lg_init", {}))
        x = (S_.step_nh if cf.get("method") == "nh" else S_.step)(x, X, M, G, lg)
        xs0 = S_.skinned(M)[1]
        Y = X.copy()
        Y[S_.sv] = x[:S_.ns]
        lg["max_move_mm"] = round(float(np.linalg.norm(Y - X, axis=1).max() * 1000), 1)
        lg["s"] = round(time.time() - t, 1)
        print(f"    fem {th:6.1f}: {lg}", flush=True)
        if any(abs(th - k) < 1e-6 for k in keys):
            out[round(th, 3)] = (Y.copy(), np.ones(mesh.n), free_w.copy(), M, G, {"march": dict(lg, fem=S_.log)})
    S_.last = x
    solve_chain.last = S_
    return [(k,) + out[round(k, 3)] for k in keys]
