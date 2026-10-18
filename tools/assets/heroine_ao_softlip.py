"""Her head's shade with the crease along her sculpt's upper-lip border eased out: heroine_ao_softlip.png.

Her head has no normal map; its shade (heroine_ao.png's red) draws her sculpt's upper-lip border, the vermilion edge
and its cupid's bow, as a thin dark crease. Every face's paint puts the red of her upper lip 4.4-7.6 mm under that
border (the portraits' upper lips are thinner than the sculpt's: heroine_lips.py --measure), so at the Look the
crease read as an outline in skin above her lip (the owner, 12 October 2026). This is the cheap answer, (b): each
face keeps its portrait's lip, and the crease's dip is filled, from 3 mm over her mouth line up to 2.5 mm over the
crease, by a grey closing wider than the crease (never darker than it was), so her mouth line, the shade under
her nose and the corners of her mouth stay as baked. The fuller-lipped answer, (a), lifts each paint's
red to the crease instead (heroine_lips.py, WIP). People.HerSoftLipAo picks this map.

    python tools/assets/heroine_ao_softlip.py            (from heroine_ao.png; writes heroine_ao_softlip.png beside it)
    python tools/assets/heroine_ao_softlip.py --fill [OUT]   (with the upper-lip sculpt, heroine_lipsculpt.py: the
        band filled whole, see fill(); writes heroine_ao_softlip.png, or OUT)

--fill (solver ls5, 12 October 2026, WIP, UNJUDGED): with her upper lip sculpted down (heroine_lipsculpt.py) the old
border is skin, but the closing above still left a faint line along it and the old lip's tone (light lip, grey skin
over it) drew the old lip's shape at the Look, a pale band capped by a line (judge j8b). fill() lays, column by
column seen from in front, a smooth ease from the shade 3 mm over her mouth line to the shade FILL_HI over the old
crease in place of everything between: no line, no tone step; her mouth line, the corners of her mouth and the
shade under her nose stay as baked.
"""
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import heroine_lips as hl  # noqa: E402

LO = 0.0030     # (the fill starts this far over her mouth line)
HI = 0.0025     # (and ends this far over the crease)
NO_CREASE = 0.0095   # (where no crease is found: the crease taken this far over the mouth line)
CLOSE = 7            # (texels: wider than the crease, narrower than her mouth line's shade)
XMAX = 0.024         # (out to her mouth's corners)


def main():
    src = os.path.join(hl.TEX, "heroine_ao.png")
    out = os.path.join(hl.TEX, "heroine_ao_softlip.png")
    img = np.asarray(Image.open(src).convert("RGBA")).astype(np.float64)
    ao = img[..., 0] / 255
    P, UV, T = hl.mesh()
    F = hl.front(P, UV, T)
    m, t, depth, a = hl.lines(F, ao)
    # (the crease's line smoothed across her, and carried past where it fades with the mouth line's shape)
    ok = ~np.isnan(m)
    tt = np.where(np.isnan(t), m + NO_CREASE, t)
    tt[ok] = ndimage.gaussian_filter1d(tt[ok], 8)
    xs = hl.X0 + (np.arange(len(m)) + 0.5) * hl.D
    # The crease is a thin dark line: a grey closing wider than it fills it and leaves the broad shade (her mouth
    # line, her nostrils) as it was. Laid only between her mouth line and the crease (seen from in front), feathered.
    closed = ndimage.gaussian_filter(ndimage.grey_closing(ao, size=(CLOSE, CLOSE)), 2.5)   # (smoothed: a bare closing left flat blocks)
    n = ao.shape[0]
    G = hl.in_uv(P, UV, T, n, None)
    gx, gy, gz = G[..., 0], G[..., 1], G[..., 2]
    has = ~np.isnan(gx)
    mx = np.interp(np.nan_to_num(gx), xs[ok], m[ok])
    tx = np.interp(np.nan_to_num(gx), xs[ok], tt[ok])
    rr, cc = hl.row(np.nan_to_num(gy)), hl.col(np.nan_to_num(gx))
    zf = np.full(ao.shape, -1.0)
    zf[has] = hl.sample(np.nan_to_num(F[..., 2], nan=-1.0), np.clip(rr[has], 0, F.shape[0] - 1), np.clip(cc[has], 0, F.shape[1] - 1))
    mask = (has & (np.abs(zf - np.nan_to_num(gz)) < 0.001) & (gy > mx + LO) & (gy < tx + HI)
            & (np.abs(np.nan_to_num(gx)) < XMAX)).astype(np.float64)
    mask = ndimage.gaussian_filter(mask, 1.5)
    d = np.maximum(closed - ao, 0) * mask
    new = img.copy()
    new[..., 0] = np.clip((ao + d) * 255 + 0.5, 0, 255)
    Image.fromarray(new.astype(np.uint8), "RGBA").save(out)
    print("SOFTLIP written", out, "texels lifted: %d, most %.1f/255, mean %.1f" %
          ((d > 1 / 255).sum(), d.max() * 255, d[d > 1 / 255].mean() * 255))


