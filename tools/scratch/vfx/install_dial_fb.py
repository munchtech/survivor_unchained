"""The watch dial as a one-frame flipbook (drawn flat in the air round her, over the crowd,
where a ground decal was hidden under it): light only, premultiplied, its outer ring kept
inside the flipbook shader's round mask (0.86 of the half-width)."""
import json
import os

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
WT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a560452c597415545"
FB = os.path.join(WT, "godot", "art", "fx", "fb")
N = 512
src = Image.open(os.path.join(HERE, "marks_out", "watch_dial2_source.jpg")).convert("RGB")
# The painted dial's outer ring sits at about 0.95 of its half-width: shrink it into 0.82.
inner = int(N * 0.82 / 0.95)
small = src.resize((inner, inner), Image.LANCZOS)
canvas = Image.new("RGB", (N, N), (0, 0, 0))
canvas.paste(small, ((N - inner) // 2, (N - inner) // 2))
c = np.asarray(canvas).astype(np.float32) / 255.0
hi = c.max(axis=2)
a = np.clip((hi - 0.2) / 0.45, 0, 1)
y, x = np.mgrid[0:N, 0:N].astype(np.float32)
r = np.hypot(x - N / 2, y - N / 2) / (N / 2)
a *= np.clip((0.86 - r) / 0.04, 0, 1)
rgb = np.minimum(c, a[..., None])  # premultiplied, never brighter than its alpha
Image.fromarray((np.dstack([rgb, a]) * 255 + 0.5).astype(np.uint8), "RGBA").save(os.path.join(FB, "watch_dial.png"))
with open(os.path.join(FB, "watch_dial.json"), "w") as f:
    json.dump({"grid": 1, "frames": 1, "fps": 1, "source": "watch_dial2 (tools/comfy/marks.py)"}, f)
print("border alpha", float(np.concatenate([a[:6].ravel(), a[-6:].ravel(), a[:, :6].ravel(), a[:, -6:].ravel()]).max()))
