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
import json
import sys
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
        self.edges = e[np.asarray(mask, bool)[e].any(1)]     # every edge with an end in the pocket

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


def edge_ratio(X, X0, ei, ej):
    """(min, max) of posed / rest length over the edges (ei, ej)."""
    r = np.linalg.norm(X[ei] - X[ej], axis=1) / np.maximum(np.linalg.norm(X0[ei] - X0[ej], axis=1), 1e-12)
    return float(r.min()), float(r.max()), r


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
INFO = ["d_pub_p50", "d_pub_p95", "d_pub_max", "edge_min", "edge_max", "edge_raw_max", "edge_car_max", "pk_edge_min", "pk_edge_max",
        "pk_d_p50", "pk_d_max", "vol", "girth_mid_deltoid", "girth_insertion"]


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
        self.car, self.anchor, self.edges = {}, {}, {}
        for s in "lr":
            ids = md.S[s]["ids"]
            A = sp.triu(md.adj[ids][:, ids], 1).tocoo()
            self.edges[s] = (A.row, A.col)
            self.car[s] = self.carrier(s)
            ch = cfg["anchor_child"].replace("{s}", s)
            ra, ja = Ab.p.parent[Ab.p.index[ch]], bd.p.parent[bd.p.index[ch]]
            rn, sn = self.ref_names[ra], bd.p.names[ja]
            assert cfg["bone_map"].get(rn, rn) == sn, f"anchor: reference {rn} does not map to source {sn}"
            self.anchor[s] = (ja, ra)
        self.girth0 = {s: md.girth(md.S[s], md.V0) for s in "lr"}
        if verbose:
            for s in "lr":
                c = self.car[s]
                print(f"pocket {s}: {len(c.bridge)} bridge edges, {0 if c.pocket is None else len(c.pocket.p)} pocket points"
                      f" of {len(md.S[s]['ids'])} (bridge_deg {cfg['bridge_deg']}, rows {cfg['pocket_rows']}, weight {cfg['pocket_weight']})")
            print(f"reference bones posed ({len(self.order)}): {' '.join(self.order)}")
            print(f"reference bones left at rest ({len(left)}): {' '.join(left)}")
            print("anchor:", {s: (self.ref_names[ra], bd.p.names[ja]) for s, (ja, ra) in self.anchor.items()},
                  "(reference, source)")

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

    def carried(self, G, side):
        """(filled, carried alone, the reference's posed vertices), all on the source's skeleton, for one pose and side."""
        Va, Ga = self.pose_ref(G)
        ja, ra = self.anchor[side]
        M = anchor_align(G[ja], self.bd.p.rest[ja], self.Ab.G0[ra], Ga[ra])
        Xf, Xr = self.car[side].carry(Va, both=True)
        return tuple(x @ M[:3, :3].T + M[:3, 3] for x in (Xf, Xr, Va))

    def target(self, G, side, Vp=None):
        """(X [region points, 3], info) for one pose of B's globals G and one side."""
        bd, Ab, md = self.bd, self.Ab, self.md
        sd = md.S[side]
        ids = sd["ids"]
        pts = md.first[ids]
        if Vp is None:
            Vp = self.rt.published(bd, G)
        MC, MR, VaM = self.carried(G, side)                              # carried and filled, carried alone, A posed
        b = md.blend(G, side)[:, None]                                   # the border's share, by row and by pose
        X = b * MC + (1 - b) * Vp[pts]
        d = np.linalg.norm(MC - Vp[pts], axis=1)[md.beta == 1] * 1000
        emin, emax, _ = edge_ratio(X, md.V0[ids], *self.edges[side])
        ecar = edge_ratio(MC, md.V0[ids], *self.edges[side])[1]         # before the border blend: what T5 judges
        eraw = edge_ratio(MR, md.V0[ids], *self.edges[side])[1]         # the carry alone: the bridge shows here
        pk = self.car[side].pocket
        pinfo = {"pk_edge_min": 1.0, "pk_edge_max": 1.0, "pk_d_p50": 0.0, "pk_d_max": 0.0}
        if pk is not None:
            pmin, pmax, _ = edge_ratio(MC, md.V0[ids], pk.edges[:, 0], pk.edges[:, 1])
            pd = surface_distance(MC[pk.p], VaM, Ab.T) * 1000           # what the fill loses: how far it spans off A's hollow
            pinfo = {"pk_edge_min": pmin, "pk_edge_max": pmax, "pk_d_p50": float(np.percentile(pd, 50)), "pk_d_max": float(pd.max())}
            st = self.car[side].stats                                   # the slide's own account (empty for the fill)
            pinfo.update({f"pk_{k}": float(st[k]) for k in ("iters", "step", "rim", "flip") if k in st})
        Y = Vp[md.first].copy()
        Y[ids] = X
        g = md.girth(sd, Y)
        info = {"d_pub_p50": float(np.percentile(d, 50)), "d_pub_p95": float(np.percentile(d, 95)), "d_pub_max": float(d.max()),
                "edge_min": emin, "edge_max": emax, "edge_raw_max": eraw, "edge_car_max": ecar, **pinfo,
                "vol": md.volume(sd, Y) / sd["vol0"],
                **{f"girth_{k}": float(g[k] / self.girth0[side][k]) for k in ("mid_deltoid", "insertion")}}
        return X, info


