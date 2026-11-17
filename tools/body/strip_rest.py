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

    def locate(self, q, chunk=1500, k=16):
        """(patch triangle, barycentrics, how far inside it) of plane points q. The k triangles nearest by centroid
        are tried first; a point inside none of them gets the full search (the answer is the full search's)."""
        if not hasattr(self, "_geo"):
            a, b, c = (self.uv[self.tri[:, i]] for i in range(3))
            v0, v1 = b - a, c - a
            self._geo = a, v0, v1, v0[:, 0] * v1[:, 1] - v0[:, 1] * v1[:, 0], cKDTree((a + b + c) / 3)
        a, v0, v1, den, tree = self._geo
        q = np.asarray(q, float)

        def best(d, v0, v1, den, ids):
            l1 = (d[..., 0] * v1[..., 1] - d[..., 1] * v1[..., 0]) / den
            l2 = (v0[..., 0] * d[..., 1] - v0[..., 1] * d[..., 0]) / den
            B = np.stack([1 - l1 - l2, l1, l2], 2)
            score = np.where(den > 0, B.min(2), -np.inf)
            j, r = score.argmax(1), np.arange(len(d))
            return (ids[r, j] if ids is not None else j), B[r, j], score[r, j]

        cand = tree.query(q, k=min(k, len(a)))[1].reshape(len(q), -1)
        t, B, sc = best(q[:, None] - a[cand], v0[cand], v1[cand], den[cand], cand)
        out = np.nonzero(sc < 0)[0]
        for s in range(0, len(out), chunk):
            o = out[s:s + chunk]
            t[o], B[o], sc[o] = best(q[o, None] - a[None], v0[None], v1[None], den[None], None)
        bt = np.clip(B, 0, 1)
        return t, bt / bt.sum(1, keepdims=True), sc

    def normals(self, V):
        """The patch points' smooth unit normals with the reference's vertices at V (a pose)."""
        P, out = V[self.vid], np.zeros((len(self.vid), 3))
        nr = np.cross(P[self.tri[:, 1]] - P[self.tri[:, 0]], P[self.tri[:, 2]] - P[self.tri[:, 0]])
        for c in range(3):
            np.add.at(out, self.tri[:, c], nr)
        return ct._unit(out)

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


def plane_area(u, tris):
    """Per triangle [f]: its signed area in the unfold's plane. THE LAY'S ORIENTATION RULE: a lay triangle is right
    when this is over 0, the sign the reference's own unfolded triangles have (lscm keeps their winding; Unfold.flipped
    counts the exceptions, 0 on a sound patch), whatever the mesh's rest triangle did across the fold."""
    d1, d2 = u[tris[:, 1]] - u[tris[:, 0]], u[tris[:, 2]] - u[tris[:, 0]]
    return 0.5 * (d1[..., 0] * d2[..., 1] - d1[..., 1] * d2[..., 0])


def corner_facing(X, N, tris):
    """[f, 3]: each triangle's unit normal dotted with the unit normal N at each of its corners (the orientation rule
    where no plane test is available: a triangle is right when it faces along the surface normal at EVERY corner)."""
    nr = ct._unit(np.cross(X[tris[:, 1]] - X[tris[:, 0]], X[tris[:, 2]] - X[tris[:, 0]]))
    return np.einsum("fj,fkj->fk", nr, ct._unit(N[tris]))


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


def paths(unf, qa, qb, PS, k=12):
    """[m, e]: the lengths of the straight plane segments qa -> qb on the patch in each of its m shapes PS [m, p, 3]."""
    s = np.linspace(0, 1, k + 1)[None, :, None]
    t, bt, _ = unf.locate((qa[:, None] + (qb - qa)[:, None] * s).reshape(-1, 2))
    S = np.einsum("nk,mnkj->mnj", bt, PS[:, unf.tri[t]]).reshape(len(PS), len(qa), k + 1, 3)
    return np.linalg.norm(np.diff(S, axis=2), axis=3).sum(2)


def chain_order(pts, E, P):
    """(the points pts in order as ONE simple path along the edges E, or None; the path's turn at each inner point, deg
    off straight, in the shape P; the points' count of neighbours among pts)."""
    nb = {int(p): set() for p in pts}
    for a, b in E[np.isin(E, pts).all(1)]:
        nb[int(a)].add(int(b))
        nb[int(b)].add(int(a))
    deg = sorted(len(v) for v in nb.values())
    ends = [p for p, v in nb.items() if len(v) == 1]
    if len(ends) != 2 or deg[-1] > 2:
        return None, [], deg
    out = [ends[0]]
    while len(out) < len(nb):
        nx = [q for q in nb[out[-1]] if q not in out]
        if not nx:
            return None, [], deg
        out.append(nx[0])
    d = ct._unit(np.diff(P[out], axis=0))
    return out, np.degrees(np.arccos(np.clip((d[:-1] * d[1:]).sum(1), -1, 1))).round().astype(int).tolist(), deg


