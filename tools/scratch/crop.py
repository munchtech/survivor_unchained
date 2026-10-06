"""crop.py SRC OUT x0 y0 x1 y1 [scale]: a region of a screenshot, scaled (nearest, to judge pixels)."""
import sys

from PIL import Image

src, out = sys.argv[1], sys.argv[2]
x0, y0, x1, y1 = (int(v) for v in sys.argv[3:7])
k = float(sys.argv[7]) if len(sys.argv) > 7 else 1.0
im = Image.open(src).crop((x0, y0, x1, y1))
if k != 1.0:
    im = im.resize((int(im.width * k), int(im.height * k)), Image.NEAREST if k >= 2 else Image.LANCZOS)
im.save(out)
print(out, im.size)
