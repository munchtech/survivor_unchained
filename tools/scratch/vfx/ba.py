"""Before/after pairs at full resolution: python ba.py OUT.png BEFORE_TAG AFTER_TAG FRAME skill[:frame[:afterframe]] ...

Each row: the same moment of a skill before and after, a W x H crop round
the survivor at full resolution (nothing scaled), labelled. --size W,H and
--shift DX,DY move the crop (to where the effect is)."""
import sys
from PIL import Image, ImageDraw, ImageFont
from shots import shot

args = sys.argv[1:]
W, H, DX, DY = 760, 440, 0, 20
rest = []
i = 0
while i < len(args):
    if args[i] == "--size": W, H = (int(v) for v in args[i + 1].split(",")); i += 2; continue
    if args[i] == "--shift": DX, DY = (int(v) for v in args[i + 1].split(",")); i += 2; continue
    rest.append(args[i]); i += 1
out, bt, at, frame = rest[:4]
skills = rest[4:]
try:
    font = ImageFont.truetype("arial.ttf", 18)
except OSError:
    font = ImageFont.load_default()
sheet = Image.new("RGB", (W * 2 + 8, (H + 4) * len(skills)), (12, 12, 12))
for i, s in enumerate(skills):
    parts = s.split(":")
    name = parts[0]
    frs = (parts[1] if len(parts) > 1 and parts[1] else frame, parts[2] if len(parts) > 2 else (parts[1] if len(parts) > 1 and parts[1] else frame))
    for j, tag in enumerate((bt, at)):
        fr = frs[j]
        im = Image.open(shot(f"{tag}_{name}_{fr}.png")).convert("RGB")
        cx, cy = im.width // 2 + DX, im.height // 2 + DY
        im = im.crop((cx - W // 2, cy - H // 2, cx + W // 2, cy + H // 2))
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, W, 24], fill=(0, 0, 0))
        d.text((6, 3), f"{'BEFORE' if j == 0 else 'AFTER'}  {name}  frame {fr}", fill=(255, 225, 120), font=font)
        sheet.paste(im, (j * (W + 8), i * (H + 4)))
sheet.save(out)
print(out, sheet.size)
