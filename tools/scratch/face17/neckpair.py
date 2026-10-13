"""neckpair.py OUT NAME...: each shot or portrait from its eyes to 1.2 pupil-chin below its chin, scaled to the same
pupil-chin (160 px), side by side, labelled; tick marks every 0.1 pupil-chin below the chin (neckprof's steps)."""
import sys, os
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import meas
out = sys.argv[1]; tiles = []
for n in sys.argv[2:]:
    p = next(q for q in (os.path.join(meas.S, n + '.png'), os.path.join(meas.R, n + '.png')) if os.path.exists(q))
    im = Image.open(p).convert('RGB'); up = 2 if im.height < 900 else 1
    L = meas.ff.detect(np.asarray(im.resize((im.width * up, im.height * up))))[:, :2] / up
    pup = (L[468] + L[473]) / 2; chin = L[152]; u = chin[1] - pup[1]
    box = (int(chin[0] - 0.9 * u), int(pup[1] - 0.3 * u), int(chin[0] + 0.9 * u), int(chin[1] + 1.2 * u))
    t = im.crop(box); s = 160 / u; t = t.resize((int(t.width * s), int(t.height * s)), Image.LANCZOS)
    d = ImageDraw.Draw(t); cy = (chin[1] - box[1]) * s
    for i in range(1, 11):
        y = cy + i * 16; d.line((0, y, 8, y), fill=(0, 255, 0))
    d.text((3, 3), n, fill=(255, 255, 0)); tiles.append(t)
W = sum(t.width for t in tiles); H = max(t.height for t in tiles)
sheet = Image.new('RGB', (W, H)); x = 0
for t in tiles: sheet.paste(t, (x, 0)); x += t.width
sheet.save(out, quality=90)
