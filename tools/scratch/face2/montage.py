"""montage.py out.jpg cols width img... [--crop x0,y0,x1,y1 (fractions)]: a labelled contact sheet."""
import os, sys
from PIL import Image, ImageDraw
a = sys.argv[1:]
crop = None
if "--crop" in a:
    i = a.index("--crop"); crop = [float(x) for x in a[i + 1].split(",")]; del a[i:i + 2]
out, cols, w = a[0], int(a[1]), int(a[2])
ims = []
for p in a[3:]:
    im = Image.open(p).convert("RGB")
    if crop:
        W, H = im.size
        im = im.crop((int(crop[0] * W), int(crop[1] * H), int(crop[2] * W), int(crop[3] * H)))
    h = int(im.size[1] * w / im.size[0])
    ims.append((os.path.splitext(os.path.basename(p))[0], im.resize((w, h), Image.LANCZOS)))
h = max(i.size[1] for _, i in ims)
rows = (len(ims) + cols - 1) // cols
sheet = Image.new("RGB", (cols * w, rows * (h + 18)), (20, 20, 20))
d = ImageDraw.Draw(sheet)
for k, (n, im) in enumerate(ims):
    x, y = (k % cols) * w, (k // cols) * (h + 18)
    sheet.paste(im, (x, y + 18))
    d.text((x + 4, y + 3), n, fill=(230, 230, 230))
sheet.save(out, quality=90)
print(out, sheet.size)
