"""Contact sheet: python sheet.py <out.jpg> <cell px> <cols> <img> [<img> ...] (labels from file names; glob patterns ok)."""
import glob
import math
import os
import sys

from PIL import Image, ImageDraw

out, cell, cols = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
files = []
for a in sys.argv[4:]:
    files += sorted(glob.glob(a)) if any(c in a for c in "*?") else [a]
ims = [Image.open(f).convert("RGB") for f in files]
h = int(cell * ims[0].height / ims[0].width)
rows = math.ceil(len(ims) / cols)
s = Image.new("RGB", (cols * cell, rows * (h + 18)), (16, 16, 16))
d = ImageDraw.Draw(s)
for i, (f, im) in enumerate(zip(files, ims)):
    x, y = (i % cols) * cell, (i // cols) * (h + 18)
    s.paste(im.resize((cell, h), Image.LANCZOS), (x, y + 18))
    d.text((x + 4, y + 3), os.path.splitext(os.path.basename(f))[0], fill=(230, 220, 200))
s.save(out, quality=90)
print("sheet", s.size)
