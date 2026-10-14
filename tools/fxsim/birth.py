"""Regrade a fireball bake's birth in its cache (boom_sim.py's Mantaflow VDBs), so its first frames read as a violent
fireball, not the sim's saturated blob. Run with Blender's own Python (it bundles openvdb, numpy and scipy):

    <blender>/4.5/python/bin/python.exe tools/fxsim/birth.py SRC_CACHE DST_CACHE [--preset b5c] [--last 9]

Mantaflow's flame is saturated (1.0) across the whole young ball, then broken into salt-and-pepper from f4 (its burning
flickers cell by cell), so any shading of the flame alone is one flat silhouette, then grain. For each frame of the
birth (1..last) this rewrites:
  flame        de-speckled (a Gaussian of a cell or so): the sim's shapes, never its grain;
  temperature  a designed heat T in [0, 1], written doubled (Blender reads the cache's temperature halved, as `heat`),
               for src_material's birth branch (take key `birth`) to colour and light the fire by: the lobes (a
               difference of Gaussians of the fire's shape: its convex lumps hot, its creases cool), its depth (deep
               fire hotter than its skin, so through semi-clear fire a lobe's limb reads darker), its distance from
               the middle on screen, and a small white-hot heart on the camera's line through the burst's centre;
  density      the soot born torn: the thrown soot puffs ripped into radial wisps (a noise fixed on directions from
               the centre, so they streak outward, broken along their length) and thin, fading in, plus torn soot
               on the lobes' skin, all handed back to the sim's own soot by the birth's end.
Every other frame is linked unchanged (a hard link, else a copy), so the rest renders as the bake's own.
"""
import os
import shutil
import sys

import numpy as np
import openvdb
from scipy import ndimage as nd

H_ = 0.0625  # the cell (m): a 15 m domain at resolution 240

PRESETS = {
    # Bake b5 (take burns_boom5): its birth, f1-f9, handed to the render b5g at f10.
    "b5c": dict(
        dom=(15.0, 15.0, 15.0), res=240, centre=(0.0, 0.0, 1.5), pitch=66.0,
        fsig=((1, 0.6), (3, 1.0), (4, 1.6), (5, 2.0), (8, 2.0), (9, 1.2)),       # flame de-speckle (cells)
        chi=(0.05, 0.35),                                               # the fire's shape: smoothstep of the flame
        s1=((1, 0.10), (4, 0.18), (9, 0.26)), s2=((1, 0.32), (4, 0.55), (9, 0.75)),  # lobe scales (m)
        base=((1, 0.78), (2, 0.70), (3, 0.68), (4, 0.67), (5, 0.66), (7, 0.66), (8, 0.64), (9, 0.63)),
        k_depth=0.36, k_lobe=0.16, k_rad=0.12, rad0=0.35,
        heart=((1, 0.26), (3, 0.26), (4, 0.2), (5, 0.1), (6, 0.0)), heart_r=((1, 0.32), (2, 0.58), (3, 0.72),
                                                                              (4, 0.68), (5, 0.5), (6, 0.4)),
        # Soot: the puffs thinned (fade) and torn (tear: how much of the wisp mask applies), skin soot on the lobes.
        fade=((1, 0.1), (3, 0.12), (5, 0.25), (7, 0.5), (8, 0.7), (9, 0.85), (10, 1.0)),
        tear=((1, 1.0), (6, 1.0), (8, 0.6), (9, 0.35), (10, 0.0)), tear_th=0.55,
        skin=((1, 0.0), (2, 0.0), (3, 0.05), (5, 0.07), (7, 0.06), (8, 0.04), (9, 0.02), (10, 0.0)), skin_th=0.55,
        ka=50.0, kb=40.0, seed=7,
    ),
}


def key(keys, f):
    fr = [k[0] for k in keys]; vs = [k[1] for k in keys]
    return float(np.interp(f, fr, vs))


def smooth(a, lo, hi):
    t = np.clip((a - lo) / (hi - lo), 0, 1)
    return t * t * (3 - 2 * t)


