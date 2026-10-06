"""A synthetic coded picture to test count.py without Godot."""
import json
import os

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'synth')
os.makedirs(OUT, exist_ok=True)


def lin2srgb(x):
    x = np.clip(x, 0, 1)
    return np.where(x <= 0.0031308, 12.92 * x, 1.055 * x ** (1 / 2.4) - 0.055) * 255


H, W = 540, 960
a = np.full((H, W, 3), 120, np.uint8)
yy, xx = np.mgrid[0:H, 0:W]
# camera in front: her left breast is on screen right
for (tx, ty, cut) in [(600, 270, 25), (360, 270, 32)]:
    d = np.hypot(xx - tx, yy - ty) / 10.0  # 10 px per cm
    m = (d < 6) & (yy < ty - cut)  # only the upper part shows
    a[m, 0] = np.round(lin2srgb(0.9 * d[m] / 6.0)).astype(np.uint8)
    a[m, 1] = 0
    a[m, 2] = 255
# her left breast, lower outer: a patch of tucked near skin 4 cm out
a[300:305, 640:650] = [int(lin2srgb(0.9 * 4 / 6)), 188, 255]
a[400:410, 100:110] = [0, 255, 255]   # deep tuck seen
a[420:425, 100:110] = [int(lin2srgb(0.6)), 255, 255]   # the edge ring
a[500:504, 480:484] = [0, 255, 0]                      # strip, 16 px
Image.fromarray(a).save(os.path.join(OUT, 'warden_test_chest_00.png'))
j = {"breast_l": {"xy": [600, 280], "behind": False}, "breast_r": {"xy": [360, 280], "behind": False},
     "tip_breast_l": {"xy": [600, 270], "behind": False, "up": [600, 250], "inner": [580, 270]},
     "tip_breast_r": {"xy": [360, 270], "behind": False, "up": [360, 250], "inner": [380, 270]},
     "size": {"xy": [960, 540], "behind": True}}
json.dump(j, open(os.path.join(OUT, 'warden_test_chest_00.json'), 'w'))
print('ok')
