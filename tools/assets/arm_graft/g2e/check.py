# Body 1 g2e step 5: seam numbers. Colour across every UV seam (her paint sampled 1.5 mm into each face from the edge's
# middle, CIE76 delta E in Lab), by kind: the torso ring (kept face | patch face), seams inside the patch, and, as the
# noise floor, plain edges (no UV split) of her kept skin within 3 cm of the ring. Normals: at each torso-ring vertex the
# angle between its kept faces' corner normals and its patch faces' corner normals.
#   python check.py <dump.npz> <body png> <graft png> <graft_geom.npz> [label]
# (dump = b_dump.py of the blend; the PNGs = the images that blend's two skin materials sample)
import sys, numpy as np, cv2
from collections import defaultdict
d=np.load(sys.argv[1]); IM=[cv2.imread(p)[::-1,:,::-1].astype(np.float64)/255 for p in sys.argv[2:4]]; g=np.load(sys.argv[4])
lab=sys.argv[5] if len(sys.argv)>5 else ""
P=d["P"]; ls,lt,lv,mi,uv,cn=d["ls"],d["lt"],d["lv"],d["mi"],d["uv"],d["cn"]; nk=len(g["kept"]); nf=len(ls); ring=set(g["ring"].tolist())
def sample(img,q):
    H,W=img.shape[:2]; x=q[0]*W-0.5; y=q[1]*H-0.5; x0=int(np.floor(x)); y0=int(np.floor(y)); fx=x-x0; fy=y-y0
    G=lambda yy,xx: img[min(max(yy,0),H-1),min(max(xx,0),W-1)]
    return G(y0,x0)*(1-fx)*(1-fy)+G(y0,x0+1)*fx*(1-fy)+G(y0+1,x0)*(1-fx)*fy+G(y0+1,x0+1)*fx*fy
def lab_(c):
    c=np.where(c<=0.04045,c/12.92,((c+0.055)/1.055)**2.4); M=np.array([[.4124,.3576,.1805],[.2126,.7152,.0722],[.0193,.1192,.9505]])
    xyz=M@c/np.array([.9505,1,1.089]); f=np.where(xyz>0.008856,np.cbrt(xyz),7.787*xyz+16/116)
    return np.array([116*f[1]-16,500*(f[0]-f[1]),200*(f[1]-f[2])])
def colour_in(i,a,b):
    s,n=ls[i],lt[i]; f=lv[s:s+n]; p=P[f]; c=p.mean(0); m=(P[a]+P[b])/2; dv=c-m; L=np.linalg.norm(dv)
    q=m+dv/L*min(0.0015,0.45*L)
    best=None
    for k in range(1,n-1):
        A,B,C=p[0],p[k],p[k+1]; v0=B-A; v1=C-A; v2=q-A; d00=v0@v0; d01=v0@v1; d11=v1@v1; d20=v2@v0; d21=v2@v1; den=d00*d11-d01*d01
        if den<=0: continue
        w1=(d11*d20-d01*d21)/den; w2=(d00*d21-d01*d20)/den; w0=1-w1-w2; e=-min(w0,w1,w2)
        if best is None or e<best[0]: best=(e,(w0,w1,w2),(s,s+k,s+k+1))
    _,w,L3=best; q2=w[0]*uv[L3[0]]+w[1]*uv[L3[1]]+w[2]*uv[L3[2]]
    return lab_(sample(IM[mi[i]],q2))
ef=defaultdict(list)
for i in range(nf):
    s,n=ls[i],lt[i]
    for k in range(n):
        a,b=lv[s+k],lv[s+(k+1)%n]; ef[(min(a,b),max(a,b))].append((i,s+k,s+(k+1)%n))
cen_ring=P[list(ring)]
from scipy.spatial import cKDTree
kd=cKDTree(cen_ring)
res=defaultdict(list)
for (a,b),l in ef.items():
    if len(l)!=2: continue
    (i,ia,ib),(j,ja,jb)=l
    # corner uv of a and b in each face
    ua={lv[x]:uv[x] for x in (ia,ib)}; ub={lv[x]:uv[x] for x in (ja,jb)}
    split=any(np.abs(ua[v]-ub[v]).max()>1e-6 for v in (a,b)) or mi[i]!=mi[j]
    pi,pj=i>=nk,j>=nk
    if pi!=pj: kind="ring"
    elif pi and pj: kind="patch seam" if split else None
    else:
        if split: continue
        if kd.query((P[a]+P[b])/2)[0]>0.03: continue
        kind="torso plain (noise floor)"
    if kind is None: continue
    dE=np.linalg.norm(colour_in(i,a,b)-colour_in(j,a,b)); res[kind].append((dE,np.linalg.norm(P[a]-P[b])))
for k,v in res.items():
    v=np.array(v); w=v[:,1]
    print("%s %-26s edges %5d (%.1f cm): dE median %.2f p95 %.2f max %.2f"%(lab,k,len(v),w.sum()*100,np.median(v[:,0]),np.percentile(v[:,0],95),v[:,0].max()))
# normals at the ring
vk=defaultdict(list); vp=defaultdict(list)
for i in range(nf):
    s,n=ls[i],lt[i]
    for k in range(n):
        v=lv[s+k]
        if v in ring: (vp if i>=nk else vk)[v].append(cn[s+k])
ang=[]
for v in ring:
    if vk[v] and vp[v]:
        A=np.array(vk[v]); B=np.array(vp[v]); A/=np.linalg.norm(A,axis=1)[:,None]; B/=np.linalg.norm(B,axis=1)[:,None]
        ang.append(np.degrees(np.arccos(np.clip(A@B.T,-1,1))).max())
ang=np.array(ang); print("%s ring corner-normal split: %d verts, deg median %.2f p95 %.2f max %.2f"%(lab,len(ang),np.median(ang),np.percentile(ang,95),ang.max()))
