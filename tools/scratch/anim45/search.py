"""Static search for the back_staff row over sampled frames (animation 45). usage: python search.py [outfit] """
import sys, pickle, numpy as np, math
from pathlib import Path
from scipy.spatial import cKDTree
outfit = sys.argv[1] if len(sys.argv) > 1 else "arcanist"
_g = [a for a in sys.argv if a.startswith('--grid=')]
sys.argv = [sys.argv[0], 'old', '--outfit=' + outfit] + _g
exec(open(Path(__file__).with_name('staffcheck.py')).read().split('print(f"row')[0])
cache = Path(r'C:/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-survivorsunchained/746784c6-95b9-4ef2-95bf-f24b9874f4bb/scratchpad/anim45/staff') / f'frames_{outfit}.pkl'
if cache.exists():
    F = pickle.loads(cache.read_bytes())
else:
    F = []
    for name, st in (("idle_arcanist_town", 8), ("run_arcanist_town", 1), ("sprint_arcanist_town", 1)):
        Gs = b.frames(b.clip(name))
        for f in range(0, len(Gs), st):
            G = Gs[f]; P = b.pose(G)
            hand = []
            for s in "lr":
                hj = G[I[f"hand_{s}"]][:3, 3]
                hand.append(P[HAND[s] | (FORE[s] & (np.linalg.norm(P - hj, axis=1) < 0.08))])
            trunk = SK & ~HAND['l'] & ~HAND['r'] & ~FORE['l'] & ~FORE['r'] & ~np.isin(vb, ['upperarm_l','upperarm_r'])
            F.append(dict(name=f"{name}:{f}", sp=G[I["spine_03"]], hat=P[HAT], headsk=P[HEADSK], braid=P[HA][::4],
                          legs=P[CALF | BOOT], hands=np.concatenate(hand), body=P[(trunk | GA) & ~HAT][::2]))
    cache.write_bytes(pickle.dumps(F))
for d in F:
    for k in ("hat", "headsk", "braid", "legs", "hands", "body"):
        d["t_" + k] = cKDTree(d[k])
us = u[::7]; hd, ft = us[:, 1] > 0.30, us[:, 1] < -0.55
R = rest("spine_03"); Ri = np.linalg.inv(R)

def row_from(top, th, ph, roll):
    sh = np.array([-math.sin(math.radians(th)), math.cos(math.radians(th)), 0.0])
    sh = sh * math.cos(math.radians(ph)) + np.array([0, 0, math.sin(math.radians(ph))])  # ph>0: top leans in (+z), foot out
    sh /= np.linalg.norm(sh)
    thick = np.array([0, 0, -1.0]); thick -= sh * thick.dot(sh); thick /= np.linalg.norm(thick)
    side = np.cross(sh, thick)
    r = math.radians(roll); thick = thick * math.cos(r) + side * math.sin(r)
    at = np.array(top) - sh * 0.9624
    return at, sh, thick

def evaluate(at, sh, thick, clr=clr):
    S = np.eye(4); S[:3, :3] = np.column_stack([np.cross(sh, thick), sh, thick]); S[:3, 3] = at
    M = Ri @ S
    p = (M @ np.c_[us, np.ones(len(us))].T).T[:, :3] + (Ri[:3, :3] @ np.array([0, 0, -1.0])) * clr
    w = {k: 9.0 for k in ("hat", "headsk", "braid", "legs", "hands", "body")}
    for d in F:
        Q = p @ d["sp"][:3, :3].T + d["sp"][:3, 3]
        for k, q in (("hat", Q[hd]), ("headsk", Q[hd]), ("braid", Q), ("legs", Q[ft]), ("hands", Q), ("body", Q)):
            w[k] = min(w[k], d["t_" + k].query(q, distance_upper_bound=0.2)[0].min())
    return w

import time
GRID = eval(opt.get("grid", "dict(th=(18,22,26,30,34), ph=(-6,-3,0,3), tx=(-0.22,-0.28,-0.34,-0.40), ty=(1.70,1.78,1.86,1.94), tz=(-0.20,-0.24,-0.28))"))
import itertools
t0 = time.time(); best = []
for th, ph, tx, ty, tz, roll in itertools.product(GRID["th"], GRID["ph"], GRID["tx"], GRID["ty"], GRID["tz"], GRID.get("roll", (0,))):
    at, sh, thick = row_from((tx, ty, tz), th, ph, roll)
    w = evaluate(at, sh, thick)
    ok = w["hat"] >= 0.045 and w["headsk"] >= 0.045 and w["legs"] >= 0.055 and w["hands"] >= 0.035 and w["body"] >= 0.008 and w["braid"] >= 0.008
    fp = at - sh * 0.7876
    best.append((ok, w["body"], th, ph, tx, ty, tz, roll, {k: round(1000 * min(x, 9)) for k, x in w.items()}, "foot", tuple(np.round(fp, 2))))
    if len(best) == 1: print("one eval", round(time.time() - t0, 2), "s", flush=True)
oks = [r for r in best if r[0]]
print(len(oks), "ok of", len(best))
for r in sorted(oks, key=lambda r: r[1])[:25]: print(r[2:])
if not oks:
    sc = lambda w: min(w["hat"] / 45, w["headsk"] / 45, w["legs"] / 55, w["hands"] / 35, w["body"] / 8, w["braid"] / 8)
    for r in sorted(best, key=lambda r: -sc(r[8]))[:25]: print(round(sc(r[8]), 2), r[2:], "row", [list(np.round(x, 3)) for x in row_from((r[4], r[5], r[6]), r[2], r[3], r[7])])
