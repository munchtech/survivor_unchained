"""Where a run flickers in motion: per-pixel |a - 2b + c| after tile alignment, over all triples,
painted over the middle frame; and the busiest window at 2x beside its painted copy.
    python flick_where.py OUTDIR TAG [TAG ...]"""
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
import crops as C  # noqa: E402
from mres import T, shift_of, fshift  # noqa: E402

out = sys.argv[1]
for tag in sys.argv[2:]:
    fs = C.frames(tag)
    ims = [C.load(f).mean(axis=2) for f in fs]
    H, W = ims[0].shape
    acc = np.zeros((H, W))
    for i in range(len(ims) - 2):
        a, b, c = ims[i], ims[i + 1], ims[i + 2]
        for y in range(0, H - T + 1, T):
            for x in range(0, W - T + 1, T):
                ta, tb, tc = a[y:y + T, x:x + T], b[y:y + T, x:x + T], c[y:y + T, x:x + T]
                if ta.std() < 1:
                    continue
                d1, d2 = shift_of(ta, tb), shift_of(ta, tc)
                dd = np.abs(ta - 2 * fshift(tb, -d1[0], -d1[1]) + fshift(tc, -d2[0], -d2[1]))
                dd[:16], dd[-16:], dd[:, :16], dd[:, -16:] = 0, 0, 0, 0
                acc[y:y + T, x:x + T] = np.maximum(acc[y:y + T, x:x + T], dd)
    mid = C.load(fs[len(fs) // 2]).astype(np.uint8)
    paint = mid.copy()
    paint[acc > 16] = [255, 0, 0]
    # The busiest 360x240 window, away from the interface's bands.
    k = 40
    band = acc.copy()
    band[: int(H * 0.15)], band[int(H * 0.78):] = 0, 0
    cs = np.add.reduceat(np.add.reduceat((band > 16).astype(float), np.arange(0, H, k), axis=0), np.arange(0, W, k), axis=1)
    by, bx = np.unravel_index(np.argmax(cs), cs.shape)
    y0, x0 = max(0, by * k - 100), max(0, bx * k - 160)
    win = np.concatenate([mid[y0:y0 + 240, x0:x0 + 360], paint[y0:y0 + 240, x0:x0 + 360]], axis=1)
    Image.fromarray(win).resize((win.shape[1] * 2, win.shape[0] * 2), Image.NEAREST).save(os.path.join(out, f"fwhere_{tag}.png"))
    Image.fromarray(paint).resize((W // 2, H // 2), Image.LANCZOS).save(os.path.join(out, f"fwhere_{tag}_whole.png"))
    print(f"{tag}: busiest window at ({x0},{y0}); pixels flickering over 8/255 somewhere in the run: {(band > 16).mean() * 100:.2f}%")
