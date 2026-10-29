# G2a edits on the blend dump (shape fields, weights), computed in glb space (Y up, +Z front).
import numpy as np
from scipy.spatial import cKDTree
import scipy.sparse as sp
from g2lib import glb, blendv, split_glb


def ss(x):
    x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)


def win(t, w):
    (a0, a1), (b0, b1) = w
    return ss((t - a0) / (a1 - a0)) * ss((b1 - t) / (b1 - b0))


class Ctx:
    def __init__(self, d, b):
        self.d = d; self.b = b
        self.Pg = glb(d["P"]); self.names = d["names"]
        I = b.sk.index
        self.J = {n: b.rest[i][:3, 3] for n, i in I.items()}
        # vertex adjacency (umbrella Laplacian)
        E = d["E"]; n = len(self.Pg)
        A = sp.coo_matrix((np.ones(2 * len(E)), (np.r_[E[:, 0], E[:, 1]], np.r_[E[:, 1], E[:, 0]])), shape=(n, n)).tocsr()
        deg = np.asarray(A.sum(1)).ravel(); self.A = A; self.deg = deg
        self.Wn = sp.diags(1 / np.maximum(deg, 1)) @ A
        self.tree = cKDTree(self.Pg)

    def shares(self, VG):
        """post-split shares on each arm (upperarm*/lowerarm*/hand) and the breasts, per dump vertex."""
        J, W = split_glb(self.b, VG, self.names, self.Pg)
        nm = np.array(self.b.sk.names)
        out = {}
        for s in "lr":
            js = [i for i, x in enumerate(nm) if x.endswith("_" + s) and any(k in x for k in ("upperarm", "lowerarm", "hand"))]
            out[s] = (W * np.isin(J, js)).sum(1)
        out["breast"] = (W * np.isin(J, [self.b.sk.index["breast_l"], self.b.sk.index["breast_r"]])).sum(1)
        out["J"], out["W"] = J, W
        return out

    def frame(self, s):
        A, E = self.J["upperarm_" + s], self.J["lowerarm_" + s]
        ax = E - A; L = np.linalg.norm(ax); n = ax / L
        up = np.array([0, 1., 0]); top = up - (up @ n) * n; top /= np.linalg.norm(top)
        fr = np.cross(n, top)
        if fr[2] < 0:
            fr = -fr
        d = self.Pg - A; t = d @ n / L; rv = d - np.outer(d @ n, n); r = np.linalg.norm(rv, axis=1); e = rv / np.maximum(r, 1e-9)[:, None]
        phi = np.degrees(np.arctan2(e @ fr, e @ top))
        side = np.sign(self.Pg[:, 0] - 0.001) == np.sign(A[0])
        return dict(A=A, n=n, L=L, top=top, fr=fr, t=t, r=r, e=e, phi=phi, ct=e @ top, side=side)

    def vsmooth(self, D, sigma):
        X = self.Pg; src = np.where(np.linalg.norm(D, axis=1) > 1e-7)[0]
        if not len(src):
            return D
        lo, hi = X[src].min(0) - 3 * sigma, X[src].max(0) + 3 * sigma
        act = np.where(((X > lo) & (X < hi)).all(1))[0]
        Ta, Ts = cKDTree(X[act]), cKDTree(X[src])
        M = Ta.sparse_distance_matrix(Ts, 3 * sigma, output_type="coo_matrix")
        Wg = sp.coo_matrix((np.exp(-0.5 * (M.data / sigma) ** 2), (M.row, M.col)), shape=(len(act), len(src))).tocsr()
        Ma = Ta.sparse_distance_matrix(Ta, 3 * sigma, output_type="coo_matrix")
        den = np.bincount(Ma.row, weights=np.exp(-0.5 * (Ma.data / sigma) ** 2), minlength=len(act))
        Dn = np.zeros_like(D); Dn[act] = (Wg @ D[src]) / np.maximum(den, 1e-12)[:, None]
        return Dn

    def breast_keep(self, D, sh, keep):
        br = sh["breast"] > 0.05
        db, _ = cKDTree(self.Pg[br]).query(self.Pg)
        return D * ss((db - keep[0]) / (keep[1] - keep[0]))[:, None]


def arm_shape_field(c, sh, K=None):
    """tools/assets/heroine_arm_shape.py field(), on the dump (same knobs)."""
    import importlib.util, os
    spec = importlib.util.spec_from_file_location("has", os.path.join(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\armor-7\tools\assets", "heroine_arm_shape.py"))
    import sys
    sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\armor-7\tools\assets")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    K = dict(K or {})
    g = lambda k: K.get(k, getattr(m, k))
    D = np.zeros_like(c.Pg)
    for s in "lr":
        f = c.frame(s); t, r, e, ct = f["t"], f["r"], f["e"], f["ct"]
        wa = ss((sh[s] - g("ARM_W")[0]) / (g("ARM_W")[1] - g("ARM_W")[0])) * f["side"]
        inner = ((1 - ct) / 2) ** g("INNER_POW")
        amt = (g("INNER") * win(t, g("INNER_T")) + g("WEB") * win(t, g("WEB_T"))) * inner * wa
        TW = g("TORSO_W")
        wt = ss(sh[s] / TW[0]) * ss((TW[2] - sh[s]) / (TW[2] - TW[1])) * f["side"]
        D[:, 0] -= np.sign(f["A"][0]) * g("WEB_TORSO") * win(t, g("WEB_T")) * inner * wt
        outer = ((1 + ct) / 2) ** g("DELT_POW")
        DR = g("DELT_R")
        delt = g("DELT") * win(t, g("DELT_T")) * outer * wa * ss((DR[1] - r) / (DR[1] - DR[0]))
        D += e * (delt - amt)[:, None]
    D = c.vsmooth(D, g("SIGMA"))
    return c.breast_keep(D, sh, g("BREAST_KEEP"))


def fair(c, P, mask, iters=20, lam=0.5, mu=-0.53):
    """Taubin fairing of glb points P weighted by mask (0..1) per vertex."""
    X = P.copy(); m = mask[:, None]
    for _ in range(iters):
        X = X + lam * m * (c.Wn @ X - X)
        X = X + mu * m * (c.Wn @ X - X)
    return X


def pit_mask(c, s, T=((-0.30, -0.18), (0.22, 0.36)), PHI=(110, 140), R=(0.085, 0.11)):
    f = c.frame(s)
    a = np.abs(f["phi"])
    return f["side"] * win(f["t"], T) * ss((a - PHI[0]) / (PHI[1] - PHI[0])) * ss((R[1] - f["r"]) / (R[1] - R[0]))


def cap_field(c, sh, s, amt=0.004, T=((-0.25, -0.05), (0.25, 0.42)), pw=2.0, phi0=15.0, R=(0.07, 0.09), sigma=0.012):
    f = c.frame(s)
    a = np.radians(f["phi"] - phi0)
    ang = ((1 + np.cos(a)) / 2) ** pw
    m = amt * win(f["t"], T) * ang * f["side"] * ss((R[1] - f["r"]) / (R[1] - R[0]))
    return f["e"] * m[:, None]