def lay2(unf, cur, u0, h, P0, N0, band, snap, E, tris, design, lim=(0.5, 2.0), walk=(0.82, 1.28), wall=50.0,
         fold=(0.3, 0.15), margin=(0.05, 0.10), steps=8, passes=3, iters=1500, start=None, ratchet=True, capm=0.10,
         qmin=0.0, qwall=1.0, capwall=1.0, lo_own=0.0, lowall=1.0, hiwall=1.0, rest_wall=1.0, ring_lim=None, judge=None,
         guard=0.0, guardwall=1.0, turnwall=1.0, boost=0.0, extra=0, log=print):
    """The band's plane points for a CARRY MAP: where each band point rides on the reference, chosen so the band is
    sound IN THE POSES IT IS USED IN, not as a rest. The snapped points (the apex row) stay on the curve and slide
    along it; they are walked onto it from their feet in `steps`.

    design: [(V the reference's vertices in a pose, Xf [n, 3] the mesh's own target there (the fill), Nf [n, 3] its
    normals, w the map's share there)]. In each pose the band is (1 - w) Xf + w (foot(u) + h normal(u)).
    min  sum_edges l0 (r0 - 1)^2 + walls on r0 at lim                          (r0: edge / rest on the rest surface)
       + sum_poses sum_edges l0 wall (max(0, r - hi)^2 + max(0, lo - r)^2)     (r: the posed edge / the mesh's rest)
       + sum_surfaces sum_triangles the barrier of `relax` under fold x the rest area (rest fold[0], poses fold[1])
    The triangles' orientation: at rest the signed area IN THE UNFOLD'S PLANE (plane_area: over 0 = the reference's own
    sign), in a pose the area along the carried normals; both over the mesh's UNSIGNED rest area. (Until lay 4 both
    were divided by the rest triangle's area signed against the reference's normals at the rest feet: a rest triangle
    that bridges the fold faces against those, and the barrier then HELD its lay triangle inverted.)
    start [n, 2]: a lay's plane points to start from (no walk onto the line: the snapped points are already on it).
    ratchet: a pose's hi never rises from one pass to the next (the reference's own worst is read under the lay's
    edges, so it moves with the lay: without this the limit chases the lay). A design pose may carry a fifth entry,
    True = judged against the fill: there hi is also at most the fill's worst + capm.
    hi = the reference's own worst stretch under the lay's edges in that pose (and the fill's worst where w < 1)
    + margin[0]; lo = the smaller of the reference's own and the fill's shortest - margin[1]: the map may open as far
    as the reference's skin does and no further. hi, lo and the triangles' facing are re-read each pass.
    Lay 5's rules (all off at their defaults): qmin, a floor on each lay triangle's quality AT REST (tri_quality of
    the lifted points, not the plane: the unfold squeezes near the fold, plane 0.35 can be 0.17 lifted) over B's rest
    quality (a sliver at rest has no stable facing in a pose: tri 290 r, 0.18 against B's 0.91, turned at leap@19),
    weighted qwall x the triangle barrier's weight; capwall, the wall's factor over hi in the poses judged against the
    fill (so the fill's worst + capm holds, not just pulls); lo_own, lo is at least this part of the reference's own
    shortest (no edge collapses where A's skin does not), lowall the wall's factor under lo in the poses, hiwall over
    hi in the other poses; rest_wall, the wall's factor on the rest edges (lim); ring_lim (lo, hi), the rest edge
    ratio's limits on an edge to the fixed ring (its far end does not move with the map: edge 2455-2456 r, lay 1.86,
    carried crossbow_shoot's worst).
    Lay 6's rules (off at their defaults): judge, a callable (X the rest lay points [n, 3]) -> (Nb [poses, band, 3]
    the lay's own rest vertex normals carried into each design pose, s0 [triangles] the facing sign of B's rest): when
    given, the poses' barrier is THE MAP COUNT'S OWN RULE (cmd_turned, Her): the area along the mixed normals
    (1 - w) fill + w Nb, signed against B's rest facing, re-read each pass; a triangle the fill itself turns in a pose
    is held at w x its weight there (the map can only move w of it), every other one at turnwall x its weight. guard, the minimum-width guard: in every pose
    no edge under guard x the reference's own shortest there, wall guardwall x wall (slivers).
    Lay 6b's rule (off at its default): boost (with judge), THE SHIPPED COUNT AT EACH PASS'S END: the judge is re-read
    on the pass's result and every triangle the count still turns there (any triangle where w >= 0.5, one the fill does
    not turn itself where w < 0.5) has its weight x boost, every posed edge under the guard its guard wall x boost
    (capped at 1000 x); up to `extra` passes more until the count sees none. (Within a pass the judge's normals are
    fixed: a triangle that straddles A's crease flips with the lay's own rest normals between passes.)
    """
    n, bi, m = len(P0), np.nonzero(band)[0], 1 + len(design)
    fi, si = np.nonzero(band & ~snap)[0], np.nonzero(snap)[0]
    pf, ps = np.searchsorted(bi, fi), np.searchsorted(bi, si)
    i, j, ne, nf = E[:, 0], E[:, 1], len(E), len(tris)
    l0 = np.linalg.norm(P0[i] - P0[j], axis=1) * 1000
    PS = np.stack([unf.P] + [d[0][unf.vid] for d in design])
    NS = np.stack([unf.nv] + [unf.normals(d[0]) for d in design])
    W = np.array([1.0] + [float(d[3]) for d in design])
    base = np.stack([P0] + [d[1] for d in design])
    fillr = np.linalg.norm(base[:, i] - base[:, j], axis=2) * 1000 / l0
    base[:, bi] *= (1 - W)[:, None, None]
    NB = np.stack([N0] + [d[2] for d in design])
    De = sp.coo_matrix((np.r_[np.ones(ne), -np.ones(ne)], (np.r_[np.arange(ne), np.arange(ne)], np.r_[i, j])), (ne, n)).tocsr()
    Tc = [sp.coo_matrix((np.ones(nf), (np.arange(nf), tris[:, c])), (nf, n)).tocsr() for c in range(3)]
    a0 = 0.5 * np.linalg.norm(np.cross(P0[tris[:, 1]] - P0[tris[:, 0]], P0[tris[:, 2]] - P0[tris[:, 0]]), axis=1)
    wt = wall * np.sqrt(a0) * 1000
    rot = lambda v: np.stack([-v[:, 1], v[:, 0]], 1)
    ring_e = ~(band[i] & band[j])
    q0p = tri_quality(P0, tris)

    def quality(X):                                          # tri_quality of 3D points [n, 3] and its gradient per corner
        a, b, c = X[tris[:, 0]], X[tris[:, 1]], X[tris[:, 2]]
        nr = np.cross(b - a, c - a)
        A2 = np.maximum(np.linalg.norm(nr, axis=1), 1e-18)
        nu, S2, K = nr / A2[:, None], ((b - a) ** 2 + (c - b) ** 2 + (a - c) ** 2).sum(1), 2 * np.sqrt(3)
        g = [K * (np.cross(nu, w1) * S2[:, None] - A2[:, None] * 2 * w2) / S2[:, None] ** 2
             for w1, w2 in ((c - b, 2 * a - b - c), (a - c, 2 * b - c - a), (b - a, 2 * c - a - b))]
        return K * A2 / S2, g
    if start is not None:
        steps, u0 = 0, np.asarray(start, float).copy()
    pr = cur.project(u0[si]) if start is None else u0[si]   # a stored row may have slid past the sampled curve's ends
    off0, x = u0[si] - pr, np.r_[u0[fi].ravel(), cur.param(pr)] * 1000

    def place(x, tau):
        uu = u0.copy()
        uu[fi], uu[si] = x[:2 * len(fi)].reshape(-1, 2) / 1000, cur.at(x[2 * len(fi):] / 1000) + tau * off0
        return uu

    def points(uu, mm, jac=False):
        t, bt, _ = unf.locate(uu[bi])
        tr = unf.tri[t]
        A, B = PS[:mm, tr], NS[:mm, tr]
        nr = np.einsum("nk,mnkj->mnj", bt, B)
        ln = np.linalg.norm(nr, axis=2, keepdims=True)
        N, X, J = nr / ln, base[:mm].copy(), None
        X[:, bi] += W[:mm, None, None] * (np.einsum("nk,mnkj->mnj", bt, A) + h[None, :, None] * N)
        if jac:
            Mi = np.linalg.inv(np.stack([unf.uv[tr[:, 1]] - unf.uv[tr[:, 0]], unf.uv[tr[:, 2]] - unf.uv[tr[:, 0]]], 2))
            col = lambda Y: np.stack([Y[:, :, 1] - Y[:, :, 0], Y[:, :, 2] - Y[:, :, 0]], 3) @ Mi
            dn = col(B)
            J = col(A) + h[None, :, None, None] * (dn - N[..., None] * np.einsum("mnk,mnkc->mnc", N, dn)[:, :, None, :]) / ln[..., None]
        return X, N, J

    def areas(X, nh, uu):
        a, b, c = (X[:, tris[:, k]] for k in range(3))
        q = 0.5 * (np.cross(b - a, c - a) * nh).sum(2) / a0 * sg[:len(X)]
        q[0] = plane_area(uu, tris) / a0                     # the rest: the plane decides
        return q, a, b, c

    capped, hi_min = np.array([len(d) > 4 and bool(d[4]) for d in design], bool), None
    sg, wtm, glo = np.ones((m, nf)), np.broadcast_to(wt, (m, nf)).copy(), np.zeros((m, 1))
    if judge is not None:                                    # the fill's own turned triangles per pose (fixed)
        ft = np.stack([ct.facing(tris, d[1], d[2]) for d in design])
        ft0 = None
    gwm = np.full((m, ne), float(guardwall))
    for step in range(steps + passes + (extra if judge is not None and boost > 1 else 0)):
        tau = max(1 - (step + 1) / steps, 0.0) if steps else 0.0
        mm = 1 if step < steps else m                        # the walk onto the line: on the rest surface alone
        lm, Ws = (walk, W[:1]) if mm == 1 else (lim, W)
        fo = np.r_[0.5 if mm == 1 else fold[0], np.full(mm - 1, fold[1])][:, None]
        kspr = np.r_[1.0, np.zeros(mm - 1)][:, None]
        scat = lambda M, v: (M.T @ v.transpose(1, 0, 2).reshape(M.shape[0], -1)).reshape(n, mm, 3).transpose(1, 0, 2)
        uu = place(x, tau)
        X, N, _ = points(uu, mm)
        NX = NB[:mm].copy()
        NX[:, bi] = ct._unit((1 - Ws)[:, None, None] * NX[:, bi] + Ws[:, None, None] * N)
        if judge is not None and mm > 1:                     # the map count's rule: B' normals carried, B's rest sign
            Nj, s0 = judge(X[0])
            NX[1:, bi] = ct._unit((1 - W[1:mm])[:, None, None] * NB[1:mm][:, bi] + W[1:mm][:, None, None] * Nj)
            sg[1:] = s0[None]
            if ft0 is None:
                ft0 = np.sign(ft) != s0[None]
                wtm[1:] = np.where(ft0, W[1:, None], turnwall) * wt[None]
        nh = ct._unit(NX[:, tris].sum(2))
        soft = areas(X, nh, uu)[0] <= 0.05
        hi, lo = np.full((mm, 1), lm[1]), np.full((mm, 1), lm[0])
        if mm > 1:
            ln = paths(unf, uu[i], uu[j], PS)
            own = ln[1:] / ln[:1]
            hi[1:, 0] = np.where(W[1:] >= 1, own.max(1), np.maximum(own.max(1), fillr[1:].max(1))) + margin[0]
            lo[1:, 0] = np.maximum(np.minimum(own.min(1), fillr[1:].min(1)) - margin[1], 0.1)
            hi[1:, 0] = np.where(capped, np.minimum(hi[1:, 0], fillr[1:].max(1) + capm), hi[1:, 0])
            if ratchet and hi_min is not None:
                hi[1:, 0] = np.minimum(hi[1:, 0], hi_min)
            hi_min = hi[1:, 0].copy()
            if lo_own:
                lo[1:, 0] = np.maximum(lo[1:, 0], lo_own * own.min(1))
            glo = np.r_[0.0, guard * own.min(1)][:, None]
        hi, lo = np.broadcast_to(hi, (mm, ne)).copy(), np.broadcast_to(lo, (mm, ne)).copy()
        if ring_lim is not None:
            lo[0, ring_e], hi[0, ring_e] = np.maximum(lo[0, ring_e], ring_lim[0]), np.minimum(hi[0, ring_e], ring_lim[1])
        wl = np.r_[rest_wall, np.where(capped, capwall, hiwall)[:mm - 1]][:, None] * wall
        wu = np.r_[rest_wall, np.full(mm - 1, lowall)][:, None] * wall

        def f(x):
            uu = place(x, tau)
            X, _, J = points(uu, mm, True)
            d = X[:, i] - X[:, j]
            L = np.linalg.norm(d, axis=2) * 1000
            r = L / l0
            over, under = np.maximum(r - hi, 0), np.maximum(lo - r, 0)
            ug, wg = np.maximum(glo[:mm] - r, 0), gwm[:mm] * wall
            e = (l0 * (kspr * (r - 1) ** 2 + wl * over ** 2 + wu * under ** 2 + wg * ug ** 2)).sum()
            gX = scat(De, (2 * kspr * (r - 1) + 2 * (wl * over - wu * under - wg * ug))[..., None] * d * (1000 / np.maximum(L, 1e-9))[..., None])
            if qmin:                                         # the rest lay's slivers (row 0 = the rest surface)
                qr, gq = quality(X[0])
                pq = np.maximum(qmin - qr / q0p, 0)
                e += (qwall * wt * pq ** 2).sum()
                kq = (-2 * qwall * wt * pq / q0p / 1000)[:, None]
                gX[0] += sum(Tc[c_].T @ (kq * gq[c_]) for c_ in range(3))
            q, a, b, c = areas(X, nh, uu)
            qc = np.maximum(q, 1e-3)
            pen = np.maximum(np.where(soft, fo - q, fo / qc - 1), 0)
            e += (wtm[:mm] * pen ** 2).sum()
            k = (wtm[:mm] * pen * np.where(soft, -1.0, -fo / qc ** 2 * (q > 1e-3)) * sg[:mm] / a0 / 1000)[..., None]
            kp, (ua, ub, uc) = k[0].copy(), (uu[tris[:, c_]] for c_ in range(3))
            k[0] = 0.0
            gX += scat(Tc[0], k * np.cross(nh, c - b)) + scat(Tc[1], k * np.cross(nh, a - c)) + scat(Tc[2], k * np.cross(nh, b - a))
            gu = np.einsum("m,mnkc,mnk->nc", Ws, J, gX[:, bi])
            gu += (Tc[0].T @ (kp * rot(uc - ub)) + Tc[1].T @ (kp * rot(ua - uc)) + Tc[2].T @ (kp * rot(ub - ua)))[bi]
            return e, np.r_[gu[pf].ravel(), (gu[ps] * cur.tangent(x[2 * len(fi):] / 1000)).sum(1)]

        res = minimize(f, x, jac=True, method="L-BFGS-B", options={"maxiter": iters, "maxfun": 2 * iters, "ftol": 1e-12, "gtol": 1e-7})
        x = res.x
        if judge is not None and mm > 1 and boost > 1:      # the shipped count on this pass's result: what it still sees
            ue = place(x, tau)
            Xe, Ne, _ = points(ue, mm)
            Nje, _ = judge(Xe[0])
            NXe = NB[:mm].copy()
            NXe[:, bi] = ct._unit((1 - W)[:, None, None] * NXe[:, bi] + W[:, None, None] * Ne)
            NXe[1:, bi] = ct._unit((1 - W[1:])[:, None, None] * NB[1:][:, bi] + W[1:, None, None] * Nje)
            te = (areas(Xe, ct._unit(NXe[:, tris].sum(2)), ue)[0][1:] <= 0) & ((W[1:, None] >= 0.5) | ~ft0)
            re = np.linalg.norm(Xe[1:, i] - Xe[1:, j], axis=2) * 1000 / l0
            ge = re < glo[1:] - 1e-9
            wtm[1:] = np.where(te, np.minimum(wtm[1:] * boost, 1000 * wt[None]), wtm[1:])
            gwm[1:] = np.where(ge, np.minimum(gwm[1:] * boost, 1000 * guardwall), gwm[1:])
            if log:
                log(f"   lay2 step {step} END (the count re-read): turned {int(te.sum())} in {int(te.any(1).sum())} poses"
                    f" (w >= 0.5: {int(te[W[1:] >= 0.5].sum())}), under the guard {int(ge.sum())} edges in {int(ge.any(1).sum())} poses", flush=True)
            if step >= steps + passes - 1 and not te.any() and not ge.any():
                break
        if log and (mm > 1 or tau == 0):
            Xn = points(place(x, tau), mm)[0]
            rr = np.linalg.norm(Xn[:, i] - Xn[:, j], axis=2) * 1000 / l0
            log(f"   lay2 step {step} tau {tau:.2f}: e {res.fun:.1f}, {res.nit} its; turned at start (rest: the plane, poses) {int(soft[0].sum())}, {int(soft[1:].sum())};"
                f" rest edge {rr[0].min():.2f}..{rr[0].max():.2f}" + (f"; poses over hi {int((rr[1:] > hi[1:]).sum())} (worst by {(rr[1:] - hi[1:]).max():.2f}),"
                f" under lo {int((rr[1:] < lo[1:]).sum())}; A's own worst over the poses {own.max():.2f}; least map / A's own shortest"
                f" {(rr[1:].min(1) / own.min(1)).min():.2f}" if mm > 1 else ""), flush=True)
    return place(x, 0.0)


