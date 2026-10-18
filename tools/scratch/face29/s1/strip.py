"""strip.py OUT box(x0,y0,x1,y1) file[:label] ... -> 1:1 crops side by side, labelled."""
import sys, os
from PIL import Image, ImageDraw
out = sys.argv[1]; box = tuple(int(v) for v in sys.argv[2].split(","))
tiles = []
for a in sys.argv[3:]:
    f, _, lab = a.partition("::")
    im = Image.open(f).convert("RGB").crop(box)
    lab = lab or os.path.basename(f)
    d = ImageDraw.Draw(im); d.rectangle((0, 0, 8 + 6 * len(lab), 14), fill=(0, 0, 0)); d.text((3, 2), lab, fill=(255, 255, 0))
    tiles.append(im)
W = sum(t.width for t in tiles) + 4 * (len(tiles) - 1); H = max(t.height for t in tiles)
o = Image.new("RGB", (W, H), (40, 40, 40)); x = 0
for t in tiles: o.paste(t, (x, 0)); x += t.width + 4
o.save(out); print(out, o.size, "%.2f MP" % (W * H / 1e6))
