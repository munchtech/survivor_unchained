"""chain_strike: for the left fist's target on the haft, the best elbow (swung round the shoulder-wrist line) and the
wrist bend it leaves (flex, dev; limits FLEX 75 EXT 65 RAD 22 ULN 38), and the pole that gives it. wsearch.py FOLDER"""
import sys, math
from pathlib import Path
import numpy as np
ANIM = Path(__file__).resolve().parents[3] / 'anim'
sys.path.insert(0, str(ANIM))
import audit as A  # noqa
from rig import qmatrix
import clips.arts as M
sk = A.Skeleton.load(A.DATA / 'heroine_skeleton.json'); I = sk.index
d, rot, pos = A.load(Path(sys.argv[1]) / 'chain_strike.json', sk)
g, p = sk.fk(rot, pos)
gr, pr = sk.rest_globals(); pr = pr[0]
lu = np.linalg.norm(pr[I['lowerarm_l']] - pr[I['upperarm_l']]); lf = np.linalg.norm(pr[I['hand_l']] - pr[I['lowerarm_l']])
R_lr, o_lr = M._left_on_haft()
def over(phi, dev):
    lp = 75 if phi > 0 else 65; ld = 22 if dev > 0 else 38
    return ((phi / lp) ** 4 + (dev / ld) ** 4) ** 0.25
# The keyed left hand's twist at a natural frame (f15, its fist), for reference.
def twist_now(f):
    S, E, W = p[f, I['upperarm_l']], p[f, I['lowerarm_l']], p[f, I['hand_l']]
    F = (W - E) / np.linalg.norm(W - E); hn = np.cross(E - S, W - E); hn /= np.linalg.norm(hn)
    X = qmatrix(g[f, I['hand_l']])[:, 0]; px = X - F * (X @ F); px /= np.linalg.norm(px)
    return math.degrees(math.atan2(np.cross(hn, px) @ F, hn @ px))
print('twist now', [round(twist_now(f)) for f in (0, 13, 15, 20, 27)])
for f in range(3, 10):
    Rr = qmatrix(g[f, I['hand_r']]); T = Rr @ R_lr; W = p[f, I['hand_r']] + Rr @ o_lr
    S = p[f, I['upperarm_l']]; v = W - S; dd = np.linalg.norm(v); u = v / dd
    a = (lu ** 2 - lf ** 2 + dd ** 2) / (2 * dd); h = math.sqrt(max(lu ** 2 - a ** 2, 0))
    e1 = np.cross(u, [0, 1, 0]); e1 /= np.linalg.norm(e1); e2 = np.cross(u, e1)
    best = None; ok = []
    for ang in range(0, 360, 5):
        t = math.radians(ang); E = S + a * u + h * (math.cos(t) * e1 + math.sin(t) * e2)
        F = (W - E) / np.linalg.norm(W - E); Y = T[:, 1]
        c = np.clip(F @ Y, -1, 1); deg = math.degrees(math.acos(c))
        ax = np.cross(F, Y); n = np.linalg.norm(ax); ax = ax / n if n > 1e-9 else ax
        phi = deg * (ax @ T[:, 2]) * -1; dev = deg * (ax @ T[:, 0])
        o = over(phi, dev)
        hn = np.cross(E - S, W - E); hn /= np.linalg.norm(hn)
        px = T[:, 0] - F * (T[:, 0] @ F); px /= np.linalg.norm(px)
        tw = math.degrees(math.atan2(np.cross(hn, px) @ F, hn @ px))
        if o < 0.9:
            ok.append((ang, round(o, 2), np.round((E - S) / lu, 2), round(tw)))
        if best is None or o < best[0]:
            best = (o, ang, phi, dev, np.round((E - S) / lu, 2))
    o, ang, phi, dev, pole = best
    if f in (3, 6, 9):
        for k in ok[::2]: print('    ', k)
    print(f"{f:2d} best over {o:4.2f} (1 = at the limit)  flex {phi:5.0f} dev {dev:5.0f}  elbow dir {pole}")