def lay_faults(P0, P, u, E, tris, lim, qrel, amin):
    """The faults of a lay P (points on the reference, u their plane points) against the mesh's rest P0: per triangle
    the signed area IN THE UNFOLD'S PLANE (plane_area: over 0 = the reference's own sign) / the unsigned rest area, and
    tri_quality lay, rest; per edge lay / rest length. Faulty: a triangle with area under amin (under 0: turned) or
    quality under qrel x its rest quality; an edge outside lim (lim None: no edge is a fault).
    -> (area [f], quality [f], rest quality [f], ratio [e], faulty triangles [f] bool, faulty edges [e] bool)."""
    cr = lambda X: np.cross(X[tris[:, 1]] - X[tris[:, 0]], X[tris[:, 2]] - X[tris[:, 0]])
    sa = 2 * plane_area(u, tris) / np.linalg.norm(cr(P0), axis=1)
    q, q0 = tri_quality(P, tris), tri_quality(P0, tris)
    r = np.linalg.norm(P[E[:, 0]] - P[E[:, 1]], axis=1) / np.linalg.norm(P0[E[:, 0]] - P0[E[:, 1]], axis=1)
    return sa, q, q0, r, (sa < amin) | (q < qrel * q0), ((r < lim[0]) | (r > lim[1])) if lim else np.zeros(len(E), bool)


