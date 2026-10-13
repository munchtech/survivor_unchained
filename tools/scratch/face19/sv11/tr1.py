"""tr1.py LOG STYLE K I: trace drape point I through each drape pass of frame k (neck frame cm, round angle)."""
from h11 import *
import hs8
LOG, st, K, I = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
fr = lg("hc", LOG); m = M8(fr, st, **per4(dict(H7, **HEAD(st)), st))
for j, d in enumerate(fr[:K + 3]): m.frame(d)
d = fr[K + 3]; at = d["at"]; neck = (at[1] + at[2]) / 2; up = nz(neck - at[10]); bk = d["back"][1]; bk = nz(bk - (bk @ up) * up); ac = np.cross(up, bk)
def P(p): r = p - neck; a, h, b = r @ ac * 100, r @ up * 100, r @ bk * 100; return "(%5.1f,%5.1f,%5.1f th%4.0f)" % (a, h, b, math.degrees(math.atan2(m.side * a, b)))
orc, odc = m.rcollide, m.dcollide; ostep = [0]
def rc(dd, p, ax, sc=1.04):
    q = orc(dd, p, ax, sc); print("    rcollide %s -> %s" % (P(p), P(q))); return q
m.rcollide = rc
print("before: p%d %s  p%d %s" % (I - 1, P(m.dr[I - 1] + (d["target"][0] - m.rootT)), I, P(m.dr[I] + (d["target"][0] - m.rootT))))
m.frame(d)
print("after:  p%d %s  p%d %s" % (I - 1, P(m.dr[I - 1]), I, P(m.dr[I])))
