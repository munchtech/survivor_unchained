"""Her nipples and areolae taken out of the shipped body (the owner, 18 Oct: "ONLY ... if it removes the legal
checks from the workflow"; and "keep the non shipping asset because we *WILL* need it"): AREOLA_OUT=1 in
heroine_outfits.py; AREOLA_OUT=0 builds the anatomical body as before (never shipped).

Two parts, both pure numpy/scipy so they run in the build and on an exported glb alike:
  flatten(): each nipple and its raised areola eased into the breast's own curve. Each point within R_GEO of
     the nipple moves only along one axis (the breast's normal there), so its place on her skin, and so its
     paint, stays put; the heights inside are a biharmonic fill (cotangent weights on her skin laid flat
     over that axis' plane) of the heights round it, so the patch meets her skin with no ridge or dent.
  paint(): each areola painted out of her albedo: the tone inside is a smooth fill of her breast's own tone
     round it, the fine grain is her own skin's grain taken from beside it, the mask is her areola's muted
     pink (heroine_head.py's rule, R between 1.4 and 2.2 G) grown GROW past it, eased in over its outer
     FEATHER; only texels of her skin's islands within the mask (and the gutter texels padding those
     islands) change.
The frame is the caller's: `front` is her forward axis in it.
"""
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
from scipy import ndimage

R_GEO = 0.034      # flattened within this of each nipple's tip (her areola's mound ends at 28-30 mm)
SUB = 0.022        # rings past R_GEO the fill leans on
GRID = 0.0005      # the paint's working patch, m per pixel
HALF = 0.070       # its half width (the grain is taken from up to 6 cm out)
GROW = 0.004       # the mask grown past her areola's pink
FEATHER = 0.0025   # eased in over its outer part
HALO = 0.03        # the halo: R/G this much over her skin's own
FILL = __import__("os").environ.get("AREOLA_FILL", "harmonic")   # the residual's fill: harmonic (bounded by the ring's own, 0.3 mm inside), or bi (overshot to 0.76)


def weld(P, eps=1e-5):
    _, w = np.unique(np.round(P / eps).astype(np.int64), axis=0, return_inverse=True)
    w = np.asarray(w).ravel()
    Pw = np.zeros((w.max() + 1, 3))
    Pw[w] = P
    return Pw, w


def frame(Pw, T, tip_guess, front, r=0.04):
    """Each nipple's frame: its tip (the most proud point within 2 cm of the guess along the normal), the
    normal (her skin's mean normal within r), and two axes along her skin."""
    fn = np.cross(Pw[T[:, 1]] - Pw[T[:, 0]], Pw[T[:, 2]] - Pw[T[:, 0]])
    fc = Pw[T].mean(1)
    sel = np.linalg.norm(fc - tip_guess, axis=1) < r
    n0 = fn[sel].sum(0)
    n0 /= np.linalg.norm(n0)
    if n0 @ front < 0:
        n0 = -n0
    near = np.where(np.linalg.norm(Pw - tip_guess, axis=1) < 0.02)[0]
    tip = Pw[near[np.argmax(Pw[near] @ n0)]]
    up = np.cross(front, np.cross(n0, front))
    a = np.cross(up if abs(up @ n0) < 0.9 else front, n0)
    a /= np.linalg.norm(a)
    b = np.cross(n0, a)
    return tip, n0, a, b


def local(Pw, fr):
    tip, n0, a, b = fr
    q = Pw - tip
    return q @ a, q @ b, q @ n0


def cotlap(X, T):
    """Cotangent Laplacian (and lumped areas) of a flat triangulation X (n, 2)."""
    n = len(X)
    I, J, V = [], [], []
    area = np.zeros(n)
    for k in range(3):
        i, j, o = T[:, k], T[:, (k + 1) % 3], T[:, (k + 2) % 3]
        e1, e2 = X[i] - X[o], X[j] - X[o]
        cr = e1[:, 0] * e2[:, 1] - e1[:, 1] * e2[:, 0]
        cot = (e1 * e2).sum(1) / np.maximum(np.abs(cr), 1e-14)
        I += [i, j]; J += [j, i]; V += [0.5 * cot, 0.5 * cot]
        np.add.at(area, o, np.abs(cr) / 6)
    W = sp.csr_matrix((np.concatenate(V), (np.concatenate(I), np.concatenate(J))), shape=(n, n))
    L = W - sp.diags(np.asarray(W.sum(1)).ravel())
    return L.tocsr(), np.maximum(area, 1e-12)


