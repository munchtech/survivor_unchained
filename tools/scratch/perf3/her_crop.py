"""Her at one zoom across tags, cropped round her (and her shadow) and
enlarged, side by side, with each tag's difference from the first amplified
below it. python her_crop.py CAM SCALE OUT TAG... (frame 07 of each run)."""
import os
import sys

import numpy as np
from PIL import Image

SHOTS = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a56abaf3a104be675\godot\.shots"
cam, k, out, tags = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4:]
half = {"12.5": (190, 230), "23": (110, 130), "31": (85, 100)}[cam]
ims = []
for t in tags:
    f = os.path.join(SHOTS, f"her_{t}_{cam.replace('.', '_')}_07.png")
    a = np.asarray(Image.open(f).convert("RGB"))
    h, w, _ = a.shape
    cy, cx = h // 2, w // 2
    ims.append(a[cy - half[1]:cy + half[1], cx - half[0]:cx + half[0]].astype(int))
row1 = [Image.fromarray(x.astype(np.uint8)).resize((x.shape[1] * k, x.shape[0] * k), Image.NEAREST) for x in ims]
row2 = [Image.fromarray(np.clip(np.abs(x - ims[0]) * 4, 0, 255).astype(np.uint8)).resize((x.shape[1] * k, x.shape[0] * k), Image.NEAREST) for x in ims]
W, H = row1[0].size
canvas = Image.new("RGB", ((W + 8) * len(tags), H * 2 + 8), "white")
for i, (a, b) in enumerate(zip(row1, row2)):
    canvas.paste(a, (i * (W + 8), 0))
    canvas.paste(b, (i * (W + 8), H + 8))
canvas.save(out)
print(canvas.size)
