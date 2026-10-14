"""edgecrop.py OUT NAME...: her jaw's lower edge from the jaw corner to the chin, 2x, side by side."""
import sys, os
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import meas
ims = []
for n in sys.argv[2:]:
    im = Image.open(os.path.join(meas.S, n + '.png')).convert('RGB'); L = meas.ff.detect(np.asarray(im))[:, :2]
    c = L[152]; j = L[136]; box = (int(j[0] - 20), int(j[1] - 30), int(c[0] + 30), int(c[1] + 50))
    ims.append(im.crop(box).resize(((box[2] - box[0]) * 2, (box[3] - box[1]) * 2), Image.LANCZOS))
W = sum(i.width for i in ims); H = max(i.height for i in ims); s = Image.new('RGB', (W, H)); x = 0
for i in ims: s.paste(i, (x, 0)); x += i.width
s.thumbnail((1900, 700)); s.save(sys.argv[1], quality=90)