def _cubic(u, v):
    return np.stack([np.ones_like(u), u, v, u * u, u * v, v * v, u ** 3, u * u * v, u * v * v, v ** 3], 1)


def flatten(Pw, T, tips, front, r_geo=R_GEO, log=print):
    """Pw: welded points; T: their triangles; tips: guesses of each nipple's tip. Returns the new points and
    the frames (the paint uses the same ones)."""
    out = Pw.copy()
    frames = []
    for t in tips:
        fr = frame(Pw, T, np.asarray(t, float), front)
        frames.append(fr)
        u, v, h = local(Pw, fr)
        r = np.hypot(u, v)
        d3 = np.linalg.norm(Pw - fr[0], axis=1)
        sub = (d3 < r_geo + SUB + 0.01) & (h > -0.05)
        tri = T[sub[T].all(1)]
        # (her skin's triangles that face the normal: the far side of her breast is not part of it)
        X3 = Pw[tri]
        fnv = np.cross(X3[:, 1] - X3[:, 0], X3[:, 2] - X3[:, 0]) @ fr[1]
        tri = tri[fnv > 0]
        ids = np.unique(tri)
        loc = -np.ones(len(Pw), int)
        loc[ids] = np.arange(len(ids))
        Tl = loc[tri]
        X = np.c_[u[ids], v[ids]]
        e1, e2 = X[Tl[:, 1]] - X[Tl[:, 0]], X[Tl[:, 2]] - X[Tl[:, 0]]
        cr = e1[:, 0] * e2[:, 1] - e1[:, 1] * e2[:, 0]
        L, M = cotlap(X, Tl)
        A = (L.T @ sp.diags(1 / M) @ L).tocsr() if FILL == "bi" else (-L).tocsr()
        inner = (r[ids] < r_geo) & (d3[ids] < r_geo + 0.01)
        ii, bb = np.where(inner)[0], np.where(~inner)[0]
        # (the breast's own curve: a cubic fitted to her skin in a ring round the patch; only what her skin
        # there departs from it is filled in, so the fill's own error is on millimetres, not the centimetre
        # of her breast's bend)
        ring = (r > r_geo) & (r < r_geo + 0.026) & (h > -0.06) & (d3 < r_geo + 0.04)
        fit = np.linalg.lstsq(_cubic(u[ring], v[ring]), h[ring], rcond=None)[0]
        hf = _cubic(u[ids], v[ids]) @ fit
        rb = h[ids][bb] - hf[bb]
        hi = hf[ii] + spla.spsolve(A[ii][:, ii].tocsc(), -A[ii][:, bb] @ rb)
        dh = hi - h[ids][ii]
        out[ids[ii]] = Pw[ids[ii]] + dh[:, None] * fr[1][None, :]
        log("AREOLA flatten tip %s: %d points within %.0f mm, %d triangles laid flat (%d turned over); moved %.2f mm at most (in), %.2f out"
            % (np.round(fr[0], 4), len(ii), r_geo * 1e3, len(Tl), int((cr <= 0).sum()), -dh.min() * 1e3, max(dh.max(), 0) * 1e3))
    return out, frames


# ---------------------------------------------------------------- paint
def _bilinear(img, x, y):
    """img sampled at continuous pixel coordinates (texel k's centre at k + 0.5)."""
    H, W = img.shape[:2]
    x = np.clip(x - 0.5, 0, W - 1.001)
    y = np.clip(y - 0.5, 0, H - 1.001)
    x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int)
    fx, fy = (x - x0)[..., None], (y - y0)[..., None]
    return (img[y0, x0] * (1 - fx) * (1 - fy) + img[y0, x0 + 1] * fx * (1 - fy)
            + img[y0 + 1, x0] * (1 - fx) * fy + img[y0 + 1, x0 + 1] * fx * fy)


