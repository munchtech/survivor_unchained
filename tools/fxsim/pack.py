"""Cut boom_sim.py's frames into a flipbook atlas (premultiplied RGBA, as flipbook.gdshader and flare_fb.gdshader
read it), or a preview strip over a ground colour.

    python tools/fxsim/pack.py atlas FRAMES_DIR OUT.png [--cols 8] [--cell 384] [--fps 24] [--first 1] [--last N]
    python tools/fxsim/pack.py preview FRAMES_DIR OUT.jpg [--every 4] [--cell 320] [--bg 0.05,0.05,0.06]

The atlas is refused (exit 2) when any frame's light reaches its border: the square of the quad would show.
"""
import glob
import json
import os
import sys

import numpy as np
from PIL import Image


def frames(d, first=1, last=None):
    fs = sorted(glob.glob(os.path.join(d, "f_[0-9][0-9][0-9].png")))
    fs = [f for f in fs if int(os.path.basename(f)[2:5]) >= first and (last is None or int(os.path.basename(f)[2:5]) <= last)]
    return fs


def load(f):
    """Straight-alpha PNG (8 or 16 bit) to premultiplied float RGBA."""
    im = Image.open(f)
    a = np.asarray(im, dtype=np.float32)
    a = a / (65535.0 if a.max() > 255.5 else 255.0)
    if a.shape[2] == 3:
        a = np.concatenate([a, np.ones_like(a[..., :1])], 2)
    a[..., :3] *= a[..., 3:4]
    return a


def edge_fade(a):
    h, w = a.shape[:2]
    y = np.minimum(np.arange(h), np.arange(h)[::-1]) / (h * 0.05)
    x = np.minimum(np.arange(w), np.arange(w)[::-1]) / (w * 0.05)
    m = np.clip(np.minimum(y[:, None], x[None, :]), 0, 1)
    return a * m[..., None]


def opt(argv, k, d, t=str):
    return t(argv[argv.index(k) + 1]) if k in argv else d


def main():
    mode, src, out = sys.argv[1:4]
    av = sys.argv[4:]
    if mode == "atlas":
        cols, cell, fps = opt(av, "--cols", 8, int), opt(av, "--cell", 384, int), opt(av, "--fps", 24.0, float)
        fs = frames(src, opt(av, "--first", 1, int), opt(av, "--last", None, int))
        rows = (len(fs) + cols - 1) // cols
        atlas = np.zeros((rows * cell, cols * cell, 4), np.float32)
        bad = []
        for i, f in enumerate(fs):
            a = load(f)
            b = 0.04
            h, w = a.shape[:2]
            ring = np.concatenate([a[: int(h * b)].reshape(-1, 4), a[-int(h * b):].reshape(-1, 4),
                                   a[:, : int(w * b)].reshape(-1, 4), a[:, -int(w * b):].reshape(-1, 4)])
            if ring[:, 3].max() > 0.06:
                bad.append((os.path.basename(f), float(ring[:, 3].max())))
            a = edge_fade(a)
            im = Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA").resize((cell, cell), Image.LANCZOS)
            r, c = divmod(i, cols)
            atlas[r * cell:(r + 1) * cell, c * cell:(c + 1) * cell] = np.asarray(im, np.float32) / 255.0
        if bad and "--force" not in av:
            print("REFUSED: light at the border in", bad[:6]); sys.exit(2)
        Image.fromarray((atlas * 255 + 0.5).astype(np.uint8), "RGBA").save(out)
        json.dump({"grid": cols, "rows": rows, "frames": len(fs), "fps": fps, "source": os.path.basename(src.rstrip("/\\"))},
                  open(os.path.splitext(out)[0] + ".json", "w"))
        print("ATLAS", out, atlas.shape, len(fs), "frames", "border warnings" if bad else "")
    else:
        every, cell = opt(av, "--every", 4, int), opt(av, "--cell", 320, int)
        bg = np.array([float(v) for v in opt(av, "--bg", "0.05,0.05,0.06").split(",")], np.float32)
        fs = frames(src)[::every]
        tiles = []
        for f in fs:
            a = load(f)
            c = a[..., :3] + bg * (1 - a[..., 3:4])
            tiles.append(Image.fromarray((np.clip(c, 0, 1) * 255).astype(np.uint8)).resize((cell, cell), Image.LANCZOS))
        cols = min(len(tiles), 6)
        rows = (len(tiles) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * cell, rows * cell))
        for i, t in enumerate(tiles):
            sheet.paste(t, ((i % cols) * cell, (i // cols) * cell))
        sheet.save(out, quality=88)
        print("PREVIEW", out, sheet.size, [os.path.basename(f) for f in fs])


main()
