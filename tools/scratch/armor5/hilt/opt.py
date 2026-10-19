import sys, time, math, json
import numpy as np
from ev import *
from scipy.optimize import minimize
q = np.array([0, -0.1614, 0.9869]); b = np.array([0.0795, -0.9838, -0.1609]); fo = np.array([0.9968, 0.0784, 0.0128])
anc = np.array([0.21, 0.1547, 0.0487]) + np.array([1.0, 0, 0]) * 0.0155
def rotv(v, ax, deg):
    ax = ax / np.linalg.norm(ax); t = math.radians(deg)
    return v * math.cos(t) + np.cross(ax, v) * math.sin(t) + ax * np.dot(ax, v) * (1 - math.cos(t))
def hilt_of(x):
    s, of, oq, a, tilt, paz, pel_ = x
    wr = anc + s * (-b) + of * fo + oq * q
    K = rotv(q, fo, a)            # fingers turned about the outward axis (+: toward the pommel)
    pn = rotv(-fo, K, tilt)        # palm normal (inward), tilted about the fingers
    Z = np.cross(pn, K)
    pole = rotv(rotv(np.array([0.3, -0.5, -0.8]), [0, 1, 0], paz), [1, 0, 0], pel_)
    return {"fingers": os.environ.get("FING", "relaxed"), "clav": CLAV, "wrist": wr.round(4).tolist(), "knuckles": K.round(4).tolist(), "thumb": Z.round(4).tolist(), "pole": pole.round(4).tolist()}
FL = [0, 10]
import os
CLAV = float(os.environ.get('CLAV', '1'))
log = open(S / "opt.log", "a")
def cost(x, verbose=False):
    h = hilt_of(x)
    rows = measure(apply("run_warden_town", h, [0, 8]), clrs=("warden", "reaver"), verbose=verbose) +            measure(apply("sprint_warden_town", h, [12, 0]), fl=[0], clrs=("warden", "reaver"), verbose=verbose)
    c = 0
    for r in rows:
        dep = max(r[(cl, k, "a")] for cl in ("warden", "reaver") for k in KEYS)
        pal = max(r[("warden", k, "p")] for k in KEYS)
        c += 10 * max(0, dep - 1.8) + 5 * max(0, pal - 9.3) + max(0, 85 - r["el"]) + 5 * max(0, r["el"] - 116) + 2 * max(0, r["wr"] - 27) + 10 * max(0, max(r[(cl, XK[0], "a")] for cl in ("warden", "reaver")) - 5.0) + 10 * max(0, max(r[(cl, XK[1], "a")] for cl in ("warden", "reaver")) - 2.0)
    print(round(c, 2), np.round(x, 4).tolist(), file=log, flush=True)
    return c
if __name__ == "__main__":
    x0 = np.array(json.loads(sys.argv[1])) if len(sys.argv) > 1 else np.array([0.026, 0.047, -0.034, 0, 0, 0, 0])
    print(cost(x0, True))
    if "--opt" in sys.argv:
        res = minimize(cost, x0, method="Nelder-Mead", options={"maxfev": int(sys.argv[sys.argv.index("--opt") + 1]), "initial_simplex": np.vstack([x0] + [x0 + np.eye(7)[i] * st for i, st in enumerate([-0.005, 0.003, 0.006, -15, 12, 15, 12])]),
                       "xatol": 1e-3, "fatol": 0.05})
        print("best", res.fun, res.x.round(4).tolist(), json.dumps(hilt_of(res.x)))
        cost(res.x, True)
