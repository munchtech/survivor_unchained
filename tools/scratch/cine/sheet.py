"""A contact sheet of images (2 columns), for looking at many frames at once."""
import sys, glob, os
from PIL import Image, ImageDraw
out = sys.argv[1]
files = []
for a in sys.argv[2:]:
    files += sorted(glob.glob(a, recursive=True))
W = int(os.environ.get("SHEET_W", "760"))
cols = int(os.environ.get("SHEET_COLS", "2"))
ims = []
for f in files:
    im = Image.open(f).convert("RGB")
    h = int(im.height * W / im.width)
    ims.append((os.path.basename(os.path.dirname(f)) + "/" + os.path.basename(f), im.resize((W, h))))
rows = (len(ims) + cols - 1) // cols
rh = max(i.height for _, i in ims) + 18
sheet = Image.new("RGB", (cols * (W + 6), rows * rh), (20, 20, 20))
d = ImageDraw.Draw(sheet)
for k, (name, im) in enumerate(ims):
    x, y = (k % cols) * (W + 6), (k // cols) * rh
    sheet.paste(im, (x, y + 16))
    d.text((x + 4, y + 2), name[-60:], fill=(230, 230, 230))
sheet.save(out, quality=88)
print(out, sheet.size)
