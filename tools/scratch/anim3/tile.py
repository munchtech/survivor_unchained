"""Tile game frames: python tile.py out.png prefix first last [step] [cx cy w h] [cols]
Frames are godot/.shots/<prefix>_<k>.png; each is cropped to the box centred at (cx, cy)."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw

SHOTS = Path(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a03acf30b3e9bdd70\godot\.shots")
out, prefix, a, b = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
step = int(sys.argv[5]) if len(sys.argv) > 5 else 1
cx, cy, w, h = (int(x) for x in sys.argv[6:10]) if len(sys.argv) > 9 else (960, 540, 480, 480)
cols = int(sys.argv[10]) if len(sys.argv) > 10 else 8
ks = list(range(a, b + 1, step))
rows = (len(ks) + cols - 1) // cols
board = Image.new("RGB", (cols * w, rows * h), (20, 20, 20))
d = ImageDraw.Draw(board)
for i, k in enumerate(ks):
    p = SHOTS / (f"{prefix}_{k:02d}.png" if (SHOTS / f"{prefix}_{k:02d}.png").exists() else f"{prefix}_{k}.png")
    if not p.exists():
        continue
    im = Image.open(p).crop((cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2))
    x, y = (i % cols) * w, (i // cols) * h
    board.paste(im, (x, y))
    d.text((x + 4, y + 4), f"{k}", fill=(255, 255, 0))
board.save(out)
print(out, board.size)
