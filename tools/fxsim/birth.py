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


def regrade3(fl, dn, tp, f, P, cubes, tabs):
    """Version 3 (preset b5e, solver 9 after judge 5a): the fire's whole life, not only its birth.
    Shape: the flame (to f5) or the hot gas relative to the frame's own peak (it keeps swelling and rising after the
    flame has broken into grain), its skin pushed by three sizes of cellular dome: big masses (3-4 on the face the
    camera sees), then two finer billows, displacement only (no billow is lit from its own middle: judge 5a 1b's
    bubble wrap). Tongues: a few flame tongues thrust out of the outline early (1c).
    Heat (the fire's colour and light, src_material's birth branch): falls off from the heart (centre hot, outer lobes
    cooler), the folds between the masses cool (deepest low and outside), a white-yellow heart f1-f5 as b5d's.
    Life (1e): every point of the fire has a score (in the masses' folds, deep, near the middle, a noise); a front
    runs up the scores over the frames (thr), so the fire chars from its outer faces inward and sinks into the
    folds, its share of the cloud falling 100 -> 60 -> 30 -> 10%. Charred fire is soot (density), lit by the fire
    still burning near it (its heat grid read by the take's glow), bellies more than tops; the bake's own soot is
    held thin round the fire and handed back by `back`."""
    N = fl.shape[0]
    h = P["dom"][0] / N
    Fs = nd.gaussian_filter(fl, key(P["fsig"], f))
    chiF = smooth(Fs, *P["chi"]) * key(P["flame_w"], f)
    Tg = nd.gaussian_filter(tp, key(P["tsig"], f))
    pk = float(np.percentile(Tg[Tg > 0.3], 99.5)) if (Tg > 0.3).any() else 1.0
    chiH = smooth(Tg / pk, key(P["hrel0"], f), key(P["hrel1"], f))
    chi = np.maximum(chiF, chiH).astype(np.float32)
    nzi = np.argwhere(chi > 0.02)
    if not len(nzi):  # the fire long gone (f45 on): the bake's own soot, held as the frames before it
        z = np.zeros_like(fl)
        return z, z, (dn * key(P["k_out"], f)).astype(np.float32), dict(R=0.0, cg=[0.0, 0.0, 0.0], pk=pk, skin_fire=0.0, thr=0.0)
    pad = int(1.2 / h) + 2
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
    d = np.array([0.0, np.cos(pt), -np.sin(pt)], np.float32)   # the camera's look
    upv = np.array([0.0, np.sin(pt), np.cos(pt)], np.float32)  # up on screen
    gx, gy, gz = X - cg[0], Y - cg[1], Z - cg[2]
    gd = gx * d[0] + gy * d[1] + gz * d[2]
    rho = np.sqrt(np.maximum((gx - gd * d[0]) ** 2 + (gy - gd * d[1]) ** 2 + (gz - gd * d[2]) ** 2, 0))
    R = float(np.percentile(rho[inside], 92)) if inside.any() else 1.0
    sv = gy * upv[1] + gz * upv[2]          # screen-up of each cell from the centre (m)
    band = np.abs(sd0) < P["band"]
    bi = np.nonzero(band)
    sc = (P["r_ref"] / max(R, 0.3)) ** P["beta"]
    q = np.stack([gx[bi[0], 0, 0], gy[0, bi[1], 0], gz[0, 0, bi[2]]], 1) * sc
    sd = sd0.copy()
    creases = []
    amp = key(P["bamp"], f)
    # the cells' walls bent by a smooth noise (else the folds run in straight lines, a cracked plate)
    wq = q * P["warp_f"]
    warp = np.stack([sample(cubes[0], (wq + 3.1 + 7.7 * j).T) - 0.5 for j in range(3)], 1) * 2.0
    for k, (s, A, rad, cw) in enumerate(P["layers"]):
        F1, F2 = worley(q + 13.7 * (k + 1) + warp * P["warp"][k] * s, s, tabs[k])
        dome = np.sqrt(np.clip(1 - (F1 / rad) ** 2, 0, 1))
        creases.append(1 - smooth(F2 - F1, 0, cw))
        sd[bi] -= A * amp * (dome - 0.5)
    # Tongues: thrust out of the outline along a few directions near the screen's plane, pointed (a Laplacian of
    # the angle), each its own length, curling a little as they go.
    tl = key(P["tongue"], f)
    if tl > 0:
        rng = np.random.default_rng(P["seed"] + 300)
        nt = P["tongues"]
        ph = (np.arange(nt) + rng.uniform(0.15, 0.85, nt)) / nt * 2 * np.pi + P["tongue_rot"]
        el = rng.uniform(-0.25, 0.25, nt)   # out of the screen's plane (rad)
        ln = rng.uniform(*P["tongue_len"], nt)
        ex = np.array([1.0, 0.0, 0.0], np.float32)
        p3 = np.stack([gx[bi[0], 0, 0], gy[0, bi[1], 0], gz[0, 0, bi[2]]], 1)
        pr = np.sqrt((p3 * p3).sum(1)) + 1e-6
        for i in range(nt):
            e = np.cos(el[i]) * (np.cos(ph[i]) * ex + np.sin(ph[i]) * upv) + np.sin(el[i]) * (-d)
            # the axis curls with distance from the centre (a turn of `tongue_curl` rad per R)
            tw = P["tongue_curl"] * np.clip(pr / R - 0.6, 0, None) * (1 if i % 2 else -1)
            side = np.cross(e, -d); side /= np.linalg.norm(side)
            ee = np.cos(tw)[:, None] * e[None] + np.sin(tw)[:, None] * side[None]
            cs = (p3 * ee).sum(1) / pr
            th = np.arccos(np.clip(cs, -1, 1))
            sd[bi] -= tl * ln[i] * R * np.exp(-th / P["tongue_w"]) * smooth(cs, 0.5, 0.9)
    occ = smooth(-sd, -P["edge"], P["edge"]).astype(np.float32)
    dep = smooth(np.clip(-sd0, 0, None), 0, P["deep"])
    rr = rho / R
    crM = np.zeros_like(sd); crB = np.zeros_like(sd)
    crM[bi] = creases[0]
    # the billows' borders dark only here and there (a noise picks them), never every cell outlined alike
    msk = [smooth(sample(cubes[1], (q * P["bmask_f"] + 11.3 * (k + 1)).T), 0.38, 0.62) for k in range(len(creases) - 1)]
    if len(creases) > 1:
        crB[bi] = np.maximum.reduce([creases[k + 1] * msk[k] * P["bwt"][k] for k in range(len(creases) - 1)])
    tex = np.zeros_like(sd)
    tex[bi] = sample(cubes[0], (q * P["tex_f"] + 57.0).T) - 0.5
    low = smooth(-sv / R, 0.0, 0.8)
    outw = smooth(rr, 0.3, 0.95)
    foldw = P["fold_in"] + (1 - P["fold_in"]) * np.maximum(low, outw)
    # Birth heat.
    T = (key(P["base"], f) + P["k_depth"] * (dep - 0.5) - key(P["k_rad"], f) * smooth(rr, 0.12, 1.05)
         - key(P["k_fold"], f) * crM * foldw - key(P["k_bcr"], f) * crB * (0.6 + 0.4 * foldw) + P["k_tex"] * tex)
    hr = key(P["heart_m"], f)
    Hc = np.exp(-(rho / max(hr, 1e-3)) ** 2) * (1 - P["heart_crease"] * np.maximum(crM, crB))
    T = T + key(P["heart"], f) * Hc
    # Life: the char front.
    thr = key(P["thr"], f)
    lw = key(P["life_w"], f)
    Fo = occ.copy()
    ch = np.zeros_like(sd)
    if thr > -0.2 or lw > 0:
        # a noise riding the ball (in its own scaled frame, as the billows), climbing a little
        qq = np.stack(np.broadcast_arrays(gx, gy, gz), 0).reshape(3, -1) * sc * P["ch_noise"]
        nzv = sample(cubes[1], qq + 31.0).reshape(sd.shape)
        # The front: a score on the skin (folds, the middle, low, a noise) ranked, so the share of the skin still
        # burning is about 1 - thr; past it the char reaches inward (ch_rate m per unit of score), so the fire under
        # charred skin is hidden, not glowing through a film.
        score = (P["w_fold"] * crM + P["w_bill"] * crB + P["w_mid"] * (1 - np.clip(rr, 0, 1))
                 + P["w_low"] * low + P["w_noise"] * (nzv - 0.5))
        surf = (occ > 0.3) & (np.abs(sd) < P["ch_skin"])
        ss = np.sort(score[surf])
        if ss.size > 100:
            srank = np.interp(score, ss, np.linspace(0, 1, ss.size)).astype(np.float32)
            zc = P["ch_rate"] * (thr - srank) + P["ch_d0"]
            ch = smooth(zc - np.clip(-sd, 0, None), -P["ch_w"], P["ch_w"]) * (occ > 0.01)
        Fo = occ * (1 - ch)
        # the fire still burning: its own heat, bright to the end (0.7-0.85 on screen), cooling at the front
        Tl = (key(P["life_T"], f) + P["life_fold"] * crM - P["life_rad"] * smooth(rr, 0.3, 1.0)
              + P["life_noise"] * (nzv - 0.5))
        T = (1 - lw) * T + lw * Tl
        T = T - P["front_cool"] * smooth(ch, 0.0, 1.0)
    T = np.clip(T, 0, 1) * (occ > 0.01)
    # The soot's light: the fire burning near it (a blur of the fire's heat), bellies more than tops.
    D = dn.copy()
    Dbox = D[sl]
    tin = smooth(nd.gaussian_filter(occ, 0.25 / h), 0.15, 0.6)   # inside the fire's cloud
    dch = key(P["dch"], f)
    kin, kout = key(P["k_in"], f), key(P["k_out"], f)
    # the charred soot lumpy, not a smooth shell: its density broken by a finer noise riding the ball
    qs = np.stack(np.broadcast_arrays(gx, gy, gz), 0).reshape(3, -1) * sc * P["stex_f"]
    stex = sample(cubes[0], qs + 77.0).reshape(sd.shape)
    Dnew = Dbox * (kin * tin + kout * (1 - tin)) + dch * ch * occ * (1 - P["stex"] + 2 * P["stex"] * stex)
    # early: the thrown soot born torn (as b5d), outside the fire
    tear = key(P["tear"], f)
    if tear > 0:
        m = Dbox > 1e-4
        ii = np.nonzero(m)
        rx, ry, rz = gx[ii[0], 0, 0], gy[0, ii[1], 0], gz[0, 0, ii[2]]
        r3 = np.sqrt(rx * rx + ry * ry + rz * rz) + 1e-6
        ua = np.stack([rx / r3, ry / r3, rz / r3]) * P["ka"]
        ub = np.stack([rx, ry, rz]) / R * P["kb"]
        wisp = smooth(0.5 * sample(cubes[0], ua + 17.0) + 0.5 * sample(cubes[1], ub + 5.0), P["tear_th"] - 0.08, P["tear_th"] + 0.08)
        o_ = 1 - tin[ii]
        Dnew[ii] = Dnew[ii] * (1 - o_ * tear * (1 - wisp))
    sootl = np.zeros_like(sd)
    gk = P["glow_k"]
    if key(P["lsoot"], f) > 0:
        hot = Fo * smooth(T, 0.55, 0.85)
        Lf = nd.gaussian_filter(hot, P["l_sig"] / h)
        Lf = np.clip(Lf / P["l_ref"], 0, 1) ** P["l_pow"]
        under = smooth(-gz / max(R, 0.3), -0.7, 0.7)
        Ls = (key(P["lsoot"], f) * Lf * (P["l_top"] + (1 - P["l_top"]) * under) * (0.7 + 0.6 * stex)
              + key(P["lmin"], f))
        sootl = np.sqrt(np.clip(Ls / gk, 0, 1))
    # The heat grid: the fire's own heat where it burns, the soot's light where it has charred.
    Tw = np.where(Fo > 0.05, (1 - ch) * T + ch * sootl, sootl * (Dnew > 1e-3))
    Fout = np.zeros_like(fl); Fout[sl] = Fo
    Tf = np.zeros_like(fl); Tf[sl] = Tw
    D = np.zeros_like(dn) if key(P["clear_out"], f) > 0 else dn * key(P["k_far"], f)
    D[sl] = Dnew
    fire_vis = float(((Fo > 0.5) & (np.abs(sd) < 0.12)).sum()) / max(float(((occ > 0.5) & (np.abs(sd) < 0.12)).sum()), 1)
    return Fout.astype(np.float32), (2.0 * Tf).astype(np.float32), D.astype(np.float32), dict(
        R=R, cg=cg.tolist(), pk=pk, skin_fire=fire_vis, thr=thr)


