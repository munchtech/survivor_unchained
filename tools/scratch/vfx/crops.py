"""Full-resolution crops of frames, side by side, labelled; nothing scaled.

    python crops.py OUT.png shot:x0,y0,x1,y1 [shot:x0,y0,x1,y1 ...]

`shot` is a frame's name in .shots (without .png), found by shots.py."""
import sys
from PIL import Image, ImageDraw
from shots import shot

out = sys.argv[1]
tiles = []
for it in sys.argv[2:]:
    name, box = it.rsplit(":", 1)
    x0, y0, x1, y1 = (int(v) for v in box.split(","))
    im = Image.open(shot(name + ".png")).convert("RGB").crop((x0, y0, x1, y1))
    ImageDraw.Draw(im).text((6, 4), name, fill=(255, 255, 0))
    tiles.append(im)
w = sum(t.width for t in tiles) + 4 * (len(tiles) - 1)
h = max(t.height for t in tiles)
sheet = Image.new("RGB", (w, h), (10, 10, 10))
x = 0
for t in tiles:
    sheet.paste(t, (x, 0))
    x += t.width + 4
sheet.save(out)
print(out, sheet.size)
