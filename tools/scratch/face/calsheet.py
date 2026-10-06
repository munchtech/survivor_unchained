"""calsheet.py <cal dir> <group prefix> <out.jpg> : rows of sliders: -2 -1 base +1 +2 (front), -2 +2 (profile)."""
import glob
import os
import sys

from PIL import Image, ImageDraw

d, pre, out = sys.argv[1:4]
names = sorted({os.path.basename(p).rsplit("_", 2)[0] for p in glob.glob(os.path.join(d, pre + "*_0.png"))})
CW, CH = 170, 210
FB, SB = (230, 150, 794, 846), (180, 150, 744, 846)


def cell(path, box):
    if not os.path.exists(path):
        return Image.new("RGB", (CW, CH))
    return Image.open(path).convert("RGB").crop(box).resize((CW, CH), Image.LANCZOS)


rows = []
for n in names:
    cells = [cell(os.path.join(d, f"{n}_{k}_0.png"), FB) for k in ("m2", "m1")]
    cells.append(cell(os.path.join(d, "base_0.png"), FB))
    cells += [cell(os.path.join(d, f"{n}_{k}_0.png"), FB) for k in ("p1", "p2")]
    cells += [cell(os.path.join(d, f"{n}_{k}_90.png"), SB) for k in ("m2", "p2")]
    row = Image.new("RGB", (CW * 7, CH + 16), (14, 14, 14))
    for i, c in enumerate(cells):
        row.paste(c, (i * CW, 16))
    ImageDraw.Draw(row).text((4, 2), n.split("_", 1)[1] + "   -2 | -1 | base | +1 | +2 || side -2 | side +2", fill=(240, 220, 180))
    rows.append(row)
s = Image.new("RGB", (CW * 7, (CH + 16) * len(rows)))
for i, r in enumerate(rows):
    s.paste(r, (0, i * (CH + 16)))
s.save(out, quality=88)
print(s.size)
