"""python crops.py out.jpg x0 y0 x1 y1 scale img... : the same box from each image, side by side (relative to this folder)."""
import os
import sys
from PIL import Image

D = os.path.dirname(os.path.abspath(__file__))
out = sys.argv[1]
x0, y0, x1, y1 = (int(v) for v in sys.argv[2:6])
s = float(sys.argv[6])
fs = sys.argv[7:]
ims = [Image.open(os.path.join(D, f)).convert('RGB').crop((x0, y0, x1, y1)) for f in fs]
ims = [a.resize((int(a.width * s), int(a.height * s)), Image.LANCZOS) for a in ims]
im = Image.new('RGB', (sum(a.width for a in ims) + 4 * (len(ims) - 1), ims[0].height), (255, 0, 255))
x = 0
for a in ims:
    im.paste(a, (x, 0))
    x += a.width + 4
im.save(os.path.join(D, out), quality=90)