def untangle(unf, u, h, P0, N0, band, hold, E, tris, lim=None, qrel=0.0, amin=0.1, grow=1, polish=False, sweeps=30,
             dirs=16, tol=1e-4, stop=1e-5):
    """A lay's faults repaired in place: (the plane points u with the faulty points re-placed, a report).
    BY DEFAULT A SAFETY NET ON TURNED TRIANGLES ONLY (plane area under amin x rest; no quality floor, no edge limits,
    polish False: a point stops as soon as its triangles are sound, its edges are not improved). A broad rest repair
    (lim (0.6, 1.6), qrel 0.5, amin 0.25, grow 2, polish True = lay 3) judges the rest alone and broke the poses.

    u [n, 2]: the lay (plane points of the unfold `unf`); h [band points]: their heights; P0 [n, 3]: the mesh's rest;
    N0 [n, 3]: the reference's normals at the rest feet (used for the points outside the band, which stay at P0);
    band [n] bool: the points of the lay; hold [n] bool: band points that never move (the snapped row); E, tris: the
    edges and triangles that touch the band. The points outside the band (the fixed ring) never move.

    Faults as lay_faults names them. Their free points are re-placed one at a time, on the reference's surface (a
    pattern search in the plane, lifted back with the point's height): first until every triangle at the point is sound
    (area >= amin, quality >= qrel x rest), then to the least worst deviation max(r, 1 / r) - 1 of the edges at the
    point with those triangles kept sound. A move is taken only if it betters the point's own score by tol, so a
    sound point stays where it is and the worst deviation over the band never rises. While faults remain, the free
    set grows by one ring of neighbours, `grow` times at most. No point is named here."""
    n, bi = len(P0), np.nonzero(band)[0]
    hh = np.zeros(n)
    hh[bi] = h
    u = np.asarray(u, float).copy()
    P, N = P0.copy(), N0.copy()
    S, Nb, _ = unf.lift(u[bi])
    P[bi], N[bi] = S + h[:, None] * Nb, Nb
    Pin = P.copy()
    l0 = np.linalg.norm(P0[E[:, 0]] - P0[E[:, 1]], axis=1)
    a0 = np.linalg.norm(np.cross(P0[tris[:, 1]] - P0[tris[:, 0]], P0[tris[:, 2]] - P0[tris[:, 0]]), axis=1)
    q0 = tri_quality(P0, tris)
    pe, pt = [[] for _ in range(n)], [[] for _ in range(n)]
    for x, (a, b) in enumerate(E):
        pe[a].append(x)
        pe[b].append(x)
    for x, t in enumerate(tris):
        for c in t:
            pt[c].append(x)
    dev = lambda r: np.maximum(r, 1 / np.maximum(r, 1e-9)) - 1
    ang = np.arange(dirs) * 2 * np.pi / dirs
    ring = np.stack([np.cos(ang), np.sin(ang)], 1)

    def score(p, q):
        """Per candidate plane point q [k, 2] of point p: (the triangles' shortfall, the worst edge deviation, the
        lay points, the normals)."""
        Sq, Nq, sc = unf.lift(q)
        C = Sq + hh[p] * Nq
        ep = np.array(pe[p])
        o = np.where(E[ep, 0] == p, E[ep, 1], E[ep, 0])
        d = dev(np.linalg.norm(C[:, None] - P[o][None], axis=2) / l0[ep]).max(1)
        short = np.where(sc < -1e-9, np.inf, 0.0)
        for t in pt[p]:
            X = np.repeat(P[tris[t]][None], len(q), 0)
            Nn = np.repeat(N[tris[t]][None], len(q), 0)
            c = int(np.nonzero(tris[t] == p)[0][0])
            X[:, c], Nn[:, c] = C, Nq
            nr = np.cross(X[:, 1] - X[:, 0], X[:, 2] - X[:, 0])
            U = np.repeat(u[tris[t]][None], len(q), 0)
            U[:, c] = q
            sa = (U[:, 1, 0] - U[:, 0, 0]) * (U[:, 2, 1] - U[:, 0, 1]) - (U[:, 1, 1] - U[:, 0, 1]) * (U[:, 2, 0] - U[:, 0, 0])
            sa = sa / a0[t]                                  # the plane rule (plane_area / the rest area)
            ql = 2 * np.sqrt(3) * np.linalg.norm(nr, axis=1) / ((X[:, 1] - X[:, 0]) ** 2 + (X[:, 2] - X[:, 1]) ** 2 + (X[:, 0] - X[:, 2]) ** 2).sum(1)
            short += np.maximum(amin - sa, 0) + np.maximum(qrel * q0[t] - ql, 0)
        return short, d, C, Nq

    better = lambda s, d, s0, d0: (s < s0 - tol) if s0 > 0 else (s <= 0) & (d < d0 - tol)
    first = lay_faults(P0, P, u, E, tris, lim, qrel, amin)
    free = np.zeros(n, bool)
    rounds = 0
    for g in range(grow + 1):
        sa, q, _, r, ft, fe = lay_faults(P0, P, u, E, tris, lim, qrel, amin)
        if not (ft.any() or fe.any()):
            break
        seed = np.zeros(n, bool)
        seed[tris[ft].ravel()] = True
        seed[E[fe].ravel()] = True
        if g:                                                # the faults that stayed: their points' neighbours too
            seed |= free
            near = np.zeros(n, bool)
            near[E[seed[E].any(1)].ravel()] = True
            seed |= near
        free = seed & band & ~hold
        rounds = g + 1
        for _ in range(sweeps):
            moved = 0.0
            for p in np.nonzero(free)[0]:
                ep = np.array(pe[p])
                rad = 0.5 * np.linalg.norm(u[E[ep, 0]] - u[E[ep, 1]], axis=1).mean()
                s0, d0, _, _ = (x[0] for x in score(p, u[p][None]))
                while rad > stop and (polish or s0 > 0):
                    cand = u[p] + np.r_[rad * ring, 0.5 * rad * ring]
                    s, d, C, Nq = score(p, cand)
                    key = np.where(s > 0, 1e6 + s, d) if s0 <= 0 else s * 1e6 + d * (s <= 0)
                    k = int(key.argmin())
                    if better(s[k], d[k], s0, d0):
                        moved = max(moved, float(np.linalg.norm(C[k] - P[p])))
                        u[p], P[p], N[p], s0, d0 = cand[k], C[k], Nq[k], s[k], d[k]
                    else:
                        rad *= 0.5
            if moved < stop:
                break
    last = lay_faults(P0, P, u, E, tris, lim, qrel, amin)
    mv = np.linalg.norm(P - Pin, axis=1)
    return u, {"moved": np.nonzero(mv > 1e-9)[0], "mm": mv[mv > 1e-9] * 1000, "free": np.nonzero(free)[0], "rounds": rounds,
               "before": first, "after": last, "lim": lim, "qrel": qrel, "amin": amin}


