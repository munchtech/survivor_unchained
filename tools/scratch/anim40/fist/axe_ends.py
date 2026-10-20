import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from axe_haft import *
pc = gc.load("viking_axe"); O, d, a1, a2 = haft_frame(pc)
tt, u, v = coords(pc, O, d, a1, a2); r = np.hypot(u, v); th = np.arctan2(v, u)
I, L = long_tris(pc); pv = np.unique(L)
def outline(sel):
    k = ((th[sel] + np.pi) / (2 * np.pi) * 72).astype(int) % 72
    o = np.zeros(72)
    for q in range(72):
        if (k == q).any(): o[q] = r[sel][k == q].max()
    return o
win = (tt > -60) & (tt < 140) & (r < 45)
ow = outline(win); op = outline(pv[tt[pv] < 0])
print("wrap outline (every 10 deg):", np.round(ow[::2], 1))
print("prism outline:", np.round(op[::2], 1))
def f(o, x):
    k = ((x + np.pi) / (2 * np.pi) * 72).astype(int) % 72
    return o[k]
for lo, hi in ((-126, -95), (150, 180)):
    s = (tt > lo) & (tt < hi) & (r < 45)
    print(f"--- t {lo}..{hi}: n {s.sum()}")
    lam = (r[s] - f(op, th[s])) / np.maximum(f(ow, th[s]) - f(op, th[s]), 1e-6)
    for tq in np.unique(np.round(tt[s] / 2) * 2):
        q = np.round(tt[s] / 2) * 2 == tq
        print(f"  t {tq:6.0f} n{q.sum():4d} r {r[s][q].min():5.1f}..{r[s][q].max():5.1f} lam {lam[q].min():5.2f}..{lam[q].max():5.2f}")
