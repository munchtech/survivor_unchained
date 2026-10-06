"""compare.py <out.jpg> <render dir> name=ref.png ... : each reference's two views beside her fitted renders (front, 30)."""
import os
import sys

from PIL import Image, ImageDraw

rows = []
d = sys.argv[2]
for a in sys.argv[3:]:
    name, ref = a.split("=", 1)
    r = Image.open(ref).convert("RGB")
    w, h = r.size
    L, R = r.crop((0, 0, w // 2, h)), r.crop((w // 2, 0, w, h))
    cells = []
    for im in (L, R):
        # (a square about the face: the half's middle, upper part)
        s = min(im.size)
        x0 = (im.width - s) // 2
        cells.append(im.crop((x0, 0, x0 + s, s)).resize((400, 400)))
    for v in ("0", "30"):
        p = os.path.join(d, f"{name}_{v}.png")
        cells.append(Image.open(p).convert("RGB").resize((400, 400)) if os.path.exists(p) else Image.new("RGB", (400, 400)))
    row = Image.new("RGB", (1600, 418), (16, 16, 16))
    dr = ImageDraw.Draw(row)
    for i, c in enumerate(cells):
        row.paste(c, (i * 400, 18))
    dr.text((4, 3), name, fill=(230, 220, 200))
    rows.append(row)
sheet = Image.new("RGB", (1600, 418 * len(rows)))
for i, r in enumerate(rows):
    sheet.paste(r, (0, i * 418))
sheet.save(sys.argv[1], quality=90)
print(sheet.size)
