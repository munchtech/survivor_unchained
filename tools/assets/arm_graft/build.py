# Her arm-root graft (Body 1, armor 18 g1, 22 Oct 2026). See tools/assets/heroine_arm_graft.py.
# Stage 2: stitch the fitted patches into her mesh. Writes graft_geom.npz.
import os, numpy as np, scipy.sparse as sp
from scipy.sparse.csgraph import connected_components
from collections import defaultdict
from geo import *; from her_load import load_her, G
d=load_her(); f=dict(np.load(G+r"\fit.npz"))
P=d["P"]; ls,lt,lv=d["ls"],d["lt"],d["lv"]; nP=len(ls); MI=d["mi"]
wid=f["wid"]; Pw=f["Pw"]; Ps=f["Ps"]; nW=len(Pw)
polys=[lv[s:s+n] for s,n in zip(ls,lt)]
TF=d["TF"]; T=d["T"]
So=Surf(P,T); Ssm=Surf(Ps,f["Tw"])
GAP=float(os.environ.get("GAP","0.006")); BLEND=0.02
Tw_all=wid[T]; ok=(Tw_all[:,0]!=Tw_all[:,1])&(Tw_all[:,1]!=Tw_all[:,2])&(Tw_all[:,0]!=Tw_all[:,2]); okidx=np.nonzero(ok)[0]
inpatch=np.zeros(nP,bool); side_of=np.full(nP,-1)
sides=("r","l")
ed=defaultdict(list)
for i,p in enumerate(polys):
    w=wid[p]
    for k in range(len(w)): ed[(min(w[k],w[(k+1)%len(w)]),max(w[k],w[(k+1)%len(w)]))].append(i)
pr=np.array([v for v in ed.values() if len(v)==2])
def comps(m):
    q=pr[m[pr[:,0]]&m[pr[:,1]]]; A=sp.coo_matrix((np.ones(len(q)),(q[:,0],q[:,1])),shape=(nP,nP)); return connected_components(A,directed=False)[1]
for si,side in enumerate(sides):
    fin=f[f"{side}_fin"]; X=f[f"{side}_Vf"]; Fq=f[f"{side}_Fs"]
    trin=np.zeros(len(T),bool); trin[okidx[fin]]=True
    Sx=Surf(X,quad_tris(Fq))
    pin=np.ones(nP,bool); np.logical_and.at(pin,TF,trin)
    has=np.zeros(nP,bool); has[TF[ok]]=True; pin&=has
    pv=np.unique(np.concatenate([wid[polys[i]] for i in np.nonzero(pin)[0]]))
    dcov=Sx.query(Ps[pv])[1]; bad=np.zeros(nW,bool); bad[pv[dcov>0.0015]]=True
    bnn=list(d["bn"]); S_=d["bh"][bnn.index(f"upperarm_{side}")]; E_=d["bh"][bnn.index(f"lowerarm_{side}")]; u_=(E_-S_)/np.linalg.norm(E_-S_); L_=np.linalg.norm(E_-S_)
    up_=np.array([0,0,1.]); up_=up_-u_*(up_@u_); up_/=np.linalg.norm(up_); fr_=np.cross(u_,up_); fr_=-fr_ if fr_[1]>0 else fr_
    dd_=Pw-S_; t_=(dd_@u_)/L_; rr_=dd_-np.outer(dd_@u_,u_); ph_=np.degrees(np.arctan2(rr_@fr_,rr_@up_)); rad_=np.linalg.norm(rr_,axis=1)
    pitv=(t_>-0.25)&(t_<0.4)&(np.abs(ph_)>110)&(rad_<0.12)
    U=pin&np.array([bad[wid[p]].any() and not pitv[wid[p]].any() for p in polys])
    labU=comps(U); mm=pin[pr[:,0]]!=pin[pr[:,1]]
    edgeU=set(labU[pr[mm][U[pr[mm][:,0]],0]])|set(labU[pr[mm][U[pr[mm][:,1]],1]])
    rm=U&np.isin(labU,list(edgeU))
    # grow: uncovered components touching the cut, repeated as the cut moves in
    for _ in range(20):
        pin2=pin&~rm; mm=pin2[pr[:,0]]!=pin2[pr[:,1]]
        e2=set(labU[pr[mm][U[pr[mm][:,0]]&pin2[pr[mm][:,0]],0]])|set(labU[pr[mm][U[pr[mm][:,1]]&pin2[pr[mm][:,1]],1]])
        rm2=U&np.isin(labU,list(e2))
        if (rm2&~rm).sum()==0: break
        rm|=rm2
    print(side,"uncovered polygons",U.sum(),"removed at the cut",rm.sum(),"kept inside (crease)",(U&~rm).sum())
    pin&=~rm
    lab=comps(pin); c=np.bincount(lab[pin],minlength=lab.max()+1); pin&=lab==np.argmax(c)
    lo=comps(~pin); co=np.bincount(lo[~pin],minlength=lo.max()+1); adj=np.zeros(co.size,bool)
    mm=pin[pr[:,0]]!=pin[pr[:,1]]; ob=np.where(pin[pr[mm,0]],pr[mm,1],pr[mm,0]); adj[lo[ob]]=True
    pin|=(~pin)&((co<300)&adj)[lo]
    inpatch|=pin; side_of[pin]=si
    print(side,"patch polygons",pin.sum())
