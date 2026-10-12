"""crop.py SHOT x0 y0 x1 y1 scale OUT [SHOT2 ...]: crops (same box) side by side, scaled, with names."""
import sys, os
from PIL import Image, ImageDraw
S = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\godot\.shots"
a = sys.argv[1:]
x0, y0, x1, y1 = map(int, a[0:4]); sc = float(a[4]); out = a[5]; shots = a[6:]
tiles = []
for s in shots:
    p = s if os.path.exists(s) else os.path.join(S, s + ".png")
    im = Image.open(p).convert("RGB").crop((x0, y0, x1, y1))
    im = im.resize((int(im.width * sc), int(im.height * sc)), Image.LANCZOS if sc < 1 else Image.NEAREST)
    ImageDraw.Draw(im).text((4, 4), os.path.basename(s), fill=(255, 255, 0)); tiles.append(im)
W = sum(t.width for t in tiles) + 4 * (len(tiles) - 1); H = max(t.height for t in tiles)
sh = Image.new("RGB", (W, H)); x = 0
for t in tiles: sh.paste(t, (x, 0)); x += t.width + 4
sh.save(out, quality=92); print(out, sh.size)