def relay(P0, edges, tris, band, bridge, face, bary, ref_V0, ref_T, reach=0.03, kappa=1.2, deg=3, ext=0.01, part=0.9,
          rounds=4, sweeps=40, lim=(0.82, 1.28), wall=50.0, fold=0.5, side=0, design=None, lay=None, u_given=None, repair=None,
          start=None, snap_given=None):
    """The band's points re-laid on the reference's rest surface: {"P1": the new points [n, 3], ...stats}.

    P0 [n, 3], edges [m, 2], tris [f, 3]: the mesh's rest points and topology; band [n] bool: the points that may move;
    bridge [nb, 2]: its edges that span the reference's fold; face, bary [n]: the rest correspondence (each point's
    reference triangle and barycentrics). kappa: an edge whose path on the reference is over kappa x its chord counts as
    bridging. part: a height is cut until the foot is the closest reference point to within this part of the height.
    side: which bridge ends make the apex row (0: the nearer side, +1 / -1: that side of the apex line).
    design (+ lay: lay2's keywords): the lay is lay2's (a carry map, judged in the poses of `design`).
    u_given [n, 2]: a stored lay's plane points; nothing is solved, the result is rebuilt from them.
    repair: untangle's keywords ({} = its defaults); the lay (solved or given) is untangled, the snapped row held.
    start [n, 2] (with design): lay2 starts from these plane points, one round, no walk. snap_given: the snapped row's
    points as stored with a lay (u_given / start); without it the row is found again (the first round's only).
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
    X = (pos if side > 0 else neg) if side else pos if np.abs(sd0[pos]).mean() <= np.abs(sd0[neg]).mean() else neg
    sx = 1.0 if X is pos else -1.0
    chains = {nm: chain_order(x, E, P0) + (float(np.abs(sd0[x]).mean()),) for nm, x in (("+", pos), ("-", neg))}
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
    snap[X if snap_given is None else np.asarray(snap_given, np.int64)] = True
    one = u_given is not None or start is not None
    u, bi = u0.copy(), np.nonzero(band)[0]
    Db = D[:, bi]
    hb = splu((Db.T @ Wd @ Db).tocsc()).solve(Db.T @ (Wd @ -(D @ np.where(band, 0.0, h0))))
    for rnd in range(1 if one else rounds):
        fi, si = np.nonzero(band & ~snap)[0], np.nonzero(snap)[0]
        Df = D[:, fi]
        K = splu((Df.T @ Wd @ Df).tocsc())
        u[si] = cur.project(u[si])
        fixed = np.ones(n, bool)
        fixed[fi] = False
        for _ in range(0 if u_given is not None or design is not None else sweeps):
            rhs = Df.T @ (Wd @ (t - D @ np.where(fixed[:, None], u, 0.0)))
            u[fi] = np.stack([K.solve(np.ascontiguousarray(rhs[:, c])) for c in range(2)], 1)
            want = np.zeros((n, 2))
            np.add.at(want, i, w[:, None] * (u[j] - t))
            np.add.at(want, j, w[:, None] * (u[i] + t))
            new = cur.project(want[si] / wsum[si, None])
            step, u[si] = np.abs(new - u[si]).max(), new
            if step < 1e-7:
                break
        if u_given is not None:
            u = np.asarray(u_given, float).copy()
        elif design is not None:
            u = lay2(unf, cur, u0, hb, P0, N0, band, snap, Eb, tb, design, **{**(lay or {}), "start": start})
        elif lim is not None:                                # real lengths decide: from the feet (no triangle turned),
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
        if not len(add) or rnd == rounds - 1 or one:
            break
        snap[add] = True
    fix = None
    if repair is not None:                                   # the lay's own faults (turned, slivers, edges out of lim)
        u, fix = untangle(unf, u, h, P0, N0, band, snap, Eb, tb, **repair)
        S, N, score = unf.lift(u[bi])
        for _ in range(24):
            bad = ct.surface_distance(S + h[:, None] * N, V0, T) < part * np.abs(h) - 1e-7
            if not bad.any():
                break
            h[bad] *= 0.7
            cut |= bad
        P1 = P0.copy()
        P1[bi] = S + h[:, None] * N
        k1 = unf.length(u[i], u[j]) / np.maximum(np.linalg.norm(P1[i] - P1[j], axis=1), 1e-12)
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
            "flip": int((plane_area(u, tb) <= 0).sum()), "flip_corner": int((corner_facing(P1, Nf, tb) <= 0).any(1).sum()),
            "flip_sum": int((ct.facing(tb, P1, Nf) <= 0).sum()), "flip_rest": int((plane_area(u0, tb) <= 0).sum()),
            "fix": fix, "N0": N0, "h": h, "cut": int(cut.sum()),
            "score": float(score.min()), "depth": depth, "apex_res": cur.res, "lscm_flipped": unf.flipped,
            "scale": np.percentile(unf.scale, [1, 50, 99]), "rounds": rnd + 1, "bridging": int(isb.sum()), "unf": unf,
            "isb": isb, "l0": l0, "cur": cur, "ring": np.nonzero(ring)[0], "chains": chains, "cross": int(cross.sum()), "sx": sx,
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
    "lay": 2,                            # 2: lay2, a carry map judged in the poses it is used in. 1 (--lay l18): the old
    "old_out": "strip_rest_l18.npz",     #    linear lay, kept in this file
    "side": {"l": -1, "r": 0},           # the apex row: 0 the nearer side's bridge ends, +1 / -1 that side of the line
                                         # (l: the nearer side, +, crushes on the line: rest edge 0.18; - walks on clean)
    "untangle": {},                      # untangle's keywords: {} = a safety net on triangles turned in the plane only
    "keep": ("strip_rest_l18.npz", "strip_rest_l19_lay2.npz", "strip_rest_l19_lay3.npz"),   # build never writes these
    "lay2": {},                          # lay2's keywords (lim, wall, fold, margin, steps, passes, iters)
    "map_elev": (45.0, 90.0),            # target --map: the lay's share, smoothstep of the arm's elevation over these deg
    "fill_bar": 90.05,                   # lay2: poses up to this elevation are judged against the fill (worst edge <= its + capm)
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



def pose_a(h, G):
    """A posed by the whole pose (Her.pose_ref), faired by HER's "fair_a" rule when the key is on (fair_a.ref_hook,
    seeds on both girdle carriers' A vertices). Key absent (as in --snap's frozen copy) or h.fair_on False: as it was."""
    Va, Ga = h.pose_ref(G)
    if getattr(h, "cfg", {}).get("fair_a"):
        import fair_a
        Va = fair_a.ref_hook(h, Va, Ga)
    return Va, Ga

class HerStrip:
    def __init__(self, cfg=HER, h=None):
        self.cfg, self.h = cfg, (ct.Her(verbose=False) if h is None else h)    # h: an existing Her (Her's own map loader)
        self.md, self.bd, self.Ab = self.h.md, self.h.bd, self.h.Ab
        self.pts = {s: self.md.first[self.md.S[s]["ids"]] for s in "lr"}
        self.E = {s: np.stack(self.h.edges[s], 1) for s in "lr"}

    def tris(self, s):
        tr = np.asarray(self.md.S[s]["tr"], np.int64)
        return tr[(tr < len(self.pts[s])).all(1)]

    def design(self, s):
        """lay2's poses for side s: every pose of poses.npz where the map has a share (elevation over map_elev[0])."""
        z, car, out = np.load(rt.OUT / "poses.npz"), self.h.car[s], []
        for k in np.nonzero(np.array([str(x) for x in z["side"]]) == s)[0]:
            el = elevation(self, z["G"][k], s)
            w = share(el, *self.cfg["map_elev"])
            if w > 0:
                Va, _ = pose_a(self.h, z["G"][k])
                out.append((Va, car.carry(Va), np.einsum("nij,nj->ni", car.rotations(Va), self.h.N0[self.pts[s]]), w,
                            el <= self.cfg["fill_bar"]))
        return out

    def relay(self, s, rows, u=None, repair=False, start=None, snap=None):
        """The lay of side s: built (cfg["lay"]: 2 = lay2 on the design poses, 1 = the old linear lay; start: lay2
        starts from these plane points), or rebuilt from stored plane points u. snap: the stored apex row."""
        car, n = self.h.car[s], len(self.pts[s])
        band = ct.rows_around(n, self.E[s], np.unique(car.bridge), rows) & (np.asarray(self.md.beta) >= 1)
        c = self.cfg
        new = c["lay"] == 2 and u is None
        des, lay = self.design(s) if new else None, dict(c["lay2"])
        if new and lay.get("judge"):
            lay["judge"] = self.judge(s, band, des)
        else:
            lay.pop("judge", None)
        return relay(self.bd.V0[self.pts[s]], self.E[s], self.tris(s), band, car.bridge, car.face, car.bary, self.Ab.V0,
                     self.Ab.T, c["reach"], c["kappa"], c["deg"], c["ext"], c["part"], lim=c["lim"],
                     rounds=2 if new else 4, side=c["side"][s] if c["lay"] == 2 else 0,
                     design=des, lay=lay, u_given=u,
                     repair=c["untangle"] if c["lay"] == 2 and (new or repair) else None,
                     start=start if new else None, snap_given=snap if c["lay"] == 2 else None)

    def judge(self, s, band, des):
        """lay2's `judge` for side s (cfg lay2 "judge": true): the map count's own normals, as cmd_turned and Her read
        them. Given the rest lay points X0 [n, 3]: B' = B with them put in, its vertex normals, its carrier (no pocket,
        as load builds car1), and those normals carried into each design pose (band points); with B's rest facing sign
        of the band's triangles."""
        pid, bi = self.pts[s], np.nonzero(band)[0]
        tr = self.tris(s)
        tb = tr[band[tr].any(1)]
        s0 = np.sign(ct.facing(tb, self.bd.V0[pid], self.h.N0[pid]))

        def f(X0):
            V1 = self.whole(self.bd.V0, {s: X0})
            keep = self.bd.V0, self.h.N0
            try:
                self.bd.V0, self.h.N0 = V1, self.bd._normals(V1)
                N1, car = self.h.N0[pid][bi], self.h.carrier(s, pocket_rows=0)
            finally:
                self.bd.V0, self.h.N0 = keep
            return np.stack([np.einsum("nij,nj->ni", car.rotations(d[0])[bi], N1) for d in des]), s0
        return f

    def load(self):
        z = np.load(rt.OUT / self.cfg["out"])
        self.u = {s: z[f"u_{s}"] for s in "lr"} if "u_l" in z.files else None
        self.snap = {s: z[f"snap_{s}"] for s in "lr"}
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


