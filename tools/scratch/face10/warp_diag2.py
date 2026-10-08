"""warp_diag2.py DIR FRAC: the brows and the forehead just above them pinned together (each eye's zone, by the eye's
frame), FRAC of the way from where the clay has them to the reference's place; the warp's vertical scale through the
brows (no fold: no value near 0); the zone's landmarks listed. Run with the facefit venv."""
import json
import os
import sys

import numpy as np
from scipy.interpolate import RBFInterpolator

D, frac = sys.argv[1], float(sys.argv[2])
BROW_A = [70, 63, 105, 66, 107, 55, 65, 52, 53, 46]
BROW_B = [300, 293, 334, 296, 336, 285, 295, 282, 283, 276]
dr = np.array(json.load(open(os.path.join(D, 'marks_drawn.json')))['points'])
rf = np.array(json.load(open(os.path.join(D, 'marks_ref.json')))['points'])


def frame(P, c0, c1):
    o = (P[c0] + P[c1]) / 2
    e1 = P[c1] - P[c0]
    w = np.linalg.norm(e1)
    e1 = e1 / w
    return o, e1, np.array([e1[1], -e1[0]]) * (1 if e1[0] > 0 else -1), w     # (e2 points up the face: -y)


zone, moved_to = [], []
for ring, (c0, c1) in ((BROW_A, (33, 133)), (BROW_B, (263, 362))):
    o_r, e1_r, e2_r, w_r = frame(rf, c0, c1)
    o_d, e1_d, e2_d, w_d = frame(dr, c0, c1)
    uv_r = np.c_[(rf - o_r) @ e1_r / w_r, (rf - o_r) @ e2_r / w_r]
    top = uv_r[ring, 1].max()
    span = uv_r[ring, 0]
    # (the zone: over this eye, from just above its lid's crease to a little over the brow's top)
    z = np.where((uv_r[:, 1] > 0.42) & (uv_r[:, 1] < top + 0.32) & (uv_r[:, 0] > span.min() - 0.15) & (uv_r[:, 0] < span.max() + 0.15))[0]
    z = sorted(set(z) | set(ring))
    for j in z:
        u, v = uv_r[j]
        at = o_d + w_d * (u * e1_d + v * e2_d)
        moved_to.append(dr[j] + frac * (at - dr[j]))
        zone.append(j)
print('zone landmarks:', len(zone), sorted(zone))
zone = np.array(zone)
moved_to = np.array(moved_to)
keep = np.setdiff1d(np.arange(len(dr)), zone)
pf = np.vstack([dr[keep], moved_to])
pt = np.vstack([rf[keep], rf[zone]])
tps = RBFInterpolator(pf, pt, kernel='thin_plate_spline', smoothing=2.0)
for name, ring in (('A', BROW_A), ('B', BROW_B)):
    sel = np.isin(zone, ring)
    q = moved_to[sel]
    x = q[:, 0].mean()
    ys = np.arange(q[:, 1].min() - 90, q[:, 1].max() + 60, 2.0)
    m = tps(np.c_[np.full_like(ys, x), ys])
    dy = np.gradient(m[:, 1], ys)
    print('brow %s frac %.2f: ref rows per drawn row min %.2f max %.2f: %s' % (name, frac, dy.min(), dy.max(), ' '.join('%.2f' % v for v in dy[::5])))
print('brows moved up %.1f px (mean)' % (-(moved_to[np.isin(zone, BROW_A + BROW_B)][:, 1] - dr[np.array(sorted(set(zone) & set(BROW_A + BROW_B)))][:, 1].mean()).mean() if False else
      -np.mean([moved_to[i][1] - dr[zone[i]][1] for i in range(len(zone)) if zone[i] in BROW_A + BROW_B])))
