"""Crop the same region from several stills and lay them side by side, at full resolution.
python crops.py OUT x0 y0 x1 y1 still1 still2 ...   (stills are names in godot/.shots, or paths)"""
import os, sys
from PIL import Image
W = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7a4c20bcfd7ccfd3\godot\.shots"
out = sys.argv[1]
x0, y0, x1, y1 = map(int, sys.argv[2:6])
names = sys.argv[6:]
ims = []
for n in names:
    p = n if os.path.isabs(n) else os.path.join(W, n if n.endswith(".png") else n + ".png")
    ims.append(Image.open(p).convert("RGB").crop((x0, y0, x1, y1)))
w, h = x1 - x0, y1 - y0
cols = min(len(ims), max(1, 1920 // w))
rows = (len(ims) + cols - 1) // cols
s = Image.new("RGB", (cols * w, rows * h), (30, 30, 30))
for i, im in enumerate(ims):
    s.paste(im, ((i % cols) * w, (i // cols) * h))
s.save(out if os.path.isabs(out) else os.path.join(os.path.dirname(os.path.abspath(__file__)), out))
print(s.size)
