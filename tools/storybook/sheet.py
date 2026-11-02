"""python tools/storybook/sheet.py <out.jpg> <cell_w> <cols> <img>... : a labelled contact sheet."""
import sys
from PIL import Image, ImageDraw
out, cw, cols, files = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4:]
ims = [Image.open(f).convert("RGB") for f in files]
cells = [im.resize((cw, round(im.height * cw / im.width)), Image.LANCZOS) for im in ims]
rows = [cells[i:i + cols] for i in range(0, len(cells), cols)]
H = sum(max(c.height for c in r) + 18 for r in rows)
S = Image.new("RGB", (cw * cols + 4 * (cols - 1), H), (40, 40, 40))
d = ImageDraw.Draw(S); y = 0; k = 0
for r in rows:
    for i, c in enumerate(r):
        x = i * (cw + 4); S.paste(c, (x, y + 18)); d.text((x + 3, y + 3), files[k].replace("\\", "/").split("/")[-1], fill=(255, 255, 0)); k += 1
    y += max(c.height for c in r) + 18
S.save(out, quality=88)
