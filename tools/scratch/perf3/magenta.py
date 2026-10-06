"""Count magenta pixels (the debug tint) in shots: python magenta.py PNG..."""
import sys

import numpy as np
from PIL import Image

for f in sys.argv[1:]:
    a = np.asarray(Image.open(f).convert("RGB")).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    m = (r > 120) & (b > 120) & (g < 0.6 * np.minimum(r, b)) & (abs(r - b) < 80)
    ys, xs = np.nonzero(m)
    where = f" x {xs.min()}-{xs.max()} y {ys.min()}-{ys.max()}" if len(xs) else ""
    print(f"{f.split(chr(92))[-1].split('/')[-1]}: {m.sum()} magenta px{where}")
