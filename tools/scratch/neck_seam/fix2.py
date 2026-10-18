"""Prototype 2: the graft under the head (straight up her neck's line) takes the head's weights there, faded by that gap.
python fix2.py <in.glb> <out.glb> [D] [Dnear]"""
import sys,os,struct,json; sys.path.insert(0,os.path.dirname(__file__))
import numpy as np
from scipy.spatial import cKDTree
from glb import trs, worlds
def match_graft(path,out,D=0.04,Dn=0.012):
    d=open(path,"rb").read(); jl=struct.unpack("<I",d[12:16])[0]; g=json.loads(d[20:20+jl])
    b0=20+jl+8; buf=bytearray(d)
    def view(ai,dt,n):
        a=g["accessors"][ai]; bv=g["bufferViews"][a["bufferView"]]; assert not bv.get("byteStride")
        off=b0+bv.get("byteOffset",0)+a.get("byteOffset",0)
        return off,np.frombuffer(d,dt,a["count"]*n,off).reshape(-1,n).copy()
    def prim(mat):
        hit=[p for m in g["meshes"] for p in m["primitives"] if "material" in p and g["materials"][p["material"]].get("name")==mat]
        assert len(hit)==1,mat; return hit[0]
    gp,hp=prim("skin_graft"),prim("skin_head")
    Pg=view(gp["attributes"]["POSITION"],np.float32,3)[1].astype(float); Ph=view(hp["attributes"]["POSITION"],np.float32,3)[1].astype(float)
    F=view(hp["indices"],{5125:np.uint32,5123:np.uint16}[g["accessors"][hp["indices"]]["componentType"]],1)[1].astype(int).reshape(-1,3)
    ojg,Jg=view(gp["attributes"]["JOINTS_0"],np.uint8,4); owg,Wg=view(gp["attributes"]["WEIGHTS_0"],np.float32,4)
    Jh=view(hp["attributes"]["JOINTS_0"],np.uint8,4)[1]; Wh=view(hp["attributes"]["WEIGHTS_0"],np.float32,4)[1]
    # her neck's line: the Head joint's offset from neck_01, in the world
    N=g["nodes"]; W=worlds(g); hi=[i for i,n in enumerate(N) if n.get("name")=="Head"][0]
    ni=[i for i,n in enumerate(N) if hi in n.get("children",[])][0]
    up=W[ni][:3,:3]@np.array(N[hi]["translation"]); up/=np.linalg.norm(up)
    e1=np.cross(up,[0,0,1.0]); e1/=np.linalg.norm(e1); e2=np.cross(up,e1)
    def p2(P): return np.c_[P@e1,P@e2]
    A,B,C=Ph[F[:,0]],Ph[F[:,1]],Ph[F[:,2]]; a2,b2,c2=p2(A),p2(B),p2(C)
    cen=(a2+b2+c2)/3; rad=np.max([np.linalg.norm(x-cen,axis=1) for x in (a2,b2,c2)],0)
    T=cKDTree(cen); g2=p2(Pg); hg=Pg@up
    gap=np.full(len(Pg),np.inf); hitf=np.full(len(Pg),-1); bary=np.zeros((len(Pg),3))
    for v,cand in enumerate(T.query_ball_point(g2,rad.max())):
        if not cand: continue
        c=np.array(cand); v0=b2[c]-a2[c]; v1=c2[c]-a2[c]; w=g2[v]-a2[c]
        den=v0[:,0]*v1[:,1]-v0[:,1]*v1[:,0]; ok=np.abs(den)>1e-14
        s=np.where(ok,(w[:,0]*v1[:,1]-w[:,1]*v1[:,0])/np.where(ok,den,1),-1); t=np.where(ok,(v0[:,0]*w[:,1]-v0[:,1]*w[:,0])/np.where(ok,den,1),-1)
        ins=ok&(s>=0)&(t>=0)&(s+t<=1)
        if not ins.any(): continue
        c,s,t=c[ins],s[ins],t[ins]
        h=(1-s-t)*(A[c]@up)+s*(B[c]@up)+t*(C[c]@up); dz=h-hg[v]
        m=dz>-0.003
        if not m.any(): continue
        k=np.argmin(np.where(m,dz,np.inf)); gap[v]=max(dz[k],0); hitf[v]=c[k]; bary[v]=[1-s[k]-t[k],s[k],t[k]]
    nj=int(max(Jg.max(),Jh.max()))+1
    def dense(J,Wt):
        M=np.zeros((len(J),nj)); np.add.at(M,(np.repeat(np.arange(len(J)),4),J.ravel()),Wt.ravel()); return M
    Hd=dense(Jh,Wh)
    # the head's weights over each graft point (at the hit; else at the nearest head point)
    dn,ixn=cKDTree(Ph).query(Pg)
    Wt=Hd[ixn].copy(); hv=hitf>=0
    Wt[hv]=np.einsum("vk,vkj->vj",bary[hv],Hd[F[hitf[hv]]])
    tr=np.clip(gap/D,0,1); ar=np.where(hv,1-(3*tr*tr-2*tr**3),0)
    tn=np.clip(dn/Dn,0,1); an=1-(3*tn*tn-2*tn**3)
    a=np.maximum(ar,an); sel=a>1e-4
    M=dense(Jg[sel],Wg[sel])*(1-a[sel,None])+Wt[sel]*a[sel,None]
    top=np.argsort(-M,1)[:,:4]; tw=np.take_along_axis(M,top,1); tw[tw<1e-5]=0; tw/=tw.sum(1,keepdims=True)
    Jn=Jg.copy(); Wn=Wg.copy(); Jn[sel]=top.astype(np.uint8); Wn[sel]=tw.astype(np.float32)
    buf[ojg:ojg+Jn.nbytes]=Jn.tobytes(); buf[owg:owg+Wn.nbytes]=Wn.tobytes()
    open(out,"wb").write(bytes(buf))
    print("GRAFT_MATCH: %d of %d graft points take the head's weights over them (%d under it, faded to 0 at a %.0f mm gap; %.0f mm by the seam)"%(sel.sum(),len(Pg),(hv&(ar>0)).sum(),D*1000,Dn*1000))
    return a
if __name__=="__main__":
    match_graft(sys.argv[1],sys.argv[2],*(float(x) for x in sys.argv[3:]))
