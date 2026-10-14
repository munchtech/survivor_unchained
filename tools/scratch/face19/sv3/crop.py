"""crop.py OUT x0,y0,x1,y1 CELLS dir/sheet [dir/sheet ...]: 1:1 crops of those cells (same box in each), one row per sheet."""
import sys
from PIL import Image, ImageDraw
F = "C:/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-survivorsunchained/91211d34-e079-4956-a2a0-7b52c04594a8/scratchpad/f19/"
Z = 1
if sys.argv[1].startswith("-z"): Z = int(sys.argv[1][2:]); sys.argv.pop(1)
out = sys.argv[1]; b = [int(v) for v in sys.argv[2].split(",")]; cells = [int(c) for c in sys.argv[3].split(",")]; sheets = sys.argv[4:]
w, h = b[2] - b[0], b[3] - b[1]
o = Image.new("RGB", (w * len(cells), h * len(sheets)))
for r, sh in enumerate(sheets):
    im = Image.open(F + sh + ".png")
    for k, c in enumerate(cells):
        o.paste(im.crop((c * 400 + b[0], b[1], c * 400 + b[2], b[3])), (k * w, r * h))
        ImageDraw.Draw(o).text((k * w + 2, r * h + 2), "%s c%d" % (sh, c), fill="yellow")
o = o.resize((o.width * Z, o.height * Z), Image.NEAREST) if Z > 1 else o
o.save(F + "s3/" + out); print(o.size)
