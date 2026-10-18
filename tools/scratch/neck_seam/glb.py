import json, struct, numpy as np
CT={5126:np.float32,5123:np.uint16,5121:np.uint8,5125:np.uint32}
NC={"SCALAR":1,"VEC2":2,"VEC3":3,"VEC4":4,"MAT4":16}
class G:
    def __init__(s,p):
        d=open(p,"rb").read(); jl=struct.unpack("<I",d[12:16])[0]
        s.g=json.loads(d[20:20+jl]); s.bin=d[20+jl+8:]
    def acc(s,i):
        a=s.g["accessors"][i]; bv=s.g["bufferViews"][a["bufferView"]]
        dt=CT[a["componentType"]]; n=NC[a["type"]]
        off=bv.get("byteOffset",0)+a.get("byteOffset",0)
        st=bv.get("byteStride",0); isz=np.dtype(dt).itemsize*n
        if st and st!=isz:
            raw=np.frombuffer(s.bin,np.uint8,a["count"]*st,off).reshape(a["count"],st)[:,:isz].copy()
            x=raw.view(dt).reshape(a["count"],n)
        else:
            x=np.frombuffer(s.bin,dt,a["count"]*n,off).reshape(a["count"],n)
        if a.get("normalized"): x=x.astype(np.float32)/np.iinfo(dt).max
        return x
def trs(n):
    M=np.eye(4)
    if "matrix" in n: return np.array(n["matrix"]).reshape(4,4).T
    t=n.get("translation",[0,0,0]); r=n.get("rotation",[0,0,0,1]); sc=n.get("scale",[1,1,1])
    x,y,z,w=r
    R=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
    M[:3,:3]=R*np.array(sc); M[:3,3]=t; return M
def worlds(g):
    N=g["nodes"]; par={}
    for i,n in enumerate(N):
        for c in n.get("children",[]): par[c]=i
    W={}
    def w(i):
        if i in W: return W[i]
        m=trs(N[i]); W[i]=(w(par[i])@m) if i in par else m; return W[i]
    for i in range(len(N)): w(i)
    return W
def skinned(G_,meshnode):
    g=G_.g; W=worlds(g); n=g["nodes"][meshnode]; sk=g["skins"][n["skin"]]
    ibm=G_.acc(sk["inverseBindMatrices"]).reshape(-1,4,4).transpose(0,2,1)
    J=np.array([W[j]@ibm[k] for k,j in enumerate(sk["joints"])])
    out=[]
    for p in g["meshes"][n["mesh"]]["primitives"]:
        a=p["attributes"]; P=G_.acc(a["POSITION"]).astype(float)
        jj=G_.acc(a["JOINTS_0"]).astype(int); ww=G_.acc(a["WEIGHTS_0"]).astype(float)
        Ph=np.c_[P,np.ones(len(P))]
        M=np.einsum("vk,vkab->vab",ww,J[jj])
        S=np.einsum("vab,vb->va",M,Ph)[:,:3]
        idx=G_.acc(p["indices"]).ravel() if "indices" in p else None
        out.append(dict(rest=P,skin=S,j=jj,w=ww,prim=p,joints=sk["joints"],idx=idx,
                        mat=g["materials"][p["material"]].get("name") if "material" in p else None))
    return out
