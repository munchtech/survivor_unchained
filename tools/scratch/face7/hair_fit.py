"""hair_fit.py ref.png x0,y0,x1,y1 render.png x0,y0,x1,y1 colour_hex [K]: her hair's colour in her portrait and in the
game under the white rig (pixels in each box that are hair: redder than they are green by a third, not the
background), median and mean in linear light; the factor the hair's colour needs per channel, and the new colour."""
import sys
import numpy as np
from PIL import Image


def lin(c):
    c = np.asarray(c, float)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def srgb(c):
    c = np.clip(np.asarray(c, float), 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def hair(path, box):
    a = np.asarray(Image.open(path).convert("RGB").crop(box)).reshape(-1, 3) / 255.0
    m = (a[:, 0] > a[:, 1] * 1.3) & (a[:, 0] > 0.08)
    l = lin(a[m])
    return l, m.mean()


ref, rb, ren, nb, hexc = sys.argv[1], [int(v) for v in sys.argv[2].split(",")], sys.argv[3], [int(v) for v in sys.argv[4].split(",")], sys.argv[5]
K = float(sys.argv[6]) if len(sys.argv) > 6 else 1.0
a, fa = hair(ref, rb)
b, fb = hair(ren, nb)
ma, mb = np.median(a, 0), np.median(b, 0)
print("portrait hair: %d px (%.0f%% of box), median lin %s srgb %s" % (len(a), 100 * fa, np.round(ma, 4), np.round(srgb(ma) * 255)))
print("game hair:     %d px (%.0f%% of box), median lin %s srgb %s" % (len(b), 100 * fb, np.round(mb, 4), np.round(srgb(mb) * 255)))
f = ma * K / mb
c = lin(np.array([int(hexc[i:i + 2], 16) for i in (1, 3, 5)]) / 255.0)
new = srgb(c * f)
print("factor %s  colour %s -> #%02x%02x%02x" % (np.round(f, 3), hexc, *(np.round(new * 255).astype(int))))
print("brightness spread (p90/p10 of luminance): portrait %.2f game %.2f" % tuple(
    np.percentile(x @ [0.2126, 0.7152, 0.0722], 90) / max(1e-4, np.percentile(x @ [0.2126, 0.7152, 0.0722], 10)) for x in (a, b)))
