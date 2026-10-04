"""A contact sheet of frames, to look at many at once before the ones worth full size.

    python tools/combat/sheet.py OUT.png COLUMNS WIDTH frame1.png frame2.png ... (or a glob)

Each frame is scaled to WIDTH pixels and labelled with its file name.
"""
import glob
import os
import sys

from PIL import Image, ImageDraw

out, cols, width = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
files = []
for a in sys.argv[4:]:
    files += sorted(glob.glob(a)) if any(c in a for c in "*?") else [a]
ims = []
for f in files:
    im = Image.open(f).convert("RGB")
    im = im.resize((width, int(im.height * width / im.width)), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, width, 18], fill=(0, 0, 0))
    d.text((4, 2), os.path.basename(f), fill=(255, 255, 0))
    ims.append(im)
rows = (len(ims) + cols - 1) // cols
sheet = Image.new("RGB", (cols * width, rows * ims[0].height), (20, 20, 20))
for i, im in enumerate(ims):
    sheet.paste(im, ((i % cols) * width, (i // cols) * ims[0].height))
sheet.save(out)
print(out, sheet.size)
