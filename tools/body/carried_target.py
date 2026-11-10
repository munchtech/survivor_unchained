"""The carried target: a reference mesh's own posed surface, carried onto another mesh's points through the REST
correspondence. No solver.

A rigged mesh that deforms well (the reference) lends its posed shape to a mesh of another topology whose rest shape
agrees with it (the source). Each source point remembers its closest point on the reference's rest surface (triangle +
barycentrics) and its rest offset from that point. In a pose the point is that barycentric point on the reference's posed
triangle, plus the offset turned by the reference's local surface rotation (smooth per-vertex frames, no faceting).

    car = Carrier(ref_V0, ref_T, P0, N0, edges=E)        # once: the correspondence of points P0 (unit normals N0)
    X = car.carry(ref_V)                                 # per pose: the reference's posed vertices -> the points

Where the points' mesh bridges a fold that the reference keeps as two walls, a carried edge would take the whole opening
of the fold. With the points' edges E the carrier finds those bridges at rest, and fills a pocket of rows around them
from its carried neighbours in every pose (the pocket rule, see Carrier).

Posing the reference like the source, for a reference skeleton that is driven by world turns:

    order = transfer_order(ref_names, ref_parent, index, bone_map, only, skip)
    turns = transfer_turns(G, rest, index, ref_index, ref_parent, bone_map, order)
    M = anchor_align(G[a], rest[a], refG0[ra], refG[ra])  # the reference's posed surface onto the source's skeleton

THE RELATIVE CARRY (the default, "carry": "relative"). The reference lends only the deformation of a region's OWN
bones; every other bone's deformation stays the source's own skinning. Per pose: Gp = the PART pose (the rest with the
local transforms of the region's bones only, local_pose, then the rig's driver), c = the reference posed by Gp's turns
and carried (pocket filled), all in the rest frame of the region's parent; then per point

    X = published(G) + M (c - published(Gp)),   M = L(G) L(Gp)^-1   (relative_place; L = the point's blended skin matrix)

which is L(G) L(Gp)^-1 c plus the source's own shape correctives that the other bones drive. A point skinned to the
region's bones alone gets the parent's rigid motion; wherever the reference and the source agree with the region's
bones moved alone, X is the published surface, whatever the trunk and neck do. ("absolute": the reference posed by the
whole pose and aligned by one rigid anchor, as before 10 Nov: the two bodies' trunk and neck skinning then disagree by
centimetres at the region's border.)

The top of this file is the general core: arrays in, arrays out, no body, bone or path names (it runs on any rigged
mesh). The bottom is HER CONFIG: her body B's shoulder region against her old body A, and the CLI.

    python tools/body/carried_target.py test
    python tools/body/carried_target.py target [--poses name,name]

`target` with no --poses writes out/shoulder/target_a.npz (X [poses, region points, 3], name, side, kind, info, params:
the layout of target.npz, same pose order; plus pocket_l / pocket_r, the pocket's points, and bridge_l / bridge_r [nb, 2],
the bridge edges, as local indices into each side's region points); a subset writes target_a_dev.npz.
"""
from __future__ import annotations

import argparse
import contextlib
import json
import re
import sys
import time
from pathlib import Path

import numpy as np
import scipy.sparse as sp
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from surfdist import closest_on_tris  # noqa: E402

AREA_EPS = 1e-14          # m^2: a triangle under this is degenerate (no frame, no candidate)


# ============================================================================================ the general core ==
def polar(F):
    """The nearest rotation of each 3x3 in F [..., 3, 3] (det +1)."""
    U, _, Vt = np.linalg.svd(F)
    neg = np.linalg.det(U @ Vt) < 0
    U = U * np.where(neg, -1.0, 1.0)[..., None, None] ** np.array([0, 0, 1])      # flip the weakest axis only
    return U @ Vt


def _frames(V, T):
    """Per triangle: [e1, e2, n] as columns [m, 3, 3] (n the unit normal) and the area [m]."""
    a = V[T[:, 0]]
    e1, e2 = V[T[:, 1]] - a, V[T[:, 2]] - a
    n = np.cross(e1, e2)
    ln = np.linalg.norm(n, axis=1)
    return np.stack([e1, e2, n / np.maximum(ln, 1e-30)[:, None]], 2), 0.5 * ln


def _bary(q, a, b, c):
    """Barycentrics [n, 3] of points q lying on triangles (a, b, c), clamped onto the triangle."""
    v0, v1, v2 = b - a, c - a, q - a
    d00, d01, d11 = (v0 * v0).sum(1), (v0 * v1).sum(1), (v1 * v1).sum(1)
    d20, d21 = (v2 * v0).sum(1), (v2 * v1).sum(1)
    den = np.maximum(d00 * d11 - d01 * d01, 1e-300)
    v, w = (d11 * d20 - d01 * d21) / den, (d00 * d21 - d01 * d20) / den
    B = np.clip(np.stack([1 - v - w, v, w], 1), 0, 1)
    return B / B.sum(1, keepdims=True)


def _angle(a, b):
    """The angle in degrees between unit vectors, row by row."""
    return np.degrees(np.arccos(np.clip((a * b).sum(1), -1.0, 1.0)))


def bridge_edges(nref, N0, edges, bridge_deg=60.0):
    """The mask [m] of the edges that bridge a fold of the reference. Found at rest only.

    nref [n, 3]: the rest normal of each point's matched reference face; N0 [n, 3]: the points' own rest normals;
    edges [m, 2]: the points' own edges. An edge is a bridge when its ends' reference normals disagree by more than
    `bridge_deg` degrees beyond what the points' own normals do: the reference has two walls there and the points'
    mesh crosses from one to the other on a single edge.
    """
    i, j = edges[:, 0], edges[:, 1]
    return _angle(nref[i], nref[j]) - _angle(N0[i], N0[j]) > bridge_deg


def _adjacency(n, edges, w=None):
    """The symmetric adjacency [n, n] of the edges (weights w per edge, 1 if None; an edge listed twice counts once)."""
    e = np.unique(np.sort(np.asarray(edges, np.int64), axis=1), axis=0, return_index=True)[1]
    i, j = edges[e, 0], edges[e, 1]
    A = sp.coo_matrix((np.ones(len(e)) if w is None else np.asarray(w, float)[e], (i, j)), (n, n))
    return (A + A.T).tocsr()


def rows_around(n, edges, seeds, rows):
    """The mask [n] of the points within `rows` edges of a seed point (the seeds included), by BFS over the edges."""
    A = _adjacency(n, edges)
    m = np.zeros(n, bool)
    m[np.asarray(seeds, np.int64)] = True
    for _ in range(int(rows)):
        m = m | ((A @ m.astype(float)) > 0)
    return m


class Pocket:
    """A harmonic fill of a set of points from their neighbours, keeping the rest shape's differential coordinates.

    P0 [n, 3] the rest points, edges [m, 2] their edges, mask [n] the pocket. L is the graph Laplacian over the edges
    and delta = L P0. fill(X, R) leaves every point outside the pocket as it is and solves the pocket's points from
    L_pp x_p = (R delta)_p - L_pb x_b: an opening between the pocket's two sides is shared by its rows instead of
    taken by one edge. L_pp is factored once. weight "uniform": every edge weighs 1, each row takes the same LENGTH of
    the opening (a short edge stretches by a larger ratio than a long one). weight "length": an edge weighs mean rest
    length / its rest length (springs of one material), each row takes the same RATIO.
    """

    def __init__(self, P0, edges, mask, weight="length"):
        from scipy.sparse.csgraph import connected_components
        from scipy.sparse.linalg import factorized
        P0 = np.asarray(P0, float)
        n = len(P0)
        w = None
        if weight == "length":
            l0 = np.maximum(np.linalg.norm(P0[edges[:, 0]] - P0[edges[:, 1]], axis=1), 1e-12)
            w = l0.mean() / l0
        elif weight != "uniform":
            raise ValueError(f"weight {weight!r}: uniform or length")
        A = _adjacency(n, edges, w)
        deg = np.asarray(A.sum(1)).ravel()
        L = (sp.diags(deg) - A).tocsr()
        self.p = np.nonzero(mask)[0]
        Lp = L[self.p]
        out = np.nonzero(~np.asarray(mask, bool))[0]
        Lpb = Lp[:, out].tocsc()
        ring = np.nonzero(np.diff(Lpb.indptr) > 0)[0]
        self.b = out[ring]                                   # the pocket's neighbours: they hold it
        self._Lpb = Lpb[:, ring].tocsr()
        Lpp = Lp[:, self.p].tocsc()
        self._Lpp = Lpp.tocsr()
        nc, lab = connected_components(Lpp, directed=False)
        held = np.zeros(nc, bool)
        held[lab[np.diff(self._Lpb.indptr) > 0]] = True
        if not held.all():
            raise ValueError("a pocket component has no neighbour outside the pocket: nothing holds it")
        self._solve = factorized(Lpp)
        self.delta = (L @ P0)[self.p]
        self._avg = sp.diags(1.0 / deg[self.p]) @ A[self.p]  # a pocket point <- the mean of its neighbours
        e = np.asarray(edges, np.int64)
        touch = np.asarray(mask, bool)[e].any(1)
        self.edges = e[touch]                                # every edge with an end in the pocket
        self.w, self.P0 = (np.ones(len(e)) if w is None else w)[touch], P0   # their weights; the rest

    def smooth_rotations(self, R, passes):
        """The pocket points' rotations after `passes` Jacobi averaging passes (the others held), polar'd [len(p), 3, 3]."""
        F = np.asarray(R, float).reshape(len(R), 9).copy()
        for _ in range(int(passes)):
            F[self.p] = self._avg @ F
        return polar(F[self.p].reshape(-1, 3, 3))

    def fill(self, X, R=None, passes=8):
        """X [n, 3] with the pocket's points filled. R [n, 3, 3]: the per-point rotations rest -> posed (None: identity)."""
        X = np.array(X, float)
        d = self.delta if R is None else np.einsum("nij,nj->ni", self.smooth_rotations(R, passes), self.delta)
        rhs = d - self._Lpb @ X[self.b]
        X[self.p] = np.stack([self._solve(np.ascontiguousarray(rhs[:, c])) for c in range(3)], 1)
        return X


def _unit(v):
    return v / np.maximum(np.linalg.norm(v, axis=-1, keepdims=True), 1e-30)


def facing(tris, X, N):
    """Per triangle [f]: its normal dotted with the sum of N at its corners. The sign says which way it faces."""
    n = np.cross(X[tris[:, 1]] - X[tris[:, 0]], X[tris[:, 2]] - X[tris[:, 0]])
    return (n * N[tris].sum(1)).sum(1)


class Band(Pocket):
    """The pocket as a band that SLIDES ON THE REFERENCE'S POSED SURFACE (the hollow of an opened fold is the reference's).

    A band point is a point of the reference's surface (a triangle and barycentrics, at rest its closest point) plus
    its rest offset: x = S + R(S) (d0 + h (n0(S) - n0)), R(S) the reference's local rotation at S, n0(S) its smooth
    REST normal there, h = d0 . n0 the point's height (the offset keeps its height over the surface wherever the point
    goes; a point that has not moved is the plain carry). A pose moves S only. The points outside hold the band at
    their carried positions, and the band's points move along the surface until the pull of their edges is in
    balance in the tangent plane: T^t (R(S) c - L x) = 0 at every band point, L the pocket's Laplacian, T the tangent
    plane of the reference's posed smooth normal at S, c = the tangent part of delta at rest. With "length" weights
    the opening is shared at one RATIO per edge. At rest the balance holds as it is (T^t (c - delta) = 0): the rest is
    a fixed point, the slide starts from it in every pose and vanishes as the fold closes.

    Solved by Newton steps in the tangent planes (T^t Lpp T) s = T^t (R c - L x), each step cut to `cap` and landed on
    the reference by the closest point over the triangles around the point's own triangle (two rings by shared
    vertices, on the posed mesh): a walk on the mesh, never a projection through a fold onto its other wall.

    V0, T: the reference's rest mesh. pt: its triangles the band may walk on (the patch), rim [len(pt)]: those on the
    patch's edge. vg [nv]: each reference vertex's row in the vertex frames (Rv, nv of Carrier._vertex_frames).
    face, bary, d0, n0 [n]: the points' correspondence and smooth rest normals. nv0: the rest vertex normals.
    step: `cap` as a part of the patch's median edge; tol: converged when the largest step is under tol * cap.
    """

    def __init__(self, P0, edges, mask, weight, V0, T, pt, rim, vg, face, bary, d0, n0, nv0, step=0.5, tol=1e-3, iters=200):
        super().__init__(P0, edges, mask, weight)
        p, T = self.p, np.asarray(T, np.int64)
        self.tv, self.rim = T[pt], np.asarray(rim, bool)
        self.tg = vg[self.tv]
        mp = len(pt)
        I = sp.csr_matrix((np.ones(3 * mp), (np.repeat(np.arange(mp), 3), self.tg.ravel())), (mp, int(vg.max()) + 1))
        R1 = (I @ I.T).tocsr()
        R1.data[:] = 1.0
        R2 = (R1 @ R1).tocsr()                               # triangles two rings apart by shared (welded) vertices
        cnt = np.diff(R2.indptr)
        self.ring = -np.ones((mp, int(cnt.max())), np.int64)
        self.ring[np.repeat(np.arange(mp), cnt), np.arange(R2.nnz) - np.repeat(R2.indptr[:-1], cnt)] = R2.indices
        inv = -np.ones(len(T), np.int64)
        inv[pt] = np.arange(mp)
        self.t0, self.b0 = inv[face[p]], bary[p]
        if (self.t0 < 0).any():
            raise ValueError("a band point's matched triangle is not in the patch")
        self.d0, self.n0, self.nv0 = d0[p], n0[p], nv0
        self.h = (self.d0 * self.n0).sum(1)
        self.c = self.delta - (self.delta * self.n0).sum(1)[:, None] * self.n0
        self.cap = step * float(np.median(np.linalg.norm(V0[self.tv] - V0[self.tv[:, [1, 2, 0]]], axis=2)))
        self.tol, self.iters = tol * self.cap, int(iters)
        C = self._Lpp.tocoo()
        self._i, self._j, self._v = C.row, C.col, C.data
        self._r = (2 * C.row[:, None] + np.array([0, 0, 1, 1])).ravel()
        self._c = (2 * C.col[:, None] + np.array([0, 1, 0, 1])).ravel()

    def _land(self, q, t, V):
        """The points q [n, 3] back on the mesh: (triangle, barycentrics) of the closest point around triangles t."""
        cand = self.ring[t]
        n, k = cand.shape
        tv = self.tv[np.maximum(cand, 0)].reshape(n * k, 3)
        P = np.repeat(q, k, axis=0)
        A, B, C = V[tv[:, 0]], V[tv[:, 1]], V[tv[:, 2]]
        Q = closest_on_tris(P, A, B, C)
        d = np.linalg.norm(P - Q, axis=1)
        d = np.where(np.isfinite(d) & (cand.ravel() >= 0), d, np.inf).reshape(n, k)
        j = np.arange(n) * k + d.argmin(1)
        return cand.ravel()[j], _bary(Q[j], A[j], B[j], C[j])

    def slide(self, ref_V, Rv, nv, X):
        """(the band's points [len(p), 3], stats, the reference's posed normal at each) for the posed reference ref_V.

        Rv, nv: the reference's vertex rotations and posed vertex normals (Carrier._vertex_frames); X [n, 3]: the
        carried points (the holders are read from it). stats: iters (Newton steps taken), step (the last step's
        largest move, m: under `tol` when converged), rim (points that ended on the patch's edge: the walk was cut).
        """
        from scipy.sparse.linalg import spsolve
        V = np.asarray(ref_V, float)
        t, be = self.t0.copy(), self.b0.copy()
        n = len(t)
        hold = self._Lpb @ X[self.b]
        for it in range(self.iters + 1):
            tv, tg = self.tv[t], self.tg[t]
            S = np.einsum("nk,nkj->nj", be, V[tv])
            R = polar(np.einsum("nk,nkij->nij", be, Rv[tg]))
            ns = _unit(np.einsum("nk,nkj->nj", be, self.nv0[tg]))
            x = S + np.einsum("nij,nj->ni", R, self.d0 + self.h[:, None] * (ns - self.n0))
            nrm = _unit(np.einsum("nk,nkj->nj", be, nv[tg]))
            a = V[tv[:, 1]] - V[tv[:, 0]]
            e1 = _unit(a - (a * nrm).sum(1)[:, None] * nrm)
            Tb = np.stack([e1, np.cross(nrm, e1)], 2)                                  # [n, 3, 2]
            f = np.einsum("nij,nj->ni", R, self.c) - self._Lpp @ x - hold
            g = np.einsum("nki,nk->ni", Tb, f)
            blk = self._v[:, None, None] * np.einsum("eki,ekj->eij", Tb[self._i], Tb[self._j])
            s = spsolve(sp.csc_matrix((blk.ravel(), (self._r, self._c)), (2 * n, 2 * n)), g.ravel()).reshape(n, 2)
            smax = float(np.linalg.norm(s, axis=1).max())
            if smax < self.tol or it == self.iters:
                break
            t, be = self._land(S + np.einsum("nki,ni->nk", Tb, s) * min(1.0, self.cap / smax), t, V)
        return x, {"iters": it, "step": smax, "rim": int(self.rim[t].sum())}, np.einsum("nij,nj->ni", R, ns)


