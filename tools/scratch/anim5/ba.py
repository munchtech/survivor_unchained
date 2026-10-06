"""Before and after, stacked with labels: python ba.py out.png "title" before.png after.png [width]"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw

out, title, a, b = sys.argv[1:5]
width = int(sys.argv[5]) if len(sys.argv) > 5 else 2000
sh = Path(__file__).parent / "sh"
ims = [Image.open(sh / a).convert("RGB"), Image.open(sh / b).convert("RGB")]
ims = [im.resize((width, int(im.height * width / im.width))) for im in ims]
bar = 22
H = sum(im.height for im in ims) + 2 * bar
canvas = Image.new("RGB", (width, H), (20, 20, 24))
d = ImageDraw.Draw(canvas)
y = 0
for label, im, col in (("BEFORE", ims[0], (240, 200, 90)), ("AFTER", ims[1], (120, 230, 140))):
    d.text((8, y + 5), f"{title}  {label}", fill=col)
    y += bar
    canvas.paste(im, (0, y))
    y += im.height
canvas.save(sh / out)
print(sh / out, canvas.size)
