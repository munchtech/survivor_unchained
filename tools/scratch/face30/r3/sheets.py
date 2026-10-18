"""Face 30 round 3: BEFORE (round 2: h1_*, s3_*) / AFTER (r3_*) sheets, 1:1 crops of native frames, each <= 1568 px wide
and <= 1.16 MP, named by face, style and turns.   python sheets.py <out dir>"""
import os, sys, glob
from PIL import Image, ImageDraw
SH = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\godot\.shots"
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
HEAD = (660, 30, 1160, 560)   # the Look's Hair camera: her head and shoulders
CU = (720, 40, 1200, 800)
NOTE = " (stale-ok: clips not merged)"


def tile(name, box, label):
    path = os.path.join(SH, name + ".png")
    if not os.path.exists(path):
        im = Image.new("RGB", (box[2] - box[0], box[3] - box[1]), (20, 20, 20)); label += " (none)"
    else:
        im = Image.open(path).convert("RGB").crop(box)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 8 + 6 * len(label), 16), fill=(0, 0, 0)); d.text((4, 3), label, fill=(255, 255, 0)); return im


def grid(name, rows, gap=6):
    w, h = rows[0][0].width, rows[0][0].height; cols = len(rows[0])
    W, H = cols * w + gap * (cols - 1), len(rows) * h + gap * (len(rows) - 1)
    assert W <= 1568 and W * H <= 1.16e6, (name, W, H)
    o = Image.new("RGB", (W, H), (40, 40, 40))
    for r, row in enumerate(rows):
        for c, t in enumerate(row): o.paste(t, (c * (w + gap), r * (h + gap)))
    o.save(os.path.join(OUT, name + ".png")); print(name, (W, H))


def frames(prefix):
    return sorted(os.path.basename(f)[:-4] for f in glob.glob(os.path.join(SH, prefix + "_[0-9][0-9].png")))


def pair(f, s, d, before, suffix=""):
    t = f"{d:03d}"
    return [tile(f"{before}_lk_{f}_{s}_t{t}{suffix}", HEAD, f"BEFORE {f} {s} turn {d}{suffix}"),
            tile(f"r3_lk_{f}_{s}_t{t}{suffix}", HEAD, f"AFTER {f} {s} turn {d}{suffix}")]


for f in ("own", "saffron", "sunborn"):
    for s in ("braid", "ponytail", "pixie"):
        for ds in ((0, 135), (180, 315)):
            grid(f"{f}_{s}_{ds[0]:03d}_{ds[1]:03d}", [pair(f, s, d, "h1") for d in ds])
for f, s in (("own", "braid"), ("own", "ponytail"), ("saffron", "ponytail")):
    grid(f"{f}_{s}_090_270", [pair(f, s, d, "s3") for d in (90, 270)])
for s in ("braid", "ponytail", "pixie"):
    grid(f"own_{s}_180_315_day", [pair("own", s, 180, "h1", "_day"), [tile(f"r3_lk_own_{s}_t315_day", HEAD, f"AFTER own {s} turn 315 day"),
                                                                     tile("x", HEAD, "(no round-2 315 by day)")]])
CUS = (("braid", "s3_cu_own_braid_across", "r3_cu_own_braid_across", "day"), ("ponytail", "s3_cu_own_ponytail_across", "r3_cu_own_ponytail_across", "day"),
       ("pixie", "h1_cu_own_pixie_across", "r3_cu_own_pixie_across", "day"), ("pixie", "h1_cu_own_pixie_across_night", "r3_cu_own_pixie_across_night", "night"))
for s, b, a, tm in CUS:
    bc, ac = frames(b), frames(a)
    for k in (5, 9):
        grid(f"cu_own_{s}_{tm}_{k:02d}", [[tile(bc[k] if k < len(bc) else "x", CU, f"BEFORE close-up {s} {tm} #{k}"),
                                           tile(ac[k] if k < len(ac) else "x", CU, f"AFTER close-up {s} {tm} #{k}")]])
sp, bp = frames("r3_spin_ponytail"), frames("s3_spin_ponytail")
for n, ks in enumerate(((3, 9), (15, 19))):
    grid(f"spin_own_ponytail_{n + 1}", [[tile(bp[k] if k < len(bp) else "x", HEAD, f"BEFORE spin 90/s #{k}"), tile(sp[k] if k < len(sp) else "x", HEAD, f"AFTER spin 90/s #{k}")] for k in ks])
print("NOTE: all frames shot with --stale-ok (animation 37's clip pack not merged here); BEFORE frames had the same clips.")
