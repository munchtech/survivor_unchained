"""Face 30 S3: before (S1's a_* frames) / after (s3_*) sheets, 1:1 crops of native frames, each <= 1568 px wide and
<= 1.16 MP.   python s3_sheets.py <out dir>"""
import os, sys, glob
from PIL import Image, ImageDraw
SH = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\godot\.shots"
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
HEAD = (660, 30, 1160, 560)   # the Look's Hair camera: her head and shoulders
CU = (720, 40, 1200, 800)


def tile(name, box, label):
    path = os.path.join(SH, name + ".png")
    if not os.path.exists(path):
        im = Image.new("RGB", (box[2] - box[0], box[3] - box[1]), (20, 20, 20)); label += " (none)"
    else:
        im = Image.open(path).convert("RGB").crop(box)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 8 + 7 * len(label), 16), fill=(0, 0, 0)); d.text((4, 3), label, fill=(255, 255, 0)); return im


def grid(name, rows, gap=6):
    w, h = rows[0][0].width, rows[0][0].height; cols = len(rows[0])
    W, H = cols * w + gap * (cols - 1), len(rows) * h + gap * (len(rows) - 1)
    assert W <= 1568 and W * H <= 1.16e6, (name, W, H)
    o = Image.new("RGB", (W, H), (40, 40, 40))
    for r, row in enumerate(rows):
        for c, t in enumerate(row): o.paste(t, (c * (w + gap), r * (h + gap)))
    o.save(os.path.join(OUT, name + ".png")); print(name, (W, H))


def frames(prefix):
    return sorted(os.path.basename(f)[:-4] for f in glob.glob(os.path.join(SH, prefix + "_*.png")))


for s in ("braid", "ponytail"):
    for pair in ((0, 90), (180, 270), (315,)):
        grid(f"own_{s}_" + "_".join(f"{d:03d}" for d in pair),
             [[tile(f"a_lk_own_{s}_t{d:03d}", HEAD, f"BEFORE own {s} Look turn {d}"), tile(f"s3_lk_own_{s}_t{d:03d}", HEAD, f"AFTER own {s} Look turn {d}")] for d in pair])
    for f in ("saffron", "sunborn"):
        grid(f"{f}_{s}_000_180", [[tile(f"a_lk_{f}_{s}_t{d:03d}", HEAD, f"BEFORE {f} {s} turn {d}"), tile(f"s3_lk_{f}_{s}_t{d:03d}", HEAD, f"AFTER {f} {s} turn {d}")] for d in (0, 180)])
        grid(f"{f}_{s}_090_270", [[tile(f"s3_lk_{f}_{s}_t{d:03d}", HEAD, f"AFTER {f} {s} turn {d}") for d in (90, 270)]])
    bc, ac = frames(f"a_cu_own_{s}_across"), frames(f"s3_cu_own_{s}_across")
    for k in (5, 9):
        grid(f"cu_{s}_{k:02d}", [[tile(bc[k] if k < len(bc) else "x", CU, f"BEFORE close-up {s} #{k}"), tile(ac[k] if k < len(ac) else "x", CU, f"AFTER close-up {s} #{k}")]])
    sp = frames(f"s3_spin_{s}")
    for n, ks in enumerate(((0, 3, 6, 9), (12, 15, 18, 19))):
        t = [tile(sp[k] if k < len(sp) else "x", HEAD, f"AFTER own {s} spin 90/s #{k} (0.1 s)") for k in ks]
        grid(f"spin_{s}_{n + 1}", [t[:2], t[2:]])
