"""Her ear lobes in each face's paint: the lobe in the ear's own tone, and the second lobe painted on her neck under
it taken out.

Her head's lobe is a solid one, fused to her neck: a rounded lower edge and a flat underside about 1.5 cm deep over
her neck (y 1.707 m), its front merging into her cheek. heroine_ears.py brought her ears to her cheek's tone, but its
reach (EAR_R about the ear's middle) stops above the lobe's lower half and underside, which kept the base head's
paint, pale and grey: at 40 degrees and in play every face's lobe read as a flat cream-white tab with a hard edge (the
owner, 13 October 2026). And five faces' paints (Sunborn, Moonlit, Saffron, Fey, Vixen) carry their portrait's own
lobe, drawn 1-2 cm lower than her head's, as a crescent on her neck under the real one (a ghost lobe), its lower edge
a dark line at y 1.689-1.697.

This works on her head's surface, not its UV islands: each texel near her ears is given its point on her head (the
glb's skin_head), and tones are smoothed over her surface in 3D (normalized convolution on a 0.3 mm grid), so no seam
of the UV layout shows. Per face, per ear, in linear light:
  lobe:  only what stands out of her head there: seen from the side, the outline where her outer surface stands
         3-6 mm proud of the skin round it (a robust fit of that skin), and in it whatever lies 0.5-3 mm or more
         above that skin (the lobe's face, its rounded edge and its underside, not the neck hidden under it). Its
         texels' fine grain (paint over the 3D smoothing at SIGMA) laid on the median tone of the ear just above it
         (fully inside heroine_ears.py's reach), UNDER deeper on its underside towards the crease (0: heroine_ao.png
         already shades the crease and underside 5-10%, and the paint's own shade there read as a warm smudge);
  neck:  the skin round and under the lobe, down past the ghost's edge: a smooth fill (a quadratic in height and
         depth fitted, robustly, to the skin round the patch, plus that skin's own departures from it carried in
         over about 4 mm, so the fill meets it without a step), with grain taken from her neck SHIFT lower (folded
         back above FLOOR), clear of the ghost: the patch's own grain carried the ghost's 1 mm dark edge through.
The lobe is laid over the neck (each its soft weight), so no hard boundary falls between them.
Idempotent: a rerun finds the lobe and the neck already laid, and no tab left, and writes nothing.

    python tools/assets/heroine_lobe.py [--from DIR] [face ...]   (no faces: all ten paints in godot/art/people/head_tex)

--from DIR lays the texels this takes (its BOX, both sides, and their padding) again from DIR's paints (e.g. the
paints before this), keeping head_tex's paint everywhere else, and writes to head_tex; then rerun heroine_concha.py
(its bowl reaches into BOX). Last, the old tab's whole footprint (tab(): what the lobe and the neck leave paler than
both the lobe and her cheek, its front-bottom corner and underside) is filled from the skin round it. Run after
heroine_ears.py (and its --render pass), which sets the ear's tone this takes. Touches nothing above y 1.722 m, in
front of z 0.012 m or behind z -0.044 m, nor further in than 3 cm from her middle.
"""
import os
import re
import sys

import numpy as np
from PIL import Image
from scipy import ndimage, sparse
from scipy.sparse.linalg import splu
from scipy.spatial import cKDTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import heroine_seam as hs  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TEX = os.path.join(ROOT, "godot", "art", "people", "head_tex")
GLB = os.path.join(ROOT, "godot", "art", "people", "heroine.glb")
VOX = 0.0003                                # (the 3D grid, metres)
SIGMA = 0.0006                              # (grain finer than this is kept, coarser is the tone laid)
UNDER = 0.0                                 # (the lobe's underside this much deeper towards the crease)
PAD = 12                                    # (texels of the UV islands' padding given their island's change)
SHIFT = 0.030                               # (the neck's grain comes from this far down her neck,
FLOOR = 1.640                               #  folded back above this: her head ends at y 1.628)
EAR = (0.076, 1.735, -0.018)                # (heroine_ears.py's)
EAR_R = (0.026, 0.034)
G = 0.0005                                  # (the side outline's grid)
BOX = (0.020, 1.626, 1.736, -0.072, 0.026)  # (the texels taken: |x| over, y and z between)
REACH = 0.009                               # (the old tab's footprint: pale texels within this of the lobe's core,
Y_TOP = (1.720, 1.724)                      #  under the ear: all of it below the first, none above the second;
LIFT = 0.006                                #  this higher in front of her tragus, z over 0.004, where the bowl's
                                            #  tone (heroine_concha.py) doesn't reach)