def share(e, lo, hi):
    """The map's share at arm elevation e: smoothstep over lo..hi deg (cmd_map's weight)."""
    t = float(np.clip((e - lo) / (hi - lo), 0, 1))
    return t * t * (3 - 2 * t)


def cmd_build(hs, rows):
    import ray
    import region_shape as rs
    md, bd, cfg, out, R = hs.md, hs.bd, hs.cfg, {}, {}
    if cfg["out"] in cfg["keep"]:
        raise SystemExit(f"{cfg['out']} is a kept lay: build writes --file another name")
    old = np.load(rt.OUT / cfg["out"]) if cfg.get("only") or cfg.get("repair") else None
    st = np.load(rt.OUT / cfg["start"]) if cfg.get("start") else None
    for s in "lr":
        kept = old is not None and s not in cfg["only"]
        src = old if kept else st
        r = R[s] = hs.relay(s, rows, old[f"u_{s}"] if kept else None, bool(cfg.get("repair")),
                            st[f"u_{s}"] if st is not None and not kept else None, src[f"snap_{s}"] if src is not None else None)
        if r["fix"]:
            fx, e, tb, pid = r["fix"], r["edges"], r["tris"], hs.pts[s]
            ids = lambda v: "/".join(str(int(x)) for x in v) + " (mesh " + "/".join(str(int(pid[x])) for x in v) + ")"
            for nm, (sa, q, q0, rr, ft, fe) in (("before", fx["before"]), ("after", fx["after"])):
                print(f"   untangle {s} {nm}: triangles turned {(sa <= 0).sum()}, faulty (area < {fx['amin']} or quality < {fx['qrel']} x rest) {ft.sum()},"
                      f" edges outside {fx['lim']} {fe.sum()}; rest edge {rr.min():.2f}..{rr.max():.2f}, least area {sa.min():+.2f}, least quality / rest {(q / q0).min():.2f}")
                for t in np.nonzero(ft)[0]:
                    print(f"      tri {t} {ids(tb[t])}: area {sa[t]:+.2f}, quality {q[t]:.2f} (rest {q0[t]:.2f})")
                for x in np.nonzero(fe)[0]:
                    print(f"      edge {x} {ids(e[x])}: {rr[x]:.2f}")
            print(f"   untangle {s}: {fx['rounds']} round(s), free points {len(fx['free'])}, moved {len(fx['moved'])}: "
                  + ", ".join(f"{int(p)} (mesh {int(pid[p])}) {m:.1f} mm" for p, m in zip(fx["moved"], fx["mm"])))
        b, ids = r["band"], md.S[s]["ids"]
        out.update({f"ids_{s}": ids[b], f"loc_{s}": b, f"V0_{s}": bd.V0[hs.pts[s]][b], f"V1_{s}": r["P1"][b],
                    f"snap_{s}": r["snap"], f"bridge_{s}": hs.h.car[s].bridge})
        if cfg["lay"] == 2:
            out.update({f"u_{s}": r["u"], f"h_{s}": r["h"]})
        for nm, (order, turn, deg, off) in r["chains"].items():
            print(f"   bridge ends on the {nm} side{' (THE APEX ROW)' if (nm == '+') == (r['sx'] > 0) else ''}: {off * 1000:.1f} mm off the line (plane); "
                  + (f"one path {order}, turns deg {turn}" if order else f"NOT one path (neighbours among them {deg})"))
        tq = tri_quality(r["P1"], r["tris"])
        print(f"   edges still crossing the line with a path over kappa: {r['cross']}; triangle quality min old / new {r['qual'][0]:.3f} / {r['qual'][1]:.3f}, new under 0.2: {(tq < 0.2).sum()}")
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
              f" rest triangles turned, THE PLANE RULE {r['flip']} (B's rest feet by the same rule {r['flip_rest']}; a corner facing off A's normal {r['flip_corner']}, summed normals {r['flip_sum']}); heights mm p5 / p50 / p95 {pct(r['h'] * 1000, (5, 50, 95))}, cut {r['cut']}")
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
    if cfg["lay"] == 2:                                      # a carry map only: B's rest is not changed, nothing to hide
        return
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
        Va, _ = pose_a(h, G)
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


