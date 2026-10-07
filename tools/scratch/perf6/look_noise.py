"""The Look's temporal noise over consecutive frames (164 Hz): her hair (top of her head) and her
face (cheeks, brow), mean |frame - next| and the share over 8/255, regions in 1080p units.
    python look_noise.py TAG [TAG ...]"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import crops as C  # noqa: E402

REGIONS = {"hair": (800, 150, 300, 110), "face": (860, 330, 210, 170)}

print(f"{'run':16s} " + " ".join(f"{k + ' mean':>10s} {k + ' >8':>8s}" for k in REGIONS))
for t in sys.argv[1:]:
    fs = C.frames(t)
    st = np.stack([C.load(f).mean(axis=2) for f in fs])
    k = st.shape[1] / 1080
    row = []
    for x, y, w, h in REGIONS.values():
        r = st[:, round(y * k):round((y + h) * k), round(x * k):round((x + w) * k)]
        d = np.abs(np.diff(r, axis=0))
        row.append(f"{d.mean():10.3f} {(d > 8).mean() * 100:7.2f}%")
    print(f"{t:16s} " + " ".join(row))
