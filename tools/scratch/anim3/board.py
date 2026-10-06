"""Tile whole stills scaled: python board.py out.png width cols file1 file2 ... (names under godot/.shots)."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw

SHOTS = Path(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a03acf30b3e9bdd70\godot\.shots")
out, w, cols = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
files = sys.argv[4:]
ims = [Image.open(SHOTS / f) for f in files]
h = int(w * ims[0].height / ims[0].width)
rows = (len(ims) + cols - 1) // cols
b = Image.new("RGB", (cols * w, rows * h), (0, 0, 0))
d = ImageDraw.Draw(b)
for i, (f, im) in enumerate(zip(files, ims)):
    x, y = (i % cols) * w, (i // cols) * h
    b.paste(im.resize((w, h)), (x, y))
    d.text((x + 4, y + 4), f, fill=(255, 255, 0))
b.save(out)
print(out, b.size)