kept=np.nonzero(~inpatch)[0]
used=np.zeros(len(P),bool)
for i in kept: used[polys[i]]=True
slots=list(np.nonzero(~used)[0]); print("reusable slots",len(slots))
newfaces=[]; kinds=[]; groups=[]; newpos={}; ringverts=set(); nextv=[len(P)]
def alloc():
    if slots: return slots.pop(0)
    i=nextv[0]; nextv[0]+=1; return i
for si,side in enumerate(sides):
    pin=side_of==si
    he=[]
    for i in kept:
        p=polys[i]; w=wid[p]
        for k in range(len(p)):
            key=(min(w[k],w[(k+1)%len(p)]),max(w[k],w[(k+1)%len(p)]))
            if any(side_of[j]==si for j in ed[key]): he.append((p[(k+1)%len(p)],p[k]))
    # traced on welded ids (g2c: her wrist ring has split vertices), each loop vertex the copy its kept face uses
    repv={}
    for a,b_ in he: repv.setdefault(wid[a],a); repv.setdefault(wid[b_],b_)
    nxt={wid[a]:wid[b_] for a,b_ in he}
    loopsR=[]; seen=set()
    for a0,_ in he:
        a=wid[a0]
        if a in seen: continue
        lp=[a]; seen.add(a); c=nxt.get(a)
        while c is not None and c!=a and c not in seen: lp.append(c); seen.add(c); c=nxt.get(c)
        loopsR.append([repv[x] for x in lp])
    print(side,"ring loops",[len(l) for l in loopsR])
    for l in loopsR: ringverts.update(l)
    X=f[f"{side}_Vf"].copy(); Fq=f[f"{side}_Fs"]
    q,dist,ft,bar=So.query(X)
    inside=pin[TF][ft]
    R=np.array([[P[l[k]],P[l[(k+1)%len(l)]]] for l in loopsR for k in range(len(l))])
    kd=cKDTree(R.mean(1))
    def segdist(Y):
        out=np.full(len(Y),np.inf); _,J=kd.query(Y,8)
        for j in range(8):
            a=R[J[:,j],0]; b=R[J[:,j],1]; ab=b-a; tt=np.clip(((Y-a)*ab).sum(1)/np.maximum((ab*ab).sum(1),1e-12),0,1)
            out=np.minimum(out,np.linalg.norm(Y-(a+ab*tt[:,None]),axis=1))
        return out
    dr=segdist(X)
    qok=(inside&(dr>=GAP))[Fq].all(1)
    emap=defaultdict(list)
    for fi,qd in enumerate(Fq):
        for k in range(4): emap[(min(qd[k],qd[(k+1)%4]),max(qd[k],qd[(k+1)%4]))].append(fi)
    qp=np.array([v for v in emap.values() if len(v)==2]); nq=len(Fq)
    def qcomps(m):
        qq=qp[m[qp[:,0]]&m[qp[:,1]]]; A=sp.coo_matrix((np.ones(len(qq)),(qq[:,0],qq[:,1])),shape=(nq,nq)); return connected_components(A,directed=False)[1]
    lab=qcomps(qok); c=np.bincount(lab[qok],minlength=lab.max()+1); qok&=lab==np.argmax(c)
    lo=qcomps(~qok); co=np.bincount(lo[~qok],minlength=lo.max()+1)
    qok|=(~qok)&(co<40)[lo]
    for _ in range(10):
        Fk=Fq[qok]; e=np.sort(np.concatenate([Fk[:,[0,1]],Fk[:,[1,2]],Fk[:,[2,3]],Fk[:,[3,0]]]),1); ue,ec=np.unique(e,axis=0,return_counts=True)
        deg=np.bincount(ue[ec==1].ravel(),minlength=len(X)); badv=np.nonzero(deg>2)[0]
        # also drop quads hanging by one edge (3 boundary edges)
        bset=set(map(tuple,ue[ec==1])); hang=np.array([sum((min(qd[k],qd[(k+1)%4]),max(qd[k],qd[(k+1)%4])) in bset for k in range(4))>=3 for qd in Fk])
        if not len(badv) and not hang.any(): break
        drop=np.isin(Fq,badv).any(1); ki=np.nonzero(qok)[0]; drop[ki[hang]]=True; qok&=~drop
    # fill notches: a quad sharing two or more edges with the kept region joins it (if it is inside and clear of the ring)
    vin=inside&(dr>=GAP*0.4)
    for _ in range(10):
        Fk=Fq[qok]; kes=set()
        for qd in Fk:
            for k in range(4): kes.add((min(qd[k],qd[(k+1)%4]),max(qd[k],qd[(k+1)%4])))
        add=np.array([(not qok[i]) and vin[Fq[i]].all() and sum((min(Fq[i][k],Fq[i][(k+1)%4]),max(Fq[i][k],Fq[i][(k+1)%4])) in kes for k in range(4))>=2 for i in range(len(Fq))])
        if not add.any(): break
        qok|=add
    for _ in range(10):
        Fk=Fq[qok]; e=np.sort(np.concatenate([Fk[:,[0,1]],Fk[:,[1,2]],Fk[:,[2,3]],Fk[:,[3,0]]]),1); ue,ec=np.unique(e,axis=0,return_counts=True)
        deg=np.bincount(ue[ec==1].ravel(),minlength=len(X)); badv=np.nonzero(deg>2)[0]
        if not len(badv): break
        qok&=~np.isin(Fq,badv).any(1)
    Fk=Fq[qok]
    heq=[(qd[k],qd[(k+1)%4]) for qd in Fk for k in range(4)]
    hs=set(heq); bhe=[(b,a) for a,b in heq if (b,a) not in hs]
    nx={a:b for a,b in bhe}; loopsB=[]; seen=set()
    for a,_ in bhe:
        if a in seen: continue
        lp=[a]; seen.add(a); c=nx.get(a)
        while c is not None and c!=a and c not in seen: lp.append(c); seen.add(c); c=nx.get(c)
        loopsB.append(lp)
    print(side,"trimmed quads",len(Fk),"boundary loops",[len(l) for l in loopsB])
    Fk=[list(q) for q in Fk]
    if int(os.environ.get("WRIST_CORNER","0")):
        # g2d: the wrist loop's staircase (the trim crosses the coarse rows on a slant) cut on the diagonal: a quad whose
        # corner is on the loop and in no other kept quad loses that corner (a triangle), one loop vertex fewer each
        Hb=d["bh"][list(d["bn"]).index(f"hand_{side}")]
        lw=min(loopsB,key=lambda l:np.linalg.norm(X[l].mean(0)-Hb)); lws=set(lw)
        cnt=defaultdict(int)
        for q in Fk:
            for v in q: cnt[v]+=1
        cut=0; usedq=set()
        for qi,q in enumerate(Fk):
            if len(q)!=4: continue
            cs=[k for k in range(4) if q[k] in lws and cnt[q[k]]==1 and q[(k+1)%4] in lws and q[(k+3)%4] in lws]
            if len(cs)!=1: continue
            k=cs[0]
            if q[(k+1)%4] in usedq or q[(k+3)%4] in usedq: continue
            usedq.update([q[(k+1)%4],q[(k+3)%4]]); Fk[qi]=[q[(k+1)%4],q[(k+2)%4],q[(k+3)%4]]; cut+=1
        heq=[(qd[k],qd[(k+1)%len(qd)]) for qd in Fk for k in range(len(qd))]
        hs=set(heq); bhe=[(b,a) for a,b in heq if (b,a) not in hs]
        nx={a:b for a,b in bhe}; loopsB=[]; seen=set()
        for a,_ in bhe:
            if a in seen: continue
            lp=[a]; seen.add(a); c=nx.get(a)
            while c is not None and c!=a and c not in seen: lp.append(c); seen.add(c); c=nx.get(c)
            loopsB.append(lp)
        print(side,"wrist corners cut",cut,"boundary loops",[len(l) for l in loopsB])
    # boundary loops made smooth along their length (the staircase of quad edges evened), and the next row with them
    for lp in loopsB:
        L_=np.array(lp)
        for _ in range(8):
            X[L_]=X[L_]+0.5*((np.roll(X[L_],1,0)+np.roll(X[L_],-1,0))/2-X[L_])
        X[L_]=Ssm.query(X[L_])[0]
    bset=set(v for lp in loopsB for v in lp); Ek=np.unique(np.sort(np.array([(q[k],q[(k+1)%len(q)]) for q in Fk for k in range(len(q))]),1),axis=0); Ak=adjacency(len(X),Ek); Wk=umbrella(len(X),Ek)
    row=np.zeros(len(X),bool); row[list(bset)]=True; row=(Ak@row>0)&~row
    for _ in range(4): X[row]=(X+0.5*(Wk@X-X))[row]
    X[row]=Ssm.query(X[row])[0]
    q,dist,ft,bar=So.query(X); dr=segdist(X)
    w=np.clip(1-dr/BLEND,0,1); w=w*w*(3-2*w); gq=np.linalg.norm(q-X,axis=1); w*=np.clip((0.0015-gq)/0.0005,0,1); Y=X+w[:,None]*(q-X)
    idx={}
    for v in np.unique(np.concatenate(Fk)):
        i=alloc(); idx[v]=i; newpos[i]=Y[v]
    for qd in Fk: newfaces.append([idx[v] for v in qd]); kinds.append("patch"); groups.append(f"{side}p")
    for lr in loopsR:
        cR=P[lr].mean(0); lb=min(loopsB,key=lambda l:np.linalg.norm(Y[l].mean(0)-cR))
        A_=list(lr); B_=[idx[v] for v in lb][::-1]; PB=np.array([newpos[i] for i in B_])
        DA=np.linalg.norm(P[A_][:,None]-PB[None],axis=2); i0,j0=np.unravel_index(np.argmin(DA),DA.shape)
        A_=A_[i0:]+A_[:i0]; B_=B_[j0:]+B_[:j0]; PB=np.array([newpos[i] for i in B_]); PA=P[A_]
        nA,nB=len(A_),len(B_)
        PAc=np.vstack([PA,PA[:1]]); PBc=np.vstack([PB,PB[:1]])
        C=np.full((nA+1,nB+1),np.inf); C[0,0]=0; bk=np.zeros((nA+1,nB+1),np.int8)
        DD=np.sum((PAc[:,None]-PBc[None])**2,axis=2)
        for ii in range(nA+1):
            for jj in range(nB+1):
                if ii>0 and C[ii-1,jj]+DD[ii,jj]<C[ii,jj]: C[ii,jj]=C[ii-1,jj]+DD[ii,jj]; bk[ii,jj]=0
                if jj>0 and C[ii,jj-1]+DD[ii,jj]<C[ii,jj]: C[ii,jj]=C[ii,jj-1]+DD[ii,jj]; bk[ii,jj]=1
        path=[]; ii,jj=nA,nB
        while ii>0 or jj>0:
            path.append(bk[ii,jj]);
            if bk[ii,jj]==0: ii-=1
            else: jj-=1
        i=j=0
        for typ in path[::-1]:
            if typ==0:
                newfaces.append([A_[i%nA],A_[(i+1)%nA],B_[j%nB]]); i+=1
            else:
                newfaces.append([A_[i%nA],B_[(j+1)%nB],B_[j%nB]]); j+=1
            kinds.append("strip"); groups.append(f"{side}z{len(lr)}")
