"""fit.py: the right ridge capsule's ends fitted at k44-48 in the carry's neck frame (a, h, b cm), carried into spine_03's
rest space (skeleton units, her scale taken out), printed per frame for a common pick."""
from ridge import *
for k in (44, 46, 48):
    d = fr[k]; at = d["at"]; neck = (at[1] + at[2]) / 2; up = nz(neck - at[10]); bk = d["back"][1]; bk = nz(bk - (bk @ up) * up); ac = np.cross(up, bk)
    f = rest_of(d); a3 = d["at"][3]
    for a, h, b in ((8, -5, 2), (22, -10, 2)):
        p = neck + (a * ac + h * up + b * bk) / 100; r = (f(p) - A3) / 1.04 + A3
        print("k%d (%d,%d,%d) -> %s" % (k, a, h, b, np.round(r, 4)))
