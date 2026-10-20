"""chest-frame blade/knuckles for hand_r so the wand points along DIR at frame f: python rot.py FOLDER f dx,dy,dz"""
import sys, math, json
from pathlib import Path
import numpy as np
ANIM = Path(__file__).resolve().parents[3] / 'anim'; sys.path.insert(0, str(ANIM))
import audit as A
from rig import qmatrix, qmul, qinv
sk = A.Skeleton.load(A.DATA / 'heroine_skeleton.json'); I = sk.index
V=np.array(json.load(open(ANIM/'data/arms_local.json'))['wand@hand_r']['v']); c=V.mean(0); W=np.linalg.svd(V-c)[2][0]; W=W*np.sign(W@(V[np.linalg.norm(V,axis=1).argmax()]-c))
d, rot, pos = A.load(Path(sys.argv[1]) / 'cast_flick.json', sk); g, p = sk.fk(rot, pos)
f = int(sys.argv[2]); t = np.array([float(x) for x in sys.argv[3].split(',')]); t /= np.linalg.norm(t)
R = qmatrix(g[f, I['hand_r']]); cur = R @ W
ax = np.cross(cur, t); sn = np.linalg.norm(ax); cs = cur @ t
K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]]) / max(sn, 1e-9)
Rm = np.eye(3) + sn * K + (1 - cs) * K @ K
Rn = Rm @ R
# the rig's grip offset: keyed blade is the hand's +Z after the grip turn? report both raw
ch = qmatrix(qmul(g[f, I['spine_03']], qinv(sk.rest_globals()[0][0][I['spine_03']])))
Ci = ch.T
print('blade', np.round(Ci @ Rn[:, 2], 3).tolist(), 'knuckles', np.round(Ci @ Rn[:, 1], 3).tolist(), 'cur', np.round(cur, 2).tolist())
