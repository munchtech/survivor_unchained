"""Face 30 neck: python nk_sheet.py BEFORE_TAG AFTER_TAG OUT_DIR: 1:1 crops of her jaw and neck, BEFORE beside AFTER,
three faces x turns 0 and 45, one sheet by day and one by night (<= 1568 px wide, <= 1.16 MP)."""
import os, sys
from PIL import Image, ImageDraw
W = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
SH = os.path.join(W, "godot", ".shots")
B, A, OUT = sys.argv[1:4]; FACES = os.environ.get("FACES", "own,saffron,sunborn").split(","); os.makedirs(OUT, exist_ok=True)
CROP = {0: (900, 330, 1220, 580), 45: (880, 330, 1200, 580)}
cw, ch, lab, gap = 320, 250, 18, 10
for tm in ("day", "night"):
    cells = [(f, d) for f in FACES for d in (0, 45)]
    pw = 2 * cw + 4; cols = 2; rows = (len(cells) + 1) // 2
    sheet = Image.new("RGB", (cols * pw + (cols - 1) * gap, rows * (ch + lab) + (rows - 1) * gap), (24, 24, 24))
    dr = ImageDraw.Draw(sheet)
    for i, (f, d) in enumerate(cells):
        x0 = (i % cols) * (pw + gap); y0 = (i // cols) * (ch + lab + gap)
        for j, tag in enumerate((B, A)):
            im = Image.open(os.path.join(SH, f"nk_{tag}_{f}_t{d:03d}_{tm}.png")).convert("RGB").crop(CROP[d])
            sheet.paste(im, (x0 + j * (cw + 4), y0 + lab))
            dr.text((x0 + j * (cw + 4) + 4, y0 + 3), f"{'BEFORE' if j == 0 else 'AFTER'}  {f} t{d} {tm}", fill=(230, 230, 230))
    p = os.path.join(OUT, (f"neck_{tm}_{B}_vs_{A}.png" if len(FACES) > 1 else f"neck_{FACES[0]}_{tm}_{B}_vs_{A}.png")); sheet.save(p); print(p, sheet.size, sheet.size[0] * sheet.size[1] / 1e6)
