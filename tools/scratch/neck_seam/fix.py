"""Prototype: graft weights matched to the head's over it, faded by distance. python fix.py <in.glb> <out.glb> [D]"""
import sys,os,struct,json; sys.path.insert(0,os.path.dirname(__file__))
import numpy as np
from scipy.spatial import cKDTree
def match_graft(path,out,D=0.04,d0=0.0,k=8,sig=0.004):
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
    _,Pg=view(gp["attributes"]["POSITION"],np.float32,3); _,Ph=view(hp["attributes"]["POSITION"],np.float32,3)
    ojg,Jg=view(gp["attributes"]["JOINTS_0"],np.uint8,4); owg,Wg=view(gp["attributes"]["WEIGHTS_0"],np.float32,4)
    _,Jh=view(hp["attributes"]["JOINTS_0"],np.uint8,4); _,Wh=view(hp["attributes"]["WEIGHTS_0"],np.float32,4)
    nj=int(max(Jg.max(),Jh.max()))+1
    def dense(J,W):
        M=np.zeros((len(J),nj)); np.add.at(M,(np.repeat(np.arange(len(J)),4),J.ravel()),W.ravel()); return M
    T=cKDTree(Ph.astype(float)); r,ix=T.query(Pg.astype(float),k=k)
    near=r[:,0]
    t=np.clip((near-d0)/(D-d0),0,1); a=1-(3*t*t-2*t**3)
    sel=a>0
    q=np.exp(-((r[sel]-r[sel][:,:1])/sig)**2); q/=q.sum(1,keepdims=True)
    Hd=dense(Jh,Wh)
    Wt=np.einsum("vk,vkj->vj",q,Hd[ix[sel]])
    M=dense(Jg[sel],Wg[sel])*(1-a[sel,None])+Wt*a[sel,None]
    top=np.argsort(-M,1)[:,:4]; tw=np.take_along_axis(M,top,1); tw/=tw.sum(1,keepdims=True)
    tw[tw<1e-6]=0; tw/=tw.sum(1,keepdims=True)
    Jn=Jg.copy(); Wn=Wg.copy(); Jn[sel]=top.astype(np.uint8); Wn[sel]=tw.astype(np.float32)
    buf[ojg:ojg+Jn.nbytes]=Jn.tobytes(); buf[owg:owg+Wn.nbytes]=Wn.tobytes()
    open(out,"wb").write(bytes(buf))
    print("GRAFT_MATCH: %d of %d graft points given the head's weights over them (faded to 0 at %.0f mm)"%(sel.sum(),len(Pg),D*1000))
if __name__=="__main__":
    match_graft(sys.argv[1],sys.argv[2],*(float(x) for x in sys.argv[3:]))
