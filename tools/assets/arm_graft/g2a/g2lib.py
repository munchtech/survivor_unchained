# G2a lib: blend dump (Z-up) <-> Body (glb Y-up), proxy overrides, helper split.
import os,sys,numpy as np
from scipy.spatial import cKDTree
WT=r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\armor-7"
sys.path.insert(0,WT+r"\tools\anim")
HERE=os.path.dirname(os.path.abspath(__file__))
def glb(p): p=np.asarray(p); return np.c_[p[...,0],p[...,2],-p[...,1]]
def blendv(p): p=np.asarray(p); return np.c_[p[...,0],-p[...,2],p[...,1]]
def load_dump(path=HERE+r"\g1d.npz"):
    d=dict(np.load(path)); ls,lt,lv=d["ls"],d["lt"],d["lv"]
    d["polys"]=[lv[s:s+n] for s,n in zip(ls,lt)]
    e=[]
    for p in d["polys"]:
        n=len(p); e+= [(p[k],p[(k+1)%n]) for k in range(n)]
    e=np.array(e); e.sort(1); d["E"]=np.unique(e,axis=0)
    d["heads"]={str(n):h for n,h in zip(d["bn"],d["bh"])}
    d["names"]=[str(x) for x in d["names"]]
    return d
def body_map(b,d):
    """b's Heroine vertex k -> dump vertex m (by position)."""
    hk=np.nonzero(b.piece=="Heroine")[0]
    dist,m=cKDTree(glb(d["P"])).query(b.P[hk])
    return hk,m,dist
def split_glb(b,Wn,names,Pg):
    """blend-group weights Wn [n, len(names)] at glb points Pg -> top-4 (J,W) in b.sk index after the helper split."""
    import helpers as hp
    I=b.sk.index; Wf=np.zeros((len(Wn),len(b.sk.names)))
    for j,n in enumerate(names):
        if n in I: Wf[:,I[n]]+=Wn[:,j]
    heads={n:b.rest[i][:3,3] for n,i in I.items()}
    Wf=hp.split(Wf,Pg,I,heads,front=(0.0,0.0,1.0))
    J=np.argsort(-Wf,1)[:,:4]; W=np.take_along_axis(Wf,J,1); W/=np.maximum(W.sum(1,keepdims=True),1e-12)
    return J,W
def apply_proxy(b,d,P=None,VG=None,changed=None,ref=None):
    """Override b in memory with dump-space positions P and weights VG at `changed` dump verts."""
    hk,m,dist=ref if ref is not None else body_map(b,d)
    sel=changed[m]&(dist<5e-3)
    k=hk[sel]; mm=m[sel]
    if P is not None: b.P[k]=b.P[k]+glb(P[mm]-d["P"][mm])
    if VG is not None:
        J,W=split_glb(b,VG[mm],d["names"],b.P[k]); b.J[k]=J; b.W[k]=W
    return len(k)
def split_full(b,Wn,names,Pg):
    import helpers as hp
    I=b.sk.index; Wf=np.zeros((len(Wn),len(b.sk.names)))
    for j,n in enumerate(names):
        if n in I: Wf[:,I[n]]+=Wn[:,j]
    heads={n:b.rest[i][:3,3] for n,i in I.items()}
    return hp.split(Wf,Pg,I,heads,front=(0.0,0.0,1.0))
def tri_polys(polys):
    T=[]
    for p in polys:
        for k in range(1,len(p)-1): T.append((p[0],p[k],p[k+1]))
    return np.array(T)
def dbody(b0,P,polys,VG,names):
    """b0 with its Heroine piece replaced by a dump-like mesh (blend coords P, polys, blend-group weights VG)."""
    import copy, helpers as hp
    b=copy.copy(b0); keep=np.nonzero(b0.piece!="Heroine")[0]
    Pg=glb(P); Wf=split_full(b0,VG,names,Pg)
    J=np.argsort(-Wf,1)[:,:4]; W=np.take_along_axis(Wf,J,1); W/=np.maximum(W.sum(1,keepdims=True),1e-12)
    n=len(Pg); remap=-np.ones(len(b0.P),int); remap[keep]=n+np.arange(len(keep))
    b.P=np.r_[Pg,b0.P[keep]]; b.J=np.r_[J,b0.J[keep]]; b.W=np.r_[W,b0.W[keep]]
    b.piece=np.r_[np.array(["Heroine"]*n,dtype=b0.piece.dtype),b0.piece[keep]]
    b.kind=np.r_[np.array(["skin"]*n,dtype=b0.kind.dtype),b0.kind[keep]]
    Th=b0.T[(b0.piece[b0.T]!="Heroine").all(1)]
    b.T=np.r_[tri_polys(polys),remap[Th]]
    Wfull=np.zeros((len(b.P),len(b0.sk.names))); Wfull[:n]=Wf
    r=np.arange(len(keep))[:,None].repeat(4,1); np.add.at(Wfull,(n+r,b0.J[keep]),b0.W[keep])
    C=hp.corrective(b.P,Wfull,b0.sk)
    b.corr={k:v for k,v in C.items() if k in b0.corr}; b.corrN={k:np.zeros_like(v) for k,v in b.corr.items()}
    for a in ("Tw","wid","EP","EF","far","rep","nW"):
        if hasattr(b,a): delattr(b,a)
    return b
