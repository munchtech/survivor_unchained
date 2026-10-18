"""Pixels of a toprender.py picture where the cap shows (blue over red), at 0.25 mm a pixel."""
import sys, numpy as np
from PIL import Image
for p in sys.argv[1:]:
    a = np.asarray(Image.open(p).convert("RGB"), float)
    print(p.split("\\")[-1], "cap showing: %d px (%.0f mm2)" % (((a[..., 2] > a[..., 0]) & (a.sum(2) > 20)).sum(), ((a[..., 2] > a[..., 0]) & (a.sum(2) > 20)).sum() * 0.0625))
