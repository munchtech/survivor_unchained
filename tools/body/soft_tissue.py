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


def project_fast(F, R):
    """project() without the SVD: R by rotation_fit; S = F / cbrt(det F) (the det-1 target on F's own axes, which is
    U diag(s / cbrt(prod s)) V^T exactly), R itself where F is inverted or flat."""
    R = rotation_fit(F, R, iters=2)
    d = np.linalg.det(F)
    ok = d > 1e-3
    S = R.copy()
    S[ok] = F[ok] / np.cbrt(d[ok])[:, None, None]
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


def _closest(Y, Tc, Q, P0c, Q0, far_m, k=48, Nq=None, facing=None):
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
    for j in range(cand.shape[1]):
        t = cand[:, j]
        q, _ = closest_on_tris(Q, A[t], B[t], C[t])
        d = np.linalg.norm(Q - q, axis=1)
        m = (d < best) & (np.linalg.norm(P0c[t] - Q0, axis=1) > far_m)
        if facing is not None:
            m &= np.einsum("ij,ij->i", nf[t], Nq) < facing
        best[m], qb[m], fb[m] = d[m], q[m], t[m]
    n = np.cross(B[fb] - A[fb], C[fb] - A[fb])
    return qb, n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12), np.isfinite(best)


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
        core = (hold == 0) & (np.arange(n) >= self.ns) & ~joint & (h < cf["core_hi"]) & \
            ((trunk & (depth > cf["core_m"]) & (h > cf.get("core_from", 0.04))) | floor)
        hold[core] = 3
        bone_of[core] = I[jc["proximal"].replace("{s}", st.s)]
        self.hold, self.bone_of = hold, bone_of
        self.free = np.nonzero(hold == 0)[0]
        self.fixed = np.nonzero(hold > 0)[0]
        # materials: one tissue for now (cf "mu" 1, "vol_w" the volume's weight over it)
        vol = self.tets.vol
        self.w_s = vol * cf.get("mu", 1.0)
        self.w_v = vol * cf.get("mu", 1.0) * cf["vol_w"]
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
        self.Aff = A[self.free][:, self.free].tocsc()
        self.Afd = A[self.free][:, self.fixed].tocsc()
        self.diag = A.diagonal()
        self.lu_key, self.lu = None, None
        self.log = {"skin_nodes": int(self.ns), "nodes": int(n), "tets": int(len(T)), "free": int(len(self.free)),
                    "femur": int((hold == 2).sum()), "core": int((hold == 3).sum()), "band": int((hold == 1).sum()),
                    "min_vol_mm3": round(float(vol.min() * 1e9), 4), "setup_s": round(time.time() - t0, 1)}

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
        return cand, Q[cand] + sh * (q - Q[cand]) + cf["margin"] * nq, ins

    def step(self, x, X, M, G, log):
        cf = self.cf
        fx = self.held_pos(X, M, G)
        x = x.copy()
        x[self.fixed] = fx[self.fixed]
        bd = self.Afd @ x[self.fixed]
        pos = -np.ones(len(x), np.int64)
        pos[self.free] = np.arange(len(self.free))
        prev = np.zeros(self.ns, bool)
        cn, tgt = np.zeros(0, np.int64), np.zeros((0, 3))
        ws, wv = self.w_s, self.w_v
        wsum = ws + wv
        dx = 0.0
        rho = cf.get("rho", 0.0)
        xm1, om, k_ch = None, 1.0, 0
        for it in range(int(cf["iters"])):
            if it % cf["contact_every"] == 0:
                cn0 = cn
                cn, tgt, ins = self.contacts(x, prev)
                prev = np.zeros(self.ns, bool)
                prev[cn] = True
                if len(cn) != len(cn0) or (cn != cn0).any():
                    xm1, om, k_ch = None, 1.0, 0            # the problem changed: restart the acceleration
            if cf.get("svd"):
                R, S = project(self.tets.F(x))
            else:
                R, S = project_fast(self.tets.F(x), self.R)
                self.R = R
            P = (ws[:, None, None] * R + wv[:, None, None] * S) / wsum[:, None, None]
            b = self.tets.rhs(wsum, P)
            if self.bend_w > 0:
                Ri = (self.avgR @ R.reshape(len(R), 9)).reshape(-1, 3, 3)
                U_, _, Vt_ = np.linalg.svd(Ri)
                Ri = U_ @ Vt_
                b = b + self.Ls.T @ (self.wb[:, None] * np.einsum("nij,nj->ni", Ri, self.d0))
            b = b[self.free] - bd
            wc = np.zeros(len(self.free))
            if len(cn):
                wc[pos[cn]] = cf["contact"] * self.diag[cn]
                b[pos[cn]] += wc[pos[cn], None] * tgt
            lu = self.factor(tuple(cn.tolist()), wc)
            xf = np.stack([lu.solve(b[:, c]) for c in range(3)], 1)
            # Chebyshev semi-iterative acceleration (Wang 2015, "A Chebyshev semi-iterative approach for
            # accelerating projective and position-based dynamics"): rho the local-global map's spectral radius
            cur = x[self.free].copy()
            if rho > 0 and k_ch >= cf.get("cheb_delay", 3) and xm1 is not None:
                om = 2.0 / (2.0 - rho * rho) if k_ch == cf.get("cheb_delay", 3) else 4.0 / (4.0 - rho * rho * om)
                xf = om * (xf - xm1) + xm1
            xm1 = cur
            k_ch += 1
            dx = float(np.abs(xf - cur).max())
            x[self.free] = xf
            if it > cf["contact_every"] and dx < cf["tol"]:
                break
        cn, tgt, ins = self.contacts(x, np.zeros(self.ns, bool))
        log.update(iters=it + 1, last_dx_mm=round(dx * 1000, 3), contacts=int(len(cn)), inside=int(ins.sum()))
        return x


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
        if x is not None:
            dev = np.einsum("nji,nj->ni", Mb0[:, :3, :3], x - xs0)          # into rest space (rotation part)
            xs = xs + np.einsum("nij,nj->ni", Mb[:, :3, :3], dev)
        x = xs
        Mb0 = Mb
        lg = {"deg": th}
        x = S_.step(x, X, M, G, lg)
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
