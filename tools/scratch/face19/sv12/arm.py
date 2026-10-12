"""arm.py: per frame, her right upper arm's direction in spine_03's rest space (elevation from hanging down, deg; and its
forward swing, deg) beside the ridge top at 14 and 18 cm (body, cm over the neck balls' middle at rest)."""
from ridge import *
for k in range(30, 61, 2):
    d = fr[k]; f = rest_of(d); u = nz(f(d["at"][14]) - f(d["at"][13])); v, _ = mesh("s12/mw", k); P = f(v[:, :3]); body = v[:, 6] == 0
    tops = []
    for x in (14, 18):
        s = body & (np.abs(-P[:, 0] - x / 100) < 0.01) & (P[:, 1] > 1.4); tops.append((P[s, 1].max() - 1.599) * 100)
    print("k%d elev %.0f fwd %.0f out %.0f | top14 %.1f top18 %.1f" % (k, math.degrees(math.acos(-u[1])), math.degrees(math.atan2(u[2], -u[1])), math.degrees(math.atan2(-u[0], -u[1])), *tops))
