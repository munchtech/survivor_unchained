"""Prototype: graft weights matched to the head's over it, faded by distance. python fix.py <in.glb> <out.glb> [D]"""
import sys,os,struct,json; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from scipy.spatial import cKDTree
CUT=0.03; ITERS=int(os.environ.get("IT","4")); SMOOTH=int(os.environ.get("SM","0")); KK=int(os.environ.get("KK","8"))
def match_graft(path,out,D=0.04,d0=0.0,k=KK,sig=0.004):
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
    def G2F(p): return view(p["indices"],{5125:np.uint32,5123:np.uint16}[g["accessors"][p["indices"]]["componentType"]],1)[1].astype(int).reshape(-1,3)
    _,Pg=view(gp["attributes"]["POSITION"],np.float32,3); _,Ph=view(hp["attributes"]["POSITION"],np.float32,3)
    ojg,Jg=view(gp["attributes"]["JOINTS_0"],np.uint8,4); owg,Wg=view(gp["attributes"]["WEIGHTS_0"],np.float32,4)
    _,Jh=view(hp["attributes"]["JOINTS_0"],np.uint8,4); _,Wh=view(hp["attributes"]["WEIGHTS_0"],np.float32,4)
    nj=int(max(Jg.max(),Jh.max()))+1
    def dense(J,W):
        M=np.zeros((len(J),nj)); np.add.at(M,(np.repeat(np.arange(len(J)),4),J.ravel()),W.ravel()); return M
    Pg=Pg.astype(float); Ph=Ph.astype(float)
    N_=g["nodes"]; hi=[i for i,n in enumerate(N_) if n.get("name")=="Head"][0]
    sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); from glb import worlds
    ni=[i for i,n in enumerate(N_) if hi in n.get("children",[])][0]
    up=worlds(g)[ni][:3,:3]@np.array(N_[hi]["translation"]); up/=np.linalg.norm(up)
    skj=g["skins"][0]["joints"]; hj=skj.index(hi)
    Hd=dense(Jh,Wh); Gd=dense(Jg,Wg)
    Sh=Ph-CUT*Hd[:,hj:hj+1]*up
    near,_=cKDTree(Ph).query(Pg)
    t=np.clip((near-d0)/(D-d0),0,1); a=1-(3*t*t-2*t**3)
    sel=a>0
    M=Gd[sel].copy()
    for it in range(ITERS):
        Sg=Pg[sel]-CUT*M[:,hj:hj+1]*up
        r,ix=cKDTree(Sh).query(Sg,k=k)
        q=np.exp(-((r-r[:,:1])/sig)**2); q/=q.sum(1,keepdims=True)
        Wt=np.einsum("vk,vkj->vj",q,Hd[ix])
        M=Gd[sel]*(1-a[sel,None])+Wt*a[sel,None]
    # smoothed over her graft's own edges (the selected points only)
    if SMOOTH:
        Fg=G2F(gp); full=Gd.copy(); full[sel]=M
        Pk=np.round(Pg,6); _,wid=np.unique(Pk,axis=0,return_inverse=True); wid=wid.ravel()
        E=np.r_[Fg[:,[0,1]],Fg[:,[1,2]],Fg[:,[2,0]]]; E=wid[E]
        for it in range(SMOOTH):
            acc=np.zeros((wid.max()+1,nj)); cnt=np.zeros(wid.max()+1)
            np.add.at(acc,E[:,0],full[[np.where(wid==0)[0][0]]*0+0] if False else 0)
            pw=np.zeros((wid.max()+1,nj)); np.add.at(pw,wid,full); pc=np.bincount(wid).astype(float); pw/=pc[:,None]
            np.add.at(acc,E[:,0],pw[E[:,1]]); np.add.at(acc,E[:,1],pw[E[:,0]]); np.add.at(cnt,E[:,0],1); np.add.at(cnt,E[:,1],1)
            sm=0.5*pw+0.5*acc/np.maximum(cnt,1)[:,None]
            full[sel]=sm[wid[sel]]
        M=full[sel]
    top=np.argsort(-M,1)[:,:4]; tw=np.take_along_axis(M,top,1); tw/=tw.sum(1,keepdims=True)
    tw[tw<1e-6]=0; tw/=tw.sum(1,keepdims=True)
    Jn=Jg.copy(); Wn=Wg.copy(); Jn[sel]=top.astype(np.uint8); Wn[sel]=tw.astype(np.float32)
    buf[ojg:ojg+Jn.nbytes]=Jn.tobytes(); buf[owg:owg+Wn.nbytes]=Wn.tobytes()
    open(out,"wb").write(bytes(buf))
    print("GRAFT_MATCH: %d of %d graft points given the head's weights over them (faded to 0 at %.0f mm)"%(sel.sum(),len(Pg),D*1000))
if __name__=="__main__":
    match_graft(sys.argv[1],sys.argv[2],*(float(x) for x in sys.argv[3:]))
