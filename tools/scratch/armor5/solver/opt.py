"""armor 5 solver: search a socket row (At offset, small turn of Shaft/Thick) against the grids.
    python opt.py <socket> [--keys a,b] [--move 0.08] [--ang 20] [--iters 400] [--fix-normal]"""
import sys, json, argparse, time
import numpy as np
from scipy.optimize import differential_evolution
from scipy.spatial.transform import Rotation
import score as S
from grids import rest

SP = "C:/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-survivorsunchained/b8d13e5f-b1a5-4365-9d36-63505c60b8a1/scratchpad/"


def trial(row, x, turn_normal):
    bone, at, shaft, thick, normal, mir = row
    R = Rotation.from_rotvec(np.radians(x[3:6])).as_matrix()
    nn = R @ np.array(normal, float) if turn_normal else np.array(normal, float)
    return (bone, tuple(np.array(at) + x[:3]), tuple(R @ np.array(shaft, float)), tuple(R @ np.array(thick, float)), tuple(nn), mir)


def angles(row0, row1):
    a = lambda u, v: np.degrees(np.arccos(np.clip(S.nz(u) @ S.nz(v), -1, 1)))
    s0, s1 = S.nz(row0[2]), S.nz(row1[2])
    t0 = S.nz(np.array(row0[3]) - s0 * (s0 @ row0[3])); t1 = S.nz(np.array(row1[3]) - s1 * (s1 @ row1[3]))
    return a(s0, s1), a(t0, t1)


def worst(res, keys):
    b = a = 0.0
    for k, v in res.items():
        if keys and k not in keys: continue
        for o, (bb, aa, *_ ) in v.items():
            b, a = max(b, bb), max(a, aa)
    return b, a


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("socket")
    ap.add_argument("--keys", default="")
    ap.add_argument("--move", type=float, default=0.08)
    ap.add_argument("--ang", type=float, default=20)
    ap.add_argument("--iters", type=int, default=60)
    ap.add_argument("--turn-normal", action="store_true")
    ap.add_argument("--wang", type=float, default=0.15, help="cost per degree of turn")
    ap.add_argument("--wmove", type=float, default=0.05, help="cost per mm of move")
    ap.add_argument("--fixgap", type=float, default=10)
    ap.add_argument("--x0", default="")
    ap.add_argument("--vox", type=float, default=0.012)
    ap.add_argument("--outfits", default="")
    ap.add_argument("--powell", action="store_true")
    ap.add_argument("--lo", default="")
    ap.add_argument("--hi", default="")
    a = ap.parse_args()
    row0 = S.ROWS[a.socket]
    s = S.Scorer({row0[0]: SP + ("pelvis.npz" if row0[0] == "pelvis" else "spine.npz")}, [a.socket])
    keys = set(a.keys.split(",")) if a.keys else set()
    # coarse points for the search (a point per 12 mm voxel)
    full = dict(s.pts)
    for k, q in full.items():
        _, first = np.unique(np.floor(q / a.vox).astype(np.int64), axis=0, return_index=True)
        s.pts[k] = q[np.sort(first)]
    outs = a.outfits.split(",") if a.outfits else S.OUTFITS
    base, _ = s.score(a.socket, row0)
    gap0 = {(k, o): v[4] for k, vv in base.items() for o, v in vv.items()}
    clr0 = s.clearance(a.socket, row0, a.socket == "sling")
    print("base worst body/arm", worst(base, keys))
    allkeys = dict(s.keys)
    if keys: s.keys = {k: v for k, v in allkeys.items() if k in keys}

    def cost(x, verbose=False):
        row = trial(row0, x, a.turn_normal)
        res, clr = s.score(a.socket, row, outfits=outs)
        b, ar = worst(res, keys)
        sa, ta = angles(row0, row)
        mv = np.linalg.norm(x[:3]) * 1000
        # snug: the gap to the outfit (skin gap less the clearance) may grow 10 mm at most
        grow = 0.0
        for (k, o), g0 in gap0.items():
            if (keys and k not in keys) or o not in outs: continue
            g1 = res[k][o][4] - clr[o] * 1000
            grow = max(grow, g1 - (max(g0 - clr0[o] * 1000, 0)) - a.fixgap)
        c = 20 * max(0, b - 0.3) + max(0, ar - 1.0) + a.wang * (sa + ta) + a.wmove * mv + 5 * max(0, grow) \
            + 3 * max(0, sa - 15) + 3 * max(0, ta - 15)
        if verbose:
            print(f"body {b:.1f} arm {ar:.1f} shaft {sa:.1f}deg thick {ta:.1f}deg move {mv:.0f}mm grow {grow:.1f} cost {c:.2f}")
        return c

    m, g = a.move, a.ang
    lo = [float(v) for v in a.lo.split(",")] if a.lo else [-m, -m, -m, -g, -g, -g]
    hi = [float(v) for v in a.hi.split(",")] if a.hi else [m, m, m, g, g, g]
    t = time.time()
    x0 = np.array([float(v) for v in a.x0.split(",")]) if a.x0 else None
    if a.powell:
        from scipy.optimize import minimize
        r = minimize(cost, x0 if x0 is not None else np.zeros(6), method="Powell", bounds=list(zip(lo, hi)), options=dict(maxfev=a.iters, xtol=1e-3, ftol=1e-3))
    else:
        r = differential_evolution(cost, list(zip(lo, hi)), maxiter=a.iters, popsize=12, tol=1e-6, seed=3, polish=False, x0=x0)
    print(f"{time.time() - t:.0f}s x {np.round(r.x, 4).tolist()}")
    cost(r.x, True)
    row = trial(row0, r.x, a.turn_normal)
    print("row", json.dumps([row[0], [round(v, 4) for v in row[1]], [round(v, 4) for v in row[2]], [round(v, 4) for v in row[3]], [round(v, 4) for v in row[4]]]))
    s.pts = full
    s.keys = allkeys
    res, clr = s.score(a.socket, row)
    for k, v in res.items():
        for o, (b, ar, af, bf, gp) in v.items():
            print(f"  {k:24} {o:9} body {b:5.1f} @{bf:22} arm {ar:5.1f} @{af:22} gap {gp - clr[o]*1000:6.1f} (was {gap0[(k, o)] - clr0[o]*1000:6.1f})")


if __name__ == "__main__":
    main()
