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
        base=((1, 0.72), (2, 0.60), (3, 0.58), (4, 0.58), (5, 0.62), (6, 0.66), (7, 0.66), (8, 0.64), (9, 0.63)),
        k_depth=0.36, k_lobe=0.22, k_rad=0.12, rad0=0.35,
        heart=((1, 0.32), (3, 0.32), (4, 0.26), (5, 0.12), (6, 0.0)), heart_r=((1, 0.32), (2, 0.58), (3, 0.72),
                                                                              (4, 0.68), (5, 0.5), (6, 0.4)),
        # Soot: the puffs thinned (fade) and torn (tear: how much of the wisp mask applies), skin soot on the lobes.
        fade=((1, 0.1), (3, 0.12), (5, 0.25), (7, 0.5), (8, 0.7), (9, 0.85), (10, 1.0)),
        tear=((1, 1.0), (6, 1.0), (8, 0.6), (9, 0.35), (10, 0.0)), tear_th=0.55,
        skin=((1, 0.0), (2, 0.0), (3, 0.05), (5, 0.07), (7, 0.06), (8, 0.04), (9, 0.02), (10, 0.0)), skin_th=0.55,
        ka=50.0, kb=40.0, seed=7,
    ),
}
# Bake b5's birth, version 2 (solver 8, after judge 4: "a flat cream cotton ball, one value, no hot core, 5-6 smooth
# lobes, no small billows"): the shape the flame or the hot gas (the edge rolls out to f9), two finer billow sizes
# (0.85 and 0.29 m at R 2.2 m, about a third and a ninth of the sim's lobes, scaled with the ball), the heat in four
# bands for take burns_boom5d's birth ramp (creases ~0.45, rims ~0.58, body ~0.75, a white-yellow core >= 0.95 on
# the camera's line through the middle, 30-40% of the ball at f2-f3, gone by f6), handed back to the sim's grain f7-f9.
PRESETS["b5d"] = dict(
    PRESETS["b5c"], v=2,
    fsig=((1, 0.6), (3, 1.0), (4, 1.6), (6, 1.6), (7, 1.2), (8, 0.8), (9, 0.6)),
    hot=(1.5, 2.2), hot_w=((1, 1.0), (9, 1.0)),
    band=0.7, r_ref=2.2, beta=1.0,
    billows=((0.85, 0.34, 0.85, 0.30), (0.29, 0.11, 0.85, 0.30)),   # (spacing m, displacement m, dome radius, crease width)
    bamp=((1, 0.7), (2, 1.0), (9, 1.0)), edge=0.06, deep=((1, 0.5), (9, 0.5)),
    base=((1, 0.80), (2, 0.80), (3, 0.79), (4, 0.78), (5, 0.77), (6, 0.75), (7, 0.72), (8, 0.68), (9, 0.64)),
    k_depth=0.30, k_bill=(0.25, 0.15), k_crease=(0.22, 0.12),
    heart=((1, 0.55), (2, 0.50), (3, 0.42), (4, 0.28), (5, 0.15), (6, 0.04), (7, 0.0)),
    heart_m=((1, 1.0), (2, 1.15), (3, 1.35), (4, 1.1), (5, 0.8), (6, 0.55), (7, 0.5)), heart_crease=0.6,
    k_rad=0.15, rad0=0.5,
    hand=((1, 0.0), (5, 0.0), (6, 0.15), (7, 0.4), (8, 0.65), (9, 0.85)),
    csoot=((1, 0.0), (3, 0.0), (4, 0.02), (6, 0.06), (8, 0.12), (9, 0.15)),
)


def key(keys, f):
    fr = [k[0] for k in keys]; vs = [k[1] for k in keys]
    return float(np.interp(f, fr, vs))


