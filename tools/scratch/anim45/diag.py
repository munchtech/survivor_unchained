"""Where the staff comes nearest the hat: python diag.py outfit "tx,ty,tz,fx,fz,roll" """
import sys, numpy as np
from pathlib import Path
rows = sys.argv[2:]; sys.argv = sys.argv[:2]
exec(open(Path(__file__).with_name('opt.py')).read().split('r = minimize')[0])
for r in rows:
    x = [float(v) for v in r.split(',')]
    at, sh, thick, Fp = row(x)
    S = np.eye(4); S[:3, :3] = np.column_stack([np.cross(sh, thick), sh, thick]); S[:3, 3] = at
    M = Ri @ S
    p = (M @ np.c_[us, np.ones(len(us))].T).T[:, :3] + (Ri[:3, :3] @ np.array([0, 0, -1.0])) * clr
    res = []
    for d in F:
        Q = p @ d["sp"][:3, :3].T + d["sp"][:3, 3]
        dd, j = d["t_hat"].query(Q)
        k = dd.argmin(); res.append((dd[k], d["name"], us[k].round(2), Q[k].round(3), d["hat"][j[k]].round(3)))
    res.sort(key=lambda t: t[0])
    for t in res[:2]: print(r, round(1000 * t[0]), t[1], "u", t[2], "staff", t[3], "hat", t[4])
    for c in ("idle", "run", "sprint"):
        t = min(x for x in res if x[1].startswith(c)); print("  ", c, round(1000 * t[0]), t[1], "u", t[2], "staff", t[3])
