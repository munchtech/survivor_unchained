"""Boxes of shots side by side, labelled, for a quick look.
    python box.py OUT.png SCALE CX CY W H FILE [FILE ...]     (box in 1080p units round CX,CY; CX=her: her place)"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(__file__))
import crops as C  # noqa: E402

out, scale = sys.argv[1], int(sys.argv[2])
cx, cy, w, h = sys.argv[3], sys.argv[4], float(sys.argv[5]), float(sys.argv[6])
ims = []
for f in sys.argv[7:]:
    a = C.load(f)
    k = a.shape[0] / 1080
    if cx == "her":
        c = C.her_at(f, a)
        x, y = c[0] / k, c[1] / k - 25
    else:
        x, y = float(cx), float(cy)
    x0, y0 = max(0, round((x - w / 2) * k)), max(0, round((y - h / 2) * k))
    im = Image.fromarray(a[y0:y0 + round(h * k), x0:x0 + round(w * k)].astype(np.uint8))
    ims.append((f, im.resize((im.width * scale, im.height * scale), Image.NEAREST)))
W = sum(i.width for _, i in ims) + 4 * (len(ims) - 1)
H = max(i.height for _, i in ims) + 16
canvas = Image.new("RGB", (W, H), (18, 18, 18))
d = ImageDraw.Draw(canvas)
x = 0
for f, im in ims:
    canvas.paste(im, (x, 16))
    d.text((x + 4, 2), f, fill=(235, 235, 235))
    x += im.width + 4
canvas.save(out)
print(out, canvas.size)
