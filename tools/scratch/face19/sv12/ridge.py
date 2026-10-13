"""ridge.py MESHDIR [K...]: her right shoulder's ridge as posed, in spine_03's rest space (cm; x to her left, so her right
is -x; y up; z front): the shoulder joint's and the lower neck ball's moves from rest, and per across bin the top of her
body (Heroine) and of anything (outfit) and where (z) that top is."""
from h12 import *
md, KS = (sys.argv[1], [int(k) for k in sys.argv[2:]] or list(range(28, 61, 2))) if __name__ == "__main__" else ("s12/mw", [])
fr = lg("hc", "s11_braid_review")
J = np.array([-0.1914, 1.4786, -0.0307]); A3 = np.array([0, 1.5240698, -0.0268065]); A2 = np.array([0, 1.5740698, -0.0433942])
def rest_of(d):
    ex = nz(d["across"][3]); ez = -nz(d["back"][3]); ey = np.cross(ez, ex); R = np.c_[ex, ey, ez]; a3 = d["at"][3]
    return lambda p: (p - a3) @ R + A3
for k in (KS if __name__ == "__main__" else []):
    d = fr[k]; f = rest_of(d); v, _ = mesh(md, k); P = f(v[:, :3]); body = v[:, 6] == 0; head = v[:, 6] == 1
    print("k%d shoulder %s neck2 %s" % (k, np.round((f(d["at"][13]) - J) * 100, 1), np.round((f(d["at"][2]) - A2) * 100, 1)))
    row = []
    for x in range(6, 24, 2):
        s = (np.abs(-P[:, 0] - x / 100) < 0.01) & ~head & (P[:, 1] > 1.40)
        sb = s & body
        tb = P[sb, 1].max() if sb.any() else np.nan; zb = P[sb][np.argmax(P[sb, 1]), 2] if sb.any() else np.nan
        ta = P[s, 1].max() if s.any() else np.nan
        row.append("%d:%.1f/%.1f@%.1f" % (x, (tb - 1.599) * 100, (ta - 1.599) * 100, zb * 100))
    print("   ", " ".join(row))
