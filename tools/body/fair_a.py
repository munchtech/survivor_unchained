"""fair_a: fair a skinned mesh's POSED surface on its own topology, per pose, at the source (body_facts/fair_a.md).

Linear blend skinning crumples skin where a joint compresses it (her front armpit and deltoid cap with the arm raised or
behind: valleys next to ridges, triangles turned). This finds the crumple on the mesh itself and replaces it with the
REST shape's own smooth curvature bent into the pose; everything else stays bit for bit.

General: the inputs are the rest vertices V0 [n, 3], the triangles T [m, 3] and a posed copy V [n, 3] (any skinned mesh,
creatures too). No vertex ids, no rig. Vertices doubled along seams are welded by rest position.

  1. Seeds: an inner edge whose fold |posed| > fold_deg AND |posed| - |rest| > beyond_deg, or a triangle FLIPPED (its
     posed normal against its rest normal turned by the smoothed rotation field; `flips`). `where` [n] bool limits the
     seeds (e.g. the vertices a carry reads). No seed: V is returned as it is (the same array, bit for bit).
  2. Patch: the seeds grown by `rings` rings. Its outer `soft` rings are pulled softly to the posed points (alpha, a
     smoothstep up to `alpha` at the outer ring); the ring just outside is held hard (the posed points).
  3. Untangle (the start that ARAP alone does not find): the patch's rotations are the HARMONIC fill of the posed
     surface's own rotations on the hard ring (9 entries, Dirichlet, then the polar), fixed, not refitted. The patch is the
     Poisson solve of the rest edges turned by them: argmin sum w_ij |x_i - x_j - (R_i + R_j)/2 (p_i - p_j)|^2
     + sum alpha_i |x_i - X_i|^2 (w the clamped rest cotangent weights). A crumple an edge or two wide cannot survive a
     smooth rotation field; the rest shape's curvature is what fills it.
  4. Volume: the area-weighted mean offset along the smooth normals (R n0) from the posed points is held at 0 (a
     Lagrange step), so the faired surface passes through the middle of the crumple, not under or over it.
  5. Optional ARAP (`iters`): rotations refitted to the result and smoothed `rot_smooth` passes (never to the crumple),
     a step kept only if the flipped count and the beyond-rest fold count in the patch do not rise (the flip barrier).
  6. Rounds: what is still bad in the patch or on its ring is added to the seeds and the patch solved again (`rounds`).

fair(V) -> (V', info). Fair.cached(V, where, folder) keys a file by the posed bytes, the params and the mesh, and stores
only the patch's vertices (bit-exact on reload). `python tools/body/fair_a.py check` runs the self tests.
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import factorized

HERE = Path(__file__).resolve().parent
DEFAULT = {"fold_deg": 45.0, "beyond_deg": 20.0, "rings": 4, "soft": 2, "alpha": 0.1, "flip_passes": 4, "volume": True,
           "iters": 0, "rot_smooth": 4, "rounds": 3, "grow": 2, "rot": "smooth", "rot_passes": 8, "alpha_core": 0.0, "weld": 1e-6, "wclamp": [0.02, 20.0],
           # the crumple (attempt 4): close = the seeds take every bad element on the patch or its ring before a solve
           # (to closure); edges "blend" = posed edges off the crumple, the rest edges turned (F, the filled gradients, with
           # stretch) inside it; c_core / c_soft: the crumple = seeds + c_core rows, smoothstep to 0 over c_soft more;
           # alpha_mid: the pull off the crumple (x median weight); rot "fill": the gradients harmonic-filled on the crumple
           "close": False, "edges": "rest", "c_core": 1, "c_soft": 2, "alpha_mid": None, "stretch": True,
           # dilate: a round's leftovers enter the seeds grown by `grow` rows (so a crumple the core keeps widens there);
           # best: the round kept is the one with the fewest (flipped, beyond-rest folds) on the patch and its ring
           "dilate": False, "best": False,
           # shrink (attempt 5): with rot "fill", stretch false and edges "blend", the crumple's rest edges turned are also
           # scaled by `shrink` (< 1), so its Poisson solve is in TENSION: a membrane pulled taut between its ring does not
           # buckle, where full-length rest edges pushed into the compressed hollow fold (the core's leftover >45s and flips)
           "shrink": None,
           # cap (attempt 7): the cap-band curvature rule (CAP's keys; None = off, bit for bit). Needs the caller's `rigid`
           # (fair(..., rigid=(R, w)): R [nraw, 3, 3] a bone's rigid turn rest -> pose, w [nraw] that bone chain's skin share)
           "cap": None}
# the cap rule's keys: band lo < w < hi; fires where the rest is a cap (smoothed mean curvature > h_min, 1/m) and the posed
# surface is clearly flatter (H < flat x H0) or creased (rim: H < -h_min); the fired set grown `grow` rows is the cap
# (share 1), a smoothstep to 0 over `soft` more. There the target edges are the rest edges turned by polar((1 - turn)
# R_posed + turn R_rigid) (R_posed: the posed rotations after `passes` averaging passes): the rest curvature carried
# rigidly by the bone; the posed points are only soft targets (pull `alpha` x median weight) and the cap's volume is held.
# "bone" / "chain": the caller's (her_hook: the rigid bone and the chain whose skin share is w), unused here.
CAP = {"lo": 0.05, "hi": 0.95, "h_min": 8.0, "flat": 0.5, "rim": True, "rings": 2, "grow": 2, "soft": 3, "turn": 1.0,
       "alpha": 0.05, "passes": 4, "bone": None, "chain": []}


def _unit(v):
    return v / np.maximum(np.linalg.norm(v, axis=-1, keepdims=True), 1e-30)


def polar(F):
    """The nearest rotation of each 3x3 in F [..., 3, 3] (det +1)."""
    U, _, Vt = np.linalg.svd(F)
    neg = np.linalg.det(U @ Vt) < 0
    U = U * np.where(neg, -1.0, 1.0)[..., None, None] ** np.array([0, 0, 1])
    return U @ Vt


def frames(V, T):
    """Per triangle [m, 3, 3]: columns e1, e2, unit normal; and the area [m]."""
    a = V[T[:, 0]]
    e1, e2 = V[T[:, 1]] - a, V[T[:, 2]] - a
    n = np.cross(e1, e2)
    ln = np.linalg.norm(n, axis=1)
    return np.stack([e1, e2, n / np.maximum(ln, 1e-30)[:, None]], 2), 0.5 * ln


def rows_from(adj, seed, cap=1 << 30):
    """[n] the count of edges to the nearest seed vertex (0 on the seed, cap where none is reached)."""
    d = np.where(seed, 0, cap)
    front, k = seed.copy(), 0
    while front.any():
        k += 1
        front = (adj @ front > 0) & (d == cap)
        d[front] = k
    return d


class Fair:
    """One mesh's rest data (welded) and the fair of its posed copies. params: DEFAULT's keys (missing ones default)."""

    def __init__(self, V0, T, **params):
        bad = set(params) - set(DEFAULT)
        if bad:
            raise ValueError(f"fair_a: unknown params {sorted(bad)}")
        self.prm = prm = {**DEFAULT, **params}
        if prm["cap"] is not None:
            bad = set(prm["cap"]) - set(CAP)
            if bad:
                raise ValueError(f"fair_a: unknown cap params {sorted(bad)}")
            prm["cap"] = {**CAP, **prm["cap"]}
        V0, T = np.asarray(V0, float), np.asarray(T, np.int64)
        _, first, grp = np.unique(np.round(V0 / prm["weld"]).astype(np.int64), axis=0, return_index=True, return_inverse=True)
        self.grp, self.first, self.nraw = np.asarray(grp).ravel(), first, len(V0)
        Tw = self.grp[T]
        ok = (Tw[:, 0] != Tw[:, 1]) & (Tw[:, 1] != Tw[:, 2]) & (Tw[:, 0] != Tw[:, 2])
        self.T, self.n = Tw[ok], len(first)
        self.P0 = P0 = V0[first]
        T = self.T
        # edges: unique; an inner edge (exactly two triangles) gets its pair for the fold
        e = np.sort(np.concatenate([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]), 1)
        opp = np.concatenate([T[:, 2], T[:, 0], T[:, 1]])
        tri = np.tile(np.arange(len(T)), 3)
        key = e[:, 0] * (self.n + 1) + e[:, 1]
        o = np.argsort(key, kind="stable")
        ks = key[o]
        start = np.r_[True, ks[1:] != ks[:-1]]
        cnt = np.diff(np.r_[np.nonzero(start)[0], len(ks)])
        self.E = e[o][start]                                    # every unique edge
        s0 = np.nonzero(start)[0]
        two = cnt == 2
        self.ie = np.nonzero(two)[0]                            # inner edges (index into E)
        a, b = o[s0[two]], o[s0[two] + 1]
        self._ta, self._tb, self._oa, self._ob = tri[a], tri[b], opp[a], opp[b]
        self.d_rest = np.abs(self.dihedral(P0))
        # adjacency and the clamped rest cotangent weights per unique edge
        E = self.E
        A = sp.coo_matrix((np.ones(len(E)), (E[:, 0], E[:, 1])), (self.n, self.n))
        self.adj = (A + A.T).tocsr()
        cot = np.zeros(len(E))
        idx = {int(k): i for i, k in enumerate(E[:, 0] * (self.n + 1) + E[:, 1])}
        for c in range(3):                                      # the angle at corner c faces edge (c+1, c+2)
            i, j, k = T[:, c], T[:, (c + 1) % 3], T[:, (c + 2) % 3]
            u, v = P0[j] - P0[i], P0[k] - P0[i]
            ct = (u * v).sum(1) / np.maximum(np.linalg.norm(np.cross(u, v), axis=1), 1e-30)
            ek = np.sort(np.stack([j, k], 1), 1)
            ids = np.array([idx[int(x)] for x in ek[:, 0] * (self.n + 1) + ek[:, 1]])
            np.add.at(cot, ids, 0.5 * ct)
        med = np.median(cot[cot > 0])
        self.w = np.clip(cot, prm["wclamp"][0] * med, prm["wclamp"][1] * med)
        self.E0, self.area = frames(P0, T)
        self._E0inv = np.linalg.inv(self.E0)
        self.varea = np.bincount(T.ravel(), np.repeat(self.area / 3, 3), self.n)
        # vertex <- incident triangles, area-weighted (the rotations' sums)
        self._VT = sp.csr_matrix((np.repeat(self.area, 3), (T.ravel(), np.repeat(np.arange(len(T)), 3))), (self.n, len(T)))
        deg = np.asarray(self.adj.sum(1)).ravel()
        self._avg = sp.diags(1.0 / np.maximum(deg, 1)) @ self.adj
        self.n0 = _unit(self._VT @ self.E0[:, :, 2])            # rest vertex normals
        self.tag = hashlib.sha1(np.ascontiguousarray(V0).tobytes() + np.ascontiguousarray(T).tobytes()   # (cap None: the old key)
                                + json.dumps({k: v for k, v in prm.items() if not (k == "cap" and v is None)}, sort_keys=True).encode()).hexdigest()[:16]
        self._L, self._cap = None, None

    # ------------------------------------------------------------------------------------------------ measures --
    def dihedral(self, X):
        """[inner edges] the fold in degrees (+ a valley, as fold_probe.dihedral), welded points X [n, 3]."""
        T = self.T
        fn = _unit(np.cross(X[T[:, 1]] - X[T[:, 0]], X[T[:, 2]] - X[T[:, 0]]))
        ang = np.degrees(np.arccos(np.clip((fn[self._ta] * fn[self._tb]).sum(1), -1, 1)))
        return ang * np.sign((fn[self._ta] * (X[self._ob] - X[self._oa])).sum(1))

    def curv(self, X, rings=2):
        """[n] the mean curvature (1/m; + convex, against the outward normals) by the clamped cotangent Laplacian, area-
        weighted over `rings` (I + adjacency) passes: the cap rule's measure. Rotation free: a rest cap carried rigidly by
        any bone keeps curv(P0)."""
        if self._L is None:
            E, w = self.E, self.w
            Wm = sp.coo_matrix((np.r_[w, w], (np.r_[E[:, 0], E[:, 1]], np.r_[E[:, 1], E[:, 0]])), (self.n, self.n)).tocsr()
            self._L = (sp.diags(np.asarray(Wm.sum(1)).ravel()) - Wm).tocsr()
            self._inc = sp.csr_matrix((np.ones(3 * len(self.T)), (self.T.ravel(), np.repeat(np.arange(len(self.T)), 3))), (self.n, len(self.T)))
        T = self.T
        fn = np.cross(X[T[:, 1]] - X[T[:, 0]], X[T[:, 2]] - X[T[:, 0]])
        a = ((self._L @ X) * _unit(self._inc @ fn)).sum(1)
        b = self._inc @ (np.linalg.norm(fn, axis=1) / 6.0)
        for _ in range(int(rings)):
            a, b = a + self.adj @ a, b + self.adj @ b
        return a / np.maximum(2.0 * b, 1e-30)

    def cap_share(self, X, rigid, wh=None):
        """The cap rule (CAP): ([n] the cap share, 1 on the fired set grown `grow` rows, a smoothstep to 0 over `soft`; or
        None when nothing fires, [n] the fired set). rigid = (R, w) per raw vertex; wh [n] limits the band."""
        cp = self.prm["cap"]
        w = np.asarray(rigid[1], float)[self.first]
        band = (w > cp["lo"]) & (w < cp["hi"])
        if wh is not None:
            band &= wh
        if getattr(self, "_h0", None) is None or self._h0[0] != cp["rings"]:
            self._h0 = (cp["rings"], self.curv(self.P0, cp["rings"]))
        h0, hx = self._h0[1], self.curv(X, cp["rings"])
        fire = band & (h0 > cp["h_min"]) & ((hx < cp["flat"] * h0) | (bool(cp["rim"]) & (hx < -cp["h_min"])))
        if not fire.any():
            return None, fire
        t = np.clip((rows_from(self.adj, fire) - cp["grow"]) / max(cp["soft"], 1e-9), 0.0, 1.0)
        return 1.0 - t * t * (3 - 2 * t), fire

    def rotations(self, X, passes=0, fixed=None):
        """[n, 3, 3] per welded vertex: the polar of the area-weighted triangle deformation gradients (rest -> X), after
        `passes` Jacobi averaging passes (vertices in `fixed` held)."""
        Ex, _ = frames(X, self.T)
        F = (self._VT @ (Ex @ self._E0inv).reshape(-1, 9))
        for _ in range(int(passes)):
            Fn = self._avg @ F
            if fixed is not None:
                Fn[fixed] = F[fixed]
            F = Fn
        return polar(F.reshape(-1, 3, 3))

    def flips(self, X, R=None):
        """[triangles] bool: the posed normal against the rest normal turned by the smoothed rotations (R per vertex:
        given, or rotations(X, flip_passes))."""
        if R is None:
            R = self.rotations(X, self.prm["flip_passes"])
        T = self.T
        Rt = polar(R[T].sum(1))
        ref = np.einsum("tij,tj->ti", Rt, self.E0[:, :, 2])
        fn = np.cross(X[T[:, 1]] - X[T[:, 0]], X[T[:, 2]] - X[T[:, 0]])
        return (fn * ref).sum(1) < 0

    def bad(self, X, R=None):
        """(edge seeds [inner edges] bool, flipped [triangles] bool, fold [inner edges] deg)."""
        d = self.dihedral(X)
        p = self.prm
        return (np.abs(d) > p["fold_deg"]) & (np.abs(d) - self.d_rest > p["beyond_deg"]), self.flips(X, R), d

    def _seed_mask(self, eb, fl):
        s = np.zeros(self.n, bool)
        s[self.E[self.ie[eb]].ravel()] = True
        s[self.T[fl].ravel()] = True
        return s

    # ---------------------------------------------------------------------------------------------- the solve --
    def _solve(self, X, patch, ring):
        """The patch's points [patch] from the posed X [n, 3] (ring held): steps 3-5 of the module docstring."""
        prm, P0, E, w = self.prm, self.P0, self.E, self.w
        p = np.nonzero(patch)[0]
        loc = -np.ones(self.n, np.int64)
        loc[p] = np.arange(len(p))
        use = patch[E].any(1)
        Eu, wu = E[use], w[use]
        d0 = P0[Eu[:, 0]] - P0[Eu[:, 1]]
        # the Laplacian of the patch (rows p), and its coupling to the held points
        Wm = sp.coo_matrix((np.r_[wu, wu], (np.r_[Eu[:, 0], Eu[:, 1]], np.r_[Eu[:, 1], Eu[:, 0]])), (self.n, self.n)).tocsr()
        deg = np.asarray(Wm.sum(1)).ravel()
        L = (sp.diags(deg) - Wm).tocsr()
        Lpp, Lpb = L[p][:, p], L[p][:, ~patch]
        hold = np.nonzero(~patch)[0]
        Xb = Lpb @ X[hold]
        # the soft pull: a smoothstep up to alpha over the outer `soft` rings (0 in the core)
        r = self._dist[p].astype(float)
        R0, S = prm["rings"] + self._extra, prm["soft"]
        t = np.clip((r - (R0 - S)) / max(S, 1), 0.0, 1.0) if S > 0 else np.zeros(len(p))
        al = (prm["alpha_core"] + (prm["alpha"] - prm["alpha_core"]) * t * t * (3 - 2 * t)) * np.median(wu)
        c = self._crumple()                                     # [n] 1 on the crumple, 0 off it (edges "blend")
        if prm["alpha_mid"] is not None:                        # off the crumple the patch is pulled to the posed points
            al = np.maximum(al, (prm["alpha_mid"] * (1 - c[p]) + prm["alpha_core"] * c[p]) * np.median(wu))
        if self._cap is not None:                               # the cap: the posed points only soft targets
            kc = self._cap[0][p]
            al = (1 - kc) * al + kc * prm["cap"]["alpha"] * np.median(wu)
        K = (Lpp + sp.diags(al)).tocsc()
        solve = factorized(K)
        cols = lambda Y: np.stack([solve(np.ascontiguousarray(Y[:, c])) for c in range(3)], 1)
        # the harmonic rotation field: the posed surface's own rotations on the held points, filled into the patch
        Rx = self.rotations(X)
        if prm["rot"] == "fill":                                # the gradients: harmonic on the crumple, then smoothed
            Fx = self._grad(X)
            core = patch & (c >= 1.0)
            if core.any():
                Lu = (sp.diags(np.asarray(self.adj.sum(1)).ravel()) - self.adj).tocsr()
                kc, nk = np.nonzero(core)[0], np.nonzero(~core)[0]
                so = factorized(Lu[kc][:, kc].tocsc())
                Fx[kc] = np.stack([so(np.ascontiguousarray(-(Lu[kc][:, nk] @ Fx[nk, j]))) for j in range(9)], 1)
            for _ in range(int(prm["rot_passes"])):
                Fn = self._avg @ Fx
                Fx[p] = Fn[p]
            R = Rx.copy()
            R[p] = polar(Fx[p].reshape(-1, 3, 3))
            Fe = Fx.reshape(-1, 3, 3) if prm["stretch"] else R
            if prm["shrink"] is not None and not prm["stretch"]:  # the crumple's target edges shortened: solved in tension
                Fe = R * float(prm["shrink"])
            return self._finish(X, patch, p, Eu, wu, d0, Xb, al, cols, R, c, Fe)
        if prm["rot"] == "smooth":                              # the posed rotations smoothed in the patch (ring held)
            R = Rx.copy()
            R[p] = self.rotations(X, prm["rot_passes"], fixed=~patch)[p]
            return self._finish(X, patch, p, Eu, wu, d0, Xb, al, cols, R, c)
        Fh = Rx.reshape(-1, 9).copy()
        Lu = (sp.diags(np.asarray(self.adj.sum(1)).ravel()) - self.adj).tocsr()
        Fh[p] = np.stack([factorized(Lu[p][:, p].tocsc())(np.ascontiguousarray(-(Lu[p][:, hold] @ Fh[hold, c])))
                          for c in range(9)], 1)
        R = Rx.copy()
        R[p] = polar(Fh[p].reshape(-1, 3, 3))
        return self._finish(X, patch, p, Eu, wu, d0, Xb, al, cols, R, c)

    def _grad(self, X):
        """[n, 9] per welded vertex: the area-weighted triangle deformation gradients (rest -> X), not polarised."""
        Ex, _ = frames(X, self.T)
        return np.asarray(self._VT @ (Ex @ self._E0inv).reshape(-1, 9))

    def _crumple(self):
        """[n] the crumple's share: 1 within c_core rows of the seeds, a smoothstep to 0 over c_soft more (0 for "rest")."""
        prm = self.prm
        if prm["edges"] != "blend":
            return np.zeros(self.n)
        t = np.clip((self._dist - prm["c_core"]) / max(prm["c_soft"], 1e-9), 0.0, 1.0)
        return 1.0 - t * t * (3 - 2 * t)

    def _finish(self, X, patch, p, Eu, wu, d0, Xb, al, cols, R, c=None, Fe=None):
        prm, E = self.prm, self.E
        blend = prm["edges"] == "blend"
        ce = 0.5 * (c[Eu[:, 0]] + c[Eu[:, 1]])[:, None] if blend else None
        Xd = X[Eu[:, 0]] - X[Eu[:, 1]]
        va = self.varea[p] * (c[p] if blend else 1.0)            # blend: the volume is the crumple's
        if self._cap is not None:                               # the cap: the rest edges turned by the rigid-blend rotations
            kc, Rc = self._cap
            ke = 0.5 * (kc[Eu[:, 0]] + kc[Eu[:, 1]])[:, None]
            vc = np.einsum("eij,ej->ei", 0.5 * (Rc[Eu[:, 0]] + Rc[Eu[:, 1]]), d0)
            va = np.maximum(va, self.varea[p] * kc[p])           # and its volume held

        def poisson(R, Fe=None):
            G = R if Fe is None else Fe
            v = np.einsum("eij,ej->ei", 0.5 * (G[Eu[:, 0]] + G[Eu[:, 1]]), d0)
            if blend:                                           # the posed edges off the crumple
                v = ce * v + (1 - ce) * Xd
            if self._cap is not None:
                v = ke * vc + (1 - ke) * v
            v = wu[:, None] * v
            Bv = np.zeros((self.n, 3))
            np.add.at(Bv, Eu[:, 0], v)
            np.add.at(Bv, Eu[:, 1], -v)
            Y = cols(Bv[p] - Xb + al[:, None] * X[p])
            if prm["volume"] and va.sum() > 0:                  # the mean offset along the smooth normals held at 0
                nrm = _unit(np.einsum("nij,nj->ni", R[p], self.n0[p]))
                a = va
                U = cols(a[:, None] * nrm)
                q = (a * (U * nrm).sum(1)).sum()
                Y = Y - (a * ((Y - X[p]) * nrm).sum(1)).sum() / q * U
            return Y

        Y = poisson(R, Fe)
        info = {"iters": 0}
        if prm["iters"]:
            Z = X.copy()
            Z[p] = Y
            sc = lambda Z: (int(self.flips(Z)[patch[self.T].any(1)].sum()), int(self.bad(Z)[0][patch[E[self.ie]].any(1)].sum()))
            best = sc(Z)
            for it in range(int(prm["iters"])):
                Sk = wu[:, None, None] * (Z[Eu[:, 0]] - Z[Eu[:, 1]])[:, :, None] * d0[:, None, :]
                Sm = np.zeros((self.n, 3, 3))
                np.add.at(Sm, Eu[:, 0], Sk)
                np.add.at(Sm, Eu[:, 1], Sk)
                F = R.reshape(-1, 9).copy()
                F[p] = Sm[p].reshape(-1, 9)
                for _ in range(int(prm["rot_smooth"])):
                    Fn = self._avg @ F
                    F[p] = Fn[p]
                Rn = R.copy()
                Rn[p] = polar(F[p].reshape(-1, 3, 3))
                Zn = Z.copy()
                Zn[p] = poisson(Rn)
                s = sc(Zn)
                if s[0] > best[0] or s[1] > best[1]:            # the flip barrier: a step that turns or folds more is not kept
                    break
                Z, R, best, info["iters"] = Zn, Rn, s, it + 1
            Y = Z[p]
        return Y, info

    def fair(self, V, where=None, extra=None, rigid=None):
        """(V', info). V [nraw, 3] posed; where [nraw] bool (None: everywhere) limits the seeds; extra [nraw] bool (None:
        none): points that are seeds whatever the measures say (a caller's own count, e.g. strip_rest's turned map
        triangles' A points). rigid (R, w): the cap rule's input (CAP; ignored when params "cap" is None). No seed: V itself."""
        V = np.asarray(V, float)
        prm = self.prm
        X = V[self.first]
        eb, fl, d = self.bad(X)
        ebA, flA = eb.copy(), fl.copy()                         # every bad element (the closure's, never limited)
        wh = None
        if where is not None:
            wh = np.zeros(self.n, bool)
            wh[self.grp[np.asarray(where, bool)]] = True
            eb &= wh[self.E[self.ie]].all(1)
            fl &= wh[self.T].all(1)
        ex = np.zeros(self.n, bool)
        if extra is not None:
            ex[self.grp[np.asarray(extra, bool)]] = True
        info = {"seed_edges": int(eb.sum()), "seed_flips": int(fl.sum()), "rounds": 0}
        if extra is not None:
            info["seed_extra"] = int(ex.sum())
        self._cap = None
        if prm["cap"] is not None and rigid is not None:        # the cap rule: its share and the rigid-blend rotations
            kc, fire = self.cap_share(X, rigid, wh)
            info["cap_fire"] = int(fire.sum())
            if kc is not None:
                cp = prm["cap"]
                Rr = np.broadcast_to(np.asarray(rigid[0], float), (self.nraw, 3, 3))[self.first]
                self._cap = (kc, polar((1 - cp["turn"]) * self.rotations(X, cp["passes"]) + cp["turn"] * Rr))
                ex = ex | (kc > 0)
        if not eb.any() and not fl.any() and not ex.any():
            return V, info
        seed = self._seed_mask(eb, fl) | ex
        Xf, self._extra, keep = X.copy(), 0, None
        for rnd in range(int(prm["rounds"])):
            for _ in range(32 if prm["close"] else 0):          # the closure: a bad element on the patch or its ring is a seed
                near = rows_from(self.adj, seed) <= prm["rings"] + self._extra + 1
                add = self._seed_mask(ebA & near[self.E[self.ie]].any(1), flA & near[self.T].any(1)) & ~seed
                if not add.any():
                    break
                seed = seed | add
            self._dist = rows_from(self.adj, seed)
            patch = self._dist <= prm["rings"] + self._extra
            ring = self._dist == prm["rings"] + self._extra + 1
            Y, inf = self._solve(X, patch, ring)
            Xf = X.copy()
            Xf[patch] = Y

            info.update(rounds=rnd + 1, patch=int(patch.sum()), arap_iters=inf["iters"])
            eb2, fl2, _ = self.bad(Xf)
            near = patch | ring
            left = (eb2 & near[self.E[self.ie]].any(1)), (fl2 & near[self.T].any(1))
            if prm["best"]:                                     # the round kept: the fewest flipped, then beyond-rest folds
                sc = (int(left[1].sum()), int(left[0].sum()))
                if keep is None or sc < keep[0]:
                    keep = (sc, Xf, patch, dict(info))
            if not left[0].any() and not left[1].any():
                break
            add = self._seed_mask(*left)
            if prm["dilate"]:
                add = rows_from(self.adj, add) <= prm["grow"]
            seed = seed | add
            if prm["close"]:                                    # the closure re-reads the bad elements of the posed points
                ebA, flA = ebA | eb2, flA | fl2
            self._extra += prm["grow"]
        if keep is not None:
            _, Xf, patch, info = keep
        self.patch = patch
        out = V.copy()
        raw = np.nonzero(patch[self.grp])[0]
        out[raw] = Xf[self.grp[raw]]
        info["raw"] = raw
        return out, info

    def cached(self, V, where=None, folder=None, extra=None, rigid=None):
        """fair(V, where, extra), the patch kept in folder / <key>.npz (key: the posed bytes, where, extra, the mesh and
        params)."""
        V = np.asarray(V, float)
        if self.prm["cap"] is None:
            rigid = None                                        # (the old key, bit for bit)
        if folder is None:
            return self.fair(V, where, extra, rigid)
        h = hashlib.sha1(np.ascontiguousarray(V).tobytes())
        h.update(b"-" if where is None else np.packbits(np.asarray(where, bool)).tobytes())
        if extra is not None:
            h.update(b"x" + np.packbits(np.asarray(extra, bool)).tobytes())
        if rigid is not None:
            h.update(b"r" + np.ascontiguousarray(rigid[0], float).tobytes() + np.ascontiguousarray(rigid[1], float).tobytes())
        f = Path(folder) / f"{self.tag}_{h.hexdigest()[:24]}.npz"
        if f.exists():
            c = np.load(f, allow_pickle=False)
            info = json.loads(str(c["info"]))
            if not len(c["raw"]):
                return V, info
            out = V.copy()
            out[c["raw"]] = c["X"]
            info["raw"] = c["raw"]
            return out, info
        out, info = self.fair(V, where, extra, rigid)
        raw = info.get("raw", np.zeros(0, np.int64))
        f.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(f, raw=np.asarray(raw, np.int32), X=out[raw], info=json.dumps({k: v for k, v in info.items() if k != "raw"}))
        return out, info