def _raster(tri_xy, n_w, n_h, pad=0.0):
    """Texel centres inside each triangle (xy in continuous pixel coordinates). Yields (tri index, px, py,
    barycentrics)."""
    for k, (p0, p1, p2) in enumerate(tri_xy):
        lo = np.floor(np.minimum(np.minimum(p0, p1), p2) - pad).astype(int)
        hi = np.ceil(np.maximum(np.maximum(p0, p1), p2) + pad).astype(int)
        lo = np.maximum(lo, 0); hi = np.minimum(hi, [n_w - 1, n_h - 1])
        if (hi < lo).any():
            continue
        gx, gy = np.meshgrid(np.arange(lo[0], hi[0] + 1), np.arange(lo[1], hi[1] + 1))
        px, py = gx.ravel() + 0.5, gy.ravel() + 0.5
        d = (p1[1] - p2[1]) * (p0[0] - p2[0]) + (p2[0] - p1[0]) * (p0[1] - p2[1])
        if abs(d) < 1e-12:
            continue
        l0 = ((p1[1] - p2[1]) * (px - p2[0]) + (p2[0] - p1[0]) * (py - p2[1])) / d
        l1 = ((p2[1] - p0[1]) * (px - p2[0]) + (p0[0] - p2[0]) * (py - p2[1])) / d
        l2 = 1 - l0 - l1
        e0, e1, e2 = [-1e-6 - pad * np.linalg.norm(a - b) / abs(d) for a, b in ((p1, p2), (p2, p0), (p0, p1))]
        m = (l0 >= e0) & (l1 >= e1) & (l2 >= e2)
        if m.any():
            yield k, gx.ravel()[m], gy.ravel()[m], np.c_[l0[m], l1[m], l2[m]]


def patch(img, Pw, T, CXY, fr, half=HALF, s=GRID):
    """Her skin round a nipple laid out flat (its frame's plane, s m per pixel): per pixel, the atlas
    position (continuous pixel coordinates) of her skin there, its colour, and whether skin is there.
    CXY: per triangle corner, its atlas position."""
    u, v, h = local(Pw, fr)
    n = int(round(2 * half / s))
    sel = (np.linalg.norm(Pw[T].mean(1) - fr[0], axis=1) < half * 1.6)
    X3 = Pw[T]
    sel &= (np.cross(X3[:, 1] - X3[:, 0], X3[:, 2] - X3[:, 0]) @ fr[1]) > 0
    sel &= (h[T] > -0.06).all(1)
    ks = np.where(sel)[0]
    G = np.stack([(u[T[ks]] + half) / s, (v[T[ks]] + half) / s], -1)
    AX = np.full((n, n, 2), np.nan)
    best = np.full((n, n), -np.inf)
    for k, gx, gy, bc in _raster(G, n, n):
        t = ks[k]
        hh = bc @ h[T[t]]
        m = hh > best[gy, gx]
        best[gy[m], gx[m]] = hh[m]
        AX[gy[m], gx[m]] = bc[m] @ CXY[t]
    ok = np.isfinite(AX[..., 0])
    col = np.zeros((n, n, img.shape[2]))
    col[ok] = _bilinear(img, AX[ok, 0], AX[ok, 1])
    return AX, col, ok, ks


