"""Face 30 H1b acceptance: the patch's pixels (by the UV probe: her head's texels the round-2 mask left untinted and the new one tints, and no hair over them in the round-2 frame) against the hair round them (a 24 px ring, saturation > 0.8).
    python measure.py <old diag.npz> <new diag.npz> <frame prefix> [...]   e.g. h1b_lk_own_pixie_t180"""
import os, sys
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uvdecode import uv_at, SH
S = 1024
zo, zn = np.load(sys.argv[1]), np.load(sys.argv[2])
def img(z, vals):
    a = np.zeros((S, S)); a[z["rows"], z["cols"]] = vals; return a[::-1]
OLD, NEW = zo["sh"][::-1], zn["sh"][::-1]
SKIN = img(zn, zn["skin"] * zn["w"])
def rd(f): return np.asarray(Image.open(os.path.join(SH, f + ".png")).convert("RGB")).astype(float)
def hsv(c):
    mx, mn = c.max(-1), c.min(-1); s = (mx - mn) / np.maximum(mx, 1)
    return c @ [0.299, 0.587, 0.114], s
for pre in sys.argv[3:]:
    face, style, t = pre.split("_")[2:5]
    probe = f"h1d_{face}_{'pixie' if style == 'pixie' else style}_{t}"
    if not os.path.exists(os.path.join(SH, probe + "_uv10.png")):
        print(pre, "no probe"); continue
    uv = uv_at(probe); ok = ~np.isnan(uv[..., 0])
    r = np.clip((np.nan_to_num(uv[..., 1]) * S).astype(int), 0, S - 1); c = np.clip((np.nan_to_num(uv[..., 0]) * S).astype(int), 0, S - 1)
    before = rd(probe + "_base"); nohair = rd(probe + "_nohair") if os.path.exists(os.path.join(SH, probe + "_nohair.png")) else before
    bare = np.abs(before - nohair).sum(-1) < 12                          # (no hair over it)
    patch = ok & bare & (OLD[r, c] < 0.5) & (NEW[r, c] > 0.5)
    patch = ndimage.binary_opening(patch, iterations=1)
    lab, n = ndimage.label(patch); sz = ndimage.sum(patch, lab, range(1, n + 1))
    patch = np.isin(lab, 1 + np.where(sz >= 30)[0])                      # (the patch, not specks)
    ring = ndimage.binary_dilation(patch, iterations=24) & ~patch
    after = rd(pre)
    for nm, fr in (("before", before), ("after", after)):
        l, s = hsv(fr)
        hair = ring & (s > 0.8) & (l < 140)
        print(f"{pre} {nm}: patch {patch.sum()} px luma {l[patch].mean():.0f} (p90 {np.percentile(l[patch], 90):.0f}) sat {s[patch].mean():.2f}"
              f" | hair {hair.sum()} px luma {l[hair].mean():.0f} sat {s[hair].mean():.2f} | ratio {l[patch].mean() / l[hair].mean():.2f}")
    np.save(os.path.join(os.path.dirname(sys.argv[2]), pre + "_patch.npy"), patch)
