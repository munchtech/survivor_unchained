import sys, os
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import meas, face_fit as ff
out = sys.argv[1]; tiles = []
for n in sys.argv[2:]:
    p = os.path.join(meas.S, n + '.png') if os.path.exists(os.path.join(meas.S, n + '.png')) else os.path.join(meas.R, n + '.png')
    im = Image.open(p).convert('RGB'); up = 2 if im.height < 900 else 1
    L = ff.detect(np.asarray(im.resize((im.width * up, im.height * up))))[:, :2] / up
    h = np.linalg.norm(L[152] - L[10]); j = L[136] + [0, 0.07 * h]; c = L[152]
    box = (int(L[136][0] - 0.25 * h), int(L[1][1]), int(c[0] + 0.15 * h), int(c[1] + 0.3 * h))
    t = im.crop(box); d = ImageDraw.Draw(t); r = 0.025 * h
    d.rectangle((j[0] - box[0] - r, j[1] - box[1] - r, j[0] - box[0] + r, j[1] - box[1] + r), outline=(0, 255, 0))
    t = t.resize((300, int(300 * t.height / t.width))); ImageDraw.Draw(t).text((3, 3), n, fill=(255, 255, 0)); tiles.append(t)
H = max(t.height for t in tiles); sh = Image.new('RGB', (len(tiles) * 304, H))
for i, t in enumerate(tiles): sh.paste(t, (i * 304, 0))
sh.save(out, quality=90)
