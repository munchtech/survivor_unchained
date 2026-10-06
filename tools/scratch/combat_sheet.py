"""Contact sheet: python combat_sheet.py OUT.png COLS WIDTH file1 file2 ... (or a glob)
Each frame is scaled to WIDTH px and labelled with its file name."""
import sys, glob, os
from PIL import Image, ImageDraw, ImageFont

out, cols, width = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
files = []
for a in sys.argv[4:]:
    files += sorted(glob.glob(a)) if any(c in a for c in "*?") else [a]
ims = []
for f in files:
    im = Image.open(f).convert("RGB")
    h = int(im.height * width / im.width)
    im = im.resize((width, h), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, width, 18], fill=(0, 0, 0))
    d.text((4, 2), os.path.basename(f), fill=(255, 255, 0))
    ims.append(im)
rows = (len(ims) + cols - 1) // cols
h = ims[0].height
sheet = Image.new("RGB", (cols * width, rows * h), (20, 20, 20))
for i, im in enumerate(ims):
    sheet.paste(im, ((i % cols) * width, (i // cols) * h))
sheet.save(out)
print(out, sheet.size)