NV=max(nextv[0],len(P)); V=np.zeros((NV,3)); V[:len(P)]=P
for i,p in newpos.items(): V[i]=p
print("slots left (loose)",len(slots),"total verts",NV)
cen=np.array([V[fc].mean(0) for fc in newfaces]); _,_,fi,_=So.query(cen); sn=So.fn[fi]; flip=0; sgn=[]
for k,fc in enumerate(newfaces):
    a,b,c=V[fc[0]],V[fc[1]],V[fc[2]]; n=np.cross(b-a,c-a)
    if len(fc)==4: n=n+np.cross(c-a,V[fc[3]]-a)
    sgn.append(np.sign(n@sn[k]))
sgn=np.array(sgn); gr_=np.array(groups)
for g_ in np.unique(gr_):
    m=gr_==g_; vote=sgn[m].sum()
    print("  winding group",g_,"faces",m.sum(),"agree",int((sgn[m]>0).sum()))
    if vote<0:
        for k in np.nonzero(m)[0]: newfaces[k]=newfaces[k][::-1]
        flip+=m.sum()
# flips: strip triangles' shared diagonals turned where that makes both face her surface better
def tscore(fc):
    p=V[fc]; n=np.cross(p[1]-p[0],p[2]-p[0]); a=np.linalg.norm(n)
    if a<1e-14: return -1.0
    c=p.mean(0); _,_,fi_,_=So.query(c[None]); return float(n@So.fn[fi_[0]]/a)
