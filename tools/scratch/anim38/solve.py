"""Direct fist solve on fistfit's own measure() (the pass), not the fit's proxy cost.
python solve.py <piece> [--start wrap.json] [--seat dx,dy (mm, hand x/y of the line moved)] [--cycles 3] [--out f.json]
                [--thumb] (refit the thumb with fistfit's own fit_thumb / fit_thumb_over after the fingers)
Per finger (coordinate descent, Nelder-Mead from the current and a few starts): its bends and spread minimise the
squared violations of the pass bands, held MARGIN inside them, plus a pull of the pads toward 0.5 mm."""
import sys, json, argparse, time
from pathlib import Path
W = Path(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a6b5a13d0be70144d")
sys.path.insert(0, str(W / "tools" / "anim"))
import numpy as np
from scipy.optimize import minimize, differential_evolution
import fistfit as F

ap = argparse.ArgumentParser()
ap.add_argument("piece"); ap.add_argument("--start"); ap.add_argument("--seat", default="0,0")
ap.add_argument("--cycles", type=int, default=3); ap.add_argument("--out"); ap.add_argument("--thumb", action="store_true")
ap.add_argument("--side", default="r"); ap.add_argument("--table", action="store_true")
ap.add_argument("--dipmax", type=float, default=F.CAP3 - 1.0)
ap.add_argument("--aim", default=None, help="JSON {finger: [a1,a2,a3]}: a soft pull toward these bends (the staff's curl)")
ap.add_argument("--aimw", type=float, default=0.002)
ap.add_argument("--y0", type=float, default=None); ap.add_argument("--de", action="store_true")
a = ap.parse_args()
piece = F.PIECES[a.piece]["left"] if a.side == "l" else a.piece
P = F.PIECES[piece]
F.THUMB_END = tuple(P.get("thumb_end", F.THUMB_END))
over = bool(P.get("thumb_over"))
A0, D = F.read_seat(piece); D = D / np.linalg.norm(D)
prof = F.hilt_profile(piece, A0, D)
dx, dy = [float(v) / 1000 for v in a.seat.split(",")]
A = A0 + np.array([dx, dy, 0.0])
_, rot, pos = F.load(F.CLIPS / f"{P['rest'][0]}.json")
h = F.Hand(rot[P["rest"][1]], pos[P["rest"][1]], P["outfit"], F.side_of(piece))
wrap = json.load(open(a.start)) if a.start else F.built_wrap(piece)
if "wrap" in wrap: wrap = wrap["wrap"]
ang, opp, roll, spr, tin = F.wrap_args(wrap)
spr = {fn: float(spr.get(fn, 0.0)) for fn in F.FINGERS}
if a.y0 is not None:      # fit()'s seat: the line at hand y y0 (mm), its depth where the palm and thumb base sit 0.3 off
    w = float(A0[2] / D[2]); y0 = a.y0 / 1000
    x = F.seat_x(h, y0, w, D, prof, ang, opp, roll, spr, tin) + dx
    A = np.array([x, y0, 0]) + w * D
gr = F.Grip(A, D, prof)
aim = json.loads(a.aim) if a.aim else {}
M = 0.25   # mm inside each band

def sq(x):
    return x * x if x > 0 else 0.0

def viol(m, fn=None):
    c = 0.0
    for f in ([fn] if fn else F.FINGERS):
        mf = m[f]
        for p in mf["pads"][1:]:
            if p is None: c += 100; continue
            c += 10 * sq((F.PAD[0] + M) - p) + 10 * sq(p - (F.PAD[1] - M))
            c += 0.2 * (p - 0.5) ** 2
        c += 10 * sq((mf["hang"] if mf["hang"] is not None else 20) - (F.HANG_MAX - M))
        c += 0.05 * sq(F.WRAP_MIN + 3 - mf["wrap"])
        if mf["deepest"] is not None: c += 10 * sq(-(F.IN_MAX - M) - mf["deepest"])
    c += 10 * sq(-(F.IN_MAX - M) - m["deepest"])
    for k, v in m["adj"].items():
        if fn is None or fn[0] in k:
            c += 10 * sq(v - (F.ADJ_MAX - M))
    c += 10 * sq(m["thumb_in"] - (F.THUMB_IN - 0.1))
    if over:
        c += 10 * sq(m["thumb_in_m"] - (F.THUMB_IN - 0.1)) + 10 * sq(m["thumb_tip"] - (F.THUMB_OVER - 0.3)) \
            + 10 * sq(m["thumb_col"] - (F.THUMB_COL - 0.2))
    return c

def meas(ang_, spr_, opp_=None, roll_=None, tin_=None):
    return F.measure(h, h.rotf(ang_, opp if opp_ is None else opp_, roll if roll_ is None else roll_, spr_,
                               tin if tin_ is None else tin_), gr)

def finger_cost(fn):
    lo, hi = (0.0, 0.0, 0.0), (100.0, 110.0, a.dipmax)
    def cost(th):
        an = dict(ang); an[fn] = list(th[:3]); s = dict(spr); s[fn] = th[3]
        m = meas(an, s); c = viol(m)
        for v, l, u in zip(th[:3], lo, hi):
            c += 4 * sq(l - v) + 4 * sq(v - u)
        sl, su = F.SPREAD[fn]; c += 4 * sq(sl - th[3]) + 4 * sq(th[3] - su)
        if fn in aim:
            c += a.aimw * sum((x - y) ** 2 for x, y in zip(th[:3], aim[fn]))
        return c
    return cost

t0 = time.time()
for cyc in range(a.cycles):
    for fn in F.FINGERS:
        cost = finger_cost(fn); x0 = np.array(list(ang[fn]) + [spr[fn]], float)
        best = None
        if a.de:
            sl, su = F.SPREAD[fn]
            de = differential_evolution(cost, [(0, 100), (0, 110), (0, a.dipmax), (sl, su)], x0=np.clip(x0, [0, 0, 0, sl], [100, 110, a.dipmax, su]),
                                        popsize=20, maxiter=120, tol=1e-6, mutation=(0.5, 1.0), recombination=0.7,
                                        seed=cyc * 7 + F.FINGERS.index(fn), polish=False)
            best = minimize(cost, de.x, method="Nelder-Mead", options={"xatol": 0.05, "fatol": 1e-5, "maxiter": 800, "adaptive": True})
        starts = [x0] + ([x0 + np.array(d) for d in ((8, -8, -6, 0), (-8, 8, -6, 0), (0, 0, -12, 0), (6, 6, -10, 0))] if cyc == 0 else [])
        for s0 in starts:
            r = minimize(cost, s0, method="Nelder-Mead", options={"xatol": 0.1, "fatol": 1e-4, "maxiter": 500, "adaptive": True})
            if best is None or r.fun < best.fun: best = r
        ang[fn] = [round(float(v), 1) for v in best.x[:3]]; spr[fn] = round(float(best.x[3]), 1)
    if a.thumb:
        if over:
            th = F.fit_thumb_over(h, gr, dict(ang), [opp, roll] + list(ang["thumb"]) + [tin], spr=spr)
            opp, roll = th[0], th[1]; ang["thumb"] = th[2:5]; tin = th[5]
        else:
            J = h.joints(h.rotf(ang, opp, roll, spr, tin))
            ti, tm = [float((J[f"{fn}_03_r"] - gr.A) @ D) * 1000 for fn in ("index", "middle")]
            th = F.fit_thumb(h, gr, dict(ang), [opp, roll] + list(ang["thumb"]), (tm - 5, ti + 5), spr=spr, tin=tin)
            opp, roll = th[0], th[1]; ang["thumb"] = th[2:5]
    m = meas(ang, spr)
    bad = F.verdict(m, ang, over)
    print(f"cycle {cyc}: viol {viol(m):.3f}, fails {len(bad)}: {'; '.join(bad) or 'none'}  ({time.time() - t0:.0f} s)", flush=True)

out = dict(bends={k: [round(float(x), 1) for x in v] for k, v in ang.items()}, spreads=spr, oppose=float(opp),
           thumb_roll=float(roll), **({"thumb_in": float(tin)} if tin else {}))
m = meas(ang, spr)
print(json.dumps(out))
print(json.dumps({fn: m[fn] for fn in F.FINGERS}))
print("palm", m["palm"], "deepest", m["deepest"], "adj", m["adj"], "thumb_in", m["thumb_in"],
      *((["tip", m["thumb_tip"], "col", m["thumb_col"], "pad", m["thumb_pad"], "in_m", m["thumb_in_m"]]) if over else []))
print("A", np.round(A * 1000, 2).tolist())
if a.out:
    json.dump(dict(wrap=out, A=A.tolist()), open(a.out, "w"))
if a.table:
    F.table(piece, out, A, prof)