def srgb_lab(c):
    c = np.clip(c[..., :3], 0, 1)
    lin = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    xyz = lin @ M.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > (6 / 29) ** 3, np.cbrt(xyz), xyz / (3 * (6 / 29) ** 2) + 4 / 29)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def de2000(l1, l2):
    L1, a1, b1 = l1; L2, a2, b2 = l2
    C1, C2 = np.hypot(a1, b1), np.hypot(a2, b2)
    Cm = (C1 + C2) / 2
    Gf = 0.5 * (1 - np.sqrt(Cm ** 7 / (Cm ** 7 + 25 ** 7)))
    a1p, a2p = (1 + Gf) * a1, (1 + Gf) * a2
    C1p, C2p = np.hypot(a1p, b1), np.hypot(a2p, b2)
    h1p, h2p = np.degrees(np.arctan2(b1, a1p)) % 360, np.degrees(np.arctan2(b2, a2p)) % 360
    dLp, dCp = L2 - L1, C2p - C1p
    dhp = h2p - h1p
    dhp = dhp - 360 if dhp > 180 else dhp + 360 if dhp < -180 else dhp
    dHp = 2 * np.sqrt(C1p * C2p) * np.sin(np.radians(dhp / 2))
    Lpm, Cpm = (L1 + L2) / 2, (C1p + C2p) / 2
    hpm = (h1p + h2p) / 2 if abs(h1p - h2p) <= 180 else (h1p + h2p + 360) / 2
    Tt = 1 - 0.17 * np.cos(np.radians(hpm - 30)) + 0.24 * np.cos(np.radians(2 * hpm)) + 0.32 * np.cos(np.radians(3 * hpm + 6)) - 0.2 * np.cos(np.radians(4 * hpm - 63))
    SL = 1 + 0.015 * (Lpm - 50) ** 2 / np.sqrt(20 + (Lpm - 50) ** 2)
    SC, SH = 1 + 0.045 * Cpm, 1 + 0.015 * Cpm * Tt
    RT = -2 * np.sqrt(Cpm ** 7 / (Cpm ** 7 + 25 ** 7)) * np.sin(np.radians(60 * np.exp(-((hpm - 275) / 25) ** 2)))
    return float(np.sqrt((dLp / SL) ** 2 + (dCp / SC) ** 2 + (dHp / SH) ** 2 + RT * (dCp / SC) * (dHp / SH)))


def _lowpass(c, valid, sig):
    """Gaussian low-pass of c (n, n, k) over the valid pixels only (normalised convolution)."""
    w = ndimage.gaussian_filter(valid.astype(float), sig)
    out = np.stack([ndimage.gaussian_filter(np.where(valid, c[..., k], 0.0), sig) for k in range(c.shape[2])], -1)
    return out / np.maximum(w, 1e-9)[..., None]


def _grid_fill(known_val, unknown, order=2):
    """Each channel over the unknown pixels, (bi)harmonic on the 4-neighbour grid, from the known values
    round them."""
    n0, n1 = unknown.shape
    uu = np.argwhere(unknown)
    known = ~unknown
    lo = np.maximum(uu.min(0) - 3, 0)
    hi = np.minimum(uu.max(0) + 4, [n0, n1])
    box = np.zeros(unknown.shape, bool)
    box[lo[0]:hi[0], lo[1]:hi[1]] = True
    allid = -np.ones(unknown.shape, int)
    bp = np.argwhere(box)
    allid[box] = np.arange(len(bp))
    I, J = [], []
    for dy, dx in ((0, 1), (1, 0)):
        a = bp[(bp[:, 0] + dy < hi[0]) & (bp[:, 1] + dx < hi[1])]
        b = a + [dy, dx]
        I.append(allid[a[:, 0], a[:, 1]])
        J.append(allid[b[:, 0], b[:, 1]])
    I, J = np.concatenate(I), np.concatenate(J)
    Wm = sp.csr_matrix((np.ones(2 * len(I)), (np.r_[I, J], np.r_[J, I])), shape=(len(bp),) * 2)
    L = (Wm - sp.diags(np.asarray(Wm.sum(1)).ravel())).tocsr()
    A = (L @ L).tocsr() if order == 2 else L
    ui = allid[uu[:, 0], uu[:, 1]]
    kn = np.where(known[box])[0]
    out = known_val.copy()
    Au = A[ui]
    lu = spla.splu(Au[:, ui].tocsc())
    for k in range(known_val.shape[2]):
        xk = known_val[box][:, k]
        out[unknown, k] = lu.solve(-(Au[:, kn] @ xk[kn]))
    return out


