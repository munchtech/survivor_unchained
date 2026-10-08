"""Cycle 1's sheets (from the worktree's .shots) into OUTDIR, each labelled, boxes in 1080p units:
  look_pony_x2.png   the Look, ponytail, 1080: her crown and an eye, frames 2 and 3, 2x nearest:
                     today's TAA, FSR 2 hashed, FSR 2 blended (prepass), FSR 2 blended (core + over)
  look_long_x2.png   the same for the loose (long) cut: today's TAA, FSR 2 blend, FSR 2 two
  look_turn_x1.png   the Look turned 40 degrees each way, head and shoulders 1:1 (where card order shows)
  look_1440_x1.png   the Look at 1440, her head 1:1: today's TAA, FSR 2 blend
  run_1440_x2.png    her running at 1440, frames 3 and 4, 2x: today's TAA, FSR 2 hashed, blend, two
  run_1080_x2.png    her running at 1080, frames 3 and 4, 2x: today's TAA, FSR 2 blend
  house_x1.png       the see-through behind the Waystation house, 1:1: FSR 2 blend, and --see-debug
    python sheets_c1.py OUTDIR"""
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
    if not os.path.exists(os.path.join(C.SHOTS, f)):
        return Image.new("RGB", (w, h), (90, 0, 90))
    a = C.load(f)
    k = a.shape[0] / 1080
    if cx is None:
        c = C.her_at(f, a)
        cx, cy = c[0] / k, c[1] / k - 25
    x0, y0 = max(0, round((cx - w / 2) * k)), max(0, round((cy - h / 2) * k))
    return Image.fromarray(a[y0:y0 + round(h * k), x0:x0 + round(w * k)].astype(np.uint8))


def look(tag, i):
    f = f"{tag}_{i:02d}.png"
    return [at(f, 890, 205, 180, 110), at(f, 1060, 435, 150, 100)]


sheet("look_pony_x2.png", [(lab, look(t, 2) + look(t, 3)) for lab, t in (
    ("TAA + MSAA 4x (today)", "c1_lp_taa"), ("FSR 2, hashed", "c1_lp_fsr"),
    ("FSR 2, blended (prepass)", "c1_lp_fb"), ("FSR 2, blended (core+over)", "c1_lp_ft"))], 2)
sheet("look_long_x2.png", [(lab, look(t, 2) + look(t, 3)) for lab, t in (
    ("TAA + MSAA 4x (today)", "c1_ll_taa"), ("FSR 2, blended (prepass)", "c1_ll_fb"),
    ("FSR 2, blended (core+over)", "c1_ll_ft"))], 2)
sheet("look_turn_x1.png", [(lab, [at(f"{t}_02.png", 960, 380, 520, 560)]) for lab, t in (
    ("pony +40 TAA (today)", "c1_lpr_taa"), ("pony +40 FSR 2 blend", "c1_lpr_fb"), ("pony -40 FSR 2 blend", "c1_lpl_fb"),
    ("long +40 TAA (today)", "c1_llr_taa"), ("long +40 FSR 2 blend", "c1_llr_fb"), ("long -40 FSR 2 blend", "c1_lll_fb"))], 1)
sheet("look_1440_x1.png", [(lab, [at(f"{t}_02.png", 960, 330, 420, 420)]) for lab, t in (
    ("TAA + MSAA 4x (today)", "c1_lp14_taa"), ("FSR 2, blended (prepass)", "c1_lp14_fb"))], 1)
sheet("run_1440_x2.png", [(lab, [at(f"{t}_{i:02d}.png", None, None, 110, 120) for i in (3, 4)]) for lab, t in (
    ("TAA + MSAA 4x (today)", "c1_run_taa"), ("FSR 2, hashed", "c1_run_fsr"),
    ("FSR 2, blended (prepass)", "c1_run_fb"), ("FSR 2, blended (core+over)", "c1_run_ft"))], 2)
sheet("run_1080_x2.png", [(lab, [at(f"{t}_{i:02d}.png", None, None, 110, 120) for i in (3, 4)]) for lab, t in (
    ("TAA + MSAA 4x (today)", "c1_r10_taa"), ("FSR 2, blended (prepass)", "c1_r10_fb"))], 2)
sheet("house_x1.png", [(lab, [at(f, None, None, 840, 500)]) for lab, f in (
    ("FSR 2 blend", "c1_house_fb.png"), ("--see-debug: tint per piece, rim by kept (blue 0, red 1)", "c1_house_dbg.png"))], 1)
