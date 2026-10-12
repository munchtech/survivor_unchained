"""tl15.py OPTS [STYLE] [K0 K1]: per frame: carried flags, armed inputs (laid weight w, upright, head height), and each
drape point's angle round her spine (deg from straight behind, toward the carry's side; >60 still to go) and height
along her spine from her neck (cm)."""
import sys; sys.path[:0] = ["../sv14"]
from ev14 import *
o = eval(sys.argv[1]); st = sys.argv[2] if len(sys.argv) > 2 else "ponytail"
K0, K1 = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (20, 61)
fr, xs, m = run14(st, o)
for k in range(K0, min(K1, len(fr) - 1) + 1):
    d = fr[k]; at = d["at"]; neck = (at[1] + at[2]) / 2; up = nz(neck - at[10]); bk = d["back"][1]; bk = nz(bk - (bk @ up) * up); ac = np.cross(up, bk)
    side = getattr(m, "side", 1) or 1; dr = m.drape[k]; row = []
    for i in range(1, 8):
        r = dr[i] - neck; a = r @ ac; b = r @ bk; th = math.degrees(math.atan2(side * a, b))
        if th < -90: th += 360
        row.append("%4.0f/%3.0f" % (th, (r @ up) * 100))
    print("k%d %s c%d w%.2f up%.3f hh%.2f | %s" % (k, "".join("1" if q else "." for q in m.rlog[k]), m.caplog[k], m.wlog[k], up[1], d["head"][0][1] - d["ground"], " ".join(row)))
print("side", getattr(m, "side", None))
