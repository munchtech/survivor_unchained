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
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import heroine_lips as hl  # noqa: E402

EDGE = 0.0007       # (the border's softness, m: smoothstep; 0.4 read stickered on Doe)
INTO = 0.0012       # (the band ramps from the old red over this, below its old top: a step showed at 1.0 linear)
UNDER = 0.0002      # (the new red's top this far under the crease's middle: the crease is its edge's shade)
LOWER = (0.0035, 0.0115)    # (the lip's colour: her LOWER lip's red, this far under the mouth line. Over 3.5 mm the
                            #  paints carry the portrait's dark mouth gap; the upper red's top sits in the mouth
                            #  line's shade and read darker and rosier than her lower lip)
NO_CREASE = 0.0095
LUMA = np.array([0.2126, 0.7152, 0.0722])
DARK = 0.85                 # (the band against her lower lip's mid-tones, linear: the upper lip a shade darker, judge j8a)
TOWARD_UPPER = 0.25         # (its hue and chroma this far toward her old upper red)
CHROMA = {"moonlit": 0.9, "wildling": 0.9, "fey": 0.9}   # (read pinker than the numbers in the engine, j8a)
CARRY_UPPER = {"sunborn"}   # (her portrait's upper lip is dark brown-mauve, far darker than her lower: carry it up)
TOP_LIFT = {"sunborn": 0.10}   # (lightened toward the border by at most this)
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


def fields(F, m, t, paint_front, face=""):
    """Per front-grid pixel the band's weight W and its target colour (linear, with her lower lip's vertical lines),
    and the paint's smoothed luminance (each texel keeps its own fine detail against it)."""
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
    # (the target: her lower lip a shade darker, its hue a quarter of the way to her old upper red (at the lower lip's
    #  lightness), as every portrait's upper lip sits a shade darker and more mauve than its lower)
    up_at = upc * ((lipc @ LUMA) / np.maximum(upc @ LUMA, 1e-4))[:, None]
    tgt = DARK * ((1 - TOWARD_UPPER) * lipc + TOWARD_UPPER * up_at)
    if face in CARRY_UPPER:                                        # (her upper red carried up whole: Sunborn)
        tgt = upc.copy()
    g = (tgt @ LUMA)[:, None]
    tgt = g + (tgt - g) * CHROMA.get(face, 1.0)
    T = np.repeat(tgt[None, :, :], F.shape[0], 0)
    lift = TOP_LIFT.get(face, 0.0)
    if lift:
        h = np.clip((Y - ee[None, :]) / np.maximum((tt - ee)[None, :], 1e-4), 0, 1)
        T = T * (1 + lift * np.nan_to_num(h))[..., None]
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
        W, T, Sm, tt, ee, lo, up = fields(F, m, t, pf, f)
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
        print("LIPCOLOR %-9s texels %6d  gap mid %.1f mm  | lum/redness: lower lip %.3f/%.0f  upper red %.3f/%.0f  "
              "band was %.3f/%.0f  now %.3f/%.0f  | seam step was %.3f now %.3f -> %s" % (
                  f, int((w > 0.05).sum()), (tt[mid] - ee[mid]) * 1000,
                  _lum(pf[lo]), _rdn(pf[lo]), _lum(pf[up]), _rdn(pf[up]), _lum(pf[band]), _rdn(pf[band]),
                  _lum(po[band]), _rdn(po[band]), _seam(pf, m, tt, ee), _seam(po, m, tt, ee), dst))


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
