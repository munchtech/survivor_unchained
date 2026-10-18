"""Face 30 H1/H8: before (S1, a_*) / after (h1_*) sheets, 1:1 crops of native frames, each <= 1568 px wide, <= 1.16 MP.
    python h1_sheets.py <out dir>"""
import os, sys
from PIL import Image, ImageDraw
SH = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\godot\.shots"
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
def tile(name, box, label):
    im = Image.open(os.path.join(SH, name + ".png")).convert("RGB").crop(box); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 8 + 7 * len(label), 16), fill=(0, 0, 0)); d.text((4, 3), label, fill=(255, 255, 0)); return im
def grid(name, rows, gap=6):
    w, h = rows[0][0].width, rows[0][0].height; cols = len(rows[0])
    W, H = cols * w + gap * (cols - 1), len(rows) * h + gap * (len(rows) - 1)
    assert W <= 1568 and W * H <= 1.16e6, (name, W, H)
    o = Image.new("RGB", (W, H), (40, 40, 40))
    for r, row in enumerate(rows):
        for c, t in enumerate(row): o.paste(t, (c * (w + gap), r * (h + gap)))
    o.save(os.path.join(OUT, name + ".png")); print(name, (W, H))
HEAD = (660, 30, 1160, 560)   # the Look's Hair camera: her head and shoulders
for s in ("braid", "ponytail", "pixie"):
    for f in ("own", "saffron", "sunborn"):
        for a, b in ((0, 135), (180, 315)):
            grid(f"{f}_{s}_{a:03d}", [[tile(f"a_lk_{f}_{s}_t{d:03d}", HEAD, f"BEFORE {f} {s} Look turn {d}"),
                                       tile(f"h1_lk_{f}_{s}_t{d:03d}", HEAD, f"AFTER {f} {s} Look turn {d}")] for d in (a, b)])
    grid(f"own_{s}_180_day", [[tile(f"a_lk_own_{s}_t180", HEAD, f"BEFORE own {s} turn 180 night"),
                               tile(f"h1_lk_own_{s}_t180", HEAD, f"AFTER night"),
                               tile(f"h1_lk_own_{s}_t180_day", HEAD, f"AFTER day")]])
CB = (720, 40, 1200, 800)
for k in (5, 9):
    grid(f"cu_pixie_{k:02d}", [[tile(f"a_cu_own_pixie_across_{k:02d}", CB, f"BEFORE close-up pixie #{k} day"),
                                tile(f"h1_cu_own_pixie_across_{k:02d}", CB, f"AFTER day #{k}"),
                                tile(f"h1_cu_own_pixie_across_night_{k:02d}", CB, f"AFTER night #{k}")]])
