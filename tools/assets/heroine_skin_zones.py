"""Her face's skin zones, two maps in her head's UV (soft, low frequency, mirrored left to right by construction):

    heroine_skin_zones.png   colour: R flush (cheeks, nose, ears, lip line, a little chin), G yellow (forehead),
                             B cool (under the eyes, along the jaw, under the chin), A lids (the upper lids)
    heroine_pore_zones.png   R her pores' coarse layer's reach (nose, inner cheeks, mid forehead, half on the chin),
                             G her lower lip's wet core
    heroine_sheen_zones.png  sheen:  R T-zone oil (forehead, nose, chin), G cheek (softer), B lips (wet),
                             A the face's coverage (1 on the face, 0 at the neck and behind the ears)

Real skin is not one colour or one gloss: blood shows through the thin skin over the cheeks, nose, ears and lip line,
the forehead runs yellower over bone, the thin skin under the eyes and the beard-line of the jaw read faintly cool,
the lids pinker; the T-zone is oilier (glossier), the cheeks drier, the lips wet (max judge b1, face 44, 26 October
2026). Each zone is a soft blob about a landmark on her head (metres, her base mesh: every face preset shares its UVs),
eased by a 3D Gaussian, then smoothed over her surface (SMOOTH) so no edge or blotch shows; the lips are her features
map's own (heroine_features.png green). The skin shader (heroine_skin.gdshader `skin_zones`, `sheen_zones`, the
zone_* uniforms) does the rest: People.Skin, her head only.

    python tools/assets/heroine_skin_zones.py        (writes both into godot/art/people/head_tex/)
"""
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import heroine_lobe as hl  # noqa: E402

SIZE = 1024
SMOOTH = 0.004          # (metres: every zone eased over her surface this much)
VOX = 0.001
SEAM_Y = 1.6805       # (her mouth's seam's height at its centre, metres)

# (centre (|x|, y, z), radii (x, y, z), weight): x is mirrored, so a centre at |x| > 0 is a pair
FLUSH = [
    ((0.036, 1.722, 0.083), (0.019, 0.016, 0.03), 1.0),     # (the apples of her cheeks)
    ((0.000, 1.712, 0.110), (0.011, 0.010, 0.03), 0.57),    # (her nose's tip; r2 x0.6: at a turn it went orange-red)
    ((0.012, 1.710, 0.098), (0.008, 0.008, 0.02), 0.54),    # (its wings)
    ((0.000, 1.737, 0.100), (0.006, 0.014, 0.02), 0.21),    # (its bridge, less)
    ((0.076, 1.735, -0.018), (0.02, 0.036, 0.03), 1.0),     # (her ears)
    ((0.000, 1.686, 0.092), (0.024, 0.011, 0.03), 0.55),    # (her lip line)
    ((0.000, 1.658, 0.084), (0.013, 0.009, 0.03), 0.3),     # (her chin)
]
YELLOW = [
    ((0.000, 1.798, 0.093), (0.066, 0.034, 0.06), 0.85),    # (her forehead; r2 feathered wider and lower, no patch under her hairline)
    ((0.058, 1.782, 0.055), (0.018, 0.022, 0.03), 0.3),     # (her temples)
]
COOL = [
    ((0.030, 1.743, 0.083), (0.014, 0.0048, 0.02), 0.9),    # (under her eyes; r2: her jaw's cool read as a beard's shadow, gone)
]
LIDS = [
    ((0.033, 1.764, 0.088), (0.014, 0.0055, 0.02), 1.0),    # (her upper lids)
]
OIL = [
    ((0.000, 1.800, 0.095), (0.040, 0.022, 0.05), 1.0),     # (her forehead)
    ((0.000, 1.722, 0.106), (0.010, 0.026, 0.03), 1.0),     # (her nose, bridge to tip)
    ((0.000, 1.658, 0.084), (0.012, 0.009, 0.03), 0.6),     # (her chin)
]
# (r2, max judge: her pores' coarse layer only where pores show: her nose, inner cheeks, mid forehead; half on her chin;
# none on her lips, jaw, under it or her neck)
PORES = [
    ((0.000, 1.722, 0.106), (0.010, 0.024, 0.03), 1.0),     # (her nose)
    ((0.012, 1.711, 0.098), (0.009, 0.008, 0.02), 1.0),     # (its wings)
    ((0.028, 1.722, 0.090), (0.012, 0.013, 0.03), 1.0),     # (her inner cheeks)
    ((0.050, 1.720, 0.072), (0.030, 0.024, 0.04), 1.0),     # (her cheeks: kept off her jaw by JAW_Y below)
    ((0.000, 1.799, 0.095), (0.038, 0.017, 0.05), 1.0),     # (her mid forehead, short of her hairline)
]
CHIN = [
    ((0.000, 1.658, 0.084), (0.011, 0.008, 0.03), 0.5),     # (her chin)
]
JAW_Y = (1.680, 1.698)  # (her pores' reach eased out below her cheeks, over these heights: none on her jaw's band)
CHEEK = [
    ((0.042, 1.718, 0.075), (0.024, 0.024, 0.04), 1.0),     # (her cheeks, out to her jaw)
]


