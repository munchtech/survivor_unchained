"""Batch 1's crops and numbers, all at once (look once).
    python cut.py OUTDIR
Sheets (1:1 unless named x2): her running at 1440 and 1080 under each smoothing, her head x2,
the crowd, Godot's motion-vector view, the see-through (house, pines), the Look's face; and the
numbers: her sharpness, still-camera shimmer, hair noise at the Look."""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(__file__))
import crops as C  # noqa: E402

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
LABEL_W = 150


def sheet(name, rows, scale=1):
    """rows: [(label, [PIL images])] -> one sheet, labels on the left."""
    rows = [(l, ims) for l, ims in rows if ims]
    if not rows:
        print(name, "nothing")
        return
    cw = max(sum(im.width * scale for im in ims) + 4 * (len(ims) - 1) for _, ims in rows)
    rh = [max(im.height for im in ims) * scale for _, ims in rows]
    canvas = Image.new("RGB", (LABEL_W + cw, sum(rh) + 4 * (len(rows) - 1)), (18, 18, 18))
    d = ImageDraw.Draw(canvas)
    y = 0
    for (label, ims), h in zip(rows, rh):
        d.text((6, y + 6), label, fill=(235, 235, 235))
        x = LABEL_W
        for im in ims:
            im = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
            canvas.paste(im, (x, y))
            x += im.width + 4
        y += h + 4
    p = os.path.join(OUT, name)
    canvas.save(p)
    print(p, canvas.size)


def her_crop(f, hw, hh, up=0.01):
    a = C.load(f)
    H = a.shape[0]
    c = C.her_at(f, a)
    return Image.fromarray(C.crop(a, (c[0], c[1] - int(H * up)), hw, hh).astype(np.uint8))


def run_rows(tags, picks, fw, fh, up=0.01):
    rows = []
    for t in tags:
        fs = C.frames(t)
        if not fs:
            continue
        H = C.load(fs[0]).shape[0]
        rows.append((t, [her_crop(fs[min(i, len(fs) - 1)], int(H * fw), int(H * fh), up) for i in picks]))
    return rows


def single(tag):
    for f in (tag + ".png", tag + "_00.png"):
        if os.path.exists(os.path.join(C.SHOTS, f)):
            return f
    return None


# 1. Her running, 1:1, three consecutive frames; and her head at 2x.
R1440 = ["run_taa_old", "run_taa", "run_taa1", "run_smaa", "run_fsr2", "run_msaa"]
R1080 = ["r1080_taa_old", "r1080_taa", "r1080_smaa", "r1080_fsr2"]
sheet("her_1440.png", run_rows(R1440, (3, 4, 5), 0.07, 0.1))
sheet("her_1080.png", run_rows(R1080, (3, 4, 5), 0.07, 0.1))
sheet("head_1440_x2.png", run_rows(R1440, (3, 4), 0.03, 0.03, up=0.06), scale=2)
sheet("head_1080_x2.png", run_rows(R1080, (3, 4), 0.03, 0.03, up=0.06), scale=2)
# 2. The crowd round her (wide), and its motion vectors.
sheet("crowd_1440.png", run_rows(["crowd_taa", "crowd_smaa", "crowd_fsr2", "mv_crowd"], (2,), 0.33, 0.2))
# 3. Godot's motion-vector view round her.
rows = []
for t in ("mv_taa", "mv_taa_old"):
    f = single(t)
    if f:
        rows.append((t, [her_crop(f, 300, 260)]))
sheet("mv_her.png", rows)
# 4. The see-through: the house (one frame each), the pines (every sixth frame of thirty).
rows = []
for t in ("house_old", "house_taa", "house_smaa", "house_fsr2"):
    f = single(t)
    if f:
        rows.append((t, [her_crop(f, 420, 300, up=0.0)]))
sheet("house.png", rows)
sheet("trees.png", run_rows(["trees_old", "trees_taa", "trees_smaa", "trees_fsr2"], (4, 10, 16, 22, 28), 0.13, 0.14, up=0.0))
# 5. The Look: her face at 1:1 (the middle of the frame's upper half holds it), first frame.
rows = []
for t in ("look_taa", "look_taa1", "look_msaa", "look_smaa", "look_fsr2", "l1440_taa", "l1440_msaa", "l1440_fsr2"):
    fs = C.frames(t)
    if not fs:
        continue
    a = C.load(fs[0]).astype(np.uint8)
    H, W = a.shape[:2]
    rows.append((t, [Image.fromarray(a[int(H * 0.08):int(H * 0.62), int(W * 0.3):int(W * 0.7)])]))
sheet("look_faces.png", rows)

# Numbers.
print("\n-- her sharpness (mean gradient of her crop; higher is crisper)")
C.sharp(R1440 + R1080)
print("\n-- still camera, frame to frame (her masked out)")
C.shimmer(["idle_taa", "idle_taa1", "idle_smaa", "idle_fsr2", "idle_msaa"])
print("\n-- the Look: frame-to-frame change over its three frames (hair noise and her breath)")
for t in ("look_taa", "look_taa1", "look_msaa", "look_smaa", "look_fsr2", "l1440_taa", "l1440_msaa", "l1440_fsr2"):
    fs = C.frames(t)
    if len(fs) < 2:
        continue
    st = np.stack([C.load(f).mean(axis=2) for f in fs])
    H, W = st.shape[1:]
    d = np.abs(np.diff(st[:, int(H * 0.05):int(H * 0.7), int(W * 0.3):int(W * 0.7)], axis=0))
    print(f"{t:14s} mean {d.mean():5.2f}  over 12/255: {(d > 12).mean() * 100:5.2f}%")
