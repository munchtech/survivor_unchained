"""The see-through after its fix, beside the old dither: the house standing (1:1, round her), and
the pines running (every sixth frame of thirty).
    python cut_see.py OUTDIR"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(__file__))
import crops as C  # noqa: E402

OUT = sys.argv[1]


def her_crop(f, hw, hh, up=0.0):
    a = C.load(f)
    H = a.shape[0]
    c = C.her_at(f, a)
    return Image.fromarray(C.crop(a, (c[0], c[1] - int(H * up)), hw, hh).astype(np.uint8))


def sheet(name, rows):
    rows = [(l, ims) for l, ims in rows if ims]
    cw = max(sum(im.width for im in ims) + 4 * (len(ims) - 1) for _, ims in rows)
    rh = [max(im.height for im in ims) for _, ims in rows]
    canvas = Image.new("RGB", (150 + cw, sum(rh) + 4 * (len(rows) - 1)), (18, 18, 18))
    d = ImageDraw.Draw(canvas)
    y = 0
    for (label, ims), h in zip(rows, rh):
        d.text((6, y + 6), label, fill=(235, 235, 235))
        x = 150
        for im in ims:
            canvas.paste(im, (x, y))
            x += im.width + 4
        y += h + 4
    canvas.save(os.path.join(OUT, name))
    print(os.path.join(OUT, name), canvas.size)


sheet("see_house.png", [(t, [her_crop(t + ".png", 560, 330)]) for t in ("house_old", "b2_house_fsr2", "b2_house_taa")])
rows = []
for t in ("trees_old", "b2_trees_fsr2", "b2_trees_taa"):
    fs = C.frames(t)
    rows.append((t, [her_crop(fs[i], 200, 190) for i in (4, 10, 16, 22, 28)]))
sheet("see_trees.png", rows)
