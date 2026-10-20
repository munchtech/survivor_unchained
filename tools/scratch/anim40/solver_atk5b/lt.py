import sys, math
from pathlib import Path
import numpy as np
ANIM = Path(__file__).resolve().parents[3] / 'anim'; sys.path.insert(0, str(ANIM))
import audit as A
from rig import qmatrix
import clips.arts as M
sk = A.Skeleton.load(A.DATA / A.SETS[0][2]); I = sk.index
d, rot, pos = A.load(Path(sys.argv[1]) / 'chain_strike.json', sk); g, p = sk.fk(rot, pos)
R_lr, o_lr = M._left_on_haft()
L = np.linalg.norm(p[0, I['lowerarm_l']] - p[0, I['upperarm_l']]) + np.linalg.norm(p[0, I['hand_l']] - p[0, I['lowerarm_l']])
for f in range(0, 4):
    Rr = qmatrix(g[f, I['hand_r']]); T = p[f, I['hand_r']] + Rr @ o_lr
    print(f, 'reach', round(np.linalg.norm(T - p[f, I['upperarm_l']]) / L, 2), 'Lhand', np.round(p[f, I['hand_l']] * 100), 'T', np.round(T * 100), 'Rhand', np.round(p[f, I['hand_r']] * 100), 'head', np.round(p[f, I['Head']] * 100))
