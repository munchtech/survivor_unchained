"""A few frames of flipbooks side by side on black: python fbview.py OUT name1 name2 ... (frames 4, 12, 24, 40)."""
import json
import sys
from PIL import Image

FB = r"C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a560452c597415545/godot/art/fx/fb/"
out = sys.argv[1]
rows = []
for name in sys.argv[2:]:
    meta = json.load(open(FB + name + ".json"))
    im = Image.open(FB + name + ".png").convert("RGBA")
    g = meta["grid"]
    w = im.size[0] // g
    n = meta["frames"]
    picks = [int(n * k) for k in (0.06, 0.2, 0.4, 0.65)]
    row = Image.new("RGB", (192 * 4, 192), (0, 0, 0))
    for k, f in enumerate(picks):
        t = im.crop(((f % g) * w, (f // g) * w, (f % g + 1) * w, (f // g + 1) * w)).resize((192, 192))
        bg = Image.new("RGB", (192, 192), (0, 0, 0))
        bg.paste(t, mask=t.split()[3])
        row.paste(bg, (k * 192, 0))
    rows.append(row)
sheet = Image.new("RGB", (192 * 4, 192 * len(rows)))
for i, r in enumerate(rows):
    sheet.paste(r, (0, i * 192))
sheet.save(out)
print(out, sheet.size)
