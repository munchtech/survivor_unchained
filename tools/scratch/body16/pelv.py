import sys, math, numpy as np
sys.path.insert(0, 'tools/scratch/body16'); sys.argv=[sys.argv[0],'--fast','--clips=none']
import hang as h
b = h.ac.Body.heroine()
I=b.sk.index
for n in ['idle_warden_town','walk_warden_town','run_warden_town','idle_reaver_town','walk_reaver_town']:
    Gs=b.frames(b.clip(n)); tw=[];sx=[];sz=[]
    for G in Gs:
        R=G[I['pelvis']][:3,:3]; R=R/np.linalg.norm(R,axis=0)
        s,t=h.split(h.quat(R@h.rotx(20.6).T))
        tw.append(math.degrees(2*math.atan2(t[2],t[0]))); sx.append(math.degrees(2*s[1])); sz.append(math.degrees(2*s[3]))
    f=lambda a:f"{min(a):6.1f}..{max(a):6.1f}"
    print(f"{n:20} yaw {f(tw)}  pitch {f(sx)}  roll {f(sz)}  frames {len(Gs)}")
