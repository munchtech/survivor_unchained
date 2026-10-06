"""Contact sheet of frames from play.

    python sheet.py OUT.png COLS WIDTH [--crop W,H[,DX,DY]] [--label TEXT] files-or-globs...

Each frame is cropped round the middle of the picture (where the survivor
stands; DX, DY shift the crop), scaled to WIDTH and labelled with its file
name (or TEXT and its index)."""
import glob
import os
import sys

from PIL import Image, ImageDraw, ImageFont

args = sys.argv[1:]
out, cols, width = args[0], int(args[1]), int(args[2])
rest = args[3:]
crop = None
label = None
files = []
i = 0
while i < len(rest):
    a = rest[i]
    if a == "--crop":
        crop = [int(v) for v in rest[i + 1].split(",")]
        i += 2
        continue
    if a == "--label":
        label = rest[i + 1]
        i += 2
        continue
    files += sorted(glob.glob(a)) if any(c in a for c in "*?") else [a]
    i += 1
try:
    font = ImageFont.truetype("arial.ttf", 16)
except OSError:
    font = ImageFont.load_default()
ims = []
for k, f in enumerate(files):
    im = Image.open(f).convert("RGB")
    if crop:
        w, h = crop[0], crop[1]
        dx, dy = (crop[2], crop[3]) if len(crop) > 3 else (0, 0)
        cx, cy = im.width // 2 + dx, im.height // 2 + dy
        im = im.crop((cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2))
    h = int(im.height * width / im.width)
    im = im.resize((width, h), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, width, 20], fill=(0, 0, 0))
    d.text((4, 2), f"{label} {k}" if label else os.path.basename(f), fill=(255, 230, 120), font=font)
    ims.append(im)
rows = (len(ims) + cols - 1) // cols
h = max(im.height for im in ims)
sheet = Image.new("RGB", (cols * width, rows * h), (16, 16, 16))
for k, im in enumerate(ims):
    sheet.paste(im, ((k % cols) * width, (k // cols) * h))
sheet.save(out)
print(out, sheet.size)
