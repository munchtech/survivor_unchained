"""chain_strike: the left fist rolled round the haft by psi: per frame and psi, the best elbow swing's wrist overrun
(1 = at the limit), its forearm twist off the hinge (natural about 6) and elbow way. rsearch.py FOLDER [frames]"""
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
frames = [int(x) for x in sys.argv[2].split(',')] if len(sys.argv) > 2 else [3, 6, 9]
g, p = sk.fk(rot, pos)
gr, pr = sk.rest_globals(); pr = pr[0]
lu = np.linalg.norm(pr[I['lowerarm_l']] - pr[I['upperarm_l']]); lf = np.linalg.norm(pr[I['hand_l']] - pr[I['lowerarm_l']])
R_lr, o_lr = M._left_on_haft(); C, H, N, Wd = M._haft()
def over(phi, dev):
    lp = 75 if phi > 0 else 65; ld = 22 if dev > 0 else 38
    return ((phi / lp) ** 4 + (dev / ld) ** 4) ** 0.25
def rotm(ax, deg):
    ax = ax / np.linalg.norm(ax); t = math.radians(deg); K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]])
    return np.eye(3) + math.sin(t) * K + (1 - math.cos(t)) * K @ K
for f in frames:
    Rr = qmatrix(g[f, I['hand_r']]); T0 = Rr @ R_lr; W0 = p[f, I['hand_r']] + Rr @ o_lr
    Hw = Rr @ H; Cw = p[f, I['hand_r']] + Rr @ C
    S = p[f, I['upperarm_l']]
    for psi in range(0, 360, 30):
        Q = rotm(Hw, psi); T = Q @ T0; W = Cw + Q @ (W0 - Cw)
        v = W - S; dd = np.linalg.norm(v); u = v / dd
        if dd > lu + lf: print(f, psi, 'out of reach'); continue
        a = (lu ** 2 - lf ** 2 + dd ** 2) / (2 * dd); h = math.sqrt(max(lu ** 2 - a ** 2, 0))
        e1 = np.cross(u, [0, 1, 0]); e1 /= np.linalg.norm(e1); e2 = np.cross(u, e1)
        best = None
        for ang in range(0, 360, 5):
            t = math.radians(ang); E = S + a * u + h * (math.cos(t) * e1 + math.sin(t) * e2)
            F = (W - E) / np.linalg.norm(W - E); Y = T[:, 1]
            deg = math.degrees(math.acos(np.clip(F @ Y, -1, 1)))
            ax = np.cross(F, Y); n = np.linalg.norm(ax); ax = ax / n if n > 1e-9 else ax
            phi = deg * (ax @ T[:, 2]) * -1; dev = deg * (ax @ T[:, 0])
            hn = np.cross(E - S, W - E); hn /= np.linalg.norm(hn)
            px = T[:, 0] - F * (T[:, 0] @ F); px /= np.linalg.norm(px)
            tw = math.degrees(math.atan2(np.cross(hn, px) @ F, hn @ px))
            cost = over(phi, dev) + abs(tw - 6) / 90
            if best is None or cost < best[0]:
                best = (cost, over(phi, dev), tw, np.round((E - S) / lu, 2), np.round((W - p[f, I['pelvis']]) * 100).astype(int))
        print(f"f{f} psi {psi:3d}: over {best[1]:4.2f} twist {best[2]:5.0f} elbow {best[3]} wrist {best[4]}")
