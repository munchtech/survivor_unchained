"""All colour icons as a labelled grid at a given shown size, plus 17 px row."""
import sys, glob
from sp import *
from PIL import ImageFont

fam = sys.argv[1] if len(sys.argv) > 1 else "glyph_color"
size = int(sys.argv[2]) if len(sys.argv) > 2 else 48
files = sorted(glob.glob(os.path.join(UI, "icons", fam, "*.png")))
cols = 12
cw, ch = max(size, 64) + 30, size + 18 + 17 + 8
rows = (len(files) + cols - 1) // cols
out = Image.new("RGB", (cols * cw, rows * ch), (24, 20, 20))
d = ImageDraw.Draw(out)
try:
    font = ImageFont.truetype("arial.ttf", 10)
except Exception:
    font = None
for i, f in enumerate(files):
    im = Image.open(f).convert("RGBA")
    x, y = (i % cols) * cw + 4, (i // cols) * ch + 4
    a = im.resize((size, size), Image.LANCZOS)
    out.paste(a, (x, y), a)
    b = im.resize((17, 17), Image.LANCZOS)
    out.paste(b, (x + size + 4, y), b)
    d.text((x, y + size + 19), os.path.basename(f)[:-4], fill=(200, 190, 170), font=font)
out.save(os.path.join(V, f"icons_{fam}_{size}.png"))
print(len(files))
