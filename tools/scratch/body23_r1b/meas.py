"""C3 numbers: per judged frame and asked region, A's silhouette move to the candidate (px at 1:1, + out) against the
target's; knots (posed face normals turned > 60 deg vs A, flips) in the pit and elbow; raised frames' outline move.
    python meas.py CAND.glb"""
import sys, numpy as np, c3lib as c, targets as T
from scipy.ndimage import distance_transform_edt, binary_fill_holes
SS = T.SS
cand = sys.argv[1]
gbC = c.h.GlbBody(cand)
b = c.body()


def region_masks(fr, B):
    """per A boundary pixel: its region name (by re-running each region with a marker)"""
    lab = np.array([""] * len(B["p"]), dtype=object)
    for nm, fn in (("cap", T.cap_region), ("pit", T.pit_region), ("waist", T.waist_region), ("elbow", T.elbow_region)):
        for sd in "lr":
            if nm in ("cap", "pit") and sd not in T.VIS.get(fr.name, ""):
                continue
            D = np.zeros(len(B["p"])); W = np.zeros(len(B["p"]))
            fn(fr, sd, B, D, W)
            lab[W > 0] = "%s_%s" % (nm, sd)
    return lab


def knots(fr, gA, gC):
    """faces folded against their smoothed neighbourhood (posed): A's count, C's count, in the moved region"""
    I = gA["I"]; nV = len(gA["X"])
    import scipy.sparse as sp_
    Adj = sp_.csr_matrix((np.ones(3 * len(I)), (I.ravel(), np.repeat(np.arange(len(I)), 3))), shape=(nV, len(I)))
    def folded(g):
        X = g["X"]; n = np.cross(X[I[:, 1]] - X[I[:, 0]], X[I[:, 2]] - X[I[:, 0]])
        Ns = np.vstack([sf["A"][:, 3:6] for sf in fr.dump["surfs"]])
        n = n * np.sign((n * Ns[I].sum(1)).sum(1))[:, None]
        vn = Adj @ n
        for _ in range(4):
            fnb = vn[I].sum(1); vn = Adj @ fnb
        fs = vn[I].sum(1)
        cs = (n * fs).sum(1) / np.maximum(np.linalg.norm(n, axis=1) * np.linalg.norm(fs, axis=1), 1e-18)
        return cs < 0.2
    def fn(g):
        X = g["X"]; n = np.cross(X[I[:, 1]] - X[I[:, 0]], X[I[:, 2]] - X[I[:, 0]])
        return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-15)
    moved = np.linalg.norm(gC["X"] - gA["X"], axis=1) > 1e-4
    tri_m = moved[I].any(1) & (c.d2u(fr)[I] >= 0).all(1)
    return int((tri_m & folded(gA)).sum()), int((tri_m & folded(gC)).sum()), int(tri_m.sum())


rows = []
for f in c.HANG + c.BEND + c.RAISE:
    fr = c.frame(f); box = c.box_of(fr)
    gA = fr.geom(c.MemBody()); gC = fr.geom(gbC)
    B = T.build(fr, gA, box)
    idsC = c.h.raster(gC["xy"], gC["z"], gC["I"], gC["front"], box, SS)
    fgC = idsC >= 0
    outer = ~binary_fill_holes(B["fg"])[B["yy"], B["xx"]] | True
    hole = ~(B["fg"] | ~binary_fill_holes(B["fg"]))         # A's see-through holes (pinched pit)
    from scipy.ndimage import binary_dilation
    onhole = binary_dilation(hole, iterations=2)[B["yy"], B["xx"]]
    sdC = (distance_transform_edt(~fgC) - distance_transform_edt(fgC)) / SS
    mv = -sdC[B["yy"], B["xx"]]
    hh_, ww_ = B["fg"].shape
    edge = (B["yy"] < 8) | (B["xx"] < 8) | (B["yy"] >= hh_ - 8) | (B["xx"] >= ww_ - 8)
    mv[edge] = 0.0
    holesA, holesC = int(hole.sum() / SS ** 2), int((~(idsC >= 0) & binary_fill_holes(idsC >= 0)).sum() / SS ** 2)
    k60, kflip, ntri = knots(fr, gA, gC)
    if f in c.RAISE:
        print("%-9s raised: outline move max %.1f mean %.2f px; folded faces A %d -> C %d (of %d moved); see-through px A %d C %d" % (f, np.abs(mv).max(), np.abs(mv).mean(), k60, kflip, ntri, holesA, holesC))
        continue
    lab = region_masks(fr, B)
    out = []
    for r in sorted(set(lab) - {""}):
        m = lab == r
        tgt, ach = B["D"][m], mv[m]
        big = np.abs(tgt) >= 4
        out.append("%s tgt %+.0f/%.1f ach %+.0f/%.1f hit %.0f%%" % (r, tgt[np.argmax(np.abs(tgt))], np.abs(tgt).mean(), ach[np.argmax(np.abs(ach))], np.abs(ach).mean(),
                                                               100 * (np.abs(ach[big]) >= 6).mean() if big.any() else 0))
    rest = lab == ""
    print("%-9s %s | other |mv| p99 %.1f | folded A %d C %d | holes A %d C %d" % (f, " ; ".join(out), np.percentile(np.abs(mv[rest]), 99), k60, kflip, holesA, holesC))