def field(pos, blobs):
    ax = np.c_[np.abs(pos[:, 0]), pos[:, 1], pos[:, 2]]
    out = np.zeros(len(pos))
    for c, rad, w in blobs:
        d = (ax - np.array(c)) / np.array(rad)
        out = np.maximum(out, w * np.exp(-0.5 * (d * d).sum(1)))
    return out


def main():
    P, N, UV, T = hl.head()
    hl.BOX = (-1.0, 0.0, 3.0, -1.0, 1.0)          # (every texel of her head)
    r, c, pos, nrm = hl.texels(P, N, UV, T, 1, SIZE)
    fe = np.asarray(Image.open(os.path.join(hl.TEX, "heroine_features.png")).convert("RGBA").resize((SIZE, SIZE), Image.BILINEAR), np.float64) / 255
    lips = fe[r, c, 1]
    # (the face: in front of her ears, above her jaw's underside; eased out over 1.5 cm)
    cover = hl.smooth(-0.035, -0.010, pos[:, 2]) * hl.smooth(1.630, 1.648, pos[:, 1])
    # (her lower lip's core: below her mouth's seam (SEAM_Y: at her lips' centre the lower lip's texels sit at 1.671-1.678,
    # the upper's at 1.684-1.690), eased off to her mouth's corners)
    lower = lips * hl.smooth(SEAM_Y + 0.0005, SEAM_Y - 0.0025, pos[:, 1]) * np.exp(-0.5 * (pos[:, 0] / 0.011) ** 2)
    vals = np.c_[field(pos, FLUSH), field(pos, YELLOW), field(pos, COOL), field(pos, LIDS),
                 field(pos, OIL), field(pos, CHEEK) * (1 - lips) * (1 - field(pos, OIL)), lips, cover,
                 np.maximum(field(pos, PORES) * hl.smooth(*JAW_Y, pos[:, 1]), field(pos, CHIN)) * (1 - lips), lower, np.zeros(len(pos)), np.ones(len(pos))]
    vals = hl.smoothed(pos, vals, SMOOTH, vox=VOX)
    # (the lips sharper than the rest: smoothed less)
    vals[:, 6] = hl.smoothed(pos, lips[:, None], 0.0012, vox=0.0008)[:, 0]
    vals[:, 9] = hl.smoothed(pos, lower[:, None], 0.0012, vox=0.0008)[:, 0]
    vals = np.clip(vals, 0, 1)
    img = np.zeros((SIZE, SIZE, 12))
    has = np.zeros((SIZE, SIZE), bool)
    img[r, c] = vals
    has[r, c] = True
    # (the islands' padding: each texel off her mesh takes its nearest texel's)
    _, (iy, ix) = ndimage.distance_transform_edt(~has, return_indices=True)
    img = img[iy, ix]
    for name, sl in (("heroine_skin_zones.png", slice(0, 4)), ("heroine_sheen_zones.png", slice(4, 8)), ("heroine_pore_zones.png", slice(8, 12))):
        out = os.path.join(hl.TEX, name)
        Image.fromarray((img[..., sl] * 255 + 0.5).astype(np.uint8), "RGBA").save(out)
        print("ZONES", out, "means", np.round(vals[:, sl].mean(0), 3), "max", np.round(vals[:, sl].max(0), 3))


if __name__ == "__main__":
    main()
