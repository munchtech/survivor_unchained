"""Before over after, cell by cell: <dir>/<tag>_b.png (without the helpers)
over <dir>/<tag>_a.png (with them), the chosen cells only, labelled.

    python pair.py <dir> <tag> <cell size> <cells, e.g. 2,3,4> <out.png> [labels,...]
"""
import sys
from PIL import Image, ImageDraw

d, tag, size, cells, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), [int(c) for c in sys.argv[4].split(",")], sys.argv[5]
labels = sys.argv[6].split(",") if len(sys.argv) > 6 else [str(c) for c in cells]
a = Image.open(f"{d}/{tag}_a.png").convert("RGB")
b = Image.open(f"{d}/{tag}_b.png").convert("RGB")
cols = a.width // size
pad = 18
img = Image.new("RGB", (size * len(cells), size * 2 + pad * 2), (20, 20, 22))
dr = ImageDraw.Draw(img)
for i, c in enumerate(cells):
    x, y = (c % cols) * size, (c // cols) * size
    img.paste(b.crop((x, y, x + size, y + size)), (i * size, pad))
    img.paste(a.crop((x, y, x + size, y + size)), (i * size, size + pad * 2))
    dr.text((i * size + 6, 3), f"{labels[i]}  before", fill=(230, 200, 120))
    dr.text((i * size + 6, size + pad + 3), f"{labels[i]}  helpers", fill=(140, 220, 160))
img.save(out)
print(out, img.size)
