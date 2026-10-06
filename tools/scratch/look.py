"""Composite a UI PNG over a backdrop to judge it: python look.py in.png out.png [bg hex|image] [scale] [crop x0,y0,x1,y1]"""
import sys
import numpy as np
from PIL import Image

src = Image.open(sys.argv[1]).convert("RGBA")
out = sys.argv[2]
bg = sys.argv[3] if len(sys.argv) > 3 else "#1a1612"
scale = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
if len(sys.argv) > 5:
    x0, y0, x1, y1 = map(int, sys.argv[5].split(","))
    src = src.crop((x0, y0, x1, y1))
if bg.startswith("#"):
    b = Image.new("RGBA", src.size, bg)
else:
    b = Image.open(bg).convert("RGBA").resize(src.size)
b.alpha_composite(src)
if scale != 1.0:
    b = b.resize((int(b.width * scale), int(b.height * scale)), Image.LANCZOS)
b.convert("RGB").save(out)