PALE = 0.010                                # (paler than both the lobe's tone and her cheek's by this, Oklab L, in
                                            #  the paint smoothed at SIGMA)
EASE = (0.0006, 0.0016)                     # (the fill: all of it within the first of a pale texel, eased out by the second)
CHEEK = (0.012, 0.022, 1.700, 1.716, 0.05)  # (her cheek in front of the lobe: z between, y between, |x| over)
GUTTER = 16                                 # (texels of the UV islands' padding given the footprint's fill)

M1 = np.array([[0.4122214708, 0.5363325363, 0.0514459929], [0.2119034982, 0.6806995451, 0.1073969566],
               [0.0883024619, 0.2817188376, 0.6299787005]])
M2L = np.array([0.2104542553, 0.7936177850, -0.0040720468])


def lin(c): return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
def srgb(c): return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(np.clip(c, 0, None), 1 / 2.4) - 0.055)
def ok_l(c): return np.cbrt(np.clip(c, 0, None) @ M1.T) @ M2L          # (Oklab lightness of linear sRGB)


def smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def head():
    js, binc = hs._load(GLB)
    mats = [m.get("name") for m in js["materials"]]
    prim = next(p for m in js["meshes"] for p in m["primitives"] if mats[p["material"]] == "skin_head")
    P = hs._read(js, binc, prim["attributes"]["POSITION"])
    N = hs._read(js, binc, prim["attributes"]["NORMAL"])
    UV = hs._read(js, binc, prim["attributes"]["TEXCOORD_0"])
    T = hs._read(js, binc, prim["indices"]).astype(np.int64).reshape(-1, 3)
    return P, N, UV, T


def inbox(q, side):
    ax0, y0, y1, z0, z1 = BOX
    return (q[..., 0] * side > ax0) & (q[..., 1] > y0) & (q[..., 1] < y1) & (q[..., 2] > z0) & (q[..., 2] < z1)


def texels(P, N, UV, T, side, size):
    """Every texel of the triangles in BOX on one side: (row, col) and its point and normal on her head."""
    tri = T[inbox(P[T], side).any(1)]
    U = UV * size
    rows, cols, pos, nrm = [], [], [], []
    for t in tri:
        a, b, cc = U[t]
        x0, y0 = np.maximum(np.floor(U[t].min(0)).astype(int), 0)
        x1, y1 = np.minimum(np.ceil(U[t].max(0)).astype(int), size - 1)
        if x1 < x0 or y1 < y0:
            continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
        q = np.stack([xs.ravel() + 0.5, ys.ravel() + 0.5], 1)
        v0, v1, v2 = b - a, cc - a, q - a
        den = v0[0] * v1[1] - v1[0] * v0[1]
        if abs(den) < 1e-12:
            continue
        vv = (v2[:, 0] * v1[1] - v1[0] * v2[:, 1]) / den
        ww = (v0[0] * v2[:, 1] - v2[:, 0] * v0[1]) / den
        bb = np.stack([1 - vv - ww, vv, ww], 1)
        m = (bb > -1e-3).all(1)
        rows.append(ys.ravel()[m]); cols.append(xs.ravel()[m])
        pos.append(bb[m] @ P[t]); nrm.append(bb[m] @ N[t])
    rows, cols = np.concatenate(rows), np.concatenate(cols)
    key = rows * size + cols
    _, first = np.unique(key, return_index=True)
    pos, nrm = np.concatenate(pos)[first], np.concatenate(nrm)[first]
    nrm /= np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-9)
    keep = inbox(pos, side)
    return rows[first][keep], cols[first][keep], pos[keep], nrm[keep]