def paint(img, Pw, T, CXY, frames, log=print, seed=1):
    """img (H, W, C) float, indexed [row, col] in the same pixel frame as CXY (each triangle corner's atlas
    position, continuous: texel k's centre at k + 0.5). Returns the painted copy, what the measure needs,
    and which texels changed."""
    out = img.copy()
    H, W = img.shape[:2]
    s, half = GRID, HALF
    info = []
    changed = np.zeros((H, W), bool)
    cov = None
    for fr in frames:
        AX, col, ok, ks = patch(img, Pw, T, CXY, fr)
        n = col.shape[0]
        gx, gy = np.meshgrid(np.arange(n), np.arange(n))
        uu, vv = (gx + 0.5) * s - half, (gy + 0.5) * s - half
        rr = np.hypot(uu, vv)
        rg = col[..., 0] / np.maximum(col[..., 1], 1e-3)
        # her areola: its muted pink (R 1.4-2.2 G), and the halo, pinker than her skin, it fades out through
        # to her skin's own R/G (the median 34-44 mm out): the part of that joined to the pink
        ringz = ok & (rr > 0.034) & (rr < 0.044)
        rg0 = np.median(rg[ringz])
        core = ok & (rg > 1.4) & (rg < 2.2) & (rr < 0.03)
        lab, _ = ndimage.label(core)
        core = lab == (1 + np.argmax(np.bincount(lab.ravel())[1:]))
        halo = ok & (rg > rg0 + HALO) & (rr < 0.045)
        lab, _ = ndimage.label(halo | core)
        keep = np.unique(lab[core])
        hard = np.isin(lab, keep[keep > 0])
        hard = ndimage.binary_closing(hard, iterations=4)
        hard = ndimage.binary_fill_holes(hard)
        hard = ndimage.binary_opening(hard, iterations=2)
        dout = ndimage.distance_transform_edt(~hard) * s
        grown = dout < GROW
        alpha = np.clip((GROW - dout) / FEATHER, 0, 1)
        alpha = alpha * alpha * (3 - 2 * alpha)
        alpha[~ok] = 0
        valid = ok & ~grown
        # tone: her skin's own round it, low-passed, carried in by a biharmonic fill
        LP = _lowpass(col[..., :3], valid, 3e-3 / s)
        unknown = grown & ok
        tone = _grid_fill(np.where(valid[..., None], LP, 0.0), unknown)
        # grain: her own skin's (each texel's own colour less the low-pass), taken from beside the mask in
        # cells 8 mm apart, each its own donor, crossfaded keeping the variance
        xi = np.clip(np.floor(np.nan_to_num(AX[..., 0])).astype(int), 0, W - 1)
        yi = np.clip(np.floor(np.nan_to_num(AX[..., 1])).astype(int), 0, H - 1)
        nn = np.zeros_like(col[..., :3])
        nn[ok] = img[yi[ok], xi[ok], :3]
        hp = np.where(valid[..., None], nn - LP, 0.0)
        lum_hp = hp @ np.array([0.2126, 0.7152, 0.0722])
        sd0 = 1.4826 * np.median(np.abs(lum_hp[valid]))
        clean = valid & (np.abs(lum_hp) < 4 * sd0)
        # (a donor: a 10 mm disc wholly clean, its centre 12-30 mm outside the mask)
        cr_ = int(0.010 / s)
        yy, xx = np.mgrid[-cr_:cr_ + 1, -cr_:cr_ + 1]
        disc = (yy ** 2 + xx ** 2) <= cr_ ** 2
        okd = ndimage.binary_erosion(clean, structure=disc) & (dout > 0.012) & (dout < 0.030)
        cand = np.argwhere(okd)
        rng = np.random.default_rng(seed)
        cell = 0.008 / s
        cy, cx = np.mgrid[0:n:cell, 0:n:cell]
        cells = np.c_[cy.ravel(), cx.ravel()] + cell / 2
        ci = np.clip(cells.astype(int), 0, n - 1)
        cells = cells[dout[ci[:, 0], ci[:, 1]] < GROW + 0.006]
        num = np.zeros((n, n, 3))
        den = np.zeros((n, n))
        den2 = np.zeros((n, n))
        tgt = np.argwhere(unknown)
        for c in cells:
            o = cand[rng.integers(len(cand))] - c
            wgt = np.exp(-((tgt - c) ** 2).sum(1) / (2 * (0.0045 / s) ** 2))
            src = np.clip(np.round(tgt + o).astype(int), 0, n - 1)
            wgt = wgt * valid[src[:, 0], src[:, 1]]
            num[tgt[:, 0], tgt[:, 1]] += wgt[:, None] * hp[src[:, 0], src[:, 1]]
            den[tgt[:, 0], tgt[:, 1]] += wgt
            den2[tgt[:, 0], tgt[:, 1]] += wgt ** 2
        grain = num / np.maximum(np.sqrt(den2), 1e-12)[..., None]
        grain[den < 1e-6] = 0
        # into the atlas: every texel of her skin's islands whose place on her is within the mask (and the
        # texels no triangle covers within 1.5 of one of these: a sliver triangle covers no texel centre,
        # and draws from those round it)
        if cov is None:
            cov = np.zeros((H, W), bool)
            for k, px, py, bc in _raster(CXY, W, H):
                cov[py, px] = True
        u_, v_, _ = local(Pw, fr)
        Gk = np.stack([(u_[T[ks]] + half) / s, (v_[T[ks]] + half) / s], -1)
        n_tex = 0
        for k, px, py, bc in _raster(CXY[ks], W, H, pad=1.5):
            own = (bc >= -1e-6).all(1)
            take = own | ~cov[py, px]
            px, py, bc = px[take], py[take], np.clip(bc[take], 0, 1)
            bc = bc / bc.sum(1, keepdims=True)
            gp = bc @ Gk[k]
            a_ = _bilinear(alpha[..., None], gp[:, 0], gp[:, 1])[:, 0]
            m = a_ > 0
            if not m.any():
                continue
            gpm = gp[m]
            t_ = _bilinear(tone, gpm[:, 0], gpm[:, 1])
            g_ = grain[np.clip(gpm[:, 1].astype(int), 0, n - 1), np.clip(gpm[:, 0].astype(int), 0, n - 1)]
            o_ = img[py[m], px[m], :3]
            out[py[m], px[m], :3] = o_ * (1 - a_[m, None]) + np.clip(t_ + g_, 0, 1) * a_[m, None]
            changed[py[m], px[m]] = True
            n_tex += int(m.sum())
        info.append(dict(hard=hard, grown=grown, ok=ok, rg0=rg0, fr=fr, alpha=alpha))
        log("AREOLA paint tip %s: skin R/G %.3f round it; mask %.1f cm2 (pink core %.1f), grown %.0f mm to %.1f cm2; %d donor cells from %d places; %d texels painted"
            % (np.round(fr[0], 4), rg0, hard.sum() * s * s * 1e4, core.sum() * s * s * 1e4, GROW * 1e3, grown.sum() * s * s * 1e4, len(cells), len(cand), n_tex))
    # the gutter round her islands there: texels no triangle covers, nearest a painted one (within 3), take its colour
    if changed.any():
        ys, xs = np.nonzero(changed)
        y0, y1 = max(ys.min() - 8, 0), min(ys.max() + 9, H)
        x0, x1 = max(xs.min() - 8, 0), min(xs.max() + 9, W)
        cov = np.zeros((y1 - y0, x1 - x0), bool)
        lo_, hi_ = CXY.min(1), CXY.max(1)
        near = (hi_[:, 0] >= x0) & (lo_[:, 0] <= x1) & (hi_[:, 1] >= y0) & (lo_[:, 1] <= y1)
        for k, px, py, bc in _raster(CXY[near] - [x0, y0], x1 - x0, y1 - y0):
            cov[py, px] = True
        d, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
        ch = changed[y0:y1, x0:x1]
        gut = ~cov & (d <= 3) & ch[iy, ix]
        sub = out[y0:y1, x0:x1]
        sub[gut] = sub[iy[gut], ix[gut]]
        changed[y0:y1, x0:x1] |= gut
        log("AREOLA paint: %d gutter texels padded" % int(gut.sum()))
    return out, info, changed


