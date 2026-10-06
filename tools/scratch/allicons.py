import os
import sys

from PIL import Image, ImageDraw

d = sys.argv[1]
s = int(sys.argv[2])
out = sys.argv[3]
only = sys.argv[4:]
fs = sorted(f for f in os.listdir(d) if f.endswith('.png') and (not only or f[:-4] in only))
cols = 13 if s <= 72 else 8
rows = (len(fs) + cols - 1) // cols
W = cols * (s + 8)
H = rows * (s + 20)
img = Image.new('RGBA', (W, H), (20, 16, 12, 255))
dr = ImageDraw.Draw(img)
for i, f in enumerate(fs):
    x, y = (i % cols) * (s + 8), (i // cols) * (s + 20)
    im = Image.open(os.path.join(d, f)).convert('RGBA').resize((s, s), Image.LANCZOS)
    img.alpha_composite(im, (x, y))
    dr.text((x, y + s + 2), f[:-4][:14], fill=(200, 180, 150, 255))
img.convert('RGB').save(out)
print(out, len(fs))
