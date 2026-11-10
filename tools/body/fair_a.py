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
           "shrink": None}


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
        self.tag = hashlib.sha1(np.ascontiguousarray(V0).tobytes() + np.ascontiguousarray(T).tobytes()
                                + json.dumps(prm, sort_keys=True).encode()).hexdigest()[:16]

    # ------------------------------------------------------------------------------------------------ measures --
    def dihedral(self, X):
        """[inner edges] the fold in degrees (+ a valley, as fold_probe.dihedral), welded points X [n, 3]."""
        T = self.T
        fn = _unit(np.cross(X[T[:, 1]] - X[T[:, 0]], X[T[:, 2]] - X[T[:, 0]]))
        ang = np.degrees(np.arccos(np.clip((fn[self._ta] * fn[self._tb]).sum(1), -1, 1)))
        return ang * np.sign((fn[self._ta] * (X[self._ob] - X[self._oa])).sum(1))

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

        def poisson(R, Fe=None):
            G = R if Fe is None else Fe
            v = np.einsum("eij,ej->ei", 0.5 * (G[Eu[:, 0]] + G[Eu[:, 1]]), d0)
            if blend:                                           # the posed edges off the crumple
                v = ce * v + (1 - ce) * Xd
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

    def fair(self, V, where=None):
        """(V', info). V [nraw, 3] posed; where [nraw] bool (None: everywhere) limits the seeds. No seed: V itself."""
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
        info = {"seed_edges": int(eb.sum()), "seed_flips": int(fl.sum()), "rounds": 0}
        if not eb.any() and not fl.any():
            return V, info
        seed = self._seed_mask(eb, fl)
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

    def cached(self, V, where=None, folder=None):
        """fair(V, where), the patch kept in folder / <key>.npz (key: the posed bytes, where, the mesh and params)."""
        V = np.asarray(V, float)
        if folder is None:
            return self.fair(V, where)
        h = hashlib.sha1(np.ascontiguousarray(V).tobytes())
        h.update(b"-" if where is None else np.packbits(np.asarray(where, bool)).tobytes())
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
        out, info = self.fair(V, where)
        raw = info.get("raw", np.zeros(0, np.int64))
        f.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(f, raw=np.asarray(raw, np.int32), X=out[raw], info=json.dumps({k: v for k, v in info.items() if k != "raw"}))
        return out, info


def her_hook(h, rg, Va):
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
    out, info = F.cached(Va, used, HERE / "out" / "fair_a")
    h._fair_info = {**getattr(h, "_fair_info", {}), rg.name: info}
    return out


def ref_hook(h, Va):
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
    out, info = F.cached(Va, used, HERE / "out" / "fair_a")
    h._fair_info = {**getattr(h, "_fair_info", {}), "pose_ref": info}
    return out
