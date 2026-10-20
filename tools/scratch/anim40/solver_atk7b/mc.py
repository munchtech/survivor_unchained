"""chain_strike f-range: hipY, feet side spread (ankle x, her space), stag, hands y (r,l), haft pitch (deg below level),
blade lowest y & z (cm), right hand z, seat->blade-low distance, elbows, head pitch (Head fwd vs level; + = chin up), knee y.
python mc.py FOLDER a-b"""
import sys, math, json
from pathlib import Path
import numpy as np
ANIM = Path(r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\anim-40\tools\anim'); sys.path.insert(0, str(ANIM))
import audit as A
from rig import qmatrix
import clips.arts as M
sk = A.Skeleton.load(A.DATA / A.SETS[0][2]); I = sk.index
d, rot, pos = A.load(Path(sys.argv[1]) / 'chain_strike.json', sk); g, p = sk.fk(rot, pos)
fa, fb = map(int, sys.argv[2].split('-'))
C, H, N, Wd = M._haft()
v = np.array(json.load(open(ANIM / 'data/arms_local.json'))['viking_axe@hand_r']['v'])
def J(f, n): return p[f, I[n]]
def ang(a, b, c):
    u, w = a - b, c - b; return math.degrees(math.acos(np.clip(u @ w / np.linalg.norm(u) / np.linalg.norm(w), -1, 1)))
# head local forward axis: use rest Head orientation; take Head->(Head + R@fwd) where fwd = rest-space +z mapped
gr = A.Skeleton.load(A.DATA / A.SETS[0][2])
print(' f hipY sprd stag  hRy hLy pitch  bladeY bladeZ hRz  L   elL elR kneeL kneeR headPitch')
for f in range(fa, fb + 1):
    Rr = qmatrix(g[f, I['hand_r']]); W = J(f,'hand_r') + (Rr @ v.T).T
    lo = W[W[:,1].argmin()]
    ad = Rr @ H; pitch = math.degrees(math.asin(-ad[1])) * (1 if ad[2] > 0 else 1)
    Lr = np.linalg.norm(lo - J(f,'hand_r'))
    el = [ang(J(f, 'upperarm_' + s), J(f, 'lowerarm_' + s), J(f, 'hand_' + s)) for s in 'lr']
    Rh = qmatrix(g[f, I['Head']]); 
    # face forward = Head's axis closest to world +z at f0? computed once
    if f == fa:
        R0 = qmatrix(g[0, I['Head']]); ax = np.argmax(np.abs(R0.T @ np.array([0,0,1.0]))); sg = np.sign((R0.T @ np.array([0,0,1.0]))[ax])
    fw = Rh[:, ax] * sg; hp = math.degrees(math.asin(fw[1]))
    print(f"{f:2d} {J(f,'pelvis')[1]*100:4.0f} {abs(J(f,'foot_l')[0]-J(f,'foot_r')[0])*100:4.0f} {(J(f,'foot_l')[2]-J(f,'foot_r')[2])*100:4.0f} {J(f,'hand_r')[1]*100:4.0f} {J(f,'hand_l')[1]*100:3.0f} {pitch:5.1f}  {lo[1]*100:5.1f} {lo[2]*100:5.0f} {J(f,'hand_r')[2]*100:4.0f} {Lr*100:4.0f} {el[0]:4.0f} {el[1]:4.0f} {J(f,'calf_l')[1]*100:4.0f} {J(f,'calf_r')[1]*100:4.0f} {hp:5.0f}")
