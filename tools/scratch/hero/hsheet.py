"""Male hero lead's sheet helper (scratchpad/hero, not shared): python hsheet.py out.jpg W H img1 img2 ...
Crops each image's centre W x H (or path@x,y to centre there) and lays them side by side.
Relative paths are in ../r."""
import os, sys
from PIL import Image
R = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "r")
out, W, H = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
ims = []
for a in sys.argv[4:]:
    c = None
    if "@" in a:
        a, xy = a.split("@")
        c = tuple(int(v) for v in xy.split(","))
    p = a if os.path.isabs(a) else os.path.join(R, a)
    im = Image.open(p).convert("RGB")
    cx, cy = c or (im.width // 2, im.height // 2)
    x0, y0 = max(0, min(im.width - W, cx - W // 2)), max(0, min(im.height - H, cy - H // 2))
    ims.append(im.crop((x0, y0, x0 + W, y0 + H)))
sheet = Image.new("RGB", (W * len(ims), H))
for i, im in enumerate(ims):
    sheet.paste(im, (i * W, 0))
o = out if os.path.isabs(out) else os.path.join(R, out)
sheet.save(o, quality=92)
print(o, sheet.size)
