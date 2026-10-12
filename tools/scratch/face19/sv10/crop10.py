"""crop10.py OUT x0,y0,x1,y1 CELLS [-zN] dir/sheet [dir/sheet ...]: crops of those cells (same box), one row per sheet, into A/s10."""
import sys, os
from PIL import Image, ImageDraw
F = "C:/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-survivorsunchained/91211d34-e079-4956-a2a0-7b52c04594a8/scratchpad/f19/"
args = sys.argv[1:]; Z = 1
if args[0].startswith("-z"): Z = int(args.pop(0)[2:])
out = args[0]; b = [int(v) for v in args[1].split(",")]; cells = [int(c) for c in args[2].split(",")]; sheets = args[3:]
w, h = b[2] - b[0], b[3] - b[1]
o = Image.new("RGB", (w * len(cells), h * len(sheets)))
for r, sh in enumerate(sheets):
    im = Image.open(F + sh + ".png")
    for k, c in enumerate(cells):
        o.paste(im.crop((c * 400 + b[0], b[1], c * 400 + b[2], b[3])), (k * w, r * h))
o = o.resize((o.width * Z, o.height * Z), Image.NEAREST) if Z > 1 else o
d = ImageDraw.Draw(o)
for r, sh in enumerate(sheets):
    for k, c in enumerate(cells): d.text((k * w * Z + 3, r * h * Z + 3), "%s c%d" % (sh, c), fill="yellow")
os.makedirs(F + "s10", exist_ok=True); o.save(F + "s10/" + out); print(F + "s10/" + out, o.size)
