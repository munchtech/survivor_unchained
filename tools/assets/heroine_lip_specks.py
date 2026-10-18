"""Small dark specks in a face's lip red, healed (face lead 23, 14 October 2026).

Judge j2 found flecks on own's lower lip at the Look: two dark brown specks in her paint's lower-lip red (not her
freckles' layer: heroine_freckles.png has none there). A speck is a blob of at most 80 texels darker than its 15-texel
median by more than D (0.1), where the median is a lip's (lightness over 0.42: the mouth's dark slit is left alone), inside
heroine_features.png's lip green (> 0.1). Each is replaced by its median, feathered over 2 texels. Lip lines are longer
than 80 texels and survive. Run after heroine_lip_raise.py, on the faces a judge names (own only so far: 58 specks,
353 texels).

    python tools/assets/heroine_lip_specks.py PAINT_IN PAINT_OUT [D]
"""
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
FEATURES = os.path.join(HERE, "..", "..", "godot", "art", "people", "head_tex", "heroine_features.png")
LUM = np.array([0.3, 0.59, 0.11])


def heal(a, d=0.1):
    H = a.shape[0]
    g = np.asarray(Image.open(FEATURES).convert("RGB").resize((H, H), Image.BILINEAR)).astype(float)[..., 1] / 255
    lip = g > 0.1
    ys, xs = np.nonzero(lip)
    y0, y1, x0, x1 = ys.min() - 20, ys.max() + 20, xs.min() - 20, xs.max() + 20
    s = a[y0:y1, x0:x1]
    med = np.dstack([ndimage.median_filter(s[..., c], 15) for c in range(3)])
    spot = (s @ LUM < med @ LUM - d) & (med @ LUM > 0.42) & lip[y0:y1, x0:x1]
    lab, n = ndimage.label(spot)
    sizes = ndimage.sum(spot, lab, range(1, n + 1)) if n else []
    keep = [i + 1 for i, z in enumerate(sizes) if z <= 80]
    small = np.isin(lab, keep)
    mw = ndimage.gaussian_filter(ndimage.binary_dilation(small, iterations=2).astype(float), 1.0)[..., None]
    b = a.copy()
    b[y0:y1, x0:x1] = s * (1 - mw) + med * mw
    return b, len(keep), int(small.sum())


if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    a = np.asarray(Image.open(src).convert("RGB")).astype(float) / 255
    b, n, px = heal(a, float(sys.argv[3]) if len(sys.argv) > 3 else 0.1)
    Image.fromarray((np.clip(b, 0, 1) * 255 + 0.5).astype(np.uint8)).save(dst, quality=95)
    print("LIP SPECKS %s: %d healed, %d texels" % (os.path.basename(src), n, px))
