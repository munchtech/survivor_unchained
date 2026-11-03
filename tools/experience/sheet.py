"""python sheet.py OUT.jpg COLS file1 file2 ... : a contact sheet, tiles 1920/COLS wide, each labelled with its name."""
import sys, os
from PIL import Image, ImageDraw, ImageFont
out, cols, files = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
tw = 1920 // cols; th = tw * 9 // 16
rows = (len(files) + cols - 1) // cols
S = Image.new("RGB", (tw * cols, th * rows), (20, 20, 20))
d = ImageDraw.Draw(S)
try: font = ImageFont.truetype("arial.ttf", 18)
except Exception: font = ImageFont.load_default()
for i, f in enumerate(files):
    im = Image.open(f).convert("RGB").resize((tw, th), Image.LANCZOS)
    x, y = (i % cols) * tw, (i // cols) * th
    S.paste(im, (x, y))
    n = os.path.splitext(os.path.basename(f))[0]
    d.rectangle([x, y, x + 9 * len(n) + 8, y + 22], fill=(0, 0, 0))
    d.text((x + 4, y + 2), n, fill=(255, 255, 0), font=font)
S.save(out, quality=85)
print(out, S.size)
