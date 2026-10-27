# Her arm-root graft (Body 1, armor 18 g1, 22 Oct 2026). See tools/assets/heroine_arm_graft.py.
import numpy as np
from collections import defaultdict
from her_load import load_her, G
d=load_her(); g=dict(np.load(G+r"\graft_geom.npz")); V=g["V"]; nold=int(g["nold"])
ls,lt,lv=d["ls"],d["lt"],d["lv"]; polys=[list(lv[s:s+n]) for s,n in zip(ls,lt)]
faces=[polys[i] for i in g["kept"]]+[[v for v in fc if v>=0] for fc in g["newfaces"]]
kinds=["old"]*len(g["kept"])+list(g["kinds"])
key=np.round(V/1e-6).astype(np.int64); _,wid=np.unique(key,axis=0,return_inverse=True); wid=wid.ravel()
def stats(F):
    ec=defaultdict(int)
    for fc in F:
        w=wid[fc]
        for k in range(len(w)): ec[(min(w[k],w[(k+1)%len(w)]),max(w[k],w[(k+1)%len(w)]))]+=1
    c=np.array(list(ec.values())); return (c==1).sum(),(c>2).sum(),ec
b0,n0,_=stats(polys); b1,n1,ec=stats(faces)
print("boundary edges before",b0,"after",b1,"; nonmanifold before",n0,"after",n1)
# strip triangles
S=[fc for fc,k in zip(faces,kinds) if k=="strip"]
L=[];A=[]
for fc in S:
    p=V[fc]; e=np.linalg.norm(p-np.roll(p,1,0),axis=1); L.append(e.max())
    for k in range(3):
        a=p[(k+1)%3]-p[k]; b=p[(k+2)%3]-p[k]; A.append(np.degrees(np.arccos(np.clip(a@b/np.linalg.norm(a)/np.linalg.norm(b),-1,1))))
L=np.array(L)*100; A=np.array(A); print("strip tris",len(S),"max edge cm median %.2f p95 %.2f max %.2f; min angle p5 %.1f min %.1f"%(np.median(L),np.percentile(L,95),L.max(),np.percentile(A,5),A.min()))
# dihedral between adjacent faces near seam (strip/patch/old ring)
fn=[]
for fc in faces:
    p=V[fc]; n=np.cross(p[1]-p[0],p[2]-p[0]); 
    if len(fc)==4: n=n+np.cross(p[2]-p[0],p[3]-p[0])
    fn.append(n/max(np.linalg.norm(n),1e-15))
fn=np.array(fn); ef=defaultdict(list)
for i,fc in enumerate(faces):
    w=wid[fc]
    for k in range(len(w)): ef[(min(w[k],w[(k+1)%len(w)]),max(w[k],w[(k+1)%len(w)]))].append(i)
kk=np.array(kinds)
for lab in ("strip","patch","old"):
    ang=[]
    for e,l in ef.items():
        if len(l)==2 and (kk[l[0]]==lab or kk[l[1]]==lab) and ("strip" in (kk[l[0]],kk[l[1]]) or lab!="old"):
            ang.append(np.degrees(np.arccos(np.clip(fn[l[0]]@fn[l[1]],-1,1))))
    ang=np.array(ang); print(f"dihedral at {lab}-adjacent edges: median {np.median(ang):.1f} p99 {np.percentile(ang,99):.1f} max {ang.max():.1f} (n {len(ang)})")
# old arm-region dihedral for reference
import sys
bn=list(d["bn"])
def tphi(X,side):
    S=d["bh"][bn.index(f"upperarm_{side}")]; E=d["bh"][bn.index(f"lowerarm_{side}")]; u=(E-S)/np.linalg.norm(E-S); L=np.linalg.norm(E-S)
    up=np.array([0,0,1.]); up=up-u*(up@u); up/=np.linalg.norm(up); fr=np.cross(u,up)
    if fr[1]>0: fr=-fr
    dd=X-S; t=(dd@u)/L; rr=dd-np.outer(dd@u,u); return t,np.degrees(np.arctan2(rr@fr,rr@up))
bad=[]
for e,l in ef.items():
    if len(l)==2 and "old" not in (kk[l[0]],kk[l[1]]) or (len(l)==2 and "strip" in (kk[l[0]],kk[l[1]])):
        a=np.degrees(np.arccos(np.clip(fn[l[0]]@fn[l[1]],-1,1)))
        if a>60: bad.append((a,e,kk[l[0]],kk[l[1]]))
print("folds>60deg:",len(bad))
rep=np.zeros(wid.max()+1,int); rep[wid]=np.arange(len(V))
for a,e,k0,k1 in sorted(bad,reverse=True)[:25]:
    p=V[rep[e[0]]]; s="r" if p[0]<0 else "l"; t,ph=tphi(p[None],s)
    print(f"  {a:.0f} {k0}/{k1} {s} t {t[0]:+.2f} phi {ph[0]:+.0f} {p.round(3)}")
