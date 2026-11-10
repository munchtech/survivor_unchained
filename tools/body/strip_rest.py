"""Strip rest: re-lay a band of a mesh's REST that bridges a fold of the reference onto the reference's rest surface.

A PROTOTYPE for an owner decision (may her body B's rest change in the hidden strip of the armpit?). Nothing here is
published or wired into a build.

Where a mesh spans the mouth of a fold that its reference keeps as a groove (carried_target's bridges), no target
carried from the reference can be right in an opened pose: the bridge takes the opening, or a fill spans the hollow.
The cure at the source is rest skin: the band around the bridges is laid INTO the reference's groove.

    r = relay(P0, edges, tris, band, bridge, face, bary, ref_V0, ref_T)      # r["P1"]: the new rest points

1. The reference's patch under the band is unfolded flat (Unfold: a least-squares conformal map, scaled to its area).
2. The fold's apex line: on each bridge's path across the unfolded groove, the point whose normal is as far from one
   mouth's as from the other's; a low-degree curve through those points (Curve).
3. The band's row on one side of the bridges goes ONTO the apex line (an edge that straddles the apex keeps a rest
   chord shorter than its path, and tears like a bridge; an edge from the apex up a wall does not).
4. Every other band point keeps the mesh's own layout: least squares on the edge vectors of the unfolded rest feet
   (the bridging edges ask for their rest length only), weights 1 / rest length, so each row takes the same share of
   the new skin. The band's neighbours stay where they are.
5. Back onto the surface: foot + height along the reference's smooth normal. Heights are interpolated from the band's
   neighbours and cut wherever another part of the reference would be closer than the foot (inside a groove), so a
   closest-point correspondence built on the new rest finds the same feet.
Vertex order, every point outside the band and the band's neighbours are untouched.

The top is the general core (arrays in, arrays out). The bottom is HER CONFIG and the CLI:

    python tools/body/strip_rest.py build  [--snap] [--rows N]   # out/shoulder/strip_rest.npz + the rest proof
    python tools/body/strip_rest.py target [--snap] [--poses a,b] # today's fill | the target on B', per pose
    python tools/body/strip_rest.py sheet  [--snap]              # out/shoulder/sheets/strip_owner.png (+ _half.jpg)

--snap: import carried_target from out/shoulder/snap (a frozen copy) instead of the live module.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import scipy.sparse as sp
from scipy.optimize import minimize
from scipy.sparse.csgraph import connected_components, dijkstra
from scipy.sparse.linalg import splu, spsolve
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
if "--snap" in sys.argv:
    sys.path.insert(0, str(HERE / "out/shoulder/snap"))
import carried_target as ct  # noqa: E402
import region_target as rt  # noqa: E402


# ============================================================================================ the general core ==
def lscm(P, tri):
    """(uv [n, 2], flipped triangles) of the least-squares conformal map of triangles tri [m, 3] over points P [n, 3],
    scaled to the mesh's area, the triangles' winding kept."""
    n, m = len(P), len(tri)
    a, e1, e2 = P[tri[:, 0]], P[tri[:, 1]] - P[tri[:, 0]], P[tri[:, 2]] - P[tri[:, 0]]
    l1 = np.linalg.norm(e1, axis=1)
    x = e1 / l1[:, None]
    nr = np.cross(e1, e2)
    a2 = np.linalg.norm(nr, axis=1)
    y = np.cross(nr / a2[:, None], x)
    p = np.stack([np.zeros(m, complex), l1 + 0j, (e2 * x).sum(1) + 1j * (e2 * y).sum(1)], 1)
    W = (p[:, [2, 0, 1]] - p[:, [1, 2, 0]]) / np.sqrt(a2)[:, None]
    r = np.repeat(np.arange(m), 3)
    Mr, Mi = (sp.coo_matrix((w.ravel(), (r, tri.ravel())), (m, n)) for w in (W.real, W.imag))
    M = sp.bmat([[Mr, -Mi], [Mi, Mr]]).tocsc()
    t = (P - P.mean(0)) @ np.linalg.svd(P - P.mean(0), full_matrices=False)[2][0]
    i0, i1 = int(t.argmin()), int(t.argmax())
    pin, val = np.array([i0, i1, n + i0, n + i1]), np.array([0.0, np.linalg.norm(P[i1] - P[i0]), 0.0, 0.0])
    free = np.setdiff1d(np.arange(2 * n), pin)
    Mf = M[:, free]
    z = np.zeros(2 * n)
    z[pin] = val
    z[free] = spsolve((Mf.T @ Mf).tocsc(), Mf.T @ -(M[:, pin] @ val))
    uv = z.reshape(2, n).T.copy()
    d1, d2 = uv[tri[:, 1]] - uv[tri[:, 0]], uv[tri[:, 2]] - uv[tri[:, 0]]
    ar = d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0]
    return uv * np.sqrt(a2.sum() / np.abs(ar).sum()), int((ar <= 0).sum())


class Unfold:
    """The reference's patch within `reach` of the points `feet` (on its triangles `faces`), unfolded flat.

    uv_of(face, bary): surface points -> the plane. lift(q): the plane -> (surface point, smooth unit normal, how far
    inside its triangle: under 0 = off the patch). length(qa, qb): the surface length of the straight plane segment.
    apex(ua, ub): on each segment, where the normal is as far from the normal at ua as from the one at ub.
    """

    def __init__(self, V0, T, feet, faces, reach, weld=1e-6):
        _, grp = np.unique(np.round(V0 / weld).astype(np.int64), axis=0, return_inverse=True)
        grp = np.asarray(grp).ravel()
        E, area = ct._frames(V0, T)
        sel = np.nonzero((cKDTree(feet).query(V0)[0] <= reach)[T].any(1) & (area > ct.AREA_EPS))[0]
        used, tl = np.unique(grp[T[sel]], return_inverse=True)
        tl = np.asarray(tl).reshape(-1, 3)
        I = sp.csr_matrix((np.ones(3 * len(sel)), (np.repeat(np.arange(len(sel)), 3), tl.ravel())), (len(sel), len(used)))
        _, lab = connected_components(I @ I.T, directed=False)
        inv = -np.ones(len(T), np.int64)
        inv[sel] = np.arange(len(sel))
        if (inv[faces] < 0).any() or len(set(lab[inv[faces]])) != 1:
            raise ValueError("the feet do not lie on one connected patch of the reference")
        keep = lab == lab[inv[faces[0]]]
        sel = sel[keep]
        used, tl = np.unique(grp[T[sel]], return_inverse=True)
        self.tri = np.asarray(tl).reshape(-1, 3)
        self.inv = -np.ones(len(T), np.int64)
        self.inv[sel] = np.arange(len(sel))
        first = np.zeros(int(grp.max()) + 1, np.int64)
        first[grp[::-1]] = np.arange(len(grp))[::-1]
        self.vid = first[used]                               # the patch's points as reference vertices
        self.P = V0[self.vid]
        Wn = sp.csr_matrix((np.repeat(area[sel], 3), (self.tri.ravel(), np.repeat(np.arange(len(sel)), 3))), (len(used), len(sel)))
        self.nv = ct._unit(Wn @ E[sel][:, :, 2])
        self.uv, self.flipped = lscm(self.P, self.tri)
        k = self.tri[:, [0, 1, 1, 2, 2, 0]].reshape(-1, 2)
        self.scale = np.linalg.norm(self.uv[k[:, 0]] - self.uv[k[:, 1]], axis=1) / np.linalg.norm(self.P[k[:, 0]] - self.P[k[:, 1]], axis=1)

    def uv_of(self, face, bary):
        return np.einsum("nk,nkj->nj", bary, self.uv[self.tri[self.inv[face]]])

    def locate(self, q, chunk=1500):
        """(patch triangle, barycentrics, how far inside it) of plane points q."""
        a, b, c = (self.uv[self.tri[:, i]] for i in range(3))
        v0, v1 = b - a, c - a
        den = v0[:, 0] * v1[:, 1] - v0[:, 1] * v1[:, 0]
        T, Bt, sc = [], [], []
        for s in range(0, len(q), chunk):
            d = q[s:s + chunk, None, :] - a[None]
            l1 = (d[..., 0] * v1[:, 1] - d[..., 1] * v1[:, 0]) / den
            l2 = (v0[:, 0] * d[..., 1] - v0[:, 1] * d[..., 0]) / den
            B = np.stack([1 - l1 - l2, l1, l2], 2)
            score = np.where(den > 0, B.min(2), -np.inf)
            t = score.argmax(1)
            bt = np.clip(B[np.arange(len(t)), t], 0, 1)
            T.append(t)
            Bt.append(bt / bt.sum(1, keepdims=True))
            sc.append(score.max(1))
        return np.concatenate(T), np.concatenate(Bt), np.concatenate(sc)

    def lift(self, q):
        t, bt, sc = self.locate(q)
        return np.einsum("nk,nkj->nj", bt, self.P[self.tri[t]]), ct._unit(np.einsum("nk,nkj->nj", bt, self.nv[self.tri[t]])), sc

    def lift_jac(self, q):
        """lift(q) with its derivatives: (S, N, dS / dq [n, 3, 2], dN / dq [n, 3, 2])."""
        t, bt, _ = self.locate(q)
        tr = self.tri[t]
        col = lambda X: np.stack([X[tr[:, 1]] - X[tr[:, 0]], X[tr[:, 2]] - X[tr[:, 0]]], 2)
        Mi = np.linalg.inv(col(self.uv))
        nr = np.einsum("nk,nkj->nj", bt, self.nv[tr])
        ln = np.linalg.norm(nr, axis=1)
        N, dn = nr / ln[:, None], col(self.nv) @ Mi
        dN = (dn - N[:, :, None] * np.einsum("nk,nkc->nc", N, dn)[:, None, :]) / ln[:, None, None]
        return np.einsum("nk,nkj->nj", bt, self.P[tr]), N, col(self.P) @ Mi, dN

    def length(self, qa, qb, k=12, V=None):
        """The surface length of the straight plane segments qa -> qb; V: the reference's vertices in a pose (else rest)."""
        s = np.linspace(0, 1, k + 1)[None, :, None]
        t, bt, _ = self.locate((qa[:, None] + (qb - qa)[:, None] * s).reshape(-1, 2))
        S = np.einsum("nk,nkj->nj", bt, (self.P if V is None else V[self.vid])[self.tri[t]]).reshape(len(qa), k + 1, 3)
        return np.linalg.norm(np.diff(S, axis=1), axis=2).sum(1)

    def stretch(self, q, V):
        """The principal stretches [n, 2] (small, large) of the patch triangle under each plane point q, rest -> V."""
        tr = self.tri[self.locate(q)[0]]
        out = np.zeros((len(q), 2))
        for r, (A, B) in enumerate(zip(self.P[tr], V[self.vid][tr])):
            x = ct._unit(A[1] - A[0])
            y = ct._unit(np.cross(np.cross(A[1] - A[0], A[2] - A[0]), x))
            R = np.stack([[(A[1] - A[0]) @ x, (A[2] - A[0]) @ x], [(A[1] - A[0]) @ y, (A[2] - A[0]) @ y]])
            out[r] = np.linalg.svd(np.stack([B[1] - B[0], B[2] - B[0]], 1) @ np.linalg.inv(R), compute_uv=False)[::-1]
        return out

    def apex(self, ua, ub, k=64):
        s = np.linspace(0, 1, k + 1)[None, :, None]
        q = ua[:, None] + (ub - ua)[:, None] * s
        N = self.lift(q.reshape(-1, 2))[1].reshape(len(ua), k + 1, 3)
        f = (N * (N[:, :1] - N[:, -1:])).sum(2)
        out = np.zeros((len(ua), 2))
        for r in range(len(ua)):
            i = np.nonzero(f[r] <= 0)[0]
            i = max(int(i[0]), 1) if len(i) else k // 2
            out[r] = q[r, i - 1] + f[r, i - 1] / max(f[r, i - 1] - f[r, i], 1e-30) * (q[r, i] - q[r, i - 1])
        return out