def surface_distance(P, V, T, k=48):
    """The distance [n] from points P to the mesh (V, T): the closest point over the k triangles nearest by centroid,
    whatever their facing."""
    V, T = np.asarray(V, float), np.asarray(T, np.int64)
    kk = min(k, len(T))
    _, cand = cKDTree(V[T].mean(1)).query(P, k=kk)
    cand = cand.reshape(len(P), kk)
    best = np.full(len(P), np.inf)
    for j in range(kk):
        tv = T[cand[:, j]]
        d = np.linalg.norm(P - closest_on_tris(P, V[tv[:, 0]], V[tv[:, 1]], V[tv[:, 2]]), axis=1)
        best = np.where(np.isfinite(d) & (d < best), d, best)
    return best


class Carrier:
    """The rest correspondence of points P0 [n, 3] (unit normals N0) to a reference mesh (ref_V0 [nv, 3], ref_T [m, 3]).

    Per point: among the k triangles nearest by centroid, those within `rad` whose rest face normal faces the same way
    as the point's normal (dot > 0) are candidates, and the one with the least `distance + nw * rad * (1 - dot)` wins.
    nw = 0 (the default) is the plain closest point. Kept: `tri` [n, 3] vertex ids, `bary` [n, 3], `d0` = P0 - closest
    point, `face` the triangle, `nref` its rest normal, `ok` (False where no candidate passed: those take the closest
    of the k without the tests; count them with (~ok).sum()).

    The local rotation is smooth: a vertex's rotation is the polar of the area-weighted sum of its triangles' rest ->
    posed rotations (vertices doubled along seams are welded by rest position, `weld` m), a point's is the polar of the
    barycentric sum of its three vertices' rotations.

    THE POCKET RULE (needs `edges` [m, 2], the points' own edges in local indices). Where the points' mesh bridges a
    tight fold that the reference keeps as two walls, the two ends of one edge land on opposite walls, and a pose that
    opens the fold would put the whole opening on that edge. Those edges are found at rest (bridge_edges, `bridge_deg`),
    the points within `pocket_rows` edges of a bridge end are the pocket (rows_around; never a point of `hold` [n]
    bool, e.g. a region's blended border), and in every pose the pocket is not carried alone but shares the opening
    over its rows, held by its carried neighbours. pocket_rows = 0, or no edges, or no bridge: the plain carry.
    Kept: `bridge` [nb, 2] the bridge edges, `pocket` (a Band or a Pocket, or None), `stats` of the last carry.
      pocket_mode "slide": the pocket is a Band that slides on the reference's posed surface (Band; `band_step`,
        `band_tol`, `band_iters`). The hollow is the reference's own; rows cost nothing in distance from it. `stats`:
        iters, step, rim (Band.slide) and, with the points' triangles `tris` [f, 3], flip: the band triangles that
        face the other way against the reference's normal than they do at rest.
      pocket_mode "fill": the harmonic fill (Pocket.fill with the carrier's rotations smoothed across the pocket by
        `frame_passes` passes). It SPANS the opened fold like a web: more rows, further off the reference's hollow.
    """

    def __init__(self, ref_V0, ref_T, P0, N0, rad=0.05, k=64, nw=0.0, weld=1e-6, edges=None, bridge_deg=60.0,
                 pocket_rows=4, frame_passes=8, pocket_weight="length", pocket_mode="fill", hold=None, tris=None,
                 band_step=0.5, band_tol=1e-3, band_iters=200):
        if pocket_mode not in ("slide", "fill"):
            raise ValueError(f"pocket_mode {pocket_mode!r}: slide or fill")
        V0, T = np.asarray(ref_V0, float), np.asarray(ref_T, np.int64)
        P0, N0 = np.asarray(P0, float), np.asarray(N0, float)
        n = len(P0)
        E0, area = _frames(V0, T)
        live = np.nonzero(area > AREA_EPS)[0]
        fn = E0[live][:, :, 2]
        kk = min(k, len(live))
        dist, cand = cKDTree(V0[T[live]].mean(1)).query(P0, k=kk)
        dist, cand = dist.reshape(n, kk), cand.reshape(n, kk)
        best, pick = np.full((2, n), np.inf), np.zeros((2, n), np.int64)
        for j in range(kk):
            t = cand[:, j]
            tv = T[live[t]]
            q = closest_on_tris(P0, V0[tv[:, 0]], V0[tv[:, 1]], V0[tv[:, 2]])
            d = np.linalg.norm(P0 - q, axis=1)
            dot = np.einsum("ij,ij->i", fn[t], N0)
            sc = d + nw * rad * (1 - dot)
            for r, m, v in ((0, (dist[:, j] <= rad) & (dot > 0) & (sc < best[0]), sc), (1, d < best[1], d)):
                best[r][m], pick[r][m] = v[m], live[t[m]]
        self.ok = np.isfinite(best[0])
        self.face = np.where(self.ok, pick[0], pick[1])
        self.tri = T[self.face]
        A, B, C = (V0[self.tri[:, i]] for i in range(3))
        self.bary = _bary(closest_on_tris(P0, A, B, C), A, B, C)
        self.d0 = P0 - np.einsum("nk,nkj->nj", self.bary, V0[self.tri])
        self.rad, self.k, self.nw = rad, k, nw
        # the pocket rule: the bridges and the pocket's points
        self.nref = E0[self.face][:, :, 2]
        self.bridge_deg, self.pocket_rows, self.frame_passes = bridge_deg, pocket_rows, frame_passes
        self.bridge, self.pocket, self.stats = np.zeros((0, 2), np.int64), None, {}
        mask = np.zeros(n, bool)
        if edges is not None and len(edges):
            edges = np.asarray(edges, np.int64)
            self.bridge = edges[bridge_edges(self.nref, N0, edges, bridge_deg)]
            if len(self.bridge) and pocket_rows > 0:
                mask = rows_around(n, edges, np.unique(self.bridge), pocket_rows)
                if hold is not None:
                    mask &= ~np.asarray(hold, bool)
        slide = bool(mask.any()) and pocket_mode == "slide"
        _, grp = np.unique(np.round(V0 / weld).astype(np.int64), axis=0, return_inverse=True)
        grp = np.asarray(grp).ravel()
        used = grp[self.tri].ravel()
        if slide:                        # the patch: the reference's triangles within the band's own width of its rest feet
            e = edges[mask[edges].any(1)]
            reach = pocket_rows * float(np.linalg.norm(P0[e[:, 0]] - P0[e[:, 1]], axis=1).mean())
            near = cKDTree(P0[mask] - self.d0[mask]).query(V0)[0] <= reach
            pt = np.nonzero(near[T].any(1) & (area > AREA_EPS))[0]
            used = np.concatenate([used, grp[T[pt]].ravel()])
        # the frames: only the triangles around the vertices in use
        used = np.unique(used)
        loc = -np.ones(int(grp.max()) + 1, np.int64)
        loc[used] = np.arange(len(used))
        tg = loc[grp[T]]
        inc = np.nonzero((tg >= 0).any(1) & (area > AREA_EPS))[0]
        self._T = T[inc]
        self._E0inv = np.linalg.inv(E0[inc])
        rows, cols, w = tg[inc].ravel(), np.repeat(np.arange(len(inc)), 3), np.repeat(area[inc], 3)
        m = rows >= 0
        self._W = sp.csr_matrix((w[m], (rows[m], cols[m])), (len(used), len(inc)))
        self._pg = loc[grp[self.tri]]
        nv0 = _unit(self._W @ E0[inc][:, :, 2])              # the reference's smooth rest normals, per vertex in use
        self.n0 = _unit(np.einsum("nk,nkj->nj", self.bary, nv0[self._pg]))               # and at each point's rest foot
        self._tris = self._face0 = None
        if slide:
            full = np.bincount(grp[T[live]].ravel(), minlength=len(loc))
            mine = np.bincount(grp[T[pt]].ravel(), minlength=len(loc))
            rim = (mine[grp[T[pt]]] < full[grp[T[pt]]]).any(1)
            self.pocket = Band(P0, edges, mask, pocket_weight, V0, T, pt, rim, loc[grp], self.face, self.bary, self.d0,
                               self.n0, nv0, band_step, band_tol, band_iters)
            if tris is not None:         # the points' triangles that touch the band, and which way they face at rest
                tris = np.asarray(tris, np.int64)
                self._tris = tris[mask[tris].any(1)]
                self._face0 = np.sign(facing(self._tris, P0, self.n0))
        elif mask.any():
            self.pocket = Pocket(P0, edges, mask, pocket_weight)

    def _vertex_frames(self, ref_V):
        """(Rv [vertices in use, 3, 3] the rotations rest -> posed, nv [vertices in use, 3] the posed smooth normals)."""
        E, _ = _frames(np.asarray(ref_V, float), self._T)
        Rt = polar(E @ self._E0inv)
        return polar((self._W @ Rt.reshape(-1, 9)).reshape(-1, 3, 3)), _unit(self._W @ E[:, :, 2])

    def rotations(self, ref_V):
        """The reference's local surface rotation rest -> posed at each point [n, 3, 3]."""
        return polar(np.einsum("nk,nkij->nij", self.bary, self._vertex_frames(ref_V)[0][self._pg]))

    def carry(self, ref_V, fill=True, both=False):
        """The points on the reference's posed surface ref_V [nv, 3] -> [n, 3], the pocket slid (or filled).

        fill=False: the carry alone (every point on its own matched face). both=True: (with the pocket, carried alone).
        """
        ref_V = np.asarray(ref_V, float)
        Rv, nv = self._vertex_frames(ref_V)
        R = polar(np.einsum("nk,nkij->nij", self.bary, Rv[self._pg]))
        raw = np.einsum("nk,nkj->nj", self.bary, ref_V[self.tri]) + np.einsum("nij,nj->ni", R, self.d0)
        X, self.stats = raw, {}
        if (fill or both) and isinstance(self.pocket, Band):
            X = raw.copy()
            X[self.pocket.p], self.stats, Np = self.pocket.slide(ref_V, Rv, nv, raw)
            if self._tris is not None:
                N = np.einsum("nij,nj->ni", R, self.n0)
                N[self.pocket.p] = Np
                self.stats["flip"] = int((np.sign(facing(self._tris, X, N)) != self._face0).sum())
        elif (fill or both) and self.pocket is not None:
            X = self.pocket.fill(raw, R, self.frame_passes)
        if both:
            return X, raw
        return X if fill else raw


def world_turn(G, rest, j):
    """Bone j's world rotation from its rest to the pose G."""
    return polar(G[j][:3, :3] @ np.linalg.inv(rest[j][:3, :3]))


def transfer_order(ref_names, ref_parent, index, bone_map=None, only=None, skip=()):
    """(order, left): the reference bones to pose, parents first, and those left at rest.

    A reference bone is posed when the source has its bone (`bone_map`: reference name -> source name; unlisted bones
    map by name), it is not in `skip` (the bones the reference's own rig drives) and, if `only` is given, it is in it.
    """
    bone_map = bone_map or {}
    depth = []
    for i in range(len(ref_names)):
        d, k = 0, ref_parent[i]
        while k >= 0:
            d, k = d + 1, ref_parent[k]
        depth.append(d)
    take = [i for i in np.argsort(depth, kind="stable")
            if bone_map.get(ref_names[i], ref_names[i]) in index and ref_names[i] not in skip
            and (only is None or ref_names[i] in only)]
    order = [ref_names[i] for i in take]
    return order, [x for x in ref_names if x not in set(order)]


def transfer_turns(G, rest, index, ref_index, ref_parent, bone_map, order):
    """The [(reference bone name, world turn)] that poses a turn-driven reference skeleton like the source.

    G, rest [nb, 4, 4]: the source's posed and rest globals; index: source bone name -> row. A turn is a world rotation
    applied on the bone's current global, so each bone gets its source bone's world turn with its nearest posed
    ancestor's taken off. `order` lists the reference bones parents first (transfer_order).
    """
    bone_map = bone_map or {}
    turns, done = [], {}
    for rn in order:
        sn = bone_map.get(rn, rn)
        if rn not in ref_index or sn not in index:
            continue
        Rb = world_turn(G, rest, index[sn])
        k, Rp = ref_parent[ref_index[rn]], np.eye(3)
        while k >= 0 and k not in done:
            k = ref_parent[k]
        if k >= 0:
            Rp = done[k]
        turns.append((rn, Rb @ Rp.T))
        done[ref_index[rn]] = Rb
    return turns


def anchor_align(G_anchor, rest_anchor, refG0_anchor, refG_anchor):
    """The 4x4 taking the reference's posed surface onto the source's skeleton at an anchor bone.

    A point rigid to the reference's anchor lands where the source's anchor carries its rest position (the two share
    rest joints there). The rotation part is re-orthonormalized.
    """
    M = G_anchor @ np.linalg.inv(rest_anchor) @ refG0_anchor @ np.linalg.inv(refG_anchor)
    M[:3, :3] = polar(M[:3, :3])
    M[3] = 0, 0, 0, 1
    return M


def local_pose(G, rest, parent, order, keep):
    """The globals [nb, 4, 4] of the rest pose with the LOCAL transforms of the bones in `keep` taken from the pose G.

    order: the bones parents first. Every other bone rides its parent at its rest local (a rig's driven bones are then
    placed by its driver, which expects them so).
    """
    out = np.array(rest, float)
    for k in order:
        pk = parent[k]
        src = G if k in keep else rest
        L = np.linalg.inv(src[pk]) @ src[k] if pk >= 0 else src[k]
        out[k] = out[pk] @ L if pk >= 0 else L
    return out


def blend_skin(S, J, W):
    """Each point's blended skin matrix [n, 4, 4] = sum_k W[:, k] S[J[:, k]] (S [nb, 4, 4]: globals @ inverse binds)."""
    return np.einsum("nk,nkij->nij", W, S[J])


def relative_place(Sf, Sp, J, W, lo=0.15, hi=0.35):
    """(M [n, 3, 3], sigma [n], share [n]): what takes a point's offset in a PART pose into the FULL pose by the points'
    own skinning: M = L_full L_part^-1 (the 3x3 parts of blend_skin; Sf, Sp [nb, 4, 4] the two poses' skin matrices).

    A point skinned to bones that the two poses move alike by one rigid motion gets that motion's rotation; a point
    whose bones are where the part pose left them at rest gets L_full itself. THE GUARD: where the part pose's weights
    mix far-apart turns, L_part collapses (sigma, its smallest singular value, goes to 0) and the inverse blows up.
    Under sigma = hi the blend of the bones' own relative turns sum_k W (Sf Sp^-1)[J] takes over (never singular: a
    blend of neighbouring turns), wholly at sigma <= lo. share = the part of M that is the exact inverse (1: unguarded).
    """
    Lf, Lp = blend_skin(Sf, J, W)[:, :3, :3], blend_skin(Sp, J, W)[:, :3, :3]
    sig = np.linalg.svd(Lp, compute_uv=False)[:, -1]
    u = np.clip((sig - lo) / (hi - lo), 0.0, 1.0)
    u = u * u * (3 - 2 * u)
    M = Lf @ np.linalg.inv(np.where((u > 0)[:, None, None], Lp, np.eye(3)))
    if (u < 1).any():
        D = blend_skin(Sf @ np.linalg.inv(Sp), J, W)[:, :3, :3]
        M = u[:, None, None] * M + (1 - u)[:, None, None] * D
    return M, sig, u


def edge_ratio(X, X0, ei, ej):
    """(min, max) of posed / rest length over the edges (ei, ej)."""
    r = np.linalg.norm(X[ei] - X[ej], axis=1) / np.maximum(np.linalg.norm(X0[ei] - X0[ej], axis=1), 1e-12)
    return float(r.min()), float(r.max()), r


