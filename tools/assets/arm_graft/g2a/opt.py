# Skin-weight optimisation at the arm root: ARAP strain over a pose set (Gauss-Newton, numeric split Jacobian).
# Per vertex in the zone: s = spine_03 share and x = upperarm/(upperarm+clavicle) of the three's total (others fixed).
import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import lsqr
from g2lib import glb, split_full
import meas


def gmap(REF, nd):
    hk, m, dist = REF
    g = -np.ones(nd, int); best = np.full(nd, 1e9)
    for k, mm, dd in zip(hk, m, dist):
        if dd < best[mm]:
            best[mm] = dd; g[mm] = k
    return g


class Opt:
    def __init__(self, b0, d, REF, Pnew, side, VG=None, poses=None, zone=None):
        self.b = b0; self.d = d; self.s = side
        self.names = d["names"]; nm = self.names
        self.iS, self.iC, self.iU = nm.index("spine_03"), nm.index("clavicle_" + side), nm.index("upperarm_" + side)
        self.VG = (d["VG"] if VG is None else VG).copy()
        self.X = glb(Pnew)
        self.g = gmap(REF, len(Pnew))
        nJ = len(b0.sk.names)
        self.Fg = np.zeros((len(Pnew), nJ)); ok = self.g >= 0
        r = np.nonzero(ok)[0][:, None].repeat(4, 1)
        np.add.at(self.Fg, (r, b0.J[self.g[ok]]), b0.W[self.g[ok]])
        bad = ~ok | (np.linalg.norm(glb(d["P"]) - np.where(ok[:, None], b0.P[np.maximum(self.g, 0)], 1e3), axis=1) > 2e-3)
        if bad.any():
            self.Fg[bad] = split_full(b0, self.VG[bad], d["names"], self.X[bad])
        print("unmapped dump verts given their own split:", int(bad.sum()))
        self.var = zone  # variable dump verts (bool)
        E = d["E"]
        self.act = self.var.copy()
        for _ in range(2):
            nb = np.zeros_like(self.act); nb[E[self.act[E[:, 0]], 1]] = True; nb[E[self.act[E[:, 1]], 0]] = True; self.act |= nb
        self.ai = np.nonzero(self.act)[0]; self.loc = -np.ones(len(Pnew), int); self.loc[self.ai] = np.arange(len(self.ai))
        em = self.act[E[:, 0]] & self.act[E[:, 1]] & (self.var[E[:, 0]] | self.var[E[:, 1]])
        self.E = self.loc[E[em]]
        self.vi = np.nonzero(self.var[self.ai])[0]          # local indices of the variables
        self.col = -np.ones(len(self.ai), int); self.col[self.vi] = np.arange(len(self.vi))
        self.F0old = split_full(b0, self.VG[self.ai], nm, self.X[self.ai])
        self.Fbase = self.Fg[self.ai]
        self.poses = poses   # list of (S [J,4,4], weight)
        V = self.VG[self.ai]
        tot = V[:, self.iS] + V[:, self.iC] + V[:, self.iU]
        self.tot = tot
        self.th = np.c_[np.where(tot > 1e-9, V[:, self.iS] / np.maximum(tot, 1e-9), 0),
                        np.where(V[:, self.iC] + V[:, self.iU] > 1e-9, V[:, self.iU] / np.maximum(V[:, self.iC] + V[:, self.iU], 1e-9), 0)]
        self.th0 = self.th.copy()

    def vg(self, th):
        V = self.VG[self.ai].copy(); t = self.tot
        V[:, self.iS] = t * th[:, 0]; V[:, self.iC] = t * (1 - th[:, 0]) * (1 - th[:, 1]); V[:, self.iU] = t * (1 - th[:, 0]) * th[:, 1]
        return V

    def F(self, th):
        Fn = split_full(self.b, self.vg(th), self.names, self.X[self.ai])
        return np.maximum(self.Fbase + Fn - self.F0old, 0)

    def posed(self, F, S):
        M = F @ S.reshape(len(S), 16)          # [n, 16]
        M = M.reshape(-1, 4, 4)
        Xh = np.c_[self.X[self.ai], np.ones(len(self.ai))]
        return np.einsum("nij,nj->ni", M[:, :3, :], Xh)

    def rots(self, P):
        X = self.X[self.ai]; E = self.E
        Cv = np.zeros((len(X), 3, 3))
        ex = X[E[:, 0]] - X[E[:, 1]]; ep = P[E[:, 0]] - P[E[:, 1]]
        o = np.einsum("ni,nj->nij", ex, ep)
        np.add.at(Cv, E[:, 0], o); np.add.at(Cv, E[:, 1], o)
        U, _, Vt = np.linalg.svd(Cv + np.eye(3) * 1e-12)
        R = np.einsum("nji,nkj->nik", Vt, U)
        dt = np.linalg.det(R); Vt2 = Vt.copy(); Vt2[dt < 0, 2] *= -1
        R = np.einsum("nji,nkj->nik", Vt2, U)
        return R

    def energy(self, th):
        F = self.F(th); X = self.X[self.ai]; E = self.E; tot = 0
        L = np.linalg.norm(X[E[:, 0]] - X[E[:, 1]], axis=1)
        for S, w in self.poses:
            P = self.posed(F, S); R = self.rots(P)
            for a, c in ((0, 1), (1, 0)):
                r = (P[E[:, a]] - P[E[:, c]]) - np.einsum("nij,nj->ni", R[E[:, a]], X[E[:, a]] - X[E[:, c]])
                tot += w * ((r / L[:, None]) ** 2).sum()
        return tot

    def step(self, lam_s=0.3, lam_p=0.01, eps=1e-3, damp=1.0):
        th = self.th; F = self.F(th); X = self.X[self.ai]; E = self.E; nv = len(self.vi)
        dF = []
        for k in range(2):
            t2 = th.copy(); t2[self.vi, k] = np.clip(t2[self.vi, k] + eps, 0, 1); d_ = (t2[:, k] - th[:, k])
            dF.append((self.F(t2) - F) / np.where(np.abs(d_) > 1e-12, d_, 1)[:, None])
        L = np.linalg.norm(X[E[:, 0]] - X[E[:, 1]], axis=1)
        rows, cols, vals, rhs = [], [], [], []; r0 = 0; etot = 0
        for S, w in self.poses:
            P = self.posed(F, S); R = self.rots(P)
            dP = [self.posed(dF[k], S) for k in range(2)]   # dp/dtheta_k (affine part drops: sum of dF is ~0)
            sw = np.sqrt(w)
            for a, c in ((0, 1), (1, 0)):
                res = ((P[E[:, a]] - P[E[:, c]]) - np.einsum("nij,nj->ni", R[E[:, a]], X[E[:, a]] - X[E[:, c]])) / L[:, None] * sw
                etot += (res ** 2).sum()
                n = len(E)
                for comp in range(3):
                    ridx = r0 + np.arange(n) * 3 + comp
                    for end, sg in ((E[:, a], 1.0), (E[:, c], -1.0)):
                        cc = self.col[end]; ok = cc >= 0
                        for k in range(2):
                            rows.append(ridx[ok]); cols.append(cc[ok] * 2 + k); vals.append(sg * dP[k][end[ok], comp] / L[ok] * sw)
                rhs.append(-res.ravel()); r0 += 3 * n
        # smoothness between variables, and a weak prior
        ev = E[(self.col[E[:, 0]] >= 0) & (self.col[E[:, 1]] >= 0)]
        for k in range(2):
            ridx = r0 + np.arange(len(ev))
            rows += [ridx, ridx]; cols += [self.col[ev[:, 0]] * 2 + k, self.col[ev[:, 1]] * 2 + k]
            vals += [np.full(len(ev), np.sqrt(lam_s)), np.full(len(ev), -np.sqrt(lam_s))]
            rhs.append(-np.sqrt(lam_s) * (th[ev[:, 0], k] - th[ev[:, 1], k])); r0 += len(ev)
            ridx = r0 + np.arange(nv)
            rows.append(ridx); cols.append(np.arange(nv) * 2 + k); vals.append(np.full(nv, np.sqrt(lam_p)))
            rhs.append(-np.sqrt(lam_p) * (th[self.vi, k] - self.th0[self.vi, k])); r0 += nv
        A = sp.coo_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), shape=(r0, 2 * nv)).tocsr()
        b = np.concatenate(rhs)
        self._A, self._b = A, b
        while True:
            dx = lsqr(A, b, damp=damp, atol=1e-8, btol=1e-8, iter_lim=400)[0].reshape(-1, 2)
            tn = th.copy(); tn[self.vi] = np.clip(th[self.vi] + dx, 0, 1)
            en = self.energy(tn)
            if en < etot or damp > 1e4:
                break
            damp *= 4
        self.th = tn if en < etot else th
        self.damp = damp
        return etot, en, np.abs(dx).max(), damp

    def result(self):
        V = self.VG.copy(); V[self.ai] = self.vg(self.th); return V


def pose_set(b, side, spec):
    """spec: list of (clip, frame, authored_arm, weight). Mirrored when authored for the other arm."""
    out = []
    for clip, f, arm, w in spec:
        G = b.globals(b._cl[clip] if clip in b._cl else b.clip(clip), f)
        if arm is not None and arm != side:
            G = meas.mirrorG(b, G)
        out.append((G @ b.rest_inv, w))
    return out