def rigid_of(h, Ga, sides):
    """The cap rule's rigid input from HER's "fair_a" params "cap" (bone, chain: names with {s}) and A's posed globals Ga:
    (R [nA, 3, 3] the side's bone turn rest -> pose, w [nA] the side's chain skin share; per A vertex the side whose
    chain carries more). None when the rule is off or Ga is not given."""
    cp = ((h.cfg.get("fair_a") or {}).get("params") or {}).get("cap")
    if not cp or Ga is None:
        return None
    Ab, I = h.Ab, h.Ab.p.index
    n = len(Ab.V0)
    R, w = np.tile(np.eye(3), (n, 1, 1)), np.full(n, -1.0)
    for s in sides:
        b = I[cp["bone"].replace("{s}", s)]
        M = Ga[b] @ np.linalg.inv(Ab.G0[b])
        ws = sum((Ab.W * (Ab.J == I[x.replace("{s}", s)])).sum(1) for x in cp["chain"])
        m = ws > w
        R[m], w[m] = M[:3, :3], ws[m]
    return R, w


def her_hook(h, rg, Va, Ga=None):
    """carried_target.Her.part's hook (config "fair_a" = {"regions": [...], "params": {...}}): the region's A posed surface
    Va faired before any carry, seeds limited to the A vertices its carrier reads; cached in out/fair_a. h.fair_on False,
    or a region not listed: Va as it is."""
    c = h.cfg.get("fair_a")
    names = {x.replace("{s}", s) for x in (c or {}).get("regions", []) for s in "lr"}
    if not c or not getattr(h, "fair_on", True) or rg.name not in names:
        return Va
    F = getattr(h, "_fair_a", None)
    if F is None:
        F = h._fair_a = Fair(h.Ab.V0, h.Ab.T, **c.get("params", {}))
    used = np.zeros(len(Va), bool)
    used[np.concatenate([x.tri.ravel() for x in getattr(rg.carrier, "parts", [rg.carrier])])] = True
    out, info = F.cached(Va, used, HERE / "out" / "fair_a", rigid=rigid_of(h, Ga, [rg.side]))
    h._fair_info = {**getattr(h, "_fair_info", {}), rg.name: info}
    return out


def ref_hook(h, Va, Ga=None):
    """strip_rest's hook on the whole pose's A surface (Her.pose_ref): the same rule as her_hook, seeds limited to the A
    vertices every listed region's carrier reads (both girdles). Key absent or h.fair_on False: Va as it is."""
    c = h.cfg.get("fair_a")
    if not c or not getattr(h, "fair_on", True):
        return Va
    names = [x.replace("{s}", s) for x in c.get("regions", []) for s in "lr"]
    F = getattr(h, "_fair_a", None)
    if F is None:
        F = h._fair_a = Fair(h.Ab.V0, h.Ab.T, **c.get("params", {}))
    used = np.zeros(len(Va), bool)
    for n in names:
        if n in h.regions:
            car = h.regions[n].carrier
            used[np.concatenate([x.tri.ravel() for x in getattr(car, "parts", [car])])] = True
    out, info = F.cached(Va, used, HERE / "out" / "fair_a", rigid=rigid_of(h, Ga, sorted({n[-1] for n in names})))
    h._fair_info = {**getattr(h, "_fair_info", {}), "pose_ref": info}
    return out
