from pose import *
from scipy import sparse
def dense(G_,inv):
    g=G_.g; pr=g["meshes"][g["nodes"][84]["mesh"]]["primitives"][:2]
    J=np.concatenate([G_.acc(p["attributes"]["JOINTS_0"]).astype(int) for p in pr]); Wt=np.concatenate([G_.acc(p["attributes"]["WEIGHTS_0"]).astype(float) for p in pr])
    nj=len(g["skins"][0]["joints"]); D=np.zeros((inv.max()+1,nj))
    for k in range(4): D[inv,J[:,k]]=0; 
    for k in range(4): np.add.at(D,(inv,J[:,k]),0)  # placeholder
    D=np.zeros((inv.max()+1,nj)); first=np.unique(inv,return_index=True)[1]
    for k in range(4): np.add.at(D,(inv[first],J[first,k]),Wt[first,k])
    return D
def adj(n,T):
    e=np.r_[T[:,[0,1]],T[:,[1,2]],T[:,[2,0]]]; e=np.r_[e,e[:,::-1]]
    A=sparse.coo_matrix((np.ones(len(e)),(e[:,0],e[:,1])),shape=(n,n)).tocsr(); A.data[:]=1
    d=np.array(A.sum(1)).ravel(); return sparse.diags(1/np.maximum(d,1))@A
def skin_custom(G_,ops,Wd,uncut=0.03):
    g=G_.g; N=g["nodes"]; keep=[dict(n) for n in N]
    if uncut:
        h=[n for n in N if n.get("name")=="Head"][0]; t=np.array(h["translation"]); L=np.linalg.norm(t); h["translation"]=list(t*(L+uncut)/L)
    for jn,ax,dg in ops:
        i=[k for k,n in enumerate(N) if n.get("name")==jn][0]; N[i]["rotation"]=qmul(N[i].get("rotation",[0,0,0,1]),aq(ax,dg))
    W=worlds(g); sk=g["skins"][0]; ibm=G_.acc(sk["inverseBindMatrices"]).reshape(-1,4,4).transpose(0,2,1)
    Jm=np.array([W[j]@ibm[k] for k,j in enumerate(sk["joints"])])
    for i in range(len(N)): N[i].clear(); N[i].update(keep[i])
    return Jm
def apply(Jm,U,Wx):
    M=np.einsum("vj,jab->vab",Wx,Jm); return np.einsum("vab,vb->va",M,np.c_[U,np.ones(len(U))])[:,:3]
