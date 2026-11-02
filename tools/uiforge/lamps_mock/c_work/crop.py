import sys
from PIL import Image
# crop.py out.png src x0 y0 x1 y1 [scale]
src, x0, y0, x1, y1 = sys.argv[2], *map(int, sys.argv[3:7])
sc = float(sys.argv[7]) if len(sys.argv) > 7 else 1
im = Image.open(src).crop((x0, y0, x1, y1))
if sc != 1: im = im.resize((int(im.width * sc), int(im.height * sc)), Image.LANCZOS)
im.save(sys.argv[1])
