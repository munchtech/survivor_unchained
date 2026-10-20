"""Nelder-Mead over the back_staff row (top xyz, foot x/z, roll) on search.py's cached frames. usage: python opt.py [outfit] [x0...]"""
import sys, math, numpy as np
from pathlib import Path
from scipy.optimize import minimize
src = open(Path(__file__).with_name('search.py')).read().split('import time\nGRID')[0]
x0 = [float(a) for a in sys.argv[2:]] if len(sys.argv) > 2 else [-0.30, 1.95, -0.27, 0.15, -0.22, 20.0]
sys.argv = sys.argv[:2]
exec(src)
L = 0.9624 + 0.7876

def row(x):
    tx, ty, tz, fx, fz, roll = x
    T = np.array([tx, ty, tz]); d = np.array([fx - tx, 0, fz - tz]); h = math.sqrt(max(L * L - d @ d, 0.01))
    Fp = np.array([fx, ty - h, fz]); sh = (T - Fp) / L
    thick = np.array([0, 0, -1.0]); thick -= sh * thick.dot(sh); thick /= np.linalg.norm(thick)
    side = np.cross(sh, thick); r = math.radians(roll); thick = thick * math.cos(r) + side * math.sin(r)
    return Fp + sh * 0.7876, sh, thick, Fp

def score(x, verbose=False):
    at, sh, thick, Fp = row(x)
    w = evaluate(at, sh, thick)
    mm = {k: 1000 * min(v, 0.2) for k, v in w.items()}
    s = min(mm["hat"] / 50, mm["headsk"] / 50, mm["legs"] / 60, mm["hands"] / 40, mm["body"] / 10, mm["braid"] / 10, 1.0)
    pen = 0.004 * max(0, mm["body"] - 15) + 2.0 * max(0, 0.28 - Fp[1])
    if verbose:
        print({k: round(v) for k, v in mm.items()}, "foot", np.round(Fp, 3), "s", round(s, 3), "pen", round(pen, 3))
    return -(s - pen)

r = minimize(score, x0, method="Nelder-Mead", options=dict(maxfev=int(opt.get("fev", 220)), xatol=1e-3, fatol=1e-3,
             initial_simplex=None))
print("best x", list(np.round(r.x, 4)), "f", round(r.fun, 3))
score(r.x, True)
at, sh, thick, Fp = row(r.x)
print("ROW", ";".join(",".join(f"{v:.4f}" for v in a) for a in (at, sh, thick)))
