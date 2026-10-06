"""Scratch: tile game shots, each cropped about a point. python tile.py <prefix> <out> [cx cy w h cols pick]"""
import sys
from pathlib import Path

from PIL import Image

SHOTS = Path(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a1e3002b800ee55ac\godot\.shots")
prefix, out = sys.argv[1], sys.argv[2]
files = sorted(SHOTS.glob(f"{prefix}_*.png"))
im0 = Image.open(files[0])
W, H = im0.size
cx = float(sys.argv[3]) if len(sys.argv) > 3 else 0.5
cy = float(sys.argv[4]) if len(sys.argv) > 4 else 0.5
w = int(sys.argv[5]) if len(sys.argv) > 5 else 400
h = int(sys.argv[6]) if len(sys.argv) > 6 else 400
cols = int(sys.argv[7]) if len(sys.argv) > 7 else 8
pick = int(sys.argv[8]) if len(sys.argv) > 8 else 1
files = files[::pick]
x0, y0 = int(cx * W - w / 2), int(cy * H - h / 2)
rows = (len(files) + cols - 1) // cols
board = Image.new("RGB", (w * min(cols, len(files)), h * rows))
for i, f in enumerate(files):
    board.paste(Image.open(f).convert("RGB").crop((x0, y0, x0 + w, y0 + h)), ((i % cols) * w, (i // cols) * h))
board.save(out)
print(out, W, H, board.size)