PRESETS["b5e"] = dict(
    PRESETS["b5c"], v=3,
    fsig=((1, 0.6), (3, 1.0), (4, 1.6), (48, 1.6)), chi=(0.05, 0.35),
    flame_w=((1, 1.0), (5, 1.0), (8, 0.0)),
    tsig=((1, 1.0), (48, 1.4)), hrel0=((1, 0.50), (6, 0.50), (12, 0.53), (17, 0.56), (22, 0.58), (48, 0.60)),
    hrel1=((1, 0.73), (6, 0.73), (12, 0.75), (17, 0.78), (22, 0.80), (48, 0.82)),
    band=0.8, r_ref=2.2, beta=1.0, edge=0.06, deep=0.5,
    # (spacing m, displacement m, dome radius, crease width): big masses, then two billow sizes; their walls bent
    layers=((2.3, 0.55, 0.9, 0.16), (0.75, 0.24, 0.85, 0.22), (0.32, 0.10, 0.85, 0.20)),
    bwt=(1.0, 0.6), bmask_f=4.0, tex_f=22.0, k_tex=0.05,
    warp=(0.35, 0.3, 0.3), warp_f=3.3,
    bamp=((1, 0.7), (2, 1.0), (48, 1.0)),
    tongue=((1, 0.0), (1.6, 0.6), (2.5, 1.0), (4.5, 1.0), (6, 0.4), (7, 0.0)), tongues=5, tongue_rot=0.4,
    tongue_len=(0.38, 0.52), tongue_w=0.085, tongue_curl=0.35,
    base=((1, 0.88), (2, 0.88), (3, 0.85), (6, 0.85), (9, 0.84)), k_depth=0.12,  # (lead 7: 0.88 f3-6, light budget)
    k_rad=((1, 0.13), (6, 0.13), (9, 0.10)),
    fold_in=0.45, k_fold=((1, 0.30), (6, 0.30), (8, 0.12), (10, 0.0)), k_bcr=((1, 0.12), (4, 0.12), (6, 0.08), (8, 0.04), (10, 0.0)),
    heart=((1, 0.55), (2, 0.60), (3, 0.55), (4, 0.28), (5, 0.15), (6, 0.04), (7, 0.0)),  # (lead 7: knee, was 0.50/0.42)
    heart_m=((1, 1.0), (2, 1.15), (3, 1.5), (4, 1.1), (5, 0.8), (6, 0.55), (7, 0.5)), heart_crease=0.6,
    # life: the char front over the skin's ranked scores (the share of the skin still burning ~ 1 - thr), reaching
    # ch_rate m inward per unit of score past it
    thr=((1, -0.3), (6, -0.1), (7, 0.0), (9, 0.3), (12, 0.48), (17, 0.78), (22, 1.0), (26, 1.15), (30, 1.6), (36, 3.0)),
    life_w=((1, 0.0), (6, 0.0), (10, 1.0)),
    w_fold=0.35, w_bill=0.06, w_mid=0.30, w_low=0.10, w_noise=0.55, ch_noise=6.0,
    ch_skin=0.14, ch_w=0.05, ch_rate=1.2, ch_d0=0.0,
    life_T=((6, 0.80), (14, 0.80), (22, 0.80), (30, 0.78)), life_fold=0.05, life_rad=0.14,  # (lead 7: the birth's falloff kept; was 0.82-0.84, 0.06) life_noise=0.06,
    front_cool=0.25,
    # soot
    stex=0.45, stex_f=14.0,
    dch=((1, 0.0), (6, 0.0), (7, 0.2), (9, 0.3), (30, 0.3), (40, 0.12)),
    k_in=((1, 1.0), (6, 0.6), (14, 0.5), (30, 0.6), (40, 0.8)), k_out=((1, 0.6), (6, 0.35), (17, 0.35), (30, 0.6), (40, 0.9)),
    k_far=((1, 0.5), (14, 0.5), (30, 0.7), (40, 0.9)), clear_out=((1, 0.0),),
    tear=((1, 1.0), (6, 1.0), (9, 0.4), (12, 0.0)),
    glow_k=1.0, lsoot=((1, 0.0), (6, 0.0), (9, 0.09), (20, 0.08), (28, 0.03), (34, 0.0)),
    lmin=((1, 0.0), (8, 0.004), (24, 0.004), (32, 0.0)), l_sig=0.45, l_ref=0.35, l_pow=0.8, l_top=0.35,
)