def noise_cube(n, seed, sig):
    """A smooth periodic noise, ranked to an even 0..1."""
    r = np.random.default_rng(seed)
    a = nd.gaussian_filter(r.standard_normal((n, n, n)).astype(np.float32), sig, mode="wrap")
    a = (a - a.mean()) / a.std()
    return (0.5 + 0.5 * np.tanh(a * 0.9)).astype(np.float32)


def sample(cube, p):
    """The cube sampled (trilinear, wrapped) at points p (3, M) in cube cells."""
    return nd.map_coordinates(cube, p, order=1, mode="grid-wrap").astype(np.float32)


def regrade(fl, dn, tp, f, P, cubes):
    N = fl.shape[0]
    h = P["dom"][0] / N
    fs = key(P["fsig"], f)
    Fs = nd.gaussian_filter(fl, fs) if fs > 0 else fl
    chi = smooth(Fs, *P["chi"]).astype(np.float32)
    G1 = nd.gaussian_filter(chi, key(P["s1"], f) / h)
    G2 = nd.gaussian_filter(chi, key(P["s2"], f) / h)
    dog = np.clip((G1 - G2) / 0.2, -1, 1)
    # Positions (world) of the cells, the fire's centroid, the view axis.
    ax = (np.arange(N, dtype=np.float32) + 0.5) * h
    X = ax[:, None, None] - P["dom"][0] / 2; Y = ax[None, :, None] - P["dom"][1] / 2; Z = ax[None, None, :]
    w = chi > 0.5
    idx = np.argwhere(w)
    cg = ((idx.mean(0) + 0.5) * h - np.array([P["dom"][0] / 2, P["dom"][1] / 2, 0.0]) if len(idx)
          else np.array(P["centre"])).astype(np.float32)
    pt = np.radians(P["pitch"])
    d = np.array([0.0, np.cos(pt), -np.sin(pt)], np.float32)  # the camera's look
    c0 = np.array(P["centre"], np.float32)
    # Projected distance from the heart's line (the camera's ray through the burst's centre) and depth toward the camera.
    vx, vy, vz = X - c0[0], Y - c0[1], Z - c0[2]
    vd = vx * d[0] + vy * d[1] + vz * d[2]
    rho = np.sqrt(np.maximum((vx - vd * d[0]) ** 2 + (vy - vd * d[1]) ** 2 + (vz - vd * d[2]) ** 2, 0))
    s_cam = -vd
    # The fire's radius on screen (from its own centroid's line): the 92nd percentile of the projected distances.
    gx, gy, gz = X - cg[0], Y - cg[1], Z - cg[2]
    gd = gx * d[0] + gy * d[1] + gz * d[2]
    rho_g = np.sqrt(np.maximum((gx - gd * d[0]) ** 2 + (gy - gd * d[1]) ** 2 + (gz - gd * d[2]) ** 2, 0))
    R = float(np.percentile(rho_g[w], 92)) if w.any() else 1.0
    hr = key(P["heart_r"], f)
    Hc = np.exp(-(rho / hr) ** 2) * smooth(s_cam, -0.35, 0.15)
    T = (key(P["base"], f) + P["k_depth"] * (G1 - 0.5) + P["k_lobe"] * dog
         - P["k_rad"] * np.clip(rho_g / R - P["rad0"], 0, 1) + key(P["heart"], f) * Hc)
    T = np.clip(T, 0, 1) * (chi > 0.01)
    # Soot.
    D = dn
    fade, tear, skin = key(P["fade"], f), key(P["tear"], f), key(P["skin"], f)
    if fade < 1 or tear > 0 or skin > 0:
        out = 1.0 - smooth(G1, 0.1, 0.6)  # outside the fire
        m = (D > 1e-4) | ((G1 > 0.02) & (G1 < 0.6))
        ii = np.nonzero(m)
        x_ = X[ii[0], 0, 0]; y_ = Y[0, ii[1], 0]; z_ = Z[0, 0, ii[2]]
        rx, ry, rz = x_ - cg[0], y_ - cg[1], z_ - cg[2]
        rr = np.sqrt(rx * rx + ry * ry + rz * rz) + 1e-6
        ua = np.stack([rx / rr, ry / rr, rz / rr]) * P["ka"]
        ub = np.stack([rx, ry, rz]) / R * P["kb"]
        na = sample(cubes[0], ua + 17.0); nb = sample(cubes[1], ub + 5.0)
        wisp = smooth(0.5 * na + 0.5 * nb, P["tear_th"] - 0.08, P["tear_th"] + 0.08)
        na2 = sample(cubes[0], ua * 1.3 + 41.0); nb2 = sample(cubes[1], ub * 1.2 + 23.0)
        rag = smooth(0.6 * na2 + 0.4 * nb2, P["skin_th"] - 0.06, P["skin_th"] + 0.06)
        o_ = out[ii]; d_ = D[ii]; g_ = G1[ii]
        dout = d_ * o_ * fade * (1 - tear + tear * wisp)
        din = d_ * (1 - o_)
        band = smooth(g_, 0.03, 0.12) * (1 - smooth(g_, 0.3, 0.55))
        dsk = skin * band * rag
        D = np.zeros_like(dn)
        D[ii] = din + np.maximum(dout, dsk)
    return Fs.astype(np.float32), (2.0 * T).astype(np.float32), D.astype(np.float32), dict(R=R, cg=cg.tolist())


