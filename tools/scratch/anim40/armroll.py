"""Chest roll, the right arm against world vertical, and the right hand out from the right hip, per town idle."""
import sys,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/"tools"/"anim"))
import numpy as np
from skin import Body
b=Body.heroine(jiggle=False,helpers=True);I=b.sk.index
for name in sys.argv[1:]:
    c=b.clip(name);n=c.frames
    rows=[]
    for f in range(n):
        G=b.globals(c,f);P=lambda k:G[I[k]][:3,3]
        sh=P("upperarm_r")-P("upperarm_l"); roll=math.degrees(math.atan2(sh[1],-sh[0]))
        a=P("hand_r")-P("upperarm_r"); wabd=math.degrees(math.atan2(-a[0],-a[1]))
        rows.append((roll,wabd,-(P("hand_r")[0]-P("thigh_r")[0]),P("hand_r")[1]-P("thigh_r")[1]))
    r=np.array(rows); q=[int(n*k/4) for k in range(4)]
    print(name,"chest roll %.1f..%.1f"%(r[:,0].min(),r[:,0].max()),"| arm vs vertical %.1f..%.1f"%(r[:,1].min(),r[:,1].max()),
          "| hand out of hip joint (cm) "+"/".join("%.0f"%(100*r[i,2]) for i in q),"| hand below hip joint "+"/".join("%.0f"%(100*r[i,3]) for i in q))
