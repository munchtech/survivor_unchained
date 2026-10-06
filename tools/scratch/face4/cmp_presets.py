"""cmp_presets.py out.jpg renderdir refsdir name ...: each reference's two views beside her fitted render (0, 30, 90)."""
import os
import sys

from PIL import Image, ImageDraw

out, rdir, fdir = sys.argv[1:4]
rows = []
S = 330
for name in sys.argv[4:]:
    r = Image.open(os.path.join(fdir, name + ".png")).convert("RGB")
    w, h = r.size
    cells = []
    for im in (r.crop((0, 0, w // 2, h)), r.crop((w // 2, 0, w, h))):
        s = min(im.size)
        x0 = (im.width - s) // 2
        cells.append(im.crop((x0, 0, x0 + s, s)).resize((S, S)))
    for v in ("0", "30", "90"):
        p = os.path.join(rdir, f"{name}_{v}.png")
        cells.append(Image.open(p).convert("RGB").resize((S, S)) if os.path.exists(p) else Image.new("RGB", (S, S)))
    row = Image.new("RGB", (S * len(cells), S + 18), (16, 16, 16))
    for i, c in enumerate(cells):
        row.paste(c, (i * S, 18))
    ImageDraw.Draw(row).text((4, 3), name, fill=(230, 220, 200))
    rows.append(row)
sheet = Image.new("RGB", (rows[0].width, sum(r.height for r in rows)))
y = 0
for r in rows:
    sheet.paste(r, (0, y))
    y += r.height
sheet.save(out, quality=90)
print(sheet.size)