FILL_HI = 0.0035      # (the fill's top: this far over the old crease)
FILL_LO = 0.0025      # (its foot: this far over her mouth line)


def fill(out=None):
    src = os.path.join(hl.TEX, "heroine_ao.png")
    out = out or os.path.join(hl.TEX, "heroine_ao_softlip.png")
    img = np.asarray(Image.open(src).convert("RGBA")).astype(np.float64)
    ao = img[..., 0] / 255
    P, UV, T = hl.mesh()
    F = hl.front(P, UV, T)
    m, t, depth, a = hl.lines(F, ao)
    ok = ~np.isnan(m)
    xs = hl.X0 + (np.arange(len(m)) + 0.5) * hl.D
    tt = np.where(np.isnan(t), m + NO_CREASE, t)
    tt[ok] = ndimage.gaussian_filter1d(tt[ok], 8)
    m_s = m.copy()
    m_s[ok] = ndimage.gaussian_filter1d(m[ok], 4)
    # (the shade seen from in front, unblurred across: its value at the fill's foot and top per column)
    A = hl.at_uv(ao, np.nan_to_num(F[..., 0]), np.nan_to_num(F[..., 1]))
    y_lo, y_hi = m_s + FILL_LO, tt + FILL_HI
    cols = np.arange(len(m))
    a_lo = np.full(len(m), np.nan)
    a_hi = np.full(len(m), np.nan)
    for c in np.where(ok)[0]:
        a_lo[c] = np.median(A[int(hl.row(y_lo[c])) - 2:int(hl.row(y_lo[c])) + 3, c])
        a_hi[c] = np.median(A[int(hl.row(y_hi[c])) - 3:int(hl.row(y_hi[c])) + 4, c])
    a_lo[ok] = ndimage.gaussian_filter1d(a_lo[ok], 6)
    a_hi[ok] = ndimage.gaussian_filter1d(a_hi[ok], 6)
    n = ao.shape[0]
    G = hl.in_uv(P, UV, T, n, None)
    gx, gy, gz = G[..., 0], G[..., 1], G[..., 2]
    has = ~np.isnan(gx)
    X = np.nan_to_num(gx)
    lo, hi = np.interp(X, xs[ok], y_lo[ok]), np.interp(X, xs[ok], y_hi[ok])
    alo, ahi = np.interp(X, xs[ok], a_lo[ok]), np.interp(X, xs[ok], a_hi[ok])
    rr, cc = hl.row(np.nan_to_num(gy)), hl.col(X)
    zf = np.full(ao.shape, -1.0)
    zf[has] = hl.sample(np.nan_to_num(F[..., 2], nan=-1.0), np.clip(rr[has], 0, F.shape[0] - 1), np.clip(cc[has], 0, F.shape[1] - 1))
    Y = np.nan_to_num(gy)
    h = np.clip((Y - lo) / np.maximum(hi - lo, 1e-4), 0, 1)
    ease = alo + (ahi - alo) * h * h * (3 - 2 * h)
    inside = has & (np.abs(zf - np.nan_to_num(gz)) < 0.001) & (Y > lo) & (Y < hi) & (np.abs(X) < XMAX)
    mask = ndimage.gaussian_filter(inside.astype(np.float64), 1.5)
    # (feathered to nothing at her mouth's corners, where the corners' own shade is kept)
    mask *= np.clip((XMAX - np.abs(X)) / 0.003, 0, 1)
    new = img.copy()
    val = np.where(inside, ease, ao)
    val = ao + (ndimage.gaussian_filter(np.where(inside, val, 0), 1.0) / np.maximum(ndimage.gaussian_filter(inside.astype(float), 1.0), 1e-6) - ao) * mask
    val = np.where(mask > 1e-3, val, ao)
    new[..., 0] = np.clip(val * 255 + 0.5, 0, 255)
    Image.fromarray(new.astype(np.uint8), "RGBA").save(out)
    d = (val - ao)[mask > 1e-3]
    print("SOFTLIP --fill written", out, "texels changed: %d, lifted most %.1f/255, lowered most %.1f/255"
          % ((np.abs(d) > 1 / 255).sum(), d.max() * 255, -d.min() * 255))


if __name__ == "__main__":
    if "--fill" in sys.argv:
        i = sys.argv.index("--fill")
        fill(sys.argv[i + 1] if len(sys.argv) > i + 1 else None)
    else:
        main()
