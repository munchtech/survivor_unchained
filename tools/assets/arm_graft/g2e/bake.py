# Body 1 g2e step 3: scale and pack the arm patch's islands into her atlases, then re-bake her paint onto them.
#   python bake.py <work dir> <out tex dir>
# Reads her.npz (the ORIGINAL mesh, UVs, materials), graft_data.npz + graft_geom.npz (the patch before the shape field,
# where it lies on her old surface within ~1 mm), plan.npz, unwrap.npz, old_body.npy / old_graft.npy (b_img.py).
# Islands = UV-connected patch faces. Each is scaled to the density of her kept skin of its material along the torso ring
# (area-weighted), rotated (DROT steps) for the tightest fit, and placed by FFT search in texels no kept face covers
# (kept faces rasterised, dilated KEEP_PAD px), islands 2 PAD px apart. If a material's islands do not fit, the density
# steps down 3% at a time (reported). Bake: per texel (SS x SS samples), the 3D point on the patch -> closest point on her
# old arm/ring surface -> her old UV there -> her old image of that face's material (bilinear). Islands dilated by PAD/2
# (padding for the mips); every texel outside the new islands' padded masks keeps its old value.
import sys, os, numpy as np, cv2
from collections import defaultdict
from scipy.signal import fftconvolve
from scipy import ndimage
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from geo import Surf
WK, OUT = sys.argv[1], sys.argv[2]; os.makedirs(OUT, exist_ok=True)
SS=int(os.environ.get("SS","3")); DROT=float(os.environ.get("DROT","5"))
KEEP_PAD={0:int(os.environ.get("KEEP_PAD0","3")),1:int(os.environ.get("KEEP_PAD1","3"))}
PAD={0:int(os.environ.get("PAD0","8")),1:int(os.environ.get("PAD1","6"))}; DENS=float(os.environ.get("DENS","1.0"))
J=lambda f: os.path.join(WK,f)
h=dict(np.load(J("her.npz"))); D=np.load(J("graft_data.npz")); g=np.load(J("graft_geom.npz")); PL=np.load(J("plan.npz")); U=np.load(J("unwrap.npz"))
IMG={0:np.load(J("old_body.npy")).astype(np.float64),1:np.load(J("old_graft.npy")).astype(np.float64)}; RES={m:IMG[m].shape[0] for m in IMG}
V=D["V"]; fl=D["fl"]; fv=D["fv"]; dls=np.r_[0,np.cumsum(fl)[:-1]]; duv=D["uv"]; nk=int(PL["nk"]); mat=PL["mat"]; nf=len(fl)
uls,ult,uuv=U["ls"],U["lt"],U["uv"]; assert np.array_equal(ult,fl)
F=[fv[dls[i]:dls[i]+fl[i]] for i in range(nf)]
def tri_of(i): f=F[i]; return [(0,k,k+1) for k in range(1,len(f)-1)]
def area3(p): return 0.5*np.linalg.norm(sum(np.cross(p[j]-p[0],p[j+1]-p[0]) for j in range(1,len(p)-1)))
def area2(q): return 0.5*abs(sum((q[j,0]-q[0,0])*(q[j+1,1]-q[0,1])-(q[j,1]-q[0,1])*(q[j+1,0]-q[0,0]) for j in range(1,len(q)-1)))
# --- target densities: kept faces touching the torso rings, per material (uv units per metre)
ring=set(g["ring"].tolist()); tgt={}
for m in (0,1):
    A=Uv=0.0
    for i in range(nk):
        if mat[i]==m and any(v in ring for v in F[i]): A+=area3(V[F[i]]); Uv+=area2(duv[dls[i]:dls[i]+fl[i]])
    tgt[m]=np.sqrt(Uv/A)*DENS; print("target density mat %d: %.2f px/cm (%d px map)"%(m,tgt[m]*RES[m]/100,RES[m]))
# --- islands
pf=np.arange(nk,nf); lid=lambda i,k: uls[i]+k
ed=defaultdict(list)
for i in pf:
    f=F[i]
    for k in range(len(f)): ed[(min(f[k],f[(k+1)%len(f)]),max(f[k],f[(k+1)%len(f)]))].append(i)
par={i:i for i in pf}
def find(x):
    while par[x]!=x: par[x]=par[par[x]]; x=par[x]
    return x
