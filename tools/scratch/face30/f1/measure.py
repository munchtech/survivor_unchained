"""python measure.py FACE TAG... : F1 numbers at c04a A5 (still 2) from godot/.shots/f30<TAG>_<FACE>_c04a_sa5_2.png,
with the teeth found in f30dbg_<FACE> (teeth emitted green). Prints: incisor band px per 8-px column over the teeth,
black (luma<12) blobs wider than 6 px inside the opening (corners = outer 10 px excluded), upper lip underside vs the
darkest row band of the lower lip's top."""
import sys, numpy as np
from PIL import Image
from scipy import ndimage
S = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\godot\.shots"
face, tags = sys.argv[1], sys.argv[2:]
d = np.asarray(Image.open(f"{S}/f30dbg_{face}_c04a_sa5_2.png").convert("RGB")).astype(int)
Y0, Y1, X0, X1 = 700, 840, 1000, 1300
D = d[Y0:Y1, X0:X1]; g = (D[..., 1] > 120) & (D[..., 1] > D[..., 0] + 25) & (D[..., 2] < 140); g = ndimage.binary_opening(g, iterations=1)
ys, xs = np.where(g); tx0, tx1 = xs.min(), xs.max(); top = ys.min()
for t in tags:
    a = np.asarray(Image.open(f"{S}/f30{t}_{face}_c04a_sa5_2.png").convert("RGB")).astype(float)[Y0:Y1, X0:X1]
    L = a @ [0.299, 0.587, 0.114]
    # the opening: dark (under 0.6 of the lips above it) or teeth, in the teeth's columns
    cols = range(tx0, tx1 + 1)
    tt = [g[:, x].nonzero()[0] for x in cols]
    band = [(c.max() - c.min() + 1) if len(c) else 0 for c in tt]
    prof = [int(np.mean(band[i:i + 8])) for i in range(0, len(band), 8)]
    # upper underside: 2-4 px above each column's teeth top; lower lip: darkest 3-row band 6..34 px under the teeth bottom
    up, lo = [], []
    for x, c in zip(cols, tt):
        if len(c) < 3: continue
        up.append(L[c.min() - 4:c.min() - 1, x].mean())
        seg = L[c.max() + 6:c.max() + 34, x]
        lo.append(seg)
    upv = np.median(up); lom = np.median(np.array([s for s in lo if len(s) == 28]), 0)
    lomin = min(lom[i:i + 3].mean() for i in range(len(lom) - 2))
    # black blobs: luma<12 within the opening's box (teeth top-3 .. teeth bottom+20), outer 10 px excluded
    box = np.zeros_like(L, bool); box[top - 3:ys.max() + 20, tx0 + 10:tx1 - 9] = True
    lab, n = ndimage.label((L < 12) & box)
    wide = [sl[1].stop - sl[1].start for sl in ndimage.find_objects(lab) if sl[1].stop - sl[1].start > 6]
    print(f"{face:8s} {t:6s} incisor px/8col {prof} | black blobs >6px wide: {wide} ({((L<12)&box).sum()} px) | upper underside {upv:.0f}, lower top min {lomin:.0f} (diff {upv-lomin:+.0f})")
