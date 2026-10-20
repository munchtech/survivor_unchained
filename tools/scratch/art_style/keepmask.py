"""python keepmask.py OUT.png [--at X,Y] [--grow PX] [--feather PX] [--close] MASK.png ...

Her keep mask from SAM 3's per-instance masks (white where she is): keeps the instance(s) that hold
the point --at (default the play camera's spot for her, the frame centre a little low), or with --close
the biggest instance; grows it by --grow px (3) and feathers it by --feather px (4). Prints her box.
"""
import sys
import numpy as np
from PIL import Image, ImageFilter

a = sys.argv[1:]; out = a.pop(0)
def opt(k, d):
    if k in a: i = a.index(k); v = a[i + 1]; del a[i:i + 2]; return v
    return d
at = opt("--at", None); grow = int(opt("--grow", "3")); feather = float(opt("--feather", "4"))
close = "--close" in a
if close: a.remove("--close")
ms = [np.asarray(Image.open(p).convert("L"), dtype=np.float32) / 255 for p in a]
h, w = ms[0].shape
x, y = (int(v) for v in at.split(",")) if at else (w // 2, int(h * 0.55))
if close:
    keep = max(ms, key=lambda m: m.sum())
else:
    hits = [m for m in ms if m[max(0, y - 6):y + 6, max(0, x - 6):x + 6].mean() > 0.3]
    if not hits:   # nearest centroid to the point
        def d(m):
            ys, xs = np.nonzero(m > 0.5)
            return 1e9 if len(xs) == 0 else (xs.mean() - x) ** 2 + (ys.mean() - y) ** 2
        hits = [min(ms, key=d)]
    keep = np.maximum.reduce(hits)
im = Image.fromarray((np.clip(keep, 0, 1) * 255).astype(np.uint8))
if grow > 0: im = im.filter(ImageFilter.MaxFilter(2 * grow + 1))
if feather > 0: im = im.filter(ImageFilter.GaussianBlur(feather))
im.save(out)
ys, xs = np.nonzero(np.asarray(im) > 127)
print(out, "box", (xs.min(), ys.min(), xs.max(), ys.max()) if len(xs) else None, "share %.4f" % (np.asarray(im).mean() / 255))