for e,l in ed.items():
    if len(l)!=2: continue
    i,j=l; fi,fj=F[i],F[j]
    ui={fi[k]:uuv[lid(i,k)] for k in range(len(fi))}; uj={fj[k]:uuv[lid(j,k)] for k in range(len(fj))}
    if mat[i]==mat[j] and all(np.allclose(ui[v],uj[v],atol=1e-6) for v in e): par[find(i)]=find(j)
roots=defaultdict(list)
for i in pf: roots[find(i)].append(i)
isl=sorted(roots.values(),key=lambda l:(mat[l[0]],np.sign(V[F[l[0]]].mean(0)[0])))
print("islands",[(len(l),int(mat[l[0]]),"R" if V[F[l[0]]].mean(0)[0]<0 else "L") for l in isl])
newuv=np.zeros((len(uuv),2)); stat=[]
for l in isl:
    m=mat[l[0]]; A=sum(area3(V[F[i]]) for i in l); Ua=sum(area2(uuv[uls[i]:uls[i]+fl[i]]) for i in l)
    s=tgt[m]/np.sqrt(Ua/A); sv=[];aw=[]
    for i in l:
        for t in tri_of(i):
            p=V[F[i][list(t)]]; q=uuv[[uls[i]+k for k in t]]*s/tgt[m]
            e1=p[1]-p[0]; e2=p[2]-p[0]; n=np.cross(e1,e2); a=np.linalg.norm(n)/2
            if a<1e-12: continue
            x=e1/np.linalg.norm(e1); y=np.cross(n/np.linalg.norm(n),x); P2=np.array([[e1@x,e2@x],[e1@y,e2@y]]); Q=np.array([q[1]-q[0],q[2]-q[0]]).T
            sg=np.linalg.svd(Q@np.linalg.inv(P2),compute_uv=False); sv.append(sg); aw.append(a)
    sv=np.array(sv); aw=np.array(aw); an=sv[:,0]/sv[:,1]; ar=sv[:,0]*sv[:,1]
    o=np.argsort(an); c=np.cumsum(aw[o])/aw.sum(); o2=np.argsort(ar); c2=np.cumsum(aw[o2])/aw.sum()
    stat.append((len(l),m,A*1e4,an[o][np.searchsorted(c,0.5)],an[o][np.searchsorted(c,0.95)],ar[o2][np.searchsorted(c2,0.05)],ar[o2][np.searchsorted(c2,0.95)]))
    for i in l:
        r=np.arange(uls[i],uls[i]+fl[i]); newuv[r]=uuv[r]*s
for st in stat: print("island faces %d mat %d area %.0f cm2: anisotropy (area-weighted) median %.3f p95 %.3f; area scale p5 %.2f p95 %.2f"%st)
def raster(polys,res,scale=None):
    scale=res if scale is None else scale; mask=np.zeros((res,res),np.uint8)
    for q in polys:
        p=np.round(np.c_[q[:,0]*scale-0.5,res-0.5-q[:,1]*scale]*4).astype(np.int32)
        cv2.fillPoly(mask,[p],1,lineType=cv2.LINE_8,shift=2); cv2.polylines(mask,[p],True,1,1,cv2.LINE_8,shift=2)
    return mask
kept_r={}; occ={}
for m in (0,1):
    kept_r[m]=raster([duv[dls[i]:dls[i]+fl[i]] for i in range(nk) if mat[i]==m],RES[m])
    occ[m]=cv2.dilate(kept_r[m],np.ones((2*KEEP_PAD[m]+1,)*2,np.uint8))
    print("mat %d kept cover %.3f (padded %.3f)"%(m,kept_r[m].mean(),occ[m].mean()))
