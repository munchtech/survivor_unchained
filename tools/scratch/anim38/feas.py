"""One finger's feasible set on a piece at a seat: a grid over its bends and spread, measured as measure() does
(pads 02/03, its deepest, its end's hang, its wrap), the rest of the hand from a start wrap.
python feas.py <piece> <finger> [--side l] [--seat dx,dy] [--start json] [--y0 mm]"""
import sys, json, argparse, itertools
from pathlib import Path
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a6b5a13d0be70144d\tools\anim")
import numpy as np
import fistfit as F

ap = argparse.ArgumentParser()
ap.add_argument("piece"); ap.add_argument("finger"); ap.add_argument("--side", default="r")
ap.add_argument("--seat", default="0,0"); ap.add_argument("--start"); ap.add_argument("--step", type=float, default=5.0)
a = ap.parse_args()
piece = F.PIECES[a.piece]["left"] if a.side == "l" else a.piece
P = F.PIECES[piece]
A0, D = F.read_seat(piece); D = D / np.linalg.norm(D)
prof = F.hilt_profile(piece, A0, D)
dx, dy = [float(v) / 1000 for v in a.seat.split(",")]
gr = F.Grip(A0 + np.array([dx, dy, 0]), D, prof)
_, rot, pos = F.load(F.CLIPS / f"{P['rest'][0]}.json")
h = F.Hand(rot[P["rest"][1]], pos[P["rest"][1]], P["outfit"], F.side_of(piece))
wrap = json.load(open(a.start)) if a.start else F.built_wrap(piece)
if "wrap" in wrap: wrap = wrap["wrap"]
ang, opp, roll, spr, tin = F.wrap_args(wrap)
fn = a.finger; sub = h.fing[fn]; B = h.bone[sub]
u = F.palm_dir(h, h.rotf(ang, opp, roll, spr, tin), gr)
gp = gr.gap(h.pose(h.rotf(ang, opp, roll, spr, tin), h.palm))[0]
print("palm", np.nanmin(gp))
s = a.step
rows = []
sl, su = F.SPREAD[fn]
for m1, m2, m3, sp in itertools.product(np.arange(0, 101, s), np.arange(0, 111, s), np.arange(0, 62, s), np.arange(sl, su + 0.1, 4)):
    an = dict(ang); an[fn] = [m1, m2, m3]; spd = dict(spr); spd[fn] = sp
    rf = h.rotf({fn: [m1, m2, m3]} | {k: v for k, v in an.items() if k != fn}, opp, roll, spd, tin)
    X = h.pose(rf, sub); g, _ = gr.gap(X); J = h.joints(rf)
    ok = ~np.isnan(g)
    p2 = g[(B == f"{fn}_02_r") & ok]; p3 = g[(B == f"{fn}_03_r") & ok]
    if not len(p2) or not len(p3): continue
    p2, p3 = p2.min(), p3.min(); dp = g[ok].min()
    e = F.end_point(X[B == f"{fn}_03_r"], J, fn); v = e - gr.A; R = gr.R(v @ gr.D, -u)
    hang = (-(v @ u) - R) * 1000 if not np.isnan(R) else 99
    wa = F.wrap_angle(e, gr, u)
    rows.append((m1, m2, m3, sp, p2, p3, dp, hang, wa))
R = np.array(rows)
ok = (R[:, 4] >= -0.5) & (R[:, 4] <= 1.5) & (R[:, 5] >= -0.5) & (R[:, 5] <= 1.5) & (R[:, 6] >= -0.5) & (R[:, 7] <= 0) & (R[:, 8] >= 180)
print(f"{len(R)} poses, {ok.sum()} pass the finger's own bands")
for r in R[ok][:15]:
    print(np.round(r, 1).tolist())
# the nearest misses: by the summed band excess
ex = np.clip(-0.5 - R[:, 4], 0, None) + np.clip(R[:, 4] - 1.5, 0, None) + np.clip(-0.5 - R[:, 5], 0, None) + np.clip(R[:, 5] - 1.5, 0, None) \
    + np.clip(-0.5 - R[:, 6], 0, None) + np.clip(R[:, 7], 0, None) + np.clip(180 - R[:, 8], 0, None) / 10
for i in np.argsort(ex)[:8]:
    print("miss", round(float(ex[i]), 2), np.round(R[i], 1).tolist())
