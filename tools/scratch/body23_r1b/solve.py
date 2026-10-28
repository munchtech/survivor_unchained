"""C3 step 2: solve her surface to the target outlines IN CAMERA (Gauss-Newton on the harness's exact posing).

Unknowns (scalar offsets along her smoothed rest normal, mm, per welded vertex):
  h0            her REST shape over each shoulder region (deltoid, acromion, pit rim and the chest wall next to it): seen by
                every frame through the frame's own blended skin (inverse skinning: the posed move S_v N_v h)
  h45/h90/h135  elbow pose-space correctives (elbow_psd{45,90,135}_{l,r}), within ~115 mm of each elbow: seen with the
                game's in-between weights at that frame's flexion (flex.py = ElbowPsd.cs)
Rows: every silhouette pixel of the current candidate at each frame: its target offset from A (targets.py, + out) minus
where it is now (signed distance to A's silhouette), through the pixel's triangle (barycentric) and the projection's
Jacobian; untargeted pixels near the fields are held at A (weight KEEP). Regularized by a bending energy (the uniform
mesh Laplacian squared: finer where the loops are dense, so the olecranon and the fold may be tighter), damping, a
fade to 0 at each region's rim, and a soft mirror coupling of the two sides' fields (each side keeps its own vertices).
    python solve.py OUT_NAME [iters]
"""
import sys, os, time, json, numpy as np, scipy.sparse as sp
from scipy.sparse.linalg import spsolve
from scipy.ndimage import distance_transform_edt, binary_erosion
from scipy.spatial import cKDTree
import c3lib as c, targets as T

FRAMES = ["w_p45", "w_m45", "look_f", "w_m80", "rL90_m45", "s_p45"]
KEEP = float(os.environ.get("C3_KEEP", 0.35))
LB = float(os.environ.get("C3_LB", 6.0))       # bending weight (rows of L h, mm)
LB_PSD = float(os.environ.get("C3_LBP", 4.0))
L0 = float(os.environ.get("C3_L0", 0.03))       # damping
LSYM = float(os.environ.get("C3_SYM", 0.5))
L0P = float(os.environ.get("C3_L0P", 0.12))
LC = float(os.environ.get("C3_LC", 0.8))
LM = float(os.environ.get("C3_LM", 0.3))       # Levenberg damping on each step
SS = T.SS
PSD = ("elbow_psd45", "elbow_psd90", "elbow_psd135")


def regions(b):
    J = {n: np.linalg.inv(b.ibm[i])[:3, 3] for i, n in enumerate(b.names)}
    U = b.U
    out = {}
    for sd in "lr":
        side = (U[:, 0] > 0) if sd == "l" else (U[:, 0] < 0)
        Sh, El, Wr = J["upperarm_" + sd], J["lowerarm_" + sd], J["hand_" + sd]
        ax = (El - Sh) / np.linalg.norm(El - Sh)
        s = (U - Sh) @ ax
        dsh = np.linalg.norm(U - Sh, axis=1)
        wa = b.arm_w(sd)
        head = U[:, 1] > Sh[1] + 0.09                    # (her neck and above: never)
        R0 = side & ~head & (dsh < 0.16) & (s < 0.175) & ((wa > 0.02) | (dsh < 0.13))
        fade0 = T.smooth01((0.16 - dsh) / 0.035) * T.smooth01((0.175 - s) / 0.04)
        de = np.linalg.norm(U - El, axis=1)
        RE = side & (wa > 0.4) & (de < 0.115)
        fadeE = T.smooth01((0.115 - de) / 0.035)
        out[sd] = dict(R0=R0, RE=RE, fade0=fade0, fadeE=fadeE, Sh=Sh, El=El)
    return out


class Layout:
    """unknown blocks: (field, side) -> welded ids"""

    def __init__(s, b, R):
        s.blocks = []
        o = 0
        for sd in "lr":
            for f in ("h0",) + PSD:
                ids = np.nonzero(R[sd]["R0"] if f == "h0" else R[sd]["RE"])[0]
                s.blocks.append(dict(f=f, sd=sd, ids=ids, o=o, fade=(R[sd]["fade0"] if f == "h0" else R[sd]["fadeE"])[ids]))
                o += len(ids)
        s.n = o
        s.col = {}
        for B in s.blocks:
            m = np.full(len(b.U), -1); m[B["ids"]] = np.arange(len(B["ids"])) + B["o"]
            s.col[(B["f"], B["sd"])] = m

    def fields(s, x, nU):
        F = {}
        for B in s.blocks:
            v = np.zeros(nU); v[B["ids"]] = x[B["o"]:B["o"] + len(B["ids"])]
            F[(B["f"], B["sd"])] = v
        return F


def membody(F, b):
    dU = (F[("h0", "l")] + F[("h0", "r")])[:, None] * b.N / 1000
    shapes = {}
    for f in PSD:
        for sd in "lr":
            shapes["%s_%s" % (f, sd)] = F[(f, sd)][:, None] * b.N / 1000
    return c.MemBody(dU, shapes), dU, shapes


