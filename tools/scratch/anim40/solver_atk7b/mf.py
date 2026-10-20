"""cast_flick measures, her own frame (pelvis-yaw-free: uses world, she faces +z). python mf.py FOLDER frames
uaL = left upper arm angle from her torso-down axis (deg); elL/elR elbow deg; hL = left hand rel thigh_l (x out,y,z fwd) cm;
hRy = right hand height minus spine_03 (cm; lower chest ~ -5..-10); hRz fwd of spine_03; shR = right shoulder z minus left (cm, + = forward);
wand = blade pitch below level (deg); tipHat = min distance wand segment to Head (cm, hat brim r~30)"""
import sys, math, json
from pathlib import Path
import numpy as np
ANIM = Path(r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\anim-40\tools\anim'); sys.path.insert(0, str(ANIM))
import audit as A
from rig import qmatrix
V=np.array(json.load(open(ANIM/'data/arms_local.json'))['wand@hand_r']['v']); c=V.mean(0); W=np.linalg.svd(V-c)[2][0]; W=W*np.sign(W@(V[np.linalg.norm(V,axis=1).argmax()]-c)); TIP=V[np.linalg.norm(V,axis=1).argmax()]
sk = A.Skeleton.load(A.DATA / 'heroine_skeleton.json'); I = sk.index
d, rot, pos = A.load(Path(sys.argv[1]) / f'{sys.argv[3] if len(sys.argv)>3 else "cast_flick"}.json', sk); g, p = sk.fk(rot, pos)
def J(f, n): return p[f, I[n]]
def ang(a, b, c):
    u, w = a - b, c - b; return math.degrees(math.acos(np.clip(u @ w / np.linalg.norm(u) / np.linalg.norm(w), -1, 1)))
fr = range(rot.shape[0]) if sys.argv[2]=='all' else map(int, sys.argv[2].split(','))
for f in fr:
    down = J(f,'pelvis') - J(f,'neck_01'); down/=np.linalg.norm(down)
    ua = J(f,'lowerarm_l')-J(f,'upperarm_l'); uaL = math.degrees(math.acos(ua@down/np.linalg.norm(ua))); sd = J(f,'upperarm_l')-J(f,'upperarm_r'); sd-=down*(sd@down); sd/=np.linalg.norm(sd); uaX = math.degrees(math.atan2(ua@sd, ua@down)); el_out=(J(f,'lowerarm_l')-J(f,'upperarm_l'))@sd*100
    el = [ang(J(f, 'upperarm_' + s), J(f, 'lowerarm_' + s), J(f, 'hand_' + s)) for s in 'lr']
    hl = J(f,'hand_l')-J(f,'thigh_l')
    s3 = J(f,'spine_03'); hr = J(f,'hand_r')-s3
    sh = (J(f,'upperarm_r')[2]-J(f,'upperarm_l')[2])*100
    R = qmatrix(g[f, I['hand_r']]); bz = R @ W; wand = math.degrees(math.asin(-bz[1]))
    a = J(f,'hand_r'); b = a + R @ TIP; h = J(f,'Head') + np.array([0,0.1,0])
    ts = np.linspace(0,1,20); dmin = min(np.linalg.norm(a+(b-a)*t-h) for t in ts)
    print(f"f{f:2d} uaL {uaL:3.0f} side {uaX:3.0f} elL {el[0]:3.0f} hL {np.round(hl*100).astype(int).tolist()} | elR {el[1]:3.0f} hRy {hr[1]*100:4.0f} hRz {hr[2]*100:3.0f} hRx {hr[0]*100:4.0f} shR {sh:3.0f} wand {wand:4.0f} tipHat {dmin*100:3.0f}")