# ------------------------------------------------------------------------------------------------- REGIONS --
# A region = any bone set of the source rig, with its points, their border share and its rigid border anchors.
def s01(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


def weld_points(V0, tol=1e-6):
    """(group [nv], first [ng]): vertices at one rest position are one point; first = its lowest vertex index."""
    _, first, group = np.unique(np.round(np.asarray(V0) / tol).astype(np.int64), axis=0, return_index=True, return_inverse=True)
    return np.asarray(group).ravel(), first


def rows_from(adj, seed, cap=1 << 30):
    """[n] the count of edges to the nearest seed point (0 on the seed; cap where none is reached)."""
    d = np.where(seed, 0, cap)
    front, k = seed.copy(), 0
    while front.any():
        k += 1
        front = (adj @ front > 0) & (d == cap)
        d[front] = k
    return d


def spread_of(group, pts):
    """(raw, loc): every vertex welded to one of the points `pts` (vertex ids) and that point's local index."""
    loc = -np.ones(group.max() + 1, np.int64)
    loc[group[pts]] = np.arange(len(pts))
    raw = np.nonzero(loc[group] >= 0)[0]
    return raw, loc[group[raw]]


def derive_region(V0, T, J, W, bones, far=(), rows=4, eps=0.02, rigid=0.999):
    """A region's points and border share DERIVED from a bone set of a skin (V0, T, J, W; all its pieces).

    core = the points the set's weights reach (their sum > eps) that are not rigid to a far anchor (`far`: one bone
    set per far anchor; weight >= rigid). The region = the core grown by `rows` rows. The share is 0 on the outer row
    and on every far-rigid point and rises over `rows` rows from either (1 on the core towards the root: the ramp lies
    in the grown rows there; inside the core towards a far anchor, whose rigid points must stay the source's own).
    Returns {pts (vertex ids, one per welded point), share, edges [m, 2] local, core, stiff (far-rigid) [points]}.
    """
    group, first = weld_points(V0)
    n = len(first)
    e = np.unique(np.sort(group[np.concatenate([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]])], 1), axis=0)
    e = e[e[:, 0] != e[:, 1]]
    adj = sp.coo_matrix((np.ones(2 * len(e)), (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])), (n, n)).tocsr()
    Jf, Wf = J[first], W[first]
    stiff = np.zeros(n, bool)
    for b in far:
        stiff |= (Wf * np.isin(Jf, sorted(b))).sum(1) >= rigid
    core = ((Wf * np.isin(Jf, sorted(bones))).sum(1) > eps) & ~stiff
    reg = core.copy()
    for _ in range(rows):
        reg |= adj @ reg > 0
    d = np.minimum(rows_from(adj, ~reg), 1 + rows_from(adj, stiff))
    ids = np.nonzero(reg)[0]
    loc = -np.ones(n, np.int64)
    loc[ids] = np.arange(len(ids))
    ed = loc[e[reg[e].all(1)]]
    return {"pts": first[ids], "share": s01((d[ids] - 1) / rows), "edges": ed, "core": core[ids], "stiff": stiff[ids]}


def support_region(adj, moved, core=None, stiff=None, gated=None, rows=4, ring=3, gate_rows=8, wall_rows=12, stages=()):
    """A region's points and border share from the bone set's MOTION SUPPORT: a true rigid border (any set, any poser).

    adj [n, n]: the points' edges. moved [n] bool: the points that the source's own surface OR the carried reference
    moves by more than a small eps under the set's part poses (measured: no weights, no names). core [n] bool: points
    that are the region's whatever moved (an explicit list). The region = (moved | core) grown by `rows` rows, the
    share 0 on the outer row and 1 from `rows` rows in: the ramp lies in rows that nothing moves, so the target is the
    source's own surface on the outer row by construction and the ramp hides less than eps.
    stiff [n] bool: points rigid to a far bone set. Never the region's, nothing grows into them, and the share is 0
    within `ring` rows of them and rises over `rows` rows (an explicit list's own far border, kept as it is).
    gated [n] bool: a part that moves but is the region's only while a gate is open (one share per gate stage comes
    back, the pose blends them in order). It is a WALL: share 0 on it, rising over `wall_rows` rows away from it (the
    ramp there hides real disagreement, so it is wide). Closed, the whole part is the wall. Open (the first stage),
    the wall stands back by `gate_rows` rows from the core: those rows of the part are blend rows (the last one is the
    wall's first: share 0).
    stages: FURTHER gate stages, in order, each {"rows": the rows the wall stands back from the core (or [n] bool: the
    part's points that open, any shape), "wall_rows": the ramp's rows away from the wall, "smooth": passes, "ramp":
    bool}. A further stage's share is a SMOOTH FIELD: the row ramp relaxed by `smooth` passes of neighbour averaging
    on the part's open points (and, "ramp" true, on the wall ramp's rows outside the part), between the wall's 0 and
    the points the wall does not reach, never over the region's own border ramp (a row ramp alone steps where the
    rows of a mesh do). Without stages the result is the two shares of one gate, as before.
    Returns (ids [m] the region's points: the first stage's region ascending, then the points further stages add,
    ascending; closed [m]; [opened [m], one share [m] per further stage]; the count of the first stage's points).
    """
    n = len(moved)
    core, stiff, gated = (np.zeros(n, bool) if x is None else np.asarray(x, bool) for x in (core, stiff, gated))
    stiff = stiff & ~core                 # far-rigid points INSIDE the list are the list's own (her deltoid and upper arm)
    reg = (moved | core) & ~gated & ~stiff
    for _ in range(rows):
        reg |= adj @ reg > 0
    dg = rows_from(adj, core)
    base = (reg & ~gated & ~stiff) | core
    full = base | (gated & (dg <= gate_rows))
    ds = s01((rows_from(adj, stiff) - ring) / rows)
    s = np.minimum(s01((rows_from(adj, ~full) - 1) / rows), ds)
    out = [np.where(full, np.minimum(s, s01(rows_from(adj, wall) / wall_rows)), 0.0) for wall in (gated, gated & (dg >= gate_rows))]
    every = full.copy()
    for st in stages:
        r = st["rows"]
        opn, wall = (gated & (dg <= r), gated & (dg >= r)) if np.isscalar(r) else (gated & np.asarray(r, bool), gated & ~np.asarray(r, bool))
        fk = base | opn
        sk = np.minimum(s01((rows_from(adj, ~fk) - 1) / rows), ds)          # the region's own border ramp, this stage's region
        dw = rows_from(adj, wall)
        w0 = np.where(fk, np.minimum(sk, s01(dw / st["wall_rows"])), 0.0)   # the row ramp (the first stage's rule)
        free = fk & ~wall & (gated | (bool(st.get("ramp", True)) & (dw <= st["wall_rows"])))
        P = sp.diags(1.0 / np.maximum(np.asarray(adj.sum(1)).ravel(), 1)) @ adj
        w = w0
        for _ in range(int(st.get("smooth", 0))):
            w = np.where(free, np.minimum(sk, P @ w), w0)
        out.append(w)
        every |= fk
    ids = np.r_[np.nonzero(full)[0], np.nonzero(every & ~full)[0]]
    return ids, out[0][ids], [x[ids] for x in out[1:]], int(full.sum())


class Carriers:
    """Carriers of consecutive blocks of points as one (carry, ok, tri, bary): a region whose blocks carry by different
    rules (an explicit list with its pocket, then the rows a support region adds, carried plainly)."""

    def __init__(self, parts):
        self.parts = parts
        self.ok, self.tri, self.bary = (np.concatenate([getattr(c, k) for c in parts]) for k in ("ok", "tri", "bary"))

    def carry(self, ref_V, fill=True, both=False):
        out = [c.carry(ref_V, fill=fill, both=both) for c in self.parts]
        return tuple(np.concatenate(x) for x in zip(*out)) if both else np.concatenate(out)


def follow_field(pose, V0, pivot, bone, deg=0.5):
    """[nv] in 0..1: how much each vertex of a posed mesh follows a bone, MEASURED (no weights read: any poser).

    pose(turns) -> vertices; the bone is turned `deg` about each axis through `pivot` (its rest joint) and the field is
    the least-squares share of the rigid displacement each vertex takes: for a blend skin, the bone's subtree weight.
    """
    from scipy.spatial.transform import Rotation
    num, den = np.zeros(len(V0)), np.zeros(len(V0))
    for ax in np.eye(3):
        R = Rotation.from_rotvec(ax * np.radians(deg)).as_matrix()
        r = (V0 - pivot) @ (R - np.eye(3)).T
        num += ((pose([(bone, R)]) - V0) * r).sum(1)
        den += (r * r).sum(1)
    return np.clip(num / np.maximum(den, 1e-30), 0.0, 1.0)


def register(Va, Ms, F):
    """The reference's posed vertices registered rigidly at each anchor (Ms: 4x4 per anchor, the root first) and blended
    by the far anchors' fields F [nv, anchors - 1] (the root takes the rest: the fields sum to at most 1)."""
    out = Va @ Ms[0][:3, :3].T + Ms[0][:3, 3]
    base = out.copy()
    for a, M in enumerate(Ms[1:]):
        out += F[:, a, None] * (Va @ M[:3, :3].T + M[:3, 3] - base)
    return out


class Region:
    """A bone set of the source rig as a carried region. bones: source bone ids (their LOCAL transforms make the part
    pose). ref_map {reference bone: source bone} and order: how the reference is posed (transfer_turns). anchors
    [(source bone, reference bone)]: the rigid borders, the root first. field [reference vertices, far anchors].
    pts (source vertex ids), share ([points] or a function of the pose), edges (ei, ej) local, carrier, spread
    (spread_of: every source vertex of the points)."""

    def __init__(self, name, **kw):
        self.name = name
        self.__dict__.update(kw)

    def share_at(self, G):
        return self.share(G) if callable(self.share) else self.share


def compose(Vp, parts):
    """The target of a pose on every source vertex: the published surface plus the regions' relative deltas.
    parts {region name: (raw, loc, delta [points, 3])}. THE RULE: the deltas ADD, each under its own share (a blend skin
    is exactly additive over sibling chains off one anchor, so shares are not normalised: that would halve the
    reference's deformation where regions overlap), summed in the order of the regions' names: the listing order
    never matters, bit for bit."""
    X = np.array(Vp, float)
    for name in sorted(parts):
        raw, loc, d = parts[name]
        X[raw] += d[loc]
    return X


# ================================================================================================= HER CONFIG ==
HER = {
    "source": "B",                       # deform_audit body keys
    "reference": "A",
    "layer": "full",
    # reference bone <- source bone (A has 3 spine bones for B's 5); every other bone by name
    "bone_map": {"spine_01": "spine_02", "spine_02": "spine_03", "spine_03": "spine_05"},
    # the reference bones posed by the transfer; the rest of A (its own rig's bones, fingers, legs) stays at rest
    "pose_bones": ["pelvis", "spine_01", "spine_02", "spine_03", "neck_01", "neck_02", "head"]
                  + [f"{b}_{s}" for s in "lr" for b in ("clavicle", "upperarm", "lowerarm", "hand")],
    "anchor_child": "clavicle_{s}",      # the anchor = this bone's parent, on each skeleton
    "carry": "relative",                 # "relative": A lends the girdle's own deformation only; "absolute": the whole pose
    # THE REGIONS ({s}: one per side). bones: the region's own, their LOCAL transforms make the part pose (the rig's
    # driver adds scapula, twists, muscles). ref: reference bone <- source bone, a chain to a chain (A's neck is 2 bones
    # for B's 3: A's neck_01 sits on B's neck_02 joint, so the END's turn against the root anchor is the source's).
    # root: the root anchor = this source bone's parent (on the reference: the parent of its first posed bone).
    # far: the far rigid border anchors. explicit: points, share, pocket from region_target.Model; derived: derive_region.
    "sides": ["l", "r"],
    "out_region": "girdle_{s}",          # a pose of side s is written on this region's points
    "regions": {
        "girdle_{s}": {"provider": "explicit", "bones": ["clavicle_{s}", "upperarm_{s}", "lowerarm_{s}", "hand_{s}"],
                       "ref": {b: b for b in ("clavicle_{s}", "upperarm_{s}", "lowerarm_{s}", "hand_{s}")},
                       "root": "clavicle_{s}", "far": [],
                       # the rigid border (support_region; body_facts/border.md): the motion support over the stored poses
                       # (eps_mm, cached), grown `rows`; stiff = rigid to this bone's subtree; gated = this part of the
                       # topology, opened by the arm's elevation over gate_deg (region_target.Model.blend)
                       # gate2 (gate3 ...): a further gate stage, opened over its own `deg` on top of the stage before
                       # (rows: an integer, or "all" = the part's whole side; body_facts/chest_fold.md section 5)
                       "support": {"eps_mm": 1.0, "rows": 4, "ring": 3, "gate_rows": 8, "wall_rows": 12, "gate_deg": [45.0, 75.0],
                                   "gate2": {"deg": [90.0, 130.0], "rows": 14, "wall_rows": 12, "smooth": 60,
                                             # relax (Her.relaxed): on the rows this stage opens, carried edges over
                                             # `ratio` x rest are filled from their neighbours `rows` around, in step
                                             # with the stage (A's own crease on the breast's rows 4-7, chest_fold.md 6)
                                             "relax": {"ratio": 2.5, "rows": 2, "fold": 45.0, "fold_open": [30.0, 45.0]}},
                                   # depinch (Pocket.fair) removed 10 Nov by lead 22: superseded by fair_a at the source; facts body_facts/depinch.md
                                   "stiff": "upperarm_{s}", "rigid": 0.999, "gated_part": "breast", "cache": "support.npz",
                                   # map (Her.part; body_facts/strip_rest.md): the armpit band's lay (out/shoulder/`file`,
                                   # strip_rest.HerStrip) blended into the carried fill on the band's points by the arm's
                                   # elevation, smoothstep over `elev` deg (strip_rest.map_targets). No key: the fill alone
                                   "map": {"file": "strip_rest.npz", "elev": [45.0, 90.0]},
                                   # open (gate_open) removed 10 Nov by lead 22: Jog's tear is a clip fault (spine_04 35-51 deg), no gate can fix it; facts body_facts/breast_gate.md
                                   }},
        "neck": {"provider": "derived", "bones": ["neck_01", "neck_02", "Head"], "ref": {"neck_01": "neck_02", "Head": "Head"},
                 "root": "neck_01", "far": ["Head"], "rows": 4, "eps": 0.02, "rigid": 0.999,
                 # relax (Her.relaxed on a region with no side): no elevation, w = 1, every row open; A's own stretched
                 # reference on the head-piece patches (body_facts/neck_edges.md) is filled from its neighbours; 2.4 not 2.5: the placement
                 # adds up to 0.1 to a carried edge (iron_vow@75:r: carried 2.47, composed 2.51)
                 # fold trigger off 10 Nov (lead 23's solver): the upper-chest notch it stood in for is cured at the source
                 # (her_b weights chain_relax, body_facts/notch.md 5)
                 "relax": {"ratio": 2.4, "rows": 2}},
    },
    # the bones the source's driver places (never read from a pose): her rig's helpers but the "unroll" kind, and the scapula
    "driven": [b + "_{s}" for b in (
        "scap", "upperarm_twist_01", "upperarm_twist_02", "upperarm_twist_03", "upperarm_twist_04", "upperarm_share", "delt",
        "trap", "lowerarm_twist_01", "lowerarm_twist_02", "lowerarm_share", "lowerarm_point", "pec", "lat", "thigh_twist_01",
        "thigh_twist_02", "thigh_share", "glute", "calf_twist_01", "calf_twist_02", "calf_share", "calf_point")],
    "sig_lo": 0.15,                      # relative_place's guard: B's girdle-only skin matrix under sig_hi hands over to
    "sig_hi": 0.35,                      #   the blend of relative turns (141 poses: the smallest sigma is far above it)
    # T9's pose: local turns in degrees about seeded random axes of bones outside EVERY region (all regions' locals at rest)
    "t9_turns": {"spine_02": 20, "spine_03": 25, "spine_05": 30},
    "t12_turns": {"neck_01": 30, "neck_02": 25, "Head": 20},             # T12: the neck alone
    "t14_poses": ["p4:iron_vow@75:r", "p4:idle_warden_town@122:l"],      # T14: where B's neck skinning stretched 11.76x
    # T17: the ramp edges over 2.5x allowed per pose (none unexplained); t17_watch: printed only (border.md's table)
    "t17_poses": {"x:abd170:l": 0, "x:abd150:l": 0, "p4:iron_vow@72:l": 0, "cast_bolt@0:l": 0, "p4:heroic_leap@19:r": 1},
    "t17_watch": ["x:flex170:l", "Jog_Fwd@14:l", "Jog_Fwd@11:r", "p4:idle_warden_town@122:l", "x:add0:l"],
    # T18: the second gate stage (and its relax rule) leaves every pose at or under its lo bit for bit: the composed
    # target against the stored target of before the stage (a frozen copy). T19: the fold stays at A's (chest_fold.md 5, 6):
    # on the fold set of the reference dump (fold_probe.py dump ... t0 --today), valley angle max <= A's + valley_deg and
    # depth mean within depth_mm of A's
    "t18_poses": ["x:add0:l", "cast_bolt@0:l", "cast_bolt@3:r", "crossbow_shoot@10:r", "x:abd90_int60:l", "Jog_Fwd@11:r"],
    "t18_stored": "target_a_l18.npz",
    "t20_n": 8,                          # T20: poses sampled with both arms under the armpit map's lo (support "map")
    # T22: the armpit map's bar, strip_rest.cmd_turned's numbers: turned triangles 0 and the worst band edge at most A's own
    # worst + 0.15 (the first list) or the fill's worst + 0.15 (the second: where A's own is the harder pose)
    "t22_own": ["x:abd120:l", "x:abd150:l", "x:abd170:l", "x:flex170:l", "p4:iron_vow@72:l", "p4:heroic_leap@7:r",
                "p4:heroic_leap@9:r", "p4:heroic_leap@19:r", "p4:heroic_leap@20:r",
                "crossbow_shoot@0:r", "crossbow_shoot@2:r", "cast_flick@8:r"],      # + lay 8's rows (lead 22)
    "t22_fill": ["crossbow_shoot@10:r", "cast_bolt@3:r", "axe_heavy@7:r", "p4:heroic_leap@5:r", "p4:idle_warden_town@126:r",
                 "p4:heroic_leap@25:r", "cast_bolt@6:l", "p4:heroic_leap@6:r", "p4:heroic_leap@0:l", "p4:heroic_leap@30:l"],
    # Left pit rows where the map rides faired A at w = 1 and faired A's OWN surface is turned (a closed pit's tight crease):
    # the bar there reads "no more turned than faired A's own": turned map <= A's own turned count and every turned map
    # triangle among A's own turned ones (the band-edge part unchanged). Coordinator's ruling, inbox RULING P1 12:17, ASK 2.
    "t22_own_turned": ["x:hadd40:l", "x:flex120:l", "p4:iron_vow@72:l"],
    "t22_tol": 0.15,
    # T23: the neck's relax rule (head-piece patches, body_facts/neck_edges.md): on these poses the neck set has no edge over
    # `ratio` but those the published surface has over it too; Head-rigid points and the girdle regions as with it off
    "t23_poses": ["p4:idle_warden_town@126:r", "p4:idle_warden_town@122:l", "sword_heavy@10:l", "p4:shield_charge@0:r",
                  "p4:iron_vow@75:r", "axe_heavy@7:r", "Jog_Fwd@11:r"],
    # T26: the relax rules' fold trigger (body_facts/notch.md 4): no region edge past rest by over `fold` on t26_poses;
    # t26_quiet: poses with no seed, composed = trigger off bit for bit. The neck has no fold key now (its checkerboard was
    # cured at the source, notch.md 5), so T26 reads the girdle trigger only.
    "t26_poses": ["p4:heroic_leap@6:r", "p4:heroic_leap@9:r", "cast_bolt@3:r"], "t26_quiet": ["x:add0:l"],
    "t21_poses": ["x:abd150:l", "p4:heroic_leap@9:r", "crossbow_shoot@10:r"],   # T21: the map through two paths
    "t19": {"poses": ["x:abd150:l", "x:abd170:l", "x:flex170:l"], "ref": "fold_probe/dump_t0.npz", "k": 3, "top": 12,
            "valley_deg": 1.0, "depth_mm": 0.2},
    "t16_poses": ["Jog_Fwd@11:r"],       # + every dev / T14 / T17 pose; each side under the gate
    # T11: the stored targets of before the border grew (frozen copies: `out` is rewritten by every full run)
    "t11_stored": {"regions": "target_a_regions.npz", "girdles": "target_a_rel.npz"},
    # fair_a (Her.part + strip_rest.pose_a; body_facts/fair_a.md): A's own posed skin faired at the source before any carry
    # (seeds: folds over 45 deg and past rest + 20, flips; limited to the A vertices the girdle carriers read). LIVE (WIP,
    # pending the lead's look): P5 = P4 + rings 4, shrink 0.5 (lead 22): patch caps met and 0 flips on all 9 poses
    # (body_facts/fair_a.md, attempt 5); one cap-front edge at 128 deg on iron_vow@72:l left. h.fair_on False = off
    "fair_a": {"regions": ["girdle_{s}"],
               "params": {"rings": 4, "shrink": 0.5, "soft": 2, "alpha": 0.5, "alpha_core": 0.02, "rot_passes": 10, "grow": 1, "close": True,
                          "rot": "fill", "edges": "blend", "c_core": 1, "c_soft": 2, "alpha_mid": 0.2, "stretch": False,
                          "dilate": True, "best": True, "rounds": 5, "iters": 4}},
    "rad": 0.05,
    "k": 64,
    "nw": 0.0,                           # the normal term: tried at 0.2, it does not cure the armpit-apex bridge
    "bridge_deg": 60.0,                  # the pocket rule (Carrier): her armpit apex, where B bridges A's closed fold
    "pocket_rows": 4,                    # dev scan, abd150 pocket edge max / off A max mm: rows 4 2.69 / 25.5, 6 2.57 / 32.5,
    "frame_passes": 8,                   #   8 2.48 / 38.6 (more rows: a little less stretch, a web further off A's hollow)
    "pocket_weight": "length",           # "uniform" gives each row the same length: short edges 3.66x at rows 4, 3.28x at 10
    "torn": 3.0,                         # a carried-alone edge over this ratio must lie inside the pocket (T5)
    "out": "target_a.npz",
    "dev_out": "target_a_dev.npz",
    "d0_p95_stop_mm": 4.0,
    "dev_poses": ["x:abd150:l", "x:add0:l", "cast_bolt@0:l", "crossbow_shoot@0:r"],
}
INFO = ["d_pub_p50", "d_pub_p95", "d_pub_max", "d_bor_p50", "d_bor_max", "edge_min", "edge_max", "edge_raw_max", "edge_car_max",
        "pk_edge_min", "pk_edge_max", "pk_d_p50", "pk_d_max", "vol", "girth_mid_deltoid", "girth_insertion",
        "rel_sig_min", "rel_guard", "drv_mem", "elev", "gated_d_max", "gated_oth_max", "edge_all_max"]


