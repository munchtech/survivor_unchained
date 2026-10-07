"""Where a still camera's picture flickers: the pixels that change by more than 12/255 between
consecutive frames, counted over the run, painted red over its first frame; and the busiest window.
    python flicker.py OUTDIR TAG [TAG ...]"""
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
import crops as C  # noqa: E402

out = sys.argv[1]
for t in sys.argv[2:]:
    fs = C.frames(t)
    st = np.stack([C.load(f).mean(axis=2) for f in fs])
    hot = (np.abs(np.diff(st, axis=0)) > 12).sum(axis=0)
    H, W = hot.shape
    # (The interface's bands left out, as the shimmer number does.)
    hot[: int(H * 0.12)] = 0
    hot[int(H * 0.8):] = 0
    first = C.load(fs[0]).astype(np.uint8)
    paint = first.copy()
    paint[hot > 0] = [255, 0, 0]
    # The busiest 400x300 window.
    k = 50
    cs = np.add.reduceat(np.add.reduceat(hot, np.arange(0, H, k), axis=0), np.arange(0, W, k), axis=1)
    by, bx = np.unravel_index(np.argmax(cs), cs.shape)
    y0, x0 = max(0, by * k - 125), max(0, bx * k - 175)
    win = np.concatenate([first[y0:y0 + 300, x0:x0 + 400], paint[y0:y0 + 300, x0:x0 + 400]], axis=1)
    Image.fromarray(win).resize((win.shape[1] * 2, win.shape[0] * 2), Image.NEAREST).save(os.path.join(out, f"flicker_{t}.png"))
    print(f"{t}: {int((hot > 0).sum())} pixels ever over 12/255; busiest window at ({x0},{y0})")
