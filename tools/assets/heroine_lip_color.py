"""Her upper lip painted lip-coloured up to her sculpt's own lip border, in each face's paint.

Her sculpt's upper lip is a full, ordinary lip (9-10 mm from her mouth line to the border, its vermilion ridge and
cupid's bow), but every face's paint (laid from a portrait with a thinner upper lip) colours its top 4.4-7.6 mm as
skin. At the Look the lit ridge and her head's shade then drew the border as an outline in skin above a thin red
lip (the owner, 12 October 2026; with her shade off it still showed: it is the sculpt's). This recolours that band,
between the paint's red top and the border, to the paint's own lower lip's colour (its red, under the mouth line), column by column
across her mouth, keeping each texel's own detail (a ratio in linear light, not a warp: a stretched lip smeared).
The border's edge is soft over 0.7 mm; the band fades into the paint's red over 1 mm below its old top; toward the
corners of her mouth, where the border meets the mouth line, the band thins to nothing.

    python tools/assets/heroine_lip_color.py [--to DIR] [face ...]   (no faces: every paint; --to: write there)

Run on paints fresh from the chain (heroine_face.py's lay, heroine_jaw_cut.py, heroine_ears.py), then this. A rerun
finds the red's top at the border and changes nothing more.
"""
import json
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import heroine_lips as hl  # noqa: E402

EDGE = 0.0007       # (the border's softness, m: smoothstep; 0.4 read stickered on Doe)
INTO = 0.0012       # (the band ramps from the old red over this, below its old top: a step showed at 1.0 linear)
UNDER = 0.0         # (the new red's edge's middle this far under the border; round two: the border is the target
                    #  curve itself (lip_borders.json's dense), the portraits' heights measured at the edge's middle)
LOWER = (0.0035, 0.0115)    # (the lip's colour: her LOWER lip's red, this far under the mouth line. Over 3.5 mm the
                            #  paints carry the portrait's dark mouth gap; the upper red's top sits in the mouth
                            #  line's shade and read darker and rosier than her lower lip)
NO_CREASE = 0.0095
LUMA = np.array([0.2126, 0.7152, 0.0722])
# (round two, judge j8b: every face's band is its OWN upper red carried up (as Sunborn's in round one), matched to
#  the old red where they meet (JOIN, under the old red's top, where the band's ramp starts) and eased to the face's
#  upper red over the band: no lower-lip pink, no stripe)
JOIN = (0.0021, 0.0013)     # (the old red's colour where the band meets it: this far under its old top)
DARKEN = {"sunborn": 0.72}  # (j8b: Sunborn's upper lip darker, like her _23; 0.90 read lighter than her old upper red at the Look, ls5)
CHROMA = {}
LINES = 0.6                 # (her lower lip's vertical lines carried into the band at this strength)
LINES_SIGMA = 4.0           # (front-grid px, 0.1 mm: the high-pass across her lip)
LINES_SHIFT = 0.0           # (the mirror's offset)
OWN_SIGMA = 5.0             # (each texel's own detail against the paint smoothed over this, px)


def lin(c):
    c = c / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055) * 255


def border(m, t, dense=False):
    """The border's height per column: the crease, smoothed, carried down to the mouth line at her mouth's corners.
    dense: t is already the whole smooth border, corner to corner (heroine_lipsculpt.py's target): taken as it is."""
    ok = ~np.isnan(m)
    if dense:
        return np.where(ok & ~np.isnan(t), t, m)
    okt = ok & ~np.isnan(t)
    x = np.arange(len(m))
    tt = np.full(len(m), np.nan)
    if okt.sum() < 10:
        return tt
    lift = np.interp(x, x[okt], (t - m)[okt])                     # (border over mouth line, held at the ends)
    c0, c1 = x[ok].min(), x[ok].max()                              # (her mouth's corners)
    k0, k1 = x[okt].min(), x[okt].max()                            # (where the crease is found)
    f = np.ones(len(m))
    f[x < k0] = np.clip((x[x < k0] - c0) / max(k0 - c0, 1), 0, 1) ** 0.7
    f[x > k1] = np.clip((c1 - x[x > k1]) / max(c1 - k1, 1), 0, 1) ** 0.7
    tt[ok] = m[ok] + ndimage.gaussian_filter1d(lift, 8)[ok] * f[ok]
    return tt