class Her:
    """Her body B's shoulder region (region_target.Model) against her old body A."""

    def __init__(self, cfg=HER, verbose=True):
        import deform_audit as da
        import region_target as rt
        self.cfg, self.rt = cfg, rt
        self.bd = bd = da.body(cfg["source"])
        bd.set_layer(cfg["layer"])
        self.Ab = Ab = da.body(cfg["reference"])
        Ab.set_layer(cfg["layer"])
        self.md = md = rt.Model(bd.p)
        self.OUT = rt.OUT
        self.ref_names = list(Ab.p.names)
        self.order, left = transfer_order(self.ref_names, Ab.p.parent, bd.p.index, cfg["bone_map"],
                                          only=set(cfg["pose_bones"]))
        self.N0 = bd._normals(bd.V0)
        self.car, self.anchor, self.edges, self.regions = {}, {}, {}, {}
        I, AI, sides = bd.p.index, Ab.p.index, cfg["sides"]
        self.group = weld_points(bd.V0)[0]
        # the bones the source's driver places, by name from the config (never read from a pose)
        self.driven = sorted({I[n.replace("{s}", s)] for n in cfg["driven"] for s in sides})
        self.main = set(range(len(bd.p.names))) - set(self.driven)
        for key, rc in cfg["regions"].items():
            for s in (sides if "{s}" in key else [""]):
                def nm(x, s=s):
                    return x.replace("{s}", s)
                ref = {nm(a_): nm(b_) for a_, b_ in rc["ref"].items()}
                order = transfer_order(self.ref_names, Ab.p.parent, I, ref, only=set(ref))[0]
                ja, ra = bd.p.parent[I[nm(rc["root"])]], Ab.p.parent[AI[order[0]]]
                rn, sn = self.ref_names[ra], bd.p.names[ja]
                assert cfg["bone_map"].get(rn, rn) == sn, f"anchor: reference {rn} does not map to source {sn}"
                anchors = [(ja, ra)] + [(I[nm(x)], AI[next(a_ for a_, b_ in ref.items() if b_ == nm(x))]) for x in rc["far"]]
                field = np.zeros((len(Ab.V0), len(rc["far"])))
                for k, (_, rf) in enumerate(anchors[1:]):   # a far anchor's field: how far the reference follows its chain
                    top = rf
                    while self.ref_names[Ab.p.parent[top]] in ref:
                        top = Ab.p.parent[top]
                    field[:, k] = follow_field(lambda t: Ab.pose_turns(t)[0], Ab.V0, Ab.G0[top][:3, 3], self.ref_names[top])
                rg = Region(nm(key), side=s, bones={I[nm(x)] for x in rc["bones"]}, ref_map=ref, order=order, anchors=anchors,
                            field=field)
                if rc["provider"] == "explicit":            # today's shoulder: region_target.Model's points, seam and pocket
                    ids = md.S[s]["ids"]
                    A = sp.triu(md.adj[ids][:, ids], 1).tocoo()
                    self.edges[s] = (A.row, A.col)
                    self.car[s], self.anchor[s] = self.carrier(s), (ja, ra)
                    rg.pts, rg.share, rg.edges, rg.carrier = md.first[ids], (lambda G, s=s: md.blend(G, s)), self.edges[s], self.car[s]
                else:
                    d = derive_region(bd.V0, bd.T, bd.J, bd.W, rg.bones, [set(bd.p.subtree(j)) | {j} for j, _ in anchors[1:]],
                                      rc["rows"], rc["eps"], rc["rigid"])
                    rg.pts, rg.share, rg.edges, rg.core, rg.stiff = d["pts"], d["share"], (d["edges"][:, 0], d["edges"][:, 1]), d["core"], d["stiff"]
                    rg.carrier = Carrier(Ab.V0, Ab.T, bd.V0[rg.pts], self.N0[rg.pts], rad=cfg["rad"], k=cfg["k"], nw=cfg["nw"], pocket_rows=0)
                    if rc.get("relax"):                     # a region with no side: always open (Her.relaxed, w = 1)
                        rg.relax = [(0.0, 0.0, np.ones(len(rg.pts), bool), rc["relax"])]
                rg.spread = spread_of(self.group, rg.pts)
                self.regions[rg.name] = rg
        self.ext = {}
        for key, rc in cfg["regions"].items():              # the explicit regions' rigid border, once every region stands
            if rc["provider"] == "explicit" and rc.get("support"):
                self.grow(key, rc["support"])
        self.map = {}                                       # region name -> its HerStrip (the lay loaded on this Her)
        for key, rc in cfg["regions"].items():
            mp = (rc.get("support") or {}).get("map") if rc["provider"] == "explicit" else None
            if mp:
                import strip_rest as sr
                self._sr = sr
                hs = sr.HerStrip({**sr.HER, "out": mp["file"], "map_elev": tuple(mp["elev"])}, h=self).load()
                self.map.update({key.replace("{s}", s): hs for s in (sides if "{s}" in key else [""])})
        self.map_on = bool(self.map)
        own ={n: set(r.spread[0].tolist()) for n, r in self.regions.items()}
        self.touch = {n: [m for m in self.regions if m != n and own[n] & own[m]] for n in self.regions}
        self.girth0 = {s: md.girth(md.S[s], md.V0) for s in sides}
        self.last = {}
        self._pose, self._parts = None, {}                  # the regions' parts of the last pose (part)
        if verbose:
            print(f"carry: {cfg['carry']}; {len(self.driven)} driven bones; regions:")
            for n, r in self.regions.items():
                print(f"  {n}: bones {' '.join(bd.p.names[k] for k in sorted(r.bones))}; reference {r.ref_map}; anchors (source, reference)"
                      f" {[(bd.p.names[j], self.ref_names[k]) for j, k in r.anchors]}; {len(r.pts)} points, share 1 on"
                      f" {int((r.share_at(bd.p.rest) == 1).sum())}, carrier not ok {int((~r.carrier.ok).sum())}; touches {self.touch[n]}")
            for s in cfg["sides"]:
                c = self.car[s]
                print(f"pocket {s}: {len(c.bridge)} bridge edges, {0 if c.pocket is None else len(c.pocket.p)} pocket points"
                      f" of {len(md.S[s]['ids'])} (bridge_deg {cfg['bridge_deg']}, rows {cfg['pocket_rows']}, weight {cfg['pocket_weight']})")
            print(f"reference bones posed ({len(self.order)}): {' '.join(self.order)}")
            print(f"reference bones left at rest ({len(left)}): {' '.join(left)}")
            print("anchor:", {s: (self.ref_names[ra], bd.p.names[ja]) for s, (ja, ra) in self.anchor.items()},
                  "(reference, source)")

    def motion(self, key, sup):
        """(pub, ref) [md points] mm, in the indexing of the first side by name: the most that B's published surface and the carried
        reference move each point under the region's part poses, over the stored poses (each on its side, the other
        sides' mirrored by the twins). Cached in OUT / sup["cache"], keyed by the pose names."""
        md, bd, Ab, p, cfg = self.md, self.bd, self.Ab, self.bd.p, self.cfg
        z = np.load(self.OUT / "poses.npz")
        names, f, F = [str(x) for x in z["name"]], self.OUT / sup["cache"], md.first
        if f.exists():
            c = np.load(f)
            if [str(x) for x in c["name"]] == names and str(c["key"]) == key and len(c["pub"]) == md.n:
                return c["pub"], c["ref"]
        wide = Carrier(Ab.V0, Ab.T, bd.V0[F], self.N0[F], rad=cfg["rad"], k=cfg["k"], nw=cfg["nw"], pocket_rows=0)
        Vp0, c0 = self.rt.published(bd, p.rest)[F], wide.carry(Ab.V0)
        MP, MA = np.zeros(md.n), np.zeros(md.n)
        for i, nm in enumerate(names):
            s = str(z["side"][i])
            rg = self.regions[key.replace("{s}", s)]
            Gr = self.part_pose(z["G"][i], rg.bones)[0]
            Va, Ga = Ab.pose_turns(transfer_turns(Gr, p.rest, p.index, Ab.p.index, Ab.p.parent, rg.ref_map, rg.order))
            Vr = register(Va, [anchor_align(Gr[ja], p.rest[ja], Ab.G0[ra], Ga[ra]) for ja, ra in rg.anchors], rg.field)
            m = (lambda x: x) if s == min(cfg["sides"]) else (lambda x: x[md.tw])   # never the listing order (T13)
            MP = np.maximum(MP, m(np.linalg.norm(self.rt.published(bd, Gr)[F] - Vp0, axis=1) * 1000))
            MA = np.maximum(MA, m(np.linalg.norm(wide.carry(Vr) - c0, axis=1) * 1000))
        np.savez_compressed(f, name=np.array(names), key=key, pub=MP, ref=MA)
        return MP, MA

    def grow(self, key, sup):
        """The explicit regions `key` grown to their rigid border (support_region): the list first (order unchanged), then
        the new points, carried plainly; the share by the pose (md.blend, grown). The other sides are the first's twins."""
        md, bd, Ab, cfg, F = self.md, self.bd, self.Ab, self.cfg, self.md.first
        s0 = min(cfg["sides"])                # the cache's indexing: never the listing order (T13)
        MP, MA = self.motion(key, sup)
        core = np.zeros(md.n, bool)
        core[md.S[s0]["ids"]] = True
        j = bd.p.index[sup["stiff"].replace("{s}", s0)]
        stiff = (bd.W[F] * np.isin(bd.J[F], sorted(set(bd.p.subtree(j)) | {j}))).sum(1) >= sup["rigid"]
        gate = md.part == md.parts.index(sup["gated_part"])
        Tm = md.src[bd.T[(bd.T < len(md.src)).all(1)]]   # the model's triangles (md ids; fold_probe.cmd_dump's)
        Tm = Tm[(Tm >= 0).all(1) & (Tm[:, 0] != Tm[:, 1]) & (Tm[:, 1] != Tm[:, 2]) & (Tm[:, 0] != Tm[:, 2])]
        dg = rows_from(md.adj, core)
        own = gate & (dg <= dg[md.tw])                       # the gated part on this side: nearer its list than the twin's
        own0 = np.nonzero(own)[0]
        more = [sup[k] for k in sorted((k for k in sup if re.fullmatch(r"gate\d+", k)), key=lambda k: int(k[4:]))]
        ids, closed, shares, n1 = support_region(md.adj, (MP > sup["eps_mm"]) | (MA > sup["eps_mm"]), core, stiff, gate, sup["rows"],
                                                 sup["ring"], sup["gate_rows"], sup["wall_rows"],
                                                 [{**g, "rows": own if isinstance(g["rows"], str) else own & (dg <= g["rows"])} for g in more])   # this side of the part only
        C, SH = np.zeros(md.n), np.zeros((len(shares), md.n))
        C[ids], SH[:, ids] = closed, shares
        new0 = ids[:n1][~core[ids[:n1]]]                     # the first stage's rows, then the rows the further stages add
        add0 = ids[n1:]                                      #   (their own carrier block: the first blocks stay as they were)
        o0 = np.r_[md.S[s0]["ids"], new0, add0]
        md.grown = getattr(md, "grown", {})
        for s in cfg["sides"]:
            rg = self.regions[key.replace("{s}", s)]
            news = [x if s == s0 else md.tw[x] for x in (new0, add0) if len(x)]
            new = np.concatenate(news) if news else new0
            allid = np.r_[md.S[s]["ids"], new]
            assert s == s0 or (md.tw[md.S[s0]["ids"]] == md.S[s]["ids"]).all(), "the sides' lists are not twins"
            md.grown[s] = {"new": new, "closed": C[o0], "opened": SH[0][o0], "gate": tuple(sup["gate_deg"]),
                           "stages": [(*g["deg"], SH[1 + k][o0]) for k, g in enumerate(more)]}
            A = sp.triu(md.adj[allid][:, allid], 1).tocoo()
            plain = [Carrier(Ab.V0, Ab.T, bd.V0[F[x]], self.N0[F[x]], rad=cfg["rad"], k=cfg["k"], nw=cfg["nw"], pocket_rows=0) for x in news]
            rg.pts, rg.edges, rg.carrier, rg.nlist = F[allid], (A.row, A.col), Carriers([self.car[s], *plain]), len(md.S[s]["ids"])
            rg.share = lambda G, s=s: md.blend(G, s, grown=True)
            rg.gated = gate[allid]
            rg.gate_own = F[own0 if s == s0 else md.tw[own0]]       # source vertices: what the side's gate rules (shut)
            rg.spread = spread_of(self.group, rg.pts)
            rg.relax = [(*g["deg"], (np.abs(SH[1 + k][o0] - SH[k][o0]) > 1e-12) & (np.arange(len(o0)) >= rg.nlist), g["relax"])
                        for k, g in enumerate(more) if g.get("relax")]      # (lo, hi, the plain rows the stage opens, rule)

    def carrier(self, side, **over):
        """The side's Carrier from the config (`over` replaces Carrier arguments: the tests' variants)."""
        cfg, md, bd = self.cfg, self.md, self.bd
        pts = md.first[md.S[side]["ids"]]
        kw = {"rad": cfg["rad"], "k": cfg["k"], "nw": cfg["nw"], "edges": np.stack(self.edges[side], 1),
              "bridge_deg": cfg["bridge_deg"], "pocket_rows": cfg["pocket_rows"], "frame_passes": cfg["frame_passes"],
              "pocket_weight": cfg["pocket_weight"], "pocket_mode": cfg.get("pocket_mode", "fill"), **over}
        if kw["pocket_mode"] == "slide":                                 # the band stays off the region's blended border
            tr = np.asarray(md.S[side]["tr"], np.int64)
            kw = {"hold": np.asarray(md.beta) < 1, "tris": tr[(tr < len(pts)).all(1)], **kw}
        return Carrier(self.Ab.V0, self.Ab.T, bd.V0[pts], self.N0[pts], **kw)

    def pose_ref(self, G):
        bd, Ab = self.bd, self.Ab
        return Ab.pose_turns(transfer_turns(G, bd.p.rest, bd.p.index, Ab.p.index, Ab.p.parent,
                                            self.cfg["bone_map"], self.order))

    def drive(self, G):
        """B's driver on a pose whose driven bones ride their parents at rest local (how every stored pose was made)."""
        return self.bd.p.driver.drive(self.bd.p, np.array(G, float), self.bd.rig)[0]

    def part_pose(self, G, bones):
        """(Gr, memory): B's globals with only the bone set `bones` turned as in G (their LOCAL transforms, so a clavicle
        the girdle law turned is taken as it stands in G; every other bone at rest; the driven bones by the driver).

        The driver gives back a stored pose from its main bones' locals but for what a driven bone holds of the pose
        before it was driven (her trap keeps the clavicle's roll: "clavicle_roll_keep"). That offset, the stored bone
        against the driver's rerun of the whole pose, goes onto the same bone here if the set moves it, so a pose with
        every other bone at rest IS its part pose. memory: the largest such offset (matrix entries).
        """
        p, order = self.bd.p, self.bd.order
        Gg = self.drive(local_pose(G, p.rest, p.parent, order, bones))
        Df = self.drive(local_pose(G, p.rest, p.parent, order, self.main))
        mem = 0.0
        for k in self.driven:
            if np.abs(Gg[k] - p.rest[k]).max() > 1e-9:
                mem = max(mem, float(np.abs(Df[k] - G[k]).max()))
                Gg[k] = Gg[k] @ np.linalg.inv(Df[k]) @ G[k]
        return Gg, mem

    def girdle_pose(self, G, side):
        return self.part_pose(G, self.regions[self.cfg["out_region"].replace("{s}", side)].bones)

    def part(self, G, name):
        """One region's account of the pose G: its part pose, the reference posed by it (the region's chain map),
        registered at each anchor and blended by the fields, carried onto the region's points (cf filled, cr alone: in
        the part pose's frame), B's own surface of the part pose Pg and the placement M (relative_place)."""
        bd, p, Ab, cfg, rg = self.bd, self.bd.p, self.Ab, self.cfg, self.regions[name]
        key = np.asarray(G, float).tobytes()                # one pose's parts are computed once: every side's target,
        if key != self._pose:                               # the regions that touch it and the checks reuse them
            self._pose, self._parts = key, {}
        if name in self._parts:
            return self._parts[name]
        Gr, mem = self.part_pose(G, rg.bones)
        Va, Ga = Ab.pose_turns(transfer_turns(Gr, p.rest, p.index, Ab.p.index, Ab.p.parent, rg.ref_map, rg.order))
        if cfg.get("fair_a"):                               # A's own posed skin faired at the source (fair_a.py); absent: as it was
            import fair_a
            Va = fair_a.her_hook(self, rg, Va)
        Vr = register(Va, [anchor_align(Gr[ja], p.rest[ja], Ab.G0[ra], Ga[ra]) for ja, ra in rg.anchors], rg.field)
        cf, cr = rg.carrier.carry(Vr, both=True)
        cf = self.relaxed(rg, G, cf, Vr)
        Pg = self.rt.published(bd, Gr)[rg.pts]
        cf, mw, mN = self.mapped(rg, G, cf, Vr)
        ibm = p.skel.ibm
        M, sig, u = relative_place(G @ ibm, Gr @ ibm, bd.J[rg.pts], bd.W[rg.pts], cfg["sig_lo"], cfg["sig_hi"])
        self._parts[name] = {"M": M, "cf": cf, "cr": cr, "Pg": Pg, "Va": Vr, "Va_own": Va,
                             "Gr": Gr, "sig": float(sig.min()), "guard": int((u < 1).sum()), "mem": mem, "map_w": mw, "map_N": mN}
        if getattr(self, "fold_on", True) and not getattr(self, "_folding", False) and any("fold" in r[3] for g in self.regions.values() for r in getattr(g, "relax", ())):
            self.folded(G)                                  # a relax rule with "fold": every region's carry first (Her.folded)
        return self._parts[name]

    def folded(self, G):
        """The relax rules' FOLD trigger (config "relax" {"fold": deg}; body_facts/notch.md 4), once a pose, after every
        region's carry. B's published surface folds where its weights alternate between bone chains (the upper chest's
        neck_01 / spine_04 checkerboard) and the relative placement M keeps that fold whatever A's carry is, so the
        trigger reads the COMPOSED surface (published + every region's delta), not the carry. In the regions' name order
        (each sees the ones before it fixed: overlapping regions never fix one fold twice), on the rows a rule opens,
        an edge of the region's triangles folded past its rest dihedral by over `fold` deg seeds a pocket of the rows
        within `rows` edges (the share > 0 points; the armpit map's band held), harmonically filled on the composed
        surface (Pocket; the carrier's rotations placed by M) and blended in by the rule's own w (the stage's elevation
        smoothstep; 1 on a region with no side). The fill goes back into the region's cf through its delta's placement,
        so every consumer (delta, compose, target) sees it. No seed: every part as it was, bit for bit."""
        import fold_probe as fp
        bd, parts = self.bd, self._parts
        self._folding = True
        try:
            for n in self.regions:
                self.part(G, n)
        finally:
            self._folding = False
        if parts.get("__fold__"):
            return
        parts["__fold__"] = True
        Vp = self.rt.published(bd, G)
        X = compose(Vp, {n: (*r.spread, self.delta(G, n)) for n, r in self.regions.items()})
        for name in sorted(self.regions):
            rg = self.regions[name]
            rules = [r for r in getattr(rg, "relax", ()) if "fold" in r[3]]
            if not rules:
                continue
            P = parts[name]
            if getattr(rg, "fold_tris", None) is None:      # the region's own triangles (local ids; welds joined) and rest fold
                lg = np.full(len(bd.V0), -1, np.int64)
                lg[rg.spread[0]] = rg.spread[1]
                Tl = lg[bd.T]
                Tl = Tl[(Tl >= 0).all(1) & (Tl[:, 0] != Tl[:, 1]) & (Tl[:, 1] != Tl[:, 2]) & (Tl[:, 0] != Tl[:, 2])]
                rg.fold_tris = Tl
                rg.fold_e0, rg.fold_d0 = fp.dihedral(bd.V0[rg.pts], Tl)
            P0, E, Tl = bd.V0[rg.pts], np.stack(rg.edges, 1), rg.fold_tris
            sh = rg.share_at(G)
            free = sh > 1e-3
            if np.any(P.get("map_w", 0.0) > 0) and rg.name in getattr(self, "map", {}):
                free[np.asarray(self.map[rg.name].loc[rg.side], np.int64)] = False
            el = self.md.elevation(G, rg.side) if rg.side else 0.0
            for lo, hi, opened, rule in rules:
                op = rule.get("fold_open")                  # [a, b] deg: the stage also opens by the fold itself
                w = 1.0
                if rg.side:
                    w = np.clip((el - lo) / (hi - lo), 0.0, 1.0)
                    w = w * w * (3 - 2 * w)
                    if w <= 0 and not op:
                        continue
                Y = X[rg.pts]
                e, d = fp.dihedral(Y, Tl)
                ex = np.where(opened[e[:, 0]] | opened[e[:, 1]], np.abs(d) - np.abs(rg.fold_d0), -np.inf)
                hit = ex > (min(rule["fold"], op[0]) if op else rule["fold"])
                if not hit.any():
                    continue
                m = rows_around(len(P0), E, np.unique(e[hit]), rule["rows"]) & opened & free
                if not m.any():
                    continue
                if op:                                      # per point: the smoothstep over [a, b] of the worst seed's
                    xv = np.full(len(P0), -np.inf)          # excess within `rows` edges, the larger of it and the
                    np.maximum.at(xv, e[hit].ravel(), np.repeat(ex[hit], 2))   # elevation's w (seeds under `fold`
                    for _ in range(int(rule["rows"])):      # get only the fold's own weight)
                        xn = xv.copy()
                        np.maximum.at(xn, E[:, 0], xv[E[:, 1]])
                        np.maximum.at(xn, E[:, 1], xv[E[:, 0]])
                        xv = xn
                    o = np.clip((xv - op[0]) / (op[1] - op[0]), 0.0, 1.0)
                    o = o * o * (3 - 2 * o)
                    w = np.maximum(np.where(xv > rule["fold"], w, 0.0), o)[:, None]
                R = np.concatenate([c.rotations(P["Va"]) for c in getattr(rg.carrier, "parts", [rg.carrier])])
                R = np.einsum("nij,njk->nik", polar(P["M"]), R)
                C = w * (Pocket(P0, E, m, self.cfg["pocket_weight"]).fill(Y, R, self.cfg["frame_passes"]) - Y)
                C[~m] = 0.0
                P["cf"] = P["cf"] + np.linalg.solve(P["M"], (C / np.maximum(sh, 1e-3)[:, None])[..., None])[..., 0] * m[:, None]
                raw, loc = rg.spread
                X[raw] += C[loc]

    def mapped(self, rg, G, cf, Vr):
        """(cf, w, N): the filled carry cf [region points, 3] with the armpit map (config support "map") on the band's
        points of the list: strip_rest.map_targets on the registered reference Vr, w = strip_rest.share of the arm's
        elevation (strip_rest.elevation of the whole pose G). N: the list's blended normals in the reference's frame
        (None when w is 0). w = 0, no map, or map_on False: cf as it was, bit for bit."""
        hs = self.map.get(rg.name) if self.map_on else None
        if hs is None:
            return cf, 0.0, None
        sr, s = self._sr, rg.side
        w = sr.share(sr.elevation(hs, G, s), *hs.cfg["map_elev"])
        if w <= 0:
            return cf, 0.0, None
        nl = getattr(rg, "nlist", len(rg.pts))
        _, _, Xm, Nm = sr.map_targets(hs, Vr, s, w, Xf=cf[:nl])
        cf = cf.copy()
        cf[:nl] = Xm
        return cf, w, Nm

    def gate_shut(self, G, side):
        """True while the side's first gate is shut: the arm under the gate's lo."""
        gr = self.md.grown[side]
        return self.md.elevation(G, side) < gr["gate"][0]

    @contextlib.contextmanager
    def fair_off(self):
        """A's posed skin as it was (no "fair_a" rule) inside the block; the parts' cache is cleared."""
        on, self.fair_on, self._pose = getattr(self, "fair_on", True), False, None
        try:
            yield
        finally:
            self.fair_on, self._pose = on, None

    @contextlib.contextmanager
    def map_off(self):
        """The fill alone (the composed target as without the map key) inside the block; the parts' cache is cleared."""
        on, self.map_on, self._pose = self.map_on, False, None
        try:
            yield
        finally:
            self.map_on, self._pose = on, None

    @contextlib.contextmanager
    def fold_off(self):
        """The relax rules without their fold trigger (Her.folded) inside the block; the parts' cache is cleared."""
        on, self.fold_on, self._pose = getattr(self, "fold_on", True), False, None
        try:
            yield
        finally:
            self.fold_on, self._pose = on, None

    def relaxed(self, rg, G, cf, Vr):
        """The filled carry cf [region points, 3] with each gate stage's relax rule (config gate2 "relax"): on the plain
        rows the stage opens, the edges A carries over `ratio` x rest (A's own creases, which B's published surface
        does not have) mark a pocket of the rows within `rows` edges of them, harmonically filled from its neighbours
        (Pocket, A's rotations smoothed); the fill is blended in by the stage's own smoothstep. At or under the stage's
        lo, cf as it was, bit for bit."""
        rules = getattr(rg, "relax", ())
        if not rules:
            return cf
        side = bool(rg.side)                                # no side (the neck): no elevation, w = 1
        el, P0, E = self.md.elevation(G, rg.side) if side else 0.0, self.bd.V0[rg.pts], np.stack(rg.edges, 1)
        for lo, hi, opened, rule in rules:
            if side:
                if el <= lo:
                    continue
                w = np.clip((el - lo) / (hi - lo), 0.0, 1.0)
                w = w * w * (3 - 2 * w)
            else:
                w = 1.0
            r = np.linalg.norm(cf[E[:, 0]] - cf[E[:, 1]], axis=1) / np.linalg.norm(P0[E[:, 0]] - P0[E[:, 1]], axis=1)
            hit = (r > rule["ratio"]) & (opened[E[:, 0]] | opened[E[:, 1]])
            if not hit.any():
                continue
            m = rows_around(len(P0), E, np.unique(E[hit]), rule["rows"]) & opened
            R = np.concatenate([c.rotations(Vr) for c in getattr(rg.carrier, "parts", [rg.carrier])])
            X = Pocket(P0, E, m, self.cfg["pocket_weight"]).fill(cf, R, self.cfg["frame_passes"])
            cf = cf + w * (X - cf)
        return cf

    def delta(self, G, name):
        """A region's relative delta on its points [points, 3], under its share: share M (c - published(part pose))."""
        P = self.part(G, name)
        return self.regions[name].share_at(G)[:, None] * np.einsum("nij,nj->ni", P["M"], P["cf"] - P["Pg"])

    def compose(self, G, Vp=None, regions=None):
        """The whole target [source vertices, 3] of the pose G: published + the deltas of `regions` (names; None: all)."""
        Vp = self.rt.published(self.bd, G) if Vp is None else Vp
        return compose(Vp, {n: (*self.regions[n].spread, self.delta(G, n)) for n in (self.regions if regions is None else regions)})

    def shut(self, G, side, regions=None):
        """(mm, mm) on the gated part of `side` (every point of the part nearer this side's list than its twin's, in a
        region or not): how far the regions under the gate rule (the grown ones, every side's: whatever the other arm
        does) move it off the published surface, and how far the other regions do, in rows they own inside the part
        (their own account, not the gate's). The rule: the first is 0 while the side's gate is shut.
        `regions`: the names composed (None: all)."""
        own = getattr(self.regions[self.cfg["out_region"].replace("{s}", side)], "gate_own", None)
        if own is None:
            return 0.0, 0.0
        out = []
        for ruled in (True, False):
            parts = {n: (*r.spread, self.delta(G, n)) for n, r in self.regions.items()
                     if hasattr(r, "gate_own") == ruled and (regions is None or n in regions)}
            out.append(float(np.linalg.norm(compose(np.zeros((len(self.bd.V0), 3)), parts)[own], axis=1).max() * 1000))
        return tuple(out)

    def carried(self, G, side, Vp=None, carry=None, regions=None, full=False):
        """(filled, carried alone, the reference's posed vertices), all on the source's skeleton, for one pose and side:
        the side's own region (config "out_region") before its border share.

        "relative" (the module docstring): the two carried surfaces are placed per point by B's own skinning (Vp: B's
        published vertices of G, computed if None); the reference's vertices are its part pose moved rigidly with
        the anchor (their edge lengths are what the target carries). "absolute": the reference posed by the whole pose
        and aligned by the anchor (the side's region alone, nothing composed). `carry` overrides the config.
        self.last: cf, Va (the filled surface and the reference in one frame, for distances between them), sig, guard,
        mem (relative_place's and the driver's account), others [points, 3]: the deltas of the regions that touch this
        one (`regions`: names composed, None = all), which the target adds whole. full=False: on the list's points
        (the region's first block, as before the border grew); True: on every region point (the list, then the new).
        """
        bd, p, cfg, car = self.bd, self.bd.p, self.cfg, self.car[side]
        ja, ra = self.anchor[side]
        name = cfg["out_region"].replace("{s}", side)
        rg = self.regions[name]
        pts = rg.pts
        nl = len(pts) if full else getattr(rg, "nlist", len(pts))
        if (carry or cfg["carry"]) == "absolute":
            Va, Ga = self.pose_ref(G)
            M = anchor_align(G[ja], p.rest[ja], self.Ab.G0[ra], Ga[ra])
            Xf, Xr, Va = (x @ M[:3, :3].T + M[:3, 3] for x in (*rg.carrier.carry(Va, both=True), Va))
            self.last = {"cf": Xf[:nl], "Va": Va, "sig": 1.0, "guard": 0, "mem": 0.0, "others": np.zeros((nl, 3))}
            return Xf[:nl], Xr[:nl], Va
        if Vp is None:
            Vp = self.rt.published(bd, G)
        P = self.part(G, name)
        oth = compose(np.zeros((len(bd.V0), 3)), {n: (*self.regions[n].spread, self.delta(G, n)) for n in self.touch[name]
                                                  if regions is None or n in regions})[pts]
        T = G[ja] @ np.linalg.inv(p.rest[ja])
        self.last = {"cf": P["cf"][:nl], "Va": P["Va"], "sig": P["sig"], "guard": P["guard"], "mem": P["mem"], "others": oth[:nl]}
        return tuple((Vp[pts] + np.einsum("nij,nj->ni", P["M"], c - P["Pg"]))[:nl] for c in (P["cf"], P["cr"])) + (P["Va"] @ T[:3, :3].T + T[:3, 3],)

    def target(self, G, side, Vp=None, carry=None, regions=None):
        """(X [region points, 3], info) for one pose of B's globals G and one side: the composed target (published + every
        region's delta; `regions`: the names composed, None = all) on the points of the side's region."""
        bd, Ab, md = self.bd, self.Ab, self.md
        sd = md.S[side]
        ids = sd["ids"]
        pts = md.first[ids]
        if Vp is None:
            Vp = self.rt.published(bd, G)
        rg = self.regions[self.cfg["out_region"].replace("{s}", side)]
        MC, MR, _ = self.carried(G, side, Vp, carry, regions, full=True)  # carried and filled, carried alone
        last, nl = self.last, len(ids)
        b = rg.share_at(G)[:, None]                                      # the border's share, by row and by pose
        Xa = b * MC + (1 - b) * Vp[rg.pts] + last["others"]              # + the regions that touch this one (compose's rule)
        gd = (0.0, 0.0) if (carry or self.cfg["carry"]) == "absolute" else self.shut(G, side, None if regions is None else [*regions, rg.name])
        extra = {"elev": md.elevation(G, side), "gated_d_max": gd[0], "gated_oth_max": gd[1],   # the side's gated part (shut)
                 "edge_all_max": edge_ratio(Xa, bd.V0[rg.pts], *rg.edges)[1]}
        X, MC, MR = Xa[:nl], MC[:nl], MR[:nl]                            # the list's points: what is returned and judged below
        last.update({"Xe": Xa[nl:], "share": b[:, 0], "cf": last["cf"][:nl], "others": last["others"][:nl]})
        d = np.linalg.norm(MC - Vp[pts], axis=1) * 1000
        db, d = d[md.beta < 1], d[md.beta == 1]                          # what the border rows must hide; the interior
        emin, emax, _ = edge_ratio(X, md.V0[ids], *self.edges[side])
        ecar = edge_ratio(MC, md.V0[ids], *self.edges[side])[1]         # before the border blend: what T5 judges
        eraw = edge_ratio(MR, md.V0[ids], *self.edges[side])[1]         # the carry alone: the bridge shows here
        pk = self.car[side].pocket
        pinfo = {"pk_edge_min": 1.0, "pk_edge_max": 1.0, "pk_d_p50": 0.0, "pk_d_max": 0.0}
        if pk is not None:
            pmin, pmax, _ = edge_ratio(MC, md.V0[ids], pk.edges[:, 0], pk.edges[:, 1])
            pd = surface_distance(last["cf"][pk.p], last["Va"], Ab.T) * 1000   # what the fill loses: how far it spans off A's hollow
            pinfo = {"pk_edge_min": pmin, "pk_edge_max": pmax, "pk_d_p50": float(np.percentile(pd, 50)), "pk_d_max": float(pd.max())}
            st = self.car[side].stats                                   # the slide's own account (empty for the fill)
            pinfo.update({f"pk_{k}": float(st[k]) for k in ("iters", "step", "rim", "flip") if k in st})
        Y = Vp[md.first].copy()
        Y[ids] = X
        g = md.girth(sd, Y)
        info = {"d_pub_p50": float(np.percentile(d, 50)), "d_pub_p95": float(np.percentile(d, 95)), "d_pub_max": float(d.max()),
                "d_bor_p50": float(np.percentile(db, 50)), "d_bor_max": float(db.max()),
                "edge_min": emin, "edge_max": emax, "edge_raw_max": eraw, "edge_car_max": ecar, **pinfo,
                "vol": md.volume(sd, Y) / sd["vol0"],
                **{f"girth_{k}": float(g[k] / self.girth0[side][k]) for k in ("mid_deltoid", "insertion")},
                "rel_sig_min": last["sig"], "rel_guard": float(last["guard"]), "drv_mem": last["mem"], **extra}
        return X, info


