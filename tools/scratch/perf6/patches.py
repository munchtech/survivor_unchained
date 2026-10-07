"""Patches of the same places from several shots, side by side, enlarged (nearest).
    python patches.py OUT.png SCALE "x0,y0,w,h[;x0,y0,w,h...]" SHOT [SHOT ...]
Regions are in 1080p pixels; a 1440p shot's are scaled by 4/3."""
import os
import sys

from PIL import Image, ImageDraw

SHOTS = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a20bdef993e00f26b\godot\.shots"
out, scale = sys.argv[1], int(sys.argv[2])
regions = [[int(v) for v in r.split(",")] for r in sys.argv[3].split(";")]
shots = sys.argv[4:]
rows = []
for s in shots:
    im = Image.open(os.path.join(SHOTS, s if s.endswith(".png") else s + ".png")).convert("RGB")
    k = im.height / 1080
    tiles = []
    for x, y, w, h in regions:
        c = im.crop((round(x * k), round(y * k), round((x + w) * k), round((y + h) * k)))
        # (Each tile at the same displayed size: a 1440p patch is shown at its own pixels, 4/3 larger.)
        tiles.append(c.resize((c.width * scale, c.height * scale), Image.NEAREST))
    rows.append((s, tiles))
W = 170 + max(sum(t.width for t in ts) + 6 * (len(ts) - 1) for _, ts in rows)
H = sum(max(t.height for t in ts) for _, ts in rows) + 6 * (len(rows) - 1)
canvas = Image.new("RGB", (W, H), (18, 18, 18))
d = ImageDraw.Draw(canvas)
y = 0
for name, ts in rows:
    d.text((6, y + 6), name, fill=(235, 235, 235))
    x = 170
    for t in ts:
        canvas.paste(t, (x, y))
        x += t.width + 6
    y += max(t.height for t in ts) + 6
canvas.save(out)
print(out, canvas.size)
