"""1:1 crops of game frames round her arms: python crops.py OUT.png DIR [DIR2 ...] (rows: dirs; cols: frame:side)"""
import sys, os
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import k
import harness as h

COLS = [("w_p45", "r"), ("w_m45", "r"), ("w_m80", "l"), ("s_p45", "r"), ("rL90_m45", "l"), ("look_f", "r"), ("look_f", "l")]
BOX = (-120, -110, 120, 230)     # px about the shoulder joint (x0, y0, x1, y1)


def box_of(fr, sd, bx=BOX):
    q = h.project(fr.Pm, k.joint(fr, "upperarm_" + sd)[None])[0]
    if fr.name == "look_f":
        bx = (-90, -70, 90, 190)
    return (int(q[0] + bx[0]), int(q[1] + bx[1]), int(q[0] + bx[2]), int(q[1] + bx[3]))


if __name__ == "__main__":
    out, dirs = sys.argv[1], sys.argv[2:]
    cols = COLS
    if os.environ.get("COLS"):
        cols = [tuple(c.split(":")) for c in os.environ["COLS"].split(",")]
    rows = []
    for d in dirs:
        ims = []
        for f, sd in cols:
            fr = k.frame(f)
            b = box_of(fr, sd)
            p = os.path.join(d, f + ".png")
            im = Image.open(p).convert("RGB").crop(b) if os.path.exists(p) else Image.new("RGB", (b[2] - b[0], b[3] - b[1]))
            ims.append(im)
        rows.append(ims)
    W = sum(im.width for im in rows[0]) + 4 * (len(rows[0]) - 1)
    H = sum(r[0].height for r in rows) + 4 * (len(rows) - 1)
    H = sum(max(im.height for im in r) for r in rows) + 4 * (len(rows) - 1)
    S = Image.new("RGB", (W, H), (255, 0, 255))
    y = 0
    for r in rows:
        x = 0
        for im in r:
            S.paste(im, (x, y)); x += im.width + 4
        y += max(im.height for im in r) + 4
    if os.environ.get("HALF"):
        S = S.resize((S.width // 2, S.height // 2), Image.LANCZOS)
    S.save(out)
    print(out, S.size)
