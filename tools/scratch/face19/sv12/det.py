"""det.py STYLE MESHDIR K [OPTS]: per link sample, the nearest vertex's mesh, its signed distance (cm), and the sample
and that vertex in her neck frame (a right, h up, b behind; cm); and the mean signed distance of the 8 nearest."""
from ev12 import *
import hs12
st, md, K = sys.argv[1], sys.argv[2], int(sys.argv[3]); oo = eval(sys.argv[4]) if len(sys.argv) > 4 else {}
fr = lg(*DUMP[st].split("/")); xs, m = run12(fr, st, **oo); x = xs[K]; d = fr[K]
at = d["at"]; neck = (at[1] + at[2]) / 2; up = nz(neck - at[10]); bk = d["back"][1]; bk = nz(bk - (bk @ up) * up); ac = np.cross(up, bk)
P = lambda p: np.array([(p - neck) @ ac, (p - neck) @ up, (p - neck) @ bk]) * 100
v, _ = mesh("s12/" + md, K); sel = np.linalg.norm(v[:, :3] - x[0], axis=1) <= 0.45; vv = v[sel]; t = cKDTree(vv[:, :3])
names = open(A + "s12/m_%s_braid.log" % ("warden" if md == "mw" else "reaver"), errors="ignore").read().split("HAIRMESH names: ")[1].split("\n")[0].split(",")
print("rnd", "".join("1" if r else "." for r in m.rlog[K]), "shoulder ball", np.round(P(at[13]), 1))
for i in range(1, 8):
    for j in range(5):
        s = x[i - 1] + (x[i] - x[i - 1]) * j / 4; _, n1 = t.query(s); dd, nn = t.query(s, 8)
        sg = (s - vv[n1, :3]) @ vv[n1, 3:6] * 100; s8 = np.mean([(s - vv[q, :3]) @ vv[q, 3:6] for q in nn]) * 100
        print("seg%d.%d %-20s %5.1f (8: %5.1f) s %s v %s n %s" % (i, j, names[int(vv[n1, 6])], sg, s8, np.round(P(s), 1), np.round(P(vv[n1, :3]), 1), np.round([vv[n1, 3:6] @ ac, vv[n1, 3:6] @ up, vv[n1, 3:6] @ bk], 2)))
