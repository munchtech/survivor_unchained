import sys
sys.path.insert(0, r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa4f5fc266b043035\tools\anim')
import numpy as np
from retarget import Source

step = 3
for f in sys.argv[1:]:
    if f.startswith('step='):
        step = int(f[5:])
        continue
    src, _, name = f.rpartition('/')
    src = src or 'mixamo'
    prof = {'mixamo': 'mixamo', 'kimodo': 'soma'}[src]
    s = Source(rf'C:/Users/munch/Tools/mocap/{src}/{name}.bvh', profile=prof)
    P = s.profile
    h = s.pos[:, s.joint('Hips')]
    la = s.pos[:, s.joint(P['ankle'][0])]; ra = s.pos[:, s.joint(P['ankle'][1])]
    lhn = 'LeftHand'; rhn = 'RightHand'
    lh = s.pos[:, s.joint(lhn)]; rh = s.pos[:, s.joint(rhn)]
    print(f, s.pos.shape[0] / 30, 's')
    for t in range(0, s.pos.shape[0], step):
        print(f"  {t/30:5.2f} hips {h[t,0]:6.2f} {h[t,1]:5.2f} {h[t,2]:6.2f}  feet L{la[t,1]:5.2f} R{ra[t,1]:5.2f}  "
              f"hands L({lh[t,0]-h[t,0]:5.2f},{lh[t,1]:5.2f},{lh[t,2]-h[t,2]:5.2f}) R({rh[t,0]-h[t,0]:5.2f},{rh[t,1]:5.2f},{rh[t,2]-h[t,2]:5.2f})")
