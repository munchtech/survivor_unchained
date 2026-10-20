cd /c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/anim-40/tools/anim
sed -i "s/^HV_YAW, HV_PITCH, HV_OFF = .*/HV_YAW, HV_PITCH, HV_OFF = $1/" clips/axe.py
python build.py --no-pack axe_heavy > /dev/null
python ../scratch/anim40/solver_atk5b/fk.py axe_heavy out/clips 0,1,2 | cut -c1-75
python -c "
import audit as A, numpy as np, math
from rig import qmatrix
sk=A.Skeleton.load(A.DATA/'heroine_skeleton.json');I=sk.index
_,r,p=A.load(A.Path('out/clips/axe_heavy.json'),sk);g,q=sk.fk(r,p)
gr,_=sk.fk(sk.rest_rot[None].copy(),sk.rest_pos[None].copy())
f=0;pv=q[f,I['pelvis']];fr=q[f,I['foot_r']];fl=q[f,I['foot_l']]
R=qmatrix(g[f,I['spine_03']])@qmatrix(gr[0,I['spine_03']]).T; fw=R@[0,0,1]
print('pelvis-footR xz',((pv-fr)*100)[[0,2]].round(),'chest yaw',round(math.degrees(math.atan2(fw[0],fw[2]))),'pitch',round(math.degrees(math.asin(-fw[1]))), 'hand_r', (q[f,I['hand_r']]*100).round(), 'neck',(q[f,I['neck_01']]*100).round())"
