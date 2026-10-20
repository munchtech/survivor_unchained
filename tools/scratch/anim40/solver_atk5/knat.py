"""solver 5a: the natural knuckles (chest frame) of hand_r per frame of a built clip. python knat.py CLIP [--folder DIR]"""
import sys
from pathlib import Path
import numpy as np
ANIM = Path(__file__).resolve().parents[3] / 'anim'
sys.path.insert(0, str(ANIM))
import audit as A
from keyed import Rig, grip_of
from rig import DATA, Skeleton, qmul, qinv, qrot, qaxis
clip = sys.argv[1]; folder = Path(sys.argv[3]) if len(sys.argv) > 3 else ANIM / 'out/clips'
sk = Skeleton.load(DATA / 'heroine_skeleton.json'); rig = Rig(sk, body='her'); I = sk.index
lean = grip_of('axe').get('r', 0.0); lq = qaxis([1.0, 0, 0], -lean) if lean else np.array([0, 0, 0, 1.0])
d, rot, pos = A.load(folder / f'{clip}.json', sk); g, p = sk.fk(rot, pos)
for f in range(rot.shape[0]):
    chest = qmul(g[f, I['spine_03']], qinv(rig.grest[I['spine_03']]))
    W = qmul(g[f, I['hand_r']], lq)
    k = qrot(qinv(chest), qrot(W, [0, 1.0, 0])); b = qrot(qinv(chest), qrot(W, [0, 0, 1.0]))
    print(f, 'knuckles', np.round(k, 3).tolist(), 'blade', np.round(b, 3).tolist())
