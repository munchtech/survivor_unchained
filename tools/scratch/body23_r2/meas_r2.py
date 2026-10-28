"""Body 23 r2 numbers. Harness on the FINAL-POSE dump (h2 dump3) unless R2_DUMP is given.
  python meas_r2.py validate                 old harness (dump2) vs h2 (dump3): the elbow contour's offset to the
                                             game picture's strongest edge (px, + = the contour inside the picture's)
  python meas_r2.py CAND.glb [SHOTS_DIR]     the pass bar's numbers, A (v2) vs CAND"""
import os, sys, numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, sobel, map_coordinates
import r2lib as c, corner as K
D2 = c.V2[1]; D3 = os.path.join(c.R2, "loops2", "dump3")


def use(ddir):
    c.DUMP = ddir; c.sh.DUMP = ddir; c._FR.clear()


def edge_offset(png, Q):
    a = np.asarray(Image.open(png).convert("L")).astype(float)
    a = gaussian_filter(a, 1.0)
    G = np.hypot(sobel(a, 0), sobel(a, 1))
    d = np.gradient(Q, axis=0); d /= np.maximum(np.linalg.norm(d, axis=1, keepdims=True), 1e-9)
    n = np.c_[d[:, 1], -d[:, 0]]
    best = []
    for sgn in (1, -1):
        vals = [map_coordinates(G, [(Q + dd * sgn * n)[:, 1], (Q + dd * sgn * n)[:, 0]], order=1).mean() for dd in range(0, 16)]
        best.append((max(vals), int(np.argmax(vals)) * sgn))
    return max(best)[1]


def knot(g, fr, ctr, rad):
    """worst-1% dihedral angle (deg) between neighbouring posed faces within rad of ctr"""
    X, I = g["X"], g["I"]
    m = np.linalg.norm(X[I].mean(1) - ctr, axis=1) < rad
    Fi = np.nonzero(m)[0]
    n = np.cross(X[I[Fi, 1]] - X[I[Fi, 0]], X[I[Fi, 2]] - X[I[Fi, 0]])
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-15)
    u = c.d2u(fr)
    W = u[I[Fi]]
    E = {}
    for t, f in enumerate(W):
        for k in range(3):
            a, b = sorted((int(f[k]), int(f[(k + 1) % 3])))
            E.setdefault((a, b), []).append(t)
    ang = [np.degrees(np.arccos(np.clip(n[l[0]] @ n[l[1]], -1, 1))) for l in E.values() if len(l) == 2]
    return float(np.percentile(ang, 99))


def width(g, fr, row_band):
    ids = c.h.raster(g["xy"], g["z"], g["I"], g["front"], (300, row_band[0], 1620, row_band[1]), 1)
    cols = np.nonzero((ids >= 0).any(0))[0]
    return int(cols.max() - cols.min())


if __name__ == "__main__":
    if sys.argv[1] == "validate":
        for dd, nm in ((D2, "dump-her (old)"), (D3, "final pose (h2)")):
            use(dd)
            out = []
            for f, sd in (("w_m80", "l"), ("rL90_m45", "l"), ("s_p45", "r"), ("w_m45", "l")):
                fr = c.frame(f); g = fr.geom(c.MemBody())
                k = K.corner(fr, g, sd)
                out.append("%s %+d" % (f, edge_offset(os.path.join(D2, f + ".png"), k["Q"])))
            print("%-16s elbow contour to the picture's edge (px): %s" % (nm, "  ".join(out)))
        sys.exit()
    use(os.environ.get("R2_DUMP", D3))
    cand = c.h.GlbBody(sys.argv[1])
    for f, sd in (("w_m80", "l"), ("rL90_m45", "l"), ("s_p45", "r"), ("w_m45", "l"), ("look_f", "l")):
        fr = c.frame(f)
        gA, gC = fr.geom(c.MemBody()), fr.geom(cand)
        kA, kC = K.corner(fr, gA, sd), K.corner(fr, gC, sd)
        E = c.joint(fr, "lowerarm_" + sd); S = c.joint(fr, "upperarm_" + sd)
        el = "corner r_eff A %4.1f -> %4.1f px, flat A %4.1f -> %4.1f mm" % (kA["r_eff"], kC["r_eff"], kA["flat_mm"], kC["flat_mm"]) if kA and kC else "corner n/a"
        print("%-9s %s; knot p99 elbow A %.0f -> %.0f, pit A %.0f -> %.0f deg" % (f, el, knot(gA, fr, E, 0.06), knot(gC, fr, E, 0.06),
              knot(gA, fr, S - np.array([0, 0.04, 0]), 0.05), knot(gC, fr, S - np.array([0, 0.04, 0]), 0.05)))
    for f in ("look_f", "r132_p45", "r132_m45", "w_p45"):
        fr = c.frame(f); gA, gC = fr.geom(c.MemBody()), fr.geom(cand)
        y = int(c.jscreen(fr, "upperarm_l")[1])
        mv = np.abs(gC["xy"] - gA["xy"]).max(1)
        print("%-9s width at the shoulders A %d -> %d px; vertex screen move max %.1f px" % (f, width(gA, fr, (y - 10, y + 40)), width(gC, fr, (y - 10, y + 40)), mv.max()))
    if len(sys.argv) > 2:      # Godot frames: pixel diff away from the arms (|diff| > 12 outside 140 px of the elbows/shoulders)
        for f in c.LIST9:
            fr = c.frame(f)
            a = np.asarray(Image.open(os.path.join(D2, f + ".png")).convert("RGB")).astype(int)
            b = np.asarray(Image.open(os.path.join(sys.argv[2], f + ".png")).convert("RGB")).astype(int)
            dif = np.abs(a - b).max(2) > 12
            yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]]
            near = np.zeros_like(dif)
            for n in ("upperarm_l", "upperarm_r", "lowerarm_l", "lowerarm_r"):
                q = c.jscreen(fr, n)
                near |= (xx - q[0]) ** 2 + (yy - q[1]) ** 2 < 140 ** 2
            print("%-9s Godot diff px: near arms %d, away %d" % (f, int((dif & near).sum()), int((dif & ~near).sum())))