class Curve:
    """A polynomial curve of degree `deg` through plane points (in their principal frame), run on straight past both
    ends by `ext`. side(q): the signed offset across the curve; project(q): the closest curve point."""

    def __init__(self, pts, deg=3, ext=0.01, step=5e-5):
        self.c = pts.mean(0)
        self.ax = np.linalg.svd(pts - self.c, full_matrices=False)[2]
        s, d = ((pts - self.c) @ self.ax.T).T
        self.poly = np.polyfit(s, d, min(deg, len(pts) - 1))
        self.s0, self.s1 = float(s.min()), float(s.max())
        self.res = float(np.abs(d - self._d(s)).max())
        ss = np.arange(self.s0 - ext, self.s1 + ext, step)
        self.Q = self.c + ss[:, None] * self.ax[0] + self._d(ss)[:, None] * self.ax[1]
        self._tree = cKDTree(self.Q)

    def _d(self, s):
        sc = np.clip(s, self.s0, self.s1)
        return np.polyval(self.poly, sc) + np.polyval(np.polyder(self.poly), sc) * (s - sc)

    def at(self, s):
        return self.c + s[:, None] * self.ax[0] + self._d(s)[:, None] * self.ax[1]

    def tangent(self, s):
        return self.ax[0] + np.polyval(np.polyder(self.poly), np.clip(s, self.s0, self.s1))[:, None] * self.ax[1]

    def param(self, q):
        return (q - self.c) @ self.ax[0]

    def side(self, q):
        r = (q - self.c) @ self.ax.T
        return r[:, 1] - self._d(r[:, 0])

    def project(self, q):
        return self.Q[self._tree.query(q)[1]]


