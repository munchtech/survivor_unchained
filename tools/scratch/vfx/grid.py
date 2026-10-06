"""Full-resolution crops of named frames, side by side: python grid.py OUT.png COLS W,H[,DX,DY] file-or-glob...

Nothing is scaled: each crop is W x H round the middle of the picture (where she stands),
shifted by DX, DY, and labelled with its file name."""
import glob
import os
import sys
from PIL import Image, ImageDraw, ImageFont
from shots import DIRS

out, cols = sys.argv[1], int(sys.argv[2])
spec = [int(v) for v in sys.argv[3].split(",")]
W, H = spec[0], spec[1]
DX, DY = (spec[2], spec[3]) if len(spec) > 3 else (0, 20)
files = []
for a in sys.argv[4:]:
    found = []
    for d in DIRS:
        found = sorted(glob.glob(os.path.join(d, a)))
        if found:
            break
    files += found or sorted(glob.glob(a))
try:
    font = ImageFont.truetype("arial.ttf", 16)
except OSError:
    font = ImageFont.load_default()
rows = (len(files) + cols - 1) // cols
sheet = Image.new("RGB", (cols * (W + 6) - 6, rows * (H + 4) - 4), (12, 12, 12))
for i, f in enumerate(files):
    im = Image.open(f).convert("RGB")
    cx, cy = im.width // 2 + DX, im.height // 2 + DY
    im = im.crop((cx - W // 2, cy - H // 2, cx + W // 2, cy + H // 2))
    d = ImageDraw.Draw(im)
    label = os.path.basename(f)[:-4]
    d.rectangle([0, 0, 8 + 8 * len(label), 20], fill=(0, 0, 0))
    d.text((4, 2), label, fill=(255, 225, 120), font=font)
    sheet.paste(im, ((i % cols) * (W + 6), (i // cols) * (H + 4)))
sheet.save(out)
print(out, sheet.size, len(files), "frames")