def fmt(i):
    return (f"d_pub {i['d_pub_p50']:.1f}/{i['d_pub_p95']:.1f}/{i['d_pub_max']:.1f} border {i['d_bor_p50']:.1f}/{i['d_bor_max']:.1f} mm"
            f"  edge {i['edge_min']:.2f}..{i['edge_max']:.2f}"
            f" (carried alone max {i['edge_raw_max']:.2f}, filled max {i['edge_car_max']:.2f})"
            f"  pocket edge {i['pk_edge_min']:.2f}..{i['pk_edge_max']:.2f} off A {i['pk_d_p50']:.1f}/{i['pk_d_max']:.1f} mm"
            f"  vol {i['vol']:.3f}  girth mid {i['girth_mid_deltoid']:.3f} ins {i['girth_insertion']:.3f}")


def cmd_test(h):
    bd, Ab, md, cfg = h.bd, h.Ab, h.md, h.cfg
    ok_all = True

    def line(name, ok, text):
        nonlocal ok_all
        ok_all &= bool(ok)
        print(f"{'PASS' if ok else 'FAIL'} {name}: {text}")

    rng = np.random.default_rng(7)
    R = polar(rng.normal(size=(3, 3)))
    t = rng.normal(size=3)
    for s in "lr":
        car, ids = h.car[s], md.S[s]["ids"]
        P0 = bd.V0[md.first[ids]]
        e = np.abs(car.carry(Ab.V0) - P0).max()
        line(f"T1 {s}", e < 1e-6, f"carry(rest) - P0 max {e:.2e} m")
        e = np.abs(car.carry(Ab.V0 @ R.T + t) - (P0 @ R.T + t)).max()
        line(f"T2 {s}", e < 1e-6, f"rigid motion of the rest: max {e:.2e} m")
    Va, Ga = h.pose_ref(bd.G0)
    dv, dg = np.abs(Va - Ab.V0).max(), np.abs(Ga - Ab.G0).max()
    print(f"   transfer of the rest pose: reference vertices off its rest by {dv:.2e} m, globals by {dg:.2e}")
    Vp0 = h.rt.published(bd, bd.G0)
    for s in "lr":
        ids = md.S[s]["ids"]
        X, _ = h.target(bd.G0, s, Vp0)
        e = np.abs(X - md.V0[ids]).max()
        txt = f"X(rest) - md.V0 max {e:.2e} m"
        if e >= 1e-5:
            txt += (f" | published(rest) - md.V0 {np.abs(Vp0[md.first[ids]] - md.V0[ids]).max():.2e}"
                    f", bd.V0 - md.V0 {np.abs(bd.V0[md.first[ids]] - md.V0[ids]).max():.2e}"
                    f", source G0 - rest {np.abs(bd.G0 - bd.p.rest).max():.2e}")
        line(f"T3 {s}", e < 1e-5, txt)
    for s in "lr":
        car, sd = h.car[s], md.S[s]
        d0 = np.linalg.norm(car.d0, axis=1) * 1000
        bad = ~car.ok
        where = ""
        if bad.any() and "arm" in sd:
            arm = np.asarray(sd["arm"])[bad] > 0.5
            where = f" (arm {int(arm.sum())}, torso {int((~arm).sum())}; their |d0| max {d0[bad].max():.1f} mm)"
        p95 = np.percentile(d0, 95)
        line(f"T4 {s}", p95 <= cfg["d0_p95_stop_mm"],
             f"ok False {int(bad.sum())} of {len(d0)}{where}; |d0| p50 {np.percentile(d0, 50):.2f} p95 {p95:.2f} max {d0.max():.2f} mm")
        if p95 > cfg["d0_p95_stop_mm"]:
            print("STOP: the rest shapes do not agree (|d0| p95 over the limit)")
            return False
    z = np.load(h.OUT / "poses.npz")
    names = [str(x) for x in z["name"]]
    for nm in cfg["dev_poses"]:
        if nm not in names:
            line(f"T5 {nm}", False, "not in poses.npz")
            continue
        i = names.index(nm)
        s = str(z["side"][i])
        ids = md.S[s]["ids"]
        car = h.car[s]
        ei, ej = h.edges[s]
        Xm_, im_ = h.target(z["G"][i], s)                              # T5 judges the pocket fill: the map off (T20 / T21's)
        with h.map_off():
            X, info = h.target(z["G"][i], s)
            MC, MR, _ = h.carried(z["G"][i], s)
        if h.map:
            print(f"     watch {nm} with the armpit map: filled max {im_['edge_car_max']:.2f}, edge {im_['edge_min']:.2f}..{im_['edge_max']:.2f}"
                  f" (map off {info['edge_car_max']:.2f}, {info['edge_min']:.2f}..{info['edge_max']:.2f}; against B's old rest)")
        inp = np.zeros(len(ids), bool)
        if car.pocket is not None:
            inp[car.pocket.p] = True
        rr = edge_ratio(MR, md.V0[ids], ei, ej)[2]
        torn = rr > cfg["torn"]
        out = torn & ~(inp[ei] & inp[ej])                              # the rule must cover every torn edge, both ends
        line(f"T5 {nm}", info["edge_car_max"] <= 3 and not out.any() and np.isfinite(X).all(),
             f"edge max carried alone {info['edge_raw_max']:.2f} -> filled {info['edge_car_max']:.2f}; torn edges (over"
             f" {cfg['torn']:g}) {int(torn.sum())}, outside the pocket {int(out.sum())} | {fmt(info)}")
        ia = h.target(z["G"][i], s, carry="absolute")[1]                # the whole-pose carry | the carry as configured
        print("     absolute | " + cfg["carry"] + ": " + "  ".join(f"{k} {ia[k]:.2f} | {info[k]:.2f}" for k in (
            "d_bor_max", "d_pub_p95", "d_pub_max", "edge_max", "edge_car_max", "pk_edge_max", "pk_d_max", "vol", "girth_mid_deltoid",
            "girth_insertion")) + f"  sigma min {info['rel_sig_min']:.3f} guarded {info['rel_guard']:.0f} driver memory {info['drv_mem']:.4f}")
        for e in np.nonzero(out)[0][:8]:
            a, b_ = ei[e], ej[e]
            print(f"     OUTSIDE edge {a}-{b_} ratio {rr[e]:.2f} in pocket {inp[a]} {inp[b_]}"
                  f" ref normals {_angle(car.nref[[a]], car.nref[[b_]])[0]:.0f} deg, own {_angle(h.N0[md.first[ids[[a]]]], h.N0[md.first[ids[[b_]]]])[0]:.0f} deg"
                  f" beta {md.beta[a]:.2f} {md.beta[b_]:.2f}")
        if info["edge_car_max"] > 3:
            r = edge_ratio(MC, md.V0[ids], ei, ej)[2]
            for e in np.argsort(-r)[:4]:
                a, b_ = ei[e], ej[e]
                print(f"     edge {a}-{b_} filled ratio {r[e]:.2f} (carried alone {rr[e]:.2f}) in pocket {inp[a]} {inp[b_]}"
                      f" beta {md.beta[a]:.2f} {md.beta[b_]:.2f}")
    # T6: no pocket rows = the old carry. T7: the fill of the rest is the rest.
    i = names.index(cfg["dev_poses"][0]) if cfg["dev_poses"][0] in names else 0
    Va, _ = h.pose_ref(z["G"][i])
    for s in "lr":
        car, ids = h.car[s], md.S[s]["ids"]
        P0 = bd.V0[md.first[ids]]
        c0 = h.carrier(s, pocket_rows=0)
        e = np.abs(c0.carry(Va) - car.carry(Va, fill=False)).max()
        moved = np.abs(car.carry(Va) - car.carry(Va, fill=False)).max(1) > 0
        npk = 0 if car.pocket is None else len(car.pocket.p)
        line(f"T6 {s}", e == 0 and c0.pocket is None and int(moved.sum()) <= npk,
             f"pocket_rows 0 - the carry alone: max {e:.2e} m; the fill moves {int(moved.sum())} points (pocket {npk})")
        if car.pocket is None:
            line(f"T7 {s}", True, "no pocket")
            continue
        e = np.abs(car.pocket.fill(P0) - P0).max()
        e2 = np.abs(car.pocket.fill(P0 @ R.T + t, np.broadcast_to(R, (len(P0), 3, 3)), car.frame_passes) - (P0 @ R.T + t)).max()
        line(f"T7 {s}", e < 1e-6 and e2 < 1e-6, f"fill(rest) - rest max {e:.2e} m; under a rigid motion {e2:.2e} m"
             f" ({len(car.bridge)} bridge edges, {npk} pocket points, {len(car.pocket.b)} holding)")
    # T9: the trunk and neck turned, the girdle's locals at rest: the target is the published surface (B's own skinning)
    from scipy.spatial.transform import Rotation
    p, pub = bd.p, h.rt.published
    Gt = p.rest.copy()
    for k in bd.order:
        L, pk = bd.rl[k].copy(), p.parent[k]
        if p.names[k] in cfg["t9_turns"]:
            L[:3, :3] = L[:3, :3] @ Rotation.from_rotvec(_unit(rng.normal(size=3)) * np.radians(cfg["t9_turns"][p.names[k]])).as_matrix()
        Gt[k] = Gt[pk] @ L if pk >= 0 else L
    Gt = h.drive(Gt)
    Vt = pub(bd, Gt)

    def shapes(G, s):                    # the correctives the other bones drive: X against the bare L(G) L(Gp)^-1 c, max m
        pts = md.first[md.S[s]["ids"]]
        Gg = h.girdle_pose(G, s)[0]
        M = relative_place(G @ p.skel.ibm, Gg @ p.skel.ibm, bd.J[pts], bd.W[pts], cfg["sig_lo"], cfg["sig_hi"])[0]
        return float(np.abs((pub(bd, G) - p._skin(G, {}))[pts] - np.einsum("nij,nj->ni", M, (pub(bd, Gg) - p._skin(Gg, {}))[pts])).max())

    for s in "lr":
        pts = md.first[md.S[s]["ids"]]
        with h.fold_off():                  # the carry alone: the fold trigger fixes B's own published folds (T26's)
            e = np.abs(h.target(Gt, s, Vt)[0] - Vt[pts]).max()
            ea = np.abs(h.target(Gt, s, Vt, carry="absolute")[0] - Vt[pts]).max()
        moved = np.abs(Vt[pts] - md.V0[md.S[s]["ids"]]).max()
        line(f"T9 {s}", e < 1e-5, f"bones outside every region turned ({' '.join(f'{k} {v}' for k, v in cfg['t9_turns'].items())} deg), every region's"
             f" locals at rest: X - published max {e * 1000:.4f} mm (absolute carry {ea * 1000:.1f} mm; the region moves {moved * 1000:.0f} mm;"
             f" correctives the trunk drives there {shapes(Gt, s) * 1000:.3f} mm)")
    # T10: a rigid motion of the whole body moves the target with it; the same pose twice is the same target
    Q = np.eye(4)
    Q[:3, :3], Q[:3, 3] = R, t
    for nm in cfg["dev_poses"][::3]:
        i = names.index(nm)
        s, G = str(z["side"][i]), z["G"][i]
        X1, X2, X3 = h.target(G, s)[0], h.target(G, s)[0], h.target(Q @ G, s)[0]
        e = np.abs(X3 - (X1 @ R.T + t)).max()
        line(f"T10 {nm}", e < 1e-6 and (X1 == X2).all(), f"whole-body rigid motion: max {e:.2e} m; twice the same: {bool((X1 == X2).all())};"
             f" correctives the other bones drive in the region {shapes(G, s) * 1000:.3f} mm")
    # T11: a config without `support` is the path of before the border grew (what any other body runs). Every region
    # composed = the stored target of that time (measured: to the bit). The two girdles alone = the stored relative
    # target, written before the regions, to 1e-5 and not 1e-6: that file posed the reference's 13 bones by the whole
    # map (identity turns on the 9 outside the girdle, which the transfer does not return exactly: the rest pose comes
    # back 4e-5 off in the reference's globals); a region poses its own 4. Measured 2.5-6.7 um with the 4, 0 with the
    # 13 as that file was written: asserted on the same line.
    gird = [n for n, r in h.regions.items() if r.side]
    h0 = Her({**{k_: v_ for k_, v_ in cfg.items() if k_ != "fair_a"}, "regions": {k: {a_: b_ for a_, b_ in v.items() if a_ != "support"} for k, v in cfg["regions"].items()}}, verbose=False)
    st = {k: np.load(h.OUT / f_) if (h.OUT / f_).exists() else None for k, f_ in cfg["t11_stored"].items()}
    tp = cfg["dev_poses"] + cfg["t14_poses"] + ["Jog_Fwd@11:r"]
    h0.fold_on = False                  # the path of before the border: the stored targets predate the fold trigger (T26's)

    def off(k, nm, regs):
        i, sn = names.index(nm), [str(x) for x in st[k]["name"]]
        return float(np.abs(h0.target(z["G"][i], str(z["side"][i]), regions=regs)[0] - st[k]["X"][sn.index(nm)]).max())

    if any(v is None for v in st.values()):
        line("T11", False, f"a stored target is missing in {h.OUT}: {[f_ for k, f_ in cfg['t11_stored'].items() if st[k] is None]}")
    else:
        e = {nm: (off("regions", nm, None), off("girdles", nm, gird)) for nm in tp}
        for n in gird:                                                   # the old transfer: every posed bone, the whole map
            h0.regions[n].ref_map, h0.regions[n].order = cfg["bone_map"], h0.order
        h0._pose = None
        for nm in tp:
            e13 = off("girdles", nm, gird)
            line(f"T11 {nm}", e[nm][0] < 1e-9 and e[nm][1] < 1e-5 and e13 < 1e-9,
                 f"no support region: every region - the stored target of before the border ({cfg['t11_stored']['regions']}) max {e[nm][0]:.2e} m"
                 f" (limit 1e-9); the girdles alone - the stored relative target ({cfg['t11_stored']['girdles']}) {e[nm][1]:.2e} m (limit 1e-5),"
                 f" with the reference's {len(h0.order)} bones posed as that file was {e13:.2e} m (limit 1e-9)")

    def turned(turns):
        G = p.rest.copy()
        for k in bd.order:
            L, pk = bd.rl[k].copy(), p.parent[k]
            if p.names[k] in turns:
                L[:3, :3] = L[:3, :3] @ Rotation.from_rotvec(_unit(rng.normal(size=3)) * np.radians(turns[p.names[k]])).as_matrix()
            G[k] = G[pk] @ L if pk >= 0 else L
        return h.drive(G)

    def worst(X, X0, ed, mask=None):     # the worst edge ratio against rest (edges with both ends in the mask)
        ei, ej = ed
        if mask is not None:
            keep = mask[ei] & mask[ej]
            ei, ej = ei[keep], ej[keep]
        return edge_ratio(X, X0, ei, ej)[1] if len(ei) else 1.0

    # T12: the neck alone. Published outside the region, on head-rigid points and on the outer row; inside, A's edges.
    nk = next(r for r in h.regions.values() if not r.side)
    ta = Ab.T[(nk.field[:, 0] > 0.02)[Ab.T].all(1)]                     # A's own neck: its triangles that follow the chain
    ae = (np.concatenate([ta[:, 0], ta[:, 1], ta[:, 2]]), np.concatenate([ta[:, 1], ta[:, 2], ta[:, 0]]))
    nloc = -np.ones(len(bd.V0), np.int64)
    nloc[nk.spread[0]] = nk.spread[1]
    Gn = turned(cfg["t12_turns"])
    Vn = pub(bd, Gn)
    Xn = h.compose(Gn, Vn)
    dn = np.linalg.norm(Xn - Vn, axis=1)
    headr = (bd.W * (bd.J == p.index[cfg["regions"][nk.name]["far"][0]])).sum(1) >= 0.999
    sh = nk.share
    e_out, e_head, e_row = dn[nloc < 0].max(), dn[headr].max(), dn[nk.pts[sh == 0]].max()
    P = h.part(Gn, nk.name)
    Mh = anchor_align(P["Gr"][nk.anchors[1][0]], p.rest[nk.anchors[1][0]], Ab.G0[nk.anchors[1][1]], Ab.G0[nk.anchors[1][1]])
    r_t, r_p = worst(Xn[nk.pts], bd.V0[nk.pts], nk.edges), worst(Vn[nk.pts], bd.V0[nk.pts], nk.edges)
    r_a, r_r = worst(P["Va_own"], Ab.V0, ae), worst(P["Va"], Ab.V0, ae)
    line("T12", max(e_out, e_head, e_row) < 1e-4 and r_t <= r_a + 0.15,
         f"neck alone ({' '.join(f'{k} {v}' for k, v in cfg['t12_turns'].items())} deg): X - published max mm: outside the region"
         f" {e_out * 1000:.4f}, head-rigid points ({int(headr.sum())}) {e_head * 1000:.4f}, outer row {e_row * 1000:.4f} (limit 0.1);"
         f" ramp rows off the core (what the share hides) {dn[nk.pts[(sh > 0) & (sh < 1) & ~nk.core]].max() * 1000:.1f} mm,"
         f" interior moved {dn[nk.pts[sh == 1]].max() * 1000:.1f} mm | worst edge in the region: target {r_t:.2f}, published {r_p:.2f},"
         f" A's own {r_a:.2f} (A registered at both anchors {r_r:.2f}; limit A's own + 0.15); sigma min {P['sig']:.3f} guarded {P['guard']}")
    # T13: the listing order never matters (bit for bit); no step where girdle and neck overlap
    h2 = Her({**cfg, "sides": cfg["sides"][::-1], "regions": dict(reversed(list(cfg["regions"].items())))}, verbose=False)
    ing = np.zeros(len(bd.V0), bool)
    for n in gird:
        ing[h.regions[n].spread[0]] = True
    for nm in cfg["t14_poses"]:
        i = names.index(nm)
        G, s = z["G"][i], str(z["side"][i])
        g = h.regions[cfg["out_region"].replace("{s}", s)]
        Vp = pub(bd, G)
        Xa = h.compose(G, Vp)
        Xl, info = h.target(G, s, Vp)
        X = np.r_[Xl, h.last["Xe"]]                                      # every region point: the list, then the grown rows
        same = bool((Xa == h2.compose(G, Vp)).all() and (Xl == h2.target(G, s, Vp)[0]).all())
        e_w = np.abs(X - Xa[g.pts]).max()
        gn, bsh, X0 = nloc[g.pts], g.share_at(G), bd.V0[g.pts]
        ov = (gn >= 0) & (bsh > 0) & (nk.share[np.maximum(gn, 0)] > 0)
        r_ov, r_g = worst(X, X0, g.edges, ov), worst(X, X0, g.edges, (bsh == 1) & (gn < 0))
        r_n = worst(Xa[nk.pts], bd.V0[nk.pts], nk.edges, (nk.share == 1) & ~ing[nk.pts])
        line(f"T13 {nm}", same and r_ov <= max(r_g, r_n) + 0.15,
             f"regions listed backwards, the same bit for bit (whole body and the side): {same}; the side - the whole body on its points {e_w:.1e} m;"
             f" worst edge in the overlap rows ({int(ov.sum())} points, both shares > 0) {r_ov:.2f}, girdle interior {r_g:.2f},"
             f" neck interior {r_n:.2f} (limit the worse + 0.15)")
        # T14: the measured poses, on the side's points inside the neck region (the trap line and the throat pit)
        MA = h.carried(G, s, Vp, carry="absolute", full=True)[1]
        r_t, r_p, r_a = (worst(x, X0, g.edges, gn >= 0) for x in (X, Vp[g.pts], MA))
        line(f"T14 {nm}", r_t < 2.5 or r_t <= r_a + 0.15,
             f"trap line and throat pit (the side's {int((gn >= 0).sum())} points in the neck region): worst edge target {r_t:.2f} |"
             f" published {r_p:.2f} | A's own there (absolute carry, alone) {r_a:.2f}; the whole side: target {info['edge_max']:.2f},"
             f" published {worst(Vp[g.pts], X0, g.edges):.2f}")
    # T15: the grown region's outer row (a neighbour outside the region) has share 0 shut and open: the region's own
    # target there IS the published surface. T16: the gate shut, the gated part is published. T17: the ramp's edges.
    lo = {s: md.grown[s]["gate"][0] for s in md.grown}
    t16 = set(cfg["t16_poses"] + cfg["dev_poses"] + cfg["t14_poses"] + list(cfg["t17_poses"]) + cfg["t17_watch"])
    for s in md.grown:
        g, gr = h.regions[cfg["out_region"].replace("{s}", s)], md.grown[s]
        allid = np.r_[md.S[s]["ids"], gr["new"]]
        inr = np.zeros(md.n, bool)
        inr[allid] = True
        outer = (md.adj @ (~inr).astype(float) > 0)[allid]
        sh, e = max(gr["closed"][outer].max(), gr["opened"][outer].max()), 0.0
        for nm in cfg["dev_poses"] + cfg["t14_poses"] + list(cfg["t17_poses"]):
            i = names.index(nm)
            if str(z["side"][i]) == s:
                Vp = pub(bd, z["G"][i])
                e = max(e, float(np.abs(np.r_[h.target(z["G"][i], s, Vp, regions=[g.name])[0], h.last["Xe"]] - Vp[g.pts])[outer].max()))
        line(f"T15 {s}", sh == 0 and e < 1e-9, f"the region's outer row ({int(outer.sum())} of {len(allid)} points): share max {sh:g} shut and open;"
             f" the region's own target - published there max {e:.1e} m (limit 1e-9)")
    # T16, per side and on the composed target: while a side's gate is shut (its arm under the gate, whatever the other
    # arm does) the regions under the gate rule (every side's) leave that side's gated part on the published surface.
    # Other regions own rows inside the part (the neck: the part map's upper rows carry the neck's weight) and move
    # them by their own rule: printed, not the gate's.
    for nm in sorted(t16):
        G = z["G"][names.index(nm)]
        el = {s: md.elevation(G, s) for s in sorted(md.grown)}
        for s in el:
            if h.gate_shut(G, s):
                gd, go = h.shut(G, s)
                line(f"T16 {nm} side {s}", gd < 1.0, f"arm elevation {el[s]:.0f} deg (gate from {lo[s]:g}; other {' '.join(f'{v:.0f}' for k, v in el.items() if k != s)}):"
                     f" the side's gated part ({len(h.regions[cfg['out_region'].replace('{s}', s)].gate_own)} points) off published by the regions under"
                     f" the gate max {gd:.4f} mm (limit 1); by the other regions in rows they own {go:.1f} mm")
    for nm in list(cfg["t17_poses"]) + cfg["t17_watch"]:
        i = names.index(nm)
        G, s = z["G"][i], str(z["side"][i])
        g = h.regions[cfg["out_region"].replace("{s}", s)]
        Vp = pub(bd, G)
        X = np.r_[h.target(G, s, Vp)[0], h.last["Xe"]]
        sh, el = h.last["share"], md.elevation(G, s)
        MC = h.carried(G, s, Vp, full=True)[0] + h.last["others"]
        ei, ej = g.edges
        t, c, pp = (edge_ratio(x, bd.V0[g.pts], ei, ej)[2] for x in (X, MC, Vp[g.pts]))
        ramp = (np.minimum(sh[ei], sh[ej]) < 1) & (np.maximum(sh[ei], sh[ej]) > 0)
        over = ramp & (t > 2.5)
        bad = over & (t > np.maximum(c, pp) + 0.15)
        txt = (f"elevation {el:.0f} deg: ramp edges over 2.5x {int(over.sum())}, not explained by the carried or the published surface's own"
               f" stretch + 0.15: {int(bad.sum())}; worst ramp edge {t[ramp].max():.2f}" + (f", worst unexplained {t[bad].max():.2f}" if bad.any() else ""))
        if nm in cfg["t17_poses"]:
            line(f"T17 {nm}", int(over.sum()) <= cfg["t17_poses"][nm] and not bad.any(), txt + f" (limit {cfg['t17_poses'][nm]} over, 0 unexplained)")
        else:
            print(f"     watch {nm}: {txt}")
    # T18: at or under the second stage's lo, the composed target is the stored one of before the stage, bit for bit
    old = np.load(h.OUT / cfg["t18_stored"])
    io = {str(x): i for i, x in enumerate(old["name"])}
    raw = np.unique(np.concatenate([r.spread[0] for r in h.regions.values()]))
    ids_c = np.unique(md.src[raw[raw < len(md.src)]])
    common, ia, ib = np.intersect1d(ids_c, old["ids_c"], return_indices=True)
    for nm in cfg["t18_poses"]:
        G = z["G"][names.index(nm)]
        el = max(md.elevation(G, s) for s in sorted(md.grown))
        nrl, nk.relax = getattr(nk, "relax", None), []        # and the neck's relax rule (T23's) is off: stored before it
        with h.map_off(), h.fair_off(), h.fold_off():  # the stage alone (map: T20 / T21; 
                                                                    # fair_a off; the relax's fold trigger, notch.md 4: T26)
            d = float(np.abs(h.compose(G, pub(bd, G))[md.first[ids_c]][ia] - old["Xc"][io[nm]][ib]).max())
        nk.relax, h._pose = nrl, None
        line(f"T18 {nm}", d == 0.0, f"elevation {el:.1f} deg: composed target - stored ({cfg['t18_stored']}) max {d * 1000:.3g} mm on"
             f" {len(common)} shared points (limit exactly 0)")
    # T19: the fold at A's (fold_probe's measure on the reference dump's fold set)
    import fold_probe as fp
    c19 = cfg["t19"]
    Z = np.load(h.OUT / c19["ref"])
    M = fp.mesh_of(Z, sp.csr_matrix(md.adj), c19["k"])
    for nm in c19["poses"]:
        G, s = z["G"][names.index(nm)], str(z["side"][names.index(nm)])
        c = fp.pose_ctx(Z, M, nm, s, c19["top"])
        new = h.compose(G, pub(bd, G))[md.first]
        ra = np.ones(len(M.E), bool)
        a_, n_ = fp.stats(M, c, c.S["A"], ra), fp.stats(M, c, new, ra)
        line(f"T19 {nm}", n_[3] <= a_[3] + c19["valley_deg"] and abs(n_[0] - a_[0]) <= c19["depth_mm"],
             f"fold ({int(c.cl.sum())} points): valley max {n_[3]:.1f} deg (A {a_[3]:.1f} + {c19['valley_deg']:g}); depth mean {n_[0]:.2f} mm"
             f" (A {a_[0]:.2f} +- {c19['depth_mm']:g})")
    # T20 / T21: the armpit map (config support "map", Her.mapped). T20: with both arms at or under the map's lo, the
    # composed target is the fill alone, bit for bit (sampled over poses.npz). T21: on cfg t21_poses the composed band
    # is strip_rest's map (map_targets) through a second path (its own HerStrip and Her, the carry not handed over),
    # placed as compose places it (within 1e-6 m, the normals too); every other vertex bit for bit against the map off
    if h.map:
        sr, hs = h._sr, next(iter(h.map.values()))
        lo = hs.cfg["map_elev"][0]
        ev = np.array([[sr.elevation(hs, z["G"][i], s_) for s_ in cfg["sides"]] for i in range(len(names))])
        low = np.nonzero(ev.max(1) <= lo)[0]
        pick = low[np.linspace(0, len(low) - 1, min(cfg["t20_n"], len(low))).astype(int)] if len(low) else low
        d20 = 0.0
        for i in pick:
            G = z["G"][i]
            Vp = pub(bd, G)
            X1 = h.compose(G, Vp)
            with h.map_off():
                X0 = h.compose(G, Vp)
            d20 = max(d20, float(np.abs(X1 - X0).max()))
        line("T20", len(pick) > 0 and d20 == 0.0, f"{len(low)} of {len(names)} poses have both arms at or under {lo:g} deg; on {len(pick)}"
             f" of them ({', '.join(names[i] for i in pick)}) composed with the map - without max {d20!r} m (limit exactly 0)")
        hs2 = sr.HerStrip({**hs.cfg}).load()                 # the second path: strip_rest's own Her and lay
        for nm in cfg["t21_poses"]:
            with h.fold_off():                               # the map alone: the fold trigger acts after it (T26's)
                i = names.index(nm)
                G, s_ = z["G"][i], str(z["side"][i])
                rn = cfg["out_region"].replace("{s}", s_)
                rg = h.regions[rn]
                Vp = pub(bd, G)
                X1 = h.compose(G, Vp)
                P1 = h.part(G, rn)
                with h.map_off():
                    X0 = h.compose(G, Vp)
                    P0 = dict(h.part(G, rn))
                w2 = sr.share(sr.elevation(hs2, G, s_), *hs2.cfg["map_elev"])
                _, _, Xm, Nm = sr.map_targets(hs2, P0["Va"], s_, w2)
                b2 = hs2.loc[s_]
                cf = P0["cf"].copy()
                cf[b2] = Xm[b2]
                parts = {n: (*r.spread, h.delta(G, n) if n != rn else
                             r.share_at(G)[:, None] * np.einsum("nij,nj->ni", P0["M"], cf - P0["Pg"])) for n, r in h.regions.items()}
                Xe = compose(Vp, parts)
                band = np.zeros(len(X1), bool)                   # every side's band the map moves in this pose (w > 0)
                for n, hm in h.map.items():
                    if n == rn or h.part(G, n)["map_w"] > 0:
                        raw, loc = h.regions[n].spread
                        band[raw[np.isin(loc, hm.loc[h.regions[n].side])]] = True
                e_b = float(np.abs(X1[band] - Xe[band]).max())
                e_n = float(np.abs(P1["map_N"][hs.loc[s_]] - Nm[b2]).max()) if P1["map_N"] is not None else np.inf
                e_o = float(np.abs(X1[~band] - X0[~band]).max())
                moved = float(np.linalg.norm(X1[band] - X0[band], axis=1).max())
                line(f"T21 {nm}", e_b <= 1e-6 and e_n <= 1e-6 and e_o == 0.0 and abs(P1["map_w"] - w2) <= 1e-12,
                     f"map w {P1['map_w']:.3f} (second path {w2:.3f}); band ({int(band.sum())} vertices, moved up to {moved * 1000:.2f} mm):"
                     f" composed - strip_rest's map placed max {e_b:.2e} m, normals {e_n:.2e} (limit 1e-6); outside the band - map off"
                     f" max {e_o!r} m (limit exactly 0)")
    # T22: the armpit map's bar as a test (strip_rest.cmd_turned's own numbers, read from its report; map on)
    if h.map:
        import io, re
        hs22 = next(iter(h.map.values()))
        tol22 = cfg["t22_tol"]
        for key, lim_name in (("t22_own", "A's own"), ("t22_fill", "fill")):
            for nm in cfg[key]:
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    h._sr.cmd_turned(hs22, [nm])
                m = re.search(rf"== {re.escape(nm)} \((.)\) w ([\d.]+): turned map (\d+) \[([\d, ]*)\], .*? map edge max ([\d.]+), A's own max ([\d.]+)"
                              r".*? A'S OWN surface under the band's triangles: turned (\d+) \[([\d, ]*)\]"
                              r".*? fill max ([\d.]+)", buf.getvalue())
                if not m:
                    line(f"T22 {nm}", False, "cmd_turned's report not read: " + buf.getvalue()[:200])
                    continue
                tm_, rm_, own_, fill_ = int(m.group(3)), float(m.group(5)), float(m.group(6)), float(m.group(9))
                tids, oids = {int(x) for x in m.group(4).split(",") if x.strip()}, {int(x) for x in m.group(8).split(",") if x.strip()}
                ref_ = own_ if key == "t22_own" else fill_
                ot = nm in cfg.get("t22_own_turned", ())
                line(f"T22 {nm}", (tids <= oids and tm_ <= int(m.group(7)) if ot else tm_ == 0) and rm_ <= ref_ + tol22,
                     f"({m.group(1)}) w {m.group(2)}: turned triangles {tm_} {sorted(tids)} (limit " + (f"A's own {m.group(7)} {sorted(oids)}" if ot else "0") + f"); worst band edge {rm_:.2f} against {lim_name} {ref_:.2f}"
                     f" (limit +{tol22:g}); A's own {own_:.2f}, fill {fill_:.2f}")
    # T23: the neck's relax rule (config neck "relax"): against the rule off, on the measured poses
    if getattr(nk, "relax", None):
        c23 = nk.relax[0][3]
        outg = np.unique(np.concatenate([h.group[h.regions[cfg["out_region"].replace("{s}", s_)].spread[0]] for s_ in cfg["sides"]]))
        keep = ~np.isin(h.group[nk.pts], outg)
        ek = keep[nk.edges[0]] & keep[nk.edges[1]]
        e23 = (nk.edges[0][ek], nk.edges[1][ek])
        rl = nk.relax
        gpts = np.unique(np.concatenate([h.regions[cfg["out_region"].replace("{s}", s_)].spread[0] for s_ in cfg["sides"]]))
        hd = (bd.W * (bd.J == p.index[cfg["regions"][nk.name]["far"][0]])).sum(1) >= 0.999
        nkp = np.zeros(len(bd.V0), bool)
        nkp[nk.spread[0]] = True
        for nm in cfg["t23_poses"]:
            G = z["G"][names.index(nm)]
            Vp = pub(bd, G)
            with h.fold_off():                              # the ratio rule alone: the fold trigger is T26's
                X1 = h.compose(G, Vp)
                nk.relax, h._pose = [], None
                try:
                    X0 = h.compose(G, Vp)
                finally:
                    nk.relax, h._pose = rl, None
            def er(X):
                return np.linalg.norm(X[nk.pts][e23[0]] - X[nk.pts][e23[1]], axis=1) / np.linalg.norm(bd.V0[nk.pts][e23[0]] - bd.V0[nk.pts][e23[1]], axis=1)
            t1, t0, pp = er(X1), er(X0), er(Vp)
            lim = 2.5
            n1, n0 = int(((t1 > lim) & (pp <= lim)).sum()), int(((t0 > lim) & (pp <= lim)).sum())
            e_h = float(np.abs(X1[hd] - X0[hd]).max())
            gi = np.zeros(len(bd.V0), bool)
            gi[gpts] = True
            e_g = float(np.abs(X1[gi & ~nkp] - X0[gi & ~nkp]).max())
            line(f"T23 {nm}", n1 == 0 and e_h == 0.0 and e_g == 0.0,
                 f"neck set ({len(e23[0])} edges): over 2.5x with the published surface under it: {n1} (rule off {n0}); worst edge {t1.max():.2f}"
                 f" (off {t0.max():.2f}, published {pp.max():.2f}); Head-rigid points ({int(hd.sum())}) moved by the rule max {e_h!r} m,"
                 f" girdle regions outside the neck {e_g!r} m (limit exactly 0)")
    # T26: the relax rules' fold trigger (Her.folded; body_facts/notch.md 4). On t26_poses, the composed surface has no
    # region edge folded past its rest dihedral by over the rule's fold (each region's own triangles, the rows its rules
    # open); on t26_quiet (no seed) the composed target is the one with the trigger off, bit for bit
    if cfg.get("t26_poses") and any("fold" in r[3] for g in h.regions.values() for r in getattr(g, "relax", ())):
        import fold_probe as fp
        for nm in cfg["t26_poses"] + cfg["t26_quiet"]:
            G = z["G"][names.index(nm)]
            Vp = pub(bd, G)
            X1 = h.compose(G, Vp)
            if nm in cfg["t26_quiet"]:
                with h.fold_off():
                    X0 = h.compose(G, Vp)
                line(f"T26 {nm}", np.array_equal(X1, X0), f"no seed: composed - trigger off max {float(np.abs(X1 - X0).max())!r} m (limit exactly 0)")
                continue
            worst = []
            for rn in sorted(h.regions):
                rg = h.regions[rn]
                for lo, hi, opened, rule in getattr(rg, "relax", ()):
                    if "fold" in rule and getattr(rg, "fold_tris", None) is not None:
                        e, d = fp.dihedral(X1[rg.pts], rg.fold_tris)
                        x = np.where(opened[e[:, 0]] | opened[e[:, 1]], np.abs(d) - np.abs(rg.fold_d0), -np.inf)
                        worst.append((float(x.max()), int((x > rule["fold"]).sum()), rule["fold"], rn))
            ok = all(n == 0 for _, n, _, _ in worst)
            line(f"T26 {nm}", ok, "fold past rest: " + "; ".join(f"{rn} worst {x:.0f} deg, over {f:g}: {n}" for x, n, f, rn in worst))
    print("ALL PASS" if ok_all else "SOME FAILED")
    return ok_all