def tri_quality(P, t):
    """4 sqrt(3) area / (the sum of the squared sides): 1 = equilateral, 0 = a sliver."""
    a, b, c = P[t[:, 0]], P[t[:, 1]], P[t[:, 2]]
    return 2 * np.sqrt(3) * np.linalg.norm(np.cross(b - a, c - a), axis=1) / ((b - a) ** 2 + (c - b) ** 2 + (a - c) ** 2).sum(1)


def relax(unf, cur, u, h, P0, N0, band, snap, E, tris, lim=(0.82, 1.28), wall=50.0, fold=0.5, passes=2, iters=3000, off=0.0):
    """The band's plane points u moved (the snapped ones ALONG the curve) until the mesh's edges, measured on the
    surface (foot + height h), are as near their rest lengths as the fixed neighbours allow: the new plane points.

    min  sum_edges l0 * phi(L / l0)  +  sum_triangles sqrt(area0) * wall * max(0, fold / q - 1)^2,  q = area / area0
    phi(r) = (r - 1)^2 + wall * (max(0, r - lim[1])^2 + max(0, lim[0] - r)^2): every edge the same strain (springs of
    one stiffness per length), a soft wall at the limits, and a BARRIER under `fold` of a triangle's rest area: it
    grows without bound as the area closes, so from a start with no triangle turned over none ever turns over (two
    points cannot pass each other). The plane only carries the unknowns: lengths and areas are the real ones, so the
    unfolding's scale does not leak in.
    off [snapped, 2]: the snapped points run along the curve shifted by these plane offsets (relay walks them to 0).
    """
    n, bi = len(P0), np.nonzero(band)[0]
    fi, si = np.nonzero(band & ~snap)[0], np.nonzero(snap)[0]
    pf, ps = np.searchsorted(bi, fi), np.searchsorted(bi, si)
    i, j = E[:, 0], E[:, 1]
    l0 = np.linalg.norm(P0[i] - P0[j], axis=1) * 1000
    ta, tb_, tc = tris[:, 0], tris[:, 1], tris[:, 2]
    x = np.r_[u[fi].ravel(), cur.param(u[si] - off)] * 1000

    def place(x):
        uu = u.copy()
        uu[fi], uu[si] = x[:2 * len(fi)].reshape(-1, 2) / 1000, cur.at(x[2 * len(fi):] / 1000) + off
        return uu

    for _ in range(passes):
        Nc = N0.copy()
        Nc[bi] = unf.lift(place(x)[bi])[1]
        nh = ct._unit(Nc[tris].sum(1))
        a0 = 0.5 * (np.cross(P0[tb_] - P0[ta], P0[tc] - P0[ta]) * ct._unit(N0[tris].sum(1))).sum(1)
        wt = wall * np.sqrt(np.abs(a0)) * 1000
        Ps = P0.copy()
        Ps[bi] = unf.lift(place(x)[bi])[0] + h[:, None] * Nc[bi]
        # a triangle turned over at the start (the feet fold at a groove's mouth) gets a finite push until it is open
        soft = 0.5 * (np.cross(Ps[tb_] - Ps[ta], Ps[tc] - Ps[ta]) * nh).sum(1) / a0 <= 0.05

        def f(x):
            uu = place(x)
            S, N, dS, dN = unf.lift_jac(uu[bi])
            P = P0.copy()
            P[bi] = S + h[:, None] * N
            d = P[i] - P[j]
            L = np.linalg.norm(d, axis=1) * 1000
            r = L / l0
            over, under = np.maximum(r - lim[1], 0), np.maximum(lim[0] - r, 0)
            e = (l0 * ((r - 1) ** 2 + wall * (over ** 2 + under ** 2))).sum()
            co = (2 * (r - 1) + 2 * wall * (over - under))[:, None] * d * (1000 / np.maximum(L, 1e-9))[:, None]
            gP = np.zeros((n, 3))
            np.add.at(gP, i, co)
            np.add.at(gP, j, -co)
            a, b, c = P[ta], P[tb_], P[tc]
            q = 0.5 * (np.cross(b - a, c - a) * nh).sum(1) / a0
            qc = np.maximum(q, 1e-3)
            pen = np.maximum(np.where(soft, fold - q, fold / qc - 1), 0)
            e += (wt * pen ** 2).sum()
            k = (wt * pen * np.where(soft, -1.0, -fold / qc ** 2 * (q > 1e-3)) / a0 / 1000)[:, None]
            np.add.at(gP, ta, k * np.cross(nh, c - b))
            np.add.at(gP, tb_, k * np.cross(nh, a - c))
            np.add.at(gP, tc, k * np.cross(nh, b - a))
            gu = np.einsum("nkc,nk->nc", dS + h[:, None, None] * dN, gP[bi])
            return e, np.r_[gu[pf].ravel(), (gu[ps] * cur.tangent(x[2 * len(fi):] / 1000)).sum(1)]

        x = minimize(f, x, jac=True, method="L-BFGS-B", options={"maxiter": iters, "maxfun": 2 * iters, "ftol": 1e-13, "gtol": 1e-7}).x
    return place(x)


