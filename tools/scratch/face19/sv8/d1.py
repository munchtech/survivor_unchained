"""d1.py CLIP STYLE [SET]: per frame: cell, w, spine up-dot, and each drawn point in her body frame (cm: across, up, back; back<0 = in front of her neck)."""
import sys; sys.path[:0] = ["../sv6", "../sv5", "../sv4", "../sv3"]
from hs6 import *
cl, st = sys.argv[1], sys.argv[2]; SET = sys.argv[3] if len(sys.argv) > 3 else "hair15"
STEP = dict(death=3, getup=4, getupback=4, throw=2, run=2, stop=2)
fr = lg(SET, cl + "_" + st)
m = M6(fr, st, **per4(H7, st))
def body(d):
    at = d["at"]; o = at[2]; up = nz(at[1] - at[10]); bk = d["back"][2]; bk = nz(bk - (bk @ up) * up); ac = np.cross(up, bk)
    return o, np.array([ac, up, bk])
for j, d in enumerate(fr):
    out = m.frame(d).copy()
    if j + 1 < len(fr):
        err = np.linalg.norm(m.x - fr[j + 1]["x"], axis=1).max() * 100
    else: err = 0
    o, B = body(d); up = nz(d["at"][1] - d["at"][10])[1]
    pts = " ".join("%4.0f,%4.0f,%4.0f" % tuple(B @ (out[i] - o) * 100) for i in (1, 3, 5, 7))
    print("f%2d c%5.2f w %.2f up %+.2f err %4.2f | %s" % (j, j / STEP[cl], m.w, up, err, pts))
