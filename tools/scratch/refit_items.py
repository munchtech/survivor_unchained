"""Refit item icons painted edge to edge to the set's fill (0.82 of the square), centred."""
import os
import sys

import numpy as np
from PIL import Image

D = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa9c11f1e40170a4d\godot\art\ui\icons\item"
for key in sys.argv[1:]:
    p = os.path.join(D, key + ".png")
    im = Image.open(p).convert("RGBA")
    size = im.width
    a = np.asarray(im)[..., 3]
    ys, xs = np.nonzero(a > 10)
    obj = im.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
    k = size * 0.82 / max(obj.size)
    # Premultiplied, so the shrink leaves no dark fringe.
    arr = np.asarray(obj, np.float32) / 255
    pm = np.dstack([arr[..., :3] * arr[..., 3:], arr[..., 3:]])
    pm_im = Image.fromarray((pm * 255 + 0.5).astype(np.uint8), "RGBA")
    nw, nh = max(1, round(obj.width * k)), max(1, round(obj.height * k))
    small = np.asarray(pm_im.resize((nw, nh), Image.LANCZOS), np.float32) / 255
    al = small[..., 3:]
    rgb = np.where(al > 1e-4, small[..., :3] / np.maximum(al, 1e-4), 0)
    out = Image.fromarray((np.clip(np.dstack([rgb, al]), 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA")
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    canvas.alpha_composite(out, ((size - nw) // 2, (size - nh) // 2))
    canvas.save(p)
    print(key, obj.size, "->", (nw, nh))
