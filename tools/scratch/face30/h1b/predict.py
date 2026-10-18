"""predicted scalp tint (a heroine_shadow.png's green) at the probe frames' pale-patch and ear pixels.
    python predict.py <shadow.png> [<shadow.png> ...]"""
import os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uvdecode import uv_at, SH
S = 1024
for f in sys.argv[1:]:
    g = np.asarray(Image.open(f))[..., 1].astype(float) / 255
    for pre, box in (("h1d_own_pixie_t180", (900, 290, 1030, 400)), ("h1d_own_braid_t315", (960, 290, 1090, 400)), ("h1d_sunborn_pixie_t180", (900, 290, 1030, 400))):
        x0, y0, x1, y1 = box
        uv = uv_at(pre)[y0:y1, x0:x1]
        sh = np.asarray(Image.open(os.path.join(SH, pre + "_nohair.png" if os.path.exists(os.path.join(SH, pre + "_nohair.png")) else os.path.join(SH, pre + "_base.png"))).convert("RGB")).astype(float)[y0:y1, x0:x1] / 255
        ok = ~np.isnan(uv[..., 0])
        s = (sh.max(2) - sh.min(2)) / np.maximum(sh.max(2), 1e-3); l = sh @ [0.299, 0.587, 0.114]
        r = np.clip((np.nan_to_num(uv[..., 1]) * S).astype(int), 0, S - 1); c = np.clip((np.nan_to_num(uv[..., 0]) * S).astype(int), 0, S - 1)
        t = g[r, c]
        pale = ok & (s < 0.25) & (l > 0.4); ear = ok & (s > 0.4) & (l > 0.45) & (t < 2)
        print(os.path.basename(os.path.dirname(f)), pre, "pale %d px: tint<0.5 %d, mean %.2f | ear-coloured %d px: tint>0.3 %d" % (pale.sum(), (t[pale] < 0.5).sum(), t[pale].mean() if pale.any() else -1, ear.sum(), (t[ear] > 0.3).sum()))