def map_targets(hs, Va, s, wk, Xf=None):
    """(Xf, Nf, Xm, Nm) [side s's list points, 3] on the posed reference Va: today's fill (Xf: given, or carried here)
    and the map, the band's points (hs.loc[s]) blended by wk toward the re-laid band carried on Va, normals alike.
    cmd_map's targets and Her (config support "map": the composed target) both run this."""
    h, N0, b = hs.h, hs.h.N0[hs.pts[s]], hs.loc[s]
    Xf = h.car[s].carry(Va) if Xf is None else Xf
    Nf = np.einsum("nij,nj->ni", h.car[s].rotations(Va), N0)
    Xb, Nb = hs.car1[s].carry(Va), np.einsum("nij,nj->ni", hs.car1[s].rotations(Va), hs.N1[hs.pts[s]])
    Xm, Nm = Xf.copy(), Nf.copy()
    Xm[b] = Xf[b] + wk * (Xb[b] - Xf[b])
    Nm[b] = ct._unit(Nf[b] + wk * (Nb[b] - Nf[b]))
    return Xf, Nf, Xm, Nm


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
        Va, _ = pose_a(h, G)
        return (Va, *map_targets(hs, Va, s, wk))

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
            r = hs.relay(s, cfg["rows"], hs.u[s] if hs.u else None, snap=hs.snap[s])
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
        Va, Ga = pose_a(h, G)
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


def fold_angles(tb, X, band):
    """The dihedral (deg, 0 = flat) across each edge shared by two triangles of tb that has an end on the band
    (smoothness: the band's folds in a pose)."""
    nt = ct._unit(np.cross(X[tb[:, 1]] - X[tb[:, 0]], X[tb[:, 2]] - X[tb[:, 0]]))
    e = np.sort(np.concatenate([tb[:, [0, 1]], tb[:, [1, 2]], tb[:, [2, 0]]]), 1)
    t = np.tile(np.arange(len(tb)), 3)
    o = np.lexsort((e[:, 1], e[:, 0]))
    e, t = e[o], t[o]
    pair = np.nonzero((e[1:] == e[:-1]).all(1))[0]
    bm = np.zeros(len(X), bool)
    bm[band] = True
    pair = pair[bm[e[pair]].any(1)]
    return np.degrees(np.arccos(np.clip((nt[t[pair]] * nt[t[pair + 1]]).sum(1), -1, 1)))