def main():
    src, dst = sys.argv[1], sys.argv[2]
    av = sys.argv[3:]
    preset = av[av.index("--preset") + 1] if "--preset" in av else "b5c"
    last = int(av[av.index("--last") + 1]) if "--last" in av else 9
    only = [int(v) for v in av[av.index("--frames") + 1].split(",")] if "--frames" in av else None
    P = PRESETS[preset]
    for sub in ("config", "data", "guiding", "mesh", "noise", "particles"):
        os.makedirs(os.path.join(dst, sub), exist_ok=True)
    for sub in ("config", "data"):
        for fn in sorted(os.listdir(os.path.join(src, sub))):
            s_, d_ = os.path.join(src, sub, fn), os.path.join(dst, sub, fn)
            fr = int(fn.split("_")[-1].split(".")[0])
            if sub == "data" and (fr in only if only else fr <= last):
                continue
            if os.path.exists(d_):
                os.remove(d_)
            try:
                os.link(s_, d_)
            except OSError:
                shutil.copy2(s_, d_)
    cubes = [noise_cube(96, P["seed"], 2.0), noise_cube(96, P["seed"] + 1, 2.5)]
    rng = np.random.default_rng(P["seed"] + 100)
    tabs = [rng.uniform(0.08, 0.92, (32, 32, 32, 3)).astype(np.float32) for _ in P.get("layers", P.get("billows", ()))]
    N = P["res"]
    for f in (only or range(1, last + 1)):
        fn = "fluid_data_%04d.vdb" % f
        grids, meta = openvdb.readAll(os.path.join(src, "data", fn))
        G = {g.name: g for g in grids}

        def dense(g):
            a = np.zeros((N, N, N), np.float32); g.copyToArray(a, ijk=(0, 0, 0)); return a
        fl, dn, tp = dense(G["flame"]), dense(G["density"]), dense(G["temperature"])
        if P.get("v") == 3:
            Fn, Tn, Dn, info = regrade3(fl, dn, tp, f, P, cubes, tabs)
        elif P.get("v") == 2:
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
              "soot sum %.0f -> %.0f" % (dn.sum(), Dn.sum()),
              ("hot-gas peak %.2f, skin burning %.0f%% (thr %.2f)" % (info["pk"], 100 * info["skin_fire"], info["thr"])
               if "pk" in info else ""), flush=True)
    print("BIRTH done", dst)


main()
