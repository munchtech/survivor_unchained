"""Per-frame arm contact on her skin for one clip (motion.py's measure): worst depth (mm) per zone, and what it hits.
    python ../scratch/anim59_contact.py flare_long_cut [--outfit warden]    (from tools/anim)"""
import sys
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\anim-59\tools\anim")
import numpy as np
import motion
from skin import Body
import staged
if "--raw" in sys.argv:
    staged.set_from_argv(["--raw"])
name = sys.argv[1]
outfits = ("warden",) if "--outfit" in sys.argv else ()
m = motion.Measure(Body.heroine(jiggle=True, helpers=True), outfits)
mw = None
if outfits:
    mw = motion.Measure(Body.heroine(outfit=None, jiggle=True, helpers=True), ())
    mw.b.jiggle.amount, mw.b.jiggle.squash = 0.55, 0.0
    mw.cover = m.cover
res = motion.run_clip(m, mw, name, outfits)
parts = m.b.parts
cov_name = outfits[0] if outfits else "skin"
tag = "plate" if outfits and "plate" in res else "free"
for s in "lr":
    pts, along, _ = m.arm[s]
    for f, (dist, hit, brst, near) in enumerate(res[tag][s]):
        ok = np.isfinite(dist)
        if not ok.any():
            continue
        d = -dist.copy()
        if outfits:
            cov = m.cover[cov_name]
            d[ok] += cov[pts[ok]] + cov[np.maximum(near[ok], 0)]
        d[~ok] = -1
        zone = np.where(along < 0.35, 0, np.where(along < 1, 1, np.where(along < 2, 2, 3)))
        row = []
        for zi, zn in enumerate(("pit", "up", "fa", "hd")):
            mk = (zone == zi) & ok
            if mk.any() and d[mk].max() > 0.002:
                i = np.nonzero(mk)[0][d[mk].argmax()]
                row.append(f"{zn} {1000 * d[mk].max():4.0f} {parts[hit[i]] if hit[i] >= 0 else '-'}{'(br)' if brst[i] else ''}")
        if row:
            print(s, f"f{f:2d}", " | ".join(row))
