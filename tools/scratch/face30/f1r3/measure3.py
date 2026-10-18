"""face30 F1 r3 acceptance at c04a A5 (still 2): python measure3.py TAG...  (all three faces; teeth from f30dbg_<face>).
teeth: per column (inner 80%, from the first to the last where the band is over half its median: its ends under her lip out) mean luma of the upper band's top 8 rows; worst dip below its +-6 column neighbours' median.
lower lip top: darkest 3-row band 2..30 px under the teeth, its luma and hue vs the upper lip body's hue (8-14 px above
the teeth) and the upper lip's underside luma (1-3 px above). black: luma<12 blobs wider than 6 px within the opening (teeth rows -3..+3), corners (10 px) out."""
import sys, colorsys, numpy as np
from PIL import Image
from scipy import ndimage
S = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\godot\.shots"
Y0, Y1, X0, X1 = 700, 840, 1000, 1300
def hue(rgb):
    h = colorsys.rgb_to_hsv(*(np.clip(rgb, 0, 255) / 255.0))[0] * 360
    return h if h < 300 else h - 360
for face in ["own", "saffron", "sunborn"]:
    d = np.asarray(Image.open(f"{S}/f30dbg_{face}_c04a_sa5_2.png").convert("RGB")).astype(int)[Y0:Y1, X0:X1]
    g = (d[..., 1] > 120) & (d[..., 1] > d[..., 0] + 25) & (d[..., 2] < 140); g = ndimage.binary_opening(g, iterations=1)
    ys, xs = np.where(g); tx0, tx1 = xs.min(), xs.max(); W = tx1 - tx0
    for t in sys.argv[1:]:
        try: a = np.asarray(Image.open(f"{S}/f30{t}_{face}_c04a_sa5_2.png").convert("RGB")).astype(float)[Y0:Y1, X0:X1]
        except FileNotFoundError: continue
        L = a @ [0.299, 0.587, 0.114]
        cols, tl, up, lipc, lo, loc = [], [], [], [], [], []
        for x in range(tx0 + W // 10, tx1 - W // 10):
            c = g[:, x].nonzero()[0]
            if len(c) < 3: continue
            top, bot = c.min(), c.max()
            run = np.argmax(np.r_[np.diff(c) > 1, True]) + 1
            cols.append((x, top, run)); tl.append(0)
            up.append(L[top - 3:top, x].mean()); lipc.append(a[top - 14:top - 8, x].mean(0))
            seg = L[bot + 2:bot + 30, x]; i = min(range(len(seg) - 2), key=lambda i: seg[i:i + 3].mean())
            lo.append(seg[i:i + 3].mean()); loc.append(a[bot + 2 + i:bot + 5 + i, x].mean(0))
        tops = ndimage.median_filter(np.array([c[1] for c in cols]), 15); run = int(np.median([c[2] for c in cols]))
        tl = np.array([L[tp:tp + run, x].mean() for (x, _, _), tp in zip(cols, tops)])
        on = tl > 0.5 * np.median(tl); i0 = int(np.argmax(on)); i1 = len(on) - int(np.argmax(on[::-1]))
        span = f"{cols[i0][0] + X0}-{cols[i1 - 1][0] + X0}"; tl = tl[i0:i1]; cols = cols[i0:i1]
        dips = [np.median(np.r_[tl[max(0, i - 6):i], tl[i + 1:i + 7]]) - tl[i] for i in range(len(tl))]
        dip = max(dips); dipx = cols[int(np.argmax(dips))][0] + X0
        hl, hlo = hue(np.mean(lipc, 0)), hue(np.mean(loc, 0))
        box = np.zeros_like(L, bool); box[ys.min() - 3:ys.max() + 4, tx0 + 10:tx1 - 9] = True
        lab, n = ndimage.label((L < 12) & box)
        wide = [sl[1].stop - sl[1].start for sl in ndimage.find_objects(lab) if sl[1].stop - sl[1].start > 6]
        print(f"{face:8s} {t:6s} teeth x {span} luma {tl.min():.0f}-{tl.max():.0f} worst dip {dip:.0f} at x {dipx} | lip top {np.median(lo):.0f} vs underside {np.median(up):.0f} "
              f"(d {np.median(lo)-np.median(up):+.0f}), hue {hlo:.0f} vs lip {hl:.0f} (d {hlo-hl:+.0f}) | black >6px {wide} ({((L<12)&box).sum()} px)")
