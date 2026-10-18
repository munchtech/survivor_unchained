"""Poke-through of the graft out of the head in head turns. python motion.py <a.glb>:<uncut_m> ..."""
import sys,os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from glb import *
from scipy.spatial import cKDTree
def qmul(a,b):
    x1,y1,z1,w1=a; x2,y2,z2,w2=b
    return [w1*x2+x1*w2+y1*z2-z1*y2, w1*y2-x1*z2+y1*w2+z1*x2, w1*z2+x1*y2-y1*x2+z1*w2, w1*w2-x1*x2-y1*y2-z1*z2]
def aq(ax,deg):
    import math; h=math.radians(deg)/2; v=[0,0,0]; v[ax]=math.sin(h); return v+[math.cos(h)]
import os as _o
POSES=[("rest",[])]+([("H%s%+d"%("xyz"[ax],dg),[("Head",ax,dg)]) for ax,dgs in ((0,(-20,20)),(1,(-45,45)),(2,(-15,15))) for dg in dgs]+[("N+H x%+d y%+d"%(dx,dy),[("neck_01",0,dx/2),("Head",0,dx/2),("neck_01",1,dy/2),("Head",1,dy/2)]) for dx in (-20,20) for dy in (-45,45)] if _o.environ.get("MOD") else [])
if not _o.environ.get("MOD"): POSES+=[]
_FULL=not _o.environ.get("MOD")
POSES=POSES if not _FULL else [("rest",[])]+[("H%s%+d"%("xyz"[ax],dg),[("Head",ax,dg)]) for ax in range(3) for dg in (-40,40)]+\
      [("N+H x%+d y%+d"%(dx,dy),[("neck_01",0,dx/2),("Head",0,dx/2),("neck_01",1,dy/2),("Head",1,dy/2)]) for dx in (-40,40) for dy in (-60,60)] if _FULL else POSES
def run(path,uncut):
    G_=G(path); g=G_.g; N=g["nodes"]
    base={i:dict(n) for i,n in enumerate(N)}
    if uncut:
        h=[n for n in N if n.get("name")=="Head"][0]; t=np.array(h["translation"]); L=np.linalg.norm(t); h["translation"]=list(t*(L+uncut)/L)
    res=[]
    rot0={i:list(N[i].get("rotation",[0,0,0,1])) for i in range(len(N))}
    for nm,ops in POSES:
        for i in range(len(N)): N[i]["rotation"]=list(rot0[i])
        for jn,ax,dg in ops:
            i=[k for k,n in enumerate(N) if n.get("name")==jn][0]; N[i]["rotation"]=qmul(N[i]["rotation"],aq(ax,dg))
        body=skinned(G_,84); head=skinned(G_,86)[0]; gr=body[1]
        # normals: skin the rest normals with the same matrices (rotation part)
        W=worlds(g); sk=g["skins"][0]; ibm=G_.acc(sk["inverseBindMatrices"]).reshape(-1,4,4).transpose(0,2,1)
        J=np.array([W[j]@ibm[k] for k,j in enumerate(sk["joints"])])
        Mh=np.einsum("vk,vkab->vab",head["w"],J[head["j"]])[:,:3,:3]
        nh=np.einsum("vab,vb->va",Mh,G_.acc(head["prim"]["attributes"]["NORMAL"]).astype(float)); nh/=np.linalg.norm(nh,axis=1,keepdims=True)
        d,ix=cKDTree(head["skin"]).query(gr["skin"]); s=np.einsum("ij,ij->i",gr["skin"]-head["skin"][ix],nh[ix]); c=d<0.02
        res.append((nm,(c&(s>0.0005)).sum(),(c&(s>0.001)).sum(),(c&(s>0.002)).sum(),s[c].max()*1e3))
    return res
if __name__=="__main__":
    cols=[run(*(a.split("|")[0],float(a.split("|")[1]))) for a in sys.argv[1:]]
    print("%-16s"%"pose"+"".join(" | %-24s"%os.path.basename(a)[:24] for a in sys.argv[1:]))
    for k in range(len(POSES)):
        print("%-16s"%cols[0][k][0]+"".join(" | >.5:%3d >1:%3d >2:%3d %4.1f"%c[k][1:] for c in cols))
