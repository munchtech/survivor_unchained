"""Her paint under each brow brought down to her upper lid's own level, in each face's paint (the brow fold's partner).

Her head's sculpt folds sharply into each upper lid's crease, right under the brow, and under the Look's key light that
crease drew a dark band under her brow (the owner, 12 October 2026: "double eyebrow"). Each face's paint had been
painted 15-20% lighter there, from the lid's crease up to the brow, against that shade. heroine_browfold.py now turns
the crease's normals into a soft fold, so the shade is gone, and the lighter paint read as a light band instead.

This brings that band's paint down to her lid's: over the brow fold's own band (heroine_browfold.band: from just above
each upper lid's lash line to the brow's lower edge, eased out into the brow and at the eyes' corners, found on each
face's own shape with its own paint's brows), each texel's broad lightness (the paint's luma over her skin, its hairs left out, blurred by LOW texels) is
held to her lid's (the median of the paint on her lid's front, LID mm above the lash line, measured along each lid and
eased between). Only lighter texels are touched, by one gain on their colour, so the grain, the brow's hairs and
everything darker stay as painted. The paint is written again at the chain's 95, 4:4:4.

    python tools/assets/heroine_browpaint.py [face ...]            (no faces: all ten; own is heroine_head.jpg)
    python tools/assets/heroine_browpaint.py --measure [face ...]  (per face: her lid's level, the band before and after)

The chain: heroine_face.py's lay, heroine_jaw_cut.py, heroine_ears.py, heroine_lips.py, heroine_nostrils.py, then this
(it touches only the skin between her upper lids and brows). Its band comes from heroine.glb's head with the brow fold
done (it needs the shapes, not the fold). Run once per paint: a face whose crease's lightest tenth is no more than TOL
over her lid (its own paint after this: +1-6%; before it: +18-30%, Moonlit's +6%) is left as it is.
"""
import os
import sys

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, map_coordinates

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import heroine_seam as hs  # noqa: E402
import heroine_browfold as bf  # noqa: E402
from heroine_nostrils import raster  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TEX = os.path.join(ROOT, "godot", "art", "people", "head_tex")
GLB = os.path.join(ROOT, "godot", "art", "people", "heroine.glb")
LOW = 8.0             # (texels: the paint's broad lightness, over her skin only, under its grain and mottling)
HAIR = (5.0, 24.0, 0.045 * 255)  # (a texel this much darker than the skin round it (blurs in texels) is brow or lash)
LID = (0.0012, 0.0028)  # (m above the lash line, along her skin: her lid's front, the level the band is held to)
BINS = 12             # (along each lid, inner corner to outer: her lid's level measured in this many pieces)
CREASE = (0.0035, 0.002)  # (m: the crease measured from this far over the lash line to this far short of the brow)
TOL = 0.08            # (a face whose crease's lightest tenth is no more than this over her lid is left: done already)
FACES = ["own", "doe", "fey", "hardwon", "highborn", "moonlit", "saffron", "sunborn", "vixen", "wildling"]


def paint_path(face):
    return os.path.join(TEX, "heroine_head%s.jpg" % ("" if face == "own" else "_" + face))


def luma(a):
    return a[..., 0] * 0.299 + a[..., 1] * 0.587 + a[..., 2] * 0.114


def broad(Y):
    """The paint's broad lightness over her skin only: its brows' and lashes' hairs left out of the average."""
    skin = (gaussian_filter(Y, HAIR[1]) - gaussian_filter(Y, HAIR[0]) < HAIR[2]).astype(np.float64)
    return gaussian_filter(Y * skin, LOW) / np.maximum(gaussian_filter(skin, LOW), 1e-3)