def covered(UV, T, size, box):
    """Texels any triangle of her head covers, in box (x0, y0, x1, y1): the rest is the islands' padding."""
    x0, y0, x1, y1 = box
    U = UV * size
    lo, hi = U[T].min(1), U[T].max(1)
    sel = T[(hi[:, 0] >= x0) & (lo[:, 0] <= x1) & (hi[:, 1] >= y0) & (lo[:, 1] <= y1)]
    cov = np.zeros((y1 - y0, x1 - x0), bool)
    for t in sel:
        a, b, cc = U[t] - [x0, y0]
        xa, ya = np.maximum(np.floor(np.min([a, b, cc], 0)).astype(int), 0)
        xb, yb = np.minimum(np.ceil(np.max([a, b, cc], 0)).astype(int), [x1 - x0 - 1, y1 - y0 - 1])
        if xb < xa or yb < ya:
            continue
        xs, ys = np.meshgrid(np.arange(xa, xb + 1), np.arange(ya, yb + 1))
        q = np.stack([xs.ravel() + 0.5, ys.ravel() + 0.5], 1)
        v0, v1, v2 = b - a, cc - a, q - a
        den = v0[0] * v1[1] - v1[0] * v0[1]
        if abs(den) < 1e-12:
            continue
        vv = (v2[:, 0] * v1[1] - v1[0] * v2[:, 1]) / den
        ww = (v0[0] * v2[:, 1] - v2[:, 0] * v0[1]) / den
        m = (vv > -0.02) & (ww > -0.02) & (vv + ww < 1.02)
        cov[ys.ravel()[m], xs.ravel()[m]] = True
    return cov


def skin_fit(pos, side):
    """The lobe's outline seen from the side: on a G grid in (y, z), the outermost |x| (F) against a robust lower
    quadratic fit of it (the skin round the lobe, B); returns the 'stands proud' weight per texel and B per texel."""
    ax, y, z = pos[:, 0] * side, pos[:, 1], pos[:, 2]
    ny, nz = 80, 120                              # (y 1.690-1.730, z -0.040-0.020)
    s = (y > 1.690) & (y < 1.730) & (z > -0.040) & (z < 0.020)
    iy, iz = ((y[s] - 1.690) / G).astype(int), ((z[s] + 0.040) / G).astype(int)
    F = np.full((ny, nz), -1.0)
    np.maximum.at(F, (iy, iz), ax[s])
    ok = F > 0
    gy, gz = np.meshgrid(1.690 + G * (np.arange(ny) + 0.5), -0.040 + G * (np.arange(nz) + 0.5), indexing="ij")

    def basis(yy, zz):
        yy, zz = yy - 1.71, zz + 0.01
        return np.stack([np.ones_like(yy), yy, zz, yy * yy, yy * zz, zz * zz], -1)
    A = basis(gy[ok], gz[ok])
    w = np.ones(ok.sum())
    for _ in range(10):
        coef = np.linalg.lstsq(A * w[:, None], F[ok] * w, rcond=None)[0]
        r = F[ok] - A @ coef
        w = np.where(r > 0.0025, 0.0, np.where(r > 0.0012, 0.3, 1.0))
    D = np.zeros((ny, nz))
    D[ok] = r
    D = ndimage.grey_closing(D, size=3)            # (fill the odd empty cell inside the outline)
    # (the lobe alone: the outline's one piece that holds the lobe (its proudest cell over y 1.700-1.722, z -0.020 to
    # 0.005). Ungated, her jaw in front of it and her neck behind stood proud of the fit at the grid's corners and took
    # the ear's tone as hard-edged tabs: the orange patch on her jaw at the Look's 80 degrees, judge rj5v, 13 October)
    lab, _ = ndimage.label(D > 0.003)
    win = (gy > 1.700) & (gy < 1.722) & (gz > -0.020) & (gz < 0.005)
    pick = lab[win][np.argmax(np.where(lab[win] > 0, D[win], -1.0))] if (win & (lab > 0)).any() else -1
    zone = ndimage.gaussian_filter(smooth(0.003, 0.006, D) * ndimage.binary_dilation(lab == pick, iterations=2), 1.0)
    zp = ndimage.map_coordinates(zone, [(y - 1.690) / G - 0.5, (z + 0.040) / G - 0.5], order=1, mode="constant")
    return zp, basis(y, z) @ coef


