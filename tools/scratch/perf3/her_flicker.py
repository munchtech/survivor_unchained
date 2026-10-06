"""Where her picture changes frame to frame: for each tag, the 8 frames' mean
absolute frame-to-frame change per pixel round her, amplified, side by side
(over a dimmed frame), with the mean over her silhouette's edges printed.
python her_flicker.py CAM SCALE OUT TAG..."""
import os
import sys

import numpy as np
from PIL import Image

SHOTS = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a56abaf3a104be675\godot\.shots"
cam, k, out, tags = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4:]
half = {"12.5": (150, 220), "23": (70, 110), "31": (55, 85)}[cam]
tiles = []
for t in tags:
    pre = f"her_{t}_{cam.replace('.', '_')}_"
    fs = sorted(f for f in os.listdir(SHOTS) if f.startswith(pre) and f.endswith(".png"))
    st = []
    for f in fs:
        a = np.asarray(Image.open(os.path.join(SHOTS, f)).convert("RGB")).astype(float)
        h, w, _ = a.shape
        st.append(a[h // 2 - half[1]:h // 2 + half[1], w // 2 - half[0]:w // 2 + half[0]])
    st = np.stack(st)
    d = np.abs(np.diff(st, axis=0)).mean(axis=(0, 3))
    print(f"{t}: mean {d.mean():.2f}, 99th pct {np.percentile(d, 99):.1f}, px over 6: {(d > 6).sum()}")
    base = st[-1] * 0.3
    heat = np.clip(d * 12, 0, 255)
    img = base.copy()
    img[..., 0] = np.maximum(img[..., 0], heat)
    img[..., 1] = np.maximum(img[..., 1], heat * 0.8)
    tiles.append(Image.fromarray(img.astype(np.uint8)).resize((img.shape[1] * k, img.shape[0] * k), Image.NEAREST))
W, H = tiles[0].size
canvas = Image.new("RGB", ((W + 8) * len(tiles), H), "white")
for i, t in enumerate(tiles):
    canvas.paste(t, (i * (W + 8), 0))
canvas.save(out)
