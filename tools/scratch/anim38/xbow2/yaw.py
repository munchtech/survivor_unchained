import sys
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a6b5a13d0be70144d\tools\anim")
import numpy as np, fistfit as F
from rig import qrot
for n in sys.argv[1:]:
    _,rot,pos=F.load(F.CLIPS/f"{n}.json"); g,p=F.sk.fk(rot,pos)
    h=F.I["hand_r"]; hp=F.I["hips"] if "hips" in F.I else 0
    ys=[];ps=[];hy=[]
    for f in range(len(rot)):
        s=qrot(g[f,h],[0,1.0,0]); fw=qrot(g[f,hp],[0,0,1.0])
        yaw=np.degrees(np.arctan2(s[0],s[2])); fy=np.degrees(np.arctan2(fw[0],fw[2]))
        ys.append(yaw); hy.append(fy); ps.append(np.degrees(np.arcsin(s[1])))
    ys=np.array(ys); hy=np.array(hy)
    print(f"{n}: stock yaw vs world +Z {ys.min():.0f}..{ys.max():.0f} (mean {ys.mean():.0f}); vs hips {np.min(ys-hy):.0f}..{np.max(ys-hy):.0f}; pitch {min(ps):.0f}..{max(ps):.0f}")