def worley(q, s, table):
    """A jittered-grid cellular noise at points q (M, 3), cells s metres: the distances (in cells) to the nearest
    and second-nearest feature point, F1 and F2. table: (n, n, n, 3) jitters, so a cell's point is fixed."""
    g = q / s
    c = np.floor(g).astype(np.int64)
    fr = (g - c).astype(np.float32)
    n = table.shape[0]
    F1 = np.full(len(q), 9.0, np.float32); F2 = np.full(len(q), 9.0, np.float32)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                j = table[(c[:, 0] + dx) % n, (c[:, 1] + dy) % n, (c[:, 2] + dz) % n]
                d = np.array([dx, dy, dz], np.float32) + j - fr
                r = np.sqrt((d * d).sum(1))
                F2 = np.minimum(F2, np.maximum(F1, r))
                F1 = np.minimum(F1, r)
    return F1, F2


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


def regrade2(fl, dn, tp, f, P, cubes, tabs):
    """Version 2 (preset b5d): the fire's shape is its flame or its hot gas, whichever is wider (the flame breaks up
    from f5 while the hot gas keeps swelling, so the edge keeps rolling out), displaced by two finer sizes of billow
    (cellular domes about a third and a ninth of the sim's lobes, riding the ball as it grows), and its heat is
    designed on that shape: deep fire hotter than its skin, each billow's face hotter than its rim, the creases
    between billows cool, a white-yellow core on the camera's line through the fire's middle, broken by the same
    creases. From `hand` the flame is handed back to the sim's own (its grain), so f9 meets f10."""
    N = fl.shape[0]
    h = P["dom"][0] / N
    fs = key(P["fsig"], f)
    Fs = nd.gaussian_filter(fl, fs) if fs > 0 else fl
    chiF = smooth(Fs, *P["chi"])
    chiH = smooth(nd.gaussian_filter(tp, 1.0), *P["hot"]) * key(P["hot_w"], f)
    chi = np.maximum(chiF, chiH).astype(np.float32)
    # Work in the fire's box (a metre of margin).
    nzi = np.argwhere(chi > 0.02)
    pad = int(1.0 / h) + 2
    lo = np.maximum(nzi.min(0) - pad, 0); hi = np.minimum(nzi.max(0) + pad + 1, N)
    sl = tuple(slice(a, b) for a, b in zip(lo, hi))
    c = chi[sl]
    inside = c > 0.5
    sd0 = h * (nd.distance_transform_edt(~inside) - nd.distance_transform_edt(inside)).astype(np.float32)
    sd0 = nd.gaussian_filter(sd0, 0.7)
    ax = [(np.arange(a, b, dtype=np.float32) + 0.5) * h for a, b in zip(lo, hi)]
    X = ax[0][:, None, None] - P["dom"][0] / 2; Y = ax[1][None, :, None] - P["dom"][1] / 2; Z = ax[2][None, None, :]
    idx = np.argwhere(inside)
    cg = ((idx.mean(0) + lo + 0.5) * h - np.array([P["dom"][0] / 2, P["dom"][1] / 2, 0.0])).astype(np.float32)
    pt = np.radians(P["pitch"])
    d = np.array([0.0, np.cos(pt), -np.sin(pt)], np.float32)  # the camera's look
    gx, gy, gz = X - cg[0], Y - cg[1], Z - cg[2]
    gd = gx * d[0] + gy * d[1] + gz * d[2]
    rho = np.sqrt(np.maximum((gx - gd * d[0]) ** 2 + (gy - gd * d[1]) ** 2 + (gz - gd * d[2]) ** 2, 0))
    R = float(np.percentile(rho[inside], 92)) if inside.any() else 1.0
    # Billows on the skin: the band within `band` m of the surface.
    band = np.abs(sd0) < P["band"]
    bi = np.nonzero(band)
    sc = (P["r_ref"] / max(R, 0.3)) ** P["beta"]
    q = np.stack([gx[bi[0], 0, 0], gy[0, bi[1], 0], gz[0, 0, bi[2]]], 1) * sc
    sd = sd0.copy()
    dome = {}; crease = {}
    for k, (s, A, rad, cw) in enumerate(P["billows"]):
        F1, F2 = worley(q + 13.7 * (k + 1), s, tabs[k])
        dome[k] = np.sqrt(np.clip(1 - (F1 / rad) ** 2, 0, 1))
        crease[k] = 1 - smooth(F2 - F1, 0, cw)
        sd[bi] -= A * key(P["bamp"], f) * (dome[k] - 0.5)
    occ = smooth(-sd, -P["edge"], P["edge"]).astype(np.float32)
    depth = np.clip(-sd, 0, None)
    dep = smooth(depth, 0, key(P["deep"], f))
    T = key(P["base"], f) + P["k_depth"] * (dep - 0.5)
    tb = np.zeros_like(sd)
    for k in dome:
        kb, kc = P["k_bill"][k], P["k_crease"][k]
        tb[bi] += kb * (dome[k] - 0.5) - kc * crease[k]
    T = T + tb * key(P["bamp"], f)
    crx = np.zeros_like(sd)
    if crease:
        crx[bi] = np.maximum.reduce([crease[k] for k in crease])
    hr = key(P["heart_m"], f) if "heart_m" in P else key(P["heart_r"], f) * R
    Hc = np.exp(-(rho / max(hr, 1e-3)) ** 2) * (1 - P["heart_crease"] * crx)
    T = T + key(P["heart"], f) * Hc - P["k_rad"] * np.clip(rho / R - P["rad0"], 0, 1)
    T = np.clip(T, 0, 1) * (occ > 0.01)
    # The flame handed back to the sim's own (its grain) from `hand`.
    hb = key(P["hand"], f)
    Fo = Fs.copy()
    Fo[sl] = (1 - hb) * occ + hb * np.maximum(Fs[sl], 0)
    Tf = np.zeros_like(fl); Tf[sl] = T
    # Soot: as version 1 (torn, thin, handed back), on the new shape.
    D = dn
    fade, tear, skin = key(P["fade"], f), key(P["tear"], f), key(P["skin"], f)
    if fade < 1 or tear > 0 or skin > 0:
        G1 = np.zeros_like(fl); G1[sl] = nd.gaussian_filter(occ, key(P["s1"], f) / h)
        Xf = (np.arange(N, dtype=np.float32) + 0.5) * h
        out = 1.0 - smooth(G1, 0.1, 0.6)
        m = (D > 1e-4) | ((G1 > 0.02) & (G1 < 0.6))
        ii = np.nonzero(m)
        rx, ry, rz = Xf[ii[0]] - P["dom"][0] / 2 - cg[0], Xf[ii[1]] - P["dom"][1] / 2 - cg[1], Xf[ii[2]] - cg[2]
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
        bnd = smooth(g_, 0.03, 0.12) * (1 - smooth(g_, 0.3, 0.55))
        dsk = skin * bnd * rag
        # Soot in the billows' creases (thin, from `csoot`).
        cs = key(P["csoot"], f)
        if cs > 0:
            CR = np.zeros_like(fl); CR[sl] = crx * smooth(-sd, -0.02, 0.15) * (1 - smooth(-sd, 0.25, 0.5))
            dsk = np.maximum(dsk, cs * CR[ii])
        D = np.zeros_like(dn)
        D[ii] = din + np.maximum(dout, dsk)
    return Fo.astype(np.float32), (2.0 * Tf).astype(np.float32), D.astype(np.float32), dict(R=R, cg=cg.tolist())


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
    rng = np.random.default_rng(P["seed"] + 100)
    tabs = [rng.uniform(0.08, 0.92, (32, 32, 32, 3)).astype(np.float32) for _ in P.get("billows", ())]
    N = P["res"]
    for f in range(1, last + 1):
        fn = "fluid_data_%04d.vdb" % f
        grids, meta = openvdb.readAll(os.path.join(src, "data", fn))
        G = {g.name: g for g in grids}

        def dense(g):
            a = np.zeros((N, N, N), np.float32); g.copyToArray(a, ijk=(0, 0, 0)); return a
        fl, dn, tp = dense(G["flame"]), dense(G["density"]), dense(G["temperature"])
        if P.get("v") == 2:
            Fn, Tn, Dn, info = regrade2(fl, dn, tp, f, P, cubes, tabs)
        else:
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
