"""How much of a frame reads as flat black (the experience director's test:
no more than a fifth of a minute-6 frame), and the ground's value and local
contrast: python black.py NAME [NAME ...]. The HUD's bottom band and top
bar are left out. A pixel is flat black when its sRGB luma is under 0.09 and
the luma round it (a 15 px box) varies by under 0.02."""
import sys, os
import numpy as np
from PIL import Image
from scipy.ndimage import uniform_filter

SHOTS = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0b61c278bdd5c994\godot\.shots"
for n in sys.argv[1:]:
    p = n if os.path.exists(n) else os.path.join(SHOTS, n + ".png")
    a = np.asarray(Image.open(p).convert("RGB")).astype(np.float32) / 255
    h = a.shape[0]
    a = a[int(h * 0.2):int(h * 0.85)]
    y = a @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
    m = uniform_filter(y, 15)
    sd = np.sqrt(np.maximum(uniform_filter(y * y, 15) - m * m, 0))
    flat = (y < 0.09) & (sd < 0.02)
    print(f"{os.path.basename(n):24s} flat-black {flat.mean() * 100:5.1f}%  median luma {np.median(y):.3f}  "
          f"p10 {np.percentile(y, 10):.3f}  p90 {np.percentile(y, 90):.3f}  local sd {np.median(sd):.4f}")
