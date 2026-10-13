"""dbg10.py OPTS: throw braid, per frame: lodge flags, hold/free, and the touch normals' world-up share."""
from hs10 import *
o = eval(sys.argv[1]); fr = lg("hair17d", "throw_braid")
m = M8(fr, "braid", **per4(dict(H7, **o), "braid"))
for k, d in enumerate(fr):
    x = m.frame(d).copy()
    if k >= 2: print("k%2d lodge %s free %s" % (k, "".join("%d" % v for v in m.loglodge[-1]), " ".join("%.2f" % v for v in m.free[1:])))
