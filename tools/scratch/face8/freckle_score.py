"""freckle_score.py img ... : freckles on each face's cheeks and nose (its skin between the bottom of its eyes and its
upper lip), every face first scaled to one size (brow-top to chin 380 px, as fair_grain.py): how many small dark spots
(1 to 3 mm: darker than the skin round them by 5% or more) to a thousand square pixels, and how dark on average.
Run with the facefit venv's python."""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage
import skin_sample as ss

FACE_PX = 380


def score(path):
    img = Image.open(path).convert("RGB")
    a = np.asarray(img)
    up = 2 if a.shape[0] < 900 else 1
    big = np.asarray(img.resize((img.width * up, img.height * up), Image.LANCZOS))
    L = ss.ff.detect(big)
    if L is None:
        return None
    L = L[:, :2] / up
    k = FACE_PX / np.linalg.norm(L[152] - L[10])
    im = img.resize((max(1, round(img.width * k)), max(1, round(img.height * k))), Image.LANCZOS)
    a = np.asarray(im).astype(float) / 255.0
    L = L * k
    lum = ss.lin(a) @ np.array([0.2126, 0.7152, 0.0722])
    oval = ndimage.binary_erosion(ss.poly(a.shape, L[ss.ff.OVAL]), iterations=4)
    feat = np.zeros_like(oval)
    for ring in (ss.EYE_R, ss.EYE_L, ss.BROW_A, ss.BROW_B, ss.LIPS, ss.NOSE):
        feat |= ss.poly(a.shape, L[ring], grow=5)
    y0 = max(L[145][1], L[374][1]) + 6          # (under the lower lids)
    y1 = L[0][1] - 4                             # (over the upper lip)
    ys = np.arange(a.shape[0])[:, None] * np.ones((1, a.shape[1]))
    zone = oval & ~feat & (ys > y0) & (ys < y1)
    base = ndimage.gaussian_filter(lum, 4.0)
    rel = (lum - base) / np.maximum(base, 1e-4)
    spots = ndimage.gaussian_filter(rel, 1.0)
    minima = (spots == ndimage.minimum_filter(spots, size=5)) & (spots < -0.05) & zone
    n = minima.sum()
    return 1000.0 * n / max(zone.sum(), 1), (-spots[minima]).mean() if n else 0.0, zone.sum()


if __name__ == "__main__":
    print("%-26s %10s %8s %8s" % ("", "per 1000px", "depth", "zone px"))
    for p in sys.argv[1:]:
        r = score(p)
        name = p.replace("\\", "/").split("/")[-1][:26]
        print("%-26s %s" % (name, "no face" if r is None else "%10.2f %8.3f %8d" % r))
