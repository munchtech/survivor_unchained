"""Rows of the same cells from several sheets, labelled, scaled by `scale`:
    python rows.py <out.png> <cell size> <cells, e.g. 2,3,4> <scale> <label=sheet.png> ...
"""
import sys
from PIL import Image, ImageDraw

out, size, cells, scale = sys.argv[1], int(sys.argv[2]), [int(c) for c in sys.argv[3].split(",")], float(sys.argv[4])
rows = [a.split("=", 1) for a in sys.argv[5:]]
cs = int(size * scale)
pad = 16
img = Image.new("RGB", (cs * len(cells), (cs + pad) * len(rows)), (20, 20, 22))
dr = ImageDraw.Draw(img)
for r, (label, path) in enumerate(rows):
    sh = Image.open(path).convert("RGB")
    cols = sh.width // size
    for i, c in enumerate(cells):
        x, y = (c % cols) * size, (c // cols) * size
        cell = sh.crop((x, y, x + size, y + size))
        if scale != 1:
            cell = cell.resize((cs, cs), Image.LANCZOS)
        img.paste(cell, (i * cs, r * (cs + pad) + pad))
        dr.text((i * cs + 4, r * (cs + pad) + 2), f"{label}  [{c}]", fill=(230, 210, 140))
img.save(out)
print(out, img.size)