def bary(xy, P):
    a, b_, c_ = xy[:, 0], xy[:, 1], xy[:, 2]
    v0, v1, v2 = b_ - a, c_ - a, P - a
    d00 = (v0 * v0).sum(1); d01 = (v0 * v1).sum(1); d11 = (v1 * v1).sum(1); d20 = (v2 * v0).sum(1); d21 = (v2 * v1).sum(1)
    den = d00 * d11 - d01 * d01; den = np.where(np.abs(den) < 1e-12, 1e-12, den)
    w1 = (d11 * d20 - d01 * d21) / den; w2 = (d00 * d21 - d01 * d20) / den
    W = np.c_[1 - w1 - w2, w1, w2]
    W = np.clip(W, 0, 1); return W / np.maximum(W.sum(1, keepdims=True), 1e-9)


class FrameTarget:
    def __init__(s, name):
        s.fr = c.frame(name)
        s.box = c.box_of(s.fr)
        s.B = T.build(s.fr, None, s.box)
        bdA = np.zeros_like(s.B["fg"]); bdA[s.B["yy"], s.B["xx"]] = True
        _, s.near = distance_transform_edt(~bdA, return_indices=True)
        s.rowof = np.full(bdA.shape, -1); s.rowof[s.B["yy"], s.B["xx"]] = np.arange(len(s.B["yy"]))
        s.S3 = c.skin3(s.fr); s.d2u = c.d2u(s.fr)
        sh_ = s.fr.dump["surfs"][0]["shapes"]
        s.w = {(f, sd): float(sh_.get("%s_%s" % (f, sd), 0.0)) for f in PSD for sd in "lr"}

    def rows(s, gb, b, lay, F):
        """(rows A (sparse), rhs, weights, stats) at the candidate gb"""
        fr = s.fr
        g = fr.geom(gb)
        ids = c.h.raster(g["xy"], g["z"], g["I"], g["front"], s.box, SS)
        fg = ids >= 0
        bd = fg & ~binary_erosion(fg)
        yy, xx = np.nonzero(bd)
        t = ids[yy, xx]
        p = np.c_[(xx + 0.5) / SS + s.box[0], (yy + 0.5) / SS + s.box[1]]
        # where the candidate is against A, and what the target wants there
        sdA = s.B["sdA"][yy, xx]
        ny, nx = s.near[0][yy, xx], s.near[1][yy, xx]
        r_ = s.rowof[ny, nx]
        Dt = s.B["D"][r_]; Wt = s.B["W"][r_]
        res = Dt - sdA
        wt = np.where(Wt > 0, 1.0, KEEP)
        tri = g["I"][t]
        u = s.d2u[tri]
        okv = (u >= 0).all(1)
        Wb = bary(g["xy"][tri], p)
        X = (g["X"][tri] * Wb[:, :, None]).sum(1)
        Jp = c.jaco(fr, X) if hasattr(c, "jaco") else c.jac(fr, X)
        Sv = s.S3[tri]                                     # (m,3,3,3)
        Nu = b.N[np.maximum(u, 0)]                         # (m,3,3)
        SN = np.einsum("mkab,mkb->mka", Sv, Nu)            # posed dir of each corner's rest normal
        n3 = (SN * Wb[:, :, None]).sum(1); n3 /= np.maximum(np.linalg.norm(n3, axis=1, keepdims=True), 1e-9)
        n2 = np.einsum("mab,mb->ma", Jp, n3)
        nn = np.linalg.norm(n2, axis=1); n2 = n2 / np.maximum(nn[:, None], 1e-9)
        # the silhouette's outward normal from the raster, to check the sign
        from scipy.ndimage import gaussian_filter
        sm = gaussian_filter((~fg).astype(float), 2.0)
        gy, gx = np.gradient(sm)
        n2r = np.c_[gx[yy, xx], gy[yy, xx]]
        agree = (n2 * n2r).sum(1) > 0.3 * np.linalg.norm(n2r, axis=1)
        coef = np.einsum("ma,mkab,mkb->mk", n2, Jp[:, None].repeat(3, 1), SN) / 1000.0 * Wb   # px per mm, per corner
        keep = okv & agree & (np.abs(res) < 40)
        rows, cols, vals = [], [], []
        idx = np.nonzero(keep)[0]
        m_ = len(idx)
        for k in range(3):
            uk = u[idx, k]
            for (f, sd), colmap in lay.col.items():
                cc = colmap[uk]
                okc = cc >= 0
                if not okc.any():
                    continue
                wgt = 1.0 if f == "h0" else s.w[(f, sd)]
                if wgt == 0:
                    continue
                rows.append(np.arange(m_)[okc]); cols.append(cc[okc]); vals.append(coef[idx[okc], k] * wgt)
        if not rows:
            return None
        A = sp.csr_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), shape=(m_, lay.n))
        has = np.asarray(abs(A).sum(1)).ravel() > 1e-6
        tgt = Wt[idx] > 0
        st = dict(n_t=int((tgt & has).sum()), err_t=float(np.abs(res[idx][tgt & has]).mean()) if (tgt & has).any() else 0.0,
                  err_k=float(np.abs(res[idx][~tgt & has]).mean()) if (~tgt & has).any() else 0.0, disagree=int((~agree).sum()))
        return A[has], res[idx][has], wt[idx][has], st


