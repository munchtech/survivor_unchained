"""Her ears' bowls (the concha) in each face's paint warmed to the ear's own shadow tone.

The bowl behind her tragus kept the base head's paint, pale and grey (heroine_ears.py scales the whole ear by one
gain, so the bowl stayed greyer than the ear round it: Own's at 0.70-0.80 of the ear's chroma). In the Look at 40
degrees every face's bowl read cool blue-grey beside the warm ear and lobe (judge rj4v, 13 October 2026).

On her head's surface, not its UV islands (as heroine_lobe.py): each texel near her ears is given its point on her
head and tones are smoothed over her surface in 3D (SIGMA), so no seam of the UV layout shows. Per face, per ear, in
Oklab: the bowl's local tone (its paint smoothed at SIGMA) is moved to the ear's own shadow tone (the median of the
ear's outer face, HUE degrees redder and DARK lighter-than-darker, as the ear's own folds are painted), where it falls
short of it: its chroma raised to it, its hue turned to it, its lightness lowered to it where paler (the canal's
dark kept). The paint's grain and shading under SIGMA are kept. Eased in over the bowl (a sphere round CENTRE,
R0 to R1) and the ear (heroine_ears.py's reach), and above the lobe (heroine_lobe.py's, from Y_LOW).
Idempotent: a rerun finds the bowl at the tone and writes nothing.

    python tools/assets/heroine_concha.py [--from DIR] [face ...]   (no faces: all ten paints in godot/art/people/head_tex)

Run after heroine_ears.py and heroine_lobe.py. Touches nothing outside R1 of CENTRE or below Y_LOW[0].
"""
import os
import re
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import heroine_lobe as hl  # noqa: E402

TEX = hl.TEX
CENTRE = (0.070, 1.729, -0.006)     # (the bowl's middle, |x| y z, metres)
R0, R1 = 0.010, 0.014               # (all of the bowl within the first, eased out by the second)
Y_LOW = (1.714, 1.720)              # (eased in above the lobe)
SIGMA = 0.0012                      # (the bowl's local tone; finer is its grain and kept)
HUE, DARK = -4.0, 0.02              # (the ear's shadow tone: hue degrees from its outer face's, Oklab L below it)
DEEP = (0.050, 0.054)               # (|x|: the bowl's deep floor taken in from the first, all of it past the second)
BOX = (0.045, 1.700, 1.760, -0.040, 0.020)
PAD = 12

M1 = np.array([[0.4122214708, 0.5363325363, 0.0514459929], [0.2119034982, 0.6806995451, 0.1073969566],
               [0.0883024619, 0.2817188376, 0.6299787005]])
M2 = np.array([[0.2104542553, 0.7936177850, -0.0040720468], [1.9779984951, -2.4285922050, 0.4505937099],
               [0.0259040371, 0.7827717662, -0.8086757660]])
def oklab(c): return np.cbrt(np.clip(c, 0, None) @ M1.T) @ M2.T
def unoklab(c): return (c @ np.linalg.inv(M2).T) ** 3 @ np.linalg.inv(M1).T


def zone(pos, side):
    ax = pos[:, 0] * side
    q = np.c_[ax, pos[:, 1], pos[:, 2]]
    d = np.linalg.norm(q - np.array(hl.EAR), axis=1)
    ear = (1 - hl.smooth(hl.EAR_R[0], hl.EAR_R[1], d)) * hl.smooth(0.062, 0.067, ax)
    # (the bowl's floor runs deeper than the ear's reach: its deepest part, |x| 0.055-0.064 behind her tragus, kept
    # the base head's grey (Own's left ear chroma 0.04 against its ear's 0.10, Sunborn's paler than its ear); taken in
    # to DEEP behind z 0, so her cheek in front of the tragus stays as it was; ear7, 13 October 2026)
    deep = (1 - hl.smooth(hl.EAR_R[0], hl.EAR_R[1], d)) * hl.smooth(DEEP[0], DEEP[1], ax) \
        * (1 - hl.smooth(-0.002, 0.002, pos[:, 2]))
    b = 1 - hl.smooth(R0, R1, np.linalg.norm(q - np.array(CENTRE), axis=1))
    return np.maximum(ear, deep) * b * hl.smooth(Y_LOW[0], Y_LOW[1], pos[:, 1]), ear