def relay(P0, edges, tris, band, bridge, face, bary, ref_V0, ref_T, reach=0.03, kappa=1.2, deg=3, ext=0.01, part=0.9,
          rounds=4, sweeps=40, lim=(0.82, 1.28), wall=50.0, fold=0.5):
    """The band's points re-laid on the reference's rest surface: {"P1": the new points [n, 3], ...stats}.

    P0 [n, 3], edges [m, 2], tris [f, 3]: the mesh's rest points and topology; band [n] bool: the points that may move;
    bridge [nb, 2]: its edges that span the reference's fold; face, bary [n]: the rest correspondence (each point's
    reference triangle and barycentrics). kappa: an edge whose path on the reference is over kappa x its chord counts as
    bridging. part: a height is cut until the foot is the closest reference point to within this part of the height.
    """
    P0, E, tris = np.asarray(P0, float), np.asarray(edges, np.int64), np.asarray(tris, np.int64)
    V0, T = np.asarray(ref_V0, float), np.asarray(ref_T, np.int64)
    n, band = len(P0), np.asarray(band, bool).copy()
    ring = (ct._adjacency(n, E) @ band > 0)
    tb = tris[band[tris].any(1)]
    ring[tb.ravel()] = True
    ring &= ~band
    act = np.nonzero(band | ring)[0]
    unf = Unfold(V0, T, np.einsum("nk,nkj->nj", bary[act], V0[T[face[act]]]), face[act], reach)
    u0, S0, N0 = np.zeros((n, 2)), np.zeros((n, 3)), np.zeros((n, 3))
    u0[act] = unf.uv_of(face[act], bary[act])
    S0[act], N0[act], _ = unf.lift(u0[act])
    h0 = ((P0 - S0) * N0).sum(1)
    apex = unf.apex(u0[bridge[:, 0]], u0[bridge[:, 1]])
    cur = Curve(apex, deg, ext)
    depth = np.linalg.norm(unf.lift(apex)[0] - 0.5 * (P0[bridge[:, 0]] + P0[bridge[:, 1]]), axis=1)
    be = np.unique(bridge)
    sd0 = cur.side(u0)
    pos, neg = be[sd0[be] > 0], be[sd0[be] <= 0]
    X = pos if np.abs(sd0[pos]).mean() <= np.abs(sd0[neg]).mean() else neg
    sx = 1.0 if X is pos else -1.0
    Eb = E[band[E].any(1)]
    i, j = Eb[:, 0], Eb[:, 1]
    l0 = np.linalg.norm(P0[i] - P0[j], axis=1)
    g = u0[j] - u0[i]
    k0 = unf.length(u0[i], u0[j]) / l0
    key = lambda e: np.sort(e, 1) @ np.array([n, 1])
    isb = (k0 > kappa) | np.isin(key(Eb), key(bridge))
    t = np.where(isb[:, None], ct._unit(g) * l0[:, None], g)
    w, ne = l0.mean() / l0, len(Eb)
    D = sp.coo_matrix((np.r_[-np.ones(ne), np.ones(ne)], (np.r_[np.arange(ne), np.arange(ne)], np.r_[i, j])), (ne, n)).tocsr()
    Wd = sp.diags(w)
    wsum = np.bincount(np.r_[i, j], np.r_[w, w], n)
    snap = np.zeros(n, bool)
    snap[X] = True
    u, bi = u0.copy(), np.nonzero(band)[0]
    Db = D[:, bi]
    hb = splu((Db.T @ Wd @ Db).tocsc()).solve(Db.T @ (Wd @ -(D @ np.where(band, 0.0, h0))))
    for rnd in range(rounds):
        fi, si = np.nonzero(band & ~snap)[0], np.nonzero(snap)[0]
        Df = D[:, fi]
        K = splu((Df.T @ Wd @ Df).tocsc())
        u[si] = cur.project(u[si])
        fixed = np.ones(n, bool)
        fixed[fi] = False
        for _ in range(sweeps):
            rhs = Df.T @ (Wd @ (t - D @ np.where(fixed[:, None], u, 0.0)))
            u[fi] = np.stack([K.solve(np.ascontiguousarray(rhs[:, c])) for c in range(2)], 1)
            want = np.zeros((n, 2))
            np.add.at(want, i, w[:, None] * (u[j] - t))
            np.add.at(want, j, w[:, None] * (u[i] + t))
            new = cur.project(want[si] / wsum[si, None])
            step, u[si] = np.abs(new - u[si]).max(), new
            if step < 1e-7:
                break
        if lim is not None:                                  # real lengths decide: from the feet (no triangle turned),
            u = u0.copy()                                    # the apex row WALKED onto its line (a jump turns triangles)
            off, tau, step = u0[si] - cur.project(u0[si]), 1.0, 0.25
            while tau > 0:
                tau = max(tau - step, 0.0)
                u = relax(unf, cur, u, hb, P0, N0, band, snap, Eb, tb, lim, wall, fold, 1 if tau else 3, off=tau * off)
        S, N, score = unf.lift(u[bi])
        h = hb.copy()
        cut = np.zeros(len(bi), bool)
        for _ in range(24):                                  # the foot must stay the closest point of the reference
            bad = ct.surface_distance(S + h[:, None] * N, V0, T) < part * np.abs(h) - 1e-7
            if not bad.any():
                break
            h[bad] *= 0.7
            cut |= bad
        P1 = P0.copy()
        P1[bi] = S + h[:, None] * N
        k1 = unf.length(u[i], u[j]) / np.maximum(np.linalg.norm(P1[i] - P1[j], axis=1), 1e-12)
        s1 = cur.side(u)
        cross = (k1 > kappa) & (s1[i] * s1[j] < 0) & ~snap[i] & ~snap[j] & band[i] & band[j]
        add = np.unique(np.where(sx * s1[i[cross]] > 0, i[cross], j[cross]))
        if not len(add) or rnd == rounds - 1:
            break
        snap[add] = True
    Nf = N0.copy()
    Nf[bi] = N
    # the skin budget across the fold: per bridge, the chain ring - bridge - ring along the mesh's edges
    side_e = sd0[i] * sd0[j] > 0
    G = sp.coo_matrix((l0[side_e], (i[side_e], j[side_e])), (n, n)).tocsr()
    dist, pred = dijkstra(G, directed=False, indices=be, return_predecessors=True)
    rg, col, path = np.nonzero(ring)[0], {int(b): r for r, b in enumerate(be)}, {}
    for b in be:
        r, c = col[int(b)], rg[dist[col[int(b)], rg].argmin()]
        path[int(b)] = [int(c)]
        while path[int(b)][-1] != b and np.isfinite(dist[r, c]):
            path[int(b)].append(int(pred[r, path[int(b)][-1]]))
    bud = []
    for a, b in bridge:
        ch = np.array(path[int(a)] + path[int(b)][::-1])
        la = unf.length(u0[ch[:1]], u0[ch[-1:]], 96)[0]
        bud.append([la / np.linalg.norm(np.diff(P0[ch], axis=0), axis=1).sum(), la / np.linalg.norm(np.diff(P1[ch], axis=0), axis=1).sum()])
    l1 = np.linalg.norm(P1[i] - P1[j], axis=1)
    return {"P1": P1, "band": bi, "snap": np.nonzero(snap)[0], "u0": u0, "u": u, "edges": Eb, "tris": tb, "Nf": Nf,
            "budget": np.array(bud), "move": np.linalg.norm(P1 - P0, axis=1)[bi], "len": l1 / l0, "k0": k0, "k1": k1,
            "flip": int((np.sign(ct.facing(tb, P1, Nf)) != np.sign(ct.facing(tb, P0, N0))).sum()), "h": h, "cut": int(cut.sum()),
            "score": float(score.min()), "depth": depth, "apex_res": cur.res, "lscm_flipped": unf.flipped,
            "scale": np.percentile(unf.scale, [1, 50, 99]), "rounds": rnd + 1, "bridging": int(isb.sum()), "unf": unf,
            "isb": isb, "l0": l0, "cur": cur, "ring": np.nonzero(ring)[0],
            "qual": (float(tri_quality(P0, tb).min()), float(tri_quality(P1, tb).min()))}


def sphere_dirs(k):
    """k unit directions spread over the sphere (a Fibonacci spiral)."""
    z = 1 - (2 * np.arange(k) + 1) / k
    a = np.pi * (3 - np.sqrt(5)) * np.arange(k)
    return np.stack([np.sqrt(1 - z * z) * np.cos(a), z, np.sqrt(1 - z * z) * np.sin(a)], 1)


def reached(scene, P, dirs, far=3.0, tol=4e-4):
    """[len(P), len(dirs)] bool: a ray from outside along -dir reaches the point (nothing in front of it by over tol)."""
    import ray
    org = (P[:, None] + far * dirs[None]).reshape(-1, 3)
    pid, tf = ray.hits(scene, org, np.broadcast_to(-dirs[None], (len(P), len(dirs), 3)).reshape(-1, 3))
    return ((pid < 0) | (tf > far - tol)).reshape(len(P), len(dirs))


