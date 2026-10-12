"""an2.py LOG STYLE K: one frame's chain (displayed) in her neck frame: point, (across, up, back) cm, link length, round
angle (deg from straight behind, toward her near side), inside which balls (cm)."""
from h11 import *
from g9 import inside
LOG, st, K = sys.argv[1], sys.argv[2], int(sys.argv[3])
fr = lg("hc", LOG); xs, m = run(fr, st)
for k in [int(v) for v in sys.argv[3:]]:
    i = k + 3; d = fr[i]; x = xs[i]; at = d["at"]; neck = (at[1] + at[2]) / 2; up = nz(neck - at[10])
    bk = d["back"][1]; bk = nz(bk - (bk @ up) * up); ac = np.cross(up, bk)
    print("k%d up=%s side=%d rnd=%s" % (k, np.round(up, 2), m.side, "".join("1" if r else "." for r in m.rlog[i])))
    for j in range(8):
        r = x[j] - neck; a, h, b = r @ ac * 100, r @ up * 100, r @ bk * 100
        print("  p%d (%5.1f,%5.1f,%5.1f) L=%4.1f th=%4.0f  %s" % (j, a, h, b, np.linalg.norm(x[j] - x[j - 1]) * 100 if j else 0,
              math.degrees(math.atan2(m.side * a, b)), inside(d, x[j])))
    for b in (1, 2, 3, 11, 13, 14):
        r = at[b] - neck; print("  ball%d (%5.1f,%5.1f,%5.1f) r=%.1f" % (b, r @ ac * 100, r @ up * 100, r @ bk * 100, d["r"][b] * 104))
