"""python sheet2.py <dir> <out.jpg> <height> name[:crop] ...   crop = c (middle 760 px) or x0,y0,x1,y1"""
import os
import sys
from PIL import Image, ImageDraw

D, OUT, H = sys.argv[1], sys.argv[2], int(sys.argv[3])
ims = []
for a in sys.argv[4:]:
    n, _, crop = a.partition(":")
    p = n if os.path.isabs(n) else os.path.join(D, n if n.endswith(".png") else n + ".png")
    if not os.path.exists(p):
        continue
    im = Image.open(p).convert("RGB")
    if crop == "c":
        c = im.width // 2
        im = im.crop((c - 380, 0, c + 380, im.height))
    elif crop:
        im = im.crop(tuple(int(v) for v in crop.split(",")))
    ims.append((os.path.basename(n), im.resize((round(im.width * H / im.height), H), Image.LANCZOS)))
W = sum(i.width for _, i in ims) + 8 * (len(ims) - 1)
s = Image.new("RGB", (W, H + 24), (20, 20, 20))
d = ImageDraw.Draw(s)
x = 0
for n, i in ims:
    s.paste(i, (x, 24))
    d.text((x + 6, 5), n, fill=(230, 230, 230))
    x += i.width + 8
s.save(OUT if os.path.isabs(OUT) else os.path.join(D, OUT), quality=92)
print(OUT, s.size)
