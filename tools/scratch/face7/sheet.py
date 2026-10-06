"""sheet.py <out.jpg> <cell width> <cols> <img[@x0,y0,x1,y1]> ...: a labelled contact sheet (crop box in fractions)."""
import os
import sys

from PIL import Image, ImageDraw

out, cw, cols = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
items = sys.argv[4:]
cells = []
for it in items:
    path, _, box = it.partition("@")
    im = Image.open(path).convert("RGB")
    if box:
        x0, y0, x1, y1 = (float(v) for v in box.split(","))
        W, H = im.size
        im = im.crop((int(x0 * W), int(y0 * H), int(x1 * W), int(y1 * H)))
    h = int(im.height * cw / im.width)
    cells.append((os.path.splitext(os.path.basename(path))[0], im.resize((cw, h))))
ch = max(c[1].height for c in cells) + 18
rows = (len(cells) + cols - 1) // cols
S = Image.new("RGB", (cw * cols, ch * rows), (20, 20, 20))
d = ImageDraw.Draw(S)
for i, (name, im) in enumerate(cells):
    x, y = (i % cols) * cw, (i // cols) * ch
    S.paste(im, (x, y + 18))
    d.text((x + 4, y + 3), name, fill=(230, 230, 230))
S.save(out, quality=88)
print("SHEET", out, S.size)
