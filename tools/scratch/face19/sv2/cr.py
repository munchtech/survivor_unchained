"""cr.py OUT DIR SHEETS CELL:x0,y0,x1,y1 ...: 1:1 crops, one row per sheet."""
import sys
from PIL import Image, ImageDraw
S = "C:/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-survivorsunchained/91211d34-e079-4956-a2a0-7b52c04594a8/scratchpad/"
out, d, sheets = sys.argv[1], sys.argv[2], sys.argv[3].split(",")
cells = [(int(a.split(":")[0]), [int(v) for v in a.split(":")[1].split(",")]) for a in sys.argv[4:]]
W = sum(b[2] - b[0] for _, b in cells); H = sum(cells[0][1][3] - cells[0][1][1] for _ in sheets)
o = Image.new("RGB", (W, H)); y = 0
for sh in sheets:
    im = Image.open(S + d + "/" + sh + ".png"); x = 0
    for c, b in cells:
        cr = im.crop((c * 400 + b[0], b[1], c * 400 + b[2], b[3])); o.paste(cr, (x, y))
        ImageDraw.Draw(o).text((x + 2, y + 2), "%s c%d" % (sh, c), fill="yellow"); x += b[2] - b[0]
    y += cells[0][1][3] - cells[0][1][1]
o.save(S + "s2/" + out); print(o.size)
