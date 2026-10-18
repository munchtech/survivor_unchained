"""Graft vs every outfit/hair piece near the neck, old vs new body weights, rest + moderate turns.
python pieces.py <old body.glb> <new body.glb> <people dir>"""
import sys,os,json; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from glb import *
from motion import qmul,aq
from scipy.spatial import cKDTree
class GL(G):
    def __init__(s,p):
        s.g=json.load(open(p)); s.bin=open(os.path.join(os.path.dirname(p),s.g["buffers"][0]["uri"]),"rb").read()
POSES=[("rest",[])]+[("Hy%+d"%d,[("Head",1,d)]) for d in (-45,45)]+[("Hx%+d"%d,[("Head",0,d)]) for d in (-20,20)]+\
      [("N+H x%+d y%+d"%(dx,dy),[("neck_01",0,dx/2),("Head",0,dx/2),("neck_01",1,dy/2),("Head",1,dy/2)]) for dx in (-20,20) for dy in (-45,45)]
def pose(g,ops,rot0):
    N=g["nodes"]
    for i in range(len(N)): N[i]["rotation"]=list(rot0[i])
    for jn,ax,dg in ops:
        i=[k for k,n in enumerate(N) if n.get("name")==jn][0]; N[i]["rotation"]=qmul(N[i]["rotation"],aq(ax,dg))
def skin_any(Gp,W,names):
    g=Gp.g; out=[]
    for ni,n in enumerate(g["nodes"]):
        if "mesh" not in n or "skin" not in n: continue
        sk=g["skins"][n["skin"]]; ibm=Gp.acc(sk["inverseBindMatrices"]).reshape(-1,4,4).transpose(0,2,1)
        J=np.array([W[names[g["nodes"][j]["name"]]]@ibm[k] for k,j in enumerate(sk["joints"])])
        for p in g["meshes"][n["mesh"]]["primitives"]:
            a=p["attributes"]; P=Gp.acc(a["POSITION"]).astype(float); jj=Gp.acc(a["JOINTS_0"]).astype(int); ww=Gp.acc(a["WEIGHTS_0"]).astype(float)
            M=np.einsum("vk,vkab->vab",ww,J[jj]); S=np.einsum("vab,vb->va",M,np.c_[P,np.ones(len(P))])[:,:3]
            nn=np.einsum("vab,vb->va",M[:,:3,:3],Gp.acc(a["NORMAL"]).astype(float)); nn/=np.linalg.norm(nn,axis=1,keepdims=True)+1e-12
            out.append((n.get("name","?")+"/"+str(g["materials"][p["material"]].get("name") if "material" in p else ""),S,nn))
    return out
oldp,newp,pdir=sys.argv[1:4]
bodies=[G(oldp),G(newp)]
files=[f for f in sorted(os.listdir(pdir)) if f.startswith("heroine_") and f.endswith(".gltf") and ("outfit" in f or any(s in f for s in ("braid","ponytail","pixie")))]
rot0={i:list(n.get("rotation",[0,0,0,1])) for i,n in enumerate(bodies[0].g["nodes"])}
names={n.get("name"):i for i,n in enumerate(bodies[0].g["nodes"])}
for f in files:
    Gp=GL(os.path.join(pdir,f)); rows=[]
    for nm,ops in POSES:
        r=[]
        for B in bodies:
            pose(B.g,ops,rot0); W=worlds(B.g); gr=skinned(B,84)[1]
            # graft normals: skinned
            pcs=skin_any(Gp,W,names)
            Tg=cKDTree(gr["skin"])
            sk=B.g["skins"][0]; ibm=B.acc(sk["inverseBindMatrices"]).reshape(-1,4,4).transpose(0,2,1)
            J=np.array([W[j]@ibm[k] for k,j in enumerate(sk["joints"])])
            ng=np.einsum("vab,vb->va",np.einsum("vk,vkab->vab",gr["w"],J[gr["j"]])[:,:3,:3],B.acc(gr["prim"]["attributes"]["NORMAL"]).astype(float)); ng/=np.linalg.norm(ng,axis=1,keepdims=True)
            cnt=0; mx=0.0
            for pn,S,nn in pcs:
                # graft points out through this piece: graft verts near the piece and on the piece's outer side
                d,ix=cKDTree(S).query(gr["skin"]); m=d<0.01
                if not m.any(): continue
                s=np.einsum("ij,ij->i",gr["skin"][m]-S[ix[m]],nn[ix[m]])
                cnt+=(s>0.001).sum(); mx=max(mx,s.max()*1e3)
            r.append((cnt,mx))
        rows.append((nm,r))
    print(f); [print("   %-14s old %4d %5.1f mm | new %4d %5.1f mm"%(nm,r[0][0],r[0][1],r[1][0],r[1][1])) for nm,r in rows]