def measure(img0, img1, Pw, T, CXY, info, log=print):
    """Old areola against a ring 1-2 cm outside it, on her skin laid flat: dE2000 of the mean colours, and
    the high-pass (2 mm) std of luminance in each."""
    s = GRID
    res = []
    for it in info:
        hard = it["hard"]
        dout = ndimage.distance_transform_edt(~hard) * s
        row = []
        for im in (img0, img1):
            _, col, ok2, _ = patch(im, Pw, T, CXY, it["fr"])
            ring = ok2 & (dout > 0.010) & (dout < 0.020)
            lab = srgb_lab(col)
            a, b = lab[hard & ok2].mean(0), lab[ring].mean(0)
            lum = col[..., :3] @ np.array([0.2126, 0.7152, 0.0722])
            hp = lum - _lowpass(lum[..., None], ok2, 2e-3 / s)[..., 0]
            row.append((de2000(a, b), hp[hard & ok2].std(), hp[ring].std()))
        log("AREOLA measure tip %s: dE2000 areola vs ring %.2f -> %.2f; high-pass std areola/ring %.4f/%.4f (%.2f) -> %.4f/%.4f (%.2f)"
            % (np.round(it["fr"][0], 4), row[0][0], row[1][0], row[0][1], row[0][2], row[0][1] / row[0][2], row[1][1], row[1][2], row[1][1] / row[1][2]))
        res.append(row)
    return res