def cmd_turned(hs, poses, top=4):
    """turned: DIAGNOSTICS of the carry map (reads the stored lay, writes nothing). Per pose: the triangles cmd_map
    counts as turned and the band edges over A's own worst + 0.15, with ids (region-local / mesh vertex), place
    (A apex row, b other bridge end, . band, r the fixed ring) and the split ratio = lay (the lay's rest edge / B's
    old rest) x pose (the posed map edge / the lay's rest edge), next to A's own stretch along that edge's path."""
    h, bd, cfg, R = hs.h, hs.bd, hs.cfg, {}
    z = np.load(rt.OUT / "poses.npz")
    names, sides = [str(x) for x in z["name"]], [str(x) for x in z["side"]]
    un = lambda t, X: np.cross(X[t[:, 1]] - X[t[:, 0]], X[t[:, 2]] - X[t[:, 0]])
    for q in poses:
        k = names.index(q)
        s, G = sides[k], z["G"][k]
        if s not in R:
            r = hs.relay(s, cfg["rows"], hs.u[s] if hs.u else None, snap=hs.snap[s])
            tr, pid = r["tris"], hs.pts[s]
            pl, co = plane_area(r["u"], tr) <= 0, (corner_facing(r["P1"], r["Nf"], tr) <= 0).any(1)
            sm = np.sign(ct.facing(tr, hs.P1[s], hs.N1[pid])) != np.sign(ct.facing(tr, bd.V0[pid], h.N0[pid]))
            wh = lambda m: np.nonzero(m)[0].tolist()
            print(f"== rest {s}: lay triangles turned, THE PLANE RULE {int(pl.sum())} {wh(pl)}; the map count's measure on the lay at rest (B' vertex normals)"
                  f" {int(sm.sum())} {wh(sm)}: {'AGREE' if (pl == sm).all() else 'DIFFER'}; a corner facing off A's foot normal {int(co.sum())} {wh(co)};"
                  f" B's rest feet by the plane rule {wh(plane_area(r['u0'], tr) <= 0)}; unfold flipped {r['lscm_flipped']}", flush=True)
            tag = np.full(len(hs.pts[s]), "o")
            tag[r["ring"]], tag[r["band"]] = "r", "."
            tag[np.unique(h.car[s].bridge)] = "b"
            tag[r["snap"]] = "A"
            act = np.unique(tr)
            R[s] = r, tag, r["unf"].length(r["u"][r["edges"][:, 0]], r["u"][r["edges"][:, 1]]), (act,) + r["unf"].locate(r["u"][act])[:2]
        r, tag, len0, (act, ta, bta) = R[s]
        e, P, N0, b, P1, c1 = r["edges"], bd.V0[hs.pts[s]], h.N0[hs.pts[s]], hs.loc[s], hs.P1[s], hs.car1[s]
        tb = hs.tris(s)
        tb = tb[np.isin(tb, b).any(1)]
        wk = share(elevation(hs, G, s), *cfg["map_elev"])
        Va, _ = pose_a(h, G)
        Xf, Nf = h.car[s].carry(Va), np.einsum("nij,nj->ni", h.car[s].rotations(Va), N0)
        Xb, Nb = c1.carry(Va), np.einsum("nij,nj->ni", c1.rotations(Va), hs.N1[hs.pts[s]])

        def mix(w):
            X, N = Xf.copy(), Nf.copy()
            X[b], N[b] = Xf[b] + w * (Xb[b] - Xf[b]), ct._unit(Nf[b] + w * (Nb[b] - Nf[b]))
            return X, N

        (Xm, Nm), (X1, N1) = mix(wk), mix(1.0)
        ln = lambda X: np.linalg.norm(X[e[:, 0]] - X[e[:, 1]], axis=1)
        l0 = ln(P)
        lay, rm, r1, rf = ln(P1) / l0, ln(Xm) / l0, ln(X1) / l0, ln(Xf) / l0
        own = r["unf"].length(r["u"][e[:, 0]], r["u"][e[:, 1]], 12, Va) / len0
        f0 = np.sign(ct.facing(tb, P, N0))
        tm, t1, tf = (np.sign(ct.facing(tb, X, N)) != f0 for X, N in ((Xm, Nm), (X1, N1), (Xf, Nf)))
        fa = ct._unit(un(hs.Ab.T[c1.face], Va))                  # A's posed triangle under each B' point (its carrier)
        fa0 = ct._unit(un(hs.Ab.T[c1.face], hs.Ab.V0))
        ng, n1, nl = ct._unit(un(tb, Xm)), ct._unit(un(tb, X1)), ct._unit(un(tb, P1))
        area = lambda X, N: 0.5 * (un(tb, X) * ct._unit(N[tb].sum(1))).sum(1)
        ql, q0, q1 = area(P1, r["Nf"]) / area(P, N0), tri_quality(P, tb), tri_quality(P1, tb)
        lim = own.max() + 0.15
        FA, NA, pa = np.zeros_like(P), np.zeros_like(P), r["unf"].tri[ta]   # A's OWN surface under the lay's triangles:
        FA[act] = np.einsum("nk,nkj->nj", bta, Va[r["unf"].vid][pa])        # the feet on A (no height), A's normals there
        NA[act] = ct._unit(np.einsum("nk,nkj->nj", bta, r["unf"].normals(Va)[pa]))
        oa, oc = ct.facing(tb, FA, NA) <= 0, corner_facing(FA, NA, tb)
        ids = lambda v: "/".join(f"{int(x)}{tag[x]}" for x in v) + " (mesh " + "/".join(str(int(hs.pts[s][x])) for x in v) + ")"
        fm, ff = fold_angles(tb, Xm, b), fold_angles(tb, Xf, b)
        print(f"== {q} ({s}) w {wk:.2f}: turned map {int(tm.sum())} {np.nonzero(tm)[0].tolist()}, at w = 1 {int(t1.sum())}, fill {int(tf.sum())}; map edge max {rm.max():.2f}, A's own max {own.max():.2f}"
              f" (limit {lim:.2f}), over the limit {int((rm > lim).sum())}; mean lay {lay.mean():.2f}, map {rm.mean():.2f}, A {own.mean():.2f};"
              f" A'S OWN surface under the band's triangles: turned {int(oa.sum())} {np.nonzero(oa)[0].tolist()}, a corner facing off {int((oc <= 0).any(1).sum())};"
              f" fill max {rf.max():.2f}; SHORTEST map {rm.min():.2f} (edge {int(rm.argmin())} {ids(e[rm.argmin()])}: lay {lay[rm.argmin()]:.2f}, A's own along it {own[rm.argmin()]:.2f}, fill {rf[rm.argmin()]:.2f}), A's own {own.min():.2f} (map / A's {rm.min() / own.min():.2f}), fill {rf.min():.2f};"
              f" lay rest edge {lay.min():.2f}..{lay.max():.2f}; FOLD deg (band edges' dihedral) map max {fm.max():.1f} p95 {np.percentile(fm, 95):.1f},"
              f" fill max {ff.max():.1f} p95 {np.percentile(ff, 95):.1f}", flush=True)
        for t in np.nonzero(tm | t1)[0]:
            v = tb[t]
            ga, ga0 = (fa[v] * ng[t]).sum(1), (fa0[v] * nl[t]).sum(1)
            ap = min(fa[v[a]] @ fa[v[c]] for a, c in ((0, 1), (1, 2), (2, 0)))
            print(f"   tri {t} {ids(v)}: turned map {bool(tm[t])}, w = 1 {bool(t1[t])}, fill {bool(tf[t])}; lay area / B's {ql[t]:+.2f}, quality B {q0[t]:.2f} lay {q1[t]:.2f};"
                  f" its normal . A's carrier normals: lay rest {ga0.round(2).tolist()}, pose {ga.round(2).tolist()} (w = 1 {(fa[v] * n1[t]).sum(1).round(2).tolist()});"
                  f" carriers' least mutual normal dot in the pose {ap:.2f} (rest {min(fa0[v[a]] @ fa0[v[c]] for a, c in ((0, 1), (1, 2), (2, 0))):.2f});"
                  f" the mixed normals . its normal {(Nm[v] * ng[t]).sum(1).round(2).tolist()};"
                  f" A's own under it: turned {bool(oa[t])}, corners {oc[t].round(2).tolist()}")
        bad = set(tb[tm | t1].ravel().tolist())
        for x in np.argsort(-rm)[:max(top, int((rm > lim).sum()))]:
            print(f"   edge {x} {ids(e[x])}: map {rm[x]:.2f} ({rm[x] - lim:+.2f} on the limit) = lay {lay[x]:.2f} x pose {rm[x] / lay[x]:.2f}; at w = 1 {r1[x]:.2f}; A's own along it {own[x]:.2f};"
                  f" fill {rf[x]:.2f}; ends in a turned triangle {sum(int(p) in bad for p in e[x])}")
        x = np.argsort(-lay)[:top]
        print("   the lay's longest rest edges: " + "; ".join(f"{i} {ids(e[i])} {lay[i]:.2f}" for i in x))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=["build", "target", "sheet", "turned"])
    ap.add_argument("--snap", action="store_true", help="import carried_target from out/shoulder/snap (a frozen copy)")
    ap.add_argument("--rows", default="", help="build: lay rows (int); sheet: pose:view,pose:view,... (default: five rows, see SHEET_ROWS)")
    ap.add_argument("--relax", action="store_true", help="build: relax the lay on real lengths (slow; the left fails, see strip_rest.md)")
    ap.add_argument("--map", action="store_true", help="target: the lay as a carry map blended in by arm elevation, B's rest kept")
    ap.add_argument("--out", default="armpit_map", help="sheet: output name")
    ap.add_argument("--poses", default="", help="comma-separated pose names, or 'named' (the config's list); none: all of poses.npz")
    ap.add_argument("--lay", default="l19", choices=["l18", "l19"], help="l19: lay 2 (out/shoulder/strip_rest.npz); l18: the old linear lay (strip_rest_l18.npz)")
    ap.add_argument("--side", default="", help="build: the apex row's side of the line per body side, e.g. l=-1,r=1 (0: the nearer)")
    ap.add_argument("--only", default="", help="build: lay this side only (l or r), the other kept from the npz on disk")
    ap.add_argument("--repair", action="store_true", help="build: no solve; the npz's lay untangled (its faults repaired) and stored")
    ap.add_argument("--fix", default="", help="build: untangle keywords as JSON, e.g. {\"lim\": [0.6, 1.6]}")
    ap.add_argument("--set", default="", help="build: lay2 keywords as JSON, e.g. {\"iters\": 800}")
    ap.add_argument("--file", default="", help="the lay's npz in out/shoulder (build writes it; target / turned / sheet read it); default strip_rest.npz")
    ap.add_argument("--start", default="", help="build: a lay npz in out/shoulder; lay2 starts from its plane points and apex row (no walk)")
    a = ap.parse_args()
    HER["lim"] = (0.82, 1.28) if a.relax else None
    if a.lay == "l18":
        HER["lay"], HER["out"] = 1, HER["old_out"]
    HER["only"], HER["repair"], HER["start"] = a.only, a.repair, a.start
    if a.file:
        HER["out"] = a.file
    HER["untangle"] = {k: tuple(v) if isinstance(v, list) else v for k, v in json.loads(a.fix or "{}").items()}
    HER["side"].update({k: int(v) for k, v in (x.split("=") for x in a.side.split(",") if x)})
    HER["lay2"] = {**HER["lay2"], **{k: tuple(v) if isinstance(v, list) else v for k, v in json.loads(a.set or "{}").items()}}
    print(f"carried_target: {ct.__file__}")
    hs = HerStrip()
    if a.cmd == "build":
        return cmd_build(hs, int(a.rows) if a.rows else HER["rows"])
    hs.load()
    if a.cmd == "turned":
        return cmd_turned(hs, HER["named"] if a.poses in ("", "named") else [q for q in a.poses.split(",") if q])
    if a.cmd == "target" and a.map:
        return cmd_map(hs, HER["named"] if a.poses in ("", "named") else [q for q in a.poses.split(",") if q])
    if a.cmd == "target":
        return cmd_target(hs, HER["named"] if a.poses == "named" else [p for p in a.poses.split(",") if p])
    cmd_sheet(hs, a.rows, a.out)


if __name__ == "__main__":
    main()
