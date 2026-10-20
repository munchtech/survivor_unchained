"""chain_strike per-frame measures. python cm.py FOLDER [frames a-b]
cm, her space (x left, y up, z fwd). hipY pelvis height; lo = lowest of knees/hands (y); kneeY l/r;
tor = pelvis->neck tilt from vertical; hd = Head y minus shoulder-mid y; elL/elR elbow deg; kn l/r knee deg;
ksp = knee spread minus ankle spread (+ = knees out); lf = left channel pt to haft axis mm / angle deg;
fl = |flat.cam| ; hz = axe head y; ft = foot_l, foot_r xz"""
import sys, math
from pathlib import Path
import numpy as np
ANIM = Path(__file__).resolve().parents[3] / 'anim'
sys.path.insert(0, str(ANIM))
import audit as A
from rig import qmatrix
import clips.arts as M
sk = A.Skeleton.load(A.DATA / A.SETS[0][2]); I = sk.index
d, rot, pos = A.load(Path(sys.argv[1]) / 'chain_strike.json', sk); g, p = sk.fk(rot, pos)
fa, fb = (map(int, sys.argv[2].split('-')) if len(sys.argv) > 2 else (0, rot.shape[0] - 1))
C, H, N, Wd = M._haft()
lc, lh, ln = M.L_CHANNEL; lh = lh / np.linalg.norm(lh)
ca, cp = math.radians(45), math.radians(20)
cam = np.array([math.sin(ca) * math.cos(cp), math.sin(cp), math.cos(ca) * math.cos(cp)])
import json
arms = json.load(open(ANIM / 'data/arms_local.json'))
v = np.array(arms['viking_axe@hand_r']['v']); r = np.linalg.norm(v, axis=1); head_l = v[r > r.max() - 0.12].mean(0)
def J(f, n): return p[f, I[n]]
def ang(a, b, c):
    u, w = a - b, c - b; return math.degrees(math.acos(np.clip(u @ w / np.linalg.norm(u) / np.linalg.norm(w), -1, 1)))
print(' f hipY  lo  knL knR  tor   hd  elL elR  knl knr  ksp  lf(mm/deg) fl   hz  footL(x,z) footR(x,z)  ballL ballR')
for f in range(fa, fb + 1):
    lo = min(J(f, 'calf_l')[1], J(f, 'calf_r')[1], J(f, 'hand_l')[1], J(f, 'hand_r')[1])
    tv = J(f, 'neck_01') - J(f, 'pelvis'); tor = math.degrees(math.atan2(math.hypot(tv[0], tv[2]), tv[1]))
    hd = J(f, 'Head')[1] - (J(f, 'upperarm_l')[1] + J(f, 'upperarm_r')[1]) / 2
    el = [ang(J(f, 'upperarm_' + s), J(f, 'lowerarm_' + s), J(f, 'hand_' + s)) for s in 'lr']
    kn = [ang(J(f, 'thigh_' + s), J(f, 'calf_' + s), J(f, 'foot_' + s)) for s in 'lr']
    ksp = (abs(J(f, 'calf_l')[0] - J(f, 'calf_r')[0]) - abs(J(f, 'foot_l')[0] - J(f, 'foot_r')[0]))
    Rr = qmatrix(g[f, I['hand_r']]); Rl = qmatrix(g[f, I['hand_l']])
    a0 = p[f, I['hand_r']] + Rr @ C; ad = Rr @ H
    q = p[f, I['hand_l']] + Rl @ lc; dq = q - a0; dist = np.linalg.norm(dq - ad * (dq @ ad)) * 1000
    lang = math.degrees(math.acos(min(1, abs((Rl @ lh) @ ad))))
    fl = abs((Rr @ N) @ cam); hz = (p[f, I['hand_r']] + Rr @ head_l)[1]
    print(f"{f:2d} {J(f,'pelvis')[1]*100:4.0f} {lo*100:4.0f} {J(f,'calf_l')[1]*100:4.0f} {J(f,'calf_r')[1]*100:4.0f} {tor:4.0f} {hd*100:5.1f} {el[0]:4.0f} {el[1]:4.0f} {kn[0]:4.0f} {kn[1]:4.0f} {ksp*100:5.1f} {dist:5.1f}/{lang:4.1f} {fl:.2f} {hz*100:4.0f}"
          f"  {J(f,'foot_l')[0]*100:4.0f},{J(f,'foot_l')[2]*100:4.0f}  {J(f,'foot_r')[0]*100:4.0f},{J(f,'foot_r')[2]*100:4.0f}  {J(f,'ball_l')[1]*100:3.0f} {J(f,'ball_r')[1]*100:3.0f}")
