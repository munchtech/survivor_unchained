"""Zoom on spots of frames from play: python zoom.py OUT.png SCALE HALF name:x,y ...

Each spot is a square 2*HALF pixels across round (x, y) in the full 1920x1080 frame, scaled up
by SCALE (LANCZOS), side by side."""
import sys
from PIL import Image
from shots import shot

out, scale, half = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
tiles = []
for it in sys.argv[4:]:
    name, xy = it.split(":")
    x, y = (int(v) for v in xy.split(","))
    im = Image.open(shot(name if name.endswith(".png") else name + ".png")).convert("RGB")
    tiles.append(im.crop((x - half, y - half, x + half, y + half)).resize((half * 2 * scale, half * 2 * scale), Image.LANCZOS))
w = half * 2 * scale
sheet = Image.new("RGB", (len(tiles) * (w + 4) - 4, w), (10, 10, 10))
for i, t in enumerate(tiles):
    sheet.paste(t, (i * (w + 4), 0))
sheet.save(out)
print(out, sheet.size)
