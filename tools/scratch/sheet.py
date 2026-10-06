"""Contact sheet: lay PNGs (RGBA) over a ground colour, each at a given scale, labelled.
usage: python sheet.py OUT.png SCALE BG(hex) file1 file2 ...   (SCALE 0.5 = shown size)"""
import sys
from PIL import Image, ImageDraw

out, scale, bg = sys.argv[1], float(sys.argv[2]), sys.argv[3]
files = sys.argv[4:]
ims = []
for f in files:
    im = Image.open(f).convert("RGBA")
    if scale != 1:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.LANCZOS)
    ims.append((f.replace("\\", "/").split("/")[-1], im))
pad = 16
W = 1800
rows, row, x, rh = [], [], pad, 0
for n, im in ims:
    if x + im.width + pad > W and row:
        rows.append((row, rh))
        row, x, rh = [], pad, 0
    row.append((n, im, x))
    x += im.width + pad
    rh = max(rh, im.height + 18)
if row:
    rows.append((row, rh))
H = sum(r[1] + pad for r in rows) + pad
sheet = Image.new("RGBA", (W, H), bg)
d = ImageDraw.Draw(sheet)
y = pad
for row, rh in rows:
    for n, im, x in row:
        sheet.alpha_composite(im, (x, y + 16))
        d.text((x, y), f"{n} {im.width}x{im.height}", fill=(200, 190, 170, 255))
    y += rh + pad
sheet.convert("RGB").save(out)
print(out, sheet.size)