def run(faces, src_dir):
    P, N, UV, T = hl.head()
    hl.BOX = BOX
    paints = {"own": "heroine_head.jpg"}
    for f in os.listdir(TEX):
        m = re.fullmatch(r"heroine_head_(\w+)\.jpg", f)
        if m: paints[m.group(1)] = f
    cache = {}
    for face in faces or sorted(paints):
        path = os.path.join(TEX, paints[face])
        im = np.asarray(Image.open(os.path.join(src_dir or TEX, paints[face])).convert("RGB")).astype(np.float64) / 255
        size = im.shape[0]
        L = hl.lin(im)
        out = L.copy()
        notes, laid, changed = [], True, 0
        for side in (-1, 1):
            if (side, size) not in cache:
                r, c, pos, nrm = hl.texels(P, N, UV, T, side, size)
                z, ear = zone(pos, side)
                ch = z > 0
                box = (max(c[ch].min() - PAD - 2, 0), max(r[ch].min() - PAD - 2, 0),
                       min(c[ch].max() + PAD + 3, size), min(r[ch].max() + PAD + 3, size))
                cache[side, size] = (r, c, pos, z, ear, box, hl.covered(UV, T, size, box))
            r, c, pos, z, ear, box, cov = cache[side, size]
            lab = oklab(L[r, c])
            ls = hl.smoothed(pos, lab, SIGMA)
            # the ear's outer face, clear of the bowl and above the lobe: its tone, turned HUE and DARK lower
            dc = np.linalg.norm(np.c_[pos[:, 0] * side, pos[:, 1], pos[:, 2]] - np.array(CENTRE), axis=1)
            ref = (ear > 0.95) & (dc > R1 + 0.002) & (pos[:, 1] > 1.722)
            o = np.median(ls[ref], 0)
            h = np.arctan2(o[2], o[1]) + np.radians(HUE)
            u, v = np.array([np.cos(h), np.sin(h)]), np.array([-np.sin(h), np.cos(h)])
            Ct, Lt = np.hypot(o[1], o[2]), o[0] - DARK
            # where the bowl's local tone falls short of it: chroma up to it, hue to it, lightness down to it
            par, perp = ls[:, 1:] @ u, ls[:, 1:] @ v
            d = np.zeros_like(lab)
            d[:, 0] = np.minimum(0.0, Lt - ls[:, 0])
            d[:, 1:] = np.maximum(0.0, Ct - par)[:, None] * u - perp[:, None] * v
            core = z > 0.97
            laid &= bool(np.median(np.abs(d[core]), 0).max() < 0.004)
            new = unoklab(lab + d * z[:, None])
            out[r, c] = np.clip(new, 0, 1)
            # (the islands' padding round what changed takes its nearest texel's change, as heroine_lobe.py)
            x0, y0, x1, y1 = box
            ratio = np.ones((y1 - y0, x1 - x0, 3))
            ib = (r >= y0) & (r < y1) & (c >= x0) & (c < x1)
            ratio[r[ib] - y0, c[ib] - x0] = out[r[ib], c[ib]] / np.maximum(L[r[ib], c[ib]], 1e-5)
            _, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
            dist = ndimage.distance_transform_edt(~cov)
            pad = (~cov) & (dist <= PAD)
            sub = out[y0:y1, x0:x1]
            sub[pad] = L[y0:y1, x0:x1][pad] * ratio[iy[pad], ix[pad]]
            cs = np.hypot(ls[core, 1], ls[core, 2])
            notes.append("ear %+d: bowl chroma %.2f of the ear's, hue %+.1f, L %+.3f (core %d texels)" % (
                side, np.median(cs) / Ct, np.degrees(np.median(np.arctan2(ls[core, 2], ls[core, 1])) - h), np.median(ls[core, 0]) - Lt, core.sum()))
        if laid and not src_dir:
            print("CONCHA %-9s already laid (its bowls at the ear's shadow tone), not written" % face)
            continue
        o8 = (np.clip(hl.srgb(np.clip(out, 0, 1)), 0, 1) * 255 + 0.5).astype(np.uint8)
        i8 = (im * 255 + 0.5).astype(np.uint8)
        diff = np.abs(o8.astype(int) - i8.astype(int)).max(-1)
        Image.fromarray(o8).save(path, quality=95, subsampling=0)
        print("CONCHA %-9s texels changed %d (>=2/255: %d), max %d/255; %s" % (face, (diff > 0).sum(), (diff >= 2).sum(), diff.max(), "; ".join(notes)))


if __name__ == "__main__":
    args = sys.argv[1:]
    src = None
    if args[:1] == ["--from"]:
        src, args = args[1], args[2:]
    run(args, src)
