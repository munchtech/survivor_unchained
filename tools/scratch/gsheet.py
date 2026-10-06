"""Images in a grid: gsheet.py OUT SIZE COLS file..."""
import os
import sys

from PIL import Image, ImageDraw

out, s, cols = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
fs = sys.argv[4:]
rows = (len(fs) + cols - 1) // cols
img = Image.new("RGB", (cols * (s + 4), rows * (s + 16)), (8, 8, 8))
d = ImageDraw.Draw(img)
for i, f in enumerate(fs):
    x, y = (i % cols) * (s + 4), (i // cols) * (s + 16)
    im = Image.open(f).convert("RGBA").resize((s, s), Image.LANCZOS)
    b = Image.new("RGBA", (s, s), (20, 16, 12, 255))
    b.alpha_composite(im)
    img.paste(b.convert("RGB"), (x, y))
    d.text((x + 2, y + s + 2), os.path.basename(f)[:40], fill=(255, 220, 160))
img.save(out)
print(out)
