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
        self.P = V0[first[used]]
        Wn = sp.csr_matrix((np.repeat(area[sel], 3), (self.tri.ravel(), np.repeat(np.arange(len(sel)), 3))), (len(used), len(sel)))
        self.nv = ct._unit(Wn @ E[sel][:, :, 2])
        self.uv, self.flipped = lscm(self.P, self.tri)
        k = self.tri[:, [0, 1, 1, 2, 2, 0]].reshape(-1, 2)
        self.scale = np.linalg.norm(self.uv[k[:, 0]] - self.uv[k[:, 1]], axis=1) / np.linalg.norm(self.P[k[:, 0]] - self.P[k[:, 1]], axis=1)

    def uv_of(self, face, bary):
        return np.einsum("nk,nkj->nj", bary, self.uv[self.tri[self.inv[face]]])

    def lift(self, q, chunk=1500):
        a, b, c = (self.uv[self.tri[:, i]] for i in range(3))
        v0, v1 = b - a, c - a
        den = v0[:, 0] * v1[:, 1] - v0[:, 1] * v1[:, 0]
        S, N, sc = [], [], []
        for s in range(0, len(q), chunk):
            d = q[s:s + chunk, None, :] - a[None]
            l1 = (d[..., 0] * v1[:, 1] - d[..., 1] * v1[:, 0]) / den
            l2 = (v0[:, 0] * d[..., 1] - v0[:, 1] * d[..., 0]) / den
            B = np.stack([1 - l1 - l2, l1, l2], 2)
            score = np.where(den > 0, B.min(2), -np.inf)
            t = score.argmax(1)
            bt = np.clip(B[np.arange(len(t)), t], 0, 1)
            bt /= bt.sum(1, keepdims=True)
            S.append(np.einsum("nk,nkj->nj", bt, self.P[self.tri[t]]))
            N.append(ct._unit(np.einsum("nk,nkj->nj", bt, self.nv[self.tri[t]])))
            sc.append(score.max(1))
        return np.concatenate(S), np.concatenate(N), np.concatenate(sc)

    def length(self, qa, qb, k=12):
        s = np.linspace(0, 1, k + 1)[None, :, None]
        S = self.lift((qa[:, None] + (qb - qa)[:, None] * s).reshape(-1, 2))[0].reshape(len(qa), k + 1, 3)
        return np.linalg.norm(np.diff(S, axis=1), axis=2).sum(1)

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

    def side(self, q):
        r = (q - self.c) @ self.ax.T
        return r[:, 1] - self._d(r[:, 0])

    def project(self, q):
        return self.Q[self._tree.query(q)[1]]


def relay(P0, edges, tris, band, bridge, face, bary, ref_V0, ref_T, reach=0.03, kappa=1.2, deg=3, ext=0.01, part=0.9,
          rounds=4, sweeps=40):
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
            "scale": np.percentile(unf.scale, [1, 50, 99]), "rounds": rnd + 1, "bridging": int(isb.sum())}


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
    "out": "strip_rest.npz",
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
                     self.Ab.T, c["reach"], c["kappa"], c["deg"], c["ext"], c["part"])

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


def cmd_sheet(hs):
    import region_shape as rs
    h, md, bd, cfg = hs.h, hs.md, hs.bd, hs.cfg
    fr, pn = bd.frame, cfg["panel"]
    lat, up, front = np.asarray(fr.lat), np.asarray(fr.up), np.asarray(fr.front)
    z = np.load(rt.OUT / "poses.npz")
    k = [str(x) for x in z["name"]].index(cfg["sheet_pose"])
    s, G = str(z["side"][k]), z["G"][k]
    sg = 1 if s == "l" else -1
    c0 = 0.5 * (bd.G0[bd.p.index["upperarm_l"]][:3, 3] + bd.G0[bd.p.index["upperarm_r"]][:3, 3]) - cfg["rest_drop"] * up
    vr = rs.chest_view(c0, np.eye(3), sg * lat, up, front, cfg["views"]["front34"], cfg["rest_half"], pn / (2 * cfg["rest_half"]))
    Vp = rt.published(bd, G)
    Xf, _ = h.target(G, s, Vp)
    Va, Ga = h.pose_ref(G)
    ja, ra = h.anchor[s]
    M = ct.anchor_align(G[ja], bd.p.rest[ja], hs.Ab.G0[ra], Ga[ra])
    b = md.blend(G, s)[:, None]
    X1 = b * (hs.car1[s].carry(Va) @ M[:3, :3].T + M[:3, 3]) + (1 - b) * Vp[hs.pts[s]]
    Vf, V1 = hs.whole(Vp, {s: Xf}), hs.whole(Vp, {s: X1})
    Rc = rs.turn(G, bd.p.rest, ja)
    vo = rs.chest_view(G[bd.p.index[f"upperarm_{s}"]][:3, 3], Rc, sg * lat, up, front, cfg["views"]["front34"], rs.SHEET["half"], pn / (2 * rs.SHEET["half"]))
    vu = rs.chest_view(X1[hs.loc[s]].mean(0), Rc, sg * lat, up, front, cfg["views"]["under"], cfg["pit_half"], pn / (2 * cfg["pit_half"]))
    nb = len(hs.loc[s])
    rows = [[rs.clay_rgb(bd.V0, bd.T, vr), rs.clay_rgb(hs.V1, bd.T, vr)], [rs.clay_rgb(Vf, bd.T, vo), rs.clay_rgb(V1, bd.T, vo)],
            [rs.clay_rgb(Vf, bd.T, vu), rs.clay_rgb(V1, bd.T, vu)]]
    labels = [["REST, front three-quarter: B today", f"REST, same camera: B with the armpit strip re-laid ({nb} points a side, inside the fold)"],
              [f"arm overhead ({cfg['sheet_pose']}), front three-quarter: today's target (the fill spans the hollow)", "the target on B with the strip change (the band lies in A's hollow)"],
              ["the same pose from under the arm: today's target", "from under the arm: the target on B with the strip change"]]
    out = rt.OUT / "sheets" / "strip_owner.png"
    rs.sheet(rows, labels, pn).save(out)
    subprocess.run([sys.executable, str(HERE.parent / "half.py"), str(out)], check=True)
    print(f"wrote {out}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=["build", "target", "sheet"])
    ap.add_argument("--snap", action="store_true", help="import carried_target from out/shoulder/snap (a frozen copy)")
    ap.add_argument("--rows", type=int, default=HER["rows"])
    ap.add_argument("--poses", default="", help="comma-separated pose names, or 'named' (the config's list); none: all of poses.npz")
    a = ap.parse_args()
    print(f"carried_target: {ct.__file__}")
    hs = HerStrip()
    if a.cmd == "build":
        return cmd_build(hs, a.rows)
    hs.load()
    if a.cmd == "target":
        return cmd_target(hs, HER["named"] if a.poses == "named" else [p for p in a.poses.split(",") if p])
    cmd_sheet(hs)


if __name__ == "__main__":
    main()