def table(names, kinds, infos):
    for kd in sorted(set(kinds)):
        rows = [i for i, k in zip(infos, kinds) if k == kd]
        print(f"{kd} ({len(rows)} poses)   min / median / max")
        for key in INFO:
            v = np.array([r[key] for r in rows])
            print(f"  {key:18s} {v.min():8.3f} {np.median(v):8.3f} {v.max():8.3f}")
    for key in ("edge_max", "edge_car_max", "pk_d_max", "d_pub_max"):
        w = np.argsort([-i[key] for i in infos])[:5]
        print(f"worst by {key}:")
        for i in w:
            print(f"  {names[i]:28s} {kinds[i]:8s} {fmt(infos[i])}")


def cmd_target(h, poses):
    z = np.load(h.OUT / "poses.npz")
    names = [str(x) for x in z["name"]]
    sel = list(range(len(names)))
    if poses:
        miss = [p for p in poses if p not in names]
        if miss:
            sys.exit(f"not in poses.npz: {miss}")
        sel = [names.index(p) for p in poses]
    X, Xe, Xc, Xr, infos, shut, t0 = [], [], [], [], [], [], time.time()
    # the whole composed surface, on the union of every region's points: what a picture of a pose shows. ids_c: md ids
    # (sorted); raw_c: the regions' source vertices the model has no point for (a derived region is built on the whole
    # source mesh, the model on its body part), stored by vertex (Xr)
    raw = np.unique(np.concatenate([r.spread[0] for r in h.regions.values()]))
    ids_c, raw_c = np.unique(h.md.src[raw[raw < len(h.md.src)]]), raw[raw >= len(h.md.src)]
    lo = {s: g["gate"][0] for s, g in getattr(h.md, "grown", {}).items()}
    for i in sel:
        G, side = z["G"][i], str(z["side"][i])
        Vp = h.rt.published(h.bd, G)
        x, info = h.target(G, side, Vp)
        X.append(x)
        Xe.append(h.last["Xe"])
        C = h.compose(G, Vp)                                             # the parts are this pose's (Her.part): no second carry
        Xc.append(C[h.md.first[ids_c]])
        Xr.append(C[raw_c])
        for s in sorted(lo):                                             # a shut gate: the side's gated part is published
            el = info["elev"] if s == side else h.md.elevation(G, s)     #   (each side of the pose, whatever the other does)
            if h.gate_shut(G, s):
                gd, go = (info["gated_d_max"], info["gated_oth_max"]) if s == side else h.shut(G, s)
                shut.append((gd, f"{names[i]} side {s}"))
                if poses or gd >= 1.0:
                    print(f"gate shut {names[i]:28s} side {s} elevation {el:5.1f} deg: gated part off published by the regions under the gate"
                          f" max {gd:.3f} mm; by the other regions in rows they own {go:.1f} mm")
        infos.append(info)
        if poses:
            print(f"{names[i]:28s} {fmt(info)}")
    cfg = h.cfg
    out = h.OUT / (cfg["dev_out"] if poses else cfg["out"])
    if cfg["carry"] != HER["carry"]:                                     # never over the default's file
        out = out.with_name(f"{out.stem}_{cfg['carry']}.npz")
    params = {**{k: v for k, v in cfg.items()}, "method": "carried_target", "posed": h.order,
              "not_ok": {n: int((~r.carrier.ok).sum()) for n, r in h.regions.items()}}
    pocket = {}
    for s in cfg["sides"]:                       # local indices into the side's region points (md.S[s]["ids"] order)
        c = h.car[s]
        pocket[f"pocket_{s}"] = np.zeros(0, np.int64) if c.pocket is None else c.pocket.p
        pocket[f"bridge_{s}"] = c.bridge
        pocket[f"ext_{s}"] = h.ext.get(s, np.zeros(0, np.int64))   # md point ids of Xe's rows
    w = max(shut, default=(0.0, "-"))
    print(f"gate shut (a side's elevation under {min(lo.values(), default=0.0):g} deg): {len(shut)} (pose, side), gated part off published by the"
          f" regions under the gate max {w[0]:.3f} mm at {w[1]} (limit 1); {len(sel)} poses in {time.time() - t0:.0f} s"
          f" ({(time.time() - t0) / max(len(sel), 1):.2f} s a pose)")
    np.savez_compressed(out, X=np.array(X), Xe=np.array(Xe), Xc=np.array(Xc), ids_c=ids_c, Xr=np.array(Xr), raw_c=raw_c, name=z["name"][sel], side=z["side"][sel], kind=z["kind"][sel],
                        info=json.dumps(infos), params=json.dumps(params), **pocket)
    table([names[i] for i in sel], [str(z["kind"][i]) for i in sel], infos)
    print(f"wrote {out}  X {np.array(X).shape}  Xc {np.array(Xc).shape} (every region's points, composed) + {len(raw_c)} vertices outside the model (Xr)")


