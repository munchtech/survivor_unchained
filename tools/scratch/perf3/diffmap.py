"""Where two shots differ: python diffmap.py A B OUT [A2 B2] -- a half-size map,
white where the pixel sum differs by more than 24, over a dimmed A. With a
second pair, the two maps side by side (e.g. A/A noise beside A/B)."""
import sys

import numpy as np
from PIL import Image


def m(a, b):
    x = np.asarray(Image.open(a).convert("RGB")).astype(int)
    y = np.asarray(Image.open(b).convert("RGB")).astype(int)
    d = np.abs(x - y).sum(2) > 24
    base = (x * 0.35).astype(np.uint8)
    base[d] = [255, 255, 255]
    im = Image.fromarray(base)
    return im.resize((im.width // 2, im.height // 2), Image.BOX)


a = m(sys.argv[1], sys.argv[2])
if len(sys.argv) > 5:
    b = m(sys.argv[4], sys.argv[5])
    out = Image.new("RGB", (a.width + b.width + 10, a.height), "red")
    out.paste(a, (0, 0))
    out.paste(b, (a.width + 10, 0))
    a = out
a.save(sys.argv[3])