def masks(pos, nrm, side):
    ax, y, z = pos[:, 0] * side, pos[:, 1], pos[:, 2]
    nx = nrm[:, 0] * side
    zone, B = skin_fit(pos, side)
    # the lobe: inside its outline and standing off the skin; eased into heroine_ears.py's ear at its top
    lobe = zone * smooth(B + 0.0005, B + 0.0030, ax) * (1 - smooth(1.716, 1.722, y))
    # (standing off that skin: its fit holds over y 1.690-1.730, and only matters by the lobe)
    proud = smooth(B + 0.0015, B + 0.0035, ax) * smooth(1.696, 1.700, y)
    # the neck round and under it, down past the ghost's edge, at the skin (not the lobe standing off it)
    neck = smooth(1.664, 1.672, y) * (1 - smooth(1.704, 1.712, y)) * smooth(-0.044, -0.036, z) \
        * (1 - smooth(0.004, 0.012, z)) * smooth(0.030, 0.036, ax) * (1 - proud) * smooth(0.0, 0.2, nx)
    d = np.linalg.norm(np.c_[ax, y, z] - np.array(EAR), axis=1)
    ear = (1 - smooth(EAR_R[0], EAR_R[1], d)) * smooth(0.062, 0.067, ax)
    # (clear of the ear's bowl, which heroine_concha.py tones after this: taken in, a rerun after it found a darker tone)
    ref = (ear > 0.95) & (y > 1.719) & (y < 1.730) & (nx > 0.3) \
        & (np.linalg.norm(np.c_[ax, y, z] - np.array((0.070, 1.729, -0.006)), axis=1) > 0.016)
    ring = (neck == 0) & (lobe == 0) & (ear < 0.02) & (ax > 0.028) & (y > 1.652) & (y < 1.722) & (z > -0.054) \
        & (z < 0.022) & (nx > 0.2) & (proud == 0)
    return lobe, neck, ref, ring


def near(pos, side, lobe):
    """The texels the old tab's footprint can take: within REACH of the lobe's core (and EASE past it, and 2 mm of
    skin round that to hold its fill), under the ear. Returns their indices, their distance to the lobe's core,
    their neighbours on her surface (each texel's 6 nearest in 3D, so no UV seam cuts the fill) and her cheek."""
    core = lobe > 0.9
    d = cKDTree(pos[core]).query(pos, distance_upper_bound=REACH + EASE[1] + 0.002)[0]
    ci = np.flatnonzero(np.isfinite(d) & (pos[:, 1] < Y_TOP[1] + LIFT + EASE[1] + 0.001))
    nb = cKDTree(pos[ci]).query(pos[ci], 7)[1][:, 1:]
    n = len(ci)
    A = sparse.coo_matrix((np.ones(nb.size), (np.repeat(np.arange(n), 6), nb.ravel())), shape=(n, n)).tocsr()
    A = ((A + A.T) > 0).astype(np.float64).tocsr()
    ax = pos[:, 0] * side
    ck = (pos[:, 2] > CHEEK[0]) & (pos[:, 2] < CHEEK[1]) & (pos[:, 1] > CHEEK[2]) & (pos[:, 1] < CHEEK[3]) & (ax > CHEEK[4])
    return ci, d[ci], A, ck