def main():
    src, dst = sys.argv[1], sys.argv[2]
    av = sys.argv[3:]
    preset = av[av.index("--preset") + 1] if "--preset" in av else "b5c"
    last = int(av[av.index("--last") + 1]) if "--last" in av else 9
    P = PRESETS[preset]
    for sub in ("config", "data", "guiding", "mesh", "noise", "particles"):
        os.makedirs(os.path.join(dst, sub), exist_ok=True)
    for sub in ("config", "data"):
        for fn in sorted(os.listdir(os.path.join(src, sub))):
            s_, d_ = os.path.join(src, sub, fn), os.path.join(dst, sub, fn)
            fr = int(fn.split("_")[-1].split(".")[0])
            if sub == "data" and fr <= last:
                continue
            if os.path.exists(d_):
                os.remove(d_)
            try:
                os.link(s_, d_)
            except OSError:
                shutil.copy2(s_, d_)
    cubes = [noise_cube(96, P["seed"], 2.0), noise_cube(96, P["seed"] + 1, 2.5)]
    N = P["res"]
    for f in range(1, last + 1):
        fn = "fluid_data_%04d.vdb" % f
        grids, meta = openvdb.readAll(os.path.join(src, "data", fn))
        G = {g.name: g for g in grids}

        def dense(g):
            a = np.zeros((N, N, N), np.float32); g.copyToArray(a, ijk=(0, 0, 0)); return a
        fl, dn, tp = dense(G["flame"]), dense(G["density"]), dense(G["temperature"])
        Fn, Tn, Dn, info = regrade(fl, dn, tp, f, P, cubes)
        new = {"flame": Fn, "temperature": Tn, "density": Dn}
        out = []
        for g in grids:
            if g.name in new:
                ng = openvdb.FloatGrid()
                ng.copyFromArray(np.ascontiguousarray(new[g.name]), ijk=(0, 0, 0), tolerance=1e-5)
                ng.transform = g.transform; ng.name = g.name; ng.gridClass = g.gridClass
                ng.saveFloatAsHalf = True
                out.append(ng)
            else:
                out.append(g)
        p = os.path.join(dst, "data", fn)
        if os.path.exists(p):
            os.remove(p)
        openvdb.write(p, grids=out, metadata=meta)
        fire = Fn > 0.3
        print("BIRTH f%02d" % f, "R %.2f m" % info["R"], "centroid (%.2f %.2f %.2f)" % tuple(info["cg"]),
              "T in fire p10/50/90/99 %.2f %.2f %.2f %.2f" % tuple(np.percentile(Tn[fire] / 2, [10, 50, 90, 99])) if fire.any() else "",
              "soot sum %.0f -> %.0f" % (dn.sum(), Dn.sum()), flush=True)
    print("BIRTH done", dst)


main()