def fields(F, m, t, paint_front, face="", t_new=None):
    """Per front-grid pixel the band's weight W and its target colour (linear, with her lower lip's vertical lines),
    and the paint's smoothed luminance (each texel keeps its own fine detail against it)."""
    e = hl.red_top(paint_front, m, t)
    tt = border(m, t if t_new is None else t_new, dense=t_new is not None)
    ok = ~np.isnan(tt) & ~np.isnan(m)
    x = np.arange(len(m))
    ok_e = ok & ~np.isnan(e)
    ee = np.full(len(m), np.nan)
    ee[ok] = np.interp(x[ok], x[ok_e], hl.smooth_cols(e, 6)[ok_e]) if ok_e.sum() > 3 else np.nan
    ee = np.minimum(ee, tt)                                        # (never above the border)
    ys = hl.Y1 - (np.arange(F.shape[0]) + 0.5) * hl.D
    Y = ys[:, None]
    top = (tt - UNDER)[None, :]
    u = np.clip((Y - (top - EDGE / 2)) / EDGE, 0, 1)
    w_top = 1 - u * u * (3 - 2 * u)                                # (1 under the border, 0 over it; smoothstep)
    v = np.clip((Y - (ee[None, :] - INTO)) / INTO, 0, 1)
    w_bot = v * v * (3 - 2 * v)                                    # (0 deep in the old red, 1 at its old top: a ramp)
    W = np.nan_to_num(w_top * w_bot) * ok[None, :]
    gap = np.nan_to_num(tt - ee)
    W *= np.clip(gap / 0.0008, 0, 1)[None, :]                      # (no band where the red already meets the border)
    L = lin(paint_front)
    lum = L @ LUMA
    lipc = np.full((len(m), 3), np.nan)
    upc = np.full((len(m), 3), np.nan)
    rd = ndimage.uniform_filter(hl.redness(paint_front), (3, 5))
    lowmask = np.zeros(rd.shape, bool)
    upmask = np.zeros(rd.shape, bool)
    for c in np.where(ok_e)[0]:
        r0, r1 = int(hl.row(m[c] - LOWER[0])), int(hl.row(m[c] - LOWER[1]))
        u0, u1 = int(hl.row(ee[c] - 0.0006)), int(hl.row(m[c] + 0.0010))
        if r1 > r0 + 10:
            sel = _lower_sel(rd[r0:r1, c], L[r0:r1, c])
            lowmask[r0:r1, c] = sel
            if sel.sum() > 4:
                lipc[c] = np.median(L[r0:r1, c][sel], 0)
        if u1 > u0 + 6:
            sel = _lower_sel(rd[u0:u1, c], L[u0:u1, c])
            upmask[u0:u1, c] = sel
            if sel.sum() > 3:
                upc[c] = np.median(L[u0:u1, c][sel], 0)
    lipc, upc = _cols(lipc, x), _cols(upc, x)
    # (the target: her own upper red (upc), met at the band's foot by the old red's colour there (jc), eased between)
    jc = np.full((len(m), 3), np.nan)
    for c in np.where(ok_e)[0]:
        j0, j1 = int(hl.row(ee[c] - JOIN[1])), int(hl.row(ee[c] - JOIN[0]))
        j1 = min(j1, int(hl.row(m[c] + 0.0008)))
        if j1 > j0 + 2:
            jc[c] = np.median(L[j0:j1, c], 0)
    jc = _cols(jc, x)
    tgt = upc * DARKEN.get(face, 1.0)
    g = (tgt @ LUMA)[:, None]
    tgt = g + (tgt - g) * CHROMA.get(face, 1.0)
    foot = (ee - INTO)[None, :]
    h = _smooth01_((Y - foot) / np.maximum((tt + EDGE / 2)[None, :] - foot, 1e-4))
    T = jc[None, :, :] + (tgt - jc)[None, :, :] * np.nan_to_num(h)[..., None]
    # (her lower lip's vertical lines, mirrored over the mouth line: its luminance high-passed across, not down)
    hp = lum / np.maximum(ndimage.gaussian_filter1d(lum, LINES_SIGMA, axis=1), 1e-4)
    hp = ndimage.gaussian_filter1d(hp, 1.5, axis=0)
    det = np.ones(lum.shape)
    for c in np.where(ok)[0]:
        rows = np.arange(lum.shape[0])
        yy = 2 * m[c] - ys - LINES_SHIFT                             # (the mirrored lower-lip height)
        src = np.clip(np.round(hl.row(yy)).astype(int), 0, lum.shape[0] - 1)
        inband = (ys > ee[c] - INTO) & (ys < tt[c] + EDGE)
        det[rows[inband], c] = hp[src[inband], c]
    det = np.clip(det, 0.8, 1.2) ** LINES
    T = T * det[..., None]
    S = ndimage.gaussian_filter(lum, OWN_SIGMA)
    W = ndimage.gaussian_filter(W, 1.0)
    return W, T, S, tt, ee, lowmask, upmask