alle=set()
for fc in [list(polys[i]) for i in kept]+newfaces:
    for k in range(len(fc)): alle.add((min(fc[k],fc[(k+1)%len(fc)]),max(fc[k],fc[(k+1)%len(fc)])))
strip_ids=[k for k,kd in enumerate(kinds) if kd=="strip"]
nflip=0
for rnd in range(30):
    em={}
    for k in strip_ids:
        fc=newfaces[k]
        for j in range(3): em.setdefault((min(fc[j],fc[(j+1)%3]),max(fc[j],fc[(j+1)%3])),[]).append(k)
    changed=0; touched=set()
    for (u,v),l in em.items():
        if len(l)!=2 or l[0] in touched or l[1] in touched: continue
        t1,t2=newfaces[l[0]],newfaces[l[1]]
        if (u,v) not in [(t1[j],t1[(j+1)%3]) for j in range(3)]: t1,t2=t2,t1; l=l[::-1]
        if (u,v) not in [(t1[j],t1[(j+1)%3]) for j in range(3)] or (v,u) not in [(t2[j],t2[(j+1)%3]) for j in range(3)]: continue
        a=[x for x in t1 if x not in (u,v)][0]; b=[x for x in t2 if x not in (u,v)][0]
        if a==b or (min(a,b),max(a,b)) in alle: continue
        old_=min(tscore(t1),tscore(t2)); n1,n2=[u,b,a],[b,v,a]; new_=min(tscore(n1),tscore(n2))
        if new_>old_+0.05:
            newfaces[l[0]]=n1; newfaces[l[1]]=n2; alle.discard((min(u,v),max(u,v))); alle.add((min(a,b),max(a,b))); changed+=1; touched.update(l)
    nflip+=changed
    if not changed: break
