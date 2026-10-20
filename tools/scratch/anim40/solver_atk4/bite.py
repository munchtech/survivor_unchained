"""lowest point of the axe (cm above her ground, - = into it) per frame, and the head's travel"""
import sys, json
from pathlib import Path
import numpy as np
ANIM = Path(__file__).resolve().parents[3] / 'anim'
sys.path.insert(0, str(ANIM))
import audit as A
from rig import qrot
sk = A.Skeleton.load(A.DATA / A.SETS[0][2]); I = sk.index
d, rot, pos = A.load(Path(sys.argv[1]) / 'chain_strike.json', sk); g, p = sk.fk(rot, pos)
V = np.array(json.load(open(ANIM / 'data/arms_local.json'))['viking_axe@hand_r']['v'])
gnd = min(p[0, I['ball_l']][1], p[0, I['ball_r']][1]) - 0.035
o = []
for f in range(1, 13):
    W = p[f, I['hand_r']] + np.array([qrot(g[f, I['hand_r']], v) for v in V[::7]])
    k = W[:, 1].argmin(); o.append(f"{f}:{(W[k,1]-gnd)*100:.0f}@{np.round(W[k,[0,2]]*100).astype(int)}")
print(' '.join(o))
