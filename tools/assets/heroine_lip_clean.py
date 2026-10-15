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

    python tools/assets/heroine_lip_clean.py [--src DIR] [--to DIR] [--hi HI] [--lo LO] [--wet LIFT] FACE ...   (FACE: doe, saffron, ...; own's paint is
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
TOP, BOTTOM = -1.0, -12.0   # (mm of rest height over her lips' line: the region's top (the lips' meeting line,
#  dark in the paint, sits at -2.5..-3.5 mm and is kept) and bottom)
GUARD = 12.0      # (sRGB luma: texels this much darker than their 4 mm median, in a blob of over GUARD_N texels (the
GUARD_N = 400     #  lips' meeting line, long), are kept, 2 texels round; a crack's short dark line is not kept)
FEATHER = 0.5     # (mm)
LIFT = 1.3        # (the meeting line's band: its smoothed shading times this)
WET_IN = 1.5      # (mm inside the meeting line the band reaches)
KEEP_MEAN = 1.5   # (mm, FWHM: the scale under which the limit's loss of lightness is put back)
FRONT = -5.0      # (mm of rest height: surely the lip's front, to tell it from the inside)
FRONT_SHARE = 0.5 # (a piece of the region is the lip's front if this share of it lies under FRONT)
CUT = 3           # (texels: the meeting line widened by this to cut the front off from the inside, across gaps)


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
    # (what the limit took, put back as its local mean (KEEP_MEAN mm): the sparkle's speckle goes, its soft highlight
    # and the lip's mean colour stay)
    sg = KEEP_MEAN / 2.355 / mmpt
    out += np.dstack([ndimage.gaussian_filter((d * (1 - f[..., None]))[..., c], sg) for c in range(3)])
    L = s @ LUM
    big = ndimage.median_filter(L, max(3, int(round(4.0 / mmpt)) | 1))
    dark = L < big - GUARD
    lab, nl = ndimage.label(dark, np.ones((3, 3)))
    sz = ndimage.sum(dark, lab, range(1, nl + 1)) if nl else np.zeros(0)
    keep = ndimage.binary_dilation(np.isin(lab, 1 + np.nonzero(sz > GUARD_N)[0]), iterations=2)
    # (the lip's front only: the part of the region the meeting line cuts off from her mouth's inside)
    ms = m[y0:y1, x0:x1]
    lab, nl = ndimage.label(ms & ~ndimage.binary_dilation(keep, iterations=CUT))
    ys_ = np.nan_to_num(yl[y0:y1, x0:x1], nan=99.0)
    idx = range(1, nl + 1)
    front = ndimage.sum(ys_ < FRONT, lab, idx) / np.maximum(ndimage.sum(np.ones_like(ys_), lab, idx), 1)
    big_ = ndimage.sum(np.ones_like(ys_), lab, idx) > 200
    if os.environ.get("LIP_CLEAN_DEBUG"):
        print("  components (size, front share):", [(int(a), round(float(b), 2)) for a, b in zip(ndimage.sum(np.ones_like(ys_), lab, idx), front) if a > 200])
    ms = ndimage.binary_dilation(np.isin(lab, 1 + np.nonzero(big_ & (front > FRONT_SHARE))[0]), iterations=CUT + 1) & ms
    m = np.zeros_like(m)
    m[y0:y1, x0:x1] = ms
    fe = FEATHER / mmpt
    w = ndimage.gaussian_filter(ndimage.binary_erosion(ms, iterations=int(round(fe))).astype(float), fe)
    w = np.where(ms, w, 0.0)
    w *= 1 - (ndimage.gaussian_filter(keep.astype(float), 1.0) * 2).clip(0, 1)
    w = w.clip(0, 1)
    o = img.copy()
    o[y0:y1, x0:x1] = s * (1 - w[..., None]) + out * w[..., None]
    W = np.zeros((n, n))
    W[y0:y1, x0:x1] = w
    return o, W, m, mmpt, k


def wet_line(img, x, yl, isl, lift=LIFT):
    """The lips' meeting line and the 1.5 mm just inside it (what a snarl rolls out under her teeth as a band): its
    paint's brown taken to her lip's own rose (the front's median colour, linear light), at its own shading smoothed
    over 0.4 mm and lifted by LIFT, so the band reads as a shadowed wet lip. At rest that zone is the dark line under
    her upper lip: it keeps its shape and most of its depth."""
    n = img.shape[0]
    y0, y1, x0, x1 = 1450, 1900, 1450, 1950   # (her mouth on the shared UV, at 4096)
    k = n / 4096.0
    y0, y1, x0, x1 = (int(v * k) for v in (y0, y1, x0, x1))
    s = img[y0:y1, x0:x1]
    L = s @ LUM
    big = ndimage.median_filter(L, 31)
    dark = L < big - GUARD
    lab, nl = ndimage.label(dark, np.ones((3, 3)))
    sz = ndimage.sum(dark, lab, range(1, nl + 1))
    I = isl[y0:y1, x0:x1]
    Y = np.nan_to_num(yl[y0:y1, x0:x1], nan=99.0)
    cand = [(ndimage.sum(I & (Y > -4) & (Y < -1.5), lab, i), i) for i in 1 + np.nonzero(sz > GUARD_N)[0]]
    line = lab == max(cand)[1]
    mmpt = 0.131 * 4096 / n
    dist = ndimage.distance_transform_edt(~line)
    ly = np.median(Y[line])
    zone = line | (I & (Y > ly - 0.5) & (dist < WET_IN / mmpt))
    w = ndimage.gaussian_filter(ndimage.binary_dilation(zone, iterations=1).astype(float), 1.5).clip(0, 1)
    lin = np.where(s / 255 <= 0.04045, s / 255 / 12.92, ((s / 255 + 0.055) / 1.055) ** 2.4)
    front = I & (Y < -5) & (Y > -8)
    rose = np.median(lin[front], 0)
    ll = lin @ LUM
    sh = ndimage.gaussian_filter(ll, 0.4 / mmpt / 2.355) * lift
    new = rose[None, None, :] * (sh / (rose @ LUM))[..., None]
    new = np.where(new <= 0.0031308, 12.92 * new, 1.055 * np.clip(new, 0, 1) ** (1 / 2.4) - 0.055) * 255
    o = img.copy()
    o[y0:y1, x0:x1] = s * (1 - w[..., None]) + new * w[..., None]
    W = np.zeros((n, n))
    W[y0:y1, x0:x1] = w
    return o, W, int(zone.sum()), rose


def main():
    a = sys.argv[1:]
    opt = {"--src": hl.TEX, "--to": None, "--hi": HI, "--lo": LO, "--wet": None}
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
        if opt["--wet"] is not None:   # (--wet LIFT: the meeting line's band too, first)
            img0 = img
            img, ww, nz, rose = wet_line(img, *cache[n], lift=float(opt["--wet"]))
            print("LIP_CLEAN %s: meeting line's band %d texels, rose (linear) %s, max change %.1f"
                  % (f, nz, np.round(rose, 3), np.abs(img - img0).max()))
        if hi <= 0:   # (--hi 0: the meeting line's band only, no fleck pass)
            dst = os.path.join(to, files[f]) if to else p
            Image.fromarray(np.clip(img + 0.5, 0, 255).astype(np.uint8), "RGB").save(dst, quality=95, subsampling=0)
            print("LIP_CLEAN %s: written %s" % (f, dst))
            continue
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