# ================================================================================================= HER CONFIG ==
HER = {
    "rows": 4,                           # the band: this many rows round the bridge ends (the pocket's rows today)
    "reach": 0.03,                       # A's patch to unfold: within this of the band's feet, m
    "kappa": 1.2,                        # path / chord over this = an edge that still bridges
    "deg": 3, "ext": 0.01,               # the apex line: a cubic through the bridges' apex points, 10 mm past both ends
    "part": 0.9,
    "lim": None,                         # None: the linear lay (the npz on disk). build --relax: (0.82, 1.28), real lengths
    "out": "strip_rest.npz",
    "map_elev": (45.0, 90.0),            # target --map: the lay's share, smoothstep of the arm's elevation over these deg
    "map_near": (45, 60, 67.5, 75, 90),  # ... also print the pose nearest each of these elevations
    "dirs": 2000,                        # outside directions of the visibility proof
    "game_up": 0.3,                      # "from the play camera's side": directions with an up part over this
    "outline": {"front34": (0.5, 0.2, 0.8), "back34": (0.5, 0.3, -0.8), "side": (1, 0, 0), "under": (0.6, -0.5, 0.6)},
    "seen_mm": 0.5,                      # a visible surface point counts as changed past this depth shift
    "outline_half": 0.30, "outline_px": 2000,
    "named": ["x:abd120:l", "x:abd150:l", "x:abd170:l", "x:flex170:l", "p4:iron_vow@72:l", "p4:heroic_leap@7:r",
              "p4:heroic_leap@9:r", "p4:heroic_leap@19:r", "p4:heroic_leap@20:r"],
    "sheet_pose": "x:abd150:l", "panel": 640, "rest_half": 0.42, "rest_drop": 0.10, "pit_half": 0.11,
    "views": {"front34": (0.5, 0.2, 0.8), "under": (0.6, -0.5, 0.6)},
}


class HerStrip:
    def __init__(self, cfg=HER):
        self.cfg, self.h = cfg, ct.Her(verbose=False)
        self.md, self.bd, self.Ab = self.h.md, self.h.bd, self.h.Ab
        self.pts = {s: self.md.first[self.md.S[s]["ids"]] for s in "lr"}
        self.E = {s: np.stack(self.h.edges[s], 1) for s in "lr"}

    def tris(self, s):
        tr = np.asarray(self.md.S[s]["tr"], np.int64)
        return tr[(tr < len(self.pts[s])).all(1)]

    def relay(self, s, rows):
        car, n = self.h.car[s], len(self.pts[s])
        band = ct.rows_around(n, self.E[s], np.unique(car.bridge), rows) & (np.asarray(self.md.beta) >= 1)
        c = self.cfg
        return relay(self.bd.V0[self.pts[s]], self.E[s], self.tris(s), band, car.bridge, car.face, car.bary, self.Ab.V0,
                     self.Ab.T, c["reach"], c["kappa"], c["deg"], c["ext"], c["part"], lim=c["lim"])

    def load(self):
        z = np.load(rt.OUT / self.cfg["out"])
        self.loc = {s: z[f"loc_{s}"] for s in "lr"}
        self.P1 = {}
        for s in "lr":
            self.P1[s] = self.bd.V0[self.pts[s]].copy()
            self.P1[s][self.loc[s]] = z[f"V1_{s}"]
        self.V1 = self.whole(self.bd.V0, self.P1, band_only=True)
        keep = self.bd.V0, self.h.N0                         # B' carriers: built as Her builds them, the rest swapped
        try:
            self.bd.V0, self.h.N0 = self.V1, self.bd._normals(self.V1)
            self.N1 = self.h.N0
            self.car1 = {s: self.h.carrier(s, pocket_rows=0) for s in "lr"}     # no pocket: B' is carried alone
        finally:
            self.bd.V0, self.h.N0 = keep
        return self

    def whole(self, V, X, band_only=False):
        """The whole-body vertices V with each side's region points X[s] put in (band_only: the moved points only)."""
        V = V.copy()
        for s, x in X.items():
            lc = self.md.S[s]["loc"][self.md.src]
            ok = np.isin(lc, self.loc[s]) if band_only else (lc >= 0) & (lc < len(x))
            g = np.nonzero(ok)[0]
            V[g] = x[lc[g]]
        return V


def pct(x, q=(50, 95, 100)):
    return " / ".join(f"{v:.2f}" for v in np.percentile(x, q))


