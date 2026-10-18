"""Face 30 round 3, H1: patch-behind-the-ear luma over the hair round it (bar 1.10), as h1b/measure.py, for every style.
The probe (UV and no-hair frames) is per face and turn (hair hidden: any style's); BEFORE is the round-2 frame
(h1_lk_*, before the tint and cap fix); its hair decides which patch texels are bare. AFTER is r3_lk_*.
    python measure_h1.py <old diag.npz> <new diag.npz> [after prefix, default r3_lk]"""
import os, sys
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "h1b"))
from uvdecode import uv_at, SH
S = 1024
zo, zn = np.load(sys.argv[1]), np.load(sys.argv[2])
AFTER = sys.argv[3] if len(sys.argv) > 3 else "r3_lk"
OLD, NEW = zo["sh"][::-1], zn["sh"][::-1]
PROBE = {("own", 180): "h1d_own_pixie_t180", ("own", 315): "h1d_own_braid_t315",
         ("sunborn", 180): "h1d_sunborn_pixie_t180", ("sunborn", 315): "h1d_sunborn_pixie_t315"}
def rd(f): return np.asarray(Image.open(os.path.join(SH, f + ".png")).convert("RGB")).astype(float)
def has(f): return os.path.exists(os.path.join(SH, f + ".png"))
def hsv(c):
    mx, mn = c.max(-1), c.min(-1); return c @ [0.299, 0.587, 0.114], (mx - mn) / np.maximum(mx, 1)
for (face, t), probe in PROBE.items():
    if not has(probe + "_uv10"):
        print(face, t, "no probe"); continue
    uv = uv_at(probe); ok = ~np.isnan(uv[..., 0])
    r = np.clip((np.nan_to_num(uv[..., 1]) * S).astype(int), 0, S - 1); c = np.clip((np.nan_to_num(uv[..., 0]) * S).astype(int), 0, S - 1)
    nohair = rd(probe + "_nohair") if has(probe + "_nohair") and not os.environ.get("NOBARE") else None
    for style in ("braid", "ponytail", "pixie"):
        bname, aname = f"h1_lk_{face}_{style}_t{t:03d}", f"{AFTER}_{face}_{style}_t{t:03d}"
        if not (has(bname) and has(aname)):
            print(aname, "missing"); continue
        before, after = rd(bname), rd(aname)
        bare = np.abs(before - nohair).sum(-1) < 12 if nohair is not None else np.ones(before.shape[:2], bool)
        patch = ok & bare & (OLD[r, c] < 0.5) & (NEW[r, c] > 0.5)
        patch = ndimage.binary_opening(patch, iterations=1)
        lab, n = ndimage.label(patch); sz = ndimage.sum(patch, lab, range(1, n + 1))
        patch = np.isin(lab, 1 + np.where(sz >= 30)[0])
        if patch.sum() == 0:
            print(f"{aname}: no bare patch (hair over it in round 2)"); continue
        ring = ndimage.binary_dilation(patch, iterations=24) & ~patch
        out = []
        for nm, fr in (("before", before), ("after", after)):
            l, s = hsv(fr)
            hair = ring & (s > 0.8) & (l < 140)
            out.append(f"{nm} {l[patch].mean() / max(l[hair].mean(), 1):.2f}")
        l, s = hsv(after)
        print(f"{aname}: patch {patch.sum()} px{'' if nohair is not None else ' (no nohair probe)'} | ratio " + ", ".join(out) +
              f" | after patch luma {l[patch].mean():.0f} sat {s[patch].mean():.2f}")
