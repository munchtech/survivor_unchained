# Body 1 g2e step 1: the arm patch's materials (cleaned) and UV seams (armor 18 g2e, 22 Oct 2026).
#   python plan.py <work dir>        (reads graft_data.npz, graft_geom.npz; writes plan.npz)
# Patch faces = the new faces (index >= len(kept)). Material: the carried one (nearest old face), majority-smoothed, then
# per side only the largest skin_graft component touching her torso ring is kept (the shoulder cap; its texels stay in the
# graft's 1024 map at the graft's density). Seams: the material boundary, and one cut through the body part from the torso
# ring to the wrist loop along the arm's underside/back (Dijkstra, edge cost length x (1 + K (1-s)^2), s = normal . under).
import sys, os, heapq, numpy as np
from collections import defaultdict
WK=sys.argv[1]; K=float(os.environ.get("CUT_K","12")); BACK=float(os.environ.get("CUT_BACK","0.6")); SMOOTH=int(os.environ.get("MAT_IT","6"))
D=np.load(os.path.join(WK,"graft_data.npz")); g=np.load(os.path.join(WK,"graft_geom.npz"))
V=D["V"]; fl=D["fl"]; fv=D["fv"]; mat=D["mat"].copy(); nk=len(g["kept"]); nf=len(fl); ls=np.r_[0,np.cumsum(fl)[:-1]]
F=[fv[ls[i]:ls[i]+fl[i]].tolist() for i in range(nf)]
pf=np.arange(nk,nf)
# face adjacency over the patch and edge -> faces over the whole mesh
ef=defaultdict(list)
for i in range(nf):
    f=F[i]
    for j in range(len(f)): ef[(min(f[j],f[(j+1)%len(f)]),max(f[j],f[(j+1)%len(f)]))].append(i)
isp=np.zeros(nf,bool); isp[pf]=True
nb=defaultdict(list)
for e,l in ef.items():
    if len(l)==2 and isp[l[0]] and isp[l[1]]: nb[l[0]].append(l[1]); nb[l[1]].append(l[0])
cen=np.array([V[f].mean(0) for f in F]); side=np.sign(cen[:,0])
print("front axis check: breast-height mean y of |x|<0.12, z 1.2-1.3 faces:",cen[(np.abs(cen[:,0])<0.12)&(cen[:,2]>1.2)&(cen[:,2]<1.3),1].min().round(3),"..",cen[(np.abs(cen[:,0])<0.12)&(cen[:,2]>1.2)&(cen[:,2]<1.3),1].max().round(3))
m0=mat.copy()
for it in range(SMOOTH):
    new=mat.copy()
    for i in pf:
        c=[mat[j] for j in nb[i]]+[mat[i]]
        new[i]=1 if 2*sum(c)>len(c) else 0 if 2*sum(c)<len(c) else mat[i]
    mat=new
# boundary loops of the patch: torso ring vs wrist
bnd=[e for e,l in ef.items() if sum(isp[x] for x in l)==1]
bv=defaultdict(list)
for a,b in bnd: bv[a].append(b); bv[b].append(a)
seen=set(); loops=[]
for s in list(bv):
    if s in seen: continue
    lp=[s]; seen.add(s); stack=[s]
    while stack:
        x=stack.pop()
        for y in bv[x]:
            if y not in seen: seen.add(y); lp.append(y); stack.append(y)
    loops.append(np.array(lp))
print("boundary components",[len(l) for l in loops])
info={}
for sd in (-1,1):
    L=[l for l in loops if np.sign(V[l,0].mean())==sd]; L.sort(key=lambda l:abs(V[l,0].mean()))
    info[sd]=dict(torso=L[0],wrist=L[-1])
    print("side",sd,"torso ring",len(L[0]),"wrist",len(L[-1]),"others",[len(x) for x in L[1:-1]])
