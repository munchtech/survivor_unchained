"""Before and after, crops side by side: python ba.py OUT X0 Y0 X1 Y1 SCALE BEFORE AFTER [BEFORE AFTER ...]
(names in .shots; each pair is a row, labelled)."""
import sys, os
from PIL import Image, ImageDraw

SHOTS = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-af2c026d86e1b532b\godot\.shots"
HERE = os.path.dirname(os.path.abspath(__file__))
out = sys.argv[1]
x0, y0, x1, y1 = (int(v) for v in sys.argv[2:6])
scale = float(sys.argv[6])
names = sys.argv[7:]
rows = []
for i in range(0, len(names), 2):
    pair = []
    for n in names[i:i + 2]:
        im = Image.open(os.path.join(SHOTS, n + ".png")).convert("RGB").crop((x0, y0, x1, y1))
        im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, 260, 18], fill=(0, 0, 0))
        d.text((4, 3), n, fill=(255, 255, 0))
        pair.append(im)
    rows.append(pair)
w = sum(p.width for p in rows[0]); h = rows[0][0].height
sheet = Image.new("RGB", (w, h * len(rows)), (20, 20, 20))
for r, pair in enumerate(rows):
    x = 0
    for p in pair:
        sheet.paste(p, (x, r * h)); x += p.width
sheet.save(os.path.join(HERE, out))
print(out, sheet.size)