def cmd_build(hs, rows):
    import ray
    import region_shape as rs
    md, bd, cfg, out, R = hs.md, hs.bd, hs.cfg, {}, {}
    for s in "lr":
        r = R[s] = relay_s = hs.relay(s, rows)
        b, ids = r["band"], md.S[s]["ids"]
        out.update({f"ids_{s}": ids[b], f"loc_{s}": b, f"V0_{s}": bd.V0[hs.pts[s]][b], f"V1_{s}": r["P1"][b],
                    f"snap_{s}": r["snap"], f"bridge_{s}": hs.h.car[s].bridge})
        part = np.bincount(md.part[ids[b]], minlength=len(md.parts))
        brd = np.nonzero(np.asarray(md.why) == 1)[0]
        print(f"== {s}: band {len(b)} points moved (rows {rows}, beta min {md.beta[b].min():.2f}, rows from the region's edge min {int(md.depth[b].min())}),"
              f" {len(r['snap'])} on the apex line, {r['bridging']} bridging edges, {r['rounds']} round(s)")
        print(f"   parts: {', '.join(f'{md.parts[k]} {c}' for k, c in enumerate(part) if c)}; nearest breast-part point"
              f" {cKDTree(md.V0[brd]).query(r['P1'][b])[0].min() * 1000:.1f} mm away" if len(brd) else "   no breast part")
        print(f"   unfold: {r['lscm_flipped']} flipped triangles, plane / surface edge length p1 / p50 / p99 {pct(r['scale'], (0, 50, 100))} (percentiles 1, 50, 99),"
              f" points off the patch {int(r['score'] < -1e-6)}; apex fit residual {r['apex_res'] * 1000:.2f} mm; groove depth under the bridges p50 / max {np.median(r['depth']) * 1000:.1f} / {r['depth'].max() * 1000:.1f} mm")
        print(f"   move mm p50 / p95 / max {pct(r['move'] * 1000)}; rest edge new / old {r['len'].min():.2f}..{r['len'].max():.2f} (p50 {np.median(r['len']):.2f});"
              f" path / chord max {r['k0'].max():.2f} -> {r['k1'].max():.2f} (over {cfg['kappa']}: {(r['k0'] > cfg['kappa']).sum()} -> {(r['k1'] > cfg['kappa']).sum()});"
              f" rest triangles turned over {r['flip']}; heights mm p5 / p50 / p95 {pct(r['h'] * 1000, (5, 50, 95))}, cut {r['cut']}")
        print(f"   A's rest path / B's p50 / max {np.median(r['budget'][:, 0]):.2f} / {r['budget'][:, 0].max():.2f}  ->  A's / B' {np.median(r['budget'][:, 1]):.2f} / {r['budget'][:, 1].max():.2f}")
    np.savez_compressed(rt.OUT / cfg["out"], params=json.dumps({**{k: v for k, v in cfg.items()}, "rows": rows}), **out)
    print(f"wrote {rt.OUT / cfg['out']}")
    hs.load()
    for s in "lr":
        c = hs.car1[s]
        d0 = np.linalg.norm(c.d0, axis=1)[hs.loc[s]] * 1000
        feet = np.linalg.norm((hs.P1[s] - c.d0)[hs.loc[s]] - (R[s]["P1"][hs.loc[s]] - R[s]["h"][:, None] * R[s]["Nf"][hs.loc[s]]), axis=1) * 1000
        print(f"   B' carrier {s} (carried alone, no pocket): the 60 deg normal rule still names {len(c.bridge)} edges; band |d0| mm p50 / p95 / max {pct(d0)};"
              f" its feet off the laid feet max {feet.max():.2f} mm; ok False {(~c.ok[hs.loc[s]]).sum()}")
    # hidden at rest: rays from outside, and the outline
    dirs = sphere_dirs(cfg["dirs"])
    up = dirs @ np.asarray(bd.frame.up) > cfg["game_up"]
    s0, s1 = ray.scene(bd.V0, bd.T), ray.scene(hs.V1, bd.T)
    for s in "lr":
        b = hs.loc[s]
        r0, r1 = reached(s0, bd.V0[hs.pts[s]][b], dirs), reached(s1, hs.P1[s][b], dirs)
        mv = R[s]["move"] * 1000
        seen = r0.any(1) | r1.any(1)
        print(f"   rays {s} ({len(dirs)} directions): moved points any ray reaches {r0.any(1).sum()} -> {r1.any(1).sum()} of {len(b)}"
              f" (from above, up > {cfg['game_up']}: {r0[:, up].any(1).sum()} -> {r1[:, up].any(1).sum()}); directions a point p50 / max {int(np.median(r0.sum(1)))} / {r0.sum(1).max()} -> {int(np.median(r1.sum(1)))} / {r1.sum(1).max()};"
              f" largest move of a reached point {mv[seen].max() if seen.any() else 0:.2f} mm")
        fr, c = bd.frame, bd.G0[bd.p.index[f"upperarm_{s}"]][:3, 3]
        for vn, v in cfg["outline"].items():
            vw = rs.chest_view(c, np.eye(3), (1 if s == "l" else -1) * np.asarray(fr.lat), np.asarray(fr.up), np.asarray(fr.front), v,
                               cfg["outline_half"], cfg["outline_px"])
            (p0, t0), (p1, t1) = vw.cast(s0), vw.cast(s1)
            m0, m1 = p0 >= 0, p1 >= 0
            d = rs.outline_signed(m1, m0)
            dz = np.abs(np.where(m0 & m1, t1 - t0, 0.0)) * 1000
            print(f"   outline {s} {vn}: {int((m0 != m1).sum())} pixels differ of {m0.size} ({1000 / cfg['outline_px']:.1f} mm a pixel),"
                  f" max shift {np.nanmax(np.abs(d)) * 1000 / cfg['outline_px'] if np.isfinite(d).any() else 0:.2f} mm;"
                  f" surface seen from there: {int((dz > cfg['seen_mm']).sum())} px ({(dz > cfg['seen_mm']).sum() / cfg['outline_px'] ** 2 * 1e4:.1f} cm2) change depth by over {cfg['seen_mm']} mm, max {dz.max():.1f} mm")


def band_stats(X, P, E, tb, N, N0, band, Va, T):
    r = np.linalg.norm(X[E[:, 0]] - X[E[:, 1]], axis=1) / np.linalg.norm(P[E[:, 0]] - P[E[:, 1]], axis=1)
    flip = int((np.sign(ct.facing(tb, X, N)) != np.sign(ct.facing(tb, P, N0))).sum())
    return [float(r.min()), float(r.max()), float(ct.surface_distance(X[band], Va, T).max() * 1000), flip]


def cmd_target(hs, poses):
    h, md, bd, cfg = hs.h, hs.md, hs.bd, hs.cfg
    z = np.load(rt.OUT / "poses.npz")
    names = [str(x) for x in z["name"]]
    sel = [names.index(p) for p in poses] if poses else list(range(len(names)))
    E = {s: hs.E[s][np.isin(hs.E[s], hs.loc[s]).any(1)] for s in "lr"}
    tb = {s: hs.tris(s)[np.isin(hs.tris(s), hs.loc[s]).any(1)] for s in "lr"}
    rows = {}
    for k in sel:
        s, G = str(z["side"][k]), z["G"][k]
        Va, _ = h.pose_ref(G)
        res = []
        for car, P, N0 in ((h.car[s], bd.V0[hs.pts[s]], h.N0[hs.pts[s]]), (hs.car1[s], hs.P1[s], hs.N1[hs.pts[s]])):
            X = car.carry(Va)
            N = np.einsum("nij,nj->ni", car.rotations(Va), N0)
            res.append(band_stats(X, P, E[s], tb[s], N, N0, hs.loc[s], Va, hs.Ab.T))
        rows[names[k]] = res
    print(f"{'pose':24s} | today's fill: edge min..max, off A max mm, turned over | B': the same")
    for nm, (f, b) in rows.items():
        if poses or nm in cfg["named"]:
            print(f"{nm:24s} | {f[0]:.2f}..{f[1]:.2f}  {f[2]:5.1f}  {f[3]:3d} | {b[0]:.2f}..{b[1]:.2f}  {b[2]:5.1f}  {b[3]:3d}")
    a = np.array(list(rows.values()))
    for c, nm in ((0, "today's fill"), (1, "B'")):
        m = a[:, c]
        print(f"{nm:13s} {len(m)} poses: band edge max <= 2.5 in {(m[:, 1] <= 2.5).sum()}, <= 3 in {(m[:, 1] <= 3).sum()}; worst {m[:, 1].max():.2f}"
              f" ({list(rows)[int(m[:, 1].argmax())]}); edge min {m[:, 0].min():.2f}; off A max {m[:, 2].max():.1f} mm (p50 {np.median(m[:, 2]):.1f});"
              f" poses with a turned-over triangle {(m[:, 3] > 0).sum()} (most {int(m[:, 3].max())})")
    if not poses:
        (rt.OUT / "strip_target.json").write_text(json.dumps(rows))
        print(f"wrote {rt.OUT / 'strip_target.json'}")


