"""stray.py <dump prefix> <eye_z>: hair guide strands that leave the way of hanging hair near her jaw and neck."""
import glob
import sys

import numpy as np

pre, ez = sys.argv[1], float(sys.argv[2])
for f in sorted(glob.glob(pre + "_*.npz")):
    d = np.load(f)
    P, pts, front = d["P"], d["pts"], d["front"]
    t = np.diff(P, axis=1)
    t /= np.linalg.norm(t, axis=2)[:, :, None] + 1e-9
    mid = (P[:, 1:] + P[:, :-1]) / 2
    zone = (mid[..., 2] < ez - 0.03) & (mid[..., 2] > ez - 0.2) & (mid[..., 1] < 0.04)
    bad = zone & (np.abs(t[..., 2]) < 0.45)            # (running sideways or forward, not down)
    s = np.where(bad.any(1))[0]
    print(f, "strands", len(P), "astray near her jaw:", len(s), "of them front locks:", front[s].sum())
    for i in s[:12]:
        k = np.where(bad[i])[0][0]
        print("  root %s  at %s  going %s  front %d  rise-of-root-z %.3f" % (np.round(pts[i], 3), np.round(mid[i, k], 3), np.round(t[i, k], 2),
                                                                          front[i], pts[i, 2] - ez))
