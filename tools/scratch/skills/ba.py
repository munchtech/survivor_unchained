"""Before/after pairs at full resolution: python ba.py OUT.png BEFORE_TAG AFTER_TAG FRAME skill [skill...]

Each row: the same moment of a skill before and after, a 760x440 crop round
the survivor at full resolution (nothing scaled), labelled."""
import sys
from PIL import Image, ImageDraw, ImageFont

SHOTS = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a8bafe3cd8a229639\godot\.shots"
out, bt, at, frame = sys.argv[1:5]
skills = sys.argv[5:]
W, H = 760, 440
try:
    font = ImageFont.truetype("arial.ttf", 18)
except OSError:
    font = ImageFont.load_default()
sheet = Image.new("RGB", (W * 2 + 8, (H + 4) * len(skills)), (12, 12, 12))
for i, s in enumerate(skills):
    name, _, fr = s.partition(":")
    fr = fr or frame
    for j, tag in enumerate((bt, at)):
        im = Image.open(rf"{SHOTS}\{tag}_{name}_{fr}.png").convert("RGB")
        cx, cy = im.width // 2, im.height // 2 + 20
        im = im.crop((cx - W // 2, cy - H // 2, cx + W // 2, cy + H // 2))
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, W, 24], fill=(0, 0, 0))
        d.text((6, 3), f"{'BEFORE' if j == 0 else 'AFTER'}  {name}  frame {fr}", fill=(255, 225, 120), font=font)
        sheet.paste(im, (j * (W + 8), i * (H + 4)))
sheet.save(out)
print(out, sheet.size)
