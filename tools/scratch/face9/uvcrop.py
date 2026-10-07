"""uvcrop.py OUT x0 y0 x1 y1 scale img ...: the same UV window (4096 texels) of several head paints side by side."""
import sys
from PIL import Image, ImageDraw
out = sys.argv[1]
x0, y0, x1, y1 = (int(v) for v in sys.argv[2:6])
sc = float(sys.argv[6])
tiles = []
for p in sys.argv[7:]:
    im = Image.open(p).convert('RGB')
    k = im.width / 4096
    t = im.crop((int(x0 * k), int(y0 * k), int(x1 * k), int(y1 * k)))
    t = t.resize((int((x1 - x0) * sc), int((y1 - y0) * sc)), Image.LANCZOS if sc < 1 else Image.NEAREST)
    ImageDraw.Draw(t).text((3, 1), p.replace('\\', '/').split('/')[-1], fill=(255, 255, 0))
    tiles.append(t)
W = sum(t.width for t in tiles) + 4 * (len(tiles) - 1)
s = Image.new('RGB', (W, tiles[0].height), (20, 20, 20))
x = 0
for t in tiles:
    s.paste(t, (x, 0))
    x += t.width + 4
s.save(out, quality=92)
print(out, s.size)