def _smooth01_(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def _cols(v, x):
    """Per-column colours, gaps filled and smoothed across her mouth."""
    out = np.ones_like(v)
    for k in range(3):
        good = ~np.isnan(v[:, k])
        if good.sum() > 3:
            r = np.interp(x, x[good], v[good, k])
            out[:, k] = ndimage.gaussian_filter1d(ndimage.median_filter(r, 31), 20)
    return out


def _lower_sel(rd, L):
    """Her lower lip's mid-tones in one column: its redder half, without the portrait's highlight or shade."""
    y = L @ np.array([0.2126, 0.7152, 0.0722])
    lo, hi = np.percentile(y, [20, 90])
    return (rd >= np.median(rd)) & (y >= lo) & (y <= hi)


def _lum(a):
    return float(np.mean(lin(a) @ np.array([0.2126, 0.7152, 0.0722]))) if len(a) else float("nan")


def _rdn(a):
    return float(np.mean(a[:, 0] - a[:, 1])) if len(a) else float("nan")


def main():
    args = sys.argv[1:]
    to = None
    if "--to" in args:
        i = args.index("--to")
        to = args[i + 1]
        del args[i:i + 2]
    border_mode = "sculpt"
    if "--border" in args:
        i = args.index("--border")
        border_mode = args[i + 1]
        del args[i:i + 2]
    pp = hl.paints()
    faces = args or sorted(pp)
    ao = np.asarray(Image.open(os.path.join(hl.TEX, "heroine_ao.png")).convert("RGBA")).astype(np.float64)[..., 0] / 255
    if border_mode == "ao":
        P, UV, TRI = hl.mesh()
    else:
        import heroine_lipsculpt as ls
        js, binc, chunks, hm, hp, names, P0, N0, UV0, T0 = ls.head(hl.GLB)
        UV, TRI = UV0.astype(np.float64), T0.astype(np.int64).reshape(-1, 3)
        bj = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "heroine_face", "lip_borders.json")))
    cache = {}
    for f in faces:
        if border_mode != "ao":
            if f not in bj:
                print("LIPCOLOR %s: not in lip_borders.json, skipped" % f)
                continue
            P = ls.shaped(js, binc, hp, names, P0, f).astype(np.float64)
        src = os.path.join(hl.TEX, pp[f])
        img = np.asarray(Image.open(src).convert("RGB")).astype(np.float64)
        n = img.shape[0]
        key = (n, "ao") if border_mode == "ao" else (n, f)
        if key not in cache:
            cache.clear()
            F = hl.front(P, UV, TRI)
            m, t, _, _ = hl.lines(F, ao)
            G = hl.in_uv(P, UV, TRI, n, None)
            gx, gy, gz = G[..., 0], G[..., 1], G[..., 2]
            has = ~np.isnan(gx)
            rr, cc = hl.row(np.nan_to_num(gy)), hl.col(np.nan_to_num(gx))
            has &= (rr >= 0) & (rr < F.shape[0] - 1) & (cc >= 0) & (cc < F.shape[1] - 1)
            zf = hl.sample(np.nan_to_num(F[..., 2], nan=-1.0), rr[has], cc[has])
            front_most = np.abs(zf - gz[has]) < 0.001
            idx = tuple(a[front_most] for a in np.where(has))
            r_s, c_s = rr[has][front_most], cc[has][front_most]
            cache[key] = 1
        t_new = None
        if border_mode != "ao":
            e = bj[f]
            U = np.array(bj["u"])
            xs = hl.X0 + (np.arange(len(m)) + 0.5) * hl.D
            uu = (1000 * xs - e["cx_mm"]) / e["w_mm"]
            if "dense" in e:                                       # (round two: the target curve, corner to corner)
                U = np.array(bj["u_dense"])
                t_new = (np.interp(uu, U, e["dense"]["slit_mm"]) + np.interp(uu, U, e["dense"]["new"]) * e["w_mm"]) / 1000
                t_new[np.abs(uu) > 0.5] = np.nan
            else:
                t_new = (np.interp(uu, U, e["slit_mm"]) + np.interp(uu, U, e["crease"]) * e["w_mm"]) / 1000
                t_new[np.abs(uu) > 0.35] = np.nan
        pf = hl.at_uv(img, np.nan_to_num(F[..., 0]), np.nan_to_num(F[..., 1]))
        W, T, Sm, tt, ee, lo, up = fields(F, m, t, pf, f, t_new)
        w = hl.sample(W, r_s, c_s)
        Tt = np.stack([hl.sample(T[..., k], r_s, c_s) for k in range(3)], -1)
        L = lin(img[idx])
        own = np.clip((L @ LUMA) / np.maximum(hl.sample(Sm, r_s, c_s), 1e-4), 0.7, 1.3)
        out = img.copy()
        out[idx] = srgb(L * (1 - w[:, None]) + w[:, None] * Tt * own[:, None])
        dst = os.path.join(to, pp[f]) if to else src
        Image.fromarray(np.clip(out + 0.5, 0, 255).astype(np.uint8), "RGB").save(dst, quality=95, subsampling=0)
        mid = len(m) // 2
        po = hl.at_uv(out, np.nan_to_num(F[..., 0]), np.nan_to_num(F[..., 1]))
        band = W > 0.6
        e0 = hl.red_top(pf, m, t)
        g_ = ~np.isnan(e0)
        hband = (tt[mid] - np.interp(mid, np.where(g_)[0], e0[g_])) * 1000
        print("LIPCOLOR %-9s texels %6d  gap mid %.1f mm  | lum/redness: lower lip %.3f/%.0f  upper red %.3f/%.0f  "
              "band was %.3f/%.0f  now %.3f/%.0f  | seam step was %.3f now %.3f | band mid %.1f mm -> %s" % (
                  f, int((w > 0.05).sum()), (tt[mid] - ee[mid]) * 1000,
                  _lum(pf[lo]), _rdn(pf[lo]), _lum(pf[up]), _rdn(pf[up]), _lum(pf[band]), _rdn(pf[band]),
                  _lum(po[band]), _rdn(po[band]), _seam(pf, m, tt, ee), _seam(po, m, tt, ee), hband, dst))


def _seam(img, m, tt, ee):
    """The upper lip's worst lightness step over 0.4 mm, from 1.5 mm under the old red's top to 1 mm under the border
    (smoothed 0.3 mm; the 90th percentile over her mouth's columns, linear luminance)."""
    y = ndimage.gaussian_filter(lin(img) @ LUMA, 3)
    steps = []
    for c in np.where(~np.isnan(m) & ~np.isnan(tt) & ~np.isnan(ee))[0]:
        i0, i1 = int(hl.row(tt[c] - 0.001)), int(hl.row(ee[c] - 0.0015))
        if i1 > i0 + 5:
            p = y[i0:i1, c]
            steps.append(np.abs(p[4:] - p[:-4]).max())
    return float(np.percentile(steps, 90)) if steps else float("nan")


if __name__ == "__main__":
    main()
