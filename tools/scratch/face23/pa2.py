"""pa2.py: j7's (a) on the portraits, silhouettes found by an Oklab edge walk (their backgrounds pass the skin mask).
Rows 0.15/0.3 pupil-chin below the jaw line's mean (both corners), the lit neck from meas.py; 3 px off each edge."""
import sys, os
import numpy as np
from PIL import Image, ImageFilter
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\tools\scratch\face21")
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\tools\scratch\face17")
import meas, neckx
for fc in sys.argv[1:] or ['own', 'highborn', 'doe', 'sunborn', 'vixen', 'moonlit', 'saffron', 'wildling', 'hardwon', 'fey']:
    p = os.path.join(meas.R, ("own_her_23" if fc == "own" else fc + "_11") + ".png")
    im = Image.open(p).convert("RGB"); a = np.asarray(im, np.float32) / 255
    up = 2 if im.height < 900 else 1
    L = meas.ff.detect(np.asarray(im.resize((im.width * up, im.height * up), Image.LANCZOS)))[:, :2] / up
    pc = np.linalg.norm((L[468] + L[473]) / 2 - L[152])
    lab = neckx.lab_img(np.asarray(im.filter(ImageFilter.BoxBlur(1)), np.float32) / 255)
    nk = meas.spots(p)[0]["neck"]
    o = "%-9s lit L.%02d C.%03d h%.0f |" % (fc, nk[0] * 100, nk[1] * 1000, nk[2])
    jy = (L[136][1] + L[365][1]) / 2
    for t in (0.15, 0.3):
        y = int(jy + t * pc); row = lab[y - 1:y + 2].mean(0)
        ends = []
        for s in (-1, 1):
            x = int(L[152][0]); ref = row[x].copy()
            while 0 < x + s < row.shape[0] - 1 and np.linalg.norm(row[x + s] - ref) < 0.05:
                x += s; ref = 0.9 * ref + 0.1 * row[x]
            ends.append(x)
        lo, hi = ends[0] + 3, ends[1] - 3; seg = row[lo:hi + 1]
        C = np.hypot(seg[:, 1], seg[:, 2]); h = np.degrees(np.arctan2(seg[:, 2], seg[:, 1])); dh = (h - nk[2] + 180) % 360 - 180
        st = np.abs(seg[4:, 0] - seg[:-4, 0])
        sc = 4 * pc / 236.0   # (4 px at the render's scale (own pc 236) in the portrait's pixels)
        k = max(1, int(round(sc))); st2 = np.abs(seg[k:, 0] - seg[:-k, 0])
        o += " r%.2f dh %+4.0f/%+4.0f Cmin %3.0f%% step4 %.3f step4r %.3f w%.2fpc |" % (t, dh.min(), dh.max(), C.min() / nk[1] * 100, st.max(), st2.max(), (hi - lo) / pc)
    print(o)