def rot(q,a,c): R=np.array([[np.cos(a),-np.sin(a)],[np.sin(a),np.cos(a)]]); return (q-c)@R.T
placed={}; scale_used={}
from itertools import permutations
def try_pack(m,ids,f_,order,corners):
    # greedy: each island in turn at the free spot nearest its corner, over every rotation (coarse search at 1/2 res, exact check)
    free=occ[m].copy(); pl={}
    for n,cn in zip(order,corners):
        l=isl[n]; L=np.concatenate([np.arange(uls[i],uls[i]+fl[i]) for i in l]); q=newuv[L]*f_; c=q.mean(0); best=None
        for a in np.deg2rad(np.arange(0,360,DROT)):
            r0=rot(q,a,c); off=-r0.min(0)+(PAD[m]+1)/RES[m]; r=r0+off
            sz=int(np.ceil(r.max()*RES[m]))+PAD[m]+2; sz+=sz%2
            key=(n,round(f_,4),round(float(a),4))
            if key not in mcache:
                msk=raster([r[np.searchsorted(L,uls[i]):np.searchsorted(L,uls[i])+fl[i]] for i in l],sz,RES[m])
                mcache[key]=cv2.dilate(msk,np.ones((2*PAD[m]+1,)*2,np.uint8))
            msk=mcache[key]
            fc=free.reshape(RES[m]//2,2,RES[m]//2,2).max((1,3)).astype(np.float32); mc=msk.reshape(sz//2,2,sz//2,2).max((1,3)).astype(np.float32)
            hit=fftconvolve(fc,mc[::-1,::-1],mode="valid"); cand=np.argwhere(hit<0.5)*2
            if not len(cand): continue
            tgt_=np.array(cn)*(RES[m]-sz); dd=((cand-tgt_)**2).sum(1); k=np.argmin(dd)
            if best is None or dd[k]<best[0]: best=(dd[k],a,c,off,cand[k],sz,msk)
        if best is None: return None
        _,a,c,off,yx,sz,msk=best
        assert not (free[yx[0]:yx[0]+sz,yx[1]:yx[1]+sz]&msk).any()
        free[yx[0]:yx[0]+sz,yx[1]:yx[1]+sz]|=msk; pl[n]=(a,c,off,yx,sz)
    return pl
CORN=[(0,0),(0,1),(1,0),(1,1)]
for m in (0,1):
    ids=[n for n,l in enumerate(isl) if mat[l[0]]==m]; mcache={}; f_=float(os.environ.get("F0_%d"%m,"1.0"))   # (a start below 1 skips known misses)
    while True:
        pl=None
        for order in permutations(ids):
            for cs in ([CORN[0]]*len(ids),)+tuple(permutations(CORN,len(ids)) if len(ids)<=2 else ()):
                pl=try_pack(m,ids,f_,order,cs)
                if pl: break
            if pl: break
        if pl: break
        f_*=0.97; print("mat %d: islands do not fit, density x%.3f"%(m,f_),flush=True)
        if f_<0.5: raise SystemExit("no room")
    scale_used[m]=f_
    for n,(a,c,off,yx,sz) in pl.items():
        l=isl[n]; L=np.concatenate([np.arange(uls[i],uls[i]+fl[i]) for i in l]); r=rot(newuv[L]*f_,a,c)+off
        newuv[L]=np.c_[(yx[1]+r[:,0]*RES[m])/RES[m],1-(yx[0]+sz-r[:,1]*RES[m])/RES[m]]; placed[n]=(m,np.rad2deg(a),tuple(int(x) for x in yx),sz)
    print("mat %d placed at density x%.3f (%.2f px/cm):"%(m,f_,f_*tgt[m]*RES[m]/100),{n:(round(p[1]),p[2],p[3]) for n,p in placed.items() if p[0]==m})
for m in (0,1):
    nm=raster([newuv[uls[i]:uls[i]+fl[i]] for i in pf if mat[i]==m],RES[m])
    print("mat %d new islands cover %d px, overlap with kept faces %d px, out of [0,1] %d corners"%(m,int(nm.sum()),int((nm&kept_r[m]).sum()),
          int(((newuv<0)|(newuv>1)).any(1)[np.concatenate([np.arange(uls[i],uls[i]+fl[i]) for i in pf if mat[i]==m])].sum())))
# --- bake
ls0,lt0,lv0=h["ls"],h["lt"],h["lv"]; tl=[];tf=[]
for f,(s,n) in enumerate(zip(ls0,lt0)):
    for k in range(1,n-1): tl.append((s,s+k,s+k+1)); tf.append(f)
tl=np.array(tl); tf=np.array(tf); T=lv0[tl]
near=g["inpatch"].copy(); polys0=[lv0[s:s+n] for s,n in zip(ls0,lt0)]
for i in g["kept"]:
    if any(v in ring for v in polys0[i]): near[i]=True
tm=near[tf]; S=Surf(h["P"],T[tm]); TLs=tl[tm]; TFs=tf[tm]; uv0=h["uv"]; mi0=h["mi"]
def sample(img,uv):
    H,W=img.shape[:2]; x=uv[:,0]*W-0.5; y=uv[:,1]*H-0.5; x0=np.floor(x).astype(int); y0=np.floor(y).astype(int); fx=(x-x0)[:,None]; fy=(y-y0)[:,None]
    g_=lambda yy,xx: img[np.clip(yy,0,H-1),np.clip(xx,0,W-1)]
    return g_(y0,x0)*(1-fx)*(1-fy)+g_(y0,x0+1)*fx*(1-fy)+g_(y0+1,x0)*(1-fx)*fy+g_(y0+1,x0+1)*fx*fy
new={m:IMG[m].copy() for m in IMG}; dists=[]; offs=(np.arange(SS)+0.5)/SS-0.5
for m in (0,1):
    R=RES[m]; acc=np.zeros((R,R,4)); cnt=np.zeros((R,R)); pts=[];pix=[]
    for i in pf:
        if mat[i]!=m: continue
        for t in tri_of(i):
            q=newuv[[uls[i]+k for k in t]]*R-0.5; p=V[F[i][list(t)]]
            d=(q[1,0]-q[0,0])*(q[2,1]-q[0,1])-(q[2,0]-q[0,0])*(q[1,1]-q[0,1])
            if abs(d)<1e-12: continue
            lo=np.floor(q.min(0)).astype(int); hi=np.ceil(q.max(0)).astype(int)
            xs,ys=np.meshgrid(np.arange(lo[0],hi[0]+1),np.arange(lo[1],hi[1]+1)); xs=xs.ravel(); ys=ys.ravel()
            for ox in offs:
                for oy in offs:
                    X=xs+ox; Y=ys+oy
                    b1=((X-q[0,0])*(q[2,1]-q[0,1])-(q[2,0]-q[0,0])*(Y-q[0,1]))/d; b2=((q[1,0]-q[0,0])*(Y-q[0,1])-(X-q[0,0])*(q[1,1]-q[0,1]))/d; b0=1-b1-b2
                    k=(b0>=-1e-6)&(b1>=-1e-6)&(b2>=-1e-6)
                    if k.any(): pts.append(b0[k,None]*p[0]+b1[k,None]*p[1]+b2[k,None]*p[2]); pix.append(np.c_[ys[k],xs[k]])
    pts=np.concatenate(pts); pix=np.concatenate(pix)
    _,dist,fi,bar=S.query(pts); dists.append(dist)
    ouv=(uv0[TLs[fi]]*bar[:,:,None]).sum(1); om=mi0[TFs[fi]]; col=np.zeros((len(pts),4))
    for mm in (0,1):
        s_=om==mm
        if s_.any(): col[s_]=sample(IMG[mm],ouv[s_])
    np.add.at(acc,(pix[:,0],pix[:,1]),col); np.add.at(cnt,(pix[:,0],pix[:,1]),1)
    cov=cnt>0; acc[cov]/=cnt[cov][:,None]
    kept_m=kept_r[m][::-1].astype(bool)   # raster rows top-down; images bottom-up
    zone=cv2.dilate(cov.astype(np.uint8),np.ones((PAD[m]+1,)*2,np.uint8)).astype(bool)&~kept_m
    _,(iy,ix)=ndimage.distance_transform_edt(~cov,return_indices=True)
    out=new[m]; out[zone,:3]=acc[iy[zone],ix[zone],:3]
    print("mat %d baked %d texels (%d samples), padded %d more; covered texels on kept faces %d (kept as they were)"%(m,int(cov.sum()),len(pts),int((zone&~cov).sum()),int((cov&kept_m).sum())))
    np.save(J("cov_%d.npy"%m),zone)
d=np.concatenate(dists); print("source distance mm: median %.2f p95 %.2f p99 %.2f max %.2f"%(np.median(d)*1e3,np.percentile(d,95)*1e3,np.percentile(d,99)*1e3,d.max()*1e3))
for m,name in ((0,"heroine_body_paint.png"),(1,"heroine_graft.png")):
    im=np.clip(np.round(new[m][::-1,:,:3]*255),0,255).astype(np.uint8); cv2.imwrite(os.path.join(OUT,name),im[:,:,::-1])
    ch=np.abs(np.round(new[m]*255)-np.round(IMG[m]*255)).max(2)>0; print("WROTE",name,"texels changed",int(ch.sum()))
np.savez(J("newuv.npz"),uv=newuv[np.concatenate([np.arange(uls[i],uls[i]+fl[i]) for i in pf])],nk=nk,scale=np.array([scale_used[0],scale_used[1]]),tgt=np.array([tgt[0],tgt[1]]))
print("BAKED")
