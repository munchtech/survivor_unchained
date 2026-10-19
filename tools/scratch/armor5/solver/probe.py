import sys, numpy as np, score as S
from grids import rest
SP = "C:/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-survivorsunchained/b8d13e5f-b1a5-4365-9d36-63505c60b8a1/scratchpad/"
so, key, o = sys.argv[1:4]
row = S.ROWS[so]
s = S.Scorer({row[0]: SP + ("pelvis.npz" if row[0] == "pelvis" else "spine.npz")}, [so])
clr = s.clearance(so, row, so == "sling")
p, n = s.key_points(key, row)
R = rest(row[0]); q = (p + n * clr[o]) @ R[:3, :3].T + R[:3, 3]
D, L = s.lookup(row[0], q)
F = s.g[row[0]]["F"]
for cls, m in (("arm", L), ("body", ~L)):
    X = np.where(m, D, -999)
    for f in np.argsort(-X.max(1))[:6]:
        if X[f].max() <= 0: break
        hit = X[f] > 0
        print(cls, F[f], f"{X[f].max():.1f}mm", "n", hit.sum(), "rest-space box", np.round(q[hit].min(0), 3), np.round(q[hit].max(0), 3))
