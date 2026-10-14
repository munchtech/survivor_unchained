"""cells.py OUT CELLS [-b x0,y0,x1,y1] [-z N] sheet [sheet ...]: cells (k: column k%8, row k//8 of an every-frame sheet of
400 px cells) side by side, one row per sheet, labelled; into A/s11. Sheets are paths under A (f19), no .png."""
import sys, os
from PIL import Image, ImageDraw
F = "C:/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-survivorsunchained/91211d34-e079-4956-a2a0-7b52c04594a8/scratchpad/f19/"
a = sys.argv[1:]; out = a.pop(0); cells = [int(c) for c in a.pop(0).split(",")]; b = [0, 0, 400, 400]; Z = 1
while a and a[0].startswith("-"):
    f = a.pop(0)
    if f == "-b": b = [int(v) for v in a.pop(0).split(",")]
    if f == "-z": Z = int(a.pop(0))
w, h = b[2] - b[0], b[3] - b[1]
o = Image.new("RGB", (w * len(cells), h * len(a)))
for r, sh in enumerate(a):
    im = Image.open(F + sh + ".png")
    for k, c in enumerate(cells):
        x0, y0 = (c % 8) * 400, (c // 8) * 400
        o.paste(im.crop((x0 + b[0], y0 + b[1], x0 + b[2], y0 + b[3])), (k * w, r * h))
if Z > 1: o = o.resize((o.width * Z, o.height * Z), Image.LANCZOS)
d = ImageDraw.Draw(o)
for r, sh in enumerate(a):
    for k, c in enumerate(cells): d.text((k * w * Z + 3, r * h * Z + 3), "%s k%d" % (sh.split("/")[-1], c), fill="yellow")
os.makedirs(F + "s11", exist_ok=True); o.save(F + "s11/" + out); print(F + "s11/" + out, o.size)
