"""python crops.py OUTNAME SCALE TAG:SHOT:x0,y0,x1,y1 ... : rows = given crops, cols = own saffron sunborn"""
import sys
from PIL import Image
SH = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\godot\.shots" + "\\"
OUT = r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\463a4243-9324-49b0-bda9-b9fb9a9d68b1\scratchpad\f30" + "\\"
name, s = sys.argv[1], float(sys.argv[2]); rows = []
for spec in sys.argv[3:]:
    tag, shot, box = spec.split(":"); box = tuple(int(v) for v in box.split(","))
    rows.append([Image.open(f"{SH}f30c{tag}_{f}_{shot}.png").convert("RGB").crop(box) for f in ("own", "saffron", "sunborn")])
W = max(sum(int(c.width * s) for c in r) for r in rows); H = sum(int(r[0].height * s) for r in rows)
m = Image.new("RGB", (W, H)); y = 0
for r in rows:
    x = 0
    for c in r: m.paste(c.resize((int(c.width * s), int(c.height * s))), (x, y)); x += int(c.width * s)
    y += int(r[0].height * s)
m.save(OUT + name + ".jpg", quality=90); print(m.size)
