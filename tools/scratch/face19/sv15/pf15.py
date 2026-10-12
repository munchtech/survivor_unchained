"""pf15.py STYLE OPTS1 [OPTS2 ..]: per frame k28-60: worst segs 4-7 (mw/mr; the segment), carried flags, move (cm), for
HEAD and each OPTS side by side."""
from ev15 import *
st = sys.argv[1]; runs = [("HEAD", full(st, {}))] + [("O%d" % i, full(st, eval(a))) for i, a in enumerate(sys.argv[2:])]
_, mvh = gmove(runs[0][1]["fr"], gx(runs[0][1]["xs"], runs[0][1]["m"]), 28, 60)
MV = [gmove(r["fr"], gx(r["xs"], r["m"]), 28, 60)[1] for _, r in runs]
print("k   " + " | ".join("%-27s" % n for n, _ in runs))
for k in range(28, 61):
    row = []
    for (n, r), mv in zip(runs, MV):
        cw = r["res"]["mw"][k][3:]; cr = r["res"]["mr"][k][3:]
        row.append("%5.1f s%d %5.1f s%d %s %4.1f" % (min(cw), 4 + int(np.argmin(cw)), min(cr), 4 + int(np.argmin(cr)),
                   "".join("1" if q else "." for q in r["m"].rlog[k][3:]), mv.get(k, 0)))
    print("k%d " % k + " | ".join(row))
