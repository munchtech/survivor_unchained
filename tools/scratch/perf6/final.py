"""The report's sheets (all from the worktree's .shots), into OUTDIR:
  run_1440_x2.png   her running at 1440, 164 Hz, two consecutive frames: today's TAA+MSAA, FSR 2 (sharpening
                    off) with the moving threshold, none (MSAA alone); 2x nearest
  look_1080_x2.png  the Look (scatter 0.1) at 1080: her hair and an eye, today's TAA, FSR 2 + moving threshold,
                    FSR 2 with Godot's hashed alpha (scatter 0.38: batch 2), none; 2x nearest
  see_house.png     the see-through behind the house: the old dither, the window after both fixes (1:1)
    python final.py OUTDIR"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(__file__))
import crops as C  # noqa: E402

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)


def sheet(name, rows, scale):
    tiles = [(l, [im.resize((im.width * scale, im.height * scale), Image.NEAREST) for im in ims]) for l, ims in rows]
    cw = max(sum(i.width for i in ims) + 4 * (len(ims) - 1) for _, ims in tiles)
    rh = [max(i.height for i in ims) for _, ims in tiles]
    canvas = Image.new("RGB", (190 + cw, sum(rh) + 4 * (len(rows) - 1)), (18, 18, 18))
    d = ImageDraw.Draw(canvas)
    y = 0
    for (label, ims), h in zip(tiles, rh):
        d.text((6, y + 6), label, fill=(235, 235, 235))
        x = 190
        for im in ims:
            canvas.paste(im, (x, y))
            x += im.width + 4
        y += h + 4
    canvas.save(os.path.join(OUT, name))
    print(os.path.join(OUT, name), canvas.size)


def at(f, cx, cy, w, h):
    """A box of a shot, given in 1080p units round (cx, cy); her place if cx is None."""
    a = C.load(f)
    k = a.shape[0] / 1080
    if cx is None:
        c = C.her_at(f, a)
        cx, cy = c[0] / k, c[1] / k - 25
    x0, y0 = round((cx - w / 2) * k), round((cy - h / 2) * k)
    return Image.fromarray(a[y0:y0 + round(h * k), x0:x0 + round(w * k)].astype(np.uint8))


sheet("run_1440_x2.png", [(lab, [at(f"{t}_{i:02d}.png", None, None, 110, 120) for i in (3, 4)])
                          for lab, t in (("TAA + MSAA 4x (today)", "b3_run_taa"), ("FSR 2, sharpening off,", "b3_run_fc"),
                                         ("none (MSAA alone)", "b3_run_msaa"))], 2)
look = [("TAA + MSAA 4x (today)", "b3_look_taa_sc_02.png"), ("FSR 2 + moving cut", "b3_look_fc_sc_02.png"),
        ("FSR 2, Godot's hash*", "b2_look_s20_02.png"), ("none (MSAA alone)", "b3_look_msaa_sc_02.png")]
sheet("look_1080_x2.png", [(lab, [at(f, 890, 205, 180, 110), at(f, 1060, 435, 150, 100)]) for lab, f in look], 2)
sheet("see_house.png", [(lab, [at(f, None, None, 840, 500)]) for lab, f in
                        (("old dither", "house_old.png"), ("window, fixed", "b3_house_fc.png"))], 1)
