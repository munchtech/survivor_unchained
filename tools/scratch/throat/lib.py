import sys; sys.path.insert(0,"C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a1941eef2c79c45fe/tools/scratch/neck_seam")
from glb import *
from scipy.spatial import cKDTree
def load(path):
    G_=G(path); g=G_.g
    pr=g["meshes"][g["nodes"][84]["mesh"]]["primitives"][:2]
    P=[];T=[];o=0
    for p in pr:
        x=G_.acc(p["attributes"]["POSITION"]).astype(float); P.append(x); T.append(G_.acc(p["indices"]).reshape(-1,3).astype(int)+o); o+=len(x)
    P=np.concatenate(P); T=np.concatenate(T)
    u,inv=np.unique(np.round(P/1e-5).astype(np.int64),axis=0,return_index=False,return_inverse=True)
    inv=inv.ravel(); n=inv.max()+1
    U=np.zeros((n,3)); U[inv]=P
    Tw=inv[T]; Tw=Tw[(Tw[:,0]!=Tw[:,1])&(Tw[:,1]!=Tw[:,2])&(Tw[:,0]!=Tw[:,2])]
    hp=g["meshes"][g["nodes"][86]["mesh"]]["primitives"][0]
    H=G_.acc(hp["attributes"]["POSITION"]).astype(float)
    return G_,P,inv,U,Tw,H
def vn(U,T):
    f=np.cross(U[T[:,1]]-U[T[:,0]],U[T[:,2]]-U[T[:,0]]); n=np.zeros_like(U)
    for k in range(3): np.add.at(n,T[:,k],f)
    return n/np.maximum(np.linalg.norm(n,axis=1,keepdims=True),1e-12)
AX=np.array([0,0,-0.045])
def cyl(U):
    th=np.degrees(np.arctan2(U[:,0],U[:,2]-AX[2])); r=np.hypot(U[:,0],U[:,2]-AX[2]); return th,r
def mls(U,Nn,idx,R=0.03,sig=0.012,deg=2):
    """project U[idx] on a weighted quadric height field fitted over neighbours within R (about the point's normal)."""
    tr=cKDTree(U); out=np.zeros((len(idx),3)); res=np.zeros(len(idx))
    for k,i in enumerate(idx):
        nb=tr.query_ball_point(U[i],R); Q=U[nb]-U[i]
        n=Nn[nb].mean(0); n/=np.linalg.norm(n)
        a=np.cross(n,[1,0,0]); 
        if np.linalg.norm(a)<0.3: a=np.cross(n,[0,1,0])
        a/=np.linalg.norm(a); b=np.cross(n,a)
        u,v,h=Q@a,Q@b,Q@n
        w=np.exp(-(u*u+v*v)/(2*sig*sig))
        A=np.c_[np.ones_like(u),u,v,u*u,u*v,v*v] if deg==2 else np.c_[np.ones_like(u),u,v]
        sw=np.sqrt(w); c=np.linalg.lstsq(A*sw[:,None],h*sw,rcond=None)[0]
        res[k]=-c[0]; out[k]=U[i]+c[0]*n
    return out,res
