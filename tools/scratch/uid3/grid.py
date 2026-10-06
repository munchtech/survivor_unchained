import sys, os, math
from PIL import Image
# grid.py OUT COLS SIZE file1 file2 ...: pictures in a grid, each at SIZE square.
out, cols, size = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
fs = sys.argv[4:]
rows = math.ceil(len(fs) / cols)
s = Image.new('RGB', (cols * size, rows * size), (20, 20, 20))
for i, f in enumerate(fs):
    im = Image.open(f).convert('RGB')
    im.thumbnail((size, size), Image.LANCZOS)
    s.paste(im, ((i % cols) * size, (i // cols) * size))
s.save(out, quality=92)
print(out, s.size)