def tab(pos, sm, new, grain, tone, lobe, neck, nr):
    """The old tab's whole footprint, filled. The lobe's outline (masks' zone) stops short of its front and lower
    rim, where it turns into her cheek and under onto her neck (merging, not proud), so there it kept the base head's
    pale paint: a cream corner at the front-bottom of every lobe (judge rj5v, 13 October 2026). Taken: every texel
    within REACH of the lobe's core, not laid by the lobe or the neck, whose paint (smoothed at SIGMA) is paler than
    both the lobe's tone and her cheek's (by PALE), and EASE round it. Its fill draws only on the skin round it that
    isn't pale: a membrane (each texel the mean of its neighbours on her surface) held to that skin's paint smoothed
    at SIGMA, so the lobe's tone runs on into her cheek's and her neck's with no edge; and the paint's own grain, at
    her cheek's strength (the old paint's carried the cream's edge and lines at 4-6 times it). Returns the fill's
    weight and values on near()'s texels, and how many were pale."""
    ci, dc, A, ck = nr
    p = pos[ci]
    y = p[:, 1] - LIFT * smooth(0.002, 0.004, p[:, 2])
    thr = max(float(ok_l(tone)), float(np.median(ok_l(sm[ck])))) + PALE
    pale = (ok_l(sm[ci]) > thr) & (dc < REACH) & (lobe[ci] < 0.97) & (neck[ci] < 0.97) & (y < Y_TOP[1])
    if not pale.any():
        return np.zeros(len(ci)), new[ci], 0, 0.0
    dp = cKDTree(p[pale]).query(p, distance_upper_bound=EASE[1] + 1e-4)[0]
    w = (1 - smooth(EASE[0], EASE[1], np.minimum(dp, 1.0))) * (1 - smooth(Y_TOP[0], Y_TOP[1], y)) \
        * (1 - smooth(0.97, 0.995, lobe[ci]))
    ui, ki = np.flatnonzero(w > 0), np.flatnonzero(w == 0)
    held = smoothed(p, new[ci], SIGMA, (w == 0).astype(float))[0]
    far = smoothed(p, new[ci], 0.003, (w == 0).astype(float), vox=0.001)[0]
    eps = 1e-4                                   # (only matters to a part cut off from the skin round it)
    deg = np.asarray(A.sum(1)).ravel()
    M = (sparse.diags(deg[ui] + eps) - A[ui][:, ui]).tocsc()
    rhs = A[ui][:, ki] @ held[ki] + eps * far[ui]
    lu = splu(M)
    fill = new[ci].copy()
    fill[ui] = np.stack([lu.solve(rhs[:, ch]) for ch in range(3)], 1)
    lg = np.log(np.maximum(grain, 1e-3))
    luma = lambda a: a @ np.array([0.2126, 0.7152, 0.0722])
    k = min(1.0, float(np.std(luma(lg[ck])) / max(np.std(luma(lg[ci][w > 0.5])), 1e-6)))
    return w, fill * np.exp(lg[ci] * k), int(pale.sum()), k


def smoothed(pos, val, sigma=SIGMA, wt=None, vox=VOX):
    """val smoothed over her surface: splat onto a 3D grid, Gaussian sigma, normalized, read back (trilinear).
    With wt, a weighted normalized convolution; also returns the weight's own smoothing."""
    lo = pos.min(0) - 4 * sigma
    g = ((pos - lo) / vox)
    shape = np.ceil(g.max(0)).astype(int) + 2
    idx = np.floor(g).astype(int)
    flat = np.ravel_multi_index(idx.T, shape)
    s = sigma / vox
    w = np.ones(len(pos)) if wt is None else wt
    out = np.zeros_like(val)
    acc_w = ndimage.gaussian_filter(np.bincount(flat, w, np.prod(shape)).reshape(shape).astype(np.float32), s)
    wv = ndimage.map_coordinates(acc_w, g.T - 0.5, order=1, mode="nearest")
    for ch in range(val.shape[1]):
        acc = ndimage.gaussian_filter(np.bincount(flat, val[:, ch] * w, np.prod(shape)).reshape(shape).astype(np.float32), s)
        out[:, ch] = ndimage.map_coordinates(acc, g.T - 0.5, order=1, mode="nearest") / np.maximum(wv, 1e-6)
    return (out, wv) if wt is not None else out


