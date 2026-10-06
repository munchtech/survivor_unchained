"""How wide a warm glow on the ground is: python warmth.py SHOT X Y [ROWS]

Along the row through (X, Y) (and the column through it), the warmth R-B of the frame, blurred, is
compared with the ground's own far off; the glow's width is where it stands 12 over that. A night
ground is blue-grey (R below B), so an amber light's reach shows plainly in R-B."""
import sys
import numpy as np
from PIL import Image, ImageFilter
from shots import shot

name, x, y = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
im = Image.open(shot(name + ".png")).convert("RGB").filter(ImageFilter.BoxBlur(6))
a = np.asarray(im).astype(np.float32)
warm = a[:, :, 0] - a[:, :, 2]


def reach(line, c):
    base = np.median(np.concatenate([line[: max(1, c - 400)], line[c + 400:]])) if len(line) > 900 else np.median(line)
    over = line > base + 12
    lo = c
    while lo > 0 and over[lo - 1]:
        lo -= 1
    hi = c
    while hi < len(line) - 1 and over[hi + 1]:
        hi += 1
    return lo, hi, base, line[c]


lo, hi, base, peak = reach(warm[y, :], x)
print(f"row y={y}: warm from x={lo} to {hi} = {hi - lo} px (ground {base:.0f}, at foot {peak:.0f})")
lo, hi, base, peak = reach(warm[:, x], y)
print(f"col x={x}: warm from y={lo} to {hi} = {hi - lo} px")
