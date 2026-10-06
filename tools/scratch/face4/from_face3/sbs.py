"""sbs.py out.jpg h  label=img[:x0,y0,x1,y1] ... : a row-per-pair side-by-side; each image cropped (fractions) and scaled to height h.
Pairs: consecutive args form a row of two."""
import sys
from PIL import Image, ImageDraw
out, h = sys.argv[1], int(sys.argv[2])
items = []
for a in sys.argv[3:]:
    lab, rest = a.split("=", 1)
    crop = None
    if rest.count(":") and rest.rsplit(":", 1)[1].count(",") == 3:
        rest, c = rest.rsplit(":", 1)
        crop = [float(x) for x in c.split(",")]
    im = Image.open(rest).convert("RGB")
    if crop:
        W, H = im.size
        im = im.crop((int(crop[0] * W), int(crop[1] * H), int(crop[2] * W), int(crop[3] * H)))
    im = im.resize((int(im.size[0] * h / im.size[1]), h), Image.LANCZOS)
    items.append((lab, im))
rows = [items[i:i + 2] for i in range(0, len(items), 2)]
wmax = max(sum(i.size[0] for _, i in r) + 8 for r in rows)
sheet = Image.new("RGB", (wmax, len(rows) * (h + 22)), (18, 18, 18))
d = ImageDraw.Draw(sheet)
for k, r in enumerate(rows):
    x = 0
    for lab, im in r:
        sheet.paste(im, (x, k * (h + 22) + 22))
        d.text((x + 6, k * (h + 22) + 5), lab, fill=(235, 235, 235))
        x += im.size[0] + 8
sheet.save(out, quality=92)
print(out, sheet.size)
