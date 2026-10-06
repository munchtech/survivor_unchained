"""Textures side by side on a ground-brown backdrop: python tex.py OUT.png SIZE file [file ...]"""
import sys
from PIL import Image

out, size, files = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
sheet = Image.new("RGB", (size * len(files), size), (60, 50, 40))
for i, f in enumerate(files):
    im = Image.open(f).convert("RGBA").resize((size, size), Image.LANCZOS)
    sheet.paste(im, (i * size, 0), im)
sheet.save(out)
print(out, sheet.size)