def _vnormals(P, T):
    fn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
    vn = np.zeros_like(P)
    for k in range(3):
        np.add.at(vn, T[:, k], fn)
    return vn / np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-12)


def _base_image(obj):
    """The image her body's material takes its base colour from."""
    for si, slot in enumerate(obj.material_slots):
        m = slot.material
        if not (m and m.use_nodes):
            continue
        for nd in m.node_tree.nodes:
            if nd.type == "BSDF_PRINCIPLED":
                stack = [l.from_node for l in nd.inputs["Base Color"].links]
                while stack:
                    x = stack.pop()
                    if x.type == "TEX_IMAGE" and x.image:
                        return x.image, si
                    stack += [l.from_node for i in x.inputs for l in i.links]
    return None, -1


def apply(obj, tips, front=(0.0, -1.0, 0.0), log=print):
    """In the build (heroine_outfits.py, AREOLA_OUT=1), on her body just before the export's mend_folds:
    her albedo painted (an in-memory copy, packed into the export), her nipples flattened (shape keys take
    the same offsets), and her normals there made anew (handed to mend_folds, as heroine_chest.py does)."""
    import sys
    import bpy  # noqa: F401
    me = obj.data
    mw = obj.matrix_world
    R = np.array(mw.to_3x3())
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    Pb = co @ R.T + np.array(mw.translation)
    Pw, w = weld(Pb)
    me.calc_loop_triangles()
    lt = np.empty(len(me.loop_triangles) * 3, np.int64); me.loop_triangles.foreach_get("vertices", lt); lt = lt.reshape(-1, 3)
    ll = np.empty(len(me.loop_triangles) * 3, np.int64); me.loop_triangles.foreach_get("loops", ll); ll = ll.reshape(-1, 3)
    T = w[lt]
    keep = (T[:, 0] != T[:, 1]) & (T[:, 1] != T[:, 2]) & (T[:, 0] != T[:, 2])
    front = np.asarray(front, float)
    frames = [frame(Pw, T[keep], np.asarray(t, float), front) for t in tips]
    # ---- paint
    im, slot = _base_image(obj)
    # (only her triangles painted from it: the graft's own image shares its UV space, and taken for hers its
    # triangles kept the gutter round her islands from being painted, outlines left round them)
    lmat = np.empty(len(me.loop_triangles), np.int64); me.loop_triangles.foreach_get("material_index", lmat)
    kp = keep & (lmat == slot)
    if im is None:
        log("AREOLA: no base colour image on her body; paint skipped")
    else:
        Wd, Hd = im.size
        nch = im.channels
        px = np.empty(Wd * Hd * nch, np.float32); im.pixels.foreach_get(px)
        img = px.reshape(Hd, Wd, nch).astype(float)          # (row 0 at v = 0, as her UVs count)
        uv = np.empty(len(me.loops) * 2); me.uv_layers.active.data.foreach_get("uv", uv); uv = uv.reshape(-1, 2)
        CXY = np.stack([uv[ll[kp]][..., 0] * Wd, uv[ll[kp]][..., 1] * Hd], -1)
        out, info, changed = paint(img, Pw, T[kp], CXY, frames, log=log)
        measure(img, out, Pw, T[kp], CXY, info, log=log)
        # (8-bit, as the export writes it: what the measure saw is what ships)
        out = np.round(np.clip(out, 0, 1) * 255) / 255
        im.pixels.foreach_set(out.astype(np.float32).ravel())
        im.update()
        im.pack()
        log("AREOLA paint: %s (%dx%d) %d texels changed, packed" % (im.name, Wd, Hd, int(changed.sum())))
    # ---- shape
    P2, _ = flatten(Pw, T[keep], [f[0] for f in frames], front, log=log)
    D = (P2 - Pw)[w]
    moved = np.nonzero(np.linalg.norm(D, axis=1) > 1e-12)[0]
    dl = D[moved] @ np.linalg.inv(R).T
    co[moved] += dl
    me.vertices.foreach_set("co", co.ravel())
    if me.shape_keys:
        for kb in me.shape_keys.key_blocks:
            kc = np.empty(len(me.vertices) * 3); kb.data.foreach_get("co", kc); kc = kc.reshape(-1, 3)
            kc[moved] += dl
            kb.data.foreach_set("co", kc.ravel())
    me.update()
    # ---- normals: her skin's own as it now is, over the patch and 6 mm past it, eased into what she had
    # over the last 10 mm (handed to mend_folds as heroine_chest.py's are; never across a normal seam)
    vn = _vnormals(P2, T[keep])
    wn = np.zeros(len(Pw))
    for fr in frames:
        u, v, h = local(Pw, fr)
        r = np.hypot(u, v)
        x = np.clip((R_GEO + 0.006 - r) / 0.010, 0, 1)
        x = x * x * (3 - 2 * x)
        wn = np.maximum(wn, np.where((h > -0.05) & (np.linalg.norm(Pw - fr[0], axis=1) < R_GEO + 0.02), x, 0))
    nl = len(me.loops)
    cn = np.empty(nl * 3, np.float32); me.corner_normals.foreach_get("vector", cn); cn = cn.reshape(-1, 3).astype(float)
    lv = np.empty(nl, np.int64); me.loops.foreach_get("vertex_index", lv)
    hc = sys.modules.get("heroine_chest")
    if hc is None:
        import heroine_chest as hc
    prev = getattr(hc, "CN_OVERRIDE", None)
    base = cn.copy()
    if prev is not None:
        base[prev[0]] = prev[1]
    lw = w[lv]
    mean = np.zeros((len(Pw), 3)); np.add.at(mean, lw, cn)
    mean /= np.maximum(np.linalg.norm(mean, axis=1, keepdims=True), 1e-12)
    spread = np.ones(len(Pw)); np.minimum.at(spread, lw, (cn * mean[lw]).sum(1))
    act = (wn > 0) & (spread > np.cos(np.radians(1.0)))
    sel = np.nonzero(act[lw])[0]
    nloc = vn[lw[sel]] @ R                                   # (to her local frame: mw rotation-only)
    nloc /= np.linalg.norm(nloc, axis=1, keepdims=True)
    # (one normal for all the corners at a point: corners differing by a hair, the export reordered a
    # point's two UV-seam copies)
    bm_ = np.zeros((len(Pw), 3)); np.add.at(bm_, lw, base)
    b_ = bm_[lw[sel]] / np.maximum(np.linalg.norm(bm_[lw[sel]], axis=1, keepdims=True), 1e-12)
    nv = nloc * wn[lw[sel], None] + b_ * (1 - wn[lw[sel], None])
    nv /= np.linalg.norm(nv, axis=1, keepdims=True)
    if prev is not None:
        allv = base.copy()
        allv[sel] = nv
        idx = np.union1d(prev[0], sel)
        hc.CN_OVERRIDE = (idx, allv[idx])
    else:
        hc.CN_OVERRIDE = (sel, nv)
    log("AREOLA: %d of her points moved (%.2f mm at most), %d corners' normals made anew (%d points kept for a normal seam)"
        % (len(moved), np.linalg.norm(D, axis=1).max() * 1e3, len(sel), int(((wn > 0) & ~act).sum())))
