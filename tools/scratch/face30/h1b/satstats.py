"""paint saturation (own, and mean of all faces) at the patch's and the ear's pixels of the probe frames"""
import os, sys, glob
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uvdecode import uv_at, SH
S = 1024
HT = os.path.join(SH, "..", "art", "people", "head_tex")
def satimg(f):
    a = np.asarray(Image.open(f).convert("RGB").resize((S, S), Image.BOX)).astype(float) / 255
    return (a.max(2) - a.min(2)) / np.maximum(a.max(2), 1e-3)
own = satimg(os.path.join(HT, "heroine_head.jpg"))
allm = np.mean([satimg(f) for f in glob.glob(os.path.join(HT, "heroine_head*.jpg"))], 0)
for pre, box in (("h1d_own_pixie_t180", (900, 290, 1030, 400)), ("h1d_own_braid_t315", (960, 290, 1090, 400))):
    x0, y0, x1, y1 = box
    uv = uv_at(pre)[y0:y1, x0:x1]
    sh = np.asarray(Image.open(os.path.join(SH, pre + "_nohair.png")).convert("RGB")).astype(float)[y0:y1, x0:x1] / 255
    ok = ~np.isnan(uv[..., 0])
    s = (sh.max(2) - sh.min(2)) / np.maximum(sh.max(2), 1e-3); l = sh @ [0.299, 0.587, 0.114]
    r = np.clip((np.nan_to_num(uv[..., 1]) * S).astype(int), 0, S - 1); c = np.clip((np.nan_to_num(uv[..., 0]) * S).astype(int), 0, S - 1)
    for name, m in (("patch", ok & (s < 0.2) & (l > 0.45)), ("ear", ok & (s > 0.33) & (l > 0.5))):
        print(pre, name, m.sum(), "own sat pct 5/50/95", np.percentile(own[r[m], c[m]], [5, 50, 95]).round(2), "mean-of-faces", np.percentile(allm[r[m], c[m]], [5, 50, 95]).round(2))
