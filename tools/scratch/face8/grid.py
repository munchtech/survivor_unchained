"""grid.py out.jpg cell_px row1_prefix,row2_prefix,... suffix1,suffix2,...: a sheet of rows of renders, labelled."""
import sys, os
from PIL import Image, ImageDraw
out, px, rows, cols = sys.argv[1], int(sys.argv[2]), sys.argv[3].split(","), sys.argv[4].split(",")
D = os.path.dirname(os.path.abspath(__file__))
W = Image.new("RGB", (px * len(cols), px * len(rows)), (30, 30, 30))
d = ImageDraw.Draw(W)
for r, rp in enumerate(rows):
    for c, cs in enumerate(cols):
        p = os.path.join(D, "%s%s" % (rp, cs))
        if not os.path.exists(p):
            continue
        im = Image.open(p).convert("RGB")
        im.thumbnail((px, px))
        W.paste(im, (c * px, r * px))
        d.text((c * px + 6, r * px + 6), "%s%s" % (rp, cs), fill=(255, 255, 0))
W.save(os.path.join(D, out), quality=92)
print(W.size)