def elevation(hs, G, s):
    """The arm's elevation from hanging down, deg: the upper arm's direction in the trunk's frame (the carry's anchor
    joint) against the body's down."""
    bd, ja = hs.bd, hs.h.anchor[s][0]
    d = np.linalg.solve(G[ja][:3, :3] @ np.linalg.inv(bd.p.rest[ja][:3, :3]),
                        G[bd.p.index[f"lowerarm_{s}"]][:3, 3] - G[bd.p.index[f"upperarm_{s}"]][:3, 3])
    return float(np.degrees(np.arccos(np.clip(-(d @ np.asarray(bd.frame.up)) / np.linalg.norm(d), -1, 1))))


def cmd_map(hs, poses):
    """target --map: the lay as a CARRY MAP only. B's rest stays as it is; per pose the band's target is
    (1 - w) * today's fill + w * the re-laid band carried on A's posed surface, w = smoothstep of the arm's elevation
    over cfg["map_elev"]. Every ratio is against B's OLD rest."""
    h, bd, cfg = hs.h, hs.bd, hs.cfg
    z = np.load(rt.OUT / "poses.npz")
    names, sides = [str(x) for x in z["name"]], [str(x) for x in z["side"]]
    lo, hi = cfg["map_elev"]
    weight = lambda e: (lambda t: t * t * (3 - 2 * t))(np.clip((e - lo) / (hi - lo), 0, 1))
    el = np.array([elevation(hs, z["G"][k], sides[k]) for k in range(len(names))])
    w = weight(el)
    sel = [names.index(q) for q in poses]
    if poses == cfg["named"]:
        sel += [int(np.abs(el - e).argmin()) for e in cfg["map_near"]]
        sel += sorted(np.nonzero((w > 0.2) & (w < 0.8))[0].tolist(), key=lambda k: abs(w[k] - 0.5))[:6]
    sel = list(dict.fromkeys(sel))
    E = {s: hs.E[s][np.isin(hs.E[s], hs.loc[s]).any(1)] for s in "lr"}
    tb = {s: hs.tris(s)[np.isin(hs.tris(s), hs.loc[s]).any(1)] for s in "lr"}
    R = {}

    def targets(G, s, wk):
        Va, _ = h.pose_ref(G)
        N0, b = h.N0[hs.pts[s]], hs.loc[s]
        Xf, Nf = h.car[s].carry(Va), np.einsum("nij,nj->ni", h.car[s].rotations(Va), N0)
        Xb, Nb = hs.car1[s].carry(Va), np.einsum("nij,nj->ni", hs.car1[s].rotations(Va), hs.N1[hs.pts[s]])
        Xm, Nm = Xf.copy(), Nf.copy()
        Xm[b] = Xf[b] + wk * (Xb[b] - Xf[b])
        Nm[b] = ct._unit(Nf[b] + wk * (Nb[b] - Nf[b]))
        return Va, Xf, Nf, Xm, Nm

    def stats(X, N, s, Va):
        P, N0, e = bd.V0[hs.pts[s]], h.N0[hs.pts[s]], E[s]
        r = np.linalg.norm(X[e[:, 0]] - X[e[:, 1]], axis=1) / np.linalg.norm(P[e[:, 0]] - P[e[:, 1]], axis=1)
        flip = int((np.sign(ct.facing(tb[s], X, N)) != np.sign(ct.facing(tb[s], P, N0))).sum())
        return [float(r.min()), float(r.max()), float(r.mean()), float(ct.surface_distance(X[hs.loc[s]], Va, hs.Ab.T).max() * 1000), flip]

    fmt = lambda a: f"{a[0]:.2f}..{a[1]:.2f} {a[2]:.2f} {a[3]:5.1f} {a[4]:3d}"
    print(f"{'pose':24s}  elev    w | fill: edge min..max mean, off A mm, turned | map: the same | A's own skin under the band edges: min..max mean")
    rows = []
    for k in sel:
        s = sides[k]
        if s not in R:
            r = hs.relay(s, cfg["rows"])
            i, j = r["edges"][:, 0], r["edges"][:, 1]
            R[s] = (r["unf"], r["u"][i], r["u"][j], r["unf"].length(r["u"][i], r["u"][j]), float(np.abs(r["P1"] - hs.P1[s]).max()))
        Va, Xf, Nf, Xm, Nm = targets(z["G"][k], s, w[k])
        unf, ui, uj, len0, _ = R[s]
        own = unf.length(ui, uj, 12, Va) / len0
        f, m = stats(Xf, Nf, s, Va), stats(Xm, Nm, s, Va)
        rows.append((w[k], f, m))
        print(f"{names[k]:24s} {el[k]:5.1f} {w[k]:4.2f} | {fmt(f)} | {fmt(m)} | {own.min():.2f}..{own.max():.2f} {own.mean():.2f}")
    mid = [(f, m) for wk, f, m in rows if 0.2 < wk < 0.8]
    if mid:
        print(f"transition (w 0.2..0.8, {len(mid)} poses): map edge min {min(m[0] for _, m in mid):.2f} (fill {min(f[0] for f, _ in mid):.2f}), max {max(m[1] for _, m in mid):.2f}"
              f" (fill {max(f[1] for f, _ in mid):.2f}); turned most {max(m[4] for _, m in mid)} (fill {max(f[4] for f, _ in mid)}), poses where the map turns more than the fill {sum(m[4] > f[4] for f, m in mid)}")
    low, d = np.nonzero(w == 0)[0], 0.0
    for k in low:                                            # the proof: the general formula, no shortcut at w = 0
        _, Xf, _, Xm, _ = targets(z["G"][k], sides[k], w[k])
        d = max(d, float(np.abs(Xm - Xf).max()))
    print(f"proof: {len(low)} of {len(names)} poses have elevation <= {lo:.0f} deg (w = 0); max |map - fill| over them {d!r} m")
    for s in "lr":
        er = elevation(hs, bd.p.rest, s)
        _, Xf, _, Xm, _ = targets(bd.p.rest, s, weight(er))
        print(f"proof: rest {s}: elevation {er:.1f} deg, w {weight(er)!r}, max |map - fill| {float(np.abs(Xm - Xf).max())!r} m, fill off B's rest max"
              f" {np.abs(Xf - bd.V0[hs.pts[s]])[hs.loc[s]].max() * 1000:.2f} mm; relay vs the npz {R[s][4] * 1000 if s in R else float('nan'):.3f} mm")
    print("elevation check (name says): " + ", ".join(f"{names[k]} {el[k]:.0f}" for k in range(len(names)) if names[k].startswith("x:")))


SHEET_ROWS = "rest:front34,x:abd150:l:front34,x:abd150:l:under,x:flex170:l:under,cast_bolt@3:r:under"


