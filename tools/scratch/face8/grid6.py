"""python grid6.py out.jpg cols size img... : images side by side, each scaled to `size` wide (relative to this folder)."""
import os
import sys
from PIL import Image

D = os.path.dirname(os.path.abspath(__file__))
out, cols, size = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
fs = [os.path.join(D, f) for f in sys.argv[4:]]
ims = [Image.open(f).convert('RGB') for f in fs]
ims = [a.resize((size, int(size * a.height / a.width))) for a in ims]
h = max(a.height for a in ims)
rows = (len(ims) + cols - 1) // cols
im = Image.new('RGB', (cols * size, rows * h))
for i, a in enumerate(ims):
    im.paste(a, ((i % cols) * size, (i // cols) * h))
im.save(os.path.join(D, out), quality=88)
