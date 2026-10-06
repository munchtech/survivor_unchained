"""A run's frames at full resolution, every Kth: python strip.py OUT.png TAG_SKILL [K] [W,H] [N] [--shift DX,DY] [--from F]

Crops W x H round the survivor (nothing scaled), two to a row."""
import sys
from PIL import Image, ImageDraw, ImageFont
from shots import run

args = sys.argv[1:]
DX, DY, FIRST = 0, 20, 0
rest = []
i = 0
while i < len(args):
    if args[i] == "--shift": DX, DY = (int(v) for v in args[i + 1].split(",")); i += 2; continue
    if args[i] == "--from": FIRST = int(args[i + 1]); i += 2; continue
    rest.append(args[i]); i += 1
out, name = rest[0], rest[1]
k = int(rest[2]) if len(rest) > 2 else 4
W, H = (int(v) for v in (rest[3] if len(rest) > 3 else "640,400").split(","))
n = int(rest[4]) if len(rest) > 4 else 8
files = run(name)[FIRST::k][:n]
try:
    font = ImageFont.truetype("arial.ttf", 16)
except OSError:
    font = ImageFont.load_default()
rows = (len(files) + 1) // 2
sheet = Image.new("RGB", (W * 2 + 6, rows * (H + 4)), (12, 12, 12))
for i, f in enumerate(files):
    im = Image.open(f).convert("RGB")
    cx, cy = im.width // 2 + DX, im.height // 2 + DY
    im = im.crop((cx - W // 2, cy - H // 2, cx + W // 2, cy + H // 2))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 220, 20], fill=(0, 0, 0))
    d.text((4, 2), f[-6:-4] + "  " + name.split("_", 1)[-1], fill=(255, 225, 120), font=font)
    sheet.paste(im, ((i % 2) * (W + 6), (i // 2) * (H + 4)))
sheet.save(out)
print(out, sheet.size)
