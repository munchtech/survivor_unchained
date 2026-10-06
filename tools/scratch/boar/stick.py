"""Stick figures from a frames JSON: side view (forward to the left), frames tiled."""
import json, sys
from PIL import Image, ImageDraw
frames = json.load(open(sys.argv[1]))
cols = 6
W, H, S = 300, 220, 160
rows = (len(frames) + cols - 1) // cols
img = Image.new("RGB", (W * cols, H * rows), (250, 250, 248))
d = ImageDraw.Draw(img)
for i, fr in enumerate(frames):
    ox, oy = (i % cols) * W + W // 2, (i // cols) * H + H - 20
    d.line([(ox - 140, oy), (ox + 140, oy)], fill=(180, 180, 180))
    for n, (h, t) in fr.items():
        if n == "Root":
            continue
        col = (200, 40, 40) if n.endswith("_L") else (40, 80, 200) if n.endswith("_R") else (30, 30, 30)
        # side view: x = y (back to the right), up = z
        d.line([(ox + h[1] * S, oy - h[2] * S), (ox + t[1] * S, oy - t[2] * S)], fill=col, width=2)
    d.text((ox - 140, oy - H + 25), str(i), fill=(0, 0, 0))
img.save(sys.argv[2])
