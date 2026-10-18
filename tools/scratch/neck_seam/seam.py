import sys, os; sys.path.insert(0,os.path.dirname(__file__))
from glb import *
from collections import Counter
from scipy.spatial import cKDTree
path=sys.argv[1]; uncut=float(sys.argv[2]) if len(sys.argv)>2 else 0.0
G_=G(path); g=G_.g
if uncut:
    h=[n for n in g["nodes"] if n.get("name")=="Head"][0]; t=np.array(h["translation"]); L=np.linalg.norm(t)
    h["translation"]=list(t*(L+uncut)/L)
names=[n.get("name") for n in g["nodes"]]
def bnd(idx):
    tri=idx.reshape(-1,3); e=np.sort(np.r_[tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]],axis=1)
    c=Counter(map(tuple,e)); return np.array(sorted({v for k,n in c.items() if n==1 for v in k}))
body=skinned(G_,84); head=skinned(G_,86)[0]
hi=[k for k,j in enumerate(head["joints"]) if names[j]=="Head"][0]
def wof(p,jn):
    k=[k for k,j in enumerate(p["joints"]) if names[j]==jn][0]
    return (p["w"]*(p["j"]==k)).sum(1)
hb=bnd(head["idx"])
print("head verts",len(head["rest"]),"boundary",len(hb))
# lowest boundary loop of head (neck stump edge)
z=head["rest"][hb,1]; print("head boundary rest y range %.3f..%.3f"%(z.min(),z.max()))
low=hb[head["rest"][hb,1]<z.min()+0.06]
print("low boundary verts",len(low),"rest y %.3f..%.3f"%(head["rest"][low,1].min(),head["rest"][low,1].max()))
wH=wof(head,"Head"); print("head low-boundary Head weight min/mean/max %.2f %.2f %.2f"%(wH[low].min(),wH[low].mean(),wH[low].max()))
for pi,p in enumerate(body):
    print("body prim",pi,p["mat"],len(p["rest"]))
    b=bnd(p["idx"]);
    wb=wof(p,"Head")
    T=cKDTree(p["rest"]); d,ix=T.query(head["rest"][low])
    print("  rest dist head-low-boundary -> nearest prim vert: mean %.1f max %.1f mm"%(d.mean()*1e3,d.max()*1e3))
    ds=np.linalg.norm(head["skin"][low]-p["skin"][ix],axis=1)
    print("  skinned dist same pairs: mean %.1f max %.1f mm; Head-weight diff mean %.2f max %.2f"%(ds.mean()*1e3,ds.max()*1e3,np.abs(wH[low]-wb[ix]).mean(),np.abs(wH[low]-wb[ix]).max()))
    # how many of the head's own verts lie near prim verts at rest (overlap band) and their weight difference
    d2,ix2=T.query(head["rest"])
    near=d2<0.004
    if near.sum():
        dw=np.abs(wH[near]-wb[ix2[near]]); ds2=np.linalg.norm(head["skin"][near]-p["skin"][ix2[near]],axis=1)
        print("  head verts within 4mm of prim at rest: %d; Head-w diff mean %.2f max %.2f; skinned sep mean %.1f max %.1f mm"%(near.sum(),dw.mean(),dw.max(),ds2.mean()*1e3,ds2.max()*1e3))
        bad=near.copy(); bad[near]=ds2>0.003
        if bad.sum():
            P=head["rest"][bad]; print("   >3mm sep: %d verts, rest x %.3f..%.3f y %.3f..%.3f z %.3f..%.3f"%(bad.sum(),P[:,0].min(),P[:,0].max(),P[:,1].min(),P[:,1].max(),P[:,2].min(),P[:,2].max()))