def fill(pos, val, sel):
    """A smooth tone for the neck: per channel a quadratic in height and depth, fitted to sel, outliers (moles,
    freckles, the ghost's own edge) reweighted away; plus sel's own departures from it, carried in over ~4 mm (a
    normalized convolution, eased out where sel is far), so the fill meets the skin round it without a step."""
    y, z = pos[:, 1] - 1.69, pos[:, 2] + 0.01
    A = np.c_[np.ones_like(y), y, z, y * y, y * z, z * z]
    out = np.zeros_like(val)
    wts = np.ones(sel.sum())
    for ch in range(val.shape[1]):
        w = np.ones(sel.sum())
        for _ in range(6):
            coef = np.linalg.lstsq(A[sel] * w[:, None], val[sel, ch] * w, rcond=None)[0]
            r = val[sel, ch] - A[sel] @ coef
            sd = 1.4826 * np.median(np.abs(r)) + 1e-6
            w = 1 / np.maximum(1, np.abs(r) / (2 * sd))
        out[:, ch] = A @ coef
        wts = np.minimum(wts, w)
    wt = np.zeros(len(pos))
    wt[sel] = wts
    res, wv = smoothed(pos, val - out, 0.004, wt, vox=0.001)
    full = np.percentile(wv[sel], 95)
    return out + res * np.clip(wv / (0.5 * full), 0, 1)[:, None]


def grain_source(pos, nrm, side, lobe, neck):
    """For each texel, the texel SHIFT lower on her neck (folded above FLOOR) whose grain it takes."""
    q = pos.copy()
    q[:, 1] -= SHIFT
    q[:, 1] = np.where(q[:, 1] < FLOOR, 2 * FLOOR - q[:, 1], q[:, 1])
    src = (pos[:, 1] < 1.686) & (lobe == 0) & (nrm[:, 0] * side > 0.0)
    ids = np.flatnonzero(src)
    _, nn = cKDTree(pos[ids]).query(q)
    return ids[nn]


