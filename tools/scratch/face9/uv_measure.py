"""uv_measure.py MASK img ...: in her head's UV, each blob of a feature mask (features_uv.png: brows, eyes, lips) and
how dark each picture is there against the skin round it: the median of the blob's darkest third over the ring's
median (linear lightness). Blobs listed by size, with their centre."""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage

LW = np.array([0.2126, 0.7152, 0.0722])


def lin(a):
    a = a / 255.0
    return np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)


m = np.asarray(Image.open(sys.argv[1]).convert('L')).astype(np.float32) / 255
lab, n = ndimage.label(m > 0.5)
sizes = ndimage.sum(np.ones_like(m), lab, range(1, n + 1))
order = np.argsort(-sizes)[:6]
imgs = []
for p in sys.argv[2:]:
    a = np.asarray(Image.open(p).convert('RGB').resize(m.shape[::-1], Image.LANCZOS)).astype(np.float32)
    imgs.append((p.replace('\\', '/').split('/')[-2] + '/' + p.replace('\\', '/').split('/')[-1], lin(a) @ LW))
for k in order:
    blob = lab == k + 1
    ys, xs = np.nonzero(blob)
    ring = ndimage.binary_dilation(blob, iterations=12) & ~ndimage.binary_dilation(blob, iterations=4) & (m < 0.2)
    line = 'blob at (%4d,%4d) %6d px:' % (xs.mean(), ys.mean(), blob.sum())
    for name, L in imgs:
        v = L[blob]
        sk = np.median(L[ring])
        dark = np.median(v[v <= np.percentile(v, 33)]) / sk
        mass = np.clip(1 - v / sk, 0, 1).mean()
        line += '  %s dark %.2f mass %.2f' % (name[-28:], dark, mass)
    print(line)
