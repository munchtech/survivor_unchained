import sys
from PIL import Image
src, out, x0, y0, x1, y1, sc = sys.argv[1], sys.argv[2], *map(int, sys.argv[3:7]), float(sys.argv[7])
im = Image.open(src).convert("RGB").crop((x0, y0, x1, y1))
im.resize((int((x1 - x0) * sc), int((y1 - y0) * sc)), Image.LANCZOS).save(out)