print("strip flips",nflip)
# untangle: new vertices of folded faces at the seam faired over the joined mesh (ring held), back onto her smoothed surface
oldnear=[list(polys[i]) for i in kept if np.isin(polys[i],list(ringverts)).any()]
allf=newfaces+oldnear; nnew=len(newfaces)
isnew=np.zeros(len(V),bool); isnew[list(newpos.keys())]=True
from scipy.sparse import coo_matrix
rows=[];cols=[]
for fc in allf:
    for k in range(len(fc)): rows+= [fc[k],fc[(k+1)%len(fc)]]; cols+=[fc[(k+1)%len(fc)],fc[k]]
Aj=coo_matrix((np.ones(len(rows)),(rows,cols)),shape=(len(V),len(V))).tocsr(); Aj.data[:]=1; dg=np.asarray(Aj.sum(1)).ravel(); Wj=sp.diags(1/np.maximum(dg,1))@Aj
def foldv():
    fn=[]
    for fc in allf:
        p=V[fc]; n=np.cross(p[1]-p[0],p[2]-p[0])
        if len(fc)==4: n=n+np.cross(p[2]-p[0],p[3]-p[0])
        fn.append(n/max(np.linalg.norm(n),1e-15))
    fn=np.array(fn); em={}
    for i,fc in enumerate(allf):
        w=wid[fc] if max(fc)<len(wid) and False else fc
        for k in range(len(fc)): em.setdefault((min(fc[k],fc[(k+1)%len(fc)]),max(fc[k],fc[(k+1)%len(fc)])),[]).append(i)
    bad=set()
    for e,l in em.items():
        if len(l)==2 and fn[l[0]]@fn[l[1]]<np.cos(np.radians(50)): bad.update(allf[l[0]]); bad.update(allf[l[1]])
    return np.array(sorted(bad),int)
it=-1
for it in range(int(os.environ.get("UNT","0"))):
    bv=foldv()
    if not len(bv): break
    sel=np.zeros(len(V),bool); sel[bv]=True; sel=sel|(Aj@sel>0); sel=sel|(Aj@sel>0); sel&=isnew
    for _ in range(3): V=np.where(sel[:,None],V+0.5*(Wj@V-V),V)
    V[sel]=Ssm.query(V[sel])[0]
print("untangle rounds",it,"remaining fold verts",len(foldv()))
kinds=np.array(kinds); print("flipped",flip,"of",len(newfaces),"strip",int((kinds=="strip").sum()))
np.savez(G+r"\graft_geom.npz",V=V,kept=kept,newfaces=np.array([fc+[-1]*(4-len(fc)) for fc in newfaces]),kinds=kinds,ring=np.array(sorted(ringverts)),slots_left=np.array(slots,int),nold=len(P),inpatch=inpatch)