def reg_matrix(b, lay):
    """bending rows (L h per vertex, over each block's region and its 1-ring), fade damping, mirror coupling"""
    nU = len(b.U)
    Lap = sp.diags(1.0 / b.deg) @ b.A - sp.eye(nU)
    R, rhs = [], []
    for B in lay.blocks:
        P = sp.csr_matrix((np.ones(len(B["ids"])), (B["ids"], np.arange(len(B["ids"])) + B["o"])), shape=(nU, lay.n))
        ring = np.unique(np.r_[B["ids"], b.A[B["ids"]].indices])
        lb = LB if B["f"] == "h0" else LB_PSD
        R.append(lb * (Lap[ring] @ P))
        damp = (L0 if B["f"] == "h0" else L0P) + 3.0 * (1 - B["fade"]) ** 2
        R.append(sp.csr_matrix((damp, (np.arange(len(B["ids"])), np.arange(len(B["ids"])) + B["o"])), shape=(len(B["ids"]), lay.n)))
    # the in-betweens kept close to each other (psd135 ~ psd90, psd45 a softer share): only flexion in between tells them apart
    for sd in "lr":
        Bs = {B["f"]: B for B in lay.blocks if B["sd"] == sd}
        n_ = len(Bs["elbow_psd90"]["ids"]); ar = np.arange(n_)
        for f, wc in (("elbow_psd135", LC), ("elbow_psd45", 0.5 * LC)):
            R.append(sp.csr_matrix((np.r_[np.full(n_, wc), np.full(n_, -wc)], (np.r_[ar, ar], np.r_[Bs[f]["o"] + ar, Bs["elbow_psd90"]["o"] + ar])), shape=(n_, lay.n)))
    # mirror coupling: each left vertex against the right surface at its mirror point (3 nearest, inverse distance)
    for f in ("h0",) + PSD:
        Bl = [B for B in lay.blocks if B["f"] == f and B["sd"] == "l"][0]
        Br = [B for B in lay.blocks if B["f"] == f and B["sd"] == "r"][0]
        Q = b.U[Bl["ids"]] * [-1, 1, 1]
        d, j = cKDTree(b.U[Br["ids"]]).query(Q, 3)
        w = 1.0 / np.maximum(d, 1e-4); w /= w.sum(1, keepdims=True)
        ok = d[:, 0] < 0.008
        n_ = ok.sum()
        rr = np.r_[np.arange(n_), np.repeat(np.arange(n_), 3)]
        cc = np.r_[Bl["o"] + np.nonzero(ok)[0], (Br["o"] + j[ok]).ravel()]
        vv = np.r_[np.ones(n_), -w[ok].ravel()] * LSYM
        R.append(sp.csr_matrix((vv, (rr, cc)), shape=(n_, lay.n)))
    return sp.vstack(R).tocsr()


def main():
    name = sys.argv[1]; iters = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    t0 = time.time()
    b = c.body(); nU = len(b.U)
    R = regions(b); lay = Layout(b, R)
    print("unknowns", lay.n, {(B["f"], B["sd"]): len(B["ids"]) for B in lay.blocks})
    Rg = reg_matrix(b, lay)
    RtR = (Rg.T @ Rg).tocsc()
    FT = [FrameTarget(f) for f in FRAMES]
    print("frames ready %.0fs" % (time.time() - t0))
    x = np.zeros(lay.n)
    for it in range(iters + 1):
        F = lay.fields(x, nU)
        gb, dU, shapes = membody(F, b)
        AtA = sp.csr_matrix((lay.n, lay.n)); Atr = np.zeros(lay.n)
        rep = []
        for ft in FT:
            out = ft.rows(gb, b, lay, F)
            if out is None:
                continue
            A, r, w, st = out
            Aw = sp.diags(w) @ A
            AtA = AtA + Aw.T @ Aw; Atr += Aw.T @ (w * r)
            rep.append("%s t%d e%.1f k%.1f" % (ft.fr.name, st["n_t"], st["err_t"], st["err_k"]))
        print("iter %d: %s   |h| max %.1f mm  (%.0fs)" % (it, " | ".join(rep), np.abs(x).max(), time.time() - t0)); sys.stdout.flush()
        if it == iters:
            break
        Mx = (AtA + RtR + LM * sp.eye(lay.n)).tocsc()
        dx = spsolve(Mx, Atr - RtR @ x)
        x = x + dx
    np.save(name + "_x.npy", x)
    F = lay.fields(x, nU)
    np.savez_compressed(name + "_fields.npz", **{"%s_%s" % k: v for k, v in F.items()})
    print("saved", name, "%.0fs" % (time.time() - t0))


if __name__ == "__main__":
    main()
