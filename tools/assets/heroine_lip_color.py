"""Her upper lip painted lip-coloured up to her sculpt's own lip border, in each face's paint.

Her sculpt's upper lip is a full, ordinary lip (9-10 mm from her mouth line to the border, its vermilion ridge and
cupid's bow), but every face's paint (laid from a portrait with a thinner upper lip) colours its top 4.4-7.6 mm as
skin. At the Look the lit ridge and her head's shade then drew the border as an outline in skin above a thin red
lip (the owner, 12 October 2026; with her shade off it still showed: it is the sculpt's). This recolours that band,
between the paint's red top and the border, to the paint's own lip colour just under its red top, column by column
across her mouth, keeping each texel's own detail (a ratio in linear light, not a warp: a stretched lip smeared).
The border's edge is soft over 0.4 mm; the band fades into the paint's red over 1 mm below its old top; toward the
corners of her mouth, where the border meets the mouth line, the band thins to nothing.

    python tools/assets/heroine_lip_color.py [--to DIR] [face ...]   (no faces: every paint; --to: write there)

Run on paints fresh from the chain (heroine_face.py's lay, heroine_jaw_cut.py, heroine_ears.py), then this. A rerun
finds the red's top at the border and changes nothing more.
"""
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import heroine_lips as hl  # noqa: E402

EDGE = 0.0004       # (the border's softness, m)
INTO = 0.0010       # (the band fades into the old red over this, below its old top)
UNDER = 0.0002      # (the new red's top this far under the crease's middle: the crease is its edge's shade)
SAMPLE = (0.0004, 0.0018)   # (the lip's colour: from this far under the old red's top to this)
NO_CREASE = 0.0095


def lin(c):
    c = c / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055) * 255


def border(m, t):
    """The border's height per column: the crease, smoothed, carried down to the mouth line at her mouth's corners."""
    ok = ~np.isnan(m)
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


def fields(F, m, t, paint_front):
    """Per front-grid pixel the band's weight, and per column the ratio (lip colour over band colour, linear)."""
    e = hl.red_top(paint_front, m, t)
    tt = border(m, t)
    ok = ~np.isnan(tt) & ~np.isnan(m)
    x = np.arange(len(m))
    ok_e = ok & ~np.isnan(e)
    ee = np.full(len(m), np.nan)
    ee[ok] = np.interp(x[ok], x[ok_e], hl.smooth_cols(e, 6)[ok_e]) if ok_e.sum() > 3 else np.nan
    ee = np.minimum(ee, tt)                                        # (never above the border)
    ys = hl.Y1 - (np.arange(F.shape[0]) + 0.5) * hl.D
    Y = ys[:, None]
    top = (tt - UNDER)[None, :]
    w_top = 1 - np.clip((Y - (top - EDGE / 2)) / EDGE, 0, 1)        # (1 under the border, 0 over it)
    w_bot = np.clip((Y - (ee[None, :] - INTO)) / INTO, 0, 1)       # (0 deep in the old red, 1 at and over its top)
    W = np.nan_to_num(w_top * w_bot) * ok[None, :]
    # (no band where the red's top is already at the border)
    gap = np.nan_to_num(tt - ee)
    W *= np.clip(gap / 0.0008, 0, 1)[None, :]
    L = lin(paint_front)
    lipc = np.full((len(m), 3), np.nan)
    band = np.full((len(m), 3), np.nan)
    for c in np.where(ok_e)[0]:
        r0, r1 = int(hl.row(ee[c] - SAMPLE[0])), int(hl.row(ee[c] - SAMPLE[1]))
        b0, b1 = int(hl.row(tt[c] - UNDER)), int(hl.row(ee[c]))
        if r1 > r0 + 2:
            lipc[c] = np.median(L[r0:r1, c], 0)
        if b1 > b0 + 2:
            band[c] = np.median(L[b0:b1, c], 0)
    ratio = np.ones((len(m), 3))
    for k in range(3):
        a, b = lipc[:, k], band[:, k]
        good = ~np.isnan(a) & ~np.isnan(b)
        if good.sum() > 3:
            r = np.interp(x, x[good], (a / np.maximum(b, 1e-4))[good])
            ratio[:, k] = ndimage.gaussian_filter1d(ndimage.median_filter(r, 15), 10)
    W = ndimage.gaussian_filter(W, 1.0)
    return W, ratio, tt, ee


def main():
    args = sys.argv[1:]
    to = None
    if "--to" in args:
        i = args.index("--to")
        to = args[i + 1]
        del args[i:i + 2]
    pp = hl.paints()
    faces = args or sorted(pp)
    P, UV, T = hl.mesh()
    F = hl.front(P, UV, T)
    ao = np.asarray(Image.open(os.path.join(hl.TEX, "heroine_ao.png")).convert("RGBA")).astype(np.float64)[..., 0] / 255
    m, t, _, _ = hl.lines(F, ao)
    G = None
    for f in faces:
        src = os.path.join(hl.TEX, pp[f])
        img = np.asarray(Image.open(src).convert("RGB")).astype(np.float64)
        n = img.shape[0]
        if G is None or G.shape[0] != n:
            G = hl.in_uv(P, UV, T, n, None)
            gx, gy, gz = G[..., 0], G[..., 1], G[..., 2]
            has = ~np.isnan(gx)
            rr, cc = hl.row(np.nan_to_num(gy)), hl.col(np.nan_to_num(gx))
            has &= (rr >= 0) & (rr < F.shape[0] - 1) & (cc >= 0) & (cc < F.shape[1] - 1)
            zf = hl.sample(np.nan_to_num(F[..., 2], nan=-1.0), rr[has], cc[has])
            front_most = np.abs(zf - gz[has]) < 0.001
            idx = tuple(a[front_most] for a in np.where(has))
            r_s, c_s = rr[has][front_most], cc[has][front_most]
        pf = hl.at_uv(img, np.nan_to_num(F[..., 0]), np.nan_to_num(F[..., 1]))
        W, ratio, tt, ee = fields(F, m, t, pf)
        w = hl.sample(W, r_s, c_s)
        rat = np.stack([np.interp(c_s, np.arange(len(m)), ratio[:, k]) for k in range(3)], -1)
        L = lin(img[idx])
        out = img.copy()
        out[idx] = srgb(L * (1 + w[:, None] * (rat - 1)))
        dst = os.path.join(to, pp[f]) if to else src
        Image.fromarray(np.clip(out + 0.5, 0, 255).astype(np.uint8), "RGB").save(dst, quality=95, subsampling=0)
        mid = len(m) // 2
        print("LIPCOLOR %-9s texels %6d  gap mid %.1f mm  ratio mid %s -> %s" % (
            f, int((w > 0.05).sum()), (tt[mid] - ee[mid]) * 1000, np.round(ratio[mid], 2), dst))


if __name__ == "__main__":
    main()
