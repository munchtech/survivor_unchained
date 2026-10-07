"""Where the Look flickers over its consecutive frames: pixels changing by more than 8/255 between
any two frames, painted red over the first, her head at 2x.
    python look_where.py OUTDIR TAG [TAG ...]"""
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
import crops as C  # noqa: E402

out = sys.argv[1]
tiles = []
for t in sys.argv[2:]:
    fs = C.frames(t)
    st = np.stack([C.load(f) for f in fs])
    g = st.mean(axis=3)
    hot = (np.abs(np.diff(g, axis=0)) > 8).any(axis=0)
    k = g.shape[1] / 1080
    y0, y1, x0, x1 = round(140 * k), round(520 * k), round(780 * k), round(1140 * k)
    first = st[0].astype(np.uint8)
    paint = first.copy()
    paint[hot] = [255, 0, 0]
    tile = np.concatenate([first[y0:y1, x0:x1], paint[y0:y1, x0:x1]], axis=1)
    tiles.append(Image.fromarray(tile).resize((tile.shape[1] * 2 // round(k), tile.shape[0] * 2 // round(k)), Image.NEAREST))
    print(t, f"{hot[y0:y1, x0:x1].mean() * 100:.2f}% of the head's pixels flicker over 8/255")
W = max(t.width for t in tiles)
canvas = Image.new("RGB", (W, sum(t.height for t in tiles) + 6 * (len(tiles) - 1)), (18, 18, 18))
y = 0
for t in tiles:
    canvas.paste(t, (0, y))
    y += t.height + 6
canvas.save(os.path.join(out, "look_where.png"))
print(canvas.size)
