# Her arm-root graft (Body 1, armor 18 g1, 22 Oct 2026). See tools/assets/heroine_arm_graft.py.
# Stage 3: carry her per-vertex and per-corner data onto the grafted patch. Writes graft_data.npz for b_write.py.
import numpy as np
from collections import defaultdict
from geo import *; from her_load import load_her, G
d=load_her(); g=dict(np.load(G+r"\graft_geom.npz"))
P=d["P"]; ls,lt,lv=d["ls"],d["lt"],d["lv"]; VG=d["VG"]; UV=d["uv"]; CN=d["cn"]; MI=d["mi"]; GR=d["graft"]; TF=d["TF"]; TL=d["TL"]
V=g["V"]; kept=g["kept"]; inpatch=g["inpatch"]; nold=int(g["nold"])
polys=[list(lv[s:s+n]) for s,n in zip(ls,lt)]
newf=[[v for v in fc if v>=0] for fc in g["newfaces"]]
used_old=np.zeros(len(V),bool)
for i in kept: used_old[polys[i]]=True
newv=np.unique(np.concatenate(newf)); newv=newv[~used_old[newv]]
ring=g["ring"]
# old source region: patch polygons and kept polygons touching the ring
near=inpatch.copy()
rs=set(ring.tolist())
for i in kept:
    if any(v in rs for v in polys[i]): near[i]=True
# UV islands over old polygons (shared edge with equal corner UVs on both sides)
corner_uv={}
for i,(s,n) in enumerate(zip(ls,lt)):
    for k in range(n): corner_uv[(i,lv[s+k])]=UV[s+k]
ep=defaultdict(list)
for i,p in enumerate(polys):
    for k in range(len(p)): ep[(min(p[k],p[(k+1)%len(p)]),max(p[k],p[(k+1)%len(p)]))].append(i)
par=list(range(len(polys)))
def find(x):
    while par[x]!=x: par[x]=par[par[x]]; x=par[x]
    return x
for (a,b),l in ep.items():
    if len(l)==2:
        i,j=l
        if MI[i]==MI[j] and np.allclose(corner_uv[(i,a)],corner_uv[(j,a)],atol=1e-5) and np.allclose(corner_uv[(i,b)],corner_uv[(j,b)],atol=1e-5):
            par[find(i)]=find(j)
isl=np.array([find(i) for i in range(len(polys))])
# triangles of the source region
tm=near[TF]; Tsrc=d["T"][tm]; TFs=TF[tm]; TLs=TL[tm]
Ssrc=Surf(P,Tsrc)
# per new vertex: weights and graft by barycentric interpolation
q,dist,fi,bar=Ssrc.query(V[newv])
tri=Tsrc[fi]
W=(VG[tri]*bar[:,:,None]).sum(1)
top=np.argsort(-W,axis=1)[:,:4]; W4=np.zeros_like(W); r=np.arange(len(W))[:,None]; W4[r,top]=W[r,top]; W4[W4<1e-4]=0
W4/=np.maximum(W4.sum(1,keepdims=True),1e-9)
Gn=((GR[tri]*bar).sum(1)>=0.5).astype(int)
print("new verts",len(newv),"source dist mm p95 %.2f max %.2f"%(np.percentile(dist,95)*1000,dist.max()*1000))
print("old weights: verts with >4 groups in source:",int(((VG[np.unique(Tsrc)]>1e-4).sum(1)>4).sum()))
# per island surfaces (lazy)
isl_tris=defaultdict(list)
for k,f_ in enumerate(TFs): isl_tris[isl[f_]].append(k)
cache={}
def isurf(i):
    if i not in cache:
        ks=np.array(isl_tris[i]); cache[i]=(Surf(P,Tsrc[ks],k=min(24,len(ks))),ks)
    return cache[i]
cen=np.array([V[fc].mean(0) for fc in newf]); _,_,cfi,_=Ssrc.query(cen)
fisl=isl[TFs[cfi]]; fmat=MI[TFs[cfi]]
uvs=[None]*len(newf)
for i in np.unique(fisl):
    S_,ks=isurf(i); ids=np.nonzero(fisl==i)[0]
    pts=np.concatenate([V[newf[k]] for k in ids]); _,_,ff,bb=S_.query(pts)
    tl=TLs[ks[ff]]; uv=(UV[tl]*bb[:,:,None]).sum(1)
    o=0
    for k in ids: n=len(newf[k]); uvs[k]=uv[o:o+n]; o+=n
# UV seams inside the new faces: edges between new faces of different islands
fe=defaultdict(list)
for k,fc in enumerate(newf):
    for j in range(len(fc)): fe[(min(fc[j],fc[(j+1)%len(fc)]),max(fc[j],fc[(j+1)%len(fc)]))].append(k)
seam=[e for e,l in fe.items() if len(l)==2 and fisl[l[0]]!=fisl[l[1]]]
sl=sum(np.linalg.norm(V[a]-V[b]) for a,b in seam)
print("islands under the new faces:",{int(i):int((fisl==i).sum()) for i in np.unique(fisl)},"materials",np.bincount(fmat))
print("UV seam edges inside the new faces: %d, %.1f cm"%(len(seam),sl*100))
seamv=np.unique(np.array(seam).ravel()) if seam else np.zeros(0,int)
np.save(G+r"\seam_pts.npy",V[seamv])
# normals: area-weighted, welded by position, over the final mesh
faces=[polys[i] for i in kept]+newf
key=np.round(V/1e-6).astype(np.int64); _,wid=np.unique(key,axis=0,return_inverse=True); wid=wid.ravel()
VN=np.zeros((wid.max()+1,3))
for fc in faces:
    p=V[fc]
    for j in range(1,len(fc)-1):
        n=np.cross(p[j]-p[0],p[j+1]-p[0])
        for v in (fc[0],fc[j],fc[j+1]): VN[wid[v]]+=n
VN/=np.maximum(np.linalg.norm(VN,axis=1)[:,None],1e-15)
# per-loop data in final face order
cn_out=[]; uv_out=[]
for i in kept:
    s,n=ls[i],lt[i]
    for k in range(n):
        v=lv[s+k]; uv_out.append(UV[s+k]); cn_out.append(VN[wid[v]] if v in rs else CN[s+k])
for k,fc in enumerate(newf):
    for j,v in enumerate(fc): uv_out.append(uvs[k][j]); cn_out.append(VN[wid[v]])
fl=np.array([len(fc) for fc in faces]); fv=np.concatenate(faces)
mat=np.concatenate([MI[kept],fmat])
Wfull=VG.copy().astype(np.float32); Wfull=np.vstack([Wfull,np.zeros((len(V)-len(P),VG.shape[1]),np.float32)]) if len(V)>len(P) else Wfull
Wfull[newv]=W4
graft=np.concatenate([GR,np.zeros(len(V)-len(P),int)]); graft[newv]=Gn
# sharp edges kept where both ends are kept old verts and the edge still exists
sh=d["ev"][d["sharp"]]; fes=set()
for fc in faces:
    for j in range(len(fc)): fes.add((min(fc[j],fc[(j+1)%len(fc)]),max(fc[j],fc[(j+1)%len(fc)])))
shk=np.array([e for e in sh if (min(e),max(e)) in fes and not np.isin(e,newv).any()])
print("sharp edges: before",len(sh),"kept",len(shk))
np.savez(G+r"\graft_data.npz",V=V,fl=fl,fv=fv,mat=mat,uv=np.array(uv_out),cn=np.array(cn_out),W=Wfull,graft=graft,sharp=shk,names=d["names"],newv=newv)
print("final verts",len(V),"faces",len(faces),"loops",len(fv))
