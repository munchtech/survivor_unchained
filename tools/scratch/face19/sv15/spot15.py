"""spot15.py OPTS K1,K2 [MD]: segments 4-7's worst sample per frame: its place in spine_03's rest space (cm; x + to her
LEFT as stored, y height, z + front), the nearest vertex's mesh id and depth."""
from ev15 import *
o = eval(sys.argv[1]); ks = [int(v) for v in sys.argv[2].split(",")]; md = sys.argv[3] if len(sys.argv) > 3 else "mw"
fr, xs, m = run14("ponytail", o)
for k in ks:
    d = fr[k]; x = xs[k]; v, _ = mesh("s12/" + md, k); sel = np.linalg.norm(v[:, :3] - x[0], axis=1) <= 0.45; vv = v[sel]; t = cKDTree(vv[:, :3])
    ex = nz(d["across"][3]); ez = -nz(d["back"][3]); ey = np.cross(ez, ex); R = np.c_[ex, ey, ez]; a3 = d["at"][3]
    rest = lambda p: (p - a3) @ R / 1.04 + A3
    for i in [int(v) for v in (sys.argv[4] if len(sys.argv) > 4 else "4,5,6,7").split(",")]:
        S = np.array([x[i - 1] + (x[i] - x[i - 1]) * j / 4 for j in range(5)]); _, j = t.query(S); sd = ((S - vv[j, :3]) * vv[j, 3:6]).sum(1)
        w = int(np.argmin(sd)); p = rest(S[w]) * 100; q = rest(vv[j[w], :3]) * 100
        print("k%d s%d.%d depth %5.1f at (%.1f, %.1f, %.1f) vert (%.1f, %.1f, %.1f) mesh %d" % (k, i, w, sd[w] * 100, *p, *q, int(vv[j[w], 6])))