def cmd_rebaseline(h):
    """Rewrite the three frozen references T11 and T18 compare against (target_a_regions / target_a_rel / target_a_l18 .npz),
    from exactly the paths those tests run, for every pose each file holds. Why: B's published skin weights changed at the
    source (her_b chain_relax, lead 23, notch.md 5), so the stored bits of before no longer hold; the coordinator ruled the
    baselines are reset in the same change. Keys, names, order and dtypes are kept; only X (T11) and Xc (T18) are replaced."""
    bd, md, cfg = h.bd, h.md, h.cfg
    z = np.load(h.OUT / "poses.npz")
    names = [str(x) for x in z["name"]]
    pub = h.rt.published
    h0 = Her({**{k_: v_ for k_, v_ in cfg.items() if k_ != "fair_a"}, "regions": {k: {a_: b_ for a_, b_ in v.items() if a_ != "support"} for k, v in cfg["regions"].items()}}, verbose=False)
    h0.fold_on = False
    gird = [n for n, r in h0.regions.items() if r.side]

    def save(fname, upd):
        old = np.load(h.OUT / fname, allow_pickle=False)
        d = {k: old[k] for k in old.files}
        for k, v in upd.items():
            assert d[k].shape == v.shape and d[k].dtype == v.dtype, (fname, k)
            print(f"{fname} {k}: max move per pose (mm), worst {max(float(np.abs(v[i] - d[k][i]).max()) for i in range(len(v))) * 1000:.4g}")
            for i, nm in enumerate(d["name"]):
                print(f"   {fname} {nm}: {float(np.abs(v[i] - d[k][i]).max()) * 1000:.4g} mm")
            d[k] = v
        np.savez_compressed(h.OUT / fname, **d)

    def tgt(nm, regs):
        i = names.index(nm)
        return h0.target(z["G"][i], str(z["side"][i]), regions=regs)[0]

    old = np.load(h.OUT / cfg["t11_stored"]["regions"])
    save(cfg["t11_stored"]["regions"], {"X": np.stack([tgt(str(n), None) for n in old["name"]]).astype(old["X"].dtype)})
    old = np.load(h.OUT / cfg["t11_stored"]["girdles"])
    for n in gird:
        h0.regions[n].ref_map, h0.regions[n].order = cfg["bone_map"], h0.order
    h0._pose = None
    save(cfg["t11_stored"]["girdles"], {"X": np.stack([tgt(str(n), gird) for n in old["name"]]).astype(old["X"].dtype)})
    old = np.load(h.OUT / cfg["t18_stored"])
    raw = np.unique(np.concatenate([r.spread[0] for r in h.regions.values()]))
    ids_c = np.unique(md.src[raw[raw < len(md.src)]])
    print("T18 ids_c: current derivation equals the old file's:", bool(np.array_equal(ids_c, old["ids_c"])), len(ids_c), len(old["ids_c"]))
    nk = next(r for r in h.regions.values() if not r.side)
    Xc = []
    for n in old["name"]:
        G = z["G"][names.index(str(n))]
        nrl, nk.relax = getattr(nk, "relax", None), []
        with h.map_off(), h.fair_off(), h.fold_off():
            Xc.append(h.compose(G, pub(bd, G))[md.first[old["ids_c"]]])
        nk.relax, h._pose = nrl, None
    save(cfg["t18_stored"], {"Xc": np.stack(Xc).astype(old["Xc"].dtype)})


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=["test", "target", "rebaseline"])
    ap.add_argument("--poses", default="", help="comma-separated pose names: a subset, written to the dev file")
    ap.add_argument("--carry", default=HER["carry"], choices=["relative", "absolute"], help="see the module docstring")
    a = ap.parse_args()
    h = Her({**HER, "carry": a.carry})
    if a.cmd == "test":
        sys.exit(0 if cmd_test(h) else 1)
    if a.cmd == "rebaseline":
        cmd_rebaseline(h)
        return
    cmd_target(h, [p for p in a.poses.split(",") if p])


if __name__ == "__main__":
    main()
