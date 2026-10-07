"""Crops of her from runs of frames, side by side, and numbers for each run.
    python crops.py her OUT.png SCALE TAG [TAG ...]   her head and body, frames 2..4 of each tag (rows)
    python crops.py shimmer TAG [TAG ...]             still camera: temporal noise of the world (her masked)
    python crops.py sharp TAG [TAG ...]               her crop's sharpness (mean gradient) over the frames
The pictures are in the worktree's godot/.shots; her place in each is in .shots/her_at.txt."""
import os
import re
import sys

import numpy as np
from PIL import Image, ImageDraw

SHOTS = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a20bdef993e00f26b\godot\.shots"
AT = {}
for line in open(os.path.join(SHOTS, "her_at.txt"), encoding="utf-8"):
    m = re.match(r"saved (.*?\.png) at [\d.]+s(?: her (-?\d+) (-?\d+))?", line.strip())
    if m and m.group(2):
        AT[os.path.basename(m.group(1))] = (int(m.group(2)), int(m.group(3)))


def her_at(f, a):
    """Her place in picture f (array a): recorded in the viewport's 1920x1080, scaled to the picture."""
    p = AT.get(f)
    if p is None:
        return (a.shape[1] // 2, a.shape[0] // 2)
    return (round(p[0] * a.shape[1] / 1920), round(p[1] * a.shape[0] / 1080))


def frames(tag):
    fs = sorted(f for f in os.listdir(SHOTS) if re.fullmatch(re.escape(tag) + r"_\d\d\.png", f))
    return fs


def load(f):
    return np.asarray(Image.open(os.path.join(SHOTS, f)).convert("RGB")).astype(np.float32)


def crop(a, c, hw, hh):
    x, y = c
    h, w, _ = a.shape
    x0, y0 = max(0, x - hw), max(0, y - hh)
    return a[y0:min(h, y0 + 2 * hh), x0:min(w, x0 + 2 * hw)]


def her(out, scale, tags, picks=(2, 3, 4)):
    rows = []
    for t in tags:
        fs = frames(t)
        a0 = load(fs[0])
        H = a0.shape[0]
        # Her figure is about a ninth of the screen high at the game camera.
        hh, hw = int(H * 0.085), int(H * 0.06)
        row = []
        for i in picks:
            f = fs[min(i, len(fs) - 1)]
            c = her_at(f, a0)
            c = (c[0], c[1] - int(H * 0.01))
            x = crop(load(f), c, hw, hh).astype(np.uint8)
            im = Image.fromarray(x).resize((x.shape[1] * scale, x.shape[0] * scale), Image.NEAREST)
            row.append(im)
        rows.append((t, row))
    W = sum(im.size[0] for im in rows[0][1]) + 6 * (len(rows[0][1]) - 1)
    Hh = rows[0][1][0].size[1]
    canvas = Image.new("RGB", (W + 200, (Hh + 6) * len(rows)), (20, 20, 20))
    d = ImageDraw.Draw(canvas)
    for r, (t, row) in enumerate(rows):
        x = 200
        d.text((8, r * (Hh + 6) + 8), t, fill=(230, 230, 230))
        for im in row:
            canvas.paste(im, (x, r * (Hh + 6)))
            x += im.size[0] + 6
    canvas.save(out)
    print(out, canvas.size)


def grad(a):
    g = a.mean(axis=2)
    return np.abs(np.diff(g, axis=0))[:, :-1] + np.abs(np.diff(g, axis=1))[:-1, :]


def sharp(tags):
    for t in tags:
        fs = frames(t)
        vals = []
        for f in fs:
            a = load(f)
            H = a.shape[0]
            c = her_at(f, a)
            x = crop(a, (c[0], c[1] - int(H * 0.01)), int(H * 0.04), int(H * 0.07))
            vals.append(grad(x).mean())
        print(f"{t:18s} her sharpness (mean gradient) {np.mean(vals):6.2f}  (frames {len(fs)}: {' '.join(f'{v:.1f}' for v in vals)})")


def shimmer(tags):
    for t in tags:
        fs = frames(t)
        st = np.stack([load(f).mean(axis=2) for f in fs])
        H, W = st.shape[1:]
        m = np.ones((H, W), bool)
        # The interface's bands and her (and her shadow) out of it.
        m[: int(H * 0.12)] = False
        m[int(H * 0.8):] = False
        c = her_at(fs[0], st[0][..., None])
        m[max(0, c[1] - int(H * 0.15)):c[1] + int(H * 0.12), max(0, c[0] - int(H * 0.1)):c[0] + int(H * 0.1)] = False
        d = np.abs(np.diff(st, axis=0))
        mean = d[:, m].mean()
        hot = (d[:, m] > 12).mean() * 100
        print(f"{t:18s} frame-to-frame change: mean {mean:5.2f}, pixels over 12/255: {hot:5.2f}%")


if __name__ == "__main__":
    what = sys.argv[1]
    if what == "her":
        her(sys.argv[2], int(sys.argv[3]), sys.argv[4:])
    elif what == "sharp":
        sharp(sys.argv[2:])
    elif what == "shimmer":
        shimmer(sys.argv[2:])
