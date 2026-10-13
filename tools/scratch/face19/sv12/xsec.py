"""xsec.py MESHDIR K [A...]: cross-sections of her right shoulder in the carry's neck frame (cm: a to her right, h up her
spine, b behind, from the neck balls' middle): per a (+-0.75 cm) and b bin (2 cm), the top of her body / of all (outfit)."""
from h12 import *
md, K = sys.argv[1], int(sys.argv[2]); AS = [float(a) for a in sys.argv[3:]] or [10, 14, 18, 22]
fr = lg("hc", "s11_braid_review"); d = fr[K]; at = d["at"]; neck = (at[1] + at[2]) / 2; up = nz(neck - at[10]); bk = d["back"][1]; bk = nz(bk - (bk @ up) * up); ac = np.cross(up, bk)
v, _ = mesh(md, K); Q = (v[:, :3] - neck) @ np.c_[ac, up, bk] * 100; body = v[:, 6] == 0; head = v[:, 6] == 1
print("k%d shoulder ball %s  r(+pad) %.1f" % (K, np.round(((at[13] - neck) @ np.c_[ac, up, bk]) * 100, 1), (0.08 + 0.025) * 104))
for a in AS:
    row = []
    for b in range(-14, 15, 2):
        s = (np.abs(Q[:, 0] - a) < 0.75) & (np.abs(Q[:, 2] - b) < 1) & ~head & (Q[:, 1] > -25)
        tb = Q[s & body, 1].max() if (s & body).any() else np.nan; ta = Q[s, 1].max() if s.any() else np.nan
        row.append("%d:%s" % (b, ("%.0f" % tb) + ("" if abs(ta - tb) < 0.3 or np.isnan(ta) else "/%.0f" % ta)))
    print(" a%-3g" % a, " ".join(row))
