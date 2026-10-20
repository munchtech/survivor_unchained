"""Static search for the back_staff row over sampled frames (animation 45). usage: python search.py [outfit] """
import sys, pickle, numpy as np, math
from pathlib import Path
from scipy.spatial import cKDTree
outfit = sys.argv[1] if len(sys.argv) > 1 else "arcanist"
sys.argv = [sys.argv[0], 'old', '--outfit=' + outfit]
exec(open(Path(__file__).with_name('staffcheck.py')).read().split('print(f"row')[0])
cache = Path(__file__).with_name(f'frames_{outfit}.pkl')
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
            w[k] = min(w[k], d["t_" + k].query(q)[0].min())
    return w

if __name__ == "__main__" and "--grid" in " ".join(sys.argv) or True:
    best = []
    for th in (18, 22, 26, 30, 34):
        for ph in (-6, -3, 0, 3):
            for tx in (-0.22, -0.28, -0.34, -0.40):
                for ty in (1.70, 1.78, 1.86, 1.94):
                    for tz in (-0.20, -0.24, -0.28):
                        at, sh, thick = row_from((tx, ty, tz), th, ph, 0)
                        w = evaluate(at, sh, thick)
                        ok = w["hat"] >= 0.045 and w["headsk"] >= 0.045 and w["legs"] >= 0.055 and w["hands"] >= 0.035 and w["body"] >= 0.008 and w["braid"] >= 0.008
                        best.append((ok, -w["body"], th, ph, tx, ty, tz, {k: round(1000 * x) for k, x in w.items()}))
    best.sort(key=lambda r: (not r[0], -r[1] if False else r[1]))
    oks = [r for r in best if r[0]]
    print(len(oks), "ok of", len(best))
    for r in sorted(oks, key=lambda r: -r[1])[:15]: print(r[2:])
    if not oks:
        for r in sorted(best, key=lambda r: -min(r[-1]['hat'], r[-1]['legs']))[:15]: print(r[2:])
