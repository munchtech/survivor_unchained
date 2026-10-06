"""UI art's contact sheet: python uiart_sheet.py OUT SIZE DIR name,name,...  (icons on a dark slot)."""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

out, size, d, names = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4].split(",")
cols = min(12, len(names))
rows = (len(names) + cols - 1) // cols
cell = size + 16
sheet = Image.new("RGB", (cols * cell, rows * (cell + 14)), "#0e0c10")
dr = ImageDraw.Draw(sheet)
try:
    font = ImageFont.truetype("arial.ttf", 11)
except OSError:
    font = ImageFont.load_default()
for i, n in enumerate(names):
    x, y = (i % cols) * cell, (i // cols) * (cell + 14)
    dr.rectangle((x + 3, y + 3, x + cell - 3, y + cell - 3), fill="#1b1820")
    p = os.path.join(d, n + ".png")
    if not os.path.exists(p):
        p = os.path.join(sys.argv[5], n + ".png") if len(sys.argv) > 5 else p
    im = Image.open(p).convert("RGBA").resize((size, size), Image.LANCZOS)
    sheet.paste(im, (x + 8, y + 8), im)
    dr.text((x + 4, y + cell), n[:16], fill="#c8bca8", font=font)
sheet.save(out)
print(out)
