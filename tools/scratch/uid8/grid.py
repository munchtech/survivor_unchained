"""A grid sheet of shots: python grid.py OUT COLS W name... (each shot resized to W wide, 16:9)."""
import os
import sys
from PIL import Image

S = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa1f430bd64b8d1ce\godot\.shots'
out, cols, w = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
names = sys.argv[4:]
h = w * 9 // 16
ims = [Image.open(os.path.join(S, n + '.png')).convert('RGB').resize((w, h), Image.LANCZOS) for n in names]
rows = (len(ims) + cols - 1) // cols
o = Image.new('RGB', (w * cols, h * rows))
for i, im in enumerate(ims):
    o.paste(im, ((i % cols) * w, (i // cols) * h))
o.save(out, quality=90)
