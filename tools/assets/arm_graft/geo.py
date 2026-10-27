import numpy as np, scipy.sparse as sp
from scipy.spatial import cKDTree
def closest_tri(p,a,b,c):
    # Ericson, vectorized: returns closest points and barycentrics (u,v,w) with q=u a+v b+w c
    ab=b-a; ac=c-a; ap=p-a
    d1=(ab*ap).sum(1); d2=(ac*ap).sum(1)
    bp=p-b; d3=(ab*bp).sum(1); d4=(ac*bp).sum(1)
    cp=p-c; d5=(ab*cp).sum(1); d6=(ac*cp).sum(1)
    n=len(p); bar=np.zeros((n,3)); done=np.zeros(n,bool)
    def put(m,u,v,w):
        m=m&~done; bar[m,0]=u[m] if np.ndim(u) else u; bar[m,1]=v[m] if np.ndim(v) else v; bar[m,2]=w[m] if np.ndim(w) else w; done[m]=True
    one=np.ones(n); zero=np.zeros(n)
    put((d1<=0)&(d2<=0),one,zero,zero)
    put((d3>=0)&(d4<=d3),zero,one,zero)
    put((d6>=0)&(d5<=d6),zero,zero,one)
    vc=d1*d4-d3*d2
    with np.errstate(all="ignore"):
        v=d1/(d1-d3); put((vc<=0)&(d1>=0)&(d3<=0),1-v,v,zero)
        vb=d5*d2-d1*d6; w=d2/(d2-d6); put((vb<=0)&(d2>=0)&(d6<=0),1-w,zero,w)
        va=d3*d6-d5*d4; w2=(d4-d3)/((d4-d3)+(d5-d6)); put((va<=0)&((d4-d3)>=0)&((d5-d6)>=0),zero,1-w2,w2)
        den=1/(va+vb+vc); vv=vb*den; ww=vc*den; put(np.ones(n,bool),1-vv-ww,vv,ww)
    q=bar[:,:1]*a+bar[:,1:2]*b+bar[:,2:]*c
    return q,bar
class Surf:
    def __init__(s,V,T,k=24):
        s.V=V; s.T=T; s.cen=V[T].mean(1); s.kd=cKDTree(s.cen); s.k=k
        fn=np.cross(V[T[:,1]]-V[T[:,0]],V[T[:,2]]-V[T[:,0]]); s.fa=np.linalg.norm(fn,axis=1)/2; s.fn=fn/np.maximum(2*s.fa[:,None],1e-15)
    def query(s,p):
        _,J=s.kd.query(p,s.k); J=J.reshape(len(p),-1); n=len(p); best=np.full(n,np.inf); bq=np.zeros((n,3)); bf=np.zeros(n,int); bb=np.zeros((n,3))
        for j in range(J.shape[1]):
            f=J[:,j]; T=s.T[f]; q,bar=closest_tri(p,s.V[T[:,0]],s.V[T[:,1]],s.V[T[:,2]]); dd=((q-p)**2).sum(1)
            m=dd<best; best[m]=dd[m]; bq[m]=q[m]; bf[m]=f[m]; bb[m]=bar[m]
        return bq,np.sqrt(best),bf,bb
def edges_of(F):
    e=[]
    for i in range(F.shape[1]): e.append(F[:,[i,(i+1)%F.shape[1]]])
    e=np.sort(np.concatenate(e),1); return np.unique(e,axis=0)
def adjacency(n,E):
    A=sp.coo_matrix((np.ones(2*len(E)),(np.r_[E[:,0],E[:,1]],np.r_[E[:,1],E[:,0]])),shape=(n,n)).tocsr(); A.data[:]=1; return A
def umbrella(n,E):
    A=adjacency(n,E); dg=np.asarray(A.sum(1)).ravel(); return sp.diags(1/np.maximum(dg,1))@A   # row-normalized
def taubin(V,E,fixed,it=10,lam=0.5,mu=-0.53):
    W=umbrella(len(V),E); X=V.copy()
    for _ in range(it):
        for f in (lam,mu):
            D=W@X-X; D[fixed]=0; X=X+f*D
    return X
def catmull_clark(V,F):
    E=edges_of(F); n=len(V); ne=len(E)
    key={tuple(e):i for i,e in enumerate(E)}
    fe=np.array([[key[tuple(sorted((f[i],f[(i+1)%4])))] for i in range(4)] for f in F])
    fp=V[F].mean(1)
    ef=[[] for _ in range(ne)]
    for fi,row in enumerate(fe):
        for e in row: ef[e].append(fi)
    bnd=np.array([len(x)==1 for x in ef])
    ep=np.zeros((ne,3))
    for i,(a,b) in enumerate(E):
        ep[i]=(V[a]+V[b])/2 if bnd[i] else (V[a]+V[b]+fp[ef[i][0]]+fp[ef[i][1]])/4
    # vertex points
    vf=[[] for _ in range(n)]
    for fi,f in enumerate(F):
        for v in f: vf[v].append(fi)
    ve=[[] for _ in range(n)]
    for i,(a,b) in enumerate(E): ve[a].append(i); ve[b].append(i)
    NV=V.copy(); isb=np.zeros(n,bool)
    for v in range(n):
        if not ve[v]: continue
        be=[e for e in ve[v] if bnd[e]]
        if be:
            isb[v]=True
            nb=[E[e][0] if E[e][1]==v else E[e][1] for e in be]
            NV[v]=(6*V[v]+V[nb].sum(0))/(6+len(nb)) if len(nb)==2 else V[v]
        else:
            k=len(ve[v]); Fa=fp[vf[v]].mean(0); R=np.mean([(V[E[e][0]]+V[E[e][1]])/2 for e in ve[v]],0)
            NV[v]=(Fa+2*R+(k-3)*V[v])/k
    V2=np.concatenate([NV,ep,fp]); oe=n; of=n+ne
    F2=[]
    for fi,f in enumerate(F):
        for i in range(4):
            F2.append([f[i],oe+fe[fi][i],of+fi,oe+fe[fi][(i-1)%4]])
    return V2,np.array(F2)
def quad_tris(F):
    return np.concatenate([F[:,[0,1,2]],F[:,[0,2,3]]])
