"""The look judge's round 2 fail: the glow halo round the white light point at (361,500) in take s01, clip second 0.5.
  python tools/scratch/godot47/halo.py REF.png NEW.png [NEW2.png ...]   mean R,G,B (8-bit levels) in rings round the point, NEW minus REF
"""
import sys
import numpy as np
from PIL import Image
CX, CY = 361, 500
RINGS = [(0, 5), (5, 10), (10, 20), (20, 35), (35, 50), (50, 80), (80, 120)]
def rings(p):
    a = np.asarray(Image.open(p).convert("RGB")).astype(np.float32)
    y, x = np.mgrid[0:a.shape[0], 0:a.shape[1]]
    d = np.hypot(x - CX, y - CY)
    return np.array([a[(d >= lo) & (d < hi)].mean(0) for lo, hi in RINGS]), a.mean()
ref, rm = rings(sys.argv[1])
print("rings px: " + "  ".join(f"{lo}-{hi}" for lo, hi in RINGS) + " | frame mean")
print("REF R: " + " ".join(f"{v:6.1f}" for v in ref[:, 0]) + f" | {rm:.2f}")
for p in sys.argv[2:]:
    n, nm = rings(p)
    d = n - ref
    print("dR " + " ".join(f"{v:+5.1f}" for v in d[:, 0]) + " | dG " + " ".join(f"{v:+5.1f}" for v in d[:, 1]) + " | dB " + " ".join(f"{v:+5.1f}" for v in d[:, 2]) + f" | {nm - rm:+.2f} | rms {np.sqrt((d[2:6] ** 2).mean()):.2f} | {p.split('sw_')[-1][:14]}")