def run(faces, src_dir):
    P, N, UV, T = head()
    paints = {"own": "heroine_head.jpg"}
    for f in os.listdir(TEX):
        m = re.fullmatch(r"heroine_head_(\w+)\.jpg", f)
        if m: paints[m.group(1)] = f
    cache = {}
    for face in faces or sorted(paints):
        path = os.path.join(TEX, paints[face])
        cur = np.asarray(Image.open(path).convert("RGB")).astype(np.float64) / 255
        im = np.asarray(Image.open(os.path.join(src_dir or TEX, paints[face])).convert("RGB")).astype(np.float64) / 255
        size = im.shape[0]
        L = lin(im)
        out = lin(cur)
        notes, laid = [], True
        for side in (-1, 1):
            if (side, size) not in cache:
                r, c, pos, nrm = texels(P, N, UV, T, side, size)
                mk = masks(pos, nrm, side)
                nr = near(pos, side, mk[0])
                # (with --from, every texel this takes is laid again from DIR, so its box is all of them)
                ch = np.ones(len(r), bool) if src_dir else (mk[0] > 0) | (mk[1] > 0)
                ch[nr[0]] = True
                box = (max(c[ch].min() - GUTTER - 2, 0), max(r[ch].min() - GUTTER - 2, 0),
                       min(c[ch].max() + GUTTER + 3, size), min(r[ch].max() + GUTTER + 3, size))
                gs = grain_source(pos, nrm, side, mk[0], mk[1])
                cache[side, size] = (r, c, pos, nrm, mk, box, covered(UV, T, size, box), gs, nr)
            r, c, pos, nrm, (lobe, neck, ref, ring), box, cov, gs, nr = cache[side, size]
            v = L[r, c]
            sm = smoothed(pos, v)
            grain = v / np.maximum(sm, 1e-4)
            # the lobe: the ear's tone, its own grain (UNDER deeper where it turns down into the crease)
            tone = np.median(v[ref], 0)
            down = smooth(0.25, 0.9, -nrm[:, 1]) * (1 - smooth(0.062, 0.072, pos[:, 0] * side))
            lobe_v = tone * (1 - UNDER * down)[:, None] * grain
            # the neck round and under it: a smooth fill from the skin round the patch, grain from lower down
            neck_v = fill(pos, sm, ring) * grain[gs]
            core_l, core_n = (lobe > 0.97) & (down < 0.05), neck > 0.97
            laid &= bool(np.all(np.abs(np.median(v[core_l], 0) / tone - 1) < 0.02)) \
                and bool(np.median(np.abs(v[core_n] / neck_v[core_n] - 1)) < 0.01)
            mid = v + (neck_v - v) * neck[:, None]
            new = mid + (lobe_v - mid) * lobe[:, None]
            # the old tab's footprint: what the lobe and the neck leave paler than both the lobe and her cheek, filled
            # from the skin round it (tab())
            ci = nr[0]
            w, tab_v, npale, k = tab(pos, sm, new, grain, tone, lobe, neck, nr)
            laid &= npale < 200                   # (a rerun finds at most a few borderline texels at the threshold)
            new[ci] += (tab_v - new[ci]) * w[:, None]
            out[r, c] = new
            # (the islands' padding round what changed takes its nearest texel's change, so no old tone bleeds
            # back in through the mipmaps at a distance; round the footprint, its fill itself, GUTTER texels out)
            x0, y0, x1, y1 = box
            ratio = np.ones((y1 - y0, x1 - x0, 3))
            ib = (r >= y0) & (r < y1) & (c >= x0) & (c < x1)
            ratio[r[ib] - y0, c[ib] - x0] = out[r[ib], c[ib]] / np.maximum(L[r[ib], c[ib]], 1e-5)
            mine, foot = np.zeros((y1 - y0, x1 - x0), bool), np.zeros((y1 - y0, x1 - x0), bool)
            mine[r[ib] - y0, c[ib] - x0] = True
            wt = np.zeros(len(r)); wt[ci] = w
            fb = ib & (wt > 0)
            foot[r[fb] - y0, c[fb] - x0] = True
            dist, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
            sub = out[y0:y1, x0:x1]
            pad = (~cov) & (dist <= PAD) & mine[iy, ix]
            sub[pad] = L[y0:y1, x0:x1][pad] * ratio[iy[pad], ix[pad]]
            gut = (~cov) & (dist <= GUTTER) & foot[iy, ix]
            sub[gut] = sub[iy[gut], ix[gut]]
            notes.append("ear %+d: tone %s, lobe %d texels, neck %d, tab %d pale, %d filled (grain x%.2f)" % (
                side, np.round(srgb(tone), 3), (lobe > 0).sum(), (neck > 0).sum(), npale, (w > 0).sum(), k))
        if laid and not src_dir:
            print("LOBE %-9s already laid (its lobe at its ear's tone, its neck filled, no tab left), not written" % face)
            continue
        o8 = (np.clip(srgb(np.clip(out, 0, 1)), 0, 1) * 255 + 0.5).astype(np.uint8)
        diff = np.abs(o8.astype(int) - (cur * 255 + 0.5).astype(int)).max()
        Image.fromarray(o8).save(path, quality=95, subsampling=0)
        print("LOBE %-9s max change %d/255; %s" % (face, diff, "; ".join(notes)))


if __name__ == "__main__":
    args = sys.argv[1:]
    src = None
    if args[:1] == ["--from"]:
        src, args = args[1], args[2:]
    run(args, src)
