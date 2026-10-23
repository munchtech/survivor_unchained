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
ARM_TO=os.environ.get("ARM_TO","elbow")
def her_patch(side):
    sx=-1 if side=="r" else 1
    ua=VGw[:,nm.index(f"upperarm_{side}")]; cl=VGw[:,nm.index(f"clavicle_{side}")]
    t,phi,rad=tphi(Pw,side)
    # the cut over the clavicle: TRAP = fraction along the clavicle bone (0.5 = mid-clavicle, g1); below it, the
    # trap/clavicle skin joins where clavicle weight > TRAP_CL (g2c: 0.3 and 0.15, the strip off the trap's top)
    ch,ct_=bone(f"clavicle_{side}"),d["bt"][bn.index(f"clavicle_{side}")]
    xmid=abs(ch[0]+(ct_[0]-ch[0])*float(os.environ.get("TRAP","0.5")))
    pit=((t>-0.15)&(t<0.4)&(np.abs(phi)>110)&(rad<0.10))|((t>-0.05)&(t<0.35)&(np.abs(phi)>150)&(rad<0.125))
    clt=(cl>0.3)|((cl>float(os.environ.get("TRAP_CL","0.3")))&(Pw[:,2]>ch[2]-0.04))
    ins=(sx*Pw[:,0]>0)&((((ua>0.2)&(t<=1.0))|(clt&(sx*Pw[:,0]>xmid))|pit))
    if ARM_TO=="wrist":
        # g2c: the forearm to WRIST_TF of the lowerarm bone (1.0 = the wrist joint); the hand stays hers
        la=VGw[:,nm.index(f"lowerarm_{side}")]; hw=VGw[:,nm.index(f"hand_{side}")]
        E_=bone(f"lowerarm_{side}"); H_=bone(f"hand_{side}"); uf=(H_-E_)/np.linalg.norm(H_-E_); tf=((Pw-E_)@uf)/np.linalg.norm(H_-E_)
        rf=np.linalg.norm((Pw-E_)-np.outer((Pw-E_)@uf,uf),axis=1)
        ins|=(sx*Pw[:,0]>0)&(tf>-0.3)&(tf<=float(os.environ.get("WRIST_TF","0.9")))&(rf<0.07)&((la+ua)>0.5)&(hw<float(os.environ.get("WRIST_HW","0.35")))
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
def loopcut(V,F,side,lmin,ok=None):
    E_=bone(f"lowerarm_{side}"); H_=bone(f"hand_{side}"); uf=(H_-E_)/np.linalg.norm(H_-E_); Lf=np.linalg.norm(H_-E_)
    key=lambda a,b:(a,b) if a<b else (b,a)
    eq={}
    for qi,q in enumerate(F):
        for k in range(4): eq.setdefault(key(q[k],q[(k+1)%4]),[]).append((qi,k))
    seeds=[]
    for (a,b) in eq:
        v=V[b]-V[a]; l=np.linalg.norm(v); m=(V[a]+V[b])/2; tf=(m-E_)@uf/Lf; rf=np.linalg.norm((m-E_)-((m-E_)@uf)*uf)
        if ok is not None and not all(ok[qi] for qi,_ in eq[(a,b)]): continue
        if l>lmin and abs(v@uf)/l>0.7 and -0.05<tf<0.75 and rf<0.07: seeds.append((a,b))
    cut=set(); stack=list(seeds)
    while stack:
        e=stack.pop()
        if e in cut: continue
        cut.add(e)
        for qi,k in eq[e]:
            q=F[qi]; o=key(q[(k+2)%4],q[(k+3)%4])
            if o not in cut: stack.append(o)
    mid={}; V=list(V)
    for e in cut: mid[e]=len(V); V.append((V[e[0]]+V[e[1]])/2)
    V=np.array(V); nm_=np.array(list(mid.values()),int); V[nm_]=Ss.query(V[nm_])[0]
    out=[]
    for q in F:
        c=[mid.get(key(q[k],q[(k+1)%4])) for k in range(4)]
        if c[0] is not None and c[2] is not None and c[1] is not None and c[3] is not None:
            ctr=len(V); V=np.vstack([V,Ss.query(V[q].mean(0)[None])[0]])
            out+= [[q[0],c[0],ctr,c[3]],[c[0],q[1],c[1],ctr],[ctr,c[1],q[2],c[2]],[c[3],ctr,c[2],q[3]]]
        elif c[0] is not None and c[2] is not None: out+= [[q[0],c[0],c[2],q[3]],[c[0],q[1],q[2],c[2]]]
        elif c[1] is not None and c[3] is not None: out+= [[q[0],q[1],c[1],c[3]],[c[3],c[1],q[2],q[3]]]
        else: out.append(list(q))
    print(side,"loop cut: seed edges",len(seeds),"cut edges",len(cut),"quads",len(F),"->",len(out))
    return V,np.array(out)
