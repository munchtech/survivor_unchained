"""Her lower lip's paint cleaned of flecks and creases (face lead 26's paint solver, 14 October 2026; UNJUDGED).

A max judge found, at 2x on the Look, a cluster of whitish flecks between the lip lines on Doe's lower lip (centre-left)
and a thin red crease at its middle (the owner's "smudges or missing paint" on B3-15; milder on Saffron). They are the
source portrait's sparkle and a lip crack, baked into the paint. On her lower lip's front (the texels mouth_open takes
down with her jaw, inside heroine_features.png's lip green, from 1 mm under her lips' line down: heroine_inner_lip.roll
places each texel in mm) each texel's difference from its local median (BASE mm across) is soft-limited:

  - lighter than the median: to at most HI (sRGB 0-255 luma, tanh), so sparkle and pale flecks sink into the lip;
  - darker: to at most LO, so the lip lines (her texture) keep their shade but a crack's red line is cut back;
  - the colour of the detail goes with its lightness (a fleck takes its median's colour as it fades).

The region is feathered (FEATHER mm) at the lip's border and its inner edge, so the B3-15 border, shape and colour family
stay; the lips' mean colour moves well under 2%. Nothing outside the region changes.

    python tools/assets/heroine_lip_clean.py [--src DIR] [--to DIR] [--hi HI] [--lo LO] FACE ...   (FACE: doe, saffron, ...; own's paint is
    heroine_head.jpg)

Run after heroine_lip_raise.py / heroine_lip_meet.py (and heroine_inner_lip.py where a face has it).
"""
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import heroine_inner_lip as il  # noqa: E402
import heroine_lips as hl  # noqa: E402

FEATURES = os.path.join(hl.TEX, "heroine_features.png")
LUM = np.array([0.299, 0.587, 0.114])
BASE = 2.4        # (mm: the median's window, across)
HI, LO = 3.0, 9.0  # (sRGB luma: the most a texel may sit over / under its median)
TOP, BOTTOM = -2.2, -12.0   # (mm of rest height over her lips' line: the region's top (the lips' meeting line,
#  dark in the paint, sits at -2.5..-3.5 mm and is kept) and bottom)
GUARD = 25.0      # (sRGB luma: texels this much darker than their 4 mm median (the meeting line) are kept, 3 texels round)
FEATHER = 0.5     # (mm)


def region(n, x, yl, isl):
    g = np.asarray(Image.open(FEATURES).convert("RGB").resize((n, n), Image.BILINEAR)).astype(float)[..., 1] / 255
    y = np.nan_to_num(yl, nan=99.0)
    m = isl & (g > 0.1) & (y < TOP) & (y > BOTTOM) & (np.abs(np.nan_to_num(x, nan=99.0)) < 25)
    return m


def clean(img, x, yl, isl, hi=HI, lo=LO):
    """img sRGB 0-255 float (n x n x 3) -> cleaned copy, the feathered weight, and the hard region."""
    n = img.shape[0]
    m = region(n, x, yl, isl)
    ys, xs = np.nonzero(m)
    pad = 40
    y0, y1, x0, x1 = ys.min() - pad, ys.max() + pad, xs.min() - pad, xs.max() + pad
    s = img[y0:y1, x0:x1]
    # texel size in mm, from the x map across the region
    gx = np.nanmedian(np.abs(np.diff(x[y0:y1, x0:x1], axis=1))[m[y0:y1, x0:x1][:, 1:]])
    gy = np.nanmedian(np.abs(np.diff(yl[y0:y1, x0:x1], axis=0))[m[y0:y1, x0:x1][1:]])
    mmpt = float(np.hypot(gx, gy))
    k = max(3, int(round(BASE / mmpt)) | 1)
    med = np.dstack([ndimage.median_filter(s[..., c], k) for c in range(3)])
    d = s - med
    dl = d @ LUM
    lim = np.where(dl > 0, hi * np.tanh(dl / hi), -lo * np.tanh(-dl / lo))
    f = np.where(np.abs(dl) > 1e-3, lim / np.where(np.abs(dl) > 1e-3, dl, 1), 1.0)
    out = med + d * f[..., None]
    fe = FEATHER / mmpt
    w = ndimage.gaussian_filter(ndimage.binary_erosion(m[y0:y1, x0:x1], iterations=int(round(fe))).astype(float), fe)
    w = np.where(m[y0:y1, x0:x1], w, 0.0)
    L = s @ LUM
    big = ndimage.median_filter(L, max(3, int(round(4.0 / mmpt)) | 1))
    keep = ndimage.binary_dilation(L < big - GUARD, iterations=3)
    w *= 1 - ndimage.gaussian_filter(keep.astype(float), 1.5).clip(0, 1) * 2
    w = w.clip(0, 1)
    o = img.copy()
    o[y0:y1, x0:x1] = s * (1 - w[..., None]) + out * w[..., None]
    W = np.zeros((n, n))
    W[y0:y1, x0:x1] = w
    return o, W, m, mmpt, k


def main():
    a = sys.argv[1:]
    opt = {"--src": hl.TEX, "--to": None, "--hi": HI, "--lo": LO}
    for flag in list(opt):
        if flag in a:
            i = a.index(flag)
            opt[flag] = a[i + 1]
            del a[i:i + 2]
    src, to, hi, lo = opt["--src"], opt["--to"], float(opt["--hi"]), float(opt["--lo"])
    files = hl.paints()
    cache = {}
    for f in a:
        p = os.path.join(src, files[f])
        img = np.asarray(Image.open(p).convert("RGB")).astype(np.float64)
        n = img.shape[0]
        if n not in cache:
            cache[n] = il.roll(n)
        out, w, m, mmpt, k = clean(img, *cache[n], hi=hi, lo=lo)
        sel = w > 0.5
        before, after = img[m].mean(0), out[m].mean(0)
        dst = os.path.join(to, files[f]) if to else p
        Image.fromarray(np.clip(out + 0.5, 0, 255).astype(np.uint8), "RGB").save(dst, quality=95, subsampling=0)
        print("LIP_CLEAN %s: %d texels (%.3f mm/texel, median %d); lip mean %s -> %s (%.2f%%); max change %.1f; %s"
              % (f, int(sel.sum()), mmpt, k, np.round(before, 1), np.round(after, 1),
                 100 * np.abs(after - before).max() / before.mean(), np.abs(out - img).max(), dst))


if __name__ == "__main__":
    main()