def map_numbers(hs, names):
    """{pose: (elev, w, fill, map, own)} as cmd_map prints them (its own code, its stdout read back), and the rest
    proof lines {side: (elev, w)}."""
    import contextlib
    import io
    import re
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        cmd_map(hs, names)
    rows, rest = {}, {}
    for ln in buf.getvalue().splitlines():
        m = re.match(r"proof: rest (\w): elevation ([\d.]+) deg, w (?:np\.float64\()?([\d.e+-]+)", ln)
        if m:
            rest[m.group(1)] = (float(m.group(2)), float(m.group(3)))
        parts = ln.split(" | ")
        if len(parts) == 4 and parts[0].split()[0] in names:
            nm, e, w = parts[0].split()
            rows[nm] = (float(e), float(w), parts[1].split(), parts[2].split(), parts[3].split())
    return rows, rest


def cmd_sheet(hs, rows_arg="", out_name="armpit_map"):
    """sheet: a grid, one row per pose:view, columns B fill | B map | A; the numbers of cmd_map under each row."""
    import region_shape as rs
    from PIL import Image, ImageDraw, ImageFont
    h, md, bd, cfg = hs.h, hs.md, hs.bd, hs.cfg
    specs = [r.rsplit(":", 1) for r in (rows_arg or SHEET_ROWS).split(",") if r]
    names = list(dict.fromkeys(p for p, _ in specs))
    cx = rs.Ctx()
    poses = {p: next(cx.poses([p])) for p in names}
    nums, rest = map_numbers(hs, [p for p in names if p != "rest"])
    lo, hi = cfg["map_elev"]
    weight = lambda e: (lambda t: t * t * (3 - 2 * t))(np.clip((e - lo) / (hi - lo), 0, 1))
    N0s = {}

    def panels(pname):
        pose = poses[pname]
        G, s = pose["G"], pose["side"]
        V = cx.surface("pub" if pname.startswith("rest") else "carried", pose)
        Vp = cx.surface("pub", pose)
        Va, Ga = h.pose_ref(G)
        ja, ra = h.anchor[s]
        M = ct.anchor_align(G[ja], bd.p.rest[ja], hs.Ab.G0[ra], Ga[ra])
        b = md.blend(G, s)[:, None]
        N0, bb = h.N0[hs.pts[s]], hs.loc[s]
        Xf = h.car[s].carry(Va)
        Xb = hs.car1[s].carry(Va)
        wk = weight(elevation(hs, G, s))
        Xm = Xf.copy()
        Xm[bb] = Xf[bb] + wk * (Xb[bb] - Xf[bb])
        put = lambda X: hs.whole(V, {s: b * (X @ M[:3, :3].T + M[:3, 3]) + (1 - b) * Vp[hs.pts[s]]}, band_only=True)
        return pose, put(Xf), put(Xm)

    cache, ims, labs, lines = {}, [], [], []
    for pname, vn in specs:
        if pname not in cache:
            cache[pname] = panels(pname)
        pose, Vf, Vm = cache[pname]
        px = rs.SHEET["panel"]
        vw = cx.view(pose, rs.SHEET["views"][vn], rs.SHEET["half"], px / (2 * rs.SHEET["half"]))
        Va = cx.a_on_B(pose)
        im = [rs.clay_rgb(Vf, bd.T, vw), rs.clay_rgb(Vm, bd.T, vw), rs.clay_rgb(Va, cx.A.T, vw)]
        ims.append(im)
        labs.append([f"{c} | {pname} | {vn}" for c in ("B fill", "B map", "A")])
        if pname == "rest":
            assert np.array_equal(im[0], im[1]), "rest: fill != map"
            print("rest: fill == map")
            e, w = rest[pose["side"]]
            lines.append(f"elev {e:.1f}  w {w:.2f}  | fill: = B's rest | map: = B's rest (cmd_map proof) | A's own: -")
        else:
            e, w, f, m, o = nums[pname]
            t = lambda a: f"edges {a[0]}, mean {a[1]}, off A {a[2]} mm, turned {a[3]}"
            lines.append(f"elev {e:.1f}  w {w:.2f}  | fill: {t(f)} | map: {t(m)} | A's own: {o[0]} mean {o[1]}")
        print(f"{pname}:{vn}  " + "  ".join(f"{c.mean():.1f}" for c in im), flush=True)
        assert all(c.std() > 1 for c in im), f"blank panel in {pname}:{vn}"
    pn = rs.SHEET["panel"]
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except OSError:
        font = ImageFont.load_default()
    strips = []
    for im, lab, ln in zip(ims, labs, lines):
        r = rs.sheet([im], [lab], pn)
        w = r.width
        parts = [ln]
        while len(parts) < 3 and max(font.getlength(x) for x in parts) > w - 8:
            parts = [x for q in parts for x in ([q] if font.getlength(q) <= w - 8 else
                                                 [q[:q.rindex(" | ", 0, len(q) // 2 + 20)], q[q.rindex(" | ", 0, len(q) // 2 + 20) + 3:]])]
        st = Image.new("RGB", (w, 26 * len(parts) + 6), (255, 255, 255))
        d = ImageDraw.Draw(st)
        for i, x in enumerate(parts):
            d.text((4, 3 + 26 * i), x, fill=(0, 0, 0), font=font)
        strips.append((r, st))
    W = strips[0][0].width
    H = sum(r.height + st.height + 4 for r, st in strips)
    big = Image.new("RGB", (W, H), (120, 120, 120))
    y = 0
    for r, st in strips:
        big.paste(r, (0, y))
        big.paste(st, (0, y + r.height))
        y += r.height + st.height + 4
    out = rt.OUT / "sheets" / f"{out_name}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    big.save(out)
    half = out.with_name(out.stem + "_half.jpg")
    rs.save_half(big, half)
    print(f"wrote {out} ({big.width}x{big.height})")
    print(f"wrote {half}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=["build", "target", "sheet"])
    ap.add_argument("--snap", action="store_true", help="import carried_target from out/shoulder/snap (a frozen copy)")
    ap.add_argument("--rows", default="", help="build: lay rows (int); sheet: pose:view,pose:view,... (default: five rows, see SHEET_ROWS)")
    ap.add_argument("--relax", action="store_true", help="build: relax the lay on real lengths (slow; the left fails, see strip_rest.md)")
    ap.add_argument("--map", action="store_true", help="target: the lay as a carry map blended in by arm elevation, B's rest kept")
    ap.add_argument("--out", default="armpit_map", help="sheet: output name")
    ap.add_argument("--poses", default="", help="comma-separated pose names, or 'named' (the config's list); none: all of poses.npz")
    a = ap.parse_args()
    HER["lim"] = (0.82, 1.28) if a.relax else None
    print(f"carried_target: {ct.__file__}")
    hs = HerStrip()
    if a.cmd == "build":
        return cmd_build(hs, int(a.rows) if a.rows else HER["rows"])
    hs.load()
    if a.cmd == "target" and a.map:
        return cmd_map(hs, HER["named"] if a.poses in ("", "named") else [q for q in a.poses.split(",") if q])
    if a.cmd == "target":
        return cmd_target(hs, HER["named"] if a.poses == "named" else [p for p in a.poses.split(",") if p])
    cmd_sheet(hs, a.rows, a.out)


if __name__ == "__main__":
    main()
