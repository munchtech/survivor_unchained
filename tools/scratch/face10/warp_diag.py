"""warp_diag.py DIR [pin=1]: the front's warp (heroine_face.from_reference) rebuilt from DIR's marks, and how much it
stretches the reference round the brows: the vertical scale (drawn px per reference px) along each brow's middle, and
a crop of painted_front.png with the pinned and the clay's brow points drawn. Run with the facefit venv."""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy.interpolate import RBFInterpolator

D = sys.argv[1]
pin = len(sys.argv) < 3 or sys.argv[2] != '0'
BROW_A = [70, 63, 105, 66, 107, 55, 65, 52, 53, 46]
BROW_B = [300, 293, 334, 296, 336, 285, 295, 282, 283, 276]
dr = np.array(json.load(open(os.path.join(D, 'marks_drawn.json')))['points'])
rf = np.array(json.load(open(os.path.join(D, 'marks_ref.json')))['points'])
use = np.setdiff1d(np.arange(len(dr)), BROW_A + BROW_B)
pf, pt = dr[use], rf[use]
add_s = []
for ring, (c0, c1) in ((BROW_A, (33, 133)), (BROW_B, (263, 362))):
    def frame(P):
        o = (P[c0] + P[c1]) / 2
        e1 = P[c1] - P[c0]
        w = np.linalg.norm(e1)
        e1 = e1 / w
        return o, e1, np.array([-e1[1], e1[0]]), w
    o_r, e1_r, e2_r, w_r = frame(rf)
    o_d, e1_d, e2_d, w_d = frame(dr)
    for b in ring:
        d = rf[b] - o_r
        u, v = d @ e1_r / w_r, d @ e2_r / w_r
        add_s.append(o_d + w_d * (u * e1_d + v * e2_d))
    print('eye width: ref %.1f px, drawn %.1f px; brow mid above corners: ref %.2f, clay %.2f eye widths' % (
        w_r, w_d, -((rf[ring].mean(0) - o_r) @ e2_r) / w_r * np.sign(e2_r[1] or 1),
        -((dr[ring].mean(0) - o_d) @ e2_d) / w_d * np.sign(e2_d[1] or 1)))
add_s = np.array(add_s)
if pin:
    pf, pt = np.vstack([pf, add_s]), np.vstack([pt, rf[BROW_A + BROW_B]])
tps = RBFInterpolator(pf, pt, kernel='thin_plate_spline', smoothing=2.0)
# (vertical scale down each brow's middle: drawn rows per reference row)
for name, ring in (('A', BROW_A), ('B', BROW_B)):
    q = add_s[:10] if name == 'A' else add_s[10:]
    x = q[:, 0].mean()
    ys = np.arange(q[:, 1].min() - 60, q[:, 1].max() + 60, 2.0)
    m = tps(np.c_[np.full_like(ys, x), ys])
    dy = np.gradient(m[:, 1], ys)
    print('brow %s at x %.0f: drawn y %.0f..%.0f; ref rows per drawn row min %.2f max %.2f (1 = no stretch); %s' % (
        name, x, ys[0], ys[-1], dy.min(), dy.max(), ' '.join('%.2f' % v for v in dy[::5])))
# nearby non-brow landmarks within 40 px of the pinned brows, drawn space, and where they go
from scipy.spatial import cKDTree
t = cKDTree(dr[use])
near = sorted(set(j for p in add_s for j in t.query_ball_point(p, 30)))
print('non-brow landmarks within 30 px of the pinned brows:', [int(use[j]) for j in near])
im = Image.open(os.path.join(D, 'painted_front.png')).convert('RGB')
dd = ImageDraw.Draw(im)
for p in dr[BROW_A + BROW_B]:
    dd.ellipse([p[0] - 3, p[1] - 3, p[0] + 3, p[1] + 3], outline=(0, 160, 255))
for p in add_s:
    dd.ellipse([p[0] - 3, p[1] - 3, p[0] + 3, p[1] + 3], outline=(255, 40, 40))
for j in near:
    p = dr[use[j]]
    dd.ellipse([p[0] - 2, p[1] - 2, p[0] + 2, p[1] + 2], fill=(255, 255, 0))
x0, y0 = add_s[:, 0].min() - 60, add_s[:, 1].min() - 80
im.crop((int(x0), int(y0), int(x0) + 820, int(y0) + 300)).save(os.path.join(D, 'diag_brows.png'))
