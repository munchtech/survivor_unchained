"""Sheets side by side (or stacked with -v): cat.py out.png a.png b.png ..."""
import sys
from PIL import Image

args = sys.argv[1:]
vert = args[0] == '-v'
if vert:
    args = args[1:]
out, files = args[0], args[1:]
S = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa4f5fc266b043035\tools\anim\out\sheets\\'
ims = [Image.open(f if (':' in f or '/' in f) else S + f) for f in files]
if vert:
    b = Image.new('RGB', (max(i.width for i in ims), sum(i.height for i in ims)))
    y = 0
    for i in ims:
        b.paste(i, (0, y))
        y += i.height
else:
    b = Image.new('RGB', (sum(i.width for i in ims), max(i.height for i in ims)))
    x = 0
    for i in ims:
        b.paste(i, (x, 0))
        x += i.width
b.save(out)
print(out, b.size)