# keep only the largest cap component per side that touches the torso ring
for sd in (-1,1):
    tor=set(info[sd]["torso"].tolist()); cand=[i for i in pf if side[i]==sd and mat[i]==1]; cs=set(cand); comp={}; best=None
    for s in cand:
        if s in comp: continue
        q=[s]; comp[s]=s; mem=[s]
        while q:
            x=q.pop()
            for y in nb[x]:
                if y in cs and y not in comp: comp[y]=s; q.append(y); mem.append(y)
        touch=any(v in tor for i in mem for v in F[i])
        if touch and (best is None or len(mem)>len(best)): best=mem
    keep=set(best or [])
    for i in cand:
        if i not in keep: mat[i]=0
    # fill holes in the cap: body faces of this side not connected to the wrist through body faces -> cap
    wr=set(info[sd]["wrist"].tolist()); body=[i for i in pf if side[i]==sd and mat[i]==0]; bs=set(body)
    start=[i for i in body if any(v in wr for v in F[i])]; vis=set(start); q=list(start)
    while q:
        x=q.pop()
        for y in nb[x]:
            if y in bs and y not in vis: vis.add(y); q.append(y)
    holes=[i for i in body if i not in vis]
    for i in holes: mat[i]=1
    print("side",sd,"cap faces",len(keep),"holes filled",len(holes))
print("patch material changed by cleanup:",int((mat[pf]!=m0[pf]).sum()),"final cap faces",int(mat[pf].sum()),"of",len(pf))
# seams: material boundary inside the patch
seam=set()
for e,l in ef.items():
    if len(l)==2 and isp[l[0]] and isp[l[1]] and mat[l[0]]!=mat[l[1]]: seam.add(e)
# vertex normals (area weighted)
VN=np.zeros_like(V)
for f in F:
    p=V[f]
    for j in range(1,len(f)-1):
        n=np.cross(p[j]-p[0],p[j+1]-p[0])
        for v in (f[0],f[j],f[j+1]): VN[v]+=n
VN/=np.maximum(np.linalg.norm(VN,axis=1)[:,None],1e-15)
cuts={}
for sd in (-1,1):
    tor=info[sd]["torso"]; wr=info[sd]["wrist"]
    a=V[wr].mean(0)-V[tor].mean(0); a/=np.linalg.norm(a)
    d=np.array([0,BACK,-1.0]); d=d-a*(d@a); d/=np.linalg.norm(d)   # down and back (+y is her back), across the arm
    body_f=[i for i in pf if side[i]==sd and mat[i]==0]
    adj=defaultdict(list)
    for i in body_f:
        f=F[i]
        for j in range(len(f)):
            x,y=f[j],f[(j+1)%len(f)]; e=(min(x,y),max(x,y))
            if e in seam: continue
            s_=(VN[x]@d+VN[y]@d)/2; c=np.linalg.norm(V[x]-V[y])*(1+K*(1-s_)**2)
            adj[x].append((y,c,e)); adj[y].append((x,c,e))
    bodyv={v for i in body_f for v in F[i]}
    capv={v for i in pf if side[i]==sd and mat[i]==1 for v in F[i]}
    cap0=set(capv)
    for i in body_f:   # and one ring of faces round the cap
        if any(v in cap0 for v in F[i]): capv|=set(F[i])
    src=[v for v in tor.tolist() if v in bodyv and v not in capv]
    sc=np.array([VN[v]@d for v in src]); src=[v for v,x in zip(src,sc) if x>=np.percentile(sc,75)]   # start in the pit's underside
    dist={v:0.0 for v in src}; prev={}; h=[(0.0,v) for v in src]; heapq.heapify(h); wset=set(wr.tolist()); end=None
    while h:
        dd,x=heapq.heappop(h)
        if dd>dist.get(x,np.inf): continue
        if x in wset: end=x; break
        for y,c,e in adj[x]:
            # stay off the patch boundary except at the two ends
            if (y in bv and y not in wset) or y in capv: continue   # nor along the cap's edge (it would cut a piece off)
            nd=dd+c
            if nd<dist.get(y,np.inf): dist[y]=nd; prev[y]=(x,e); heapq.heappush(h,(nd,y))
    path=[]; x=end
    while x in prev: x,e=prev[x]; path.append(e)
    L=sum(np.linalg.norm(V[a_]-V[b_]) for a_,b_ in path)
    sv=np.array([VN[v]@d for e in path for v in e])
    print("side",sd,"cut edges",len(path),"length %.1f cm"%(L*100),"under-score mean %.2f min %.2f"%(sv.mean(),sv.min()))
    for e in path: seam.add(e)
    cuts[sd]=np.array(path)
seam=np.array(sorted(seam))
np.savez(os.path.join(WK,"plan.npz"),nk=nk,mat=mat,seam=seam,cut_r=cuts[-1],cut_l=cuts[1])
print("PLAN seams",len(seam),"cap faces",int(mat[pf].sum()))
