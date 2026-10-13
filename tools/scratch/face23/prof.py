"""prof.py TAG [faces]: along neckx's rows (.15, .30), where the (a) failures sit: per 3 px bin, L C h and flags
(h: hue off the lit neck > 6, c: C < 75% of the lit neck's, s: L step > .02 within 4 px). x from the far silhouette (0) in px."""
import sys, os
import numpy as np
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\tools\scratch\face21")
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\tools\scratch\face17")
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\tools\scratch\face19")
import meas, neckx
from PIL import Image, ImageFilter
tag = sys.argv[1]; faces = sys.argv[2:] or ['own', 'highborn', 'vixen', 'moonlit', 'fey']
for fc in faces:
    p = os.path.join(meas.S, "%s_%s.png" % (tag, fc))
    m, im = neckx.measure(p)
    lab = neckx.lab_img(np.asarray(im.filter(ImageFilter.BoxBlur(1)), np.float32) / 255)
    nk = m["nk"]; s = m["s"]
    print("== %s lit neck L.%02d C.%03d h%.0f  pc %.0f px" % (fc, nk[0] * 100, nk[1] * 1000, nk[2], m["pc"]))
    for t in (0.15, 0.3):
        q = m["rows"][t]; y = q["y"]
        seg = lab[y - 1:y + 2, q["lo"]:q["hi"] + 1].mean(0)
        C = np.hypot(seg[:, 1], seg[:, 2]); h = np.degrees(np.arctan2(seg[:, 2], seg[:, 1]))
        dh = (h - nk[2] + 180) % 360 - 180
        st = np.zeros(len(seg)); st[4:] = np.abs(seg[4:, 0] - seg[:-4, 0])
        n = len(seg); xs = np.arange(q["lo"], q["hi"] + 1)
        # far silhouette first
        order = range(n - 1, -1, -1) if s > 0 else range(n)
        out = []
        for k, i in enumerate(order):
            if k % 3: continue
            fl = ("h" if abs(dh[i]) > 6 else "") + ("c" if C[i] < 0.75 * nk[1] else "") + ("s" if st[i] > 0.02 else "")
            out.append("%d:%.2f/%02.0f/%+.0f%s" % (k, seg[i, 0], C[i] * 1000, dh[i], fl))
        print(" row %.2f y%d w%d: " % (t, y, n) + " ".join(out))
