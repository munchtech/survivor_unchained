import sys, json, math
from pathlib import Path
import numpy as np
ANIM = Path(__file__).resolve().parents[3] / 'anim'; sys.path.insert(0, str(ANIM))
import audit as A
from rig import qmatrix
sk=A.Skeleton.load(A.DATA/'heroine_skeleton.json');I=sk.index
arms = json.load(open(ANIM / 'data/arms_local.json'))
v = np.array(arms['viking_axe@hand_l']['v']); r = np.linalg.norm(v, axis=1); far = v[r > r.max() - 0.12].mean(0)
_,rr,pp=A.load(ANIM/'out/clips/axes_right.json',sk);g,q=sk.fk(rr,pp)
gr,_=sk.fk(sk.rest_rot[None].copy(),sk.rest_pos[None].copy())
for f in map(int, sys.argv[1].split(',')):
  R=qmatrix(g[f,I['spine_03']])@qmatrix(gr[0,I['spine_03']]).T
  hd=A.qrot(g[f,I['hand_l']],far); hd/=np.linalg.norm(hd)
  off=q[f,I['hand_l']]-q[f,I['upperarm_l']]
  print(f, 'chest-frame off', np.round(R.T@off,3), 'haft', np.round(R.T@hd,2))
if len(sys.argv)>2:
  f=int(sys.argv[2]); R=qmatrix(g[f,I['spine_03']])@qmatrix(gr[0,I['spine_03']]).T
  for w in sys.argv[3:]:
    print('world', w, '-> chest', np.round(R.T@np.array(eval(w),float),3))
