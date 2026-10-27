# Body 2 A: per-station half-extents of the right arm about its bone (mm): top+ (lateral/up), top- (medial), front+, back.
#   python ext.py <dump.npz>[|P.npy] [wts.npz]   (arm-weighted vertices: upperarm+lowerarm+hand rows > 0.5)
import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import load, armframe
def ext(d, P, VG, names, s="r", st=None):
    F = armframe(d, s, P); ix = {n: i for i, n in enumerate(names)}
    arm = VG[:, [ix["upperarm_" + s], ix["lowerarm_" + s], ix["hand_" + s]]].sum(1) > 0.5
    rows = []
    for seg, ts in (("u", [0.1, 0.2, 0.3, 0.4, 0.46, 0.55, 0.65, 0.75, 0.85, 0.95]), ("f", [0.05, 0.15, 0.25, 0.4, 0.5, 0.6, 0.75, 0.85, 0.9, 0.95, 0.98])):
        g = F[seg]
        for t in ts:
            m = F["side"] & arm & (np.abs(g["t"] - t) * g["L"] < 0.006) & (g["r"] < 0.08)
            dd = P[m] - g["o"]; x = dd @ g["top"]; y = dd @ g["fr"]
            rows.append((seg, t, x.max() * 1e3, -x.min() * 1e3, y.max() * 1e3, -y.min() * 1e3, int(m.sum())))
    return rows
if __name__ == "__main__":
    for a_ in sys.argv[1:]:
        p = a_.split("|"); d = load(p[0]); P = np.load(p[1]) if len(p) > 1 else d["P"]
        for r in ext(d, P, d["VG"], d["names"]): print(p[-1][-12:], "%s%.2f top+ %5.1f top- %5.1f fr+ %5.1f back %5.1f n%d" % r)
