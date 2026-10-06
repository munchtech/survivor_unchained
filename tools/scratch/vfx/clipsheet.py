"""Frames of clips side by side: python clipsheet.py OUT.png N clip.mp4 [clip.mp4 ...] (N frames each, one row per clip)."""
import sys
import imageio.v3 as iio
import numpy as np
from PIL import Image, ImageDraw

out, n, clips = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
W = 220
rows = []
for c in clips:
    frames = iio.imread(c)
    idx = np.linspace(0, len(frames) - 1, n).astype(int)
    row = Image.new("RGB", (W * n, W + 16), (30, 0, 30))
    for k, i in enumerate(idx):
        im = Image.fromarray(frames[i]).convert("RGB").resize((W, W))
        row.paste(im, (k * W, 16))
    ImageDraw.Draw(row).text((4, 2), c.split("/")[-1].split("\\")[-1] + f"  {len(frames)} frames", fill=(255, 255, 0))
    rows.append(row)
sheet = Image.new("RGB", (W * n, (W + 16) * len(rows)))
for r, row in enumerate(rows):
    sheet.paste(row, (0, r * (W + 16)))
sheet.save(out)
print(out, sheet.size)