def wrist_coarsen(Vf2,Fs,F,Vc,side,tc):
    """g2d: the patch's wrist end coarsened round the arm (half the ring count; along-arm rows kept) over the base quads
    whose centre lies past tc of the lowerarm bone, with one ring of base quads as a 4:2 quad transition (no triangles).
    Fs must be the two-level Catmull-Clark of the base quads F (face 16*fi+4*i+j)."""
    E_=bone(f"lowerarm_{side}"); H_=bone(f"hand_{side}"); uf=(H_-E_)/np.linalg.norm(H_-E_); Lf=np.linalg.norm(H_-E_)
    nb=len(F); assert len(Fs)==16*nb
    # grid coordinates (0..4) of every level-2 vertex of each base quad
    Pc=np.array([[0,0],[4,0],[4,4],[0,4]],float); grid=[dict() for _ in range(nb)]
    for fi in range(nb):
        for i in range(4):
            Q=[Pc[i],(Pc[i]+Pc[(i+1)%4])/2,Pc.mean(0),(Pc[i]+Pc[(i-1)%4])/2]
            for j in range(4):
                R=[Q[j],(Q[j]+Q[(j+1)%4])/2,np.mean(Q,0),(Q[j]+Q[(j-1)%4])/2]
                for v,p in zip(Fs[16*fi+4*i+j],R): grid[fi][(int(round(p[0])),int(round(p[1])))]=v
    ctr=Vc[F].mean(1); tfc=((ctr-E_)@uf)/Lf; rfc=np.linalg.norm((ctr-E_)-np.outer((ctr-E_)@uf,uf),axis=1)
    d1=Vc[F[:,1]]-Vc[F[:,0]]; d3=Vc[F[:,3]]-Vc[F[:,0]]
    UC=np.abs(d1@uf)/np.linalg.norm(d1,axis=1)<np.abs(d3@uf)/np.linalg.norm(d3,axis=1)   # grid u runs round the arm
    key=lambda a,b:(a,b) if a<b else (b,a)
    em={}
    for fi,q in enumerate(F):
        for k in range(4): em.setdefault(key(q[k],q[(k+1)%4]),[]).append((fi,k))
    def nbr(fi,k):
        l=[x for x in em[key(F[fi][k],F[fi][(k+1)%4])] if x[0]!=fi]; return l[0][0] if l else -1
    # whole rings of base quads (walked across their along-the-arm edges): the ring nearest tc starts the coarse end,
    # the ring before it is the transition, everything past it (to tf 1.08; beyond is dropped, the trim cuts there) coarse
    def ring(seed):
        R=[seed]; seen={seed}; st=[seed]
        while st:
            fi=st.pop()
            for k in ((1,3) if UC[fi] else (0,2)):
                n_=nbr(fi,k)
                if n_>=0 and n_ not in seen and rfc[n_]<0.09: seen.add(n_); R.append(n_); st.append(n_)
        return R
    cand=np.nonzero((rfc<0.07)&(np.abs(tfc-tc)<0.05))[0]; R0=ring(cand[np.argmin(np.abs(tfc[cand]-tc))])
    R0s=set(R0); Tr=set()
    for fi in R0:
        for k in ((0,2) if UC[fi] else (1,3)):
            n_=nbr(fi,k)
            if n_>=0 and n_ not in R0s and tfc[n_]<tfc[fi]: Tr.add(n_)
    reach=np.zeros(nb,bool); reach[R0]=True; st=list(R0)
    while st:
        fi=st.pop()
        for k in range(4):
            n_=nbr(fi,k)
            if n_>=0 and not reach[n_] and n_ not in Tr: reach[n_]=True; st.append(n_)
    drop=reach&(tfc>=1.08); C=reach&~drop
    print(side,"wrist coarsen: ring",len(R0),"tf %.2f..%.2f"%(tfc[R0].min(),tfc[R0].max()),"transition ring",len(Tr),"dropped past tf 1.08",int(drop.sum()))
    ccbad=sum(1 for (a,b),l in em.items() if len(l)==2 and C[l[0][0]] and C[l[1][0]] and ((l[0][1]%2==0)==UC[l[0][0]])!=((l[1][1]%2==0)==UC[l[1][0]]))
    print(side,"coarse-coarse edges disagreeing round/along",ccbad)
    for it in range(20):
        T=np.zeros(nb,bool); fs=np.full(nb,-1); bad=[]
        for fi in np.nonzero(~C&~drop)[0]:
            ks=[k for k in range(4) if nbr(fi,k)>=0 and C[nbr(fi,k)]]
            if ks: T[fi]=True; fs[fi]=(ks[0]+2)%4 if len(ks)==1 else -1
            if len(ks)>1: bad.append(fi)
        for fi in np.nonzero(T)[0]:
            if fi in bad: continue
            k=fs[fi]; o=nbr(fi,k)
            if o>=0 and (C[o] or T[o]): bad.append(fi); continue
            cq=nbr(fi,(k+2)%4); kc=[x[1] for x in em[key(F[fi][(k+2)%4],F[fi][(k+3)%4])] if x[0]==cq][0]
            if (kc%2==0)!=UC[cq]: bad.append(fi); continue
            for kl in ((k+1)%4,(k+3)%4):
                n_=nbr(fi,kl)
                if n_>=0 and not T[n_]: bad.append(fi)
        if not bad: break
        C[bad]=True
    assert not bad, "wrist coarsen: no conforming transition"
    out=[]; fine=[]
    for fi in range(nb):
        g=grid[fi]
        if drop[fi]: continue
        if not C[fi] and not T[fi]: out+=list(Fs[16*fi:16*fi+16]); fine+=[True]*16; continue
        n0_=len(out)
        if C[fi]:
            # which grid axis runs round the arm: the one less aligned with the forearm
            ucirc=UC[fi]
            for a in (0,2):
                for b in range(4):
                    if ucirc: out.append([g[(a,b)],g[(a+2,b)],g[(a+2,b+1)],g[(a,b+1)]])
                    else: out.append([g[(b,a)],g[(b+1,a)],g[(b+1,a+2)],g[(b,a+2)]])
            fine+=[False]*(len(out)-n0_); continue
        k=fs[fi]; o=Pc[k]; ex=(Pc[(k+1)%4]-o)/4; ey=(Pc[(k+3)%4]-o)/4
        G_=lambda x,y: g[tuple(int(round(c)) for c in o+x*ex+y*ey)]
        for y in (0,1):
            for x in range(4): out.append([G_(x,y),G_(x+1,y),G_(x+1,y+1),G_(x,y+1)])
        f_=[G_(x,2) for x in range(5)]; c0,c1,c2=G_(0,4),G_(2,4),G_(4,4); a,m,b=G_(1,3),G_(2,3),G_(3,3)
        out+=[[f_[0],f_[1],a,c0],[f_[1],f_[2],m,a],[f_[2],f_[3],b,m],[f_[3],f_[4],c2,b],[a,m,c1,c0],[m,b,c2,c1]]
        fine+=[False]*(len(out)-n0_)
    print(side,"wrist coarsen: base quads coarse",int(C.sum()),"transition",int(T.sum()),"quads",len(Fs),"->",len(out))
    return np.array(out),np.array(fine)
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
    if ARM_TO=="wrist":
        # g2c: the base's forearm turned about its elbow onto hers (smooth over +-4 cm of the elbow), then a rigid ICP of it
        bjX=lambda n: X[np.unique(BT[BTG==bgroups.index(n)])].mean(0)   # base joints where the ICP left them
        bE,bS,bW=bjX(f"joint-{s_}-elbow"),bjX(f"joint-{s_}-shoulder"),bjX(f"joint-{s_}-hand")
        hE=bone(f"lowerarm_{s_}"); hW=bone(f"hand_{s_}")
        a_=(bW-bE)/np.linalg.norm(bW-bE); b_=(hW-hE)/np.linalg.norm(hW-hE); ax=np.cross(a_,b_); sn=np.linalg.norm(ax); cs=a_@b_
        K=np.array([[0,-ax[2],ax[1]],[ax[2],0,-ax[0]],[-ax[1],ax[0],0]])/max(sn,1e-12); ang=np.arctan2(sn,cs)
        ua_=(bE-bS)/np.linalg.norm(bE-bS); sel_=(X-bE)@ua_
        print(side,"forearm turn %.1f deg"%np.degrees(ang),"base S E W",np.round([bS,bE,bW],3).tolist(),"her",np.round([bone(f"upperarm_{s_}"),hE,hW],3).tolist())
        kx=ax/max(sn,1e-12)
        def turn(Y,w):
            th=(ang*w)[:,None]; Yd=Y-bE
            return bE+Yd*np.cos(th)+np.cross(kx,Yd)*np.sin(th)+np.outer(Yd@kx,kx)*(1-np.cos(th))
        wgt=np.clip((sel_+0.04)/0.08,0,1); wgt=wgt*wgt*(3-2*wgt)*((sx*X[:,0]>0)&(np.linalg.norm(X-bE,axis=1)<0.45))
        X=turn(X,wgt)
        tfX=((X-hE)@b_)/np.linalg.norm(hW-hE)
        E2=bone(f"lowerarm_{s_}"); tfh=((Ps-E2)@b_)/np.linalg.norm(hW-hE); rfh=np.linalg.norm((Ps-E2)-np.outer((Ps-E2)@b_,b_),axis=1)
        herfa=(sx*Ps[:,0]>0)&(tfh>0.1)&(tfh<0.95)&(rfh<0.07); kd_f=cKDTree(Ps[herfa])
        rfX=np.linalg.norm((X-hE)-np.outer((X-hE)@b_,b_),axis=1)
        fa=bodyv[(sx*X[bodyv,0]>0)&(tfX[bodyv]>0.1)&(tfX[bodyv]<0.95)&(rfX[bodyv]<0.07)]
        Xf=X.copy()
        for it in range(20):
            dd,j=kd_f.query(Xf[fa]); keep=dd<np.percentile(dd,90)
            f2,_=similarity(Xf[fa][keep],Ps[herfa][j[keep]],scale=False); Xf=f2(Xf)
        w2=np.clip((tfX+0.15)/0.3,0,1); w2=w2*w2*(3-2*w2)*((sx*X[:,0]>0)&(rfX<0.15)); X=X+(Xf-X)*w2[:,None]
        print(side,"forearm ICP mean dist mm %.1f"%(kd_f.query(X[fa])[0].mean()*1000))
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
    if ARM_TO=="wrist" and float(os.environ.get("WRIST_TC","0"))>0:
        if os.environ.get("WC_DUMP"): np.savez(G+rf"\wc_{side}.npz",Vf2=Vf2,Fs=Fs,F=F,Vc=Vc,E=bone(f"lowerarm_{side}"),H=bone(f"hand_{side}"))
        Fs,fine_=wrist_coarsen(Vf2,Fs,F,Vc,side,float(os.environ["WRIST_TC"]))
    else: fine_=None
    if ARM_TO=="wrist" and float(os.environ.get("FA_CUT","0.5"))>0:
        # g2c: the base's forearm loops are 0.75-0.8 cm apart (around it 0.3): loop cuts through every edge ring whose
        # along-the-forearm edges there are longer than FA_CUT cm, new points on her smoothed surface
        Vf2,Fs=loopcut(Vf2,Fs,side,float(os.environ.get("FA_CUT","0.5"))/100,fine_)
    Vf2_pre=Vf2
    res[side]=dict(fin=fin,pv=pv,Vc=Vc,F=F,Vf=Vf2,Vfit=Vf2_pre,Fs=Fs,Vsub=Vf,used=used)
    print(side,"patch faces",fin.sum(),"verts",len(pv),"base quads",len(F),"sub quads",len(Fs))
np.savez(G+r"\fit.npz",**{f"{s}_{k}":v for s in res for k,v in res[s].items()},Ps=Ps,Pw=Pw,Tw=Tw,wid=wid)
