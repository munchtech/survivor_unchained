"""e3.py: what holds p1/p2 where they are? From the dumped state at frame k, run that frame and the next N with one term off
(no speed carried in, no gravity, no hold), and see where p1, p2, p3 go (b3 frame, cm)."""
from g9 import *
import hs5
fr = lg("hair17d", "throw_braid"); st = "braid"
K = int(sys.argv[1]) if len(sys.argv) > 1 else 14; N = int(sys.argv[2]) if len(sys.argv) > 2 else 4
def runfrom(k0, n, still=False, nograv=False, holdx=1.0):
    m = M8(fr, st, **per4(H7, st))
    for k in range(k0): m.frame(fr[k])
    d = fr[k0]; m.x[:] = d["x"]; m.xp[:] = d["xp"]
    if still: m.xp[:] = m.x
    out = []
    for k in range(k0, k0 + n):
        dd = dict(fr[k])
        if nograv: dd["dt"] = fr[k]["dt"]
        s_ = m.stiff; m.stiff = s_ * holdx if holdx != 1 else s_
        out.append(m.frame(dd).copy())
    return out
base = runfrom(K, N); still = runfrom(K, N, still=True)
for name, o in (("as is", base), ("no speed in", still)):
    for j, x in enumerate(o):
        d = fr[K + j]; a = angles(x)
        print("%-12s k%2d ang %3.0f %3.0f %3.0f  p1 %s p2 %s p3 %s" % (name, K + j, a[0], a[1], a[2], np.round(F(d, x[1]), 1), np.round(F(d, x[2]), 1), np.round(F(d, x[3]), 1)))
# the root's motion against b3 and the body's turn, per frame
for k in range(K - 2, K + N):
    d0, d1 = fr[k], fr[k + 1]
    print("k%2d root in b3 %s  root world step %s cm  b3 world step %s" % (k, np.round(F(d0, d0["target"][0]), 1), np.round((d1["target"][0] - d0["target"][0]) * 100, 1), np.round((d1["at"][3] - d0["at"][3]) * 100, 1)))
