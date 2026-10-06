"""Where the whole picture changes frame to frame (8 frames, 1/30 s apart), for
the photoscans before (A) and after (B) their mipmaps: per-pixel mean absolute
frame-to-frame change, amplified, over a dimmed frame; A above B. The stats
leave out a box round her (she breathes in both).
    python scan_flicker.py NAME OUT [--crop x0 y0 x1 y1] [--scale K]
NAME is e.g. pack_23 (files scanA_pack_23_*.png and scanB_pack_23_*.png)."""
import os
import sys

import numpy as np
from PIL import Image

SHOTS = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0eb8c612c94d4aa5\godot\.shots"
argv = sys.argv[1:]
crop = None
k = 1
if "--crop" in argv:
    i = argv.index("--crop")
    crop = [int(v) for v in argv[i + 1:i + 5]]
    del argv[i:i + 5]
if "--scale" in argv:
    i = argv.index("--scale")
    k = float(argv[i + 1])
    del argv[i:i + 2]
name, out = argv[0], argv[1]


def stack(tag):
    pre = f"scan{tag}_{name}_"
    fs = sorted(f for f in os.listdir(SHOTS) if f.startswith(pre) and f.endswith(".png"))
    return np.stack([np.asarray(Image.open(os.path.join(SHOTS, f)).convert("RGB")).astype(float) for f in fs]), len(fs)


rows = []
for tag in ("A", "B"):
    st, n = stack(tag)
    h, w = st.shape[1:3]
    d = np.abs(np.diff(st, axis=0)).mean(axis=(0, 3))
    mask = np.ones_like(d, bool)
    mask[h // 2 - 260:h // 2 + 160, w // 2 - 160:w // 2 + 160] = False
    dm = d[mask]
    print(f"{name} {tag} ({n} frames): mean {dm.mean():.3f}, 99th {np.percentile(dm, 99):.1f}, px over 6: {(dm > 6).sum()}, over 12: {(dm > 12).sum()}")
    img = st[-1] * 0.35
    heat = np.clip(d * 12, 0, 255)
    img[..., 0] = np.maximum(img[..., 0], heat)
    img[..., 1] = np.maximum(img[..., 1], heat * 0.8)
    if crop:
        img = img[crop[1]:crop[3], crop[0]:crop[2]]
    im = Image.fromarray(img.astype(np.uint8))
    if k != 1:
        im = im.resize((int(im.width * k), int(im.height * k)), Image.NEAREST if k > 1 else Image.BOX)
    rows.append(im)
canvas = Image.new("RGB", (rows[0].width, rows[0].height * 2 + 8), "white")
canvas.paste(rows[0], (0, 0))
canvas.paste(rows[1], (0, rows[0].height + 8))
canvas.save(out)
