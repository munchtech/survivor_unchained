"""stance/arm numbers: python fk.py CLIP FOLDER frames(comma)
spread = ankle x distance, stag = ankle z distance (cm); knee = bend deg (0 straight); hipY; pelvis z vs feet mid (weight fwd +);
elR/elL elbow deg (180 straight); wand = right hand blade (+Z) pitch below horizontal; hl = left hand from left hip joint (x out,y,z)"""
import sys, math
from pathlib import Path
import numpy as np
ANIM = Path(__file__).resolve().parents[3] / 'anim'; sys.path.insert(0, str(ANIM))
import audit as A
from rig import qmatrix
import json
V=np.array(json.load(open(ANIM/'data/arms_local.json'))['wand@hand_r']['v']); c=V.mean(0); W=np.linalg.svd(V-c)[2][0]; W=W*np.sign(W@(V[np.linalg.norm(V,axis=1).argmax()]-c)); TIP=V[np.linalg.norm(V,axis=1).argmax()]
sk = A.Skeleton.load(A.DATA / 'heroine_skeleton.json'); I = sk.index
d, rot, pos = A.load(Path(sys.argv[2]) / f'{sys.argv[1]}.json', sk); g, p = sk.fk(rot, pos)
def J(f, n): return p[f, I[n]]
def ang(a, b, c):
    u, w = a - b, c - b; return math.degrees(math.acos(np.clip(u @ w / np.linalg.norm(u) / np.linalg.norm(w), -1, 1)))
for f in map(int, sys.argv[3].split(',')):
    kn = [180 - ang(J(f, 'thigh_' + s), J(f, 'calf_' + s), J(f, 'foot_' + s)) for s in 'lr']
    el = [ang(J(f, 'upperarm_' + s), J(f, 'lowerarm_' + s), J(f, 'hand_' + s)) for s in 'lr']
    fm = (J(f, 'foot_l') + J(f, 'foot_r')) / 2
    R = qmatrix(g[f, I['hand_r']]); bz = R @ W; wand = math.degrees(math.asin(-bz[1])); tip = J(f,'hand_r') + R @ TIP; hat = J(f,'Head')
    hl = J(f, 'hand_l') - J(f, 'thigh_l')
    print(f"f{f}: spread {abs(J(f,'foot_l')[0]-J(f,'foot_r')[0])*100:.0f} stag {(J(f,'foot_l')[2]-J(f,'foot_r')[2])*100:.0f} knee L{kn[0]:.0f} R{kn[1]:.0f} hipY {J(f,'pelvis')[1]*100:.0f} wfwd {(J(f,'pelvis')[2]-fm[2])*100:.0f} | elL {el[0]:.0f} elR {el[1]:.0f} wand {wand:.0f} dir {np.round(bz,2).tolist()} tip-head {np.round((tip-hat)*100).astype(int).tolist()} | hl {np.round(hl*100).astype(int).tolist()}")
