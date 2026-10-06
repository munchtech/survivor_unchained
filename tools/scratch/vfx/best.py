"""The frame of a run with the most coloured effect light round the survivor: python best.py RUN [RUN...]"""
import sys
import numpy as np
from PIL import Image
from shots import run

W, H = 760, 440
for name in sys.argv[1:]:
    best, at = -1, None
    for f in run(name):
        a = np.asarray(Image.open(f).convert("RGB")).astype(np.float32) / 255
        cy, cx = a.shape[0] // 2 + 20, a.shape[1] // 2
        a = a[cy - H // 2:cy + H // 2, cx - W // 2:cx + W // 2]
        mx, mn = a.max(axis=2), a.min(axis=2)
        lit = ((mx > 0.6) & ((mx - mn) > 0.2)).mean()
        if lit > best:
            best, at = lit, f[-6:-4]
    print(name, at, round(best * 1000, 1))