def fmt(i):
    return (f"d_pub {i['d_pub_p50']:.1f}/{i['d_pub_p95']:.1f}/{i['d_pub_max']:.1f} mm  edge {i['edge_min']:.2f}..{i['edge_max']:.2f}"
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
        X, info = h.target(z["G"][i], s)
        MC, MR, _ = h.carried(z["G"][i], s)
        inp = np.zeros(len(ids), bool)
        if car.pocket is not None:
            inp[car.pocket.p] = True
        rr = edge_ratio(MR, md.V0[ids], ei, ej)[2]
        torn = rr > cfg["torn"]
        out = torn & ~(inp[ei] & inp[ej])                              # the rule must cover every torn edge, both ends
        line(f"T5 {nm}", info["edge_car_max"] <= 3 and not out.any() and np.isfinite(X).all(),
             f"edge max carried alone {info['edge_raw_max']:.2f} -> filled {info['edge_car_max']:.2f}; torn edges (over"
             f" {cfg['torn']:g}) {int(torn.sum())}, outside the pocket {int(out.sum())} | {fmt(info)}")
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
    X, infos = [], []
    for i in sel:
        x, info = h.target(z["G"][i], str(z["side"][i]))
        X.append(x)
        infos.append(info)
        if poses:
            print(f"{names[i]:28s} {fmt(info)}")
    cfg = h.cfg
    out = h.OUT / (cfg["dev_out"] if poses else cfg["out"])
    params = {**{k: v for k, v in cfg.items()}, "method": "carried_target", "posed": h.order,
              "not_ok": {s: int((~h.car[s].ok).sum()) for s in "lr"}}
    pocket = {}
    for s in "lr":                       # local indices into the side's region points (md.S[s]["ids"] order)
        c = h.car[s]
        pocket[f"pocket_{s}"] = np.zeros(0, np.int64) if c.pocket is None else c.pocket.p
        pocket[f"bridge_{s}"] = c.bridge
    np.savez_compressed(out, X=np.array(X), name=z["name"][sel], side=z["side"][sel], kind=z["kind"][sel],
                        info=json.dumps(infos), params=json.dumps(params), **pocket)
    table([names[i] for i in sel], [str(z["kind"][i]) for i in sel], infos)
    print(f"wrote {out}  X {np.array(X).shape}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=["test", "target"])
    ap.add_argument("--poses", default="", help="comma-separated pose names: a subset, written to the dev file")
    a = ap.parse_args()
    h = Her()
    if a.cmd == "test":
        sys.exit(0 if cmd_test(h) else 1)
    cmd_target(h, [p for p in a.poses.split(",") if p])


if __name__ == "__main__":
    main()
