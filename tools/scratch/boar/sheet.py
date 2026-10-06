"""Tile pictures into a sheet: python sheet.py OUT.jpg COLS WIDTH files..."""
import sys
from PIL import Image, ImageDraw
out, cols, w = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
fs = sys.argv[4:]
ims = [Image.open(f).convert("RGB") for f in fs]
h = int(w * ims[0].height / ims[0].width)
sheet = Image.new("RGB", (w * cols, h * ((len(ims) + cols - 1) // cols)), (40, 40, 40))
d = ImageDraw.Draw(sheet)
for i, (f, im) in enumerate(zip(fs, ims)):
    x, y = (i % cols) * w, (i // cols) * h
    sheet.paste(im.resize((w, h)), (x, y))
    d.text((x + 6, y + 6), f.replace("\\", "/").split("/")[-1], fill=(255, 255, 0))
sheet.save(out, quality=90)
