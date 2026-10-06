"""A run's frames at full resolution, every Kth: python strip.py OUT.png TAG_SKILL [K] [W,H] [N]

Crops W x H round the survivor (nothing scaled), two to a row."""
import glob
import sys
from PIL import Image, ImageDraw, ImageFont

SHOTS = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a8bafe3cd8a229639\godot\.shots"
out, run = sys.argv[1], sys.argv[2]
k = int(sys.argv[3]) if len(sys.argv) > 3 else 4
W, H = (int(v) for v in (sys.argv[4] if len(sys.argv) > 4 else "640,400").split(","))
n = int(sys.argv[5]) if len(sys.argv) > 5 else 8
files = sorted(glob.glob(rf"{SHOTS}\{run}_[0-9][0-9].png"))[::k][:n]
try:
    font = ImageFont.truetype("arial.ttf", 16)
except OSError:
    font = ImageFont.load_default()
rows = (len(files) + 1) // 2
sheet = Image.new("RGB", (W * 2 + 6, rows * (H + 4)), (12, 12, 12))
for i, f in enumerate(files):
    im = Image.open(f).convert("RGB")
    cx, cy = im.width // 2, im.height // 2 + 20
    im = im.crop((cx - W // 2, cy - H // 2, cx + W // 2, cy + H // 2))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 160, 20], fill=(0, 0, 0))
    d.text((4, 2), f[-6:-4] + "  " + run.split("_", 1)[1], fill=(255, 225, 120), font=font)
    sheet.paste(im, ((i % 2) * (W + 6), (i // 2) * (H + 4)))
sheet.save(out)
print(out, sheet.size)
