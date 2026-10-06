"""The backdrop layers laid over a page shot (as the code would: grain tiled at half, edges stretched)."""
import sys

from PIL import Image

shot, grain, edges, out = sys.argv[1:5]
base = Image.open(shot).convert("RGBA")
W, H = base.size
g = Image.open(grain).convert("RGBA")
g = g.resize((g.width // 2, g.height // 2), Image.LANCZOS)
tile = Image.new("RGBA", (W, H), (0, 0, 0, 0))
for y in range(0, H, g.height):
    for x in range(0, W, g.width):
        tile.alpha_composite(g, (x, y))
e = Image.open(edges).convert("RGBA").resize((W, H), Image.LANCZOS)
base.alpha_composite(e)
base.alpha_composite(tile)
base.convert("RGB").save(out)
print(out)