def gains(T, P, w, info, img):
    """The gain per texel (1 where untouched) for one face's paint img (float 0-255), and its numbers."""
    n = img.shape[0]
    low = broad(luma(img))
    uv = T.UV[T.pick]
    Lp = map_coordinates(low, [uv[:, 1] * n - 0.5, uv[:, 0] * n - 0.5], order=1, mode="nearest")
    d, src = info["d_up"], info["src"].clip(0)
    frac = np.array([T.s_in.get(i, 0) / max(T.s_in.get(i, 0) + T.s_out.get(i, 0), 1e-9) for i in src])
    side = np.sign(P[:, 0])
    # (her lid's front: off its rolled margin, away from the corners, where the lower lid is near too)
    lid = T.inmain & ~info["marg"] & np.isfinite(d) & (d >= LID[0]) & (d <= LID[1]) & (frac > 0.12) & (frac < 0.88)
    # (her lid's level along each lid: a median per piece, empty pieces from their neighbours)
    level = np.full(T.n, np.nan)
    per = {}
    for sd in (-1, 1):
        cen = (np.arange(BINS) + 0.5) / BINS
        med = np.array([np.median(Lp[m]) if (m := lid & (side == sd) & (frac >= b / BINS) & (frac < (b + 1) / BINS)).sum() >= 3
                        else np.nan for b in range(BINS)])
        ok = np.isfinite(med)
        med = np.interp(cen, cen[ok], med[ok])
        med = np.convolve(np.r_[med[0], med, med[-1]], [0.25, 0.5, 0.25], "valid")
        sel = side == sd
        level[sel] = np.interp(frac[sel], cen, med)
        per[sd] = med
    band = w > 1e-4
    # (the band's weight and her lid's level, laid in the paint by her UVs over the triangles that touch the band)
    rep = T.rep
    F = T.F[T.main_v[T.F[:, 0]]]
    tris = np.where(band[rep[F]].any(1))[0]
    vals = np.zeros((len(T.V), 2))
    vals[:, 0] = w[rep]
    vals[:, 1] = np.nan_to_num(level[rep], nan=0.0)
    lay = raster(T.UV, F, vals, tris, n)
    m = np.nan_to_num(lay[..., 0], nan=0.0)
    lv = lay[..., 1]
    ok = (m > 1e-4) & np.isfinite(lv) & (lv > 0)
    g = np.ones_like(low)
    g[ok] = np.minimum(1.0, lv[ok] / np.maximum(low[ok], 1.0))
    gain = 1.0 - m * (1.0 - g)
    gain[~ok] = 1.0
    return gain, dict(per=per, Lp=Lp, band=band, w=w, level=level)


def apply(faces, measure_only=False):
    glb = GLB
    js, binc = hs._load(glb)
    T, hm, hp, names, bands = bf.plan(js, binc, glb, faces=faces)
    for face in faces:
        w, info, _, P = bands[face]
        path = paint_path(face)
        img = np.asarray(Image.open(path).convert("RGB")).astype(np.float64)
        gain, nb = gains(T, P, w, info, img)
        out = img * gain[..., None]
        # (the crease: the band's middle, off the lid's ease and short of the brow)
        d = info["d_up"]
        core = (w > 0.5) & (d >= CREASE[0]) & (d <= info["gap"] - CREASE[1])
        uv = T.UV[T.pick]
        n = img.shape[0]
        after = map_coordinates(broad(luma(out)), [uv[:, 1] * n - 0.5, uv[:, 0] * n - 0.5], order=1, mode="nearest")
        r0, r1 = nb["Lp"][core] / nb["level"][core], after[core] / nb["level"][core]
        print("%-9s lid %3.0f/%3.0f (R/L); crease over lid: before median %+3.0f%% p90 %+3.0f%%, after median %+3.0f%% "
              "p90 %+3.0f%%; gain min %.3f" % (face, np.median(nb["per"][-1]), np.median(nb["per"][1]),
                                              100 * (np.median(r0) - 1), 100 * (np.percentile(r0, 90) - 1),
                                              100 * (np.median(r1) - 1), 100 * (np.percentile(r1, 90) - 1), gain.min()))
        if measure_only:
            continue
        if np.percentile(r0, 90) - 1 <= TOL:
            print("BROWPAINT: %s already level - left" % face)
            continue
        Image.fromarray(np.clip(out + 0.5, 0, 255).astype(np.uint8)).save(path, quality=95, subsampling=0)
        print("BROWPAINT: written", path)


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["--measure"]:
        apply(a[1:] or FACES, measure_only=True)
    else:
        apply(a or FACES)
