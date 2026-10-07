"""lin_down.py IN OUT SCALE [srgb]: a picture made smaller in linear light (as a GPU filters an sRGB texture), or in
its sRGB values (as an image viewer does), by an area average."""
import sys
import numpy as np
from PIL import Image
a = np.asarray(Image.open(sys.argv[1]).convert('RGB')).astype(np.float32) / 255
k = float(sys.argv[3])
srgb = len(sys.argv) > 4
if not srgb:
    a = np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)
h, w = a.shape[:2]
H, W = int(h * k), int(w * k)
out = np.stack([np.asarray(Image.fromarray(a[..., c]).resize((W, H), Image.BOX)) for c in range(3)], 2)
if not srgb:
    out = np.where(out <= 0.0031308, out * 12.92, 1.055 * np.maximum(out, 0) ** (1 / 2.4) - 0.055)
Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)).save(sys.argv[2])
print(sys.argv[2], W, H)
