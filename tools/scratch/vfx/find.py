"""Which frames of a run hold the most effect light round the survivor: python find.py RUN [W,H]

Counts bright, coloured pixels (not the pale grey dead) in the crop, per frame."""
import sys
import numpy as np
from PIL import Image
from shots import run

name = sys.argv[1]
W, H = (int(v) for v in (sys.argv[2] if len(sys.argv) > 2 else "900,600").split(","))
for f in run(name):
    a = np.asarray(Image.open(f).convert("RGB")).astype(np.float32) / 255
    cy, cx = a.shape[0] // 2 + 20, a.shape[1] // 2
    a = a[cy - H // 2:cy + H // 2, cx - W // 2:cx + W // 2]
    mx, mn = a.max(axis=2), a.min(axis=2)
    lit = ((mx > 0.75) & ((mx - mn) > 0.25)).mean() * 1000
    white = (mn > 0.85).mean() * 1000
    print(f[-6:-4], f"coloured {lit:6.1f}", f"white {white:6.1f}")
