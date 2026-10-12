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


if __name__ == "__main__":
    main()
