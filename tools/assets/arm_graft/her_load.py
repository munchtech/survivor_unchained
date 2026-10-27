import numpy as np
import os
G=os.environ.get("ARM_GRAFT_WORK", os.path.join(os.environ.get("TEMP","."), "arm_graft"))
os.makedirs(G, exist_ok=True)
def load_her(path=G+r"\her.npz"):
    d=dict(np.load(path))
    ls,lt,lv=d["ls"],d["lt"],d["lv"]
    # triangulate polys (fan) keeping face id and corner (loop) ids
    tri=[];tf=[];tl=[]
    for f,(s,n) in enumerate(zip(ls,lt)):
        for k in range(1,n-1):
            tl.append((s,s+k,s+k+1)); tf.append(f)
    tl=np.array(tl); d["TL"]=tl; d["TF"]=np.array(tf); d["T"]=lv[tl]
    return d
