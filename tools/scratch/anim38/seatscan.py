"""Per seat (dx,dy mm of the line in hand x/y), each finger's least band excess on its own (DE over its bends and
spread), the palm's gap: where a passing fist can exist at all.
python seatscan.py <piece> <side> <start json|-> <dx,dy> [<dx,dy> ...]"""
import sys, json
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a6b5a13d0be70144d\tools\anim")
import numpy as np
from scipy.optimize import differential_evolution
import fistfit as F

piece, side, start = sys.argv[1], sys.argv[2], sys.argv[3]
piece = F.PIECES[piece]["left"] if side == "l" else piece
P = F.PIECES[piece]
A0, D = F.read_seat(piece); D = D / np.linalg.norm(D)
prof = F.hilt_profile(piece, A0, D)
_, rot, pos = F.load(F.CLIPS / f"{P['rest'][0]}.json")
h = F.Hand(rot[P["rest"][1]], pos[P["rest"][1]], P["outfit"], F.side_of(piece))
wrap = json.load(open(start)) if start != "-" else F.built_wrap(piece)
if "wrap" in wrap: wrap = wrap["wrap"]
ang, opp, roll, spr, tin = F.wrap_args(wrap)

def excess(fn, gr, u, th):
    sub = h.fing[fn]; B = h.bone[sub]
    s = dict(spr); s[fn] = th[3]
    rf = h.rotf({fn: list(th[:3])}, opp, roll, s, tin)
    X = h.pose(rf, sub); g, _ = gr.gap(X); J = h.joints(rf); ok = ~np.isnan(g)
    p2 = g[(B == f"{fn}_02_r") & ok]; p3 = g[(B == f"{fn}_03_r") & ok]
    if not len(p2) or not len(p3): return 50.0, None
    p2, p3 = p2.min(), p3.min(); dp = g[ok].min()
    e = F.end_point(X[B == f"{fn}_03_r"], J, fn); v = e - gr.A; R = gr.R(v @ gr.D, -u)
    hang = (-(v @ u) - R) * 1000 if not np.isnan(R) else 20
    wa = F.wrap_angle(e, gr, u)
    M = 0.2
    ex = max(0, -0.5 + M - p2) + max(0, p2 - 1.5 + M) + max(0, -0.5 + M - p3) + max(0, p3 - 1.5 + M) \
        + max(0, -0.5 + M - dp) + max(0, hang + M) + max(0, 182 - wa) / 10
    return ex, (round(p2, 1), round(p3, 1), round(dp, 1), round(hang, 1), round(wa))

for sxy in sys.argv[4:]:
    dx, dy = [float(v) / 1000 for v in sxy.split(",")]
    gr = F.Grip(A0 + np.array([dx, dy, 0]), D, prof)
    rf0 = h.rotf(ang, opp, roll, spr, tin)
    u = F.palm_dir(h, rf0, gr)
    gp = gr.gap(h.pose(rf0, h.palm))[0]; pm = float(np.nanmin(gp)) if (~np.isnan(gp)).any() else 99
    out = [f"seat {sxy}: palm {pm:.1f}"]
    tot = 0
    for fn in F.FINGERS:
        sl, su = F.SPREAD[fn]
        r = differential_evolution(lambda th: excess(fn, gr, u, th)[0], [(0, 100), (0, 110), (0, F.CAP3 - 1), (sl, su)],
                                   popsize=15, maxiter=60, tol=1e-6, seed=1, polish=False)
        ex, info = excess(fn, gr, u, r.x); tot += ex
        out.append(f"{fn} {ex:.2f} {np.round(r.x, 0).tolist()} {info}")
    print(f"TOTAL {tot:.2f} | " + " | ".join(out), flush=True)
