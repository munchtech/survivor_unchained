"""solver 6: the left axe's head as the game shows it (hypothesis: the plain mount's head local (0.03, 0.54, -0.49), the
pinky side; the arms_local hand_l dump carries the right's seat). Pelvis-lateral frame, cm. axl.py clip [hx hy hz]"""
import sys; sys.path.insert(0, '.')
import audit as A, numpy as np
from pathlib import Path
sk = A.Skeleton.load(A.DATA / 'heroine_skeleton.json'); I = sk.index
H = np.array([float(a) for a in sys.argv[2:5]]) if len(sys.argv) > 4 else np.array([-0.03, 0.54, 0.49])
d, rot, pos = A.load(Path('out/clips/' + sys.argv[1] + '.json'), sk); g, p = sk.fk(rot, pos)
for f in range(len(p)):
    pel = p[f, I['pelvis']]; lat = p[f, I['thigh_l']] - p[f, I['thigh_r']]; lat[1] = 0; lat /= np.linalg.norm(lat)
    fw = np.cross(lat, [0, 1, 0]); fw *= -1 if fw[2] < 0 else 1
    def L(q): v = q - pel; return np.array([v @ lat, v[1], v @ fw]) * 100
    h = p[f, I['hand_l']]; hd = h + A.qrot(g[f, I['hand_l']], H)
    print(f"f{f:2d} hand {np.round(L(h)).astype(int)}  head {np.round(L(hd)).astype(int)}  knee_l {np.round(L(p[f, I['calf_l']])).astype(int)}")
