"""where.py STYLE MD: HEAD chain samples k38-52: those inside her mesh (< -1 cm) and, for contrast, those outside (> +1 cm)
inside the capsule: place along the right capsule (t), distance from its axis over its radius, and the angle from its top
(deg, + toward her front)."""
from ev13 import *
st, md = sys.argv[1], sys.argv[2]; fr, xs, m = run13(st)
sc = 1.04; r = (0.085 + 0.035) * sc
for k in range(38, 53):
    d = fr[k]; x = xs[k]; (a, b), _ = caps(d, sc); at = d["at"]; neck = (at[1] + at[2]) / 2; up = nz(neck - at[10])
    bk = d["back"][1]; bk = nz(bk - (bk @ up) * up); ax = nz(b - a); u = nz(up - ax * (up @ ax)); fw = np.cross(ax, u)
    if fw @ bk > 0: fw = -fw
    v, _ = mesh("s12/" + md, k); sel = np.linalg.norm(v[:, :3] - x[0], axis=1) <= 0.45; vv = v[sel]; tr = cKDTree(vv[:, :3]); row = []
    for i in range(3, 8):
        for j in range(5):
            s = x[i - 1] + (x[i] - x[i - 1]) * j / 4; _, n1 = tr.query(s); sd = (s - vv[n1, :3]) @ vv[n1, 3:6] * 100
            tt = (s - a) @ (b - a) / ((b - a) @ (b - a)); c = a + (b - a) * min(1, max(0, tt)); off = s - c; L = np.linalg.norm(off)
            if L > r * 1.3: continue
            ang = math.degrees(math.atan2(off @ fw, off @ u))
            if sd < -1 or (sd > 1 and L < r): row.append("s%d.%d sd%.1f t%.2f L%.2f ang%.0f" % (i, j, sd, tt, L / r, ang))
    print("k%d" % k, " | ".join(row))
