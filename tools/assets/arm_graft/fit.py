# Her arm-root graft (Body 1, armor 18 g1, 22 Oct 2026). See tools/assets/heroine_arm_graft.py.
# Stage 1: fit study. Fits the MakeHuman base's arm patch to her lightly smoothed sculpt, per side.
import os, sys, numpy as np, scipy.sparse as sp, scipy.sparse.linalg as spl
from scipy.spatial import cKDTree
from geo import *; from her_load import load_her, G; from base_load import load_base
d=load_her(); P=d["P"]; T=d["T"]; VG=d["VG"]; nm=list(d["names"]); bn=list(d["bn"])
# weld
key=np.round(P/1e-6).astype(np.int64); _,wid,_=np.unique(key,axis=0,return_inverse=True,return_counts=True); wid=wid.ravel()
nW=wid.max()+1; rep=np.zeros(nW,int); rep[wid]=np.arange(len(P)); Pw=P[rep]
Tw=wid[T]; ok=(Tw[:,0]!=Tw[:,1])&(Tw[:,1]!=Tw[:,2])&(Tw[:,0]!=Tw[:,2]); Tw=Tw[ok]
Ew=edges_of(Tw)
e3=np.sort(np.concatenate([Tw[:,[0,1]],Tw[:,[1,2]],Tw[:,[2,0]]]),1); ue,ec=np.unique(e3,axis=0,return_counts=True)
bv=np.zeros(nW,bool); bv[ue[ec==1].ravel()]=True
Ps=taubin(Pw,Ew,bv,it=10)
Ss=Surf(Ps,Tw)
HN=np.zeros_like(Ps)
for kk in range(3): np.add.at(HN,Tw[:,kk],Ss.fn*Ss.fa[:,None])
HN/=np.maximum(np.linalg.norm(HN,axis=1)[:,None],1e-15)
VGw=VG[rep]
js,BP,BT,BUV,BTU,BTG=load_base(); bgroups=js["groups"]
BQ=np.c_[BP[:,0],-BP[:,2],BP[:,1]]
bodyT=BT[BTG==0]; BF=np.c_[bodyT[0::2],np.zeros(len(bodyT)//2,int)]
# quads from consecutive tri pairs: tri a=(p,q,r), tri b shares 2; build quad ordering
quads=[]
for a,b in zip(bodyT[0::2],bodyT[1::2]):
    x=[v for v in b if v not in a][0]; sa=list(a)
    # find edge of a shared with b, insert x between its ends
    for i in range(3):
        u,v=sa[i],sa[(i+1)%3]
        if u in b and v in b: quads.append(sa[:i+1]+[x]+sa[i+1:]); break
BF=np.array(quads)
def bjoint(n): v=np.unique(BT[BTG==bgroups.index(n)]); return BQ[v].mean(0)
def bone(n): return d["bh"][bn.index(n)]
def similarity(A,B,scale=True):
    ca,cb=A.mean(0),B.mean(0); A0,B0=A-ca,B-cb; U,S,Vt=np.linalg.svd(A0.T@B0); D=np.eye(3); D[2,2]=np.sign(np.linalg.det(U@Vt))
    R=(U@D@Vt).T; s=(S*np.diag(D)).sum()/(A0**2).sum() if scale else 1.0
    return lambda X: s*(X-ca)@R.T+cb, s
def armframe(side):
    S=bone(f"upperarm_{side}"); E=bone(f"lowerarm_{side}"); u=(E-S)/np.linalg.norm(E-S); L=np.linalg.norm(E-S)
    up=np.array([0,0,1.]); up=up-u*(up@u); up/=np.linalg.norm(up); fr=np.cross(u,up)
    if fr[1]>0: fr=-fr     # front is -y
    return S,E,u,L,up,fr
def tphi(X,side):
    S,E,u,L,up,fr=armframe(side); dd=X-S; t=(dd@u)/L; rr=dd-np.outer(dd@u,u)
    return t,np.degrees(np.arctan2(rr@fr,rr@up)),np.linalg.norm(rr,axis=1)
def her_patch(side):
    sx=-1 if side=="r" else 1
    ua=VGw[:,nm.index(f"upperarm_{side}")]; cl=VGw[:,nm.index(f"clavicle_{side}")]
    t,phi,rad=tphi(Pw,side)
    xmid=abs(bone(f"clavicle_{side}")[0]+d["bt"][bn.index(f"clavicle_{side}")][0])/2
    pit=((t>-0.15)&(t<0.4)&(np.abs(phi)>110)&(rad<0.10))|((t>-0.05)&(t<0.35)&(np.abs(phi)>150)&(rad<0.125))
    ins=(sx*Pw[:,0]>0)&((((ua>0.2)&(t<=1.0))|((cl>0.3)&(sx*Pw[:,0]>xmid))|pit))
    fin=ins[Tw].all(1)
    # face adjacency components: keep largest inside comp, fill holes (outside comps not the largest outside)
    from scipy.sparse.csgraph import connected_components
    fe={}
    for fi,tr in enumerate(Tw):
        for a,b in ((tr[0],tr[1]),(tr[1],tr[2]),(tr[2],tr[0])): fe.setdefault((min(a,b),max(a,b)),[]).append(fi)
    pairs=np.array([v for v in fe.values() if len(v)==2])
    def comps(mask):
        m=mask[pairs[:,0]]&mask[pairs[:,1]]; pp=pairs[m]; n=len(Tw)
        A=sp.coo_matrix((np.ones(len(pp)),(pp[:,0],pp[:,1])),shape=(n,n)); _,lab=connected_components(A,directed=False); return lab
    lab=comps(fin); c=np.bincount(lab[fin]); fin=fin&(lab==np.argmax(c)) if True else fin
    lo=comps(~fin); co=np.bincount(lo[~fin],minlength=lo.max()+1); adj=np.zeros(co.size,bool)
    m=fin[pairs[:,0]]!=fin[pairs[:,1]]; ob=np.where(fin[pairs[m,0]],pairs[m,1],pairs[m,0]); adj[lo[ob]]=True
    small=(co<300)&adj; fin=fin|((~fin)&small[lo])
    return fin
res={}
for side in ("r","l"):
    sx=-1 if side=="r" else 1; s_=side
    fin=her_patch(side); pv=np.unique(Tw[fin])
    # init similarity from joints
    A=np.array([bjoint(f"joint-{s_}-shoulder"),bjoint(f"joint-{s_}-elbow"),bjoint(f"joint-{s_}-clavicle"),bjoint("joint-neck")])
    B=np.array([bone(f"upperarm_{s_}"),bone(f"lowerarm_{s_}"),bone(f"clavicle_{s_}"),bone("neck_01")])
    f0,s0=similarity(A,B); X=f0(BQ)
    # rigid+scale ICP on arm region
    t_h,_,rad_h=tphi(Ps,side); herarm=(sx*Ps[:,0]>0)&(t_h>-0.2)&(t_h<1.1)&(rad_h<0.1)
    kd_h=cKDTree(Ps[herarm]); bodyv=np.unique(BF)
    for it in range(30):
        tb,_,rb=tphi(X,side); sel=bodyv[(sx*X[bodyv,0]>0)&(tb[bodyv]>-0.1)&(tb[bodyv]<1.05)&(rb[bodyv]<0.1)]
        dd,j=kd_h.query(X[sel]); keep=dd<np.percentile(dd,90)
        f1,_=similarity(X[sel][keep],Ps[herarm][j[keep]]); X=f1(X)
    # base fit region: quads with all verts within 3.5 cm of her patch
    kd_p=cKDTree(Ps[pv]); dq=kd_p.query(X)[0]
    qin=(dq[BF]<0.05).all(1)
    used=np.unique(BF[qin]); remap=-np.ones(len(X),int); remap[used]=np.arange(len(used))
    V=X[used].copy(); F=remap[BF[qin]]
    def nonrigid(V,F,alphas,iters,beta=0.3):
        E=edges_of(F); n=len(V); Lp=sp.eye(n)-umbrella(n,E); LtL=(Lp.T@Lp).tocsr(); V0=V.copy(); X=V.copy()
        hp=Ps[pv]
        for a in alphas:
            for _ in range(iters):
                C,dist,fi,_=Ss.query(X)
                Nq=np.cross(X[F[:,2]]-X[F[:,0]],X[F[:,3]]-X[F[:,1]]); NV=np.zeros_like(X)
                for kk in range(4): np.add.at(NV,F[:,kk],Nq)
                NV/=np.maximum(np.linalg.norm(NV,axis=1)[:,None],1e-15)
                comp=(NV*Ss.fn[fi]).sum(1)
                w=np.where(dist<0.03,1.0,0.1)*(comp>0.5)
                kdx=cKDTree(X); dj,ij=kdx.query(hp); m=(dj<0.02)&((NV[ij]*HN[pv]).sum(1)>0.5)
                R=sp.coo_matrix((np.ones(m.sum()),(np.arange(m.sum()),ij[m])),shape=(m.sum(),n)).tocsr()
                Amat=(sp.diags(w)+a*LtL+beta*(R.T@R)).tocsc()
                rhs=w[:,None]*C+a*(LtL@V0)+beta*(R.T@hp[m])
                lu=spl.splu(Amat); X=np.column_stack([lu.solve(rhs[:,k]) for k in range(3)])
        return X
    Vc=nonrigid(V,F,[30,10,3,1],4,beta=1.0)
    Vs,Fs=V,F; Vf=Vc
    for lev in range(2): Vf,Fs=catmull_clark(Vf,Fs)
    Vf2=nonrigid(Vf,Fs,eval(os.environ.get("RA","[10,3]")),3,beta=float(os.environ.get("RB","0.3")))
    # tangential relax: umbrella smoothing then back onto her smoothed surface
    Wu=umbrella(len(Vf2),edges_of(Fs)); Vr=Vf2.copy()
    for _ in range(6): Vr=Ss.query(Vr+0.5*(Wu@Vr-Vr))[0]
    # unfold: fair the few folded quads in the pinched pit (and two rings round them), the rest held
    Eu=edges_of(Fs); Wu=umbrella(len(Vf2),Eu); Au=adjacency(len(Vf2),Eu); nfix=0
    for _ in range(30):
        n=np.cross(Vf2[Fs[:,2]]-Vf2[Fs[:,0]],Vf2[Fs[:,3]]-Vf2[Fs[:,1]]); n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-15)
        em={}
        for i,q in enumerate(Fs):
            for k in range(4): em.setdefault((min(q[k],q[(k+1)%4]),max(q[k],q[(k+1)%4])),[]).append(i)
        pr=np.array([v for v in em.values() if len(v)==2]); a=(n[pr[:,0]]*n[pr[:,1]]).sum(1)<np.cos(np.radians(40))
        if not a.any(): break
        sel=np.zeros(len(Vf2),bool); sel[np.unique(Fs[pr[a]].ravel())]=True
        for _r in range(2): sel=sel|(Au@sel>0)
        nfix+=1
        for _s in range(5): Vf2=np.where(sel[:,None],Vf2+0.5*(Wu@Vf2-Vf2),Vf2)
    print(side,"unfold rounds",nfix)
    Vf2_pre=Vf2
    res[side]=dict(fin=fin,pv=pv,Vc=Vc,F=F,Vf=Vf2,Vfit=Vf2_pre,Fs=Fs,Vsub=Vf,used=used)
    print(side,"patch faces",fin.sum(),"verts",len(pv),"base quads",len(F),"sub quads",len(Fs))
np.savez(G+r"\fit.npz",**{f"{s}_{k}":v for s in res for k,v in res[s].items()},Ps=Ps,Pw=Pw,Tw=Tw,wid=wid)
