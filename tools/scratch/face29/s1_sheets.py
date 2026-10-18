"""Face 29: before/after sheets for S1's round (H1 scalp wedge, H3 strands on the face), 1:1 crops of native frames,
each sheet <= 1568 px wide and <= 1.16 MP.   python s1_sheets.py <S1 before dir> <out dir>"""
import os, sys
from PIL import Image, ImageDraw
SH = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\godot\.shots"
BEF, OUT = sys.argv[1], sys.argv[2]; os.makedirs(OUT, exist_ok=True)
def tile(path, box, label):
    im = Image.open(path).convert("RGB").crop(box); d = ImageDraw.Draw(im)
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
    for a, b in ((0, 135), (180, 315)):
        grid(f"own_{s}_{a:03d}", [[tile(os.path.join(BEF, f"h_lk_{s}_t{d:03d}.png"), HEAD, f"BEFORE own {s} Look turn {d}"),
                                   tile(os.path.join(SH, f"a_lk_own_{s}_t{d:03d}.png"), HEAD, f"AFTER own {s} Look turn {d}")] for d in (a, b)])
        for f in ("saffron", "sunborn"):
            grid(f"{f}_{s}_{a:03d}", [[tile(os.path.join(SH, f"b_lk_{f}_{s}_t{d:03d}.png"), HEAD, f"BEFORE {f} {s} Look turn {d}"),
                                       tile(os.path.join(SH, f"a_lk_{f}_{s}_t{d:03d}.png"), HEAD, f"AFTER {f} {s} Look turn {d}")] for d in (a, b)])
    for k in (5, 9):
        grid(f"cu_{s}_{k:02d}", [[tile(os.path.join(BEF, f"r_cu_day_{s}_across_{k:02d}.png"), (720, 40, 1200, 800), f"BEFORE close-up {s} #{k}"),
                                  tile(os.path.join(SH, f"a_cu_own_{s}_across_{k:02d}.png"), (720, 40, 1200, 800), f"AFTER close-up {s} #{k}")]])
    grid(f"spin_{s}", [[tile(os.path.join(SH, f"a_lk_own_{s}_spin_{k:02d}.png"), HEAD, f"AFTER own {s} spinning #{k}") for k in (1, 3)],
                       [tile(os.path.join(SH, f"a_lk_own_{s}_spin_{k:02d}.png"), HEAD, f"AFTER own {s} spinning #{k}") for k in (5, 7)]])
